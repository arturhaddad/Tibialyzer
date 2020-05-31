
# Copyright 2016 Mark Raasveldt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re

from coordinates import convert_x, convert_y

mapperRegex = re.compile('Mapper\\?coords=([0-9.]+)[,-]([0-9.]+)[,-]([0-9]+)')
creatureRegex = re.compile('\\{\\{\\:([^|/]+)\\|List}}')
creatureRegex2 = re.compile('\\{\\{(Creature[ \t\n]?List[^}]+)\\}\\}')

def parseHunt(title, attributes, c, content, huntcreatures, getURL):
    name = title.replace('<br>', ' ').strip()
    if 'name' in attributes:
        name = attributes['name'].replace('<br>', ' ').strip()
    city = None
    if 'city' in attributes:
        city = attributes['city']
    if city == None:
        return False

    c.execute('SELECT * FROM HuntingPlaces WHERE LOWER(name)=?', (name.lower(),))
    results = c.fetchall()

    if len(results) > 0:
        huntattribs = [name, city].count(None)
        otherAttributes = results[0].count(None)
        if otherAttributes > huntattribs:
            c.execute('DELETE FROM HuntingPlaces WHERE LOWER(name)=?', (name.lower(),))
        else:
            print(name, 'more null values than other hunt of the same name', huntattribs, otherAttributes)
            return True

    coordinates = None
    if 'location' in attributes:
        locstr = attributes['location']
        index = 0;
        while True:
            match = re.search(mapperRegex, locstr[index:])
            if match == None: 
                break
            x = convert_x(match.groups()[0])
            y = convert_y(match.groups()[1])
            z = int(match.groups()[2])
            coordinates = f'{x},{y},{z}'
            index += match.end()
    index = 0;

    c.execute('INSERT INTO HuntingPlaces (name, city, coordinates) VALUES (?,?,?)', (name, city, coordinates))
    huntingid = c.lastrowid
    huntcreatures[huntingid] = list()
    while True:
        match = re.search(creatureRegex, content[index:])
        if match == None: break
        creature = match.groups()[0]
        if creature not in huntcreatures[huntingid]:
            huntcreatures[huntingid].append(creature)
        index += match.end()
    index = 0
    while True:
        match = re.search(creatureRegex2, content[index:])
        if match == None: break
        creatureList = match.groups()[0].split('|')[1:]
        for creature in creatureList:
            huntcreatures[huntingid].append(creature)
        index += match.end()
    return True
