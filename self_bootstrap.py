import logging
import time
import sys
from btdht import DHT

# Enable logging at DEBUG level
loglevel = logging.DEBUG
formatter = logging.Formatter("[%(levelname)s@%(created)s] %(message)s")
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logging.getLogger("btdht").setLevel(loglevel)
logging.getLogger("btdht").addHandler(stdout_handler)

logger = logging.getLogger(__name__)
logger.setLevel(loglevel)
logger.addHandler(stdout_handler)

if __name__ == "__main__":

    # Start DHT Node on port 60000
    dht = DHT(host='0.0.0.0', port=60000)
    dht.start()

    while True:
        continue
    
    # Boostrap it
    #dht.bootstrap('localhost', 6001)
