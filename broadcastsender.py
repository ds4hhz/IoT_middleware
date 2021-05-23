import socket
from pipesfilter import create_frame


class BroadcastSender:
    # typeofsender might be a
    # "server" (S)
    # "controlling client" (CC)
    # "executing client" (EC)
    #  ^
    # "non" not any of above
    def __init__(self, tos, bcn="192.168.1.255",
                 bcp=10500):  # message muss von create_frame kommen um sicherzustellen, dass alle Nachrichten gleich aufgebaut sind
        if tos in ["S", "CC", "EC"]:
            self.ToS = tos
        else:
            self.ToS = ""
        self.BROADCAST_IP = bcn
        self.BROADCAST_PORT = bcp
        self.args = {"ToS": self.ToS, "message": message}


    def broadcast(self,message):
        # leading String (message) design:
        #encoded message from calling source

        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send message on broadcast address
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        broadcast_socket.sendto(message, (self.BROADCAST_IP, self.BROADCAST_PORT))
        broadcast_socket.close()


# ---------- for testing purposes below -------------

def mainbc(ip, port, broadcast_message):
    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Send message on broadcast address
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    broadcast_socket.sendto(str.encode(broadcast_message), (ip, port))
    broadcast_socket.close()


if __name__ == '__main__':
    # Broadcast address and port
    BROADCAST_IP = "192.168.1.255"
    BROADCAST_PORT = 10500
    # Send broadcast message
    message = "A placeholder message"
    mainbc(BROADCAST_IP, BROADCAST_PORT, message)
