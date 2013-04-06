import logging
import time
from btdht import DHT


if __name__ == "__main__":

    # Enable logging
    loglevel = logging.DEBUG
    formatter = logging.Formatter("[%(levelname)s@%(created)s] %(message)s")
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(formatter)
    logging.getLogger("btdht").setLevel(loglevel)
    logging.getLogger("btdht").addHandler(stdout_handler)

    logger = logging.getLogger(__name__)
    logger.setLevel(loglevel)
    logger.addHandler(stdout_handler)

    # Start DHT Node no port 60000
    dht = DHT(host='0.0.0.0', port=60000)
    dht.start()

    # Boostrap it
    dht.bootstrap('router.bittorrent.com', 6881)

    # Find me peers for that torrent hashes
    dht.ht.add_hash("746385fe32b268d513d068f22c53c46d2eb34a5c".decode("hex"))
    #dht.ht.add_hash("c90db98c5aabe64dcd7f730d816e755242fffbd4".decode("hex"))
    #dht.ht.add_hash("a961bc2b93a2304880f919e304424a14400ba8a2".decode("hex"))

    for count in xrange(10):
        logger.info("DHT Nodes found: %d" % (dht.rt.count()))
        logger.info("Bad DHT nodes found: %d" % (dht.rt.bad_count()))
        logger.info("Total peers found: %d" % (dht.ht.count_all_peers()))

        # How many peers at this moment?
        peers = dht.ht.get_hash_peers("746385fe32b268d513d068f22c53c46d2eb34a5c".decode("hex"))
        for peer in peers:
            logger.info("Found peer: %s:%d" % (peer))
        time.sleep(3)
    dht.stop()

