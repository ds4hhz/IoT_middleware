import sys, socket
import os
from configurations import cfg
from server import Server
from communicationchannels import Communication


# get machine IPv4-Adress & set configurations:
hostname = socket.gethostname()
MACHINE_IPV4 = socket.gethostbyname(hostname)
cfg["machine_ipv4"] = str(MACHINE_IPV4)
print("Configurations are done... deploying participant...")
# print('Parent process id:', os.getppid())
# print('Process id:', os.getpid())



#   "server" (S)
#   "controlling client" (CC)
#   "executing client" (EC)
# arg1 as type of partipicant
if __name__=="__main__":
    if len(sys.argv)>1:
        if sys.argv[1]==str("EC"):
            print("Executing Client with IP-Adress " + MACHINE_IPV4 + " is starting ...")
        elif sys.argv[1]==str("CC"):
            print("Commanding Client with IP-Adress " + MACHINE_IPV4 + " is starting ...")
        elif sys.argv[1] == str("S"):
            print("Server with IP-Adress " + MACHINE_IPV4 + " is starting ...")

            server = Server()



        else:
            print("Wrong type of partipicant is defined... Choose EC, CC or S")
    else:
        print("Type of partipicant is not defined...")