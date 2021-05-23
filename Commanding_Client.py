import broadcastsender


class CommandingClient:
    def __init__(self,executing_clients_list):
        self.states_list = ["off", "on", "blinking"]
        self.executing_clients_list = executing_clients_list
