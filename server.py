import socket
from ConnectionsManager import ConnectionsManager
from ConnectionsManager import ClientConnection


HOST, PORT = '',9998
clientConnexions=[]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST,PORT))
s.listen(3)
while True:
	print('waiting for new client')
	socket,addr=s.accept()
	ConnectionsManager.add(socket,addr)
