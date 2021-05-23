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
        self.MY_MAIN_PPID = main_ppid
        self.MY_IP = my_ip
        self.cc = communicationchannels
        self.incoming_pipe = queue.Queue()
        self.outgoing_pipe = queue.Queue()


        self.lastheartbeatfromprimary = time.time()
        #do not start if election is already running...
        self.electionstarted = False
        self.bully_message = "I am alive"
        self.discovery_initiated = False
        self.elected = False

        self.election_uuid = None
        self.electionstarttime = None
        self.electiontimeout = 5

        self.voteIDs = {
            "voteID": [self.election_uuid],
            "PID": [self.MY_MAIN_PPID],
            "ELECTED": [],
            "ELECTIONTIMESTAMP": [],
        }
        # {"host_ip": time.time()}
        self.heartbeatcatalogue = {

        }
        self.PRIMARY = None

    def clearelectionboard(self):
        self.election_uuid = None
        refresh_intervall = 10
        for i in range(0, len(self.voteIDs["ELECTIONTIMESTAMP"])):
            if (time.time() - self.voteIDs["ELECTIONTIMESTAMP"]) > refresh_intervall:
                del self.voteIDs["voteID"][i]
                del self.voteIDs["PID"][i]
                del self.voteIDs["ELECTIONTIMESTAMP"][i]

        self.elected = False
        self.discovery_initiated = False

    def run(self):
        if self.PRIMARY == None:
            try:
                election = threading.Thread(target=self.startelection, args=())
                election.daemon = True
                election.start()
            except Exception:
                print(Exception)
            finally:
                election.stop()
                election.join()

        # watch for hearbeats from primary and start election
        while True:
            # ALSO DYNAMIC DISCOVERY PURPOSE:

            incoming_msg = self.incoming_pipe.get(block=True)
            if self.electionstarted != True:
                self.updateHeartbeatTime(incoming_msg)

            if ((time.time() - self.lastheartbeatfromprimary) > self.electiontimeout-1.5) and (self.PRIMARY != self.MY_IP) and self.electionstarted != True:
                try:
                    election = threading.Thread(target=self.startelection, args=())
                    election.daemon = True
                    election.start()
                except Exception:
                    print(Exception)
                finally:
                    election.stop()
                    election.join()



    def updateHeartbeatTime(self, host):

        if host == self.PRIMARY:
            self.lastheartbeatfromprimary = time.time()
        self.heartbeatcatalogue[self.MY_IP] = time.time()
        self.heartbeatcatalogue[host] = time.time()

        # answer/bully election starter - "I AM ALIVE!" & start another election

    def startelection(self):
        self.electionstarted = True
        self.electionstarttime = time.time()

        while self.electionstarted == True:
            if self.incoming_pipe.empty() != True:
                message = self.incoming_pipe.get(block=True)
            if message[2] == "HB":
                self.updateHeartbeatTime(self, message[9])
            electionid = uuid.uuid4()
            announce_myself_frame = [0, "S", "EL", electionid, None, None, None, self.bully_message, self.MY_IP]
            self.electionmessage(announce_myself_frame)




            if message[0] == "EL":
                self.handle_election_message(message)

            if time.time() - self.electionstarttime > self.electiontimeout:
                self.coordinatormessage(message)

    # inquiry
    def electionmessage(self, message):
        electionid = uuid.uuid4()
        self.outgoing_pipe.put((message, electionid))




    def handle_election_message(self, message):
        try:
            if message[0] not in self.voteIDs["voteID"]:
                self.voteIDs["voteID"].append(message[3])
                self.voteIDs["PID"].append(message[4])
                self.voteIDs["ELECTIONTIMESTAMP"].append(message[3])
            else:
                print("Election is already known.")
        except Exception as e:
            print(e)

    def coordinatormessage(self, message):
        # pack message for outgoing channel
        # announce myself as coordinator/primary
        self.outgoing_pipe.put(message)


