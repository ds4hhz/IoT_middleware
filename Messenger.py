import socket
from pipesfilter import create_frame, in_filter
from queue import PriorityQueue
from broadcastsender import BroadcastSender
from broadcastlistener import BroadcastListener
from multicastsender import MulticastSender
from multicastreceiver import MulticastListener

#ToDo vector clock in lampert clock
class Messenger:
    def __init__(self, process_id: int, ToS: int, multicast_group: str, multicast_port: int,
                 bcn="192.168.1.255", bcp=10500):
        self.my_id = process_id
        self.ToS = ToS
        self.ToS_list = ["S", "CC", "EC"]
        self.message_type_list = ["msg_ack", "dynamic_discovery", "state_change_request", "state_change_ack",
                                  "election", "leader_msg", "replication", "replication_ack", "heartbeat"]

        self.bcn = bcn
        self.bsp = bcp
        self.multicast_group = (multicast_group, multicast_port)
        self.udp_socket = socket.socket(socket.AF_INET,
                                        socket.SOCK_DGRAM)  # ToDo: Klären muss Socket wieder geschlossen werden? Und wenn wann?

        self.message_max_size = 4096
        self.message_id_counter = 0

        self.has_received = {}
        self.has_acknowledged = {}  # saves acknowledged messages
        self.unack_messages = []  # messages with pending acknowledgement
        self.holdback_queue = []  # list of received messages -> last messages

        self.holdback_sequence_counter = 0
        self.sequence_counter = 0
        self.SEQUENCER_ID = 0

        self.queue = PriorityQueue()
        self.my_lamport_clock = [0] # * num_processes

        self.broadcast_sender_obj = BroadcastSender()

    def compute_priority(self):
        sorted(self.holdback_queue, key=lambda x: x[6][:])  # message sorted by vector clock!

    def parse_vector_clock(self, vector_sting: str):
        return [int(x) for x in vector_sting.split(";")]

    def stringify_vector_clock(self, vector: list):
        return ";".join([str(x) for x in vector])

    def encode_message(self, priority,role, msg_type,msg_uuid, ppid, fairness_assertion,sender_clock, payload):
        return create_frame(priority, role=role, message_type=msg_type, msg_uuid=msg_uuid,
                            fairness_assertion=fairness_assertion,
                            sender_clock=self.stringify_vector_clock(self.my_lamport_clock),
                            payload=payload, sender=self.my_id,
                            msg_id=self.message_id_counter).encode('utf-8')

    def send_broadcast(self, message):
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        self.udp_socket.sendto(message, (self.bcn, self.bcp))
        self.message_id_counter += 1  # increment message_id_counter
        self.my_lamport_clock[self.my_id] += 1  # increment vector clock

    def receive_udp_message(self):
        data, addr = self.udp_socket.recvfrom(self.message_max_size)
        data_frame = in_filter(data.decode(), addr)
        # self.holdback_queue.append(in_filter(data.decode(), addr))
        # self.compute_priority()  # sort holdback queue
        return data_frame

    def send_multicast(self, message):
        self.udp_socket.sendto(message, self.multicast_group)
        self.message_id_counter += 1  # increment message_id_counter
        self.my_lamport_clock[self.my_id] += 1  # increment vector clock