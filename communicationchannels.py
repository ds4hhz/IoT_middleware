import socket

import configurations
from configurations import cfg as defcfg
import struct
import threading
import pipesfilter

class Communication(threading.Thread):

    def __init__(self, cfg):
        if cfg == None:
            self.configs = defcfg
        else:
            self.configs = cfg

        self.binded_bc = self.bind_broadcastlistener()
        self.binded_mc = self.bind_multicastlistener()
        #self.binded_tcp_sock = self.binded_tcp_socket()
        #self.binded_udp_unicast = self.get_unicast_socket()
        #self.binded_tcp = self.get_tcp_socket()

    def send_bc_socket(self, message_frame):
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send message on broadcast address
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        broadcast_socket.sendto(str.encode(message_frame), (self.configs["brc_addr"], self.configs["brc_port"]))
        broadcast_socket.close()

    def send_mc_socket(self, message_frame):
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.sendto(message_frame, (self.configs["multicast_group"], self.configs["multicast_port"]))
        broadcast_socket.close()

    def send_udp_unicast(self, message_frame, receiver):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # workaround broadcasting...
        sock.sendto(message_frame, (receiver, self.configs["unicast_port"]))

    """def binded_tcp_socket(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind((self.configs["machine_ipv4"]),1024)
        return tcp_socket"""

    def get_tcp_socket(self):
        return self.binded_tcp_sock

    def bind_multicastlistener(self):
        mc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        mc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mc_sock.bind(('', self.configs["multicast_port"]))
        mreq = struct.pack("4sl", socket.inet_aton(self.configs["multicast_group"]), socket.INADDR_ANY)
        mc_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return mc_sock

    def get_multicastlistener(self):
        return self.binded_mc

    def bind_broadcastlistener(self):
        # Create a UDP socket
        bc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Set the socket to broadcast and enable reusing addresses
        bc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        bc_socket.bind((self.configs["brc_addr"], self.configs["brc_port"]))
        return bc_socket

    def get_broadcastlistener(self):
        return self.binded_bc

    def send_msg(self, typeofmessage, dataframe, destination):
        if typeofmessage == "broadcast":
            self.binded_bc.sendto(dataframe, (self.configs["brc_addr"], self.configs["brc_port"]))

        if typeofmessage == "multicast":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(dataframe, (self.configs["multicast_group"], self.configs["multicast_port"]))

        if typeofmessage == "udp_unicast":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(pipesfilter.outFilter(dataframe), dataframe[9], self.configs["multicast_port"])


        if typeofmessage == "tcp_unicast":
            pass



