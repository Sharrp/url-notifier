#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import urllib2
import os.path
from xml.etree import ElementTree as ET
import re

devices_path = './devices'

def is_valid_url(url):
    if url is None:
        return False
    regex = re.compile(
        r'(^https?://)?'  # http:// or https://
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
        # 'icon': path_to_icon
    }
    return dic

# Shortcut for help item
def help_item(title='Help'):
    command = 'openurl'
    url = 'https://github.com/Sharrp/url-notifier/blob/master/Alfred%20Workflow/README'
    arg = '{"command":"' + command + '","url":"' + url + '"}'
    return make_item('10', arg, title, 'Read help on this workflow on github.com')

# Get all registered devices
def get_devices():
    if not os.path.isfile(devices_path):
        return []
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
    items = [] # items to show in alfred's list
    parts = query.split(' ') # it should be like these: {url}, rm {device}, add {device}

    if len(parts) == 1: # trying to send url (or empty command)
        if not is_valid_url(query):
            items.append(help_item('Not an url'))
        else: # Send command
            arg = '{"command":"send","url":"' + query + '"}'
            items.append(make_item('1', arg, 'Push to all', 'Send url to all registered devices'))
    elif len(parts) == 2: # add or remove commands
        if parts[0] == 'add':
            if len(parts[1]) > 4: # the shortest udid is 5 chars long
                devices = get_devices()
                if parts[1] in devices: # device already added
                    items.append(help_item('Device already added'))
                else:
                    arg = '{"command":"add","udid":"' + parts[1] + '"}'
                    items.append(make_item('1', arg, 'Add this device'))
            else:
                items.append(help_item('Not a valid device id'))
        elif parts[0] == 'rm':
            devices = get_devices()
            num = 1
            for d in devices: # filter existing devices
                if parts[1] in d:
                    arg = '{"command":"remove","udid":"' + d + '"}'
                    items.append(make_item(str(num), arg, 'Remove '+ d + ' device'))
                    num += 1
            if len(items) == 0:
                items.append(help_item('No devices with "' + parts[1] + '" in id'))
        else:
            items.append(help_item('Unknown command'))
    else:
        items.append(help_item('Too much parameters'))

    print(generate_xml(items))

# Second part of workflow. Executing received command and showing feedback
def execute(command):
    data = json.loads(command)
    if data['command'] == 'send':
        # data = json.loads(urllib2.urlopen(uri).read().decode('utf-8'))
        pass
    elif data['command'] == 'add':
        devices = get_devices()
        devices.append(data['udid'])
        write_devices(devices)
        print('Device ' + data['udid'] + ' added')
    elif data['command'] == 'remove':
        devices = get_devices()
        devices.remove(data['udid'])
        write_devices(devices)
        print('Device ' + data['udid'] + ' removed')
    elif data['command'] == 'openurl':
        import webbrowser
        new = 2 # open in a new tab, if possible
        webbrowser.open(data['url'],new=new)
