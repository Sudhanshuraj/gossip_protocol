from socket import *
import os
import argparse
import json
import random
import pdb
import time
import select
import hashlib

def create_msg(msg):
	# create message in the format given in problem statement
	return str(time.ctime().replace(":", "-"))+":"+get_ip()+":"+hashlib.sha224(msg).hexdigest()

def get_ip():
	# gives the ip of this machine
	s = socket(AF_INET, SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = str(s.getsockname()[0])
	s.close()
	return ip

def send_to_all(n_socs, msg_to_send):
	# send the message to all the sockets in n_socs
	for soc in n_socs:
		soc.sendall(msg_to_send.encode("ASCII"))

if __name__ == "__main__":
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("--numSeeds", help="number of seeds")
	parser.add_argument("--numClients", help="number of clients")
	parser.add_argument("--delay", help="delay in network")
	parser.add_argument("--interface", help="interface id for communication")
	args = parser.parse_args()

	num_clients = int(args.numClients)
	net_delay = args.delay
	i_id = args.interface

	# make Seed nodes
	fork = 1
	child_pid = [0] * int(args.numClients)
	
	
	file_seed = open("seed_node.txt",'r')
	seed_info = file_seed.readline()
	seed_info = seed_info.split("\t")
	seed_ip = seed_info[0]
	seed_port = int(seed_info[1])
	
	cmd = "tcset %s --overwrite --delay %ss --dst-network %s"%(i_id, net_delay, seed_ip)
	os.system(cmd)

	cmd = "rm -f ./outputfile*"
	os.system(cmd)
	
	for i in range(int(args.numClients)):
		child_pid[i] = os.fork()
		fork *= int(child_pid[i] > 0)
		if fork == 0: # child

			client = socket(AF_INET, SOCK_STREAM) # client node

			listener = socket(AF_INET, SOCK_STREAM) # client will accept other clients on listner socket
			listener.bind((get_ip(), 10000 + i))
			listener.listen(5)
			if num_clients > 1:
				open("outputfile%s_%s.txt"%(str(listener.getsockname()[0]), str(listener.getsockname()[1])), 'w', 1)
			else:
				open("outputfile.txt", 'w', 1)

			while True: # connect to seed
				try:
					client.connect((seed_ip, seed_port))
					print("connected to seed", client.getsockname())
					break
				except:
					print("refused connection to seed sleeping for 5 seconds", client.getsockname())
					time.sleep(5)

			# validate itself as client and get CL
			client.sendall(b'send CL')
			CL = client.recv(10000)
			CL = json.loads(CL.decode('ASCII'))
			if num_clients > 1:
				# print("CL RECVD: ", CL,  file=open("outputfile%s_%s.txt"%(str(listener.getsockname()[0]), str(listener.getsockname()[1])), 'a', 1))
				pass
			else:
				# print("CL RECVD: ", CL,  file=open("outputfile.txt", 'a', 1))
				pass


			n_socs = [] # message sockets
			if CL == []: # if first client
				# print("first client", listener.getsockname())
				pass
			else:
				random.shuffle(CL) # get neighbours from CL
				neighbours = CL[:random.randrange(1, 5)]

				for n in neighbours: # estabilish connection with neighbours
					s = socket(AF_INET, SOCK_STREAM)
					while True:
						try:
							s.connect((n[0], n[1])) # CL had listener sockets of clients
							cmd = "tcset %s --overwrite --delay %ss --dst-network %s"%(i_id, net_delay, n[0])
							os.system(cmd)
							break
						except:
							print("refused connection to neighbour", n, "sleeping for 5 seconds", listener.getsockname())
							time.sleep(5)

					s.sendall(b'hey neighbour') # validate itself to neighbour client
					data = b''
					while True: # recieve from neighbour its reciever
						data = s.recv(10000)
						if data != b'':
							data = json.loads(data.decode('ASCII')) # get a message socket from neighbour
							n_socs.append(socket(AF_INET, SOCK_STREAM)) # make new message socket
							break

					while True:
						try:
							n_socs[-1].connect((n[0],data[1])) # connect to the message socket of neighbour
							break
						except:
							print("refused connection to neighbour's receiver", data, "sleeping for 5 seconds", listener.getsockname())
							time.sleep(5)

					s.shutdown(SHUT_RDWR) # close connection socket to neighbour
					s.close()
					print(listener.getsockname(), "connected to neighbour", n)

					# test message connection
					n_socs[-1].sendall(b'mike check! new client')
					# print("dummy message sent by", listener.getsockname(), " -- ","mike check! new client")
					first_recvd = n_socs[-1].recv(10000)
					# print("dummy message recieved by", listener.getsockname(), ":", first_recvd)					

			client.sendall(json.dumps(listener.getsockname()).encode('ASCII')) # close connection with seed
			client.shutdown(SHUT_RDWR)
			client.close()

			listener.setblocking(0)
			print("accepting", listener.getsockname())
			time_now = time.time()
			ML = []
			i = 0
			while True: # accept connections from other clients
				ready_to_read, ready_to_write, in_error = select.select(n_socs, n_socs, [], 0)	# returns whether anything to read from the sockets in CL
				try:	# checks whether any connection is waiting to be connected on the listener socket
					c,a = listener.accept()
					req = c.recv(10000)
					if req != b'hey neighbour': # validate client
						print(listener.getsockname(), "invalid request from", a)
						pass
					else:
						s = socket(AF_INET, SOCK_STREAM) # make new message socket and send to new neighbour
						s.listen(5)
						c.sendall(json.dumps(s.getsockname()).encode('ASCII'))
						c1,a1 = s.accept() # connect to the message socket of neighbour
						n_socs.append(c1)

						s.shutdown(SHUT_RDWR)
						s.close()

					print(listener.getsockname(), "connected to new neighbour")
					c.shutdown(SHUT_RDWR)
					c.close()

					# test message connection
					test_msg_recvd = n_socs[-1].recv(10000)
					# print("dummy message recieved by", listener.getsockname(), ":", test_msg_recvd)
					n_socs[-1].sendall(b'mike check! old client')
					# print("dummy message sent by", listener.getsockname(), " -- ","mike check! old client")
				except:
					pass

				if ready_to_read != []:	# something to read from the sockets
					for soc in ready_to_read:
						recvd = (soc.recv(95)).decode("ASCII")
						if recvd.split(":")[-1] not in ML:
							ip = str(soc.getsockname()[0])
							if num_clients > 1:
								print("MSG RECVD at %s from %s: "%(time.ctime(), ip), recvd, file=open("outputfile%s_%s.txt"%(str(listener.getsockname()[0]), str(listener.getsockname()[1])), 'a', 1 ))
							else:
								print("MSG RECVD at %s from %s: "%(time.ctime(), ip), recvd, file=open("outputfile.txt", 'a', 1))

							print("MSG RECVD at %s from %s: "%(time.ctime(), ip), recvd)
							send_to_all(n_socs, recvd)
							ML.append(recvd.split(":")[-1])
				if time.time() - time_now > 5 and i < 10:	# send 10 messages at interval of 5 secs
					msg_to_send = create_msg(b'Sending message no: %d by %b'%(i, (str(listener.getsockname())).encode("ASCII") ))
					if num_clients > 1:
						# print("MSG SENT: %s"%(msg_to_send), file=open("outputfile%s_%s.txt"%(str(listener.getsockname()[0]), str(listener.getsockname()[1])), 'a', 1))
						pass
					else:
						# print("MSG SENT: %s"%(msg_to_send), file=open("outputfile.txt", 'a', 1))
						pass

					# print("MSG SENT: %s"%(msg_to_send))
					send_to_all(n_socs, msg_to_send)
					ML.append(msg_to_send.split(":")[-1])
					time_now = time.time()
					i+=1		

			listener.shutdown(SHUT_RDWR)
			listener.close()

			break
		else:
			# parent
			pass

	if fork > 0:
		for i in range(int(args.numClients)):
			pid, status = os.waitpid(child_pid[i], 0)
			print("wait returned, pid = %d, status = %d" % (pid, status))
