import os
import threading
import uuid

from configurations import cfg as configurations
from broadcastlistener import BroadcastListener
from multicastreceiver import MulticastListener
from orderedreliablemc import OrderedReliableMulticast
from communicationchannels import Communication
from election2 import Election
import pipesfilter
from dynamicdiscovery import DynamicDiscovery

import time
import queue


# toDO: zykliches senden der states an die commanding clients

class Server:

    def __init__(self):

        self.ToS = "S"
        self.ip = configurations["machine_ipv4"]
        self.cfg = configurations
        self.lead = False
        self.running = True
        self.my_ppid = os.getppid()

        # dont send statechange messages if a election is pending (true) => no coordinator probably
        # dont answer to discovery broadcasts

        # w8 for several seconds
        self.pending_election = False

        # configurate communication channels
        self.communicationchannels = Communication(configurations)

        ormc = OrderedReliableMulticast()

        self.server_uuid = uuid.uuid4()

        # initialize sockets...
        brclistener = BroadcastListener(configurations, self.communicationchannels.get_broadcastlistener())
        brclistener.daemon = True
        mclistener = MulticastListener(configurations, self.communicationchannels.get_multicastlistener())
        mclistener.daemon = True

        self.discovery = DynamicDiscovery(self.server_uuid, self.my_ppid, self.communicationchannels)
        self.discovery.daemon = True
        election = Election(self.server_uuid, self.ip, self.communicationchannels)
        election.daemon = True

        brclistener.start()
        mclistener.start()
        self.discovery.start()
        election.start()
        try:
            while self.running is True:
                time.sleep(2)
                print("my server uuid " + str(self.server_uuid))
                print(election.electionboard)
                #self.pending_election = election.electionstarted

                if not brclistener.mssg_queue.empty():
                    intercepted_broadcast = brclistener.getFromQueue()
                    print(intercepted_broadcast)
                    # answer to CC or EC
                    if intercepted_broadcast[2] == "DD" \
                            and intercepted_broadcast[1] != "S":
                        self.discovery.answerToClients(intercepted_broadcast)

                    # set election to True if election is pending
                    # => @ bully algorithm no future hosts shall join the network for safety reasons
                    if intercepted_broadcast[2] == "DD" \
                            and intercepted_broadcast[1] == "S" \
                            and self.pending_election is not True \
                            and intercepted_broadcast[4] not in election.electionboard["PPID"]:
                        self.discovery.answerToHosts(intercepted_broadcast)

                    if intercepted_broadcast[1] == "S" \
                            and intercepted_broadcast[8] != self.ip \
                            and intercepted_broadcast[8] not in election.electionboard["HOST"]\
                            and self.pending_election is not True:
                        election.electionboard["HOST"].append(intercepted_broadcast[8])
                        election.electionboard["PPID"].append(
                            intercepted_broadcast[3])  # append uuid instead ppid => more unique
                        election.electionboard["LAST_ACTIVITY_TIMESTAMP"].append(time.time())
                        election.electionboard["SIGNED"].append(False)
                        self.discovery.setHostCount(len(election.electionboard["HOST"]))

#               -----------------------------------------------------------------------------------------------------

                if mclistener.mssg_queue:
                    intercepted_mc = mclistener.getFromQueue()
                    print("-- pending interception --")
                    interception_time = time.time()
                    if intercepted_mc[2] == "HB" or intercepted_mc[2] == "EL":
                        election.incoming_pipe.put(intercepted_mc, interception_time)
                        if intercepted_mc[8] in election.electionboard["HOST"]:
                            election.electionboard["LAST_ACTIVITY_TIMESTAMP"][election.electionboard["HOST"].index(intercepted_mc[8])] = time.time()




        except Exception as e:
            print(e)

        finally:
            brclistener.join()
            mclistener.join()
            self.discovery.join()
            election.join()

            brclistener.stop()
            mclistener.stop()
            self.discovery.stop()
            election.join()
        # hearbeat_thread.join()
        # hearbeat_thread.stop()

    def mirror_msg(self):
        pass

