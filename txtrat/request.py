# request.py
import dnszones


def buildquestion(domainname):
    qbytes = b''

    for part in domainname:
        length = len(part)
        qbytes += bytes([length])

        for char in part:
            qbytes += ord(char).to_bytes(1, byteorder='big')

    return qbytes

# gets the parts of the domain
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

# This function will parse out the sections of the DNS request.  The first part of the response will be generated (up to the end of the query section)
# The zone records and rectype will be needed to generate the Answers section
def parseRequest(data):

    # Transaction ID
    TransactionID = data[:2]

    # Get the flags
    Flags = getflags(data[2:4])

    # Get answer for query
    domainname, rectype = getquestiondomain(data[12:])      # Argument data is everything from the domain name on (ex: b'\x07koratxt\x03net\x00\x00\x10\x00\x01')
                                                            # domainname: array of domain parts (ex: ['koratxt', 'net', ''])
                                                            # rectype: hex of query type, txt, ns, a, (ex: b'\x00\x10')

    # Question Count
    QDCOUNT = b'\x00\x01'

    # Answer Count
    if rectype == b'\x00\x01' and (domainname[0] == "ns1" or domainname[0] == "ns2"):
        records = dnszones.getzone(domainname[-4:], rectype)
    else:
        records = dnszones.getzone(domainname[-3:], rectype)     # argument domainname and rectype
    #if records is None:                                     # records: an array dns type record (ex: [{'name': '@', 'ttl': 400, 'value': 'Hello World!'}])
    #    return None                                         # return None if record does not exist in .zone file
    ANCOUNT = (len(records)).to_bytes(2, byteorder='big')

    # Nameserver Count
    NSCOUNT = (0).to_bytes(2, byteorder='big')

    # Additonal Count
    ARCOUNT = (0).to_bytes(2, byteorder='big')

    dnsheader = TransactionID+Flags+QDCOUNT+ANCOUNT+NSCOUNT+ARCOUNT

    # Create question portion of DNS body
    dnsquestion = buildquestion(domainname)

    # Put together the dns reponse body up to the query
    dnsquerybody = dnsheader + dnsquestion + rectype + (1).to_bytes(2, byteorder='big')

    return (dnsquerybody, records, rectype, domainname[:len(domainname)-3])