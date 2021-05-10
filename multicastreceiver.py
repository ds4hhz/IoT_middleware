import socket


hostname = socket.gethostname()
UDP_IP = "127.0.0.1"
UDP_PORT = 5005


# Internet  # UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    print("received message: %s" % data)