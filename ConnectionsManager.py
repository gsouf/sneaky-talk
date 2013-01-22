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
        if decodedData.startswith("/"):

            # searching for : /command[ ]content
            #                          ^
            spaceIndex=decodedData.find(" ")

            #if no space it means that there is no content
            if(-1 == spaceIndex):
                command=decodedData.lstrip('/')
                content=""
            else:
                command=decodedData.lstrip('/')[:spaceIndex-1]
                content=decodedData[spaceIndex+1:].lstrip(" ")

            self.routeCommand(command,content)

    # analyse the given command to make the associated action
    def routeCommand(self,command="",content=""):
        
        # /say -[idReceiver] [message]
        #  => he sends a [message] to [idReceiver]
        if command==Command.SAY:
            
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

        # /list
        # he asks to list the users logged
        elif command==Command.LIST:
            self.sendList()

        # /setname
        # he asks to change his pseudo
        elif command==Command.SETNAME:
            if len(content)>0:
                name=content
                self.setName(name)
        # /logout
        elif command==Command.LOGOUT:
            self.logout()
        # /setavailability
        elif command==Command.SETAVAILABILITY:
            if(int(content)!=0 and int(content)!=1):
                content=2
            self.availability=content
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
        data="/"+Command.WRITE+" -"+str(senderId)+" "+message
        print("@"+str(self.id)+" "+data)
        self.socket.sendall(data.encode('utf-8'))
    #
    # /userslist [jsonized users] 
    # == send a json representation of the users logged in
    def sendList(self):
        data = "/"+Command.USERLIST+" "
        data+= ConnectionsManager.getJsonList()
        self.socket.sendall(data.encode('utf-8'))
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
        ConnectionsManager.broadcast("/"+Command.REFRESH+" "+json.dumps(self.publicRepresentation()))
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
            ConnectionsManager.broadcast("/"+Command.LOGOUT+" "+str(client.id))

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

    #send a messager to all of the clients
    def broadcast(message=""):
        for client in ConnectionsManager.clients:
            client.socket.sendall(message.encode("utf-8"))