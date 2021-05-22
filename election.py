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
        # {"host_ip":"lastheartbeat"}
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
                del self.voteIDs["ELECTED"][i]
                del self.voteIDs["ELECTIONTIMESTAMP"][i]




        self.elected = False
        self.discovery_initiated = False

    def run(self):
        # watch for hearbeats from primary and start election
        while True:
            if self.electionstarted != True:
                self.updateHeartbeatTime(self.incoming_pipe.get(block=True))
            time.sleep(1.5)
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
            message = self.incoming_pipe.get(block=True)
            #self.updateHeartbeatTime(self)
            if self.PRIMARY == None and self.discovery_initiated != True:
                self.discovery_initiated = True
                self.electionmessage(message)




            elif message[0] == "EM":
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
                self.voteIDs["voteID"].append(message[0])
                self.voteIDs["PID"].append(message[1])
                self.voteIDs["ELECTED"].append(message[2])
                self.voteIDs["ELECTIONTIMESTAMP"].append(message[3])
            else:
                print("Election is already known.")
        except Exception as e:
            print(e)

    def coordinatormessage(self, message):
        # pack message for outgoing channel
        # announce myself as coordinator/primary
        self.outgoing_pipe.put(message)


