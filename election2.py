import uuid

import threading
import time
import queue
import pipesfilter
from configurations import cfg


class Election(threading.Thread):
    # DYNAMIC DISCOVERY
    # &
    # BULLY ALGORITHM
    def __init__(self, server_uuid, my_ip, communicationchannels):
        super(Election, self).__init__()
        self.MY_IP = my_ip
        self.cc = communicationchannels
        self.incoming_pipe = queue.Queue()
        self.outgoing_pipe = queue.Queue()

        # do not start if election is already running...
        self.electionstarted = False
        self.hold = False
        self.candidate = False
        self.serverstarttime = time.time()

        self.elected = False
        self.PRIMARY = ""
        self.electionblock = 20

        self.lastheartbeatfromprimary = time.time()
        self.election_uuid = uuid.uuid4()
        self.MY_SERVER_UUID = server_uuid
        self.electionstarttime = None
        self.electiontimeout = 5
        self.holdtimeout = 3

        self.electionboard = {
            "HOST": [],
            "PPID": [],
            "HIGHER_UUIDS": [],
            "ELECTIONS": {},
            "LEAD_CONFIRMATIONS": []
        }






# --------------------------------------------

    def run(self):

        #print("before start")
        #heartbeat.start()
        while True:
            time.sleep(4)
            print("I Am King: "+ str(self.elected))
            self.__watchprimary()
            self.__watchACKS()
            ##self._kickhost()

            if self.electionstarted == True and self.hold != True and (float(time.time())-self.electionstarttime) > cfg["hb_timeout"] and len(self.electionboard["ELECTIONS"]) == 0 and False in self.electionboard["CONFIRMATIONS"]:
                self.coordinatormessage()
                if not False in self.electionboard["LEAD_CONFIRMATIONS"]:
                    self.elected = True
                    for _ in self.electionboard["LEAD_CONFIRMATIONS"]:
                        _ = False
                    self.hold = False
            else:
                self.coordinatormessage()
                self.elected


            if len(self.electionboard["HOST"]) != 0:
                self.compareHosts()

            if self.hold == True and (float(time.time()) - float(self.electionstarttime)) > cfg["hb_timeout"]:
                self.elected = True




            if not self.incoming_pipe.empty():
                incoming_msg = self.incoming_pipe.get(block=True)
                if incoming_msg[2] == "HB" and incoming_msg[8] == self.PRIMARY:
                    self.lastheartbeatfromprimary = time.time()
                if incoming_msg[2] == "HB" and incoming_msg[2] == "S" and incoming_msg[8] != str(self.MY_IP):
                    print("hi")

                    self.electionboard["LAST_ACTIVITY_TIMESTAMP"][self.electionboard["HOST"].index(incoming_msg[8])] = time.time()
                if incoming_msg[2] == "EL" and incoming_msg[8] != self.MY_IP:

                    if incoming_msg[7] == "ELECTION STARTED" and incoming_msg[4] < str(self.MY_SERVER_UUID):
                        self._ackAlive(incoming_msg[8])
                        self.election()
                        self.electionstarted = True
                    if incoming_msg[7] == "ELECTION STARTED" and incoming_msg[4] > str(self.MY_SERVER_UUID):
                        self._ackAlive(incoming_msg[8])

                    if incoming_msg[7] == "COORDINATOR" and incoming_msg[4] > str(self.MY_SERVER_UUID) and incoming_msg[8] in self.electionboard["HOST"]:
                        self._ackLead(incoming_msg[8])
                        self.PRIMARY = incoming_msg[8]

                    if incoming_msg[7] == "COORDINATOR" and incoming_msg[4] < str(self.MY_SERVER_UUID):
                        self.election()

                    if incoming_msg[7] == "OK" and incoming_msg[4] > str(self.MY_SERVER_UUID):
                        self.PRIMARY = ""

                    if incoming_msg[7] == "OK" and incoming_msg[4] > str(self.MY_SERVER_UUID):
                        self._ackLead(incoming_msg[8])
                        self.PRIMARY = ""










    def election(self):
        self.electionstarttime = time.time()
        self.electionstarted = True
        self.PRIMARY = ""
        print("election has started...")
        if self.electionboard["HOST"] != 0:
            for host in self.electionboard["HOST"]:
                if self.electionboard["HIGHER_UUIDS"][self.electionboard["HOST"].index(host)] == True:
                    self.electionboard["ELECTION"][host] = False
                    self.cc.send_udp_unicast(
                        pipesfilter.create_frame(priority=0,
                                                 role="S",
                                                 message_type="EL",
                                                 msg_uuid=uuid.uuid4(),
                                                 ppid=self.MY_SERVER_UUID,
                                                 fairness_assertion=0,
                                                 sender_clock=0,
                                                 payload="Are you Alive?",
                                                 sender=str(cfg["machine_ipv4"]))[0], host)


    def _ackLead(self, receiver):
        self.cc.send_udp_unicast(
            pipesfilter.create_frame(priority=0,
                                     role="S",
                                     message_type="EL",
                                     msg_uuid=uuid.uuid4(),
                                     ppid=self.MY_SERVER_UUID,
                                     fairness_assertion=0,
                                     sender_clock=0,
                                     payload="LEAD OK",
                                     sender=str(cfg["machine_ipv4"]))[0], receiver)

    def _ackAlive(self, receiver):
        self.cc.send_udp_unicast(
            pipesfilter.create_frame(priority=0,
                                     role="S",
                                     message_type="EL",
                                     msg_uuid=uuid.uuid4(),
                                     ppid=self.MY_SERVER_UUID,
                                     fairness_assertion=0,
                                     sender_clock=0,
                                     payload="OK",
                                     sender=str(cfg["machine_ipv4"]))[0], receiver)



    def coordinatormessage(self):
        self.cc.send_mc_socket(
            pipesfilter.create_frame(priority=0,
                                     role="S",
                                     message_type="EL",
                                     msg_uuid=uuid.uuid4(),
                                     ppid=self.MY_SERVER_UUID,
                                     fairness_assertion=0,
                                     sender_clock=0,
                                     payload="COORDINATOR",
                                     sender=str(cfg["machine_ipv4"]))[0])


    def compareHosts(self):
        for uuid in self.electionboard["PPID"]:
            if str(self.MY_SERVER_UUID) < uuid:
                self.electionboard["HIGHER_UUIDS"][self.electionboard["PPID"].index(uuid)] = True

    def __watchprimary(self):
        # if first server in network, then initiate an election
        if self.PRIMARY == "" and (float(time.time()) - float(self.serverstarttime)) > 20 and self.electionstarted == False:
            self.election()

        if (time.time() - float(self.lastheartbeatfromprimary)) > cfg["hb_timeout"] and self.PRIMARY != "":
            self.electionstarted = True
            self.electionstarttime = time.time()

            for host in self.electionboard["HOST"]:
                if self.electionboard["HIGHER_UUIDS"][self.electionboard["HOST"].index(host)] == True:
                    self.cc.send_udp_unicast(
                        pipesfilter.create_frame(priority=0,
                                                 role="S",
                                                 message_type="EL",
                                                 msg_uuid=uuid.uuid4(),
                                                 ppid=self.MY_SERVER_UUID,
                                                 fairness_assertion=0,
                                                 sender_clock=0,
                                                 payload="ELECTION STARTED",
                                                 sender=str(cfg["machine_ipv4"]))[0], host)
                    self.electionboard["ELECTIONS"][host] = False

    def __watchACKS(self):
        if self.electionstarted == True and len(self.electionboard["ELECTIONS"]) != 0:
            if True in self.electionboard["ELECTIONS"]:
                self.hold = True

    def __coordinatorACKhandler(self):
        pass

# ---------- extra/s below -----------

    def _kickhost(self):
        refresh_intervall = 10
        for i in range(0, len(self.electionboard["LAST_ACTIVITY_TIMESTAMP"])):
            if (time.time() - self.electionboard["LAST_ACTIVITY_TIMESTAMP"]) > refresh_intervall:
                del self.electionboard["HOST"][i]

