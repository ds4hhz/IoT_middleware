import threading
import queue
import pipesfilter as pf


class UnicastListener(threading.Thread):

    def __init__(self, cfgs, socket):
        super(UnicastListener, self).__init__()
        self.UNICAST_ADDR = cfgs["machine_ipv4"]
        self.UNICAST_PORT = cfgs["unicast_port"]
        self.configurations = cfgs
        self.socket = socket

        self.mssg_queue = queue.Queue()

    def run(self):
        print("Unicast listening-thread has started...")
        while True:
            data, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
            if data:
                self.mssg_queue.put(pf.in_filter(data.decode("utf-8"), addr))

    def getFromQueue(self):
        return self.mssg_queue.get(block=True)
