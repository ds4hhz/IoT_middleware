from enum import Enum


class Role(Enum):
    S = 0
    CC = 1
    EC = 2


class MessageType(Enum):
    msg_ack = 0
    dynamic_discovery = 1
    dynamic_discovery_ack = 2
    state_change_request = 3
    state_change_ack = 4
    election = 5
    leader_msg = 6
    replication = 7
    replication_ack = 8
    heartbeat = 9
    ec_list_query = 10


# todo: Prios für messages bestimmen

# FRAME-Structure
# POSITIONS:
#    0    |  1 | 2         |   3    | 4  |         5        |      6     |    7  |   8  |
# PRIORITY;ROLE;MESSAGE_TYP;MSG-UUID;PPID;FAIRNESS ASSERTION;SENDER-CLOCK;PAYLOAD;SENDER
#                           ;for ack;
# @staticmethod
def in_filter(frame, sender_addr):
    unpacked_frame = frame.split(";")
    unpacked_frame[0] = int(unpacked_frame[0])  # PRIORITY
    unpacked_frame[1] = int(unpacked_frame[1])  # ROLE
    unpacked_frame[2] = int(unpacked_frame[2])  # MESSAGE_TYPE
    unpacked_frame[3] = str(unpacked_frame[3])  # MSG_UUID
    unpacked_frame[4] = str(unpacked_frame[4])  # PPID
    unpacked_frame[5] = int(unpacked_frame[5])  # RTT
    unpacked_frame[6] = int(unpacked_frame[6])  # SENDER-CLOCK
    unpacked_frame[7] = str(unpacked_frame[7])  # PAYLOAD
    unpacked_frame.append(sender_addr)
    return unpacked_frame


def create_frame(priority, role, message_type, msg_uuid, ppid, fairness_assertion, sender_clock, payload):
    message_list = [priority, role, message_type, msg_uuid, ppid, fairness_assertion, sender_clock, payload]
    return ";".join([str(x) for x in message_list])
