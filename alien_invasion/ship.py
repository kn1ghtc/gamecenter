import pygame
import os
from pygame.sprite import Sprite

class Ship(Sprite):
    """A class to manage the ship."""

    def __init__(self, ai_game,player_number):
        """Initialize the ship and set its starting position."""
        super().__init__()
        self.screen = ai_game.screen
        self.screen_rect = ai_game.screen.get_rect()
        self.settings = ai_game.settings
        self.player_number = player_number
        # Load the ship image and get its rect.
        self.image = pygame.image.load(os.path.dirname(__file__) + '/images/spaceship_tut.bmp')
        self.rect = self.image.get_rect()

       # Set initial position based on player number
        self.rect.midbottom = self.screen_rect.midbottom
        self.rect.x += 100 if player_number == 1 else -100

        # Movement flags
        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False

        # Set custom controls
        self.set_controls()

    def set_controls(self):
        if self.player_number == 1:
            self.key_left = pygame.K_LEFT
            self.key_right = pygame.K_RIGHT
            self.key_up = pygame.K_UP
            self.key_down = pygame.K_DOWN
            self.key_shoot = pygame.K_SPACE
        else:
            self.key_left = pygame.K_a
            self.key_right = pygame.K_d
            self.key_up = pygame.K_w
            self.key_down = pygame.K_s
            self.key_shoot = pygame.K_1

    def update(self):
        """Update the ship's position based on the movement flags."""
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.rect.x += self.settings.ship_speed
        if self.moving_left and self.rect.left > 0:
            self.rect.x -= self.settings.ship_speed
        if self.moving_up and self.rect.top > 0:
            self.rect.y -= self.settings.ship_speed
        if self.moving_down and self.rect.bottom < self.screen_rect.bottom:
            self.rect.y += self.settings.ship_speed

    def center_ship(self):
        self.rect.midbottom = self.screen_rect.midbottom
        self.rect.x += 100 if self.player_number == 1 else -100

    def blitme(self):
        """Draw the ship at its current location."""
        self.screen.blit(self.image, self.rect)

