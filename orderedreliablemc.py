import queue


class OrderedReliableMulticast:

    def __init__(self):
        self.mssg_pipe = queue.PriorityQueue()