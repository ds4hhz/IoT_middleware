import struct
import socket
import sys
multicast_group = '224.3.29.71'
server_address = ('127.0.0.1', 10000)


# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
# Receive/respond loop
while True:
    data, address = sock.recvfrom(2048)
    print(data.encode())


    sock.sendto('ack', address)