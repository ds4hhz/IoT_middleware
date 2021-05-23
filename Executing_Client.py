from configurations import cfg
import logging
import socket
from Messenger import Messenger
from pipesfilter import create_frame
from pipesfilter import Role
from pipesfilter import MessageType
from pipesfilter import in_filter


class ExecutingClient:
    def __init__(self, address, port, buffer_size, process_id, num_processes):
        self.client_address = address
        self.port_address = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        self.buffer_size = buffer_size
        self.states_dict = {"off": [0, 0, 0], "on": [0, 1, 0], "blinking": [1, 0, 0]}
        self.state = self.states_dict["off"]
        self.messenger_obj = Messenger(process_id=process_id, num_processes=num_processes, ToS=Role.EC,
                                       multicast_group="233.33.33.33", multicast_port=9950,
                                       bcn="192.168.1.255",
                                       bcp=10500)
        # toDo: client id

    def __bind_socket(self):
        self.socket.bind((self.client_address, self.port_address))

    def receive_message(self):
        data, address = self.socket.recvfrom(2048)
        self.holdback_queue.append(in_filter(data.decode(), address))


    def send_process_id(self):
        msg = self.messenger_obj.encode_message(priority=1, msg_type=MessageType.dynamic_discovery,
                                                fairness_assertion=1,
                                                ec_address=None, statement=None)
        self.messenger_obj.send_broadcast(message=msg)
        # ToDo: send process id / broadcast for dynamic discovery

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
