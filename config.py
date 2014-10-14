from data.models import *
import json

# random world seed ...
WORLD_SEED = 1024

class ReadJson(object):
    def __init__(self, path):
        try:
            self.__json_data = open(path)
            self.data = json.load(self.__json_data)
        except Exception, e:
            print e

class User(object):
    def __init__(self, name, entity):
        self._username = name
        self.entity = entity
        self._items = []
        self._info = ''

    @property
    def username(self):
        return self._username
    @username.setter
    def username(self, value):
        self._username = value

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, values):
        self._items.extend(values)

    def remove_items(self, items):
        for i in items:
            self._items.remove(i)

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, value):
        self._info = value



class Item(object):
    def __init__(self, name, attributes):
        self.name = name
        self._readname = attributes['name']
        self._attributes = attributes['attributes']
        self._rate = attributes['rate']
        self._enemies = attributes['enemies']
        self._condition = attributes['condition']
        # FIXME: link to useable classes

    @property
    def readname(self):
        return self._readname

    @property
    def attributes(self):
        return self._attributes

    @property
    def rate(self):
        return self._rate

    @property
    def enemies(self):
        return self._enemies

    @property
    def condition(self):
        return self._condition

class Enemy(object):
    def __init__(self, name,  attributes):
        self.name = name
        self._health = attributes['health']
        self._level = attributes['level']
        self._sign = attributes['sign']
        self._etype = attributes['type']

    @property
    def health(self):
        return self._health
    @health.setter
    def health(self, value):
        self._health = value

    @property
    def level(self):
        return self._level

    @property
    def sign(self):
        return self._sign

    @property
    def etype(self):
        return self._etype

class Config(object):
    def __init__(self):
        self.enemies = {}
        self.items = {}
        # init enemies
        enemies = ReadJson('data/enemies.json').data
        for name, attributes in enemies.items():
            self.enemies[name] = Enemy(name, attributes)
        # init items
        items = ReadJson('data/items.json').data
        for name, attributes in items.items():
            self.items[name] = Item(name, attributes)

        @property
        def enemies(self):
            return self.enemies

config = Config()
