#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import urllib2
import os.path
from xml.etree import ElementTree as ET
import re

devices_path = './devices'
server = 'http://188.226.174.130:5000/'
# server = 'http://localhost:5000/'

def is_valid_url(url):
    if url is None:
        return False
    regex = re.compile(
        r'(^https?://)?'  # http:// or https:// or none
        r'(?:(?:[A-Z0-9-_](?:[A-Z0-9-_]{0,61}[A-Z0-9-_])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    m = regex.search(url)
    if m:
        return True
    return False

# Convert list of items to alfred-understandable xml
def generate_xml(items):
    xml_items = ET.Element('items')
    for item in items:
        xml_item = ET.SubElement(xml_items, 'item')
        for key in item.keys():
            if key is 'uid' or key is 'arg':
                xml_item.set(key, item[key])
            else:
                child = ET.SubElement(xml_item, key)
                child.text = item[key]
    return ET.tostring(xml_items)

# Compact way to create items for alfred's list
def make_item(uid, arg, title, subtitle=''):
    dic = {
        'uid': uid,
        'arg': arg,
        'title': title,
        'subtitle': subtitle
    }
    return dic

# Shortcut for help item
def help_item(title='Help'):
    command = 'openurl'
    url = 'https://github.com/Sharrp/url-notifier/blob/master/README.md'
    arg = '{"command":"' + command + '","url":"' + url + '"}'
    return make_item('10', arg, title, 'Read help on this workflow on github.com')

# Get all registered devices
def get_devices():
    if not os.path.isfile(devices_path):
        return {}
    f = open(devices_path, 'r')
    devices = json.loads(f.read())
    f.close()
    return devices

# Dump devices to file. Will rewrite existing file
def write_devices(devices):
    f = open(devices_path, 'w+')
    f.write(json.dumps(devices))
    f.close()

# First part of workflow. Parsing command and validating parameters
def process(query):
    query = query.decode('utf-8')
    items = [] # items to show in alfred's list
    parts = query.split(' ') # it should be like these: {url}, rm {device}, add {device}

    if len(parts) == 1: # trying to send url (or empty command)
        if not is_valid_url(query):
            items.append(help_item('Not an url'))
        else: # Send command
            devices = get_devices()
            if len(devices) == 0: # no devices added yet
                items.append(help_item('You didn\'t add devices'))
            else:
                # send to all
                json_devices = json.dumps([d for d in devices])
                arg = '{"command":"send","url":"' + query + '","udids":' + json_devices + '}'
                items.append(make_item('1', arg, 'Push to all', 'Send url to all registered devices'))
                # send to specific
                num = 2
                for d in devices:
                    arg = '{"command":"send","url":"' + query + '","udids":["' + d + '"]}'
                    items.append(make_item(str(num), arg, 'Send to '+ devices[d], 'Device id: ' + d))
                    num += 1
    elif len(parts) == 2: # remove command and hint for add command
        if parts[0] == 'rm':
            devices = get_devices()
            num = 1
            if len(devices) == 0:
                items.append(help_item('No devices added yet'))
            for d in devices: # filter existing devices
                if parts[1] in d or parts[1] in devices[d]:
                    arg = '{"command":"remove","udid":"' + d + '"}'
                    items.append(make_item(str(num), arg, 'Remove '+ devices[d], 'Device id: ' + d))
                    num += 1
            if len(items) == 0:
                items.append(help_item('No devices with "' + parts[1] + '" in id or name'))
        elif parts[0] == 'add':
            items.append(help_item('Enter device id and name'))
        else:
            items.append(help_item('Unknown command'))
    elif len(parts) == 3:
        if parts[0] == 'add':
            if len(parts[1]) > 4: # the shortest udid is 5 chars long
                if len(parts[2]) < 1:
                    items.append(help_item('Enter device name'))
                else:
                    devices = get_devices()
                    if parts[1] in devices or parts[2] in devices.values(): # device already added
                        items.append(help_item('Device already added'))
                    else:
                        arg = '{"command":"add","udid":"' + parts[1] + \
                            '","name":"' + parts[2] + '"}'
                        items.append(make_item('1', arg, 'Add this device'))
            else:
                items.append(help_item('Not a valid device id'))
    else:
        items.append(help_item('Too much parameters'))

    print(generate_xml(items))

# Second part of workflow. Executing received command and showing feedback
def execute(command):
    data = json.loads(command)
    if data['command'] == 'send':
        del(data['command'])
        url = server + 'url/'
        req = urllib2.Request(url=url, data=json.dumps(data))
        req.add_header('Content-Type', 'application/json')
        urllib2.urlopen(req)
        # print(r.read())
        print('Url sent')
    elif data['command'] == 'add':
        # Checking that udid exists
        url = server + 'client/'
        params = {'udid':data['udid']}
        req = urllib2.Request(url=url, data=json.dumps(params))
        req.add_header('Content-Type', 'application/json')
        r = urllib2.urlopen(req)
        response = json.loads(r.read())
        if 'client_exists' in response and not response['client_exists']:
            print('No registered device with id "' + data['udid'] + '"')
        else:
            devices = get_devices()
            devices[data['udid']] = data['name']
            write_devices(devices)
            print('Device "' + data['name'] + '" with id "' + data['udid'] + '" added')
    elif data['command'] == 'remove':
        devices = get_devices()
        name = devices[data['udid']]
        del(devices[data['udid']])
        write_devices(devices)
        print('Device ' + name + ' with id "' + data['udid'] + '" removed')
    elif data['command'] == 'openurl':
        import webbrowser
        new = 2 # open in a new tab, if possible
        webbrowser.open(data['url'],new=new)
