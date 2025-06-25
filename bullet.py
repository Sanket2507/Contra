import pygame as pg
import settings as st

class Bullet(pg.sprite.Sprite):
    def __init__(self, position, surface, dir, groups, is_player_shot=False):
        super().__init__(groups)
        self.z = st.LAYERS['Level']
        self.is_player_shot = is_player_shot

        self.image = surface
        if dir.x < 0:
            self.image = pg.transform.flip(self.image, True, False)
        
        self.rect = self.image.get_rect(center=position)
        self.mask = pg.mask.from_surface(self.image)

        self.direction = dir
        self.speed = 500
        self.pos = pg.math.Vector2(self.rect.center)
        self.start_time = pg.time.get_ticks()

    def update(self, deltaTime):
        self.pos += self.direction * self.speed * deltaTime
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if pg.time.get_ticks() - self.start_time > 1500:
            self.kill()

class BulletAnimation(pg.sprite.Sprite):
    def __init__(self, entity, surface_list, dir, groups):
        super().__init__(groups)
        self.z = st.LAYERS['Level']
        self.entity = entity

        self.frames = surface_list
        if dir.x < 0:
            self.frames = [pg.transform.flip(i, True, False) for i in self.frames]

        self.frame_index = 0
        self.image = self.frames[self.frame_index]

        if dir.x > 0:
            x_offset = 60
        else:
            x_offset = -60
        if entity.ducking:
            y_offset = 10
        else:
            y_offset = -15
        self.offset = pg.math.Vector2(x_offset, y_offset)

        self.rect = self.image.get_rect(center=self.entity.rect.center + self.offset)

    def animate(self, deltaTime):
        self.frame_index += 15 * deltaTime
        if int(self.frame_index) >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]

    def move_with_entity(self):
        self.rect.center = self.entity.rect.center + self.offset

    def update(self, deltaTime):
        self.animate(deltaTime)
        self.move_with_entity()