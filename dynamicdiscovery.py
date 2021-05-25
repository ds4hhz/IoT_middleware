import threading
import time
import uuid

import pipesfilter
from configurations import cfg as configurations


class DynamicDiscovery(threading.Thread):

    def __init__(self, suuid, ppid, cc):
        super(DynamicDiscovery, self).__init__()
        self.hc = 0
        self.server_uuid = suuid
        self.my_ppid = ppid
        self.communicationchannels = cc
        self.ip = configurations["machine_ipv4"]
        self.lts = 1

    def run(self):
        while True:
            time.sleep(10)
            self.send_mssg()

    def send_mssg(self):
        self.communicationchannels.send_bc_socket(
            pipesfilter.create_frame(priority=0,
                                     role="S",
                                     message_type="DD",
                                     msg_uuid=str(uuid.uuid4()),
                                     ppid=self.server_uuid,
                                     fairness_assertion=0,
                                     sender_clock=0,
                                     payload="Who is there?",
                                     sender=self.ip)[0])

    def answerToHosts(self, frame):
        self.communicationchannels.send_bc_socket(pipesfilter.create_frame(priority=0,
                                                                             role="S",
                                                                             message_type="ACK",
                                                                             msg_uuid=frame[3],
                                                                             ppid=self.server_uuid,
                                                                             fairness_assertion=0,
                                                                             sender_clock=0,
                                                                             payload="I am alive",
                                                                             sender=None)[0])

    def answerToClients(self, frame):
        # answer to exploratory (CC OR EC)!
        if (frame[1] == "CC" or frame[1] == "EC") and frame[2] == "DD":
            self.communicationchannels.send_bc_socket(pipesfilter.create_frame(priority=0,
                                                                                 role="S",
                                                                                 message_type="ACK",
                                                                                 msg_uuid=uuid.uuid4(),
                                                                                 ppid=self.my_ppid, # clients shall not see the uuid of the server
                                                                                 fairness_assertion=0,
                                                                                 sender_clock=0,
                                                                                 payload="I am alive",
                                                                                 sender=None)[0])

    def setHostCount(self, count):
        self.hc = count
