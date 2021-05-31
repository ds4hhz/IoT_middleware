import os
import uuid

from configurations import cfg as configurations
from broadcastlistener import BroadcastListener
from multicastreceiver import MulticastListener
from orderedreliablemc import OrderedReliableMulticast
from communicationchannels import Communication
from election2 import Election
import pipesfilter
from dynamicdiscovery import DynamicDiscovery
from unicastlistener import UnicastListener
from heartbeat import HeartbeatThread

import time


# toDO: zykliches senden der states an die commanding clients

class Server:

    def __init__(self):
        self.stateclock = 0
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
        self.lastheartbeatsend = 0

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
        self.election = Election(self.server_uuid, self.ip, self.communicationchannels)
        self.election.daemon = True
        self.unicastlistener = UnicastListener(configurations, self.communicationchannels.get_multicastlistener())
        self.unicastlistener.daemon = True
        self.heartbeat_thread = HeartbeatThread(self.election.electionboard, self.communicationchannels, self.server_uuid, election)

        self.unicastlistener.start()
        brclistener.start()
        mclistener.start()
        self.discovery.start()
        self.election.start()

        try:
            while self.running is True:

                # self.heartbeat_thread.updateHostboard(self.election.electionboard["HOST"])
                #print(self.discovery.hc)
                #print(self.election.electionboard)

                if not brclistener.mssg_queue.empty():
                    intercepted_broadcast = brclistener.getFromQueue()
                    # answer to CC or EC
                    if intercepted_broadcast[2] == "DD" \
                            and (intercepted_broadcast[1] == "CC" or intercepted_broadcast[1] == "EC"):
                        self.discovery.answerToClients(intercepted_broadcast)

                    # set election to True if election is pending
                    # => @ bully algorithm no future hosts shall join the network for safety reasons
                    if intercepted_broadcast[2] == "DD" \
                            and intercepted_broadcast[1] == "S" \
                            and intercepted_broadcast[8] != str(self.ip) \
                            and self.pending_election is not True \
                            and intercepted_broadcast[4] not in self.election.electionboard["PPID"]:
                        self.discovery.answerToHosts(intercepted_broadcast)
                        self.election.electionboard["HOST"].append(intercepted_broadcast[8])
                        self.election.electionboard["PPID"].append(
                            intercepted_broadcast[4])  # append uuid instead ppid => more unique
                        self.election.electionboard["LAST_ACTIVITY_TIMESTAMP"].append(time.time())
                        self.election.electionboard["HIGHER_UUIDS"].append(False)
                        self.discovery.setHostCount(len(self.election.electionboard["HOST"]))

                    if intercepted_broadcast[1] == "S" \
                            and intercepted_broadcast[2] == "ACK" \
                            and intercepted_broadcast[8] != str(self.ip) \
                            and intercepted_broadcast[4] != str(self.server_uuid) \
                            and intercepted_broadcast[8] not in self.election.electionboard["HOST"] \
                            and self.pending_election != True:
                        self.election.electionboard["HOST"].append(intercepted_broadcast[8])
                        self.election.electionboard["PPID"].append(
                            intercepted_broadcast[4])  # append uuid instead ppid => more unique
                        self.election.electionboard["LAST_ACTIVITY_TIMESTAMP"].append(time.time())
                        self.election.electionboard["HIGHER_UUIDS"].append(False)
                        self.election.electionboard["LEAD_CONFIRMATIONS"].append(False)
                        self.discovery.setHostCount(len(self.election.electionboard["HOST"]))

                #   -----------------------------------------------------------------------------------------------------

                if not mclistener.mssg_queue.empty():
                    intercepted_mc = mclistener.getFromQueue()
                    if (intercepted_mc[2] == "HB" or intercepted_mc[2] == "EL") and intercepted_mc[8] != str(self.ip):
                        self.election.incoming_pipe.put(intercepted_mc)
                        print(intercepted_mc)

                #   -----------------------------------------------------------------------------------------------------

                if not self.unicastlistener.mssg_queue.empty():
                    intercepted_unicast = self.unicastlistener.getFromQueue()
                    if (intercepted_unicast[2] == "HB" or intercepted_unicast[2] == "EL") and intercepted_unicast[8] != str(self.ip):
                        self.election.incoming_pipe.put(intercepted_unicast)
                        print(intercepted_unicast)


        except Exception as e:
            print(e)

        finally:
            brclistener.join()
            mclistener.join()
            self.discovery.join()
            self.election.join()
            self.unicastlistener.join()

            brclistener.stop()
            mclistener.stop()
            self.discovery.stop()
            self.election.join()
            self.unicastlistener.stop()
            # self.heartbeat_thread.join()
            # self.heartbeat_thread.stop()

    def mirror_msg(self):
        pass

    """def __hearbeat(self):
        if float(time.time()) - float(self.lastheartbeatsend) > 2 and self.election.elected == True and len(self.election.electionboard["HOST"]) !=0:
            self.lastheartbeatsend = time.time()
            print("last hearbeattime: " + str(self.lastheartbeatsend))
            for host in self.election.electionboard["HOST"]:
                self.communicationchannels.send_udp_unicast(
                    pipesfilter.create_frame(priority=0,
                                             role="S",
                                             message_type="HB",
                                             msg_uuid=uuid.uuid4(),
                                             ppid=self.server_uuid,
                                             fairness_assertion=0,
                                             sender_clock=0,
                                             payload="I am Alive",
                                             sender=str(self.cfg["machine_ipv4"]))[0], host)
"""