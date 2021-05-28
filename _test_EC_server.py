import struct
import socket
from pipesfilter import create_frame
from pipesfilter import Role
from pipesfilter import MessageType
from pipesfilter import in_filter
import uuid
import time
import sys
import json
import multiprocessing
from threading import Thread
from sched import scheduler

ec_dict = {}


class Server:
    def __init__(self):
        global ec_dict
        self.multicast_group = '224.3.29.71'
        self.tcp_addr = ("10.0.2.15", 12000)
        self.server_address = ('', 10000)
        self.my_clock = 0
        self.my_uuid = uuid.uuid4()
        self.ec_dict = ec_dict
        self.CC_connection_list = []
        self.CC_address_list = []

    def __create_multicast_socket(self):
        # Create the socket
        self.multi_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to the server address
        self.multi_sock.bind(self.server_address)
        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        group = socket.inet_aton(self.multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.multi_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def __dynamic_discovery(self):
        data, address = self.multi_sock.recvfrom(2048)
        print("data from Client over multicast_group: ", data)
        data_frame = in_filter(data.decode(), address)
        if (data_frame[1] == "CC" and data_frame[2] == "ec_list_query"):
            # send dict of all known executing clients with state
            msg = create_frame(1, "S", "ec_list_query_ack ", data_frame[3], self.my_uuid, 1, self.my_clock,
                               json.dumps(self.ec_dict))
            self.multi_sock.sendto(msg.encode(), address)
            print("Send message to CC: ", msg)
            self.my_clock += 1
        elif (data_frame[1] == "EC" and data_frame[2] == "dynamic_discovery"):
            # get current state
            # and uuid
            print("Save state of EC")
            temp_dict = json.loads(data_frame[7])
            for k, v in temp_dict.items():
                self.ec_dict[k] = v
            self.__dynamic_discovery_ack(data_frame, address)
        return data_frame, address

    def __dynamic_discovery_ack(self, data_frame, address):
        msg = create_frame(1, "S", "dynamic_discovery_ack ", data_frame[3], self.my_uuid, 1, self.my_clock, "runs")
        self.multi_sock.sendto(msg.encode(), address)
        print("dynamic discovery ack msg: ", msg)
        self.my_clock += 1

    def __open_tcp_socket(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        self.tcp_socket.bind(self.tcp_addr)
        self.tcp_socket.listen(1)  # allows 1 CCs
        CC_conn, CC_addr = self.tcp_socket.accept()
        self.CC_connection_list.append(CC_conn)
        self.CC_address_list.append(CC_addr)

    def __receive_state_change_request(self):  # from CC
        data = self.CC_connection_list[-1].recvfrom(2048)  # ToDo: Logik um zu erfassen, welche Verbindung
        payload = None
        message_id = None
        state_request = None
        target_ec_uuid = None
        if (len(data[0]) == 0):
            print("connection lost!")
            self.CC_connection_list[-1].close()
            # listen for new connection
            self.tcp_socket.listen(1)  # allows 1 CCs
            CC_conn, CC_addr = self.tcp_socket.accept()
            self.CC_connection_list.append(CC_conn)
            self.CC_address_list.append(CC_addr)
            data_received = False
        else:
            data_received = True
            data_frame = in_filter(data[0].decode(), self.CC_address_list[-1])
            target_ec_uuid = data_frame[7][:data_frame[7].index(",")]
            state_request = data_frame[7][data_frame[7].index("[") + 1:data_frame[7].index("]")]
            payload = "{}, [{}]".format(target_ec_uuid, state_request)
            message_id = data_frame[3]
            print("payload: ", payload)
            # update ex_dict after state
        return data_received, payload, message_id, state_request, target_ec_uuid

    def __send_state_change_request_to_EC(self, message_id, payload, cc_uuid, state_request, EC_connection: tuple):
        ex_tcp_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # ex_tcp_con.connect(('127.0.0.1', 11000))
        ex_tcp_con.connect(EC_connection)
        ex_tcp_con.send(create_frame(1, "S", "state_change_request", message_id, self.my_uuid, 1, self.my_clock,
                                     payload).encode())
        data = ex_tcp_con.recv(2048)
        print("data from EC tcp connection: ", data)
        if (len(data) != 0):
            print("received data from EC: ", data[0])
            self.ec_dict[cc_uuid][0] = state_request
            ex_tcp_con.close()
            return True
        else:
            ex_tcp_con.close()
            return False

    def __check_EC_state(self):
        for key, item in self.ec_dict.items():
            addr_tuple = (item[1], item[2])
            ex_tcp_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ex_tcp_con.connect(addr_tuple)
            ex_tcp_con.send(create_frame(1, "S", "heartbeat", uuid.uuid4(), self.my_uuid, 1, self.my_clock,
                                         "give me your state").encode())
            ex_tcp_con.settimeout(2)
            try:
                data = ex_tcp_con.recv(2048)
                data_frame = in_filter(data.decode(), addr_tuple)
                print("Save state of EC")
                temp_dict = json.loads(data_frame[7])
                for k, v in temp_dict.items():
                    self.ec_dict[k] = v
            except:
                del ec_dict[key]
        print("EC_dict updated")

    def __state_change_ack_to_CC(self, payload, message_id, state_request):  # to CC
        self.CC_connection_list[-1].send(
            create_frame(1, "S", "state_change_ack", message_id, self.my_uuid, 1, self.my_clock,
                         "update your ex_dict, state ={}".format(state_request)).encode())

    def run_dynamic_discovery(self):
        self.__create_multicast_socket()
        while (True):
            data_frame, address = self.__dynamic_discovery()
            # self.__dynamic_discovery_ack(data_frame, address)
            print("ec_dict in udp thread: ", self.ec_dict)

    def run_tcp_socket(self):
        self.__open_tcp_socket()  # socket for CC communication
        while (True):
            data_received, payload, message_id, state_request, target_ec_uuid = self.__receive_state_change_request()
            if (data_received):
                EC_address = (self.ec_dict[target_ec_uuid][1], self.ec_dict[target_ec_uuid][2])
                got_state_change_request = self.__send_state_change_request_to_EC(message_id, payload, target_ec_uuid,
                                                                                  state_request, EC_address)
                if (got_state_change_request):
                    if (data_received):
                        self.__state_change_ack_to_CC(payload, message_id, state_request)
                    else:
                        # self.run_tcp_socket()
                        continue
                else:
                    continue
            else:
                continue
                # self.__open_tcp_socket()

    def run_all(self):
        # tcp_process = multiprocessing.Process(target=server.run_tcp_socket, name="tcp_process")
        # udp_process = multiprocessing.Process(target=server.run_dynamic_discovery, name="udp_process")
        # tcp_process.start()
        # udp_process.start()
        tcp_thread = Thread(target=server.run_tcp_socket, name="tcp-thread")
        udp_thread = Thread(target=server.run_dynamic_discovery, name="tcp-thread")
        tcp_thread.start()
        udp_thread.start()

        #ToDO: scheduler for heartbeat

        # multicast_group = '224.3.29.71'


server = Server()
server.run_all()

# tcp_thread = Thread(target=server.run_tcp_socket, name="tcp-thread")
# udp_thread = Thread(target=server.run_dynamic_discovery, name="tcp-thread")
# tcp_thread.start()
# udp_thread.start()


# tcp_process = multiprocessing.Process(target=server.run_tcp_socket, name="tcp_process")
# udp_process = multiprocessing.Process(target=server.run_dynamic_discovery, name="udp_process")
# tcp_process.start()
# udp_process.start()
# server.run_tcp_socket()
