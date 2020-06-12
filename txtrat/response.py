# response.py
import struct

# Default response.  This is used if normal DNS requests are send (no C2)
def genResponse(records, rectype):

    # A record
    if rectype == b'\x00\x01':
        rbytes = b''
        
        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.connect(('8.8.8.8', 80))
        #ip_address = s.getsockname()[0]
        #s.close()

        for record in records:
            rbytes += b'\xc0\x0c' + rectype + b'\x00\x01'
            rbytes += int(record['ttl']).to_bytes(4, byteorder='big')

            rbytes += b'\x00\x04'           # size of ip address
            for part in record['value'].split('.'):
                rbytes += bytes([int(part)])

    # SOA record (if ns request on name server, return start of authority record)
    elif rectype == b'\x00\x06':
        rbytes = b''
        for record in records:
            jumpback = b'\xc0\x0c'
            if len(record['name'].split('.')) == 4:
                jumpback = b'\xc0\x10'

            rbytes += jumpback + rectype + b'\x00\x01'
            rbytes += int(record['ttl']).to_bytes(4, byteorder='big')
            
            parts = record['mname'].split('.')
            answerbody = (len(parts[0])).to_bytes(1, byteorder='big')
            answerbody += (parts[0]).encode() + jumpback

            parts = record['rname'].split('.')
            answerbody += (len(parts[0])).to_bytes(1, byteorder='big')
            answerbody += (parts[0]).encode() + jumpback

            answerbody += struct.pack(">I", record['serial'])
            answerbody += struct.pack(">I", record['refresh'])
            answerbody += struct.pack(">I", record['retry'])
            answerbody += struct.pack(">I", record['expire'])
            answerbody += struct.pack(">I", record['minimum'])

            rbytes += (len(answerbody)).to_bytes(2, byteorder='big')
            rbytes += answerbody

    # NS record
    elif rectype == b'\x00\x02':
        rbytes = b''
        for record in records:
            rbytes += b'\xc0\x0c' + rectype + b'\x00\x01'
            rbytes += int(record['ttl']).to_bytes(4, byteorder='big')

            rbytes += b'\x00\x06'           # size of name server response (only need to calculate 'ns1.' because the rest is stored at 0xc00c)
            parts = record['value'].split('.')
            rbytes += (3).to_bytes(1, byteorder='big') + (parts[0]).encode() + b'\xc0\x0c'

    # TXT record
    elif rectype == b'\x00\x10':
        rbytes = b''
        for record in records:
            rbytes += b'\xc0\x0c' + rectype + b'\x00\x01'
            rbytes += int(record['ttl']).to_bytes(4, byteorder='big')

            rbytes += (len(record['value'])+1).to_bytes(2, byteorder='big')
            rbytes += (len(record['value'])).to_bytes(1, byteorder='big')
            rbytes += record['value'].encode()

    return rbytes

# C2 response.  This is used if a txt request is send with encoded data in the request query
def genTxtResponse(records, value):

    rbytes = b'\xc0\x0c\x00\x10\x00\x01'
    rbytes += int(records[0]['ttl']).to_bytes(4, byteorder='big')

    rbytes += (len(value)+1).to_bytes(2, byteorder='big')
    rbytes += (len(value)).to_bytes(1, byteorder='big')
    rbytes += value

    return rbytes