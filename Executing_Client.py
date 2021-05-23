from configurations import cfg
import logging
import socket
from broadcastsender import BroadcastSender
from pipesfilter import create_frame


class ExecutingClient:
    def __init__(self, address, port, buffer_size):
        self.client_address = address
        self.port_address = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        self.buffer_size = buffer_size
        self.states_dict = {"off": [0, 0, 0], "on": [0, 1, 0], "blinking": [1, 0, 0]}
        self.state = self.states_dict["off"]
        self.broadcast_sender_obj = BroadcastSender(tos="EC", bcn="192.168.1.255")
        # toDo: client id

    def __bind_socket(self):
        self.socket.bind((self.client_address, self.port_address))

    def receive_message(self):
        pass

    def send_process_id(self):
        self.broadcast_sender_obj.broadcast(message=create_frame(0, "EC", "dynamic_discovery", ))
        pass  # ToDo: send process id / broadcast for dynamic discovery

    def __state_change(self, state_request):
        if state_request in self.states_dict:
            self.state = self.states_dict[state_request]
        else:
            logging.ERROR(
                'state request was not possible! Possible states are "off, on, blinking" ->state has not changed!')

    def __send_ack(self, address):
        self.socket.sendto("state change to: {}".format(self.state), address)

    def __check_state(self):
        state_index = self.state.index(1)
        if state_index == 0:
            self.__off()
        elif state_index == 1:
            self.__on()
        elif state_index == 2:
            self.__blinking()
        else:
            logging.ERROR("No valid state!")

    def __off(self):
        print("client is off")

    def __on(self):
        print(("client is on"))

    def __blinking(self):
        print("client is blinking")

    def run(self):
        self.__bind_socket()
        while (True):
            data, address = self.socket.recvfrom(self.buffer_size)
            self.__state_change(state_request=data.decode())
            self.__send_ack(address=address)
            self.__check_state()
