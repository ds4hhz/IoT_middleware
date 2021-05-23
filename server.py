import socket, os
import threading
import uuid

from configurations import cfg as configurations
from broadcastlistener import BroadcastListener
from multicastreceiver import MulticastListener
from orderedreliablemc import OrderedReliableMulticast
from communicationchannels import Communication
from election2 import Election
import pipesfilter

import time
import queue
#toDO: zykliches senden der states an die commanding clients

class Server():

    def __init__(self):

        self.ToS = "S"
        self.ip = configurations["machine_ipv4"]
        self.cfg = configurations
        self.lead = False
        self.running = True
        self.hosts = []
        #self.hosts.append(self.ip)
        self.reliablemcdummylist = []

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
            #DYNAMIC DISCOVERY
            self.dd_uuid = uuid.uuid4()
            print("hi")
            self.communicationchannels.send_bc_socket(
                pipesfilter.create_frame(priority=0,
                                         role="S",
                                         message_type="DD",
                                         msg_uuid=self.dd_uuid,
                                         ppid=0,
                                         fairness_assertion=0,
                                         sender_clock=0,
                                         payload="Who is there?",
                                         sender=self.ip)[0])
            while self.running is True:
                if not brclistener.mssg_queue.empty():
                    intercepted_broadcast = brclistener.getFromQueue()
                    print("-- pending discovery --")
                    interception_time = time.time()
                    # answer to CC or EC
                    if intercepted_broadcast[2] == "DD" and intercepted_broadcast[1] != "S" and intercepted_broadcast[8] != self.ip:
                        # answer to exploratory (CC OR EC)!
                        self.communicationchannels.send_bc_socket(pipesfilter.create_frame(priority=0,
                                                         role="S",
                                                         message_type="ACK",
                                                         msg_uuid=intercepted_broadcast[3],
                                                         ppid=0,
                                                         fairness_assertion=0,
                                                         sender_clock=0,
                                                         payload="I am alive",
                                                         sender=intercepted_broadcast[8])[0])

                    # set election to True if election is pending => @ bully algorithm no future hosts shall join the network for safety reasons
                    elif intercepted_broadcast[2] == "DD" \
                            and intercepted_broadcast[1] == "S" \
                            and self.pending_election != True \
                            and intercepted_broadcast[8] != self.ip:
                        print("hi")
                        print(self.ip)
                        self.communicationchannels.send_bc_socket(pipesfilter.create_frame(priority=0,
                                                 role="S",
                                                 message_type="ACK",
                                                 msg_uuid=intercepted_broadcast[3],
                                                 ppid=0,
                                                 fairness_assertion=0,
                                                 sender_clock=0,
                                                 payload="I am alive",
                                                 sender=intercepted_broadcast[8])[0])

                    elif intercepted_broadcast[3] == self.dd_uuid and intercepted_broadcast[8] not in self.hosts and intercepted_broadcast[8] != self.ip:
                        print(intercepted_broadcast[8])
                        self.hosts.append(intercepted_broadcast[8])

                elif mclistener.mssg_queue.empty() != True:
                    intercepted_mc = mclistener.getFromQueue()
                    print("-- pending interception --")
                    interception_time = time.time()
                    if intercepted_mc[2] == "HB" or intercepted_mc[2] == "EL ":
                        election.incoming_pipe.put(intercepted_mc, interception_time)
                    # answer to CC or EC
                    elif intercepted_mc[2] == "DD" and intercepted_mc[1] != "S":
                        # answer to exploratory (CC OR EC)!
                        self.communicationchannels.send_mc_socket(pipesfilter.create_frame(priority=0,
                                                         role="S",
                                                         message_type="ACK",
                                                         msg_uuid=intercepted_broadcast[3],
                                                         ppid=0,
                                                         fairness_assertion=0,
                                                         sender_clock=0,
                                                         payload="I am alive",
                                                         sender=intercepted_broadcast[8])[0])
                    elif intercepted_mc[3] == self.dd_uuid and intercepted_mc[8] not in self.hosts:
                        self.hosts.append(intercepted_mc[8])

                    # set election to True if election is pending => @ bully algorithm no future hosts shall join the network for safety reasons
                    elif intercepted_mc[2] == "DD" and intercepted_mc[1] == "S" and self.pending_election != True:
                        # answer to exploratory (CC OR EC)!
                        self.communicationchannels.send_mc_socket(pipesfilter.create_frame(priority=0,
                                                                                           role="S",
                                                                                           message_type="ACK",
                                                                                           msg_uuid=
                                                                                           intercepted_broadcast[3],
                                                                                           ppid=0,
                                                                                           fairness_assertion=0,
                                                                                           sender_clock=0,
                                                                                           payload="I am alive",
                                                                                           sender=intercepted_broadcast[
                                                                                               8])[0])



        except Exception as e:
            print(e)

        finally:

            brclistener.join()
            mclistener.join()
            brclistener.stop()
            mclistener.stop()

    def mirror_msg(self):
        pass

