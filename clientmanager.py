import threading


class ClientManager(threading.Thread):

    def __init__(self):
        super(ClientManager, self).__init__()
        self.clock = 0
        # key == ip
        #structure => {"executing_client_ip": state}
        self.ECs = {}
        # structure => {"commanding_client_ip": pending_state_change_request(True or False)}
        self.CCs = {}


        self.statechange_reqs = {}
        self.confirmed_statechanges = {}

    def run(self):
        while True:
            pass



    def statechange(self):
        # if primary
        # received statechange => statechange to executing_client
        # w8 until executing ACKs state
        # if acked mirror state with clocktime to replicas
        pass

