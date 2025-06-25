import pygame as pg
import settings as st
from entity import Entity

class Enemy(Entity):
    def __init__(self, position, asset_path, groups, create_bullet, player, coll_sprites):
        super().__init__(position=position, asset_path=asset_path, groups=groups, create_bullet=create_bullet)
        self.time_bw_shots = 700
        self.player = player
        self.bullet_damage = 1
        self.bullet_speed = 500

        for sprite in coll_sprites.sprites():
            if sprite.rect.collidepoint(self.rect.midbottom):
                self.rect.bottom = sprite.rect.top

    def get_face_dir(self):
        if self.player.rect.centerx < self.rect.centerx:
            self.move_dir = "left"
        else:
            self.move_dir = "right"
        
    def should_fire(self):
        pos_enemy = pg.math.Vector2(self.rect.center)
        pos_player = pg.math.Vector2(self.player.rect.center)
        dist = (pos_player - pos_enemy).magnitude()
        
        if self.rect.top - 20 < pos_player.y and self.rect.bottom + 20 > pos_player.y:
            same_y = True
        else:
            same_y = False

        if dist < 600 and same_y and self.can_shoot:
            if self.move_dir == "right":
                blt_dir = pg.math.Vector2(1, 0)
            else:
                blt_dir = pg.math.Vector2(-1, 0)

            y_offset = pg.math.Vector2(0, -15)
            blt_pos = self.rect.center + blt_dir * 60

            self.fire_bullet(blt_pos + y_offset, blt_dir, self)
            self.can_shoot = False
            self.blt_time = pg.time.get_ticks()
            self.fire_sound.play()
    
    def update(self, deltaTime):
        self.get_face_dir()
        self.animate(deltaTime)
        self.blink()
        self.blt_timer()
        self.invulnerable_timer()
        self.should_fire()
        self.check_alive()