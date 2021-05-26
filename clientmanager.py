import threading


class ClientManager(threading.Thread):

    def __init__(self):
        super(ClientManager, self).__init__()
        # key == ip
        #
        self.ECs = []
        self.CCs = []

    def run(self):
        while True:
            pass



    def statechange(self):
        pass

