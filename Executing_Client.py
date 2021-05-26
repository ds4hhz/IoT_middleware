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


class ExecutingClient:
    def __init__(self, address='127.0.0.1', port=11000, buffer_size=2048, multicast_group='224.3.29.71',
                 multicast_port=10000):
        self.client_address = address
        self.port_address = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        self.buffer_size = buffer_size
        self.states_dict = {"off": [0, 0, 0], "on": [0, 1, 0], "blinking": [1, 0, 0]}
        self.state = self.states_dict["off"]
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

    def receive_message(self):
        data, address = self.socket.recvfrom(2048)
        self.holdback_queue.append(in_filter(data.decode(), address))

    def get_server(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        ttl = struct.pack('b', 1)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        msg = create_frame(priority=2, role="EC", message_type=MessageType.dynamic_discovery, msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,payload="I'm alive")
        udp_socket.sendto(msg.encode(), (self.multicast_group,self.multicast_port))
        print("send message: ",msg)
        self.my_lamport_clock += 1
        data, addr = udp_socket.recvfrom(2048)
        data_frame = in_filter(data.decode(), addr)
        while (data_frame[2] != MessageType.dynamic_discovery_ack):
            data, addr = udp_socket.recvfrom(2048)
            data_frame = in_filter(data.decode(), addr)
        self.communication_partner = addr

    def __state_change(self, state_request):
        if state_request in self.states_dict:
            self.state = self.states_dict[state_request]
        else:
            logging.ERROR(
                'state request was not possible! Possible states are "off, on, blinking" ->state has not changed!')

    def __send_ack(self, address):
        msg = create_frame(priority=2, role="EC", message_type=MessageType.state_change_ack, msg_uuid=uuid.uuid4(),
                           ppid=self.uuid, fairness_assertion=1,
                           sender_clock=self.my_lamport_clock,payload="state change to: {}".format(self.state))  # ToDo: msg_uuid bei ack gleiche wie bei Ursprungsnachricht?
        self.socket.sendto(msg, address)
        self.my_lamport_clock += 1

    def __check_state(self):
        state_index = self.state.index(1)
        if state_index == 0:
            self.__off()
        elif state_index == 1:
            self.__on()
        elif state_index == 2:
            self.__blinking()
        else:
            logging.ERROR("No valid state!")

    def __off(self):
        print("client is off")

    def __on(self):
        print(("client is on"))

    def __blinking(self):
        print("client is blinking")

    def run(self):
        self.get_server()  # dynamic discovery -> bekannt machen bei den Servern
        self.__bind_socket()
        while (True):
            data, address = self.socket.recvfrom(self.buffer_size)
            data_frame = in_filter(data.decode(), address)
            if (data_frame[2] == MessageType.state_change_request):
                self.__state_change(state_request=data_frame[
                                                      7][data_frame[7].index(
                    "{"):])  # ToDo: Payload muss genauer definiert werden, weil Addresse des executing client und neuer state muss es beinhalten
                self.__send_ack(address=address)
            self.__check_state()
