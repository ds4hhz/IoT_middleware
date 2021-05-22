import queue
import threading
import logging


class OrderedReliableMulticast(threading.Thread):

    def __init__(self):
        self.acked_mssgs = {}
        self.non_acked_mssgs = {}

        #self.fairness_to_lead_ = {}
        self.outgoing_mssg_pipe = queue.PriorityQueue()

    def fairness(self, fairness):
        pass


    def run(self):
        """ Initialize and start all threads. """
        thread_routines = [
            self.ack_handler,
            self.message_queue_handler,
            self.incoming_message_handler,
        ]

        count = 1
        for thread_routine in thread_routines:
            thread = threading.Thread(
                target=thread_routine,
                args=(self.running,),
                name="ReliableSocketWorker-%s" % count,
            )
            thread.daemon = True
            thread.start()
            logging.info("Thread %s started." % thread.name)
            self.threads.append(thread)
            count += 1