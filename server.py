import socket, os
import threading
from configurations import cfg as configurations
from broadcastlistener import BroadcastListener
from multicastreceiver import MulticastListener
from orderedreliablemc import OrderedReliableMulticast
from communicationchannels import Communication
from election import Election
import pipesfilter

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

        self.discovery_thread = []

        # dont send statechange messages if a election is pending (true) => no coordinator probably
        # dont answer to discovery broadcasts

        # w8 for several seconds
        self.pending_election = False

        # configurate communication channels
        self.communicationchannels = Communication(configurations)


        ormc = OrderedReliableMulticast()
        election = Election(os.getppid(), self.cfg["machine_ipv4"], self.communicationchannels)


        # initialize sockets...
        brclistener = BroadcastListener(configurations, self.communicationchannels.get_broadcastlistener())
        brclistener.daemon = True
        mclistener = MulticastListener(configurations, self.communicationchannels.get_multicastlistener())
        mclistener.daemon = True

        try:
            brclistener.start()
            mclistener.start()


            # brclistener.election = True
            while self.running is True:


                if brclistener.mssg_queue.empty() != True:
                    intercepted_broadcast = brclistener.getFromQueue()
                    print("-- pending discovery --")
                    interception_time = time.time()
                    # answer to CC or EC
                    if intercepted_broadcast[2] == "DD" and intercepted_broadcast[1] != "S":
                        # answer to exploratory (CC OR EC)!
                        pass
                    # set election to True if election is pending => @ bully algorithm no future hosts shall join the network for safety reasons
                    elif intercepted_broadcast[2] == "DD" and intercepted_broadcast[1] == "S" and self.pending_election != True:
                        # answer to exploratory (CC OR EC)!
                        pass


                    # ormc.mssg_pipe.put(brclistener.getFromQueue())

                elif mclistener.mssg_queue.empty() != True:
                    intercepted_broadcast = mclistener.getFromQueue()
                    print("-- pending interception --")
                    interception_time = time.time()
                    if intercepted_broadcast[3] in ormc.acked_mssgs:
                        # do nothing if already acknowledged
                        pass
                    elif intercepted_broadcast[3] in ormc.non_acked_mssgs:
                        # acknowledge message as received
                        ormc.non_acked_mssgs[intercepted_broadcast[3]][0] = True
                        election.incoming_pipe.put(intercepted_broadcast, interception_time)

                        # fairness = time.time() - ormc.non_acked_mssgs[intercepted_broadcast[3]][1]
                    elif intercepted_broadcast[2] == "HB" or intercepted_broadcast[2] == "EL ":
                        election.incoming_pipe.put(intercepted_broadcast, interception_time)
                    # answer to CC or EC
                    elif intercepted_broadcast[2] == "DD" and intercepted_broadcast[1] != "S":
                        # answer to exploratory (CC OR EC)!
                        self.communicationchannels.send_msg("udp_unicast", "I AM HERE", intercepted_broadcast[9])

                    # set election to True if election is pending => @ bully algorithm no future hosts shall join the network for safety reasons
                    elif intercepted_broadcast[2] == "DD" and intercepted_broadcast[1] == "S" and self.pending_election != True:
                        # answer to exploratory (CC OR EC)!
                        # not needed to reach reliable delivery of broadcast/discovery responses, since each server answers the discovery...
                        self.communicationchannels.send_msg("udp_unicast", "I AM HERE", intercepted_broadcast[9])

                    # election outgoing pipe to ordered reliable mc pipe
                    #ormc.mssg_pipe.put(mclistener.getFromQueue())


        except Exception as e:
            print(e)

        finally:
            brclistener.stop()
            mclistener.stop()
            brclistener.join()
            mclistener.join()

    def mirror_msg(self):
        pass

