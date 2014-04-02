import json
import os
import random
import re
from flask import Flask, request
from apns import APNs, Payload

apns = APNs(use_sandbox=True, cert_file='cert.pem', key_file='key.pem')
app = Flask(__name__)

def read_settings():
    cur_dir = os.path.dirname(__file__)
    path = os.path.join(cur_dir, 'settings.json')
    if not os.path.exists(path): # default settings
        settings = {"last_id":1,"did2udid":{},"udid2token":{},"urls":{}}
    else:
        f = open(path, 'r')
        settings = json.loads(f.read())
        f.close()
    return settings

def save_settings(s):
    f = open('./settings.json', 'w+')
    f.write(json.dumps(s))
    f.close()

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
    return uid_hash + str(uid)

# If could - returns domain, otherwise - url or it's first 20 symbols
def readable_url(url):
    r = re.compile('https?://([^?/&]+)')
    m = r.match(url)
    if m:
        return m.group(1)
    else:
        if len(url) > 20:
            return url[:20] + '...'
        else:
            return url


@app.route('/', methods=['GET'])
def default_response():
    return "It's ok"

# Receives token from device and respond with udid
@app.route('/device/', methods=['POST'])
def update_device_token():
    s = read_settings()
    did = request.json['did'] # device id, received from phone
    token = request.json['token'] # APNS token
    print('Device update: ' + did)
    print('Received token: ' + token)
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
    return udid

# Pushes url to multiple devices
@app.route('/url/', methods=['POST'])
def send_url_to_device():
    url = request.json['url']
    udids = request.json['udids']
    # add http to url
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
        else:
            response[udid] = 404
            continue
        url_data = {"url":url, "len":len(url)} # url length for checking data consistency on client
        payload = Payload(alert=readable_url(url), custom=url_data)
        apns.gateway_server.send_notification(token, payload)

    save_settings(s)
    return json.dumps(response)

# In some cases payload in push notification wouldn't be full
# Then mobile client should ask for last sended url, when launched
@app.route('/lasturl/', methods=['POST'])
def get_last_url():
    did = request.json['did'] # device id, received from phone
    s = read_settings()
    if did in s['did2udid']:
        udid = s['did2udid'][did]
        url = s['urls'][udid]
        if url:
            return '{"url":"' + url + '"}'
        else:
            return '{"error":"No url for this device"}'
    else:
        return '{"error":"Unknown device"}'

# Checks that received mobile client exists in database
@app.route('/client/', methods=['POST'])
def check_client():
    udid = request.json['udid']
    print('Client check: ' + udid)
    s = read_settings()
    if udid in s['udid2token']:
        return '{"client_exists":true}'
    else:
        return '{"client_exists":false}'


if __name__ == "__main__":
    app.run(debug=True)
    # app.run()
