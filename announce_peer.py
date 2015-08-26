import logging
import time
import sys
from btdht import DHT

# Enable logging at DEBUG level
loglevel = logging.INFO
formatter = logging.Formatter("[%(levelname)s@%(created)s] %(message)s")
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logging.getLogger("btdht").setLevel(loglevel)
logging.getLogger("btdht").addHandler(stdout_handler)

logger = logging.getLogger(__name__)
logger.setLevel(loglevel)
logger.addHandler(stdout_handler)

#current_magnet = "deca7a89a1dbdc4b213de1c0d5351e92582f31fb".decode("hex")
current_magnet = "5D0269557095FC7A05AB23BAD467FE7BF307AAB1".decode("hex")

if __name__ == "__main__":

    # Start DHT Node on port 60000
    dht = DHT(host='0.0.0.0', port=60000)
    dht.start()

    # Boostrap it
    dht.bootstrap('router.bittorrent.com', 6881)

    # Find peers for the hash
    dht.ht.add_hash(current_magnet)

    res = []
    for count in xrange(20):
        logger.info("DHT Nodes found: %d" % (dht.rt.count()))
        logger.info("Bad DHT nodes found: %d" % (dht.rt.bad_count()))
        logger.info("Total peers found: %d" % (dht.ht.count_all_peers()))

        # How many peers at this moment?
        peers = dht.ht.get_hash_peers(current_magnet)
        for peer in peers:
            res.append((peer))
            #logger.info("Found peer: %s:%d" % (peer[0],peer[1]))
            #pnode = Node(peer[0],peer[1],'target')
            #pnode.announce_peer(peer[2],current_magnet)
        if len(peers) > 0:
            #dht.ht.remove_hash(current_magnet)
            break;    
                        
        time.sleep(10)

    # announce peer
    dht.announces.add_hash(current_magnet)

    time.sleep(60)
    
    logger.info("Found peers (total): %d" % (len(res)))
    logger.info("Found peers (uniq): %d" % (len(set(res))))
    dht.stop()
