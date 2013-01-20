import socket, threading, json

class Command(object):
    SAY="say"
    LIST="list"
    SETNAME="setname"
    LOGOUT="logout"


#   CLIENT THREAD   #
#                   #
class ClientConnection(threading.Thread):
    def __init__(self, socket,address):
        threading.Thread.__init__(self)
        self.socket  = socket
        self.address = address
        self.socket.setblocking(True)
        self.socket.settimeout(20)
        self.id=None
        self.name="foo"

    def run(self):
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                # something has been received !
                # Route it now !
                self.routeData(data.decode('utf8'))
            except socket.timeout:
                break
        ConnectionsManager.disconnect(self)


    def routeData(self,decodedData):

        if decodedData.startswith("/"):
            spaceIndex=decodedData.find(" ")
            if(-1 == spaceIndex):
                command=decodedData.lstrip('/')
                content=""
            else:
                command=decodedData.lstrip('/')[:spaceIndex-1]
                content=decodedData[spaceIndex+1:].lstrip(" ")

            #Route the command :
            if command==Command.SAY:
                #the syntaxe is : "/say -idReceiver message"
                if "-"==content[0:1]:
                    # searchong for "/say -idReceiver[ ]message"
                    #                                 ^
                    spaceIndexArg=content.find(" ")
                   
                    #-1 error (no space=>something is missing)
                    # 0 impossible (dash position)
                    # 1 error (number expected)
                    # so we only check >1
                    if(spaceIndexArg>1):
                        receiver=content[1:spaceIndexArg]
                        if receiver.isdigit():
                            message=content[spaceIndexArg+1:]
                            self.sayTo(idReceiver=receiver,message=message)

            elif command==Command.LIST:
                self.sendList()

            elif command==Command.SETNAME:
                spaceIndex=decodedData.find(" ")
                if spaceIndex>1:
                    name=decodedData[spaceIndex+1:]
                    self.setName(name)
            elif command==Command.LOGOUT:
                ConnectionsManager.disconnect(self)

    def sayTo(self,idReceiver=None,client=None,message=None):
        if(client==None and idReceiver!=None):
            client=ConnectionsManager.getClientById(idReceiver)

        print("say to : "+str(idReceiver)+", from :"+str(self.id)+" : "+message)

        if(client==None):
            pass #TODO
        else:
            client.sendMessage(message=message,senderId=self.id)

    def sendMessage(self,message,senderId):
        data="/write -"+str(senderId)+" "+message
        print("@"+str(self.id)+" "+data)
        self.socket.sendall(data.encode('utf-8'))

    def sendList(self):
        data = "/userslist "
        data+= ConnectionsManager.getJsonList()
        self.socket.sendall(data.encode('utf-8'))

    def setName(self,newName):
        self.name=newName
        self.refresh()
    
    def refresh(self):
        ConnectionsManager.broadcast("/refresh "+json.dumps(self.publicRepresentation()))
    
    def publicRepresentation(self):
        return {'id':self.id,'name':self.name}


#   CONNEXIONS   #
#                #
class ConnectionsManager(object):
    clients=[]
    maxId=1

    def add(socket,addr):
        client=ClientConnection(socket,addr)
        client.id=ConnectionsManager.maxId
        ConnectionsManager.maxId+=1
        ConnectionsManager.clients.append(client)
        print(repr(addr)+" just connected")
        print(ConnectionsManager.clientSize())
        client.start()


    def clientSize():
        return len(ConnectionsManager.clients)

    def disconnect(client):
        ConnectionsManager.clients.remove(client)
        client.socket.close()
        print("disconnection of "+repr(client.address))
        print(ConnectionsManager.clientSize())
        ConnectionsManager.broadcast("/logout "+str(client.id))

    def getClientById(id):
        if None==id:
            return None
        
        for client in ConnectionsManager.clients:
            print(str(client.id)+","+str(id))
            if int(id)==client.id:
                return client

        return None

    def getJsonList():
        clientlist=[]
        for client in ConnectionsManager.clients:
            clientlist.append(client.publicRepresentation())
        return json.dumps(clientlist,separators=(',',':'))

    def broadcast(message=""):
        for client in ConnectionsManager.clients:
            client.socket.sendall(message.encode("utf-8"))