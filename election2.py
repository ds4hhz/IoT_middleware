import threading
import uuid
import os
import threading
import time
import queue


class Election(threading.Thread):
    # DYNAMIC DISCOVERY
    # &
    # BULLY ALGORITHM
    def __init__(self, main_ppid, my_ip, communicationchannels):
        self.MY_IP = my_ip
        self.cc = communicationchannels
        self.incoming_pipe = queue.Queue()
        self.outgoing_pipe = queue.Queue()

        # do not start if election is already running...
        self.electionstarted = False
        self.bully_message = "I am alive"

        self.elected = False
        self.PRIMARY = None

        self.election_uuid = uuid.uuid4()
        self.MY_MAIN_PPID = main_ppid
        self.electionstarttime = None
        self.electiontimeout = 5

        self.electionboard = {
            "HOST": [],
            "PPID": [],
            "LAST_ACTIVITY_TIMESTAMP": [],
        }

# --------------------------------------------

    def run(self):
        while True:
            incoming_msg = self.incoming_pipe.get(block=True)

            self._kickhost
            if incoming_msg[2] == "HB":
                pass
            elif incoming_msg[2] == "EL":
                sender = incoming_msg[9]
                for index in range(len(self.electionboard["HOST"])):
                    if self.electionboard["HOST"][index] == sender and self.electionboard["PPID"][index] < self.MY_MAIN_PPID:
                        self._rejectOccupation(incoming_msg[9])
                        try:
                            election = threading.Thread(target=self._rejectOccupation(incoming_msg[9]), args=())
                            election.daemon = True
                            election.start()
                        except Exception:
                            print(Exception)
                        finally:
                            election.stop()
                            election.join()
                    else:
                        self._ackOccupation(incoming_msg[9])
                        try:
                            election = threading.Thread(target=self._rejectOccupation(incoming_msg[9]), args=())
                            election.daemon = True
                            election.start()
                        except Exception:
                            print(Exception)
                        finally:
                            election.stop()
                            election.join()

    def _rejectOccupation(self):

        rejection_frame = [0, "S", "EL", None, None, None, None, self.bully_message, self.MY_IP]
        # implement TCP or UDP-Unicast

    def _ackOccupation(self):
        ack_frame = [0, "S", "EL", None, None, None, None, self.bully_message, self.MY_IP]
        # implement TCP or UDP-Unicast

    def coordinatormessage(self, message):
        # pack message for outgoing channel
        # announce myself as coordinator/primary
        self.outgoing_pipe.put(message)

# ---------- extra/s below -----------

    def _kickhost(self):
        refresh_intervall = 10
        for i in range(0, len(self.electionboard["LAST_ACTIVITY_TIMESTAMP"])):
            if (time.time() - self.electionboard["LAST_ACTIVITY_TIMESTAMP"]) > refresh_intervall:
                del self.electionboard["HOST"][i]
                del self.electionboard["PPID"][i]
                del self.electionboard["LAST_ACTIVITY_TIMESTAMP"][i]

    def updateHeartbeatTime(self, host):

        if host == self.PRIMARY:
            self.lastheartbeatfromprimary = time.time()
        self.heartbeatcatalogue[self.MY_IP] = time.time()
        self.heartbeatcatalogue[host] = time.time()

        # answer/bully election starter - "I AM ALIVE!" & start another election



