import pygame as pg
import settings as st

class Tile(pg.sprite.Sprite):
    def __init__(self, position, surface, groups, layer_name):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft=position)
        self.z = st.LAYERS[layer_name]

class TileForCollision(Tile):
    def __init__(self, position, surface, groups):
        super().__init__(position, surface, groups, 'Level')
        self.prev_rect = self.rect.copy()

class MovingPlatform(TileForCollision):
    def __init__(self, position, surface, groups):
        super().__init__(position, surface, groups)
        self.direction = pg.math.Vector2(0, -1)
        self.speed = 100
        self.pos = pg.math.Vector2(self.rect.topleft)
    
    def update(self, deltaTime):
        self.prev_rect = self.rect.copy()
        self.pos.y += self.direction.y * self.speed * deltaTime
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))