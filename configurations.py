import socket

hostname = socket.gethostname()
MACHINE_IPV4 = socket.gethostbyname(hostname)

cfg = {
    "machine_ipv4": MACHINE_IPV4,
    # for coordination and elections:

    "multicast_group": "233.33.33.33",
    "multicast_port": 9950,
    "multicast_retrys": 3,

    # "brc_addr": "192.168.1.255",
    "brc_addr": "192.168.56.255",
    "brc_port": 10500,

    "unicast_port": 10001,
    "reliable_socket_port": 10033,

    "announcement_timeout": 3,
    # max rount trip time,
    "max_rtt": 1,
    "hb_intervall": 2,
    "hb_timeout": 6,

    "server_response_timeout": 5,


}