# -*- coding: utf-8 -*-

import os
import struct
import socket

__node_id_bits__ = 160
__trans_id_bits__ = 32

def random_node_id():
    """ Generate random bits for using as node id """
    #return random.getrandbits(id_bits)
    return os.urandom(__node_id_bits__/8)

def random_trans_id():
    """ Generate random bits for using as transaction id """
    return os.urandom(__trans_id_bits__/8)

def dottedQuadToNum(ip):
    """ Convert decimal dotted quad string to long integer """
    hexn = ''.join(["%02X" % long(i) for i in ip.split('.')])
    return long(hexn, 16) 

def numToDottedQuad(n):
    """ Convert long int to dotted quad string """
    d = 256 * 256 * 256 
    q = []
    while d > 0:
        m, n = divmod(n, d)
        q.append(str(m))
        d /= 256 
    return '.'.join(q)

def decode_nodes(nodes):
    """ Decode node_info into a list of id, connect_info """
    nrnodes = len(nodes) / 26
    nodes = struct.unpack("!" + "20sIH" * nrnodes, nodes)
    for i in xrange(nrnodes):
        node_id, ip, port = nodes[i * 3], numToDottedQuad(nodes[i * 3 + 1]), nodes[i * 3 + 2]
        yield node_id, ip, port

def encode_nodes(nodes):
    """ Encode a list of (id, connect_info) pairs into a node_info """
    n = []
    for node in nodes:
        n.extend([node[0], dottedQuadToNum(node[1].host), node[1].port])
    return struct.pack("!" + "20sIH" * len(nodes), *n) 

def pack_host(host):
    try:
        addr = socket.inet_pton(socket.AF_INET, host)
    except (ValueError, socket.error):
        addr = socket.inet_pton(socket.AF_INET6, host)
    return addr 

def pack_port(port):
    return chr(port >> 8) + chr(port % 256)

def unpack_host(host):
    if len(host) == 4:
        return socket.inet_ntop(socket.AF_INET, host)
    elif len(host) == 16: 
        return socket.inet_ntop(socket.AF_INET6, host)

def unpack_port(port):
    return (ord(port[0]) << 8) + ord(port[1])

def unpack_hostport(addr):
    if len(addr) == 6:
        host = addr[:4]
        port = addr[4:6]
    if len(addr) == 18:
        host = addr[:16]
        port = addr[16:18]
    return (unpack_host(host), unpack_port(port))

def pack_hostport(host, port):
    host = pack_host(host)
    port = pack_port(port)
    return host + port

def get_version():
    """ Return appropriate DHT version bytes """
    return "BT\x00\x01"

