import pygame as pg

class Health:
    def __init__(self, player):
        self.player = player
        self.display_surface = pg.display.get_surface()
        self.health_surf = pg.image.load('./graphics/health.png').convert_alpha()
        self.font = pg.font.SysFont('Arial', 30)  # Added for challenge status
        
    def display_health(self):
        # Health icons
        for i in range(self.player.health):
            pos_x = 5 + i * (self.health_surf.get_width() + 5)
            pos_y = 10
            self.display_surface.blit(self.health_surf, (pos_x, pos_y))
        
        # Challenge status indicator
        status_text = "Challenge: Active"
        status_color = (0, 255, 0) if getattr(self.player, 'challenge_completed', False) else (255, 255, 0)
        status_surf = self.font.render(status_text, True, status_color)
        self.display_surface.blit(status_surf, (10, 50))