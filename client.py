import socket



HOST, PORT = "localhost", 9998

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall(b"/logout")
while True:
	data = s.recv(1024)
	
	if not data:
		break

	print('Received', repr(data))

s.close()