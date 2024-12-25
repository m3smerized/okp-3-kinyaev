import random
import pygame
from pygame.sprite import Sprite

class Bonus(Sprite):
    def __init__(self, ai_game, bonus_type):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

       
        self.bonus_type = bonus_type

      
        if self.bonus_type == "life":
            self.image = os.path.join('resources', 'heart.bmp')
        elif self.bonus_type == "shield":
            self.image = pygame.image.load('resources/armor.bmp')

        self.image = pygame.transform.scale(self.image, (50, 50))

        self.rect = self.image.get_rect()



      
        self.rect.x = random.randint(0, ai_game.settings.screen_width - self.rect.width)
        self.rect.y = -self.rect.height

       
        self.speed = self.settings.bonus_speed

    def update(self):
        """Перемещает бонус вниз."""
        self.rect.y += self.speed

    def draw_bonus(self):
        """Отрисовывает бонус на экране."""
        self.screen.blit(self.image, self.rect)
