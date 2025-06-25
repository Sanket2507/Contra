import pygame as pg
import settings as st
from os import walk
from entity import Entity
import sys

class Player(Entity):
    def __init__(self, position, asset_path, groups, coll_sprites, create_bullet):
        super().__init__(position=position, asset_path=asset_path, groups=groups, create_bullet=create_bullet)
        self.health = 10
        self.coll_obj = coll_sprites
        self.gravity = 15
        self.jump_speed = 1200
        self.on_ground = False
        self.moving_floor = None

    def check_alive(self):
        if self.health <= 0:
            self.kill()

    # ... (rest of the Player class remains exactly the same as before)

    def get_move_dir(self):
        base_dir = self.move_dir.split('_')[0] if '_' in self.move_dir else self.move_dir
        
        if self.direction.x == 0 and self.on_ground:
            self.move_dir = f"{base_dir}_idle"
        elif self.direction.y != 0 and not self.on_ground:
            self.move_dir = f"{base_dir}_jump"
        elif self.ducking and self.on_ground:
            self.move_dir = f"{base_dir}_duck"

    def check_on_ground(self):
        rect_below_player = pg.Rect(0, 0, self.rect.width, 5)
        rect_below_player.midtop = self.rect.midbottom

        for sprite in self.coll_obj.sprites():
            if sprite.rect.colliderect(rect_below_player):
                if self.direction.y > 0:
                    self.on_ground = True
                if hasattr(sprite, "direction"):
                    self.moving_floor = sprite

    def input(self):
        keys = pg.key.get_pressed()

        if keys[pg.K_LEFT]:
            self.direction.x = -1
            self.move_dir = "left"
        elif keys[pg.K_RIGHT]:
            self.direction.x = 1
            self.move_dir = "right"
        else:
            self.direction.x = 0

        if keys[pg.K_UP] and self.on_ground:
            self.direction.y = -self.jump_speed

        self.ducking = keys[pg.K_DOWN]
        
        if keys[pg.K_SPACE] and self.can_shoot:
            blt_dir = pg.math.Vector2(1, 0) if "right" in self.move_dir else pg.math.Vector2(-1, 0)
            blt_pos = self.rect.center + blt_dir * 60
            y_offset = pg.math.Vector2(0, 10 if self.ducking else -15)

            self.fire_bullet(blt_pos + y_offset, blt_dir, self)
            self.can_shoot = False
            self.blt_time = pg.time.get_ticks()
            self.fire_sound.play()

    def collision(self, dir):
        for sprite in self.coll_obj.sprites():
            if sprite.rect.colliderect(self.rect):
                if dir == "horizontal":
                    if self.rect.left <= sprite.rect.right and self.prev_rect.left >= sprite.prev_rect.right:
                        self.rect.left = sprite.rect.right
                    if self.rect.right >= sprite.rect.left and self.prev_rect.right <= sprite.prev_rect.left:
                        self.rect.right = sprite.rect.left
                    self.pos.x = self.rect.x
                else:
                    if self.rect.bottom >= sprite.rect.top and self.prev_rect.bottom <= sprite.prev_rect.top:
                        self.rect.bottom = sprite.rect.top
                        self.on_ground = True
                    if self.rect.top <= sprite.rect.bottom and self.prev_rect.top >= sprite.prev_rect.bottom:
                        self.rect.top = sprite.rect.bottom
                    self.direction.y = 0
                    self.pos.y = self.rect.y
        
        if self.on_ground and self.direction.y != 0:
            self.on_ground = False

    def move(self, deltaTime):
        if self.ducking and self.on_ground:
            self.direction.x = 0
        
        self.pos.x += self.direction.x * self.speed * deltaTime
        self.rect.x = round(self.pos.x)
        self.collision("horizontal")

        self.direction.y += self.gravity
        self.pos.y += self.direction.y * deltaTime

        if self.moving_floor and self.moving_floor.direction.y > 0 and self.direction.y > 0:
            self.direction.y = 0
            self.rect.bottom = self.moving_floor.rect.top
            self.pos.y = self.rect.y
            self.on_ground = True

        self.rect.y = round(self.pos.y)
        self.collision("vertical")
        self.moving_floor = None
    
    def update(self, deltaTime):
        self.prev_rect = self.rect.copy()
        self.input()
        self.get_move_dir()
        self.move(deltaTime)
        self.check_on_ground()
        self.animate(deltaTime)
        self.blink()
        self.blt_timer()
        self.invulnerable_timer()
        self.check_alive()