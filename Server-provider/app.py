from flask import Flask
from flask import request
import json
import os
from apns import APNs, Payload

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

s = read_settings() # settings

@app.route('/device/', methods=['POST'])
def update_device_token():
    global s
    did = request.json['did'] # device id, received from phone
    token = request.json['token'] # APNS token
    udid = -1 # user-friendly device id
    # 2 dictionaries: udid –> token (where to send), did –> udid (is it in base)
    if did in s['dids']:
        udid = s['dids'][did]
        s['udids'][udid] = token
    else:
        udid = str(s['last_id'])
        s['last_id'] += 1
        s['dids'][did] = udid
        s['udids'][udid] = token
    save_settings(s)
    return str(udid)

@app.route('/url/', methods=['POST'])
def send_url_to_device():
    print('Url received')
    token_hex = 'b55a363fceae1394ad170faff4c0c53a296fa179898ed3cc0d9035852f386921'
    payload = Payload(alert="New url received", custom={"url":"http://yandex.ru/touchsearch?text=nokia+xl"})
    apns.gateway_server.send_notification(token_hex, payload)
    # udid = request.json['udid']
    return 'Url sent\n'

if __name__ == "__main__":
    app.run(debug=True)
    # app.run()
