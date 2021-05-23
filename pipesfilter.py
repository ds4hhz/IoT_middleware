from struct import *


# FRAME-Structure
# POSITIONS:
#    0   |  1 | 2 |   3    | 4  |         5        |      6     |    7    |   8     |   9  |
# PRIORITY;ROLE;TYP;MSG-UUID;PPID;FAIRNESS ASSERTION;SENDER-CLOCK;EC-ADDRESS;STATEMENT;SENDER

@staticmethod
def inFilter(frame, sender_addr):
    unpacked_frame = frame.split(" ")
    unpacked_frame.append(sender_addr)
    unpacked_frame[0] = int(unpacked_frame[0])  # PIORITY
    unpacked_frame[4] = int(unpacked_frame[4])  # PPID
    unpacked_frame[5] = int(unpacked_frame[5])  # RTT
    unpacked_frame[6] = int(unpacked_frame[6])  # SENDER-CLOCK
    return unpacked_frame


@staticmethod
def outFilter(frame):
    RECEIVER = frame[9]
    del frame[-1]
    frame[0] = str(frame[0])  # PPID
    frame[4] = str(frame[4])  # RTT
    frame[5] = str(frame[5])
    frame[6] = str(frame[6])
    msg_string = " ".join(frame)
    return [msg_string, RECEIVER]


def create_frame(priority, role, sender_type, msd_uuid, fairness_assertion, sender_clock, ec_address, statement, sender):
    message_list = [priority, role, sender_type, msd_uuid, fairness_assertion, sender_clock, ec_address, statement, sender]
    return ",".join([str(x) for x in message_list])
