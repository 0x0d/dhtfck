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
    # dht = DHT(host='0.0.0.0', port=60000)
    dht = DHT(host='0.0.0.0', port=0)
    dht.start()

    # Boostrap it
    dht.bootstrap('router.bittorrent.com', 6881)

    CurrentMagnet = "746385fe32b268d513d068f22c53c46d2eb34a5c"
    # CurrentMagnet = "4CDE5B50A8930315B479931F6872A3DB59575366"

    # Find me peers for that torrent hashes
    dht.ht.add_hash(CurrentMagnet.decode("hex"))
    TotalCnt = 0
    Res = []
    for count in xrange(10):
        logger.info("DHT Nodes found: %d" % (dht.rt.count()))
        logger.info("Bad DHT nodes found: %d" % (dht.rt.bad_count()))
        logger.info("Total peers found: %d" % (dht.ht.count_all_peers()))

        # How many peers at this moment?
        peers = dht.ht.get_hash_peers(CurrentMagnet.decode("hex"))
        for peer in peers:
            TotalCnt += 1
            Res.append((peer))
            logger.info("Found peer: %s:%d" % (peer))
        time.sleep(3)
    logger.info("Found peers (total): %d" % (TotalCnt))
    logger.info("Found peers (uniq): %d" % (len(set(Res))))
    dht.stop()
