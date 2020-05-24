

import math
import re
import urllib.request
import sqlite3
import time

htmlTagRegex = re.compile('<[^>]*>')
numberRegex = re.compile('([0-9]+[,.]?[0-9]*[,.]?[0-9]*[,.]?[0-9]*[,.]?[0-9]*)')

def parseKey(title, attributes, c, keyImages, buyitems, sellitems, getURL):
    if 'number' not in attributes:
        return False
    try: 
        name = 'Key %s' % int(attributes['number'].lower().strip())
    except: 
        return False
    if 'aka' in attributes and len(attributes['aka'].strip()) > 0:
        aka_text = attributes['aka'].strip()
        # first take care of [[Fire Rune||Great Fireball]] => Great Fireball
        aka_text = re.sub(r'\[\[[^]|]+\|([^]]+)\]\]', '\g<1>', aka_text)
        # then take care of [[Fire Rune]] => Fire Rune
        aka_text = re.sub(r'\[\[([^]]+)\]\]', '\g<1>', aka_text)
        name = "%s (%s)" % (name, aka_text)
    minValue = None
    maxValue = None
    if 'value' in attributes: 
        valueRange = attributes['value'].replace(' to ', '-').replace('on', '(')
        valueRange = re.sub('\(.+|[^0-9\-]', '', valueRange).split('-')
        try:
            minValue = int(valueRange[0])
            minValue = minValue if minValue > 0 else None
        except: pass

        try:
            maxValue = int(valueRange[1]) if len(valueRange) > 1 else None
            maxValue = maxValue if maxValue > 0 else None
        except: pass
    npcBuyValue = None
    if 'npcvalue' in attributes:
        try:
            npcBuyValue = int(attributes['npcvalue'])
            if npcBuyValue > 0:
                if minValue == None or minValue < npcBuyValue:
                    minValue = npcBuyValue
                if maxValue != None and maxValue < npcBuyValue:
                    maxValue = npcBuyValue
            else:
                npcBuyValue = None
        except: pass
    npcSellValue = None
    if 'npcprice' in attributes:
        try: 
            npcSellValue = int(attributes['npcprice'])
            if npcSellValue <= 0:
                npcSellValue = None
        except: pass
    if minValue != None and maxValue != None and minValue > maxValue:
        maxValue = None

    stackable = False
    capacity = 1
    image = None
    category = "Keys"
    convert_to_gold, discard = False, False
    look_text = None
    if 'longnotes' in attributes:
        look_text = attributes['longnotes']
    elif 'shortnotes' in attributes:
        look_text = attributes['shortnotes']
    if look_text != None:
        # first take care of [[Fire Rune||Great Fireball]] => Great Fireball
        look_text = re.sub(r'\[\[[^]|]+\|([^]]+)\]\]', '\g<1>', look_text)
        # first take care of {{Character|<Name>}} => <Name>
        look_text = re.sub(r'\{\{[^}|]+\|([^}]+)\}\}', '\g<1>', look_text)
        # then take care of [[Fire Rune]] => Fire Rune
        look_text = re.sub(r'\[\[([^]]+)\]\]', '\g<1>', look_text)
        # sometimes there are links in single brackets [http:www.link.com] => remove htem
        look_text = re.sub(r'\[[^]]+\]', '', look_text)
        # remove html tags
        look_text = look_text.replace("<br />", " ").replace("<br/>", " ").replace("<br>", " ").replace("\n", " ")
        # replace double spaces with single spaces
        look_text = look_text.replace('  ', ' ')
        # Remove spoilers 
        if "{{JSpoiler" in look_text:
            look_text = look_text.replace(look_text[look_text.find("{{JSpoiler"):], "")
        if "<gallery>" in look_text:
            look_text = look_text.replace(look_text[look_text.find("<gallery>"):], "")

    c.execute('INSERT INTO Items (title,name, npc_buy_value, npc_sell_value, actual_min_value, actual_max_value, capacity, stackable, image, category, discard, convert_to_gold, look_text) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (title,name, npcBuyValue, npcSellValue, minValue, maxValue, capacity, stackable, image, category, discard, convert_to_gold, look_text))
    itemid = c.lastrowid
    keyImages[itemid] = attributes['primarytype']
    if 'buyfrom' in attributes:
        buyitems[itemid] = dict()
        npcs = attributes['buyfrom'].split(',')
        for n in npcs:
            npc = n
            if npc == '' or npc == '-' or npc == '--': continue
            value = npcPrice
            if ';' in npc: 
                npc = npc.split(';')[0]
            if ':' in npc:
                token = npc.split(':')[1].strip()
                npc = npc.split(':')[0]
                try: 
                    value = math.ceil(float(token))
                except: 
                    match = re.search('\\[\\[([^]]+)\\]\\]', token)
                    if match == None:
                        continue
                    currencymap[itemid] = match.groups()[0]
                    match = numberRegex.search(token)
                    if match == None:
                        continue
                    value = float(match.groups()[0])
            if value == None: continue
            buyitems[itemid][npc.strip()] = value
    if 'sellto' in attributes:
        sellitems[itemid] = dict()
        npcs = attributes['sellto'].split(',')
        for n in npcs:
            npc = n
            if npc == '' or npc == '-' or npc == '--': continue
            value = npcValue
            if ';' in npc: 
                npc = npc.split(';')[0]
            if ':' in npc:
                value = math.ceil(float(npc.split(':')[1].strip()))
                npc = npc.split(':')[0]
            if value == None: continue
            sellitems[itemid][npc.strip()] = value
    return True