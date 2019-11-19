# Description of code
## seed.py
- It forks a process that becomes the seed node. It maintains a list of clients. On acquiring a connection request from a client, it first verifies the client and sends it the client list. It then waits till the client is initialized and then adds the client to client list. This process is repeated forever

## client.py
- Client first connects to the seed node and gets client list. From that it selects few neighbours and connects to them. This is the initialization part of client after which it informs the seed and closes connection with it.
- Then the client waits for incomming connections from new clients and broadcasts 10 messages at 5 second intervals. It writes the log of these messages to outputfile.txt

# Code usage
Initialization - 
Change IP in seed_node.txt to IP of machine with seed node

For seed node -
python3 seed.py --numSeeds 1

For client node - (each on a different machine)
sudo python3 client.py --numSeeds 1 --numClients 1 --delay 2 --interface wlp2s0
