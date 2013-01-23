import socket, threading, json
from Command import Command

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
        self.availability=0 # 0=hidden 1=available 2=busy

    #the listening thread
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
            except socket.error:
                print("exeption")
                break
        if(self in ConnectionsManager.clients):
            ConnectionsManager.disconnect(self)


    # analyse the sent data to know what to do
    def routeData(self,decodedData):
        # expected syntaxe is :
        # /[command] [content]

        # looking if it is a command
        # all commands begin by a slash
        try:
            decodedJson=json.loads(decodedData)
            
            if 'command' in decodedJson:
                command=decodedJson['command']
                self.routeCommand(command,decodedJson)
            else:
                print("no command : "+decodedJson)
            
        except ValueError:
            print("not json")

    # analyse the given command to make the associated action
    def routeCommand(self,command="",content=""):
        
        # SAY
        # @param : idreceiver
        # @param : message
        if command==Command.SAY:
            
            if 'idreceiver' in content:
                if type(content['idreceiver'] == int):
                    if 'message' in content:
                        if type(content['message'] == str):
                            receiver=content['idreceiver']
                            message=content['message']
                            self.sayTo(idReceiver=receiver,message=message)
                        

        # LIST
        elif command==Command.LIST:
            self.sendList()

        # SETNAME
        # @param : name
        elif command==Command.SETNAME:
            if 'name' in content:
                if type(content['name'] == str):
                    name=content['name']
                    self.setName(name)
        # LOGOUT
        elif command==Command.LOGOUT:
            self.logout()
        # SETAVAILABILITY
        elif command==Command.SETAVAILABILITY:
            if 'availability' in content:
                if type(content['availability']) == int:
                    self.availability=content['availability']
                    self.sendRefresh()
   

    # say something to someone
    def sayTo(self,idReceiver=None,client=None,message=None):
        if(client==None and idReceiver!=None):
            client=ConnectionsManager.getClientById(idReceiver)

        print("say to : "+str(idReceiver)+", from :"+str(self.id)+" : "+message)

        if(client==None):
            pass #TODO
        else:
            client.sendMessage(message=message,senderId=self.id)

    ###########################
    # DATA SEND TO THE CLIENT
    #
    # /write -[idSender] [message]
    # == a [message] is sent by [idSender]
    # == if id sender is not set or if = 0 this means that the sender is the server
    def sendMessage(self,message,senderId):
        message=Command.create(command=Command.WRITE,senderid=str(senderId),content=message)
        print("@"+str(self.id)+" "+message)
        ConnectionsManager.sendTo(message,client=self)
    #
    # /userslist [jsonized users] 
    # == send a json representation of the users logged in
    def sendList(self):
        message=Command.create(command=Command.USERLIST,users=ConnectionsManager.getJsonList())
        ConnectionsManager.sendTo(message,client=self)
    #
    # will change the name call sendRefresh for broadcasting the new name
    #
    def setName(self,newName):
        self.name=newName
        self.sendRefresh()
    #
    # /refresh [jsonized user]
    # == will broadcast the public properties of this user
    def sendRefresh(self):
        message=Command.create(command=Command.REFRESH,user=self.publicRepresentation())
        ConnectionsManager.broadcast(message)
    #
    #
    # /logout
    # => into ConnectionsManager.disconnect()
    def logout(self):
        ConnectionsManager.disconnect(self)
    #
    ##############################


    def publicRepresentation(self):
        return {'id':self.id,'name':self.name,'availability':self.availability}


#   CONNEXIONS   #
#                #
class ConnectionsManager(object):
    clients=[]
    maxId=1

    # add a client to the client list
    # and starts the socket listening
    def add(socket,addr):
        # creat the clientconnection object from the given socket
        client=ClientConnection(socket,addr)
        # giving him a free id
        client.id=ConnectionsManager.maxId
        # increment the global id for the next user
        ConnectionsManager.maxId+=1
        # add the client to the client list
        ConnectionsManager.clients.append(client)
        #start to listen what he says
        client.start()

        print(repr(addr)+" just connected")
        print(ConnectionsManager.clientSize())
        

    # number of clients
    def clientSize():
        return len(ConnectionsManager.clients)

    #disconnect the given client
    def disconnect(client):

        try:
            # remove it from the list
            ConnectionsManager.clients.remove(client)
            # close the socket listening
            client.socket.close()
            # broadcast the disconnexion
            message=Command.create(command=Command.LOGOUT,id=str(client.id))
            ConnectionsManager.broadcast(message)

            print("disconnection of "+repr(client.address))
            print(ConnectionsManager.clientSize())
        except ValueError:
            print('noting to disconnect or already disconnected')

    #return the client matching with the given id
    def getClientById(id):
        if None==id:
            return None
        
        for client in ConnectionsManager.clients:
            print(str(client.id)+","+str(id))
            if int(id)==client.id:
                return client

        return None

    #return a public jsonized list of client list
    def getJsonList():
        clientlist=[]
        for client in ConnectionsManager.clients:
            if client.availability>0:
                clientlist.append(client.publicRepresentation())
        return json.dumps(clientlist,separators=(',',':'))

    #broadcast a message
    def broadcast(message=""):
        for client in ConnectionsManager.clients:
            ConnectionsManager.sendTo(message,client=client)

    def sendTo(message,idclient=None,client=None):
        if client==None:
            client=ConnectionsManager.getClientById(idclient)

        if client!=None and type(message)==str:
            print("sendto : "+str(client.id)+ " - "+message)
            client.socket.sendall(message.encode("utf-8")+"\n")