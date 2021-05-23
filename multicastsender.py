import socket
from queue import PriorityQueue

# UDP_IP = "127.0.0.1"
# UDP_PORT = 5005

UDP_IP = "233.33.33.33"
UDP_PORT = 9950

MESSAGE = b"Hello, World!"

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

# Internet # UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# workaround broadcasting...
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))


class MulticastSender:
    def __init__(self, multicast_group: str, port: int, num_processes: int):
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
        self.my_timestamp = [0] * num_processes

    def __create_message(self, message_list: list):
        return ",".join([str(x) for x in message_list])

    def send_message(self, message):
        self.sock.sendto(message, self.multicast_group)
