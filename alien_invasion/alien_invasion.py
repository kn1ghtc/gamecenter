import sys
import pygame
from pygame.sprite import Group

from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from game_stats import GameStats
from sound_manager import SoundManager
from button import Button
from scoreboard import Scoreboard
from time import sleep


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        # set the clock to control how fast the screen updates
        self.clock = pygame.time.Clock()

        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        # self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        self.bg_color = self.settings.bg_color
        pygame.display.set_caption("Alien Invasion")

        # Initialize stats.
        self.stats = GameStats(self)

        #sound manager
        self.sound_manager = SoundManager()

        # Make a ship.
        self.ships = [Ship(self, 1), Ship(self, 2)]
        self.bullets = [Group(), Group()]

        self.aliens = Group()
        self._create_fleet()
        self.play_button = Button(self, "Play")
        self.sb = Scoreboard(self)


    def _create_fleet(self):
        """Create the fleet of aliens."""
        # Make an alien and find the number of aliens in a row.
        # Spacing between each alien is one alien width.
        alien = Alien(self.settings, self.screen)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width) # the available space for the alien in the x direction
        number_aliens_x = available_space_x // (2 * alien_width) # the number of aliens in a row

        # Determine the number of rows of aliens that fit on the screen.
        ship_height = self.ships[0].rect.height
        available_space_y = (self.settings.screen_height - (6 * alien_height) - (2*ship_height))
        number_rows = available_space_y // (2 * alien_height)

        # Create the full fleet of aliens.
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)


    def _create_alien(self, alien_number, row_number):
        """Create an alien and place it in the row."""
        alien = Alien(self.settings, self.screen)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien_height + 2 * alien_height * row_number
        self.aliens.add(alien)

    def _check_events(self):
        """Respond to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)


    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        for ship in self.ships:
            if event.key == ship.key_right:
                ship.moving_right = True
            elif event.key == ship.key_left:
                ship.moving_left = True
            elif event.key == ship.key_up:
                ship.moving_up = True
            elif event.key == ship.key_down:
                ship.moving_down = True
            elif event.key == ship.key_shoot:
                self._fire_bullet(ship)
        if event.key == pygame.K_q:
            sys.exit()


    def _check_keyup_events(self, event):
        """Respond to key releases."""
        for ship in self.ships:
            if event.key == ship.key_right:
                ship.moving_right = False
            elif event.key == ship.key_left:
                ship.moving_left = False
            elif event.key == ship.key_up:
                ship.moving_up = False
            elif event.key == ship.key_down:
                ship.moving_down = False


    def _fire_bullet(self,ship):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets[ship.player_number - 1]) < self.settings.bullets_allowed:
            new_bullet = Bullet(self.settings, self.screen, ship)
            self.bullets[ship.player_number - 1].add(new_bullet)
            self.sound_manager.play_bullet_sound()


    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        for bullet_group in self.bullets:
            bullet_group.update()
            for bullet in bullet_group.copy():
                if bullet.rect.bottom <= 0:
                    bullet_group.remove(bullet)
            self._check_bullet_alien_collisions(bullet_group)

    def _check_bullet_alien_collisions(self,bullet_group):
        collisions = pygame.sprite.groupcollide(bullet_group, self.aliens, False, True)
        if collisions:
            self.sound_manager.play_alien_explode_sound()
            for aliens in collisions.values():
                player = 0 if bullet_group == self.bullets[0] else 1
                self.stats.score[player] += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()
        if not self.aliens:
            for bullet_group in self.bullets:
                bullet_group.empty()
            self._create_fleet()
            self.settings.increase_speed()
            self.stats.level += 1
            self.sb.prep_level()


    def _update_aliens(self):
        """Check if the fleet is at an edge,
        and then update the positions of all aliens in the fleet."""
        self._check_fleet_edges()
        self.aliens.update()
        for ship in self.ships:
            if pygame.sprite.spritecollideany(ship, self.aliens):
                self._ship_hit(ship)

    def _ship_hit(self, ship):
        """Respond to the ship being hit by an alien."""
        if self.stats.ships_left[ship.player_number - 1] > 0:
            self.sound_manager.play_ship_explode_sound()
            self.stats.ships_left[ship.player_number - 1] -= 1
            self.sb.prep_ships()
            self.aliens.empty()
            for bullet_group in self.bullets:
                bullet_group.empty()
            self._create_fleet()
            ship.center_ship()
            sleep(0.5)
        else:
            self.stats.game_active = False
            self.sound_manager.stop_background_music()
            pygame.mouse.set_visible(True)



    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self.settings.initialize_dynamic_settings()
            # Reset the game statistics.
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            for bullet_group in self.bullets:
                bullet_group.empty()
            self.aliens.empty()
            # Hide the mouse cursor.
            pygame.mouse.set_visible(False)
            # Reset the game settings.

            # Create a new fleet and center the ship.
            self._create_fleet()
            for ship in self.ships:
                ship.center_ship()

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Treat this the same as if the ship got hit.
                for ship in self.ships:
                    self._ship_hit(ship)
                break

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        self.screen.fill(self.settings.bg_color)
        for ship in self.ships:
            ship.blitme()
        for bullet_group in self.bullets:
            for bullet in bullet_group.sprites():
                bullet.draw_bullet()
        self.aliens.draw(self.screen)
        if self.stats.game_active:
            self.sb.show_score()
        else:
            self.play_button.draw_button()
        pygame.display.flip()


    def run_game(self):
        """Start the main loop for the game."""

        while True:       
            # Watch for keyboard and mouse events.
            self._check_events()

            # 激活游戏时更新ship，子弹，外星人位置
            if self.stats.game_active:
                for ship in self.ships:
                    ship.update()
                # Update bullet positions.
                self._update_bullets()
                #update the aliens position.
                self._update_aliens()
                # Redraw the screen during each pass through the loop.


            self._update_screen()
            # Set the speed of the loop.
            self.clock.tick(60)


# Make a game instance, and run the game.
if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()
