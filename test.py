import logging
import time
from btdht import DHT

# Enable logging:
loglevel = logging.DEBUG
formatter = logging.Formatter("[%(levelname)s@%(created)s] %(message)s")
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logging.getLogger("btdht").setLevel(loglevel)
logging.getLogger("btdht").addHandler(stdout_handler)

dht1 = DHT(host='0.0.0.0', port=60000)
dht1.start()
dht1.bootstrap('router.bittorrent.com', 6881)

time.sleep(10)
dht1.stop()

print "OK"
time.sleep(1000)

