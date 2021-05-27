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
        group = socket.inet_aton(multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.multi_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


    def __dynamic_discovery(self):
        data, address = self.multi_sock.recvfrom(2048)
        print("data from Client over multicast_group: ",data)
        data_frame = in_filter(data.decode(), address)
        if (data_frame[1] == "CC" and data_frame[2] == "ec_list_query"):
            # send dict of all known executing clients with state
            msg = create_frame(1, "S", "ec_list_query_ack ", data_frame[3], my_uuid, 1, self.my_clock, json.dumps(ec_dict))
            self.multi_sock.sendto(msg.encode(), address)
            print("Send message to CC: ",msg)
            self.my_clock += 1
        elif (data_frame[1] == "EC" and data_frame[2] == "dynamic_discovery"):
            # get current state
            # and uuid
            print("Save state of EC")
            temp_dict = json.loads(data_frame[7])
            for k, v in temp_dict.items():
                ec_dict[k] = v
        return data_frame , address

    def __dynamic_discovery_ack(self, data_frame , address):
        msg = create_frame(1, "S", "dynamic_discovery_ack ", data_frame[3], my_uuid, 1, self.my_clock, "runs")
        self.multi_sock.sendto(msg.encode(), address)
        print("dynamic discovery ack msg: ",msg)
        self.my_clock += 1

    def run_dynamic_discovery(self):
        self.__create_multicast_socket()
        while(True):
            data_frame , address = self.__dynamic_discovery()
            self.__dynamic_discovery_ack(data_frame,address)

    def __open_tcp_socket(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        self.tcp_socket.bind(self.tcp_addr)
        self.tcp_socket.listen(100) # allows 100 CCs
        CC_conn, CC_addr = tcp_socket.accept()
        self.CC_connection_list.append(CC_conn)
        self.CC_address_list.append(CC_addr)

    def __receive_state_change_request(self):
        data = self.CC_connection_list[0].recvfrom(2048) # ToDo: Logik um zu erfassen, welche Verbindung
        if (len(data[0]) == 0):
            print("connection lost!")
            self.conn.close()

multicast_group = '224.3.29.71'
server_address = ('', 10000)
my_uuid = uuid.uuid4()
my_clock = 0
ec_dict = {}


def create_tcp_ex_connection(message_id, my_uuid, my_clock, payload):
    ex_tcp_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ex_tcp_con.connect(('127.0.0.1', 11000))
    ex_tcp_con.send(create_frame(1, "S", "state_change_request", message_id, my_uuid, 1, my_clock,
                                 payload).encode())
    data = ex_tcp_con.recv(1024)
    print(data)

    # "172.156.0.1, [blinking]"


def tcp_socket():  # for CC
    my_lamport = 0
    my_uuid = uuid.uuid4()
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
    tcp_socket.bind(("10.0.2.15", 12000))
    tcp_socket.listen(1)
    conn, addr = tcp_socket.accept()
    while (True):
        data = conn.recvfrom(2048)
        if (len(data[0]) == 0):
            print("connection lost!")
            conn.close()
            # restart tcp socket to CC
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
            tcp_socket.bind(("10.0.2.15", 12000))
            tcp_socket.listen(1)
            conn, addr = tcp_socket.accept()
            data = conn.recvfrom(2048)
        data_frame = in_filter(data[0].decode(), addr)
        cc_uuid = data_frame[4]
        state_request = data_frame[7][data_frame[7].index("[") + 1:data_frame[7].index("]")]
        payload = "{}, [{}]".format(cc_uuid, state_request)
        print("payload: ", payload)
        create_tcp_ex_connection(data_frame[3], my_uuid, my_lamport, payload)  # command to EC
        my_lamport += 1
        # update ex_dict after state change!
        ec_dict[cc_uuid] = state_request
        # send ack to CC
        conn.send(create_frame(1, "S", "state_change_ack", data_frame[3], my_uuid, 1, my_lamport,
                               "update your ex_dict, state ={}".format(state_request)).encode())


def udp_socket():  # for dynamic discovery
    multicast_group = '224.3.29.71'
    server_address = ('', 10000)
    my_uuid = uuid.uuid4()
    my_clock = 0
    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the server address
    sock.bind(server_address)

    # Tell the operating system to add the socket to the multicast group
    # on all interfaces.
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    # Receive/respond loop
    i = 0
    # ec_dict = {}
    global ec_dict
    while True:
        data, address = sock.recvfrom(2048)
        print(data)
        data = in_filter(data.decode(), address)
        if (data[1] == "CC" and data[2] == "ec_list_query"):
            # send dict of all known executing clients with state
            msg = create_frame(1, "S", "ec_list_query_ack ", data[3], my_uuid, 1, my_clock, json.dumps(ec_dict))
            sock.sendto(msg.encode(), address)
            print(msg)
            print("lamport clock: ", my_clock)
            my_clock += 1
            i += 1

        elif (data[1] == "EC" and data[2] == "dynamic_discovery"):
            # get current state
            # and uuid
            temp_dict = json.loads(data[7])
            for k, v in temp_dict.items():
                ec_dict[k] = v
                print(ec_dict)
            if (i % 2 == 0):
                print("sleep 5")
                time.sleep(1)
            else:
                print("sleep 2")
                time.sleep(1)
            msg = create_frame(1, "S", "dynamic_discovery_ack ", data[3], my_uuid, 1, my_clock, "runs")
            sock.sendto(msg.encode(), address)
            print(msg)
            print("lamport clock: ", my_clock)
            my_clock += 1
            i += 1


# ToDo: Multiprocessing zweiten Prozess mit TCP Socket für CC->state_change_request -> S -> EX

tcp_process = multiprocessing.Process(target=tcp_socket, name="tcp_process")
udp_process = multiprocessing.Process(target=udp_socket, name="udp_process")
tcp_process.start()
udp_process.start()
