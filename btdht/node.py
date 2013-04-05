# -*- coding: utf-8 -*-

import threading
import time
import logging

from .bencode import bencode
from .utils import random_trans_id, get_version 

logger = logging.getLogger(__name__)

class Node(object):
    """ Represent a DHT node """
    def __init__(self, host, port, _id):
        self._id = _id
        self.host = host
        self.port = port
        self.trans = {}

        self.lock = threading.Lock()

        self.access_time = time.time()

    def __repr__(self):
        return repr("%s %s:%d" % (self._id.encode('hex'), self.host, self.port))

    def add_trans(self, name, info_hash=None):
        """ Generate and add new transaction """
        trans_id = random_trans_id()
        with self.lock:
            self.trans[trans_id] = {
                    "name": name,
                    "info_hash": info_hash,
                    "access_time": int(time.time())
            }
        return trans_id

    def delete_trans(self, trans_id):
        """ Delete specified transaction """
        with self.lock:
            del self.trans[trans_id]

    def update_access(self, unixtime=None):
        """ Update last access/modify time of this node """
        with self.lock:
            if unixtime:
                self.access_time = unixtime
            else:
                self.access_time = time.time()

    def _sendmessage(self, message, sock=None, trans_id=None, lock=None):
        """ Send and bencode constructed message to other node """
        message["v"] = get_version()
        if trans_id:
            message["t"] = trans_id
        encoded = bencode(message)
        if sock:
            if lock:
                with lock:
                    sock.sendto(encoded, (self.host, self.port))
            else:
                sock.sendto(encoded, (self.host, self.port))
        
    def ping(self, socket=None, sender_id=None, lock=None):
        """ Construct query ping message """
        trans_id = self.add_trans("ping")
        message = {
            "y": "q",
            "q": "ping",
            "a": {
                "id": sender_id
            }
        }
        logger.debug("ping msg to %s:%d, y:%s, q:%s, t: %r" % (
            self.host, 
            self.port, 
            message["y"], 
            message["q"], 
            trans_id.encode("hex")
        ))
        self._sendmessage(message, socket, trans_id=trans_id, lock=lock)
        
    def pong(self, socket=None, trans_id=None, sender_id=None, lock=None):
        """ Construct reply message for ping """
        message = {
            "y": "r",
            "r": {
                "id": sender_id
            }
        }
        logger.debug("pong msg to %s:%d, y:%s, t: %r" % (
            self.host, 
            self.port, 
            message["y"], 
            trans_id.encode("hex")
        ))
        self._sendmessage(message, socket, trans_id=trans_id, lock=lock)
        
    def find_node(self, target_id, socket=None, sender_id=None, lock=None):
        """ Construct query find_node message """
        trans_id = self.add_trans("find_node")
        message = {
            "y": "q",
            "q": "find_node",
            "a": { 
                "id": sender_id,
                "target": target_id
            }
        }
        logger.debug("find_node msg to %s:%d, y:%s, q:%s, t: %r" % (
            self.host, 
            self.port, 
            message["y"], 
            message["q"], 
            trans_id.encode("hex")
        ))
        self._sendmessage(message, socket, trans_id=trans_id, lock=lock)

    def found_node(self, found_nodes, socket=None, trans_id=None, sender_id=None, lock=None):
        """ Construct reply message for find_node """

        message = {
            "y": "r",
            "r": {
                "id": sender_id,
                "nodes": found_nodes
            }
        }
        logger.debug("found_node msg to %s:%d, y:%s, t: %r" % (
            self.host, 
            self.port, 
            message["y"], 
            trans_id.encode("hex")
        ))
        self._sendmessage(message, socket, trans_id=trans_id, lock=lock)

    def get_peers(self, info_hash, socket=None, sender_id=None, lock=None):
        """ Construct query get_peers message """
        trans_id = self.add_trans("get_peers", info_hash)
        message = {
            "y": "q",
            "q": "get_peers",
            "a": { 
                "id": sender_id,
                "info_hash": info_hash
            }
        }
        logger.debug("get_peers msg to %s:%d, y:%s, q:%s, t: %r" % (
            self.host, 
            self.port, 
            message["y"], 
            message["q"], 
            trans_id.encode("hex")
        ))
        self._sendmessage(message, socket, trans_id=trans_id, lock=lock)

    def got_peers(self, token, values, socket=None, trans_id=None, sender_id=None, lock=None):
        """ Construct reply message for got_peers """

        message = {
            "y": "r",
            "r": {
                "id": sender_id,
                "nodes": values
            }
        }
        logger.debug("got_peers msg to %s:%d, y:%s, t: %r" % (
            self.host, 
            self.port, 
            message["y"], 
            trans_id.encode("hex")
        ))
        self._sendmessage(message, socket, trans_id=trans_id, lock=lock)
