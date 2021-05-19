import socket, os
import threading
from configurations import cfg as configurations
from broadcastlistener import BroadcastListener
from multicastreceiver import MulticastListener
from communicationchannels import Communication
import time
import queue

class Server():

    def __init__(self):

        self.ToS = "S"
        self.ip = configurations["machine_ipv4"]
        self.cfg = configurations
        self.lead = False
        self.running = True
        self.hosts = []
        self.hosts.append(self.ip)

        self.discovery_threads = []

        # dont send statechange messages if a election is pending (true) => no coordinator probably
        # dont answer to discovery broadcasts
        self.pending_election = False

        # configurate communication channels
        self.communicationchannels = Communication(configurations)




        # initialize sockets...
        brclistener = BroadcastListener(configurations, self.communicationchannels.get_broadcastlistener())
        brclistener.daemon = True

        mclistener = MulticastListener(configurations, self.communicationchannels.get_multicastlistener())
        mclistener.daemon = True

        try:
            brclistener.start()
            mclistener.start()

            # set election to True if election is pending => @ bully algorithm no future hosts shall join the network
            # brclistener.election = True
            while self.running is True:

                if brclistener.mssg_queue.empty() != True:

                    print(brclistener.getFromQueue())
                elif mclistener.mssg_queue.empty() != True:

                    print(mclistener.getFromQueue())


        except Exception as e:
            print(e)

        finally:
            brclistener.join()
            brclistener.join()




        #group of servers
        multicastgroup = []


# broadcastlistening
# multicastlistening
# tcp between server(primary) and executing client



"""if __name__ == "__main__":
    p = Process(target=run, args=("DS",))
    p.daemon =True
    p.start()
    p.join()"""