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
import sys
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
        print(self.ex_dict)
        # data_frame = in_filter(data.decode(), addr)
        # while (data_frame[2] != 2):
        #     data, addr = udp_socket.recvfrom(2048)
        #     data_frame = in_filter(data.decode(), addr)
        self.communication_partner = addr

    def __send_state_change_request(self, ex_uuid, state):
        msg = create_frame(priority=2, role="CC", message_type="state_change_request", msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                           payload="{}, [{}]".format(ex_uuid, state))
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(3)

    def __send_ack(self, connection):
        msg = create_frame(priority=2, role="EC", message_type=MessageType.state_change_ack, msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1,
                           sender_clock=self.my_lamport_clock, payload="state change to: {}".format(
                self.state))  # ToDo: msg_uuid bei ack gleiche wie bei Ursprungsnachricht?
        # self.socket.sendto(msg.encode(), address)
        connection.send(msg.encode())
        self.my_lamport_clock += 1

    def run(self):
        self.get_server()  # dictionary mit executing clients
        print(self.ex_dict)
        print("please enter the UUID of the client for the state change requst:")
        executing_client_uuid = str(input())
        print("please enter the state you want, possible states are \"off, on , blinking\" ")
        executing_client_state = str(input())
        # connection, addr = self.__bind_socket()
        # while (True):
        #     data = connection.recvfrom(self.buffer_size)
        #     if (len(data[0])== 0):
        #         print("connection lost!")
        #         connection.close()
        #         self.get_server()
        #         self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        #         connection, addr = self.__bind_socket()
        #     else:
        #         print(data)
        #         data_frame = in_filter(data[0].decode(), addr)
        #         print("data frame: ", data_frame)
        #         if (data_frame[2] == 3):
        #             self.__state_change(state_request=data_frame[7][data_frame[7].index("{")+1:data_frame[7].index("}")])
        #             # ToDo: Payload muss genauer definiert werden, weil Addresse des executing client und neuer state muss es beinhalten
        #             # state wird so erwartet: {blinking}
        #             self.__send_ack(connection=connection)
        #     self.__check_state()
