from configurations import cfg
import logging
import socket
from Messenger import Messenger
from pipesfilter import create_frame
from pipesfilter import Role
from pipesfilter import MessageType
from pipesfilter import in_filter
import uuid
import struct
import time
import json


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
        self.message_type_list = ["msg_ack", "dynamic_discovery", "dynamic_discovery_ack", "state_change_request",
                                  "state_change_ack",
                                  "election", "leader_msg", "replication", "replication_ack", "heartbeat"]
        # self.messenger_obj = Messenger(process_id=self.uuid, ToS=Role.EC,
        #                                multicast_group="233.33.33.33", multicast_port=9950,
        #                                bcn="192.168.1.255",
        #                                bcp=10500)
        # toDo: client id

    def __bind_socket(self):
        self.socket.bind((self.client_address, self.port_address))
        self.socket.listen(1)
        conn, addr = self.socket.accept()
        return conn, addr

    def receive_message(self):
        data, address = self.socket.recvfrom(2048)
        self.holdback_queue.append(in_filter(data.decode(), address))

    def get_server(self):  # ToDO: get list of executing client
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(3)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        ttl = struct.pack('b', 1)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        msg = create_frame(priority=2, role="CC", message_type="ec_list_query", msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="Send me a list of all executing clients")

        udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_lamport_clock += 1
        try:
            data, addr = udp_socket.recvfrom(2048)
        except socket.timeout:
            print("time out! No response!")
            print("try again!")
            udp_socket.close()
            self.get_server()
            return
        print("received data: ", data.decode())
        data = in_filter(data.decode(), addr)
        self.ex_dict = json.loads(data[7])
        self.communication_partner = addr

    def __send_state_change_request(self, ex_uuid, state):
        state_change_msg_id = uuid.uuid4()
        msg = create_frame(priority=2, role="CC", message_type="state_change_request", msg_uuid=state_change_msg_id,
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="{}, [{}]".format(ex_uuid, state))
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((self.communication_partner[0], 12000))
        # tcp_socket.connect(("127.0.0.1", 12000))
        tcp_socket.send(msg.encode())
        print("length of the message: ", len(msg.encode()))
        print("message id of change state request: ", state_change_msg_id)
        # wait for ack
        while (True):
            data, add = tcp_socket.recvfrom(2048)
            if (len(data) == 0):
                print("connection lost!")
                tcp_socket.close()
                break
            data_frame = in_filter(data.decode(), add)
            # if ack for state_change, than update ex_dict
            print("ack from Server: ", data_frame)
            if (data_frame[2] == "state_change_ack" and data_frame[3] == str(state_change_msg_id)):
                self.ex_dict[ex_uuid] = state
                print("update EC state: ", self.ex_dict)
                tcp_socket.close()
                break
            else:
                print("wrong message, wait for state_change_ack")

    def __send_ack(self, connection):
        msg = create_frame(priority=2, role="EC", message_type=MessageType.state_change_ack, msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1,
                           sender_clock=self.my_lamport_clock, payload="state change to: {}".format(
                self.state).encode())  # ToDo: msg_uuid bei ack gleiche wie bei Ursprungsnachricht?
        # self.socket.sendto(msg.encode(), address)
        connection.send(msg.encode())
        self.my_lamport_clock += 1

    def run(self):
        self.get_server()  # dictionary mit executing clients
        while (True):
            print(self.ex_dict)
            if (len(self.ex_dict) == 0):
                print("update list of ECs")
                time.sleep(5)
                self.get_server()
                continue
            print("please enter the UUID of the client for the state change requst:")
            executing_client_uuid = str(input())
            print("please enter the state you want, possible states are \"off, on , blinking\" ")
            executing_client_state = str(input())
            self.__send_state_change_request(executing_client_uuid, executing_client_state)
