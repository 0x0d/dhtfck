# -*- coding: utf-8 -*-

import threading

class HashTable(object):

    def __init__(self):
        self.hashes = {}
        self.lock = threading.Lock()

    def add_hash(self, hash):
        with self.lock:
            if hash not in self.hashes:
                self.hashes[hash] = set([])

    def remove_hash(self, hash):
        with self.lock:
            if hash in self.hashes:
                del self.hashes[hash]

    def add_peer(self, hash, peer):
        with self.lock:
            if hash in self.hashes:
                if peer not in self.hashes[hash]:
                    self.hashes[hash].add(peer)

    def remove_peer(self, hash, peer):
        with self.lock:
            if hash in self.hashes:
                peer_set = self.hashes[hash]
                if peer in peer_set:
                    peer_set.remove(peer)
        return peer_set

    def count_hash_peers(self, hash):
        return len(self.hashes[hash])
    
    def get_hash_peers(self, hash):
        return self.hashes.get(hash,None)

    def count_hashes(self):
        return len(self.hashes)

    def get_hashes(self):
        return self.hashes

    def count_all_peers(self):
        tlen = 0
        for hash in self.hashes.keys():
            tlen += len(self.hashes[hash])
        return tlen

