#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Core Game Class
Main game loop and state management
"""

import pygame
import sys
import os
import random
from pathlib import Path
from src.downloader import ResourceDownloader
from src.player import Player
from src.level import Level
from src.scoring import ScoringSystem
from src.audio import get_audio_manager
from src.config import load_config
from src.save import load_game, save_game, has_save
from src.font import get_text_renderer

class Game:
    """Main game class handling the game loop and state"""

    # Game constants
    WIDTH = 800
    HEIGHT = 600
    FPS = 60
    TITLE = "超级玛丽兄弟"

    def __init__(self):
        """Initialize the game"""
        self.screen = None
        self.clock = None
        self.running = False
        self.current_level = 1
        self.max_levels = 30

        # Game objects
        self.player = None
        self.level = None
        self.scoring = None

        # Fonts
        self.font = None
        self.chinese_font = None
        self.text_renderer = None

        # Audio
        self.audio_manager = None

        # Game state
        self.game_state = "menu"  # menu, playing, paused, game_over, level_complete, level_select
        self.score = 0
        self.lives = 3
        self.time_left = 400  # seconds
        self.music_enabled = True

        # Menu related
        self.menu_index = 0
        self.menu_options = []  # will be set after resources and save detection
        self.selected_level = 1

        # Assets path
        self.assets_dir = Path("assets")

        # Initialize Pygame
        pygame.init()
        pygame.mixer.init()

        # Set up display
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(self.TITLE)

        # Set up clock
        self.clock = pygame.time.Clock()

        # Load config then resources
        self.config = load_config(self.assets_dir)
        self.max_levels = int(self.config["game"].get("max_levels", self.max_levels))
        self.lives = int(self.config["game"].get("initial_lives", self.lives))
        self.time_left = float(self.config["game"].get("time_per_level", self.time_left))
        self.music_enabled = bool(self.config["game"].get("music_enabled", self.music_enabled))

        # Load resources
        self._load_resources()

        # Ensure 30 levels exist if levels folder empty
        self._ensure_levels()

        # Prepare menu options based on save state
        self._refresh_menu_options()

        # Initialize game objects
        self._init_game_objects()

    def _load_resources(self):
        """Load game resources"""
        print("Loading resources...")

        # Download resources if needed
        downloader = ResourceDownloader()
        if not downloader.verify_resources():
            print("Downloading missing resources...")
            downloader.download_all_resources()

        # Initialize font system
        self.text_renderer = get_text_renderer(str(self.assets_dir))

        # Initialize audio system
        self.audio_manager = get_audio_manager(str(self.assets_dir))
        if self.music_enabled:
            self.audio_manager.start_menu_music()

        print("Resources loaded successfully")

    def _init_game_objects(self):
        """Initialize game objects"""
        self.scoring = ScoringSystem()
        self._load_level(self.current_level)

    def _ensure_levels(self):
        levels_dir = Path("levels")
        try:
            if not levels_dir.exists() or not any(levels_dir.glob("level_*.json")):
                Level.generate_and_save_levels(self.max_levels, levels_dir)
                print(f"Generated {self.max_levels} procedural levels")
        except Exception as e:
            print(f"Failed to ensure levels: {e}")

    def _load_level(self, level_num):
        """Load a specific level"""
        try:
            self.level = Level(level_num, self.assets_dir)
            self.player = Player(self.level.player_start_pos, self.assets_dir, self.config.get("player", {}))
            self.time_left = float(self.config["game"].get("time_per_level", 400))  # Reset timer
            print(f"Level {level_num} loaded")
        except Exception as e:
            print(f"Failed to load level {level_num}: {e}")
            # Create a default level if loading fails
            self.level = Level.create_default_level(level_num, self.assets_dir)
            self.player = Player((100, 500), self.assets_dir, self.config.get("player", {}))

    def run(self):
        """Main game loop"""
        self.running = True

        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0  # Delta time in seconds

            self._handle_events()
            self._update(dt)
            self._render()

        self._cleanup()

    def _handle_events(self):
        """Handle user input and events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event.key)

    def _handle_keydown(self, key):
        """Handle key press events"""
        if self.game_state == "menu":
            if key == pygame.K_RETURN:
                self._activate_menu_choice()
            elif key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % len(self.menu_options)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % len(self.menu_options)
            elif key == pygame.K_q:
                self.running = False
            elif key == pygame.K_m:
                self.music_enabled = not self.music_enabled
                if self.music_enabled:
                    self.audio_manager.start_menu_music()
                else:
                    self.audio_manager.stop_music()

        elif self.game_state == "playing":
            if key == pygame.K_LEFT or key == pygame.K_a:
                self.player.move_left()
            elif key == pygame.K_RIGHT or key == pygame.K_d:
                self.player.move_right()
            elif key == pygame.K_SPACE or key == pygame.K_UP or key == pygame.K_w:
                self.player.jump()
            elif key == pygame.K_p:
                self.game_state = "paused"
            elif key == pygame.K_m:
                self.music_enabled = not self.music_enabled
                if self.music_enabled:
                    self.audio_manager.start_game_music()
                else:
                    self.audio_manager.stop_music()

        elif self.game_state == "paused":
            if key == pygame.K_p:
                self.game_state = "playing"
            elif key == pygame.K_q:
                self.game_state = "menu"
                self._refresh_menu_options()
                if self.music_enabled:
                    self.audio_manager.start_menu_music()
            elif key == pygame.K_m:
                self.music_enabled = not self.music_enabled
                if self.music_enabled:
                    self.audio_manager.start_game_music()
                else:
                    self.audio_manager.stop_music()

        elif self.game_state == "level_select":
            if key in (pygame.K_LEFT, pygame.K_a):
                self.selected_level = max(1, self.selected_level - 1)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_level = min(self.max_levels, self.selected_level + 1)
            elif key == pygame.K_RETURN:
                self._start_new_game(self.selected_level)
            elif key in (pygame.K_ESCAPE, pygame.K_q):
                self.game_state = "menu"

        elif self.game_state in ["game_over", "level_complete"]:
            if key == pygame.K_RETURN:
                if self.game_state == "level_complete" and self.current_level < self.max_levels:
                    self.current_level += 1
                    self._load_level(self.current_level)
                    self.game_state = "playing"
                else:
                    self.game_state = "menu"
                    self._refresh_menu_options()
                    if self.music_enabled:
                        self.audio_manager.start_menu_music()

    def _handle_keyup(self, key):
        """Handle key release events"""
        if self.game_state == "playing":
            if key in [pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d]:
                self.player.stop_moving()

    def _update(self, dt):
        """Update game state"""
        if self.game_state == "playing":
            # Update timer
            self.time_left -= dt
            if self.time_left <= 0:
                self._game_over()

            # Update game objects
            self.player.update(dt, self.level)
            self.level.update(dt, self.player)

            # Check collisions and game logic
            self._check_collisions()

            # Check win/lose conditions
            if self.player.y > self.HEIGHT + 100:  # Fell off screen
                self._lose_life()
            else:
                # Goal collision check
                if self.player.get_rect().colliderect(self.level.get_goal_rect()):
                    self._level_complete()

    def _check_collisions(self):
        """Check for collisions between game objects"""
        # Player vs coins
        coins_collected = self.level.check_coin_collisions(self.player)
        for coin in coins_collected:
            self.score += self.scoring.coin_points
            self._play_sound("coin")

        # Player vs enemies
        if self.level.check_enemy_collisions(self.player):
            self._lose_life()

        # Player vs powerups
        powerups_collected = self.level.check_powerup_collisions(self.player)
        for powerup in powerups_collected:
            if isinstance(powerup, dict) and powerup.get('type') == "mushroom":
                self.player.grow()
                self.score += self.scoring.powerup_points
                self._play_sound("powerup")

    def _lose_life(self):
        """Handle player losing a life"""
        self.lives -= 1
        if self.lives <= 0:
            self._game_over()
        else:
            # Reset player position
            self.player.reset(self.level.player_start_pos)
            self.time_left = float(self.config["game"].get("time_per_level", 400))
            self._save_progress()

    def _level_complete(self):
        """Handle level completion"""
        self.game_state = "level_complete"
        time_bonus = int(self.time_left * self.scoring.time_bonus_multiplier)
        self.score += time_bonus + self.scoring.level_complete_bonus
        self._play_sound("level_complete")
        self._save_progress()

    def _game_over(self):
        """Handle game over"""
        self.game_state = "game_over"
        self._play_sound("game_over")
        # On game over, do not overwrite existing save with dead state; keep last good save

    def _play_sound(self, sound_name):
        """Play a sound effect"""
        if self.audio_manager:
            try:
                if sound_name == "coin":
                    self.audio_manager.play_coin()
                elif sound_name == "jump":
                    self.audio_manager.play_jump()
                elif sound_name == "powerup":
                    self.audio_manager.play_powerup()
                elif sound_name == "level_complete":
                    self.audio_manager.play_level_complete()
                elif sound_name == "game_over":
                    self.audio_manager.play_game_over()
                else:
                    # Generic sound playback
                    getattr(self.audio_manager, f"play_{sound_name}", lambda: None)()
            except Exception as e:
                print(f"Failed to play sound {sound_name}: {e}")

    def _render(self):
        """Render the game"""
        self._render_gradient_bg()

        if self.game_state == "menu":
            self._render_menu()
        elif self.game_state == "playing":
            self._render_game()
        elif self.game_state == "paused":
            self._render_game()
            self._render_pause()
        elif self.game_state == "game_over":
            self._render_game_over()
        elif self.game_state == "level_complete":
            self._render_level_complete()
        elif self.game_state == "level_select":
            self._render_level_select()

        pygame.display.flip()

    def _render_menu(self):
        """Render main menu"""
        # Title
        self.text_renderer.draw_text(self.screen, "超级玛丽兄弟", (self.WIDTH//2, 140),
                   size_name="title", centered=True, shadow=True, outline=True)

        # Menu options
        base_y = 260
        for idx, text in enumerate(self.menu_options):
            color = (255, 255, 0) if idx == self.menu_index else (255, 255, 255)
            self.text_renderer.draw_text(self.screen, text, (self.WIDTH//2, base_y + idx * 48),
                       size_name="large", color=color, centered=True, shadow=True, outline=True)

        # Music hint
        music_text = "音乐: 开" if self.music_enabled else "音乐: 关"
        self.text_renderer.draw_text(self.screen, f"按 M 切换音乐 ({music_text})", (self.WIDTH//2, base_y + len(self.menu_options) * 48 + 20),
                   size_name="medium", centered=True, shadow=True, outline=True)

    def _render_game(self):
        """Render the game world"""
        # Render level
        self.level.render(self.screen)

        # Render player
        self.player.render(self.screen)

        # Render HUD
        self._render_hud()

    def _render_hud(self):
        """Render heads-up display"""
        # Score
        self.text_renderer.draw_text(self.screen, f"分数: {self.score}", (10, 10), shadow=True, outline=True)

        # Lives
        self.text_renderer.draw_text(self.screen, f"生命: {self.lives}", (10, 40), shadow=True, outline=True)

        # Level
        self.text_renderer.draw_text(self.screen, f"关卡: {self.current_level}", (10, 70), shadow=True, outline=True)

        # Time
        self.text_renderer.draw_text(self.screen, f"时间: {int(self.time_left)}", (self.WIDTH - 150, 10), shadow=True, outline=True)

        # Music state
        music_text = "开" if self.music_enabled else "关"
        self.text_renderer.draw_text(self.screen, f"音乐: {music_text}", (self.WIDTH - 150, 40), shadow=True, outline=True)

    def _render_pause(self):
        """Render pause overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        # Pause text
        self.text_renderer.draw_text(self.screen, "游戏暂停", (self.WIDTH//2, self.HEIGHT//2),
                   size_name="large", centered=True, shadow=True, outline=True)

        self.text_renderer.draw_text(self.screen, "按 P 继续", (self.WIDTH//2, self.HEIGHT//2 + 50),
                   size_name="medium", centered=True, shadow=True, outline=True)
        self.text_renderer.draw_text(self.screen, "按 M 切换音乐", (self.WIDTH//2, self.HEIGHT//2 + 90),
                   size_name="medium", centered=True, shadow=True, outline=True)

    def _render_game_over(self):
        """Render game over screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(192)
        self.screen.blit(overlay, (0, 0))

        # Game over text
        self.text_renderer.draw_text(self.screen, "游戏结束", (self.WIDTH//2, self.HEIGHT//2 - 50),
                   size_name="large", color=(255, 0, 0), centered=True, shadow=True, outline=True)

        self.text_renderer.draw_text(self.screen, f"最终分数: {self.score}", (self.WIDTH//2, self.HEIGHT//2),
                   size_name="medium", centered=True, shadow=True, outline=True)

        self.text_renderer.draw_text(self.screen, "按 ENTER 返回主菜单", (self.WIDTH//2, self.HEIGHT//2 + 50),
                   size_name="medium", centered=True, shadow=True, outline=True)

    def _render_level_complete(self):
        """Render level complete screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(192)
        self.screen.blit(overlay, (0, 0))

        # Level complete text
        self.text_renderer.draw_text(self.screen, f"关卡 {self.current_level} 完成!", (self.WIDTH//2, self.HEIGHT//2 - 50),
                       size_name="large", color=(0, 255, 0), centered=True, shadow=True, outline=True)

        self.text_renderer.draw_text(self.screen, f"关卡分数: {self.score}", (self.WIDTH//2, self.HEIGHT//2),
                   size_name="medium", centered=True, shadow=True, outline=True)

        if self.current_level < self.max_levels:
            self.text_renderer.draw_text(self.screen, "按 ENTER 进入下一关", (self.WIDTH//2, self.HEIGHT//2 + 50),
                                       size_name="medium", centered=True, shadow=True, outline=True)
        else:
            self.text_renderer.draw_text(self.screen, "恭喜通关! 按 ENTER 返回主菜单", (self.WIDTH//2, self.HEIGHT//2 + 50),
                                       size_name="medium", centered=True, shadow=True, outline=True)

    def _render_level_select(self):
        """Render level selection screen"""
        self.text_renderer.draw_text(self.screen, "选择关卡", (self.WIDTH//2, 160),
                   size_name="large", centered=True, shadow=True, outline=True)
        self.text_renderer.draw_text(self.screen, f"当前: 第 {self.selected_level} 关", (self.WIDTH//2, 240),
                   size_name="large", centered=True, shadow=True, outline=True)
        self.text_renderer.draw_text(self.screen, "左右切换，Enter开始，Esc返回", (self.WIDTH//2, 300),
                   size_name="medium", centered=True, shadow=True, outline=True)

    def _activate_menu_choice(self):
        """Activate current menu selection"""
        if not self.menu_options:
            return
        choice = self.menu_options[self.menu_index]
        if choice == "继续游戏" and has_save(self.assets_dir):
            self._continue_game()
        elif choice == "新游戏":
            self._start_new_game(1)
        elif choice == "关卡选择":
            self.selected_level = self.current_level
            self.game_state = "level_select"
        elif choice == "退出":
            self.running = False

    def _refresh_menu_options(self):
        """Refresh menu options based on save availability"""
        self.menu_options = (["继续游戏"] if has_save(self.assets_dir) else []) + ["新游戏", "关卡选择", "退出"]
        if self.menu_index >= len(self.menu_options):
            self.menu_index = 0

    def _start_new_game(self, start_level: int = 1):
        """Start a new game with defaults and selected level"""
        self.score = 0
        self.lives = int(self.config["game"].get("initial_lives", 3))
        self.current_level = max(1, min(self.max_levels, start_level))
        self._load_level(self.current_level)
        self.game_state = "playing"
        if self.music_enabled:
            self.audio_manager.start_game_music()
        self._save_progress()

    def _continue_game(self):
        """Continue from savegame"""
        data = load_game(self.assets_dir)
        if not data:
            return
        self.current_level = int(data.get("level", 1))
        self.score = int(data.get("score", 0))
        self.lives = int(data.get("lives", max(1, int(self.config["game"].get("initial_lives", 3)))))
        self.time_left = float(data.get("time_left", self.config["game"].get("time_per_level", 400)))
        self._load_level(self.current_level)
        self.game_state = "playing"
        if self.music_enabled:
            self.audio_manager.start_game_music()

    def _save_progress(self):
        """Persist current progress"""
        try:
            save_game(self.assets_dir, {
                "level": self.current_level,
                "score": self.score,
                "lives": self.lives,
                "time_left": int(self.time_left)
            })
        except Exception as e:
            print(f"Failed to save progress: {e}")

    def _cleanup(self):
        """Clean up resources"""
        pygame.quit()

    def _render_gradient_bg(self):
        """Render a simple vertical gradient background"""
        top = (120, 180, 255)
        bottom = (30, 100, 200)
        height = self.HEIGHT
        for y in range(height):
            t = y / max(1, height - 1)
            color = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t)
            )
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))

    def get_score(self):
        """Get current score"""
        return self.score

    def get_level(self):
        """Get current level"""
        return self.current_level

    def get_lives(self):
        """Get remaining lives"""
        return self.lives