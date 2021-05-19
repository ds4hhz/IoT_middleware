import uuid
import os

class Election:

    #BULLY ALGORITHM
    def __init__(self, main_ppid, my_ip, coordinator):
        self.MAIN_PPID = main_ppid
        self.MY_IP = my_ip

        #do not start if election is already started...
        self.electionstarted = False
        self.bully_message = "OBEY ME SUBSERVIENTS!"

        self.election_uuid = uuid.uuid4()
        self.electionstarttime = None
        self.electiontimeout = 5
        self.voteIDs = {
            "voteID": [self.election_uuid],
            "PID": [os.getppid()]
        }


        self.COORDINATOR = coordinator

    # election start
    def startelection(self):
        zip_message = (self.voteIDs)
        return 0

    # answer/bully election starter - "I AM ALIVE!" & start another election
    def inquiry(self):
        pass

    def announcecordinator(self):
        pass

    def handle_election(self, message):
        if message.split("//") not in self.voteIDs["voteID"]:
            self.voteIDs["voteID"].append(message[0])
            self.voteIDs["PID"].append(message[1])

    def clearelectionboard(self):
        self.voteIDs = {
            "voteID": [self.election_uuid],
            "PID": [os.getppid()]
        }
        self.elected = False