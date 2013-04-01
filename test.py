import logging
from btdht import DHT

# Enable logging:
loglevel = logging.INFO
formatter = logging.Formatter("[%(levelname)s@%(created)s] %(message)s")
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logging.getLogger("btdht").setLevel(loglevel)
logging.getLogger("btdht").addHandler(stdout_handler)

dht1 = DHT(host='0.0.0.0', port=80, boot_host='router.bittorrent.com', boot_port=6881)
