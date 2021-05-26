import socket
from pipesfilter import *
import uuid
import time
my_uuid = uuid.uuid4()
my_clock= 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 11000))


while(True):
    s.send(create_frame(1,2,3,uuid.uuid4(),my_uuid,1,my_clock,"172.156.0.1, {blinking}").encode())
    my_clock +=1
    data = s.recv(1024)
    # s.close()
    print(data)
    time.sleep(5)

