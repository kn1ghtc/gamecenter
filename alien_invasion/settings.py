from math import e


class Settings:
    """A class to store all settings for Alien Invasion."""

    def __init__(self):
        """Initialize the game's settings."""
        # Screen settings
        self.screen_width = 3440
        self.screen_height = 1400
        self.bg_color = (230, 230, 230)

        # Ship settings
        self.ship_limit = 5

        # Bullet settings
        self.bullet_width = 1500
        self.bullet_height = 10
        self.bullet_color = (60, 60, 60)
        self.bullets_allowed = 2000

        # Alien settings
        self.fleet_drop_speed = 50

        # How quickly the game speeds up
        self.speedup_scale = 1.4
        # How quickly the alien point values increase
        self.score_scale = 3.0

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """Initialize settings that change throughout the game."""
        self.ship_speed = 1.0
        self.bullet_speed = 5.0
        self.alien_speed = 1.0

        # fleet_direction of 1 represents right; -1 represents left.
        self.fleet_direction = 1

        # Scoring
        self.alien_points = 10

    def increase_speed(self):
        """Increase speed settings and alien point values."""
        if self.ship_speed < 20:
            self.ship_speed *= self.speedup_scale
        else:
            self.ship_speed = 20
        if self.bullet_speed < 55:
            self.bullet_speed *= self.speedup_scale
        else:
            self.bullet_speed = 55
        if self.alien_speed < 5:
            self.alien_speed *= self.speedup_scale
        else:
            self.alien_speed = 5

        self.alien_points = int(self.alien_points * self.score_scale)

