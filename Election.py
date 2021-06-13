import socket
import struct
import uuid
from pipesfilter import in_filter
from pipesfilter import create_frame
from threading import Thread
import json


class Election:
    def __init__(self, own_PPID, members: list, server_address=('', 18000), multicast_group='232.3.29.89'):
        self.multicast_election_msg = '224.3.29.71'
        self.multicast_election_msg_port = 10000
        self.server_address = server_address
        self.multicast_group = multicast_group
        self.max_response_size = 2048
        self.my_uuid = own_PPID
        self.election_clock = 0
        self.members = members

        self.is_leader = False
        self.running_election = False
        self.leader_address = None
        self.election_counter = 0
        self.leader_message_counter = 0

    def create_multicast_sender(self):
        # Create the socket
        self.multi_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        self.multi_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.multi_sock.settimeout(2)
        # Bind to the server address
        self.multi_sock.bind(self.server_address)
        group = socket.inet_aton(self.multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.multi_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def __get_bigger_ids(self):
        return self.members[:self.members.index(str(self.my_uuid))]

    def __send_list_as_str(self, message_list):
        return (','.join([str(x) for x in message_list]))

    def election(self):
        self.running_election = True
        print("Node: ", self.my_uuid)
        print("starts election!")
        bigger_members = self.__get_bigger_ids()
        if len(bigger_members) == 0:
            self.is_leader = True
            self.__send_leader_message()
            print("Node: ", self.my_uuid)
            print("I'm the leader!")
            self.election_counter = 0  # reset counter for next election
            return
        msg = create_frame(priority=1, role="S", message_type="election", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.election_clock,
                           payload=self.__send_list_as_str(bigger_members)).encode()
        self.multi_sock.sendto(msg, (self.multicast_group, self.server_address[1]))
        self.election_clock += 1
        for member in range(len(bigger_members)):
            try:
                data, addr = self.multi_sock.recvfrom(2048)
            except socket.timeout:
                print("time out! No response!")
                print("try again!")
                self.election_counter += 1
                # self.multi_sock.close()
                if self.election_counter >= 2:
                    self.is_leader = True  # bigger member don't react
                    self.__send_leader_message()
                    print("Node: ", self.my_uuid)
                    print("I'm the leader!")
                    self.election_counter = 0  # reset counter for next election
                    return
                # self.create_multicast_sender()
                self.election()
                return
            print("received data in election: ", data.decode())
            data_frame = in_filter(data.decode(), addr)
            if data_frame[2] == "election_ack" and data_frame[4] in bigger_members:
                print("Node: ", self.my_uuid)
                print("I'm not the leader!")
                self.is_leader = False
                return
            elif data_frame[2] == "election_ack" and data_frame[4] < str(self.my_uuid):
                self.is_leader = True
                self.__send_leader_message()
                print("Node: ", self.my_uuid)
                print("I'm the leader!")
                self.election_counter = 0  # reset counter for next election
                return
            else: #ToDo: wtf??
                continue
        self.election_counter = 0  # reset counter for next election

    def __send_election_ack(self, address):
        msg = create_frame(priority=1, role="S", message_type="election_ack", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.election_clock,
                           payload="I'm alive!")
        self.multi_sock.sendto(msg.encode(), address)
        self.election_clock += 1

    def __send_leader_message(self):
        msg = create_frame(priority=1, role="S", message_type="leader_msg", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.election_clock,
                           payload="I'm the leader!")
        try:
            self.multi_sock.sendto(msg.encode(), (self.multicast_group, self.server_address[1]))
            self.udp_socket.sendto(msg.encode(), (self.multicast_election_msg, self.multicast_election_msg_port))
        except:
            self.__create_multicast_socket_member_discovery()
            self.multi_sock.sendto(msg.encode(), (self.multicast_group, self.server_address[1]))
        self.election_clock += 1
        copy_of_members = self.members.copy()
        for member in range(len(self.members)):
            try:
                data, address = self.udp_socket.recvfrom(2048)
            except socket.timeout:
                continue
                # self.__send_leader_message()
            data_frame = in_filter(data.decode(), address)
            if data_frame[4] in copy_of_members:
                copy_of_members.pop(copy_of_members.index(data_frame[4]))
        if len(copy_of_members) == 0:
            print("all members know the leader!")
            self.running_election = False
        elif self.leader_message_counter <= 2:
            self.leader_message_counter += 1
            self.__send_leader_message()
            return
        else:
            print("The nodes {} are not reachable!".format(copy_of_members))
            self.running_election = False
            return

    def __send_leader_message_ack(self, address):
        msg = create_frame(1, "S", "leader_msg_ack ", uuid.uuid4(), self.my_uuid, 1, self.election_clock,
                           "You are the leader")
        self.multi_sock.sendto(msg.encode(), address)
        self.election_clock += 1

    def __multicast_message_receiver(self):
        while True:
            try:
                data, address = self.multi_sock.recvfrom(2048)
            except:
                continue
            print("message receiver gets data: ", data)
            data_frame = in_filter(data.decode(), address)
            if data_frame[2] == "leader_msg" and data_frame[4] != str(self.my_uuid):
                self.leader_address = data_frame[8]
                print("Node: {} accepts node: {} as leader!".format(self.my_uuid, data_frame[4]))
                self.__send_leader_message_ack(address)
                self.is_leader = False
                self.running_election = False
            elif data_frame[2] == "election":
                self.running_election = True
                payload_list = data_frame[7].split(",")
                if str(self.my_uuid) in payload_list:
                    self.__send_election_ack(address)  # election starter is not leader!
                    if len(self.__get_bigger_ids()) == 0:
                        print("Node: ", self.my_uuid)
                        print("I'm the leader!")
                        self.is_leader = True
                        self.__send_leader_message()
                # else:
                    # self.__send_election_ack(address)  # election starter is not leader! ToDo: kein ack bedeutet 3 neue versuche!
                    # self.election()  # starts election with bigger members

    def send_election_start_message(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(3)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        ttl = struct.pack('b', 2)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        msg = create_frame(priority=1, role="EC", message_type="election", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.election_clock,
                           payload="election is started!")
        print("send election message: ", msg)
        self.udp_socket.sendto(msg.encode(), (self.multicast_election_msg, self.multicast_election_msg_port))
        self.election_clock += 1
        try:
            data, addr = self.udp_socket.recvfrom(self.max_response_size)
        except socket.timeout:
            print("time out! No response!")
            print("try again!")
            self.udp_socket.close()
            self.send_election_start_message()
            return
        print("election start ack")

    def __run_message_receiver(self):
        receiver_thread = Thread(target=self.__multicast_message_receiver, name="receiver_thread")
        receiver_thread.start()


    def run_election(self):
        self.send_election_start_message()
        self.create_multicast_sender()
        self.__run_message_receiver()
        # self.__multicast_message_receiver()
        # self.create_multicast_receiver()
        self.election()

