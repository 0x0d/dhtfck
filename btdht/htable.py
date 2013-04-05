# -*- coding: utf-8 -*-

import threading
import random

class HashTable(object):

    def __init__(self):
        self.hashes = {}
        self.lock = threading.Lock()

    def add_hash(self, hash):
        with self.lock:
            if hash not in self.hashes:
                self.hashes[hash] = []

    def remove_hash(self, hash):
        with self.lock:
            if hash in self.hashes:
                del self.hashes[hash]

    def add_peer(self, hash, peer):
        with self.lock:
            if hash in self.hashes:
                self.hashes[hash].append(peer)

    def remove_peer(self):
        return

    def count(self):
        return len(self.hashes)

