from threading import Thread

import logging
import socket
from pipesfilter import create_frame
from pipesfilter import in_filter
import uuid
import struct
import sys
import json
import time
import sched


class ExecutingClient:
    def __init__(self, address='', port=11000, buffer_size=2048, multicast_group='224.3.29.71',
                 multicast_port=10000):
        self.client_address = address
        self.client_port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
        self.buffer_size = buffer_size
        self.state_list = ["off", "on", "blinking"]
        self.state = self.state_list[0]
        self.uuid = uuid.uuid4()
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.my_lamport_clock = 0
        self.communication_partner = ""  # Not in use

        # heartbeat on server
        # heartbeat
        self.heartbeat_period = 3
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(self.heartbeat_period, 1, self.__send_heartbeat)

    def __bind_socket(self):
        print("open TCP socket: ", (self.client_address, self.client_port))
        self.socket.bind((self.client_address, self.client_port))
        self.socket.listen(1)
        conn, addr = self.socket.accept()
        return conn, addr

    def __tcp_listener(self):
        print("open TCP socket: ", (self.client_address, self.client_port))
        self.socket.bind((self.client_address, self.client_port))
        self.tcp_socket.listen(20)  # allows 1 CCs
        while True:
            CC_conn, CC_addr = self.tcp_socket.accept()
            print("EC accept new server connection!")
            thread = Thread(target=self.__handle_tcp_communication, args=(CC_conn, CC_addr))
            thread.start()

    def __handle_tcp_communication(self,conn, addr):
        while (True):
            try:
                data = conn.recvfrom(self.buffer_size)
            except:
                pass    # leading server has died! #ToDo: create new connection to leading server!
            if (len(data[0]) == 0):
                conn.close()
                time.sleep(1)
                self.socket.listen(1)
                conn, addr = self.socket.accept()
                continue
            else:
                data_frame = in_filter(data[0].decode(), addr)
                # print("received data from TCP connection: ", data_frame)
                if (data_frame[2] == "state_change_request"):
                    self.__state_change(
                        state_request=data_frame[7][data_frame[7].index("[") + 1:data_frame[7].index("]")])
                    # state wird so erwartet: [blinking]
                    self.__send_ack(connection=connection, msg_uuid=data_frame[3])
                elif (data_frame[2] == "heartbeat"):
                    msg = self.__state_message("dynamic_discovery")
                    try:
                        conn.send(msg.encode())
                    except:
                        self.socket.listen(1)
                        conn, addr = self.socket.accept()
                        conn.send(msg.encode())
                    self.my_lamport_clock += 1
            self.__check_state()

    def __create_udp_socket(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(3)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        ttl = struct.pack('b', 1)
        self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def __state_message(self, message_type: str):
        ec_json = {str(self.uuid): [self.state, self.client_address, self.client_port]}
        return create_frame(priority=2, role="EC", message_type=message_type, msg_uuid=uuid.uuid4(),
                            ppid=self.uuid, fairness_assertion=1, sender_clock=self.my_lamport_clock,
                            payload=json.dumps(ec_json))

    def get_server(self):
        msg = self.__state_message("dynamic_discovery")
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_lamport_clock += 1
        try:
            data, addr = self.udp_socket.recvfrom(2048)
        except socket.timeout:
            print("time out! No response!")
            print("try again!")
            self.udp_socket.close()
            self.__create_udp_socket()
            self.get_server()
            return
        print("received data from Server: ", data.decode())
        self.communication_partner = addr

    def __state_change(self, state_request):
        if state_request in self.state_list:
            self.state = state_request
        else:
            logging.ERROR(
                'state request was not possible! Possible states are "off, on, blinking" ->state has not changed!')

    def __send_ack(self, connection, msg_uuid):
        msg = create_frame(priority=2, role="EC", message_type="state_change_ack", msg_uuid=msg_uuid,
                           ppid=self.uuid, fairness_assertion=1,
                           sender_clock=self.my_lamport_clock, payload="state changed to: {}".format(self.state))
        print("state_change_ack to server: ", msg)
        connection.send(msg.encode())
        self.my_lamport_clock += 1

    def __send_heartbeat(self):
        msg = self.__state_message("heartbeat")
        self.udp_socket.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        self.my_lamport_clock += 1
        try:
            data, addr = self.udp_socket.recvfrom(2048)
        except socket.timeout:
            print("No leading server reachable!")
            print("try again!")
            # self.udp_socket.close()
            time.sleep(1)
            # self.__create_udp_socket()
            self.__send_heartbeat()
            return
        if addr != self.communication_partner:
            print("leading server has changed!")
            self.communication_partner = addr
        self.scheduler.enter(self.heartbeat_period, 1, self.__send_heartbeat)

    def __check_state(self):
        if self.state == "off":
            self.__off()
        elif self.state == "on":
            self.__on()
        elif self.state == "blinking":
            self.__blinking()
        else:
            logging.ERROR("No valid state!")

    def __off(self):
        print("client {} is off".format(self.uuid))

    def __on(self):
        print(("client {} is on".format(self.uuid)))

    def __blinking(self):
        print("client {} is blinking".format(self.uuid))

    def run_heartbeat_S(self):
        self.scheduler.run()

    def run(self):
        heartbeat_thread = Thread(target=self.run_heartbeat_S, name="heartbeat_thread")
        self.__create_udp_socket()
        self.get_server()  # dynamic discovery -> bekannt machen bei den Servern
        # connection, addr = self.__bind_socket()  # tcp socket to Server
        heartbeat_thread.start()
        self.__tcp_listener()
        while (True):
            print("EC_client runs")
            time.sleep(5)
            # try:
            #     data = connection.recvfrom(self.buffer_size)
            # except:
            #     pass    # leading server has died! #ToDo: create new connection to leading server!
            # if (len(data[0]) == 0):
            #     connection.close()
            #     time.sleep(1)
            #     self.socket.listen(1)
            #     connection, addr = self.socket.accept()
            #     continue
            # else:
            #     data_frame = in_filter(data[0].decode(), addr)
            #     # print("received data from TCP connection: ", data_frame)
            #     if (data_frame[2] == "state_change_request"):
            #         self.__state_change(
            #             state_request=data_frame[7][data_frame[7].index("[") + 1:data_frame[7].index("]")])
            #         # state wird so erwartet: [blinking]
            #         self.__send_ack(connection=connection, msg_uuid=data_frame[3])
            #     elif (data_frame[2] == "heartbeat"):
            #         msg = self.__state_message("dynamic_discovery")
            #         try:
            #             connection.send(msg.encode())
            #         except:
            #             self.socket.listen(1)
            #             connection, addr = self.socket.accept()
            #             connection.send(msg.encode())
            #         self.my_lamport_clock += 1
            # self.__check_state()
