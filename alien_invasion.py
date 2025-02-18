import sys
from time import sleep
import os
import random

import pickle

import pygame
from pygame.mixer import Sound

from settings import  Settings
from game_stats import GameStats
from ship import Ship
from bullet import Bullet
from alien import Alien
from bonus import Bonus

class AlienInvasion:
    """Класс для управления ресурсами и поведением игры."""

    def __init__(self):
        """Инициализирует игру и создает игровые ресурсы."""
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")

        self.stats = GameStats(self)

        self.ship = Ship(self)
        self.shoot_sound = Sound(os.path.join('resources', 'shoot.wav'))
        self.enemy_death_sound = Sound(os.path.join('resources', 'kill.wav'))
        self.damage_sound = Sound(os.path.join('resources', 'game_over.wav'))

        self.bonuses = pygame.sprite.Group()
        self.shield_active = False
        self.shield_end_time = 0
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()
        

    def run_game(self):
        """Запуск основного цикла игры."""
        while True:
            # Отслеживание событий клавиатуры и мыши.
            self._check_events()
            
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()

    def save_game(self, filename='savefile.pkl'):
        """Сохраняет текущий уровень, очки и здоровье в файл."""
        game_data = {
            "level": self.settings.level,
            "score": self.stats.score,
            "health": self.stats.ships_left,
        }
        with open(filename, "wb") as file:
            pickle.dump(game_data, file)
        print("Игра сохранена!")

    def load_game(self, filename='savefile.pkl'):
        """Загружает сохраненные данные игры."""
        try:
            with open(filename, "rb") as file:
                game_data = pickle.load(file)
                self.settings.level = game_data["level"]
                self.score = game_data["score"]
                self.stats.ships_left = game_data["health"]

            self.settings.initialize_dynamic_settings()
            for _ in range(self.settings.level - 1):  # Увеличиваем скорости для всех предыдущих уровней
                self.settings.increase_speed()



            self.aliens.empty()
            self.bullets.empty()
            self._create_fleet()
            print("Игра загружена!")
        except FileNotFoundError:
            print("Файл сохранения не найден!")
        
    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)

            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)                 

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self.shoot_sound.play()
            self._fire_bullet()
        elif event.key == pygame.K_s:
            self.save_game() 
        elif event.key == pygame.K_l:
            self.load_game()  

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        self.bullets.update()

        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        
        self._check_bullet_alien_collisions()

    def _create_bonus(self):
        if random.random() < self.settings.bonus_probability:
            bonus_type = random.choice(["life", "shield"])
            bonus = Bonus(self, bonus_type)
            self.bonuses.add(bonus)
        
        

    def _update_aliens(self):
        self._check_fleet_edges()
        self.aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        self._check_bonus_collisions()
        self._check_aliens_bottom()
    

    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()

        self.bonuses.update()
        for bonus in self.bonuses.sprites():
            bonus.draw_bonus()

        self.aliens.draw(self.screen)

        
        self._draw_lives()


        pygame.display.flip()
    
    def _create_fleet(self):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        ship_height = self.ship.rect.height 
        available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)

        number_rows = available_space_y // (2 * alien_height)
        
        for row_number in range(number_rows): 
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        alien = Alien(self)

        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)
    
    def _check_fleet_edges(self):
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
    
    def _change_fleet_direction(self):
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_bullet_alien_collisions(self):
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
        if collisions:
            self.enemy_death_sound.play()
            for aliens in collisions.values():
                for alien in aliens:
                    self._create_bonus()

    
        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.level += 1
            self.settings.increase_speed()
    
    def  _ship_hit(self):

        if self.shield_active:
            return
        
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1

            self.aliens.empty()
            self.bullets.empty()

            self._create_fleet()
            self.ship.center_ship()

            self.damage_sound.play()
            sleep(0.5)
        else:
            self.stats.game_active = False
        
    def _check_aliens_bottom(self):
        
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _draw_lives(self):
        lives_text = f"Lives: {self.stats.ships_left}"
        lives_image = self.settings.font.render(lives_text, True, (30, 30, 30), self.settings.bg_color)
        lives_rect = lives_image.get_rect()
        lives_rect.topright = (self.settings.screen_width - 20, 20)  # Позиция в правом верхнем углу
        self.screen.blit(lives_image, lives_rect)

    def _check_bonus_collisions(self):
        collisions = pygame.sprite.spritecollide(self.ship, self.bonuses, True)
        for bonus in collisions:
            if bonus.bonus_type == "life":
                self.stats.ships_left += 1
            elif bonus.bonus_type == "shield":
                self.shield_active = True
                self.shield_end_time = pygame.time.get_ticks() + self.settings.shield_duration
            elif bonus.bonus_type == "power_bullet":
                self.settings.bullet_width *= 2


if __name__ == '__main__':
    # Создание экземпляра и запуск игры.
    ai = AlienInvasion()
    ai.run_game()
