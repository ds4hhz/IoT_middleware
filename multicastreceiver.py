import threading
import queue
import pipesfilter as pf


class MulticastListener(threading.Thread):

    def __init__(self, cfgs, mc_socket):
        super(MulticastListener, self).__init__()
        self.MCAST_GRP = cfgs["multicast_group"]
        self.MCAST_PORT = cfgs["multicast_group"]
        self.socket = mc_socket

        self.mssg_queue = queue.Queue()



    def run(self):
        print("Multicast listening-thread has started...")
        try:
            while True:
                data, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
                if data:
                    # incoming frame...
                    # self.mssg_queue.put([addr,  data.decode()])
                    self.mssg_queue.put(pf.in_filter(data.decode(), addr))
                    print("MC")
        except Exception as e:
            print(e)

    def getFromQueue(self):
        return self.mssg_queue.get(block=True)




