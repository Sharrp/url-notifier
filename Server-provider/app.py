import json
import os
import random
import re
import sys
from time import strftime
from flask import Flask, request
from apns import APNs, Payload

apns = APNs(use_sandbox=True, cert_file='cert.pem', key_file='key.pem')
app = Flask(__name__)

log_file = './log.txt'

def log(entry):
    entry = "[" + strftime("%Y-%m-%d %H:%M:%S") + "] " + str(entry)
    # console
    print(entry)
    # file
    f = open(log_file, 'a+')
    f.write(entry + '\n')
    f.close()

def read_settings():
    cur_dir = os.path.dirname(__file__)
    path = os.path.join(cur_dir, 'settings.json')
    if not os.path.exists(path): # default settings
        settings = {"last_id":1,"did2udid":{},"udid2token":{},"urls":{}}
        log('Read settings: default')
    else:
        f = open(path, 'r')
        settings = json.loads(f.read())
        f.close()
        log('Read settings: from file')
    return settings

def save_settings(s):
    f = open('./settings.json', 'w+')
    f.write(json.dumps(s))
    f.close()
    log('Settings saved')

# Short id. Not so long (since it's for humans) and not just a serial number
def human_hash(uid):
    uid_hash = ''
    symbols = [str(chr(65+i)) for i in range(26)] # uppercase laters
    symbols.extend([str(chr(97+i)) for i in range(26)]) # lowercase
    symbols.extend([str(i) for i in range(10)]) # digits
    toRemove = '10olOI' # they're too ambiguous
    count = 26 + 26 + 10 - len(toRemove)
    for ch in toRemove:
        symbols.remove(ch)

    for i in range(4): # 56 ^ 4 = 9 834 496, that's enough
        uid_hash += symbols[random.randint(0, count - 1)]
    uid_hash = uid_hash + str(uid)
    log('Generated hash: ' + uid_hash)
    return uid_hash

# If could - returns domain, otherwise - url or it's first 20 symbols
def readable_url(url):
    r = re.compile('https?://([^?/&]+)')
    m = r.match(url)
    nice_url = url
    if m:
        nice_url = m.group(1)
    if len(nice_url) > 20:
        return url[:20] + '...'
    else:
        return url


@app.route('/', methods=['GET'])
def default_response():
    return "It's ok"

# Receives token from device and respond with udid
@app.route('/device/', methods=['POST'])
def update_device_token():
    if not request.json or 'did' not in request.json or 'token' not in request.json:
        log('/device/: no did or token in request')
        return '{"error":"Request should contain json serialized parameters: \
            device id (key - did) and APNS token (key - token)"}'
    did = request.json['did'] # device id, received from phone
    token = request.json['token'] # APNS token
    log('/device/: did: ' + did)
    log('/device/: token: ' + token)
    s = read_settings()
    udid = '' # user-friendly device id
    # 2 dictionaries: udid -> token (where to send), did -> udid (is it in base)
    if did in s['did2udid']:
        udid = s['did2udid'][did]
        s['udid2token'][udid] = token
    else:
        udid = human_hash(s['last_id'])
        s['last_id'] += 1
        s['did2udid'][did] = udid
        s['udid2token'][udid] = token
    save_settings(s)
    log('/device/: finished' )
    return udid

# Pushes url to multiple devices
@app.route('/url/', methods=['POST'])
def send_url_to_device():
    # Data validation
    if not request.json or 'url' not in request.json or 'udids' not in request.json:
        log('/url/: no udids or url in request')
        return '{"error":"Request should contain json serialized parameters: \
            url (key - url) and array with destination devices\'s udids (key - udids)"}'
    url = request.json['url']
    udids = request.json['udids']
    if not isinstance(url, basestring) or len(url) == 0:
        log('/url/: url is empty')
        return '{"error":"Url - should be non-empty string"}'
    if not isinstance(udids, list) or len(udids) == 0:
        log('/url/: udids is empty')
        return '{"error":"Udids should be a non-empty array with string-ids"}'
    for udid in udids:
        if not isinstance(udid, basestring) or len(udid) == 0:
            log('/url/: one udid is empty or not a string')
            return '{"error":"Every udid in udids should be a non-empty string"}'

    # Add http to url
    url = url.strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    response = {}
    print('Url: ' + url)
    print('Devices: ' + ', '.join(udids))
    s = read_settings()

    for udid in udids:
        token = ''
        if udid in s['udid2token']:
            token = s['udid2token'][udid]
            s['urls'][udid] = url
            response[udid] = 200
            log('/url/: device ' + udid + ' found. Token: ' + token)
        else:
            response[udid] = 404
            log('/url/: device ' + udid + ' not found')
            continue
        # Since max payload size is 256 bytes we should crop long urls and client will
        # ask server for /lasturl because len(url) != payload[len]
        url_data = {"len":len(url)} # url length for checking data consistency on client
        readable = readable_url(url)
        if len(url) + len(readable_url(url)) > 200:
            url = ''
        url_data["url"] = url
        payload = Payload(alert=readable, custom=url_data)
        log('Payload: ' + str(payload))
        apns.gateway_server.send_notification(token, payload)
        log('/url/: payload sent to Apple')

    save_settings(s)
    log('/url/: finished')
    return json.dumps(response)

# In some cases payload in push notification wouldn't be full
# Then mobile client should ask for last sended url, when launched
@app.route('/lasturl/', methods=['POST'])
def get_last_url():
    log('/lasturl/: start')
    did = request.json['did'] # device id, received from phone
    s = read_settings()
    if did in s['did2udid']:
        udid = s['did2udid'][did]
        url = s['urls'][udid]
        if url:
            log('/lasturl/: found url for device did: ' + udid + '\n' + url)
            return '{"url":"' + url + '"}'
        else:
            log('/lasturl/: no url for device did: ' + udid)
            return '{"error":"No url for this device"}'
    else:
        log('/lasturl/: did not found in base: ' + did)
        return '{"error":"Unknown device"}'

# Checks that received mobile client exists in database
@app.route('/client/', methods=['POST'])
def check_client():
    log('/client/: start')
    if not request.json or 'udid' not in request.json:
        log('/client/: no udid in request')
        return '{"error":"Request should contain user device id (key - did) \
            as json serialized parameter"}'
    udid = request.json['udid']
    if not isinstance(udid, basestring) or len(udid) == 0:
        log('/client/: udid is not valid')
        return '{"error":"Udid should be a non-empty string"}'
    log('/client/: checking udid: ' + udid)
    s = read_settings()
    if udid in s['udid2token']:
        log('/client/: client exists')
        return '{"client_exists":true}'
    else:
        log('/client/: client does not exist')
        return '{"client_exists":false}'


if __name__ == "__main__":
    app.run()
