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
import sched
from replication import Replication
from Election import Election

ec_dict = {}


class Server:
    def __init__(self, tcp_address):
        global ec_dict
        self.multicast_group = '224.3.29.71'
        self.multicast_port = 10000
        self.tcp_addr = tcp_address  # ("", 12000) #("10.0.2.15", 12000)
        self.server_address = ('', 10000)
        self.my_clock = 0
        self.my_uuid = uuid.uuid4()
        self.ec_dict = ec_dict
        self.CC_connection_list = []
        self.CC_address_list = []

        # election
        self.is_leader = False
        self.running_election = False
        self.leader_address = None
        self.group_member_list = []
        self.discovery_counter = 4
        self.election_counter = 0
        self.leader_message_counter = 0

        # heartbeat ECs
        self.heartbeat_period_ec = 10
        self.scheduler_ec = sched.scheduler(time.time, time.sleep)
        self.scheduler_ec.enter(self.heartbeat_period_ec, 1, self.__check_EC_state)

        # heartbeat leading Server
        self.heartbeat_period_server = 1
        self.scheduler_s = sched.scheduler(time.time, time.sleep)
        self.scheduler_s.enter(self.heartbeat_period_server, 1, self.__send_heartbeat_message_s)
        self.leading_server_address = ""
        self.server_heartbeat_fail_counter = 0
        self.thread_list = []

    def __create_multicast_socket_member_discovery(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(3)
        ttl = struct.pack('b', 1)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def __get_group_members(self):
        msg = create_frame(priority=2, role="S", message_type="group_discovery", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.my_clock,
                           payload="Get group member ids")
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_clock += 1
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(2048)
            except socket.timeout:
                print("time out! No response!")
                print("try again!")
                self.discovery_counter -= 1
                if self.discovery_counter <= 0 and len(self.group_member_list) == 1:
                    self.is_leader = True  # lonely group member
                    self.running_election = False
                    return
                elif self.discovery_counter <= 0:
                    break
                self.udp_socket.close()
                self.__create_multicast_socket_member_discovery()
                self.__get_group_members()
                return
            print("received data: ", data.decode())
            data_frame = in_filter(data.decode(), addr)
            if data_frame[2] == "group_discovery_ack" and not data_frame[7] in self.group_member_list:
                payload_list = data_frame[7].split("/")
                self.group_member_list.append(payload_list[0])
                # sorted(self.group_member_list, reverse=True)  # absteigende Sortierung
                self.group_member_list.sort(reverse=True)
                temp_dict = json.loads(payload_list[1])
                if len(temp_dict) != 0:
                    for k, v in temp_dict.items():
                        self.ec_dict[k] = v
                # self.udp_socket.close()

    def __send_heartbeat_message_s(self):
        msg = create_frame(priority=2, role="S", message_type="heartbeat", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.my_clock,
                           payload="Are you alive?")
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_clock += 1
        print("send server heartbeat message")
        try:
            data, addr = self.udp_socket.recvfrom(2048)
        except socket.timeout:
            print("Primary not reachable!!")
            self.server_heartbeat_fail_counter += 1
            if self.server_heartbeat_fail_counter >= 3:
                print("start new election!")
                self.server_heartbeat_fail_counter = 0
                self.udp_socket.close()
                self.group_member_list.clear()
                self.run_member_discovery()
                self.election_obj = Election(self.my_uuid, self.group_member_list)
                self.election_obj.run_election()
                self.thread_list[-1].join()
                return
            print("try again!")
            self.udp_socket.close()
            time.sleep(3)
            self.__create_multicast_socket_member_discovery()
            self.__send_heartbeat_message_s()
            return
        if addr != self.leading_server_address:
            print("leading server has changed!")
            self.leading_server_address = addr
        self.scheduler_ec.enter(self.heartbeat_period_ec, 1, self.__send_heartbeat_message_s)

    def __create_multicast_socket(self):
        # Create the socket
        self.multi_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        self.multi_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to the server address
        self.multi_sock.bind(self.server_address)
        group = socket.inet_aton(self.multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.multi_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # self.multi_sock.setsockopt(socket.IPPROTO_IP, socket.SO_REUSEPORT, mreq)

    def __dynamic_discovery(self):  # messages over multicast group
        data, address = self.multi_sock.recvfrom(2048)
        data_frame = in_filter(data.decode(), address)
        if data_frame[1] == "CC" and data_frame[2] == "ec_list_query" and self.is_leader:
            # send dict of all known executing clients with state
            msg = create_frame(1, "S", "ec_list_query_ack", data_frame[3], self.my_uuid, 1, self.my_clock,
                               json.dumps(self.ec_dict))
            self.multi_sock.sendto(msg.encode(), address)
            print("Send message to CC: ", msg)
            self.my_clock += 1
        elif data_frame[1] == "EC" and data_frame[2] == "dynamic_discovery" and self.is_leader:
            temp_dict = json.loads(data_frame[7])
            for k, v in temp_dict.items():
                self.ec_dict[k] = v
            self.__dynamic_discovery_ack(data_frame, address)
            # self.replication_obj.send_replication_message(json.dumps(self.ec_dict))
        elif data_frame[1] == "S" and data_frame[2] == "group_discovery":  # group member request
            self.__group_discovery_ack(address)
        elif data_frame[2] == "tcp_port_request" and self.is_leader:  # send tcp socket port
            self.__send_tcp_port(address)
        # election messages
        elif data_frame[2] == "election":
            self.running_election = True
            self.is_leader = False
            self.__send_election_ack(address)
        elif data_frame[2] == "leader_msg" and data_frame[4] != str(self.my_uuid):
            self.__send_leader_message_ack(address)
            self.leading_server_address = address
            print("leader message received")
            self.is_leader = False
            self.running_election = False
        elif data_frame[2] == "leader_msg" and data_frame[4] == str(self.my_uuid):
            self.__send_leader_message_ack(address)
            print("leader message received -> I'm the leader!")
            self.is_leader = True
            self.running_election = False
        # heartbeat messages
        elif self.is_leader and data_frame[2] == "heartbeat" and data_frame[1] == "EC":
            self.__send_heartbeat_ack(address)
            temp_dict = json.loads(data_frame[7])
            for k, v in temp_dict.items():
                self.ec_dict[k] = v
            self.__dynamic_discovery_ack(data_frame, address)
        elif self.is_leader and data_frame[2] == "heartbeat" and data_frame[1] == "S":
            self.__send_heartbeat_ack(address)
            print("server heartbeat message received")
        return data_frame, address

    def __send_heartbeat_ack(self, address):
        msg = create_frame(1, "S", "heartbeat_ack ", uuid.uuid4(), self.my_uuid, 1, self.my_clock,
                           "heartbeat received!")
        self.multi_sock.sendto(msg.encode(), address)
        self.my_clock += 1

    def __group_discovery_ack(self, address):
        msg = create_frame(priority=2, role="S", message_type="group_discovery_ack", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.my_clock,
                           payload="{}/{}".format(self.my_uuid, json.dumps(self.ec_dict)))
        self.multi_sock.sendto(msg.encode(), address)
        self.my_clock += 1

    def __send_leader_message_ack(self, address):
        msg = create_frame(1, "S", "leader_msg_ack ", uuid.uuid4(), self.my_uuid, 1, self.my_clock,
                           "election done!")
        self.multi_sock.sendto(msg.encode(), address)
        self.my_clock += 1

    def __send_election_ack(self, address):
        msg = create_frame(1, "S", "election_ack ", uuid.uuid4(), self.my_uuid, 1, self.my_clock,
                           "election message received")
        self.multi_sock.sendto(msg.encode(), address)
        self.my_clock += 1

    def __dynamic_discovery_ack(self, data_frame, address):
        msg = create_frame(1, "S", "dynamic_discovery_ack ", data_frame[3], self.my_uuid, 1, self.my_clock, "runs")
        self.multi_sock.sendto(msg.encode(), address)
        print("dynamic discovery ack msg: ", msg)
        self.my_clock += 1

    def __send_tcp_port(self, address):  # to CC
        msg = create_frame(priority=2, role="S", message_type="tcp_port_request_ack", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.my_clock,
                           payload=self.tcp_addr[1])
        self.multi_sock.sendto(msg.encode(), address)
        self.my_clock += 1

    def __open_tcp_socket(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client for CC connection
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
        del_list = []
        for key, item in self.ec_dict.items():
            addr_tuple = (item[1], item[2])
            ex_tcp_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                ex_tcp_con.connect(addr_tuple)
            except:
                print("Executing client {} not reachable!".format(key))
                del_list.append(key)
                continue
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
                del_list.append(key)
        for key in del_list:
            del self.ec_dict[key]
        print("EC_dict updated")
        print("EC_dict: ", self.ec_dict)
        # self.replication_obj.send_replication_message(json.dumps(self.ec_dict))
        self.scheduler_ec.enter(self.heartbeat_period_ec, 1, self.__check_EC_state)

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

    def run_heartbeat_EC(self):
        self.scheduler_ec.run()

    def run_heartbeat_s(self):
        self.scheduler_s.run()
        while True:
            pass

    def run_member_discovery(self):
        self.__create_multicast_socket_member_discovery()
        self.group_member_list.append(str(self.my_uuid))
        self.__get_group_members()
        self.group_member_list = list(dict.fromkeys(self.group_member_list))

    def run_secondary(self):
        self.replication_obj.create_multicast_receiver()
        while True:
            self.ec_dict = self.replication_obj.get_replication_message()

    def run_all(self, server):
        tcp_thread = Thread(target=server.run_tcp_socket, name="tcp-thread")
        udp_thread = Thread(target=server.run_dynamic_discovery, name="discovery-thread")
        heartbeat_thread_EC = Thread(target=self.run_heartbeat_EC, name="heartbeat_thread_EC")
        self.thread_list.append(Thread(target=self.run_heartbeat_s, name="heartbeat_thread_s"))
        # secondary_thread = Thread(target=self.run_secondary, name="secondary_thread")
        udp_thread.start()
        self.run_member_discovery()
        self.election_obj = Election(self.my_uuid, self.group_member_list)
        # self.replication_obj = Replication(self.my_uuid, self.group_member_list)
        self.election_obj.run_election()
        # ToDo: start election -> need members
        tcp_thread.start()
        heartbeat_thread_EC.start()
        while True:  # main thread for election and replication
            print("leader: ", self.is_leader)
            time.sleep(1)
            if not self.running_election:
                # if not secondary_thread.is_alive() and not self.is_leader:
                #     secondary_thread.start()
                if (not self.thread_list[-1].is_alive()) and (not self.is_leader):
                    self.thread_list.append(Thread(target=self.run_heartbeat_s,
                                                     name="heartbeat_thread_s{}".format(len(self.thread_list))))
                    try:
                        self.thread_list[-1].start()
                    except RuntimeError as e:
                        print(e)
            else:
                # if secondary_thread.is_alive():
                #     secondary_thread.join()
                if self.thread_list[-1].is_alive():
                    self.thread_list[-1].join()


# server = Server()
server1 = Server(("", 12000))
server2 = Server(("", 12001))
server3 = Server(("", 12003))
# server.run_all()
server1_process = multiprocessing.Process(target=server1.run_all, name="server1", args=(server1,))
server2_process = multiprocessing.Process(target=server2.run_all, name="server2", args=(server2,))
# server3_process = multiprocessing.Process(target=server3.run_all, name="server3", args=(server3,))
#
# server1_process.start()
# time.sleep(5)
# server2_process.start()
# time.sleep(5)
# server3_process.start()
server3.run_all(server3)
