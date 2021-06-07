from Executing_Client import ExecutingClient
from multiprocessing import Process
import time
import sys

if "-p" in sys.argv:
    tcp_port = sys.argv[sys.argv.index("-p") + 1]
else:
    tcp_port = 11000
tcp_address = (int(tcp_port))
print("tcp socket address: {}".format(tcp_address))

executing_client_obj = ExecutingClient(port=tcp_address)
executing_client_obj.run()
