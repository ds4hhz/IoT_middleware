import socket


# UDP_IP = "127.0.0.1"
# UDP_PORT = 5005

UDP_IP = "233.33.33.33"
UDP_PORT = 9950

MESSAGE = b"Hello, World!"

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

# Internet # UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#workaround broadcasting...
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))