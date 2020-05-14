# dnszones.py
import glob
import json
import settings

def load_zones():

    jsonzone = {}
    zonefiles = glob.glob('zones/*.zone')

    for zone in zonefiles:
        with open(zone) as zonedata:
            data = json.load(zonedata)
            zonename = data["$origin"]
            jsonzone[zonename] = data
    return jsonzone


def getzone(domain, rectype):
    zonedata = load_zones()

    zone_name = '.'.join(domain)
    if zone_name in zonedata:
        try:
            records = zonedata[zone_name][settings.dnstype[rectype]]     # records: an array dns type record (ex: [{'name': '@', 'ttl': 400, 'value': 'Hello World!'}])
            return records
        except:
            print("unknown dns type")
            return []
    else:
        print("no zone record found")
        return []