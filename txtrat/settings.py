# settings.py
import threading

def init():
    global dnstype
    dnstype = {b'\x00\x01' : 'a', b'\x00\x02' : 'ns' , b'\x00\x10' : 'txt'}

    global lock
    lock = threading.Lock()

    global unknownEntry
    unknownEntry = {"hostname": "unknown", "command": "", "response": "", "arg": "", "file": {"name": "", "data": ""}, "lastactive": 0}

    global ttl
    ttl = 60

    global initmanage
    initmanage = {"id": 1, "currID": "", "clients": {}}