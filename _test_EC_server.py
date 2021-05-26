import struct
import socket
from pipesfilter import create_frame
from pipesfilter import Role
from pipesfilter import MessageType
from pipesfilter import in_filter
import uuid
import time
import sys
import json
import multiprocessing

multicast_group = '224.3.29.71'
server_address = ('', 10000)
my_uuid= uuid.uuid4()
my_clock = 0



def tcp_socket():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp client
    tcp_socket.bind(("10.0.2.15", 12000))
    tcp_socket.listen(1)
    conn, addr = tcp_socket.accept()
    data = conn.recvfrom(2048)
    if (len(data[0]) == 0):
        print("connection lost!")
        conn.close()
    print(data)

def udp_socket():
    multicast_group = '224.3.29.71'
    server_address = ('', 10000)
    my_uuid = uuid.uuid4()
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
    ec_dict={}
    while True:
        data, address = sock.recvfrom(2048)
        print(data)
        data= in_filter(data.decode(),address)
        if(data[1] == "CC" and data[2] == "ec_list_query"):
            # send dict of all known executing clients with state
            msg = create_frame(1, "S", "ec_list_query_ack ", data[3], my_uuid, 1, my_clock,json.dumps(ec_dict))
            sock.sendto(msg.encode(), address)
            print(msg)
            print("lamport clock: ", my_clock)
            my_clock += 1
            i += 1

        elif (data[1] == "EC" and data[2]=="dynamic_discovery"):
            # get current state
            # and uuid
            temp_dict = json.loads(data[7])
            for k, v in temp_dict.items():
                ec_dict[k]=v
                print(ec_dict)
            if (i%2 == 0):
                print("sleep 5")
                time.sleep(1)
            else:
                print("sleep 2")
                time.sleep(1)
            msg = create_frame(1, "S", "dynamic_discovery_ack ", data[3], my_uuid, 1, my_clock, "runs")
            sock.sendto(msg.encode() ,address)
            print(msg)
            print("lamport clock: ",my_clock)
            my_clock+=1
            i +=1

# ToDo: Multiprocessing zweiten Prozess mit TCP Socket für CC->state_change_request -> S -> EX

tcp_process = multiprocessing.Process(target=tcp_socket,name="tcp_process")
udp_process = multiprocessing.Process(target=udp_socket(),name="udp_process")