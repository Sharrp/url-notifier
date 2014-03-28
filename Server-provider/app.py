from flask import Flask
from flask import request
import json
import os
from apns import APNs, Payload
import random

apns = APNs(use_sandbox=True, cert_file='cert.pem', key_file='key.pem')

app = Flask(__name__)

def read_settings():
    cur_dir = os.path.dirname(__file__)
    path = os.path.join(cur_dir, 'settings.json')
    if not os.path.exists(path):
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
    symbols = [str(chr(i+65)) for i in range(26)] # uppercase laters
    symbols.extend([str(chr(i+97)) for i in range(26)]) # lowercase
    symbols.extend([str(i) for i in range(10)]) # digits
    for i in range(4): # 62 ^ 4 = 14 776 336, that's enough
        uid_hash += symbols[random.randint(0, 61)]
    return uid_hash + str(uid)


@app.route('/', methods=['GET'])
def default_response():
    return 'Just works'

@app.route('/device/', methods=['POST'])
def update_device_token():
    s = read_settings()
    did = request.json['did'] # device id, received from phone
    token = request.json['token'] # APNS token
    print(did)
    print(token)
    udid = -1 # user-friendly device id
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
    return str(udid)

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
            response[udid] = 'Ok'
        else:
            response[udid] = 'Device not found'
            continue
        url_data = {"url":url, "len":len(url)} # url length for checking data consistency on client
        payload = Payload(alert="New url", custom=url_data)
        apns.gateway_server.send_notification(token, payload)
    save_settings(s)
    return json.dumps(response)

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
