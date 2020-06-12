# settings.py
import threading

def init():
    global dnstype
    dnstype = {b'\x00\x01' : 'a', b'\x00\x02' : 'ns' , b'\x00\x10' : 'txt', b'\x00\x06': 'soa'}

    global lock
    lock = threading.Lock()

    global unknownEntry
    unknownEntry = {"hostname": "unknown", "command": "", "args": [], "response": "", "lastactive": 0}

    global ttl
    ttl = 60

    global initmanage
    initmanage = {"id": 1, "currID": "", "clients": {}}