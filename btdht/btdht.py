# -*- coding: utf-8 -*-

import SocketServer
import socket
import threading
import time
import logging

from .defines import *
from .rtable import RoutingTable
from .htable import HashTable
from .bencode import bdecode, BTFailure
from .node import Node
from .utils import decode_nodes, encode_nodes, random_node_id, unpack_host, unpack_hostport

logger = logging.getLogger(__name__)

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
                logger.debug("Cannot find appropriate node for transaction: %r" % (trans_id.encode("hex")))
                return

        logger.debug("We found apropriate node %r for %r" % (node, node_id.encode("hex")))

        if trans_id in node.trans:
            logger.debug("Found and deleting transaction %r in node: %r" % (trans_id.encode("hex"), node))
            trans = node.trans[trans_id]
            node.delete_trans(trans_id)
        else:
            logger.debug("Cannot find transaction %r in node: %r" % (trans_id.encode("hex"), node))
            for trans in node.trans:
                logger.debug(trans.encode("hex"))
            return

        if "ip" in args:
            logger.debug("They try to SECURE me: %s", unpack_host(args["ip"]))

        t_name = trans["name"]
        if t_name == "find_node":
            node.update_access()
            logger.debug("find_node response from %r" % (node))
            if "nodes" in args:
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
            node.update_access()
            logger.debug("ping response for: %r" % (node))
        elif t_name == "get_peers":
            node.update_access()
            info_hash = trans["info_hash"]
            
            logger.debug("get_peers response for %r" % (node))

            if "token" in args:
                token = args["token"]
                logger.debug("Got token: %s" % (token.encode("hex")))
            else:
                token = None
                logger.error("No token in get_peers response from %r" % (node))

            if "values" in args:
                logger.debug("We got new peers for %s" % (info_hash.encode("hex")))
                values = args["values"]
                for addr in values:
                    hp = unpack_hostport(addr)
                    self.server.dht.ht.add_peer(info_hash, hp)
                    logger.debug("Got new peer for %s: %r" % (info_hash.encode("hex"), hp))
            if "nodes" in args:
                logger.debug("We got new nodes from %r" % (node))
                new_nodes = decode_nodes(args["nodes"])
                for new_node_id, new_node_host, new_node_port in new_nodes:
                    logger.debug("Adding %r %s:%d as new node" % (new_node_id.encode("hex"), new_node_host, new_node_port))
                    self.server.dht.rt.update_node(new_node_id, Node(new_node_host, new_node_port, new_node_id))

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
            node.pong(socket=self.server.socket, trans_id = trans_id, sender_id=self.server.dht.node._id, lock=self.server.send_lock)
            return
        elif query_type == "announce_peer":
            logger.debug("handle query announce_peer")
            node.pong(socket=self.server.socket, trans_id = trans_id, sender_id=self.server.dht.node._id, lock=self.server.send_lock)
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
    def __init__(self, host, port):
        self.node = Node(unicode(host), port, random_node_id())
        self.rt = RoutingTable()
        self.ht = HashTable()
        self.server = DHTServer((self.node.host, self.node.port), DHTRequestHandler)
        self.server.dht = self

        self.sample_count = SAMPLE_COUNT
        self.max_bootstrap_errors = MAX_BOOTSTRAP_ERRORS
        self.iteration_timeout = ITERATION_TIMEOUT
        self.gc_max_time = GC_MAX_TIME
        self.gc_max_trans = GX_MAX_TRANS

        self.randomize_node_id = RANDOMIZE_NODE_ID
        self.random_find_peers = RANDOM_FIND_PEERS

        self.running = False

        logger.debug("DHT Server listening on %s:%d" % (host, port))
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

        self.iterative_thread = threading.Thread(target=self.iterative)
        self.iterative_thread.daemon = True

    def start(self):
        self.server_thread.start()
        logger.debug("DHT server thread started")

    def bootstrap(self, boot_host, boot_port):

        logger.debug("Starting DHT bootstrap on %s:%d" % (boot_host, boot_port))
        boot_node = Node(boot_host, boot_port, "boot")
        self.rt.update_node("boot", boot_node)

        # Do cycle, while we didnt get enough nodes to start
        while self.rt.count() <= self.sample_count:

            if len(boot_node.trans) > self.max_bootstrap_errors:
                logger.error("Too many attempts to bootstrap, seems boot node %s:%d is down. Givin up" % (boot_host, boot_port))
                return False

            boot_node.find_node(self.node._id, socket=self.server.socket, sender_id=self.node._id)
            time.sleep(self.iteration_timeout)

        self.running = True
        
        self.iterative_thread.start()

        return True

    def iterative(self):
        logger.debug("Entering iterative node finding loop")

        while self.running:

            # find nodes
            if self.randomize_node_id:
                nid = random_node_id()
                nodes = self.rt.sample(self.sample_count)
            else:
                nid = self.node._id
                nodes = self.rt.get_close_nodes(nid, self.sample_count)

            for node_id, node in nodes:
                node.find_node(nid, socket=self.server.socket, sender_id=self.node._id)

            # garbage collector
            nodes = self.rt.sample(int(self.rt.count() / 2))
            #nodes = self.rt.get_nodes().items()
            for node_id, node in nodes:
                time_diff = time.time() - node.access_time
                if time_diff > self.gc_max_time:
                    if len(node.trans) > self.gc_max_trans:
                        logger.debug("We have node with last access time difference: %d sec and %d pending transactions, remove it: %r" % (time_diff, len(node.trans), node))
                        self.rt.remove_node(node_id)
                        continue
                    node.ping(socket=self.server.socket, sender_id=self.node._id)

            # peer search
            for hash_id in self.ht.hashes.keys():
                if self.random_find_peers:
                    nodes = self.rt.sample(self.sample_count)
                else:
                    nodes = self.rt.get_close_nodes(hash_id, self.sample_count)
                for node_id, node in nodes:
                    node.get_peers(hash_id, socket=self.server.socket, sender_id=self.node._id)

            time.sleep(self.iteration_timeout)

    def stop(self):
        self.running = False

        self.iterative_thread.join()
        logger.debug("Stopped iterative loop")

        self.server.shutdown()
        self.server_thread.join()
        logger.debug("Stopped server thread")
           
