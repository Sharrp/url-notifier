#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import urllib2
import os.path
from xml.etree import ElementTree as ET
import re

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

def process_command(query):
    if not is_valid_url(query):
        dic = {
            'uid': '1',
            # 'arg': '',
            'title': 'Not an url',
            'subtitle': 'Please don\'t do this'
        }
        print(generate_xml([dic]))
        return
    command = 'send'
    url = 'http://ya.ru'
    dic = {
        'uid': '1',
        'arg': '{"command":"' + command + '","url":"' + url + '"}',
        'title': 'Push to all devices',
        'param': 'pampam'
    }
    print(generate_xml([dic]))

def execute(command):
    data = json.loads(command)
    print(data['url'])

def get_people(query):
    query = query.replace('й', 'й').replace('ё', 'ё')
    uri = 'http://search.yandex-team.ru/suggest?s%5B%5D=people&s%5B%5D=text&text=' + urllib2.quote(query)
    people = []
    data = json.loads(urllib2.urlopen(uri).read().decode('utf-8'))

    for human in data['people']:
        people.append(parse_item(human))

    print(generate_xml(people))

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

def parse_item(item):
    subtitle = item['login'] + '@'
    if item['phone']:
        subtitle = subtitle + u' — ' + item['phone']
    subtitle = subtitle + u' — ' + item['department']

    # substitute non-existing avatars
    ava_path = './avatars/' + item['login'] + '.jpg'
    if not os.path.isfile(ava_path):
        ava_path = './avatars/__default__.png'

    return {
        'uid': item['login'],
        'arg': item['login'],
        'title': item['title'],
        'subtitle': subtitle,
        'icon': ava_path,
    }
