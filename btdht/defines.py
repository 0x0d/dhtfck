
# How many DHT nodes for bootstrap
BOOTSTRAP_COUNT = 1

# How many DHT nodes we query per ITERATION_TIMEOUT
SAMPLE_COUNT = 8

# How often we query DHT nodes
ITERATION_TIMEOUT = 2

# Exit if error count > then these
MAX_BOOTSTRAP_ERRORS = 5

# Searching for dead nodes and cleanup them every GC_MAX_TIME
GC_MAX_TIME = 60
GX_MAX_TRANS = 5

# If True, we start to generate random node_id every ITERATION_TIMEOUT. This can greatly increase speed of DHT node harvesting, but slows down BT peers harvesting.
RANDOMIZE_NODE_ID = False

# If True, we start to send find_peers message to every known DHT node instead of SAMPLE_COUNT. This can greatly increase speed of DHT node harvesting, but slows down BT peers harvesting.
RANDOM_FIND_PEERS = False
