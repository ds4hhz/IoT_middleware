from Executing_Client import ExecutingClient
from multiprocessing import Process
import time

executing_client_obj = ExecutingClient()
executing_client_obj2 = ExecutingClient(port=11111)
# executing_client_obj.run()

executing_client1 = Process(target=executing_client_obj.run, name="EC1")
executing_client2 = Process(target=executing_client_obj2.run, name="EC2")
executing_client2.start()
time.sleep(1)
# executing_client1.start()
executing_client_obj.run()