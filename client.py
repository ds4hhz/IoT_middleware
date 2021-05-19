import threading
from configurations import cfg
from tkinter import *

class Client:

    def __init__(self, toc=None):
        # CC == Commanding Client
        # EC == Excecuting Client
        try:
            self.TypeOfClient = toc
        except Exception as e:
            print(e)


    def handle_msg(self):
        pass

    def statechangerequest(self):
        pass

    def statechange(self):
        pass

    def deliver_message(self):
        pass


if __name__=="__main__":
    client = Client()