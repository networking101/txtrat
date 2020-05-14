# settings.py
import threading

def init():
    global dnstype
    dnstype = {b'\x00\x01' : 'a', b'\x00\x02' : 'ns' , b'\x00\x10' : 'txt'}

    global lock
    lock = threading.Lock()