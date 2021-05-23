import socket
from pipesfilter import create_frame
from queue import PriorityQueue
from broadcastsender import BroadcastSender
from broadcastlistener import BroadcastListener
from multicastsender import MulticastSender
from multicastreceiver import MulticastListener


class MulticastSender:
    def __init__(self, process_id: int, multicast_group: str, port: int, num_processes: int, ToS: str):
        self.my_id = process_id
        self.ToS = ToS
        self.port = port
        self.multicast_group = (multicast_group, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.message_max_size = 4096
        self.message_id_counter = 0

        self.has_received = {}
        self.has_acknowledged = {}  # saves acknowledged messages
        self.unack_messages = []  # messages with pending acknowledgement
        self.holdback_queue = []

        self.holdback_sequence_counter = 0
        self.sequence_counter = 0
        self.SEQUENCER_ID = 0

        self.queue = PriorityQueue()
        self.my_vector_clock = [0] * num_processes

        self.broadcast_sender_obj = BroadcastSender()

    def parse_vector_clock(self, vector_sting: str):
        return [int(x) for x in vector_sting.split(";")]

    def stringify_vector_clock(self, vector: list):
        return ";".join([str(x) for x in vector])

    def encode_message(self, priority, msg_type, fairness_assertion, ec_address, statement):
        return create_frame(priority, role=self.ToS, message_type=msg_type, msg_uuid=self.message_id_counter,
                            fairness_assertion=fairness_assertion,
                            sender_clock=self.stringify_vector_clock(self.my_vector_clock),
                            ec_address=ec_address,
                            statement=statement, sender=self.my_id,
                            msg_id=self.message_id_counter).encode('utf-8')

    def send_broadcast(self, message):
        self.broadcast_sender_obj.broadcast(message)

    def send_multicast(self, message):
        self.sock.sendto(message, self.multicast_group)
