import pygame as pg
import settings as st
from os import walk
from math import sin

class Entity(pg.sprite.Sprite):
    def __init__(self, position, asset_path, groups, create_bullet):
        super().__init__(groups)
        self.import_assets(asset_path)
        self.frame_index = 0
        self.move_dir = "right"

        self.image = self.animations[self.move_dir][self.frame_index]
        self.rect = self.image.get_rect(topleft=position)
        self.prev_rect = self.rect.copy()
        self.z = st.LAYERS["Level"]
        self.mask = pg.mask.from_surface(self.image)

        self.pos = pg.math.Vector2(self.rect.topleft)
        self.direction = pg.math.Vector2()
        self.speed = 400
        self.ducking = False

        self.fire_bullet = create_bullet
        self.can_shoot = True
        self.blt_time = None
        self.time_bw_shots = 300

        self.health = 3
        self.vulnerable = True
        self.time_last_hit = None
        self.bullet_damage = 1  # Default damage value

        self.hit_sound = pg.mixer.Sound('./audio/hit.wav')
        self.hit_sound.set_volume(0.2)
        self.fire_sound = pg.mixer.Sound('./audio/bullet.wav')
        self.fire_sound.set_volume(0.2)

    def blink(self):
        if not self.vulnerable and self.wave_val():
            mask = pg.mask.from_surface(self.image)
            white_surf = mask.to_surface()
            white_surf.set_colorkey((0, 0, 0))
            self.image = white_surf

    def wave_val(self):
        val = sin(pg.time.get_ticks())      
        return val >= 0
    
    def check_alive(self):
        if self.health <= 0:
            self.kill()

    def damage(self):
        if self.vulnerable:
            self.vulnerable = False
            self.health -= getattr(self, 'bullet_damage', 1)
            self.time_last_hit = pg.time.get_ticks()
            self.hit_sound.play()

    def animate(self, deltaTime):
        self.frame_index += 7 * deltaTime
        if self.frame_index >= len(self.animations[self.move_dir]):
            self.frame_index = 0
        self.image = self.animations[self.move_dir][int(self.frame_index)]
        self.mask = pg.mask.from_surface(self.image)

    def blt_timer(self):
        if not self.can_shoot:
            if pg.time.get_ticks() - self.blt_time > self.time_bw_shots:
                self.can_shoot = True

    def invulnerable_timer(self):
        if not self.vulnerable:
            if pg.time.get_ticks() - self.time_last_hit > 500:
                self.vulnerable = True

    def import_assets(self, asset_path):
        self.animations = {}
        for (index, folder) in enumerate(walk(asset_path)):
            if index == 0:
                for subfolder in folder[1]:
                    self.animations[subfolder] = []
            else:
                img_path = asset_path + "/" + folder[0].split("\\")[1]
                for img in sorted(folder[2], key=lambda string: int(string.split(".")[0])):
                    surf = pg.image.load(f"{img_path}/{img}").convert_alpha()
                    self.animations[folder[0].split("\\")[1]].append(surf)