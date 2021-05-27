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


class Server:
    def __init__(self):
        self.multicast_group = '224.3.29.71'
        self.tcp_addr = ("10.0.2.15", 12000)
        self.server_address = ('', 10000)
        self.my_clock = 0
        self.my_uuid = uuid.uuid4()
        self.ec_dict = {}
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
        cc_uuid = None

        # for conn in self.CC_connection_list:
        #    data_list.append(conn.recvfrom(2048))
        # for data in data_list:
        if (len(data[0]) == 0):
            print("connection lost!")
            self.CC_connection_list[-1].close()
            data_received = False

        else:
            data_received = True
            data_frame = in_filter(data[0].decode(), self.CC_address_list[-1])
            cc_uuid = data_frame[4]
            state_request = data_frame[7][data_frame[7].index("[") + 1:data_frame[7].index("]")]
            payload = "{}, [{}]".format(cc_uuid, state_request)
            message_id = data_frame[3]
            print("payload: ", payload)
            # update ex_dict after state
        return data_received, payload, message_id, state_request, cc_uuid

    def __send_state_change_request_to_EC(self, message_id, payload, cc_uuid, state_request):
        ex_tcp_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ex_tcp_con.connect(('127.0.0.1', 11000))
        ex_tcp_con.send(create_frame(1, "S", "state_change_request", message_id, self.my_uuid, 1, self.my_clock,
                                     payload).encode())
        data = ex_tcp_con.recv(1024)
        print("data from EC tcpconnection: ", data)
        if (len(data) != 0):
            print("received data from EC: ", data[0])
            self.ec_dict[cc_uuid] = state_request
            return True
        else:
            return False

    def __state_change_ack_to_CC(self, payload, message_id, state_request):  # to CC
        # self.__send_state_change_request_to_EC(message_id, payload)  # command to EC
        # self.my_clock += 1
        # send ack to CC
        self.CC_connection_list[-1].send(
            create_frame(1, "S", "state_change_ack", message_id, self.my_uuid, 1, self.my_clock,
                         "update your ex_dict, state ={}".format(state_request)).encode())

    def run_dynamic_discovery(self):
        self.__create_multicast_socket()
        while (True):
            data_frame, address = self.__dynamic_discovery()
            self.__dynamic_discovery_ack(data_frame, address)

    def run_tcp_socket(self):
        self.__open_tcp_socket()
        while (True):
            data_received, payload, message_id, state_request, cc_uuid = self.__receive_state_change_request()
            if (data_received):
                got_state_change_request = self.__send_state_change_request_to_EC(message_id, payload, cc_uuid, state_request)
                if (got_state_change_request):
                    if (data_received):
                        self.__state_change_ack_to_CC(payload, message_id, state_request)
                        print("message id of change ack: ", message_id)
                    else:
                        self.run_tcp_socket()
                        return
                else:
                    continue
            else:
                self.__open_tcp_socket()

            # multicast_group = '224.3.29.71'


server = Server()

tcp_process = multiprocessing.Process(target=server.run_tcp_socket, name="tcp_process")
udp_process = multiprocessing.Process(target=server.run_dynamic_discovery, name="udp_process")
tcp_process.start()
udp_process.start()

# server_address = ('', 10000)
# my_uuid = uuid.uuid4()
# my_clock = 0
# ec_dict = {}
#
#
# def create_tcp_ex_connection(message_id, my_uuid, my_clock, payload):
#     ex_tcp_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     ex_tcp_con.connect(('127.0.0.1', 11000))
#     ex_tcp_con.send(create_frame(1, "S", "state_change_request", message_id, my_uuid, 1, my_clock,
#                                  payload).encode())
#     data = ex_tcp_con.recv(1024)
#     print(data)
#
#     # "172.156.0.1, [blinking]"
#
#
# def tcp_socket():  # for CC
#     my_lamport = 0
#     my_uuid = uuid.uuid4()
#     tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
#     tcp_socket.bind(("10.0.2.15", 12000))
#     tcp_socket.listen(1)
#     conn, addr = tcp_socket.accept()
#     while (True):
#         data = conn.recvfrom(2048)
#         if (len(data[0]) == 0):
#             print("connection lost!")
#             conn.close()
#             # restart tcp socket to CC
#             tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
#             tcp_socket.bind(("10.0.2.15", 12000))
#             tcp_socket.listen(1)
#             conn, addr = tcp_socket.accept()
#             data = conn.recvfrom(2048)
#         else:
#             data_frame = in_filter(data[0].decode(), addr)
#             cc_uuid = data_frame[4]
#             state_request = data_frame[7][data_frame[7].index("[") + 1:data_frame[7].index("]")]
#             payload = "{}, [{}]".format(cc_uuid, state_request)
#             print("payload: ", payload)
#             create_tcp_ex_connection(data_frame[3], my_uuid, my_lamport, payload)  # command to EC
#             my_lamport += 1
#             # update ex_dict after state change!
#             ec_dict[cc_uuid] = state_request
#             # send ack to CC
#             conn.send(create_frame(1, "S", "state_change_ack", data_frame[3], my_uuid, 1, my_lamport,
#                                    "update your ex_dict, state ={}".format(state_request)).encode())
#
#
# def udp_socket():  # for dynamic discovery
#     multicast_group = '224.3.29.71'
#     server_address = ('', 10000)
#     my_uuid = uuid.uuid4()
#     my_clock = 0
#     # Create the socket
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
#     # Bind to the server address
#     sock.bind(server_address)
#
#     # Tell the operating system to add the socket to the multicast group
#     # on all interfaces.
#     group = socket.inet_aton(multicast_group)
#     mreq = struct.pack('4sL', group, socket.INADDR_ANY)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
#     # Receive/respond loop
#     i = 0
#     # ec_dict = {}
#     global ec_dict
#     while True:
#         data, address = sock.recvfrom(2048)
#         print(data)
#         data = in_filter(data.decode(), address)
#         if (data[1] == "CC" and data[2] == "ec_list_query"):
#             # send dict of all known executing clients with state
#             msg = create_frame(1, "S", "ec_list_query_ack ", data[3], my_uuid, 1, my_clock, json.dumps(ec_dict))
#             sock.sendto(msg.encode(), address)
#             print(msg)
#             print("lamport clock: ", my_clock)
#             my_clock += 1
#             i += 1
#
#         elif (data[1] == "EC" and data[2] == "dynamic_discovery"):
#             # get current state
#             # and uuid
#             temp_dict = json.loads(data[7])
#             for k, v in temp_dict.items():
#                 ec_dict[k] = v
#                 print(ec_dict)
#             if (i % 2 == 0):
#                 print("sleep 5")
#                 time.sleep(1)
#             else:
#                 print("sleep 2")
#                 time.sleep(1)
#             msg = create_frame(1, "S", "dynamic_discovery_ack ", data[3], my_uuid, 1, my_clock, "runs")
#             sock.sendto(msg.encode(), address)
#             print(msg)
#             print("lamport clock: ", my_clock)
#             my_clock += 1
#             i += 1
