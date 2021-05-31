import threading
import time
import uuid
from communicationchannels import Communication
from configurations import cfg
import pipesfilter


class HeartbeatThread(threading.Thread):

    def __init__(self, hb, cc, suuid):
        super(HeartbeatThread, self).__init__()
        self.hostsboard = hb
        self.communicationchannels = cc
        self.server_uuid = suuid


    def run(self):
        while True:
                time.sleep(cfg["hb_intervall"])
                self.__hearbeat()

    def __hearbeat(self):
        if self.hostsboard.elected == True and len(self.hostsboard.electionboard["HOST"]) != 0:
            for host in self.hostsboard.electionboard["HOST"]:
                self.communicationchannels.send_udp_unicast(
                    pipesfilter.create_frame(priority=0,
                                             role="S",
                                             message_type="HB",
                                             msg_uuid=uuid.uuid4(),
                                             ppid=self.server_uuid,
                                             fairness_assertion=0,
                                             sender_clock=0,
                                             payload="I am Alive",
                                             sender=str(cfg["machine_ipv4"]))[0], host)

    def rej(self):
        self.communicationchannels.send_mc_socket(
            pipesfilter.create_frame(priority=0,
                                     role="S",
                                     message_type="HB",
                                     msg_uuid=uuid.uuid4(),
                                     ppid=self.server_uuid,
                                     fairness_assertion=0,
                                     sender_clock=0,
                                     payload="I am Alive",
                                     sender=str(cfg["machine_ipv4"]))[0])

    def updateHostboard(self, electionboard):
        self.hostsboard = electionboard
