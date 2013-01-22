import json

class Command(object):
    # list of commands
    
    # client=>serveur commands
    SAY="say"
    LIST="list"
    SETNAME="setname"
    SETAVAILABILITY="setavailability"
    

    # serveur=>client commands
    WRITE="write"
    USERLIST="userlist"
    REFRESH="refresh"
    


    # bidirectional commands
    LOGOUT="logout"

    def create(**kwarg):
        if 'command' not in kwarg:
            return False

        return json.dumps(kwarg)