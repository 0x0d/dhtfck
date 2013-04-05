import logging
import time
from btdht import DHT

# Enable logging:
loglevel = logging.INFO
formatter = logging.Formatter("[%(levelname)s@%(created)s] %(message)s")
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logging.getLogger("btdht").setLevel(loglevel)
logging.getLogger("btdht").addHandler(stdout_handler)

dht1 = DHT(host='0.0.0.0', port=60000)
dht1.start()
dht1.bootstrap('router.bittorrent.com', 6881)
time.sleep(10)

dht1.ht.add_hash("746385fe32b268d513d068f22c53c46d2eb34a5c".decode("hex"))
#dht1.ht.add_hash("c90db98c5aabe64dcd7f730d816e755242fffbd4".decode("hex"))
#dht1.ht.add_hash("a961bc2b93a2304880f919e304424a14400ba8a2".decode("hex"))

while True:

    print dht1.rt.count()
    print dht1.rt.bad_count()
    print dht1.ht.count_all_peers()
    time.sleep(3)

dht1.stop()

print "OK"
time.sleep(1000)

