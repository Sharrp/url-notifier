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


s = read_settings() # settings

@app.route('/', methods=['GET'])
def default_response():
    return 'Just works'

@app.route('/device/', methods=['POST'])
def update_device_token():
    global s
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
    udid = request.json['udid']
    print(udid)
    print(url)
    token = ''
    if udid in s['udid2token']:
        token = s['udid2token'][udid]
        s['urls'][udid] = url
    else:
        return 'There is no such device'
    url_data = {"url":url, "len":len(url)} # url length for checking data consistency on client
    payload = Payload(alert="New url", custom=url_data)
    apns.gateway_server.send_notification(token, payload)
    return 'Url sent\n'

@app.route('/lasturl/', methods=['POST'])
def get_last_url():
    did = request.json['did'] # device id, received from phone
    if did in s['did2udid']:
        udid = s['did2udid'][did]
        url = s['urls'][udid]
        if url:
            return '{"url":"' + url + '"}'
        else:
            return '{"error":"No url for this device"}'
    else:
        return '{"error":"Unknown device"}'

if __name__ == "__main__":
    app.run(debug=True)
    # app.run()
