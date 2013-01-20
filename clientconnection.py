import socket, threading
import ConnectionsManager

class ClientConnection(threading.Thread):
    def __init__(self, socket,address):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address= address

    def run(self):
        while True:
            data = self.socket.recv(1024)
            if not data:
                break
            print('%s:%s said :' % self.address)
            print(repr(data))
        ConnectionsManager.disconnect(self)
        