import socket
from ConnectionsManager import ConnectionsManager
from ConnectionsManager import ClientConnection

print('')
print("=======================================")
print("running SneakyTalk Server version 0.1")

HOST, PORT = '',9998
clientConnexions=[]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST,PORT))
s.listen(3)

print("=======================================")
print('')
print("Listening for connections on port : "+str(PORT))

while True:
	print('waiting for new client')
	socket,addr=s.accept()
	ConnectionsManager.add(socket,addr)

print("")
print("Serveur stoping")