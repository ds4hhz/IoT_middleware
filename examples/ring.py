import socket


def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    print(sorted_binary_ring)
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    print(sorted_ip_ring)
    return sorted_ip_ring


def get_neighbour(ring, current_node_ip, direction='left'):
    current_node_index = ring.index(current_node_ip) if current_node_ip in ring else -1
    if current_node_index != -1:
        if direction == 'left':
            if current_node_index + 1 == len(ring):
                return ring[0]
            else:
                return ring[current_node_index + 1]
        else:
            if current_node_index == 0:
                return ring[len(ring) - 1]
            else:
                return ring[current_node_index - 1]
    else:
        return None


members = ['192.168.0.1', '130.234.204.2', '130.234.203.2', '130.234.204.1', '182.4.3.111']
ring = form_ring(members)
print(ring)
neighbour = get_neighbour(ring, '130.234.204.2', '')
print(neighbour)
