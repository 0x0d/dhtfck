# -*- coding: utf-8 -*-

import threading
import random

def strxor(str1, str2):
    """ xor two strings of different lengths """
    if len(str1) > len(str2):
        return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(str1[:len(str2)], str2)])
    else:
        return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(str1, str2[:len(str1)])])

class RoutingTable(object):
    """ This is our routing table. """
    # We don't do any bucketing or anything like that, we just
    # keep track of all the nodes we know about.
    # This gives us significant memory overhead over a bucketed
    # implementation and ruins the logN scaling behaviour of the DHT.
    # We don't care, we have a lot of mem ;)
    
    def __init__(self):
        self.nodes = {}
        self.bad_nodes = {}
        self.lock = threading.Lock()

    def get_close_nodes(self, target, num=3):
        """ Find the "num" nodes in the routing table closest to target """
        # We do this by brute force: we compute the distance of the
        # target node to all the nodes in the routing table.
        # A bucketing system would speed things up considerably, and
        # require less memory.
        # However, we like to keep as many nodes as possible in our routing
        # table for research purposes.

        if len(self.nodes) == 0:
            raise RuntimeError, "No nodes in routing table!"

        # Sort the entire routing table by distance to the target
        # and return the top N matches
        with self.lock:
            nodes = [(node_id, self.nodes[node_id]) for node_id in self.nodes]
        nodes.sort(key=lambda x: strxor(target, x[0]))
        return nodes[:num]

    def update_node(self, node_id, node):
        """ Add new or update node """
        with self.lock:
            if node_id in self.bad_nodes:
                return
            if node_id not in self.nodes:
                self.nodes[node_id] = node
            self.nodes[node_id].update_access()

    def remove_node(self, node_id):
        """ Remove node from routing table """
        with self.lock:
            if node_id in self.nodes:
                self.bad_nodes[node_id] = self.nodes[node_id]
                del self.nodes[node_id]

    def get_nodes(self):
        return self.nodes

    def count(self):
        """ Count nodes in table """
        return len(self.nodes)

    def bad_count(self):
        """ Count bad nodes in table """
        return len(self.bad_nodes)

    def node_by_trans(self, trans_id):
        """ Get apropriate node by transaction_id """
        with self.lock:
            for node_id in self.nodes:
                if trans_id in self.nodes[node_id].trans:
                    return self.nodes[node_id]
        return None

    def node_by_id(self, node_id):
        """ Get apropriate node by node_id """
        with self.lock:
            if node_id in self.nodes:
                return self.nodes[node_id]
        return None

    def sample(self, num):
        """ Return "num" random nodes from table """
        with self.lock:
            return random.sample(self.nodes.items(), num)

