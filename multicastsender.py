import socket

# UDP_IP = "127.0.0.1"
# UDP_PORT = 5005

UDP_IP = "192.168.1."
UDP_PORT = 5005

MESSAGE = b"Hello, World!"

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

# Internet # UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#workaround broadcasting...
for i in range(1,254):
    sock.sendto(MESSAGE, (UDP_IP+str(i), UDP_PORT))