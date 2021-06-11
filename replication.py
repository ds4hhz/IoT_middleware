import socket
import struct
import uuid
from pipesfilter import in_filter
from pipesfilter import create_frame
import json


class Replication:

    def __init__(self, own_PPID, members: list, server_address=('', 15000), multicast_group='232.3.29.79'):
        self.server_address = server_address
        self.multicast_group = multicast_group
        self.max_response_size = 2048
        self.my_uuid = own_PPID
        self.replication_clock = 0
        self.members = members

        self.replication_message_counter = 0
        self.ec_dict = {}

    def create_multicast_sender(self):
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

    def send_replication_message(self, ec_dict_str: str):  # only in use from primary
        print("send replication message!")
        msg = create_frame(priority=0, role="S", message_type="replication", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.replication_clock,
                           payload=ec_dict_str)
        print(msg)
        self.multi_sock.sendto(msg.encode(), (self.multicast_group, self.server_address[1]))
        self.replication_clock += 1
        copy_of_members = self.members.copy()
        for member in range(len(self.members)):
            data, address = self.multi_sock.recvfrom(self.max_response_size)
            data_frame = in_filter(data.decode(), address)
            if data_frame[4] in copy_of_members:
                copy_of_members.pop(copy_of_members.index(data_frame[4]))
            # ToDo: receive ack from all members!
        if len(copy_of_members) == 0:
            print("all members have updated the state")
        elif self.replication_message_counter <= 2:
            self.replication_message_counter += 1
            self.send_replication_message(ec_dict_str)
            return
        else:
            print("The nodes {} are not reachable!".format(copy_of_members))
            return

    def __send_replication_message_ack(self):
        msg = create_frame(priority=0, role="S", message_type="replication_ack", msg_uuid=uuid.uuid4(),
                           ppid=self.my_uuid, fairness_assertion=1, sender_clock=self.replication_clock,
                           payload="replication message received!")
        self.multi_sock.sendto(msg.encode(), (self.multicast_group, self.server_address[1]))
        self.replication_clock += 1

    def get_replication_message(self):  # only used from secondary
        data, address = self.multi_sock.recvfrom(self.max_response_size)
        data_frame = in_filter(data.decode(), address)
        if data_frame[2] == "replication" and data_frame[4] != self.my_uuid:
            self.__send_replication_message_ack()
            self.replication_clock += 1
            temp_dict = json.loads(data_frame[7])
            for k, v in temp_dict.items():
                self.ec_dict[k] = v
            print("ec dict in rep msg: ", self.ec_dict)
            return json.dumps(self.ec_dict)
        return " fail"
