import pygame as pg
import settings as st
import sys
from tiles import Tile, TileForCollision, MovingPlatform
from player import Player
from enemy import Enemy
from bullet import Bullet, BulletAnimation
from health import Health
from pytmx.util_pygame import load_pygame

class AllSprites(pg.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pg.display.get_surface()
        self.offset = pg.math.Vector2()
        self.sky_fg = pg.image.load('./graphics/sky/fg_sky.png').convert_alpha()
        self.sky_bg = pg.image.load('./graphics/sky/bg_sky.png').convert_alpha()
        self.margin = st.WINDOW_WIDTH / 2
        tmx_map = load_pygame('./data/map.tmx')
        map_width = tmx_map.tilewidth * tmx_map.width + 2 * self.margin
        self.sky_width = self.sky_bg.get_width()
        self.sky_blit_num = int(map_width // self.sky_width)

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - st.WINDOW_WIDTH / 2
        self.offset.y = player.rect.centery - st.WINDOW_HEIGHT / 2

        for i in range(self.sky_blit_num):
            pos_x = -self.margin + (i * self.sky_width)
            self.display_surface.blit(self.sky_bg, (pos_x - (self.offset.x / 3), (650 - self.offset.y / 3)))
            self.display_surface.blit(self.sky_fg, (pos_x - (self.offset.x / 2), (850 - self.offset.y / 2)))

        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.z):
            offset_rect = sprite.image.get_rect(center=sprite.rect.center)
            offset_rect.center -= self.offset
            self.display_surface.blit(sprite.image, offset_rect)

class GameWindow:
    def __init__(self):
        pg.init()
        self.display_surface = pg.display.set_mode((st.WINDOW_WIDTH, st.WINDOW_HEIGHT))
        pg.display.set_caption("Contra")
        self.clk = pg.time.Clock()

        self.all_sprites = AllSprites()
        self.coll_grp = pg.sprite.Group()
        self.mov_platforms_grp = pg.sprite.Group()
        self.bullet_grp = pg.sprite.Group()
        self.vulnerable_grp = pg.sprite.Group()

        self.setup()
        self.health_bar = Health(self.my_player)

        self.bullet_surf = pg.image.load('./graphics/bullet.png').convert_alpha()
        self.fire_surfs = [
            pg.image.load('./graphics/fire/0.png').convert_alpha(),
            pg.image.load('./graphics/fire/1.png').convert_alpha()
        ]

        self.bg_music = pg.mixer.Sound('./audio/music.wav')
        self.bg_music.play(loops=-1)

        # Game state variables
        self.start_time = pg.time.get_ticks()
        self.shots_fired = 0
        self.shots_hit = 0
        self.game_over = False
        self.difficulty_increased = False
        self.font = pg.font.SysFont('Arial', 30)

    def setup(self):
        tmx_map = load_pygame('./data/map.tmx')

        for (x, y, surf) in tmx_map.get_layer_by_name("Level").tiles():
            TileForCollision((x * 64, y * 64), surf, [self.all_sprites, self.coll_grp])

        for layer in ["BG", "BG Detail", "FG Detail Bottom", "FG Detail Top"]:
            for (x, y, surf) in tmx_map.get_layer_by_name(layer).tiles():
                Tile((x * 64, y * 64), surf, self.all_sprites, layer)        

        for obj in tmx_map.get_layer_by_name("Entities"):
            if obj.name == "Player":
                self.my_player = Player(
                    (obj.x, obj.y), 
                    "./graphics/player", 
                    [self.all_sprites, self.vulnerable_grp], 
                    self.coll_grp, 
                    self.fire_bullet
                )
            elif obj.name == "Enemy":
                Enemy(
                    (obj.x, obj.y), 
                    "./graphics/enemy", 
                    [self.all_sprites, self.vulnerable_grp], 
                    self.fire_bullet, 
                    self.my_player, 
                    coll_sprites=self.coll_grp
                )

        self.border_rect_list = []
        for obj in tmx_map.get_layer_by_name("Platforms"):
            if obj.name == "Platform":
                MovingPlatform((obj.x, obj.y), obj.image, [self.all_sprites, self.coll_grp, self.mov_platforms_grp])
            else:
                border_rect = pg.Rect(obj.x, obj.y, obj.width, obj.height)
                self.border_rect_list.append(border_rect)

    def platform_restriction(self):
        for plt in self.mov_platforms_grp.sprites():
            for border in self.border_rect_list:
                if plt.rect.colliderect(border):
                    if plt.direction.y < 0:
                        plt.rect.top = border.bottom
                        plt.pos.y = plt.rect.y
                        plt.direction.y = 1
                    else:
                        plt.rect.bottom = border.top
                        plt.pos.y = plt.rect.y
                        plt.direction.y = -1
            
            if plt.rect.colliderect(self.my_player.rect) and self.my_player.rect.centery > plt.rect.centery:
                plt.rect.bottom = self.my_player.rect.top
                plt.pos.y = plt.rect.y
                plt.direction.y = -1

    def fire_bullet(self, position, dir, shooter):
        is_player = shooter == self.my_player
        Bullet(position, self.bullet_surf, dir, [self.all_sprites, self.bullet_grp], is_player_shot=is_player)
        BulletAnimation(entity=shooter, surface_list=self.fire_surfs, dir=dir, groups=self.all_sprites)

    def bullet_collisions(self):
        for bullet in self.bullet_grp:
            if bullet.is_player_shot:
                self.shots_fired += 1
                break
        
        for obst in self.coll_grp.sprites():
            pg.sprite.spritecollide(obst, self.bullet_grp, True)
        
        for sprite in self.vulnerable_grp.sprites():
            if pg.sprite.spritecollide(sprite, self.bullet_grp, True, pg.sprite.collide_mask):
                if sprite != self.my_player:
                    self.shots_hit += 1
                sprite.damage()

    def display_game_stats(self):
        current_time = (pg.time.get_ticks() - self.start_time) // 1000
        minutes = current_time // 60
        seconds = current_time % 60
        timer_text = f"Time: {minutes}:{seconds:02d}"
        timer_surf = self.font.render(timer_text, True, (255, 255, 255))
        self.display_surface.blit(timer_surf, (st.WINDOW_WIDTH - 200, 10))

        accuracy = (self.shots_hit / self.shots_fired * 100) if self.shots_fired > 0 else 0
        accuracy_text = f"Accuracy: {accuracy:.1f}%"
        accuracy_surf = self.font.render(accuracy_text, True, (255, 255, 255))
        self.display_surface.blit(accuracy_surf, (st.WINDOW_WIDTH - 200, 50))

    def check_game_over_conditions(self):
        if self.my_player.health <= 0 and not self.game_over:
            self.game_over = True
            current_time = (pg.time.get_ticks() - self.start_time) // 1000
            accuracy = (self.shots_hit / self.shots_fired * 100) if self.shots_fired > 0 else 0
            
            if accuracy > 1 and current_time < st.CHALLENGE_PARAMS['time_limit']:
                return self.show_prompt("Challenge Complete! Increase difficulty? (Y/N)")
            else:
                self.show_message("Better luck next time!")
                return False
        return False

    def show_prompt(self, message):
        prompt = self.font.render(message, True, (255, 255, 0))
        self.display_surface.blit(prompt, (st.WINDOW_WIDTH//2 - 200, st.WINDOW_HEIGHT//2))
        pg.display.update()
        
        waiting = True
        while waiting:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_y:
                        return True
                    elif event.key == pg.K_n:
                        return False
                elif event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
        return False

    def show_message(self, message):
        msg = self.font.render(message, True, (255, 0, 0))
        self.display_surface.blit(msg, (st.WINDOW_WIDTH//2 - 150, st.WINDOW_HEIGHT//2))
        pg.display.update()
        pg.time.delay(2000)  # Show message for 2 seconds

    def increase_difficulty(self):
        for enemy in [s for s in self.vulnerable_grp if isinstance(s, Enemy)]:
            enemy.bullet_damage = st.CHALLENGE_PARAMS['damage_increase']
            enemy.bullet_speed = st.CHALLENGE_PARAMS['speed_increase']
        self.difficulty_increased = True

    def reset_game(self):
        self.__init__()
        self.runGame()

    def runGame(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if self.game_over and event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:
                        self.reset_game()
            
            dt = self.clk.tick(120)/1000
            self.display_surface.fill((249, 131, 103))

            if not self.game_over:
                self.platform_restriction()
                self.all_sprites.update(dt)
                self.bullet_collisions()
                
                if self.check_game_over_conditions():
                    self.increase_difficulty()
                    self.reset_game()
            else:
                restart_msg = self.font.render("Press R to restart", True, (255, 255, 255))
                self.display_surface.blit(restart_msg, (st.WINDOW_WIDTH//2 - 100, st.WINDOW_HEIGHT//2 + 50))

            self.all_sprites.custom_draw(self.my_player)
            self.health_bar.display_health()
            self.display_game_stats()

            pg.display.update()

if __name__ == "__main__":
    window = GameWindow()
    window.runGame()