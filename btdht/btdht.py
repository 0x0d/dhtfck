# -*- coding: utf-8 -*-

import SocketServer
import socket
import threading
import time
import logging

from .rtable import RoutingTable
from .bencode import bdecode, BTFailure
from .node import Node
from .utils import decode_nodes, encode_nodes, random_node_id, unpack_host, unpack_hostport

logger = logging.getLogger(__name__)

def hexiptostring(data, start):
    return str(int(data[start:start+1].encode('hex'),16)) + "." + str(int(data[start+1:start+2].encode('hex'),16)) + "." + str(int(data[start+2:start+3].encode('hex'),16)) + "." +    str(int(data[start+3:start+4].encode('hex'),16))

class DHTRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):

        logger.debug("Got packet from: %s:%d" % (self.client_address))
        req = self.request[0].strip()

        try:
            message = bdecode(req)
            msg_type = message["y"]
            logger.debug("This is DHT connection with msg_type: %s" % (msg_type))

            if msg_type == "r":
                self.handle_response(message)
            elif msg_type == "q":
                self.handle_query(message)
            elif msg_type == "e":
                self.handle_error(message)
            else:
                logger.error("Unknown rpc message type %r" % (msg_type))
        except BTFailure:
            logger.error("Fail to parse message %r" % (self.request[0].encode("hex")))
            pass

    def handle_response(self, message):
        trans_id = message["t"]
        args = message["r"]
        node_id = args["id"]

        client_host, client_port = self.client_address
        logger.debug("Response message from %s:%d, t:%r, id:%r" % (client_host, client_port, trans_id.encode("hex"), node_id.encode("hex")))

        # Do we know already about this node?
        node = self.server.dht.rt.node_by_id(node_id)
        if not node:
            logger.debug("Cannot find appropriate node during simple search: %r" % (node_id.encode("hex")))

            # Trying to search via transaction id
            node = self.server.dht.rt.node_by_trans(trans_id)
            if not node:
                logger.error("Cannot find appropriate node for transaction: %r" % (trans_id.encode("hex")))
                return

        logger.debug("We found apropriate node %r for %r" % (node, node_id.encode("hex")))

        if trans_id in node.trans:
            logger.debug("Found and deleting transaction %r in node: %r" % (trans_id.encode("hex"), node))
            trans = node.trans[trans_id]
            node.delete_trans(trans_id)
        else:
            logger.error("Cannot find transaction %r in node: %r" % (trans_id.encode("hex"), node))
            for trans in node.trans:
                logger.debug(trans.encode("hex"))
            return

        node.update_access()

        if "ip" in args:
            logger.debug("They try to SECURE me: %s", unpack_host(args["ip"]))

        t_name = trans["name"]
        if t_name == "find_node":
            logger.debug("find_node response from %r" % (node))
            new_nodes = decode_nodes(args["nodes"])
            logger.debug("We got new nodes from %r" % (node))
            for new_node_id, new_node_host, new_node_port in new_nodes:
                logger.debug("Adding %r %s:%d as new node" % (new_node_id.encode("hex"), new_node_host, new_node_port))
                self.server.dht.rt.update_node(new_node_id, Node(new_node_host, new_node_port, new_node_id))

            # cleanup boot node
            if node._id == "boot":
                logger.debug("This is response from \"boot\" node, replacing it")
                # Create new node instance and move transactions from boot node to newly node
                new_boot_node = Node(client_host, client_port, node_id)
                new_boot_node.trans = node.trans
                self.server.dht.rt.update_node(node_id, new_boot_node)
                # Remove old boot node
                self.server.dht.rt.remove_node(node._id)
        elif t_name == "ping":
            logger.debug("ping response for: %r" % (node))
        elif t_name == "get_peers":
            logger.debug("get peers response for: %r" % (node))
            if "values" in args:
                values = args["values"]
                logger.info("got values")
                for addr in values:
                    logger.info(unpack_hostport(addr))
                    logger.info(addr.encode("hex"))
            if "nodes" in args:
                logger.info("got nodes")
                nodes = args["nodes"]
                #logger.info(nodes)

    def handle_query(self, message):
        trans_id = message["t"]
        query_type = message["q"]
        args = message["a"]
        node_id = args["id"]

        client_host, client_port = self.client_address
        logger.debug("Query message %s from %s:%d, id:%r" % (query_type, client_host, client_port, node_id.encode("hex")))
        
        # Do we know already about this node?
        node = self.server.dht.rt.node_by_id(node_id)
        if not node:
            node = Node(client_host, client_port, node_id)
            logger.debug("We don`t know about %r, add it as new" % (node))
            self.server.dht.rt.update_node(node_id, node)
        else:
            logger.debug("We already know about: %r" % (node))

        node.update_access()

        if query_type == "ping":
            logger.debug("handle query ping")
            node.pong(socket=self.server.socket, trans_id = trans_id, sender_id=self.server.dht.node._id, lock=self.server.send_lock)
        elif query_type == "find_node":
            logger.debug("handle query find_node")
            target = args["target"]
            found_nodes = encode_nodes(self.server.dht.rt.get_close_nodes(target, 8))
            node.found_node(found_nodes, socket=self.server.socket, trans_id = trans_id, sender_id=self.server.dht.node._id, lock=self.server.send_lock)
        elif query_type == "get_peers":
            logger.debug("handle query get_peers")
            return
        elif query_type == "announce_peer":
            logger.debug("handle query announce_peer")
            return
        else:
            logger.error("Unknown query type: %s" % (query_type))

    def handle_error(self, message):
        logger.debug("We got error message from: ")
        return

class DHTServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    def __init__(self, host_address, handler_cls):
        SocketServer.UDPServer.__init__(self, host_address, handler_cls)
        self.send_lock = threading.Lock()

class DHT(object):
    def __init__(self, host, port, boot_host, boot_port):
        self.node = Node(unicode(host), port, random_node_id())
        self.rt = RoutingTable()
        self.server = DHTServer((self.node.host, self.node.port), DHTRequestHandler)
        self.server.dht = self

        logger.debug("DHT Server listening on %s:%d" % (host, port))
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.gc_thread = threading.Thread(target=self.gc)
        self.gc_thread.daemon = True
        self.gc_thread.start()

        self.bootstrap(unicode(boot_host), boot_port)
    
    def iterative_find_nodes(self, find_iteration_timeout, sample_count):

        logger.debug("Entering main node finding loop")

        while True:
            nodes = self.rt.sample(sample_count)
            for node_id, node in nodes:
                node.find_node(random_node_id(), socket=self.server.socket, sender_id=self.node._id)
                #node.get_peers("3253ccc93c6b1a6c5f39c898ecfb2a47f33c3421".decode("hex"), socket=self.server.socket, sender_id=self.node._id)

            logger.info("Current known nodes count: %d" % (self.rt.count()))
            time.sleep(find_iteration_timeout)

    def bootstrap(self, boot_host, boot_port):

        sample_count = 8
        max_bootstrap_errors = 5
        bootstrap_iteration_timeout = 2
        find_iteration_timeout = 2

        logger.debug("Starting DHT bootstrap on %s:%d" % (boot_host, boot_port))
        boot_node = Node(boot_host, boot_port, "boot")
        self.rt.update_node("boot", boot_node)

        # Do cycle, while we didnt get enough nodes to start
        while self.rt.count() <= sample_count:

            if len(boot_node.trans) > max_bootstrap_errors:
                logger.error("Too many attempts to bootstrap, seems boot node %s:%d is down. Givin up" % (boot_host, boot_port))
                return

            boot_node.find_node(self.node._id, socket=self.server.socket, sender_id=self.node._id)
            time.sleep(bootstrap_iteration_timeout)
        
        self.iterative_find_nodes(find_iteration_timeout, sample_count)

    def gc(self):

        logger.debug("Garbage collector started")
        while self.rt.count() <= 8:
            time.sleep(1)
            
        while True:
            nodes = self.rt.sample(int(self.rt.count() / 3))
            for node_id, node in nodes:
                time_diff = time.time() - node.access_time
                if time_diff > 60:
                    if len(node.trans) > 5:
                        logger.info("We have node with last access time difference: %d sec and %d pending transactions, remove it: %r" % (time_diff, len(node.trans), node))
                        self.rt.remove_node(node_id)
                        continue
                    node.ping(socket=self.server.socket, sender_id=self.node._id)

            time.sleep(1)
