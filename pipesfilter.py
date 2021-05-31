
#todo: Prios für messages bestimmen

# FRAME-Structure
# POSITIONS:
#    0    |  1 | 2         |   3    | 4  |         5        |      6     |    7  |   8  |
# PRIORITY;ROLE;MESSAGE_TYP;MSG-UUID;PPID;FAIRNESS ASSERTION;SENDER-CLOCK;PAYLOAD;SENDER


def in_filter(frame, sender_addr):
    unpacked_frame = frame.split(";")
    unpacked_frame[0] = int(unpacked_frame[0])  # PRIORITY
    unpacked_frame[1] = str(unpacked_frame[1])  # ROLE
    unpacked_frame[2] = str(unpacked_frame[2])  # MESSAGE_TYPE
    unpacked_frame[3] = str(unpacked_frame[3])  # MSG_UUID
    unpacked_frame[4] = str(unpacked_frame[4])  # PPID
    unpacked_frame[5] = int(unpacked_frame[5])  # FAIRNESS ASSERTION
    unpacked_frame[6] = int(unpacked_frame[6])  # SENDER-CLOCK
    unpacked_frame[7] = str(unpacked_frame[7])  # PAYLOAD -> nur gültig bei state_change_request
    unpacked_frame.append(sender_addr[0])
    unpacked_frame[8] = str(unpacked_frame[8])  # SENDER
    return unpacked_frame


def create_frame(priority, role, message_type, msg_uuid, ppid, fairness_assertion, sender_clock, payload, sender):
    message_list = [str(priority), str(role), str(message_type), str(msg_uuid), str(ppid), str(fairness_assertion),
                    str(sender_clock), str(payload), str(sender)]
    receiver = message_list[8]
    del message_list[-1]
    msg_string = ";".join(message_list)
    return [msg_string, receiver]
