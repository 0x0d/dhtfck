WTF is this?
----------------

This is my BitTorrent Distributed Hash Tables research project. 

Where i can use it?
-------------------
This tool has several main purposes:

1. To be a custom Python BTDHT realization, which you can easily use in your application. You can play with DHT protocol, fuzz it, change DHT internal timing limits etc.
2. Act as my Proof-Of-Concept of DHT amplification DDoS attack

Is BitTorrent protocol included?
--------------------------------
No. This is just DHT.

Example?
--------
Lookup for BitTorrent peers for *746385fe32b268d513d068f22c53c46d2eb34a5c* hash in BitTorrent DHT:

```python
import time
from btdht import DHT 

current_magnet = "746385fe32b268d513d068f22c53c46d2eb34a5c".decode("hex")

if __name__ == "__main__":

    # Start DHT Node on port 60000
    dht = DHT(host='0.0.0.0', port=60000)
    dht.start()
    
    # Boostrap it
    dht.bootstrap('router.bittorrent.com', 6881)
    
    # Find me peers for that torrent hashes
    dht.ht.add_hash(current_magnet)

    res = []  
    for count in xrange(5):
        print("DHT Nodes found: %d" % (dht.rt.count()))
        print("Bad DHT nodes found: %d" % (dht.rt.bad_count()))
        print("Total peers found: %d" % (dht.ht.count_all_peers()))
        
        # How many peers at this moment?
        peers = dht.ht.get_hash_peers(current_magnet)
        for peer in peers:
            res.append((peer))
            print("Found peer: %s:%d" % (peer))
        time.sleep(3)
    print("Total peers found: %d" % (len(res)))
    dht.stop()
```
