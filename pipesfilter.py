from struct import *
from enum import Enum


class Role(Enum):
    S = 0
    CC = 1
    EC = 2


class MessageType(Enum):
    msg_ack = 0
    dynamic_discovery = 1
    state_change_request = 2
    state_change_ack = 3
    election = 4
    leader_msg = 5
    replication = 6
    replication_ack = 7
    heartbeat = 8

#todo: Prios für messages bestimmen

# FRAME-Structure
# POSITIONS:
#    0    |  1 | 2         |   3    | 4  |         5        |      6     |    7  |   8  |
# PRIORITY;ROLE;MESSAGE_TYP;MSG-UUID;PPID;FAIRNESS ASSERTION;SENDER-CLOCK;PAYLOAD;SENDER


def in_filter(frame, sender_addr):
    unpacked_frame = frame.split(",")
    unpacked_frame[0] = int(unpacked_frame[0])  # PRIORITY
    unpacked_frame[1] = str(unpacked_frame[1])  # ROLE
    unpacked_frame[2] = str(unpacked_frame[2])  # MESSAGE_TYPE
    unpacked_frame[3] = str(unpacked_frame[3])  # MSG_UUID
    unpacked_frame[4] = int(unpacked_frame[4])  # PPID
    unpacked_frame[5] = int(unpacked_frame[5])  # FAIRNESS ASSERTION
    unpacked_frame[6] = int(unpacked_frame[6])  # SENDER-CLOCK
    unpacked_frame[7] = str(unpacked_frame[7])  # PAYLOAD -> nur gültig bei state_change_request
    unpacked_frame.append(sender_addr)
    unpacked_frame[8] = str(unpacked_frame[8])  # SENDER
    return unpacked_frame

@staticmethod
def outFilter(frame):
    RECEIVER = frame[9]
    del frame[-1]
    frame[0] = str(frame[0])  # PPID
    frame[4] = str(frame[4])  # RTT
    frame[5] = str(frame[5])
    frame[6] = str(frame[6])
    msg_string = ",".join(frame)
    return [msg_string, RECEIVER]


def create_frame(priority, role, message_type, msg_uuid, ppid, fairness_assertion, sender_clock, payload, sender):
    message_list = [str(priority), str(role), str(message_type), str(msg_uuid), str(ppid), str(fairness_assertion), str(sender_clock), str(payload), str(sender)]
    RECEIVER = message_list[8]
    del message_list[-1]
    msg_string = ",".join(message_list)
    print(msg_string)
    return [msg_string, RECEIVER]
