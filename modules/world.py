#
#   world.py
#
import random
from config import WORLD_SEED, config, Item, Enemy, User
from copy import copy
from lib.static import Colors
from lib.pnoise import PerlinNoise

ZONE_WIDTH = 48
ZONE_HEIGHT = 18

TILES = {
    0: ' ', 1: Colors.GREEN+'#'+Colors.RESET, 2: Colors.BLUE+'~'+Colors.RESET, 3: '#'
}

#
#   General purpose 2D map object
#
class CellMap(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._cells = {}

    def inboard(self, x, y):
        return (0 <= x < self.width) and (0 <= y < self.height)

    def get_cell(self, x, y):
        if self.inboard(x, y):
            return self._cells.get(y * self.width + x)
        else:
            return None

    def set_cell(self, x, y, data):
        if self.inboard(x, y):
            self._cells[y * self.width + x] = data

    def fill(self, data):
        for x in range(self.width):
            for y in range(self.height):
                self.set_cell(x, y, data)

    def clear(self):
        self._cells = {}


#
#   Entity abstraction
#
class Entity(object):
    def __init__(self, world, zone_x, zone_y, x, y, tile, basis = None):
        self._world = world
        self.zone_x = zone_x
        self.zone_y = zone_y
        self.x = x
        self.y = y
        self.tile = tile
        self.basis = basis
        #self.move(0, 0) # link

    def render_world(self):
        return self._world.get_zone(self.zone_x, self.zone_y).render()

    def move(self, dx, dy):
        zone = self._world.get_zone(self.zone_x, self.zone_y)
        range_x = 10
        range_y = 8
        moved_entities = []

        # move enemies
        if type(self.basis) is User:
            for ex in xrange(self.x-range_x if self.x-range_x >= 0 else 0, self.x+range_x if self.x+range_x <= ZONE_WIDTH else ZONE_WIDTH):
                for ey in xrange(self.y-range_y if self.y >=0 else 0, self.y+range_y if self.y+range_y <= ZONE_HEIGHT else ZONE_HEIGHT):
                    entity = zone._entitymap.get_cell(ex, ey)
                    if entity:
                        if type(entity.basis) is Enemy and entity not in moved_entities:
                            distance_x = self.x-entity.x
                            distance_y = self.y-entity.y

                            if distance_x > 0:
                                entity.move(1, 0)
                            elif distance_x < 0:
                                entity.move(-1, 0)
                            if distance_y > 0:
                                entity.move(0, 1)
                            elif distance_y < 0:
                                entity.move(0, -1)
                            moved_entities.append(entity)

        # calc new pos
        newx = self.x + dx
        newy = self.y + dy
        zonex = self.zone_x
        zoney = self.zone_y
        if newx < 0:
            newx = ZONE_WIDTH - 1
            zonex = zonex - 1
        if newx >= ZONE_WIDTH:
            newx = 0
            zonex = zonex + 1
        if newy < 0:
            newy = ZONE_HEIGHT - 1
            zoney = zoney - 1
        if newy >= ZONE_HEIGHT:
            newy = 0
            zoney = zoney + 1
        # check collission
        if self._world.get_zone(zonex, zoney).collide(self, newx, newy):
            # implement enemy intelligence
            '''
            if type(self.basis) is Enemy:
                if self.x-newx < 0:
                    self.move(-1, 0)
                elif self.x-newx > 0:
                    self.move(1, 0)
                elif self.y-newy < 0:
                    self.move(0, -1)
                elif self.y-newy > 0:
                    self.move(0, 1)
            '''
            return
        # unlink from old pos
        self._world.get_zone(self.zone_x, self.zone_y).remove_entity(self)
        # update pos
        self.x = newx
        self.y = newy
        self.zone_x = zonex
        self.zone_y = zoney
        if type(self.basis) is User:
            if self.basis.zonex != self.zone_x or self.basis.zoney != zoney:
                self.basis.zonex = zonex
                self.basis.zoney = zoney
        # link to new pos
        self._world.get_zone(self.zone_x, self.zone_y).set_entity(self)

    def damage(self, amount):
        if self.basis:
            if self.basis.health > amount:
                self.basis.health = self.basis.health - amount
                return (True, True)
            else:
                self._world.get_zone(self.zone_x, self.zone_y).remove_entity(self)
                drop_list = [item for item in config.items.keys() if self.basis.etype in config.items[item].enemies]
                drop_list = [config.items[item] for item in drop_list if config.items[item].rate >= random.randint(0, 100)]
                if drop_list:
                    item = random.choice(drop_list)
                    entity = self._world.add_entity(self.zone_x, self.zone_y, self.x, self.y, '+', copy(item))
                    self._world.get_zone(self.zone_x, self.zone_y).set_entity(entity)
                    self._world._items.append(item)
                    return (True, False)
                else:
                    return (False, False)
        else:
            return (True, True)

#
#   World abstraction
#
class World(object):
    def __init__(self):
        self._zones = {}
        self._enemies = []
        self._items = []
        pass

    def get_zone(self, x, y):
        zone_id = '%dx%d' % (x, y)
        zone = self._zones.get(zone_id)
        if not zone:
            zone = Zone(self, x, y)
            self._zones[zone_id] = zone
        return zone

    def add_entity(self, zone_x, zone_y, x, y, tile = '@', basis = None):
        return Entity(self, zone_x, zone_y, x, y, tile, basis)

    def remove_entity(self, entity):
        self.get_zone(entity.zone_x, entity.zone_y).remove_entity(entity)


#
#   Zone abstraction
#
class Zone(object):
    def __init__(self, world, zone_x, zone_y):
        self.__set_seed(zone_x, zone_y)
        self._zone_x = zone_x
        self._zone_y = zone_y
        self._world = world
        self._tilemap = CellMap(ZONE_WIDTH, ZONE_HEIGHT)
        self._entitymap = CellMap(ZONE_WIDTH, ZONE_HEIGHT)

        self.generate3()

        for e in range(random.randint(0, 4)):
            enemy = config.enemies[random.choice(config.enemies.keys())]
            x = random.randint(1, ZONE_WIDTH-2)
            y = random.randint(1, ZONE_HEIGHT-2)
            if self._tilemap.get_cell(x, y):
                continue
            entity = self._world.add_entity(zone_x, zone_y, x, y, enemy.colored_sign, copy(enemy))
            self.set_entity(entity)
            self._world._enemies.append(entity)

    def __set_seed(self, zone_x, zone_y):
        random.seed(WORLD_SEED * (zone_x + zone_y))

    def generate3(self):
        def dig_path_connection_east_west(start, stop, step=1):
            empty_count = 0
            for i in range(start, stop, step):
                if empty_count >= 3:
                    return
                for y in range(-1,2):
                    t = self._tilemap.get_cell(i, h2+y)
                    if t > 0:
                        self._tilemap.set_cell(i, h2+y, 0)
                    else:
                        empty_count += 1

        def dig_path_connection_north_south(start, stop, step=1):
            empty_count = 0
            for j in range(start, stop, step):
                if empty_count >= 3:
                    return
                for x in range(-1,2):
                    t = self._tilemap.get_cell(w2+x, j)
                    if t > 0:
                        self._tilemap.set_cell(w2+x, j, 0)
                    else:
                        empty_count += 1

        w2 = int(ZONE_WIDTH / 2)
        h2 = int(ZONE_HEIGHT / 2)
        pn = PerlinNoise(WORLD_SEED * (self._zone_x + self._zone_y))
        for i in range(0, ZONE_WIDTH): #x
            for j in range(0, ZONE_HEIGHT): #y
                x = float(j)/float(ZONE_HEIGHT)
                y = float(i)/float(ZONE_WIDTH)

                n = pn.noise(4 * x, 4 * y, 0.8)
                # set different tiles
                if n < 0.30:
                    self._tilemap.set_cell(i, j, 2)
                elif n >= 0.30 and n < 0.6:
                    self._tilemap.set_cell(i, j, 0)
                elif n >= 0.6 and n < 0.8:
                    self._tilemap.set_cell(i, j, 1)
                else:
                    self._tilemap.set_cell(i, j, 3)

                if i == 0 or i == ZONE_WIDTH-1:
                    self._tilemap.set_cell(i, j, 1)

                if j == 0 or j == ZONE_HEIGHT-1:
                    self._tilemap.set_cell(i, j, 1)

        dig_path_connection_east_west(0, ZONE_WIDTH)
        dig_path_connection_east_west(ZONE_WIDTH-1, 0, -1)

        dig_path_connection_north_south(0, ZONE_HEIGHT)
        dig_path_connection_north_south(ZONE_HEIGHT-1, 0, -1)


    def generate2(self):
        # drunken walk path connection stuff :)
        w2 = int(ZONE_WIDTH / 2)
        h2 = int(ZONE_HEIGHT / 2)
        cx = w2 + random.randint(-5, 5)
        cy = h2 + random.randint(-3, 3)
        sillyness = random.randint(1, 2)
        def connect(startx, starty, targetx, targety):
            x = startx
            y = starty
            while True:
                self._tilemap.set_cell(x, y, 255)
                if x > 2:
                    self._tilemap.set_cell(x-1, y, 255)
                if x < ZONE_WIDTH - 3:
                    self._tilemap.set_cell(x+1, y, 255)
                if y > 2:
                    self._tilemap.set_cell(x, y-1, 255)
                if y < ZONE_HEIGHT - 3:
                    self._tilemap.set_cell(x, y+1, 255)
                r = random.randint(0, sillyness)
                if r == 0:
                    if x < targetx:
                        x = x + 1
                    if x > targetx:
                        x = x - 1
                elif r == 1:
                    if y < targety:
                        y = y + 1
                    if y > targety:
                        y = y - 1
                else:
                    if r % 2:
                        x = x + random.choice((-1, 1))
                    else:
                        y = y + random.choice((-1, 1))
                x = min(max(x, 1), ZONE_WIDTH-2)
                y = min(max(y, 1), ZONE_HEIGHT-2)
                if self._tilemap.get_cell(x, y) == 0:
                    return
                if x == targetx and y == targety:
                    return

        def mark():
            for x in range(ZONE_WIDTH):
                for y in range(ZONE_HEIGHT):
                    if self._tilemap.get_cell(x, y) == 255:
                        self._tilemap.set_cell(x, y, 0)

        def drunken_walk(sx, sy, dx, dy):
            self._tilemap.set_cell(cx, cy, 0)
            for x in range(-1,2):
                for y in range(-1,2):
                    self._tilemap.set_cell(sx+x, sy+y, 0)
            connect(sx + dx, sy + dy, cx, cy)
            mark()

        # create 4 paths...
        self._tilemap.fill(1)
        drunken_walk(0, h2, 1, 0)
        drunken_walk(ZONE_WIDTH - 1, h2, -1, 0)
        drunken_walk(w2, 0, 0, 1)
        drunken_walk(w2, ZONE_HEIGHT -1, 0, -1)

    def generate1(self):
        for x in range(ZONE_WIDTH):
            self._tilemap.set_cell(x, 0, 1)
            self._tilemap.set_cell(x, ZONE_HEIGHT-1, 1)
        for y in range(ZONE_HEIGHT):
            self._tilemap.set_cell(0, y, 1)
            self._tilemap.set_cell(ZONE_WIDTH-1, y, 1)

        self._tilemap.set_cell(0, int(ZONE_HEIGHT / 2), 0)
        self._tilemap.set_cell(ZONE_WIDTH-1, int(ZONE_HEIGHT / 2), 0)
        self._tilemap.set_cell(int(ZONE_WIDTH / 2), 0, 0)
        self._tilemap.set_cell(int(ZONE_WIDTH / 2), ZONE_HEIGHT-1, 0)

        for i in range(10):
            cx = random.randint(0, ZONE_WIDTH-1)
            cy = random.randint(0, ZONE_HEIGHT-1)
            r = random.randint(2, 4)
            rsq = r * r
            for x in range(cx - r, cx + r + 1):
                for y in range(cy - r, cy + r + 1):
                    dx = cx - x
                    dy = cy - y
                    dist = dx * dx + dy * dy
                    if dist <= rsq:
                        self._tilemap.set_cell(x, y, 1)

    def collide(self, caller, x, y):
        if self._tilemap.get_cell(x, y) > 0:
            return True
        entity = self._entitymap.get_cell(x, y)
        if entity:
            if type(entity.basis) is User:
                if random.randint(0, 100) < 10:
                    entity.basis.health = entity.basis.health - 1
                return True
            elif type(entity.basis) is Enemy and type(caller.basis) is User:
                block, exp = entity.damage(1)
                if not exp:
                    if entity.basis.etype == 0:
                        caller.basis.experience += 10
                    elif entity.basis.etype == 1:
                        caller.basis.experience += 30
                    elif entity.basis.etype == 2:
                        caller.basis.experience += 50
                    elif entity.basis.etype == 3:
                        caller.basis.experience += 100
                    caller.basis.level = (caller.basis.experience/1000)+1
                return block
            elif type(entity.basis) is Item:
                item_count = caller.basis.inventory.item_count
                if item_count < 8:
                    caller.basis.items = entity.basis
                    caller.basis.info = 'found %s' % entity.basis.readname
                    return False
                else:
                    caller.basis.info = 'found %s. you carry %s items, cant carry any more' % (entity.basis.readname, str(item_count))
                    return True
            else:
                return True
        return False

    def render(self):
        data = []
        for y in range(ZONE_HEIGHT):
            for x in range(ZONE_WIDTH):
                entity = self._entitymap.get_cell(x, y)
                if entity:
                    data.append(entity.tile)
                else:
                    data.append(TILES.get(self._tilemap.get_cell(x, y), ' '))
            data.append('\n')
        return ''.join(data)

    def remove_entity(self, entity):
        self._entitymap.set_cell(entity.x, entity.y, None)

    def set_entity(self, entity):
        self._entitymap.set_cell(entity.x, entity.y, entity)

    def find_free_place(self):
        while True:
            x = random.randint(0, ZONE_WIDTH-1)
            y = random.randint(0, ZONE_HEIGHT-1)
            if self._tilemap.get_cell(x, y) == 0:
                if not self._entitymap.get_cell(x, y):
                    return x, y

