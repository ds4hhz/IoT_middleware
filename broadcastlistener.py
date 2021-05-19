import socket
import threading
import queue


class BroadcastListener(threading.Thread):

    def __init__(self, cfgs, socket):
        super(BroadcastListener, self).__init__()
        self.BROADCAST_ADDR = cfgs["brc_addr"]
        self.BROADCAST_PORT = cfgs["brc_port"]
        self.configurations = cfgs
        self.socket = socket

        self.mssg_queue = queue.Queue()
        self.mutex = threading.Lock()

    def run(self):
        print("Broadcast listening-thread has started...")
        try:
            while True:
                data, addr = self.socket.recvfrom(1024)
                if data:
                    # incoming frame...
                    self.mssg_queue.put((addr,  data.decode()))

        except Exception as e:
            print(e)

    def getFromQueue(self):
        return self.mssg_queue.get(block=True)


# ---------- for testing purposes below -------------

if __name__ == '__main__':
    # Listening port
    BROADCAST_PORT = 10500

    # Local host information
    MY_HOST = socket.gethostname()
    #MY_IP = socket.gethostbyname(MY_HOST)
    MY_IP = "192.168.1.255"
    print("Listening on broadcasts: "+ MY_IP + ":"+ str(BROADCAST_PORT))
    # Create a UDP socket
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the socket to broadcast and enable reusing addresses
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind socket to address and port
    listen_socket.bind((MY_IP, BROADCAST_PORT))

    print("Listening to broadcast messages")

    while True:
        data, addr = listen_socket.recvfrom(1024)
        if data:
            print("Received broadcast message from:" + str(addr), data.decode())
