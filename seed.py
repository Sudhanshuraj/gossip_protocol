import os
import argparse
import json
from socket import *
import pdb

def get_ip():
	# gives the ip of this machine
	s = socket(AF_INET, SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = str(s.getsockname()[0])
	s.close()
	return ip

if __name__ == "__main__":
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("--numSeeds", help="number of seeds")
	args = parser.parse_args()

	fork = 1
	child_pid = [0] * int(args.numSeeds)
	
	for i in range(int(args.numSeeds)):
		child_pid[i] = os.fork()
		if child_pid[i] == 0: # child
			# make Seed nodes
			seed = socket(AF_INET, SOCK_STREAM)
			seed.bind((get_ip(), 9000 + i))
			seed.listen(5)
			CL = []

			while True: # accept clients eternally
				c,a = seed.accept()
				req = c.recv(10000)
				if req != b'send CL': # validate client
					print("invalid request from", a)
				else:
					print("sending CL") # send CL
					c.sendall(json.dumps(CL).encode('ASCII'))
					print("CL sent")
					while True: # confirm client has initialized
						data = c.recv(10000)
						if data != b'':
							# recieve from client the socket on which it will accept connections
							# from other clients and add it to CL
							data = json.loads(data.decode('ASCII'))
							CL.append(data)
							break
					print("connected to", CL[-1])
				c.shutdown(SHUT_RDWR) # close connection to client
				c.close()
			break
		else: # parent
			pass

	if fork > 0: # wait for seed to close
		for i in range(int(args.numSeeds)):
			pid, status = os.waitpid(child_pid[i], 0)
			print("wait returned, pid = %d, status = %d" % (pid, status))
