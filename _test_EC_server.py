import struct
import socket
from pipesfilter import create_frame
from pipesfilter import Role
from pipesfilter import MessageType
from pipesfilter import in_filter
import uuid
import time
import sys
multicast_group = '224.3.29.71'
server_address = ('', 10000)
my_uuid= uuid.uuid4()
my_clock = 0

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
i = 0
while True:
    data, address = sock.recvfrom(2048)
    print(data)
    data= in_filter(data.decode(),address)
    msg = create_frame(1, 0, 2, data[3],my_uuid,1,my_clock,"runs")
    if (i%2 == 0):
        print("sleep 5")
        time.sleep(5)
    else:
        print("sleep 2")
        time.sleep(1)
    sock.sendto(msg.encode() ,address)
    print(msg)
    print("lamport clock: ",my_clock)
    my_clock+=1
    i +=1