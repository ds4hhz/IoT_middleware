from threading import Thread

import socket
from pipesfilter import create_frame
from pipesfilter import MessageType
from pipesfilter import in_filter
import uuid
import struct
import time
import json
import sched


class CommandingClient:
    def __init__(self, buffer_size=2048, multicast_group='224.3.29.71',
                 multicast_port=10000):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        self.buffer_size = buffer_size
        self.state_list = ["off", "on", "blinking"]
        # self.states_dict = {"off": [1, 0, 0], "on": [0, 1, 0], "blinking": [0, 0, 1]}
        self.state = self.state_list[0]
        self.uuid = uuid.uuid4()
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.my_lamport_clock = 0
        self.communication_partner = ""
        self.tcp_port = 12000
        self.ex_dict = {}

        # heartbeat on server
        # heartbeat
        self.heartbeat_period = 3
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(self.heartbeat_period, 1, self.__send_heartbeat)

    def __create_multicast_socket(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(3)
        ttl = struct.pack('b', 1)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def __get_server(self):  # query list of executing client
        msg = create_frame(priority=2, role="CC", message_type="ec_list_query", msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="Send me a list of all executing clients")
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_lamport_clock += 1
        try:
            data, addr = self.udp_socket.recvfrom(2048)
        except socket.timeout:
            print("time out! No response!")
            print("try again!")
            self.udp_socket.close()
            self.__create_multicast_socket()
            self.__get_server()
            return
        data = in_filter(data.decode(), addr)
        if data[2] == "ec_list_query_ack":
            self.ex_dict = json.loads(data[7])
            self.communication_partner = addr
            print("communicationpartner address: {}".format(self.communication_partner))

    def __send_heartbeat(self):
        msg = create_frame(priority=2, role="CC", message_type="heartbeat", msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="Are you alive?")
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_lamport_clock += 1
        try:
            data, addr = self.udp_socket.recvfrom(2048)
        except socket.timeout:
            print("No leading server reachable!")
            print("try again!")
            # self.udp_socket.close()
            time.sleep(1)
            # self.__create_multicast_socket()
            self.__send_heartbeat()
            return
        if addr != self.communication_partner:
            print("leading server has changed!")
            self.communication_partner = addr
            self.__get_tcp_port()
            print("tcp_port: ", self.tcp_port)
            self.__get_server()  # dictionary mit executing clients
        self.scheduler.enter(self.heartbeat_period, 1, self.__send_heartbeat)

    def __get_tcp_port(self):
        msg = create_frame(priority=2, role="CC", message_type="tcp_port_request", msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="Send me your tcp socket port")
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_lamport_clock += 1
        try:
            data, addr = self.udp_socket.recvfrom(2048)
        except socket.timeout:
            print("time out! No response!")
            print("try again!")
            self.udp_socket.close()
            self.__create_multicast_socket()
            self.__get_server()
            return
        data_frame = in_filter(data.decode(), addr)
        if data_frame[2] == "tcp_port_request_ack":
            self.tcp_port = int(data_frame[7])
        elif data[2] == "ec_list_query_ack":
            self.ex_dict = json.loads(data[7])
            self.communication_partner = addr

    def __create_tcp_socket(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(3)
        print("open connection to: {} {}".format(self.communication_partner[0], self.tcp_port))
        self.tcp_socket.connect((self.communication_partner[0], self.tcp_port))

    def __send_state_change_request_udp(self, ex_uuid, state):
        state_change_msg_id = uuid.uuid4()
        msg = create_frame(priority=2, role="CC", message_type="state_change_request", msg_uuid=state_change_msg_id,
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="{}, [{}]".format(ex_uuid, state))
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        # wait for ack
        while True:
            try:
                data, add = self.udp_socket.recvfrom(2048)
            except socket.timeout:
                self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
                continue
            data_frame = in_filter(data.decode(), add)
            if data_frame[2] == "error":
                self.tcp_socket.close()
                self.__create_tcp_socket()
                self.__send_state_change_request(ex_uuid, state)
                break
            # if ack for state_change, than update ex_dict
            print("ack from Server: ", data_frame)
            if (data_frame[2] == "state_change_ack" and data_frame[3] == str(state_change_msg_id)):
                self.ex_dict[ex_uuid] = state
                print("update EC state: ", self.ex_dict)
                # tcp_socket.close()
                break
            else:
                print("wrong message, wait for state_change_ack")

    def __send_state_change_request(self, ex_uuid, state):
        state_change_msg_id = uuid.uuid4()
        msg = create_frame(priority=2, role="CC", message_type="state_change_request", msg_uuid=state_change_msg_id,
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="{}, [{}]".format(ex_uuid, state))
        # tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # tcp_socket.settimeout(2)
        # tcp_socket.connect((self.communication_partner[0], self.tcp_port))
        # tcp_socket.connect(("127.0.0.1", 12000))
        self.tcp_socket.send(msg.encode())
        print("length of the message: ", len(msg.encode()))
        print("message id of change state request: ", state_change_msg_id)
        # wait for ack
        while True:
            try:
                data, add = self.tcp_socket.recvfrom(2048)
            except socket.timeout as e:
                print(e)
                # reopen tcp connection
                try:
                    self.tcp_socket.connect((self.communication_partner[0], self.tcp_port))
                    self.tcp_socket.send(msg.encode())
                    continue
                except:
                    self.tcp_socket.close()
                    self.__get_tcp_port()
                    self.__get_server()
                    self.__create_tcp_socket()
                    self.tcp_socket.send(msg.encode())
                continue
            if (len(data) == 0):
                print("connection lost!")
                self.tcp_socket.close()
                self.__create_tcp_socket()
                self.__send_state_change_request(ex_uuid, state)
                break
            data_frame = in_filter(data.decode(), add)
            # if ack for state_change, than update ex_dict
            print("ack from Server: ", data_frame)
            if (data_frame[2] == "state_change_ack" and data_frame[3] == str(state_change_msg_id)):
                self.ex_dict[ex_uuid] = state
                print("update EC state: ", self.ex_dict)
                # tcp_socket.close()
                break
            elif data_frame[2] == "error":
                self.tcp_socket.close()
                self.__create_tcp_socket()
                self.__send_state_change_request(ex_uuid, state)
                break
            elif data_frame[2] == "state_change_ack_err":
                print("wrong PPID!")
                break
            else:
                print("wrong message, wait for state_change_ack")

    def __send_ack(self, connection):
        msg = create_frame(priority=2, role="EC", message_type="state_change_ack", msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1,
                           sender_clock=self.my_lamport_clock, payload="state change to: {}".format(
                self.state).encode())
        # self.socket.sendto(msg.encode(), address)
        connection.send(msg.encode())
        self.my_lamport_clock += 1

    def run_heartbeat_S(self):
        self.scheduler.run()

    def run(self):
        heartbeat_thread = Thread(target=self.run_heartbeat_S, name="heartbeat_thread")
        self.__create_multicast_socket()
        self.__get_tcp_port()
        print("tcp_port: ", self.tcp_port)
        self.__get_server()  # dictionary mit executing clients
        self.__create_tcp_socket()
        heartbeat_thread.start()
        while (True):
            print(self.ex_dict)
            if (len(self.ex_dict) == 0):
                print("update list of ECs")
                time.sleep(5)
                self.__get_server()
                continue
            print(
                "please enter the UUID of the client for the state change request or type \"update\" for update of ECs:")
            executing_client_uuid = str(input())
            if (executing_client_uuid == "update"):
                self.__get_server()
                continue
            elif not executing_client_uuid in self.ex_dict:
                print("Please type a UUID from the list!")
                print("update list of ECs")
                print(
                    "please enter the UUID of the client for the state change request or type \"update\" for update of ECs:")
                executing_client_uuid = str(input())
                if (executing_client_uuid == "update"):
                    self.__get_server()
                    continue
            print("please enter the state you want, possible states are \"off, on , blinking\" ")
            executing_client_state = str(input())
            # self.__send_state_change_request_udp(executing_client_uuid, executing_client_state)
            self.__send_state_change_request(executing_client_uuid, executing_client_state)
            self.__get_server()  # update states of ECs
