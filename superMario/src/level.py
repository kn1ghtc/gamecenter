#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Level Class
Handles level loading, rendering, and game objects
"""

import pygame
import json
import random
from pathlib import Path
from itertools import islice

class Level:
    """Level class handling level data and rendering"""

    # Level constants
    TILE_SIZE = 32
    LEVEL_WIDTH = 50  # tiles
    LEVEL_HEIGHT = 20  # tiles

    def __init__(self, level_num, assets_dir):
        """Initialize level"""
        self.level_num = level_num
        self.assets_dir = Path(assets_dir).resolve()

        # Level data
        self.tiles = []  # 2D list of tile types
        self.width = self.LEVEL_WIDTH * self.TILE_SIZE
        self.height = self.LEVEL_HEIGHT * self.TILE_SIZE

        # Game objects
        self.coins = []
        self.enemies = []
        self.powerups = []

        # Player start position
        self.player_start_pos = (100, 500)

        # Goal position
        self.goal_pos = (self.width - 100, 400)

        # Rendering helpers
        self.background_layers: list[pygame.Surface] = []
        self.foreground_decorations: list[tuple[pygame.Surface, tuple[int, int]]] = []
        self._collidable_cache = None

        # Load level data
        self._load_level_data()

        # Load assets
        self._load_assets()

    def _load_level_data(self):
        """Load level data from file or generate procedurally"""
        level_file = Path(__file__).resolve().parent.parent / "levels" / f"level_{self.level_num}.json"

        if level_file.exists():
            self._load_from_file(level_file)
        else:
            self._generate_level()

    def _load_from_file(self, level_file):
        """Load level from JSON file"""
        try:
            with open(level_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.tiles = data.get('tiles', [])
            self.coins = data.get('coins', [])
            self.enemies = data.get('enemies', [])
            self.powerups = data.get('powerups', [])
            self.player_start_pos = tuple(data.get('player_start', [100, 500]))
            self.goal_pos = tuple(data.get('goal', [self.width - 100, 400]))
            self._collidable_cache = None

        except Exception as e:
            print(f"Failed to load level {self.level_num}: {e}")
            self._generate_level()

    def _generate_level(self):
        """Generate a procedural level"""
        random.seed(1000 + self.level_num)
        # Initialize empty level
        self.tiles = [[0 for _ in range(self.LEVEL_WIDTH)] for _ in range(self.LEVEL_HEIGHT)]

        # Generate ground
        for x in range(self.LEVEL_WIDTH):
            self.tiles[self.LEVEL_HEIGHT - 1][x] = 1  # Ground tile
            if x % 4 == 0:  # Every 4th tile
                self.tiles[self.LEVEL_HEIGHT - 2][x] = 1  # Grass on top

        # Generate platforms
        platform_count = 5 + self.level_num // 2  # More platforms in higher levels
        for _ in range(platform_count):
            platform_x = random.randint(5, self.LEVEL_WIDTH - 10)
            platform_y = random.randint(8, self.LEVEL_HEIGHT - 5)
            platform_width = random.randint(3, 8)

            for i in range(platform_width):
                if platform_x + i < self.LEVEL_WIDTH:
                    self.tiles[platform_y][platform_x + i] = 1

        # Generate pipes
        pipe_count = 2 + self.level_num // 5
        for _ in range(pipe_count):
            pipe_x = random.randint(10, self.LEVEL_WIDTH - 5)
            pipe_height = random.randint(2, 4)

            for h in range(pipe_height):
                self.tiles[self.LEVEL_HEIGHT - 2 - h][pipe_x] = 2  # Pipe tile
                self.tiles[self.LEVEL_HEIGHT - 2 - h][pipe_x + 1] = 2

        # Generate coins
        coin_count = 10 + self.level_num * 2
        for _ in range(coin_count):
            coin_x = random.randint(1, self.LEVEL_WIDTH - 2)
            coin_y = random.randint(5, self.LEVEL_HEIGHT - 3)

            # Make sure coin is not in solid tile
            if self.tiles[coin_y][coin_x] == 0:
                self.coins.append((coin_x * self.TILE_SIZE, coin_y * self.TILE_SIZE))

        # Generate enemies
        enemy_count = 3 + self.level_num // 3
        for _ in range(enemy_count):
            enemy_x = random.randint(10, self.LEVEL_WIDTH - 5)
            enemy_y = self.LEVEL_HEIGHT - 2  # On ground

            # Make sure position is clear
            if self.tiles[enemy_y][enemy_x] == 0:
                self.enemies.append({
                    'x': enemy_x * self.TILE_SIZE,
                    'y': enemy_y * self.TILE_SIZE,
                    'type': 'goomba' if random.random() < 0.7 else 'koopa',
                    'direction': 1 if random.random() < 0.5 else -1
                })

        # Generate powerups (more in higher levels)
        if self.level_num >= 5 and random.random() < 0.3:
            powerup_x = random.randint(5, self.LEVEL_WIDTH - 5)
            powerup_y = random.randint(8, self.LEVEL_HEIGHT - 5)

            if self.tiles[powerup_y][powerup_x] == 0:
                self.powerups.append({
                    'x': powerup_x * self.TILE_SIZE,
                    'y': powerup_y * self.TILE_SIZE,
                    'type': 'mushroom'
                })

        self._collidable_cache = None

    @classmethod
    def create_default_level(cls, level_num, assets_dir):
        """Create a simple default level for testing"""
        level = cls.__new__(cls)
        level.level_num = level_num
        level.assets_dir = Path(assets_dir)
        level.tiles = [[0 for _ in range(cls.LEVEL_WIDTH)] for _ in range(cls.LEVEL_HEIGHT)]
        level.width = cls.LEVEL_WIDTH * cls.TILE_SIZE
        level.height = cls.LEVEL_HEIGHT * cls.TILE_SIZE
        level.coins = [(200, 400), (400, 300), (600, 200)]
        level.enemies = []
        level.powerups = []
        level.player_start_pos = (100, 500)
        level.goal_pos = (level.width - 100, 400)

        # Simple ground
        for x in range(cls.LEVEL_WIDTH):
            level.tiles[cls.LEVEL_HEIGHT - 1][x] = 1

        level._load_assets()
        return level

    def _load_assets(self):
        """Load level assets"""
        try:
            tiles_path = self._find_first_asset(["tiles.png", "tilesheet.png", "tilemap.png", "ground.png"])
            self.tileset = pygame.image.load(str(tiles_path)).convert_alpha() if tiles_path else None

            # Load individual sprites
            self.coin_sprite = self._load_sprite("coin")
            self.enemy_sprite = self._load_sprite("enemy")
            self.powerup_sprite = self._load_sprite("powerup")
            self.goal_sprite = self._load_sprite("goal")

            self._load_background_layers()

        except Exception as e:
            print(f"Failed to load level assets: {e}")
            self.tileset = None
            self.coin_sprite = None
            self.enemy_sprite = None
            self.powerup_sprite = None
            self.goal_sprite = None
            self.background_layers = []

    def _load_sprite(self, name):
        """Load a single sprite"""
        try:
            sprite_path = self.assets_dir / "images" / f"{name}.png"
            if sprite_path.exists():
                return pygame.image.load(str(sprite_path)).convert_alpha()
            # Fallback: search recursively for named sprite
            for candidate in (self.assets_dir / "images").rglob(f"{name}*.png"):
                return pygame.image.load(str(candidate)).convert_alpha()
        except:
            pass
        return None

    def _find_first_asset(self, candidates):
        """Find first matching asset file name from list"""
        images_dir = self.assets_dir / "images"
        for candidate in candidates:
            direct = images_dir / candidate
            if direct.exists():
                return direct
        # recursive search fallback
        lower_candidates = [c.lower() for c in candidates]
        for path in images_dir.rglob("*.png"):
            if any(candidate in path.name.lower() for candidate in lower_candidates):
                return path
        return None

    def _load_background_layers(self):
        """Load layered backgrounds for parallax rendering"""
        images_dir = self.assets_dir / "images"
        layer_candidates = []
        patterns = ("background", "bg", "parallax")
        for path in images_dir.rglob("*.png"):
            name = path.name.lower()
            if any(pat in name for pat in patterns):
                layer_candidates.append(path)

        # Prioritize sorted order to keep near/far layers consistent
        self.background_layers = []
        for path in islice(sorted(layer_candidates), 5):
            try:
                layer_surface = pygame.image.load(str(path)).convert_alpha()
                self.background_layers.append(layer_surface)
            except Exception as exc:  # pragma: no cover - pygame specific
                print(f"Failed to load background layer {path}: {exc}")

    def update(self, dt, player):
        """Update level objects"""
        # Update enemies
        for enemy in self.enemies:
            self._update_enemy(enemy, dt)

        # Update powerups (simple animation)
        for powerup in self.powerups:
            powerup['animation_timer'] = powerup.get('animation_timer', 0) + dt
            powerup['y_offset'] = 5 * (powerup['animation_timer'] * 2) % 10 - 5

    def _update_enemy(self, enemy, dt):
        """Update enemy movement"""
        speed = 50  # pixels per second
        enemy['x'] += enemy['direction'] * speed * dt

        # Check bounds and reverse direction
        if enemy['x'] <= 0 or enemy['x'] >= self.width - 32:
            enemy['direction'] *= -1

    def render(self, screen, camera_x: float = 0.0):
        """Render the level"""
        self._render_background(screen, camera_x)
        # Render tiles
        self._render_tiles(screen, camera_x)

        # Render coins
        self._render_coins(screen, camera_x)

        # Render enemies
        self._render_enemies(screen, camera_x)

        # Render powerups
        self._render_powerups(screen, camera_x)

        # Render goal
        self._render_goal(screen, camera_x)

    def _render_background(self, screen, camera_x: float):
        if not self.background_layers:
            return

        for idx, layer in enumerate(self.background_layers):
            parallax = 0.15 + idx * 0.15
            width = layer.get_width()
            height = layer.get_height()
            y_pos = max(0, self.height - height)
            offset = - (camera_x * parallax) % width
            tiles_needed = int((screen.get_width() / width) + 2)
            for i in range(-1, tiles_needed):
                screen.blit(layer, (offset + i * width, y_pos))

    def _render_tiles(self, screen, camera_x: float):
        """Render level tiles"""
        for y in range(self.LEVEL_HEIGHT):
            for x in range(self.LEVEL_WIDTH):
                tile_type = self.tiles[y][x]
                if tile_type > 0:
                    rect = pygame.Rect(x * self.TILE_SIZE, y * self.TILE_SIZE,
                                     self.TILE_SIZE, self.TILE_SIZE)
                    draw_rect = rect.move(-camera_x, 0)
                    if draw_rect.right < 0 or draw_rect.left > screen.get_width():
                        continue

                    if self.tileset and tile_type == 1:
                        # Ground tile
                        screen.blit(self.tileset, draw_rect, (0, 0, self.TILE_SIZE, self.TILE_SIZE))
                    elif self.tileset and tile_type == 2:
                        # Pipe tile
                        screen.blit(self.tileset, draw_rect, (32, 0, self.TILE_SIZE, self.TILE_SIZE))
                    else:
                        # Default colored tiles
                        if tile_type == 1:
                            color = (34, 139, 34)  # Green for ground
                        elif tile_type == 2:
                            color = (0, 100, 0)   # Dark green for pipes
                        else:
                            color = (128, 128, 128)  # Gray for others

                        pygame.draw.rect(screen, color, draw_rect)
                        pygame.draw.rect(screen, (0, 0, 0), draw_rect, 1)  # Black border

    def _render_coins(self, screen, camera_x: float):
        """Render coins"""
        for coin_x, coin_y in self.coins:
            if self.coin_sprite:
                screen.blit(self.coin_sprite, (coin_x - camera_x, coin_y))
            else:
                # Draw coin as yellow circle
                pygame.draw.circle(screen, (255, 215, 0), (coin_x - camera_x + 16, coin_y + 16), 12)
                pygame.draw.circle(screen, (255, 255, 0), (coin_x - camera_x + 16, coin_y + 16), 8)

    def _render_enemies(self, screen, camera_x: float):
        """Render enemies"""
        for enemy in self.enemies:
            if self.enemy_sprite:
                screen.blit(self.enemy_sprite, (enemy['x'] - camera_x, enemy['y']))
            else:
                # Draw enemy as brown rectangle
                color = (139, 69, 19) if enemy['type'] == 'goomba' else (160, 82, 45)
                pygame.draw.rect(screen, color, (enemy['x'] - camera_x, enemy['y'], 32, 32))

    def _render_powerups(self, screen, camera_x: float):
        """Render powerups"""
        for powerup in self.powerups:
            y_offset = powerup.get('y_offset', 0)
            if self.powerup_sprite:
                screen.blit(self.powerup_sprite, (powerup['x'] - camera_x, powerup['y'] + y_offset))
            else:
                # Draw powerup as red mushroom
                pygame.draw.circle(screen, (255, 0, 0), (powerup['x'] - camera_x + 16, powerup['y'] + 16 + y_offset), 12)
                pygame.draw.rect(screen, (255, 0, 0), (powerup['x'] - camera_x + 8, powerup['y'] + 16 + y_offset, 16, 8))

    def _render_goal(self, screen, camera_x: float):
        """Render level goal"""
        if self.goal_sprite:
            screen.blit(self.goal_sprite, (self.goal_pos[0] - camera_x, self.goal_pos[1]))
        else:
            # Draw goal as flag
            pygame.draw.rect(screen, (255, 0, 0), (self.goal_pos[0] - camera_x, self.goal_pos[1], 32, 64))
            pygame.draw.polygon(screen, (255, 255, 0),
                              [(self.goal_pos[0] - camera_x + 32, self.goal_pos[1]),
                               (self.goal_pos[0] - camera_x + 32, self.goal_pos[1] + 32),
                               (self.goal_pos[0] - camera_x + 48, self.goal_pos[1] + 16)])

    def get_collidable_tiles(self):
        """Get list of collidable tile rectangles"""
        if self._collidable_cache is None:
            collidable = []
            for y in range(self.LEVEL_HEIGHT):
                for x in range(self.LEVEL_WIDTH):
                    if self.tiles[y][x] > 0:  # Any non-empty tile is collidable
                        rect = pygame.Rect(x * self.TILE_SIZE, y * self.TILE_SIZE,
                                         self.TILE_SIZE, self.TILE_SIZE)
                        collidable.append(rect)
            self._collidable_cache = collidable
        return self._collidable_cache

    def check_coin_collisions(self, player):
        """Check for coin collection"""
        player_rect = player.get_rect()
        collected_coins = []

        for i, (coin_x, coin_y) in enumerate(self.coins):
            coin_rect = pygame.Rect(coin_x, coin_y, 32, 32)
            if player_rect.colliderect(coin_rect):
                collected_coins.append(self.coins[i])

        # Remove collected coins
        for coin in collected_coins:
            self.coins.remove(coin)

        return collected_coins

    def check_enemy_collisions(self, player):
        """Check for enemy collisions"""
        player_rect = player.get_rect()
        _, vy = player.velocity
        hit_player = False
        stomped_count = 0
        defeated = []

        for enemy in self.enemies:
            enemy_rect = pygame.Rect(enemy['x'], enemy['y'], 32, 32)
            if not player_rect.colliderect(enemy_rect):
                continue

            top_overlap = player_rect.bottom - enemy_rect.top
            if vy > 0 and 0 <= top_overlap <= 24:
                stomped_count += 1
                defeated.append(enemy)
            else:
                hit_player = True

        for enemy in defeated:
            try:
                self.enemies.remove(enemy)
            except ValueError:
                pass

        return hit_player, stomped_count

    def check_powerup_collisions(self, player):
        """Check for powerup collection"""
        player_rect = player.get_rect()
        collected_powerups = []

        for i, powerup in enumerate(self.powerups):
            powerup_rect = pygame.Rect(powerup['x'], powerup['y'], 32, 32)
            if player_rect.colliderect(powerup_rect):
                collected_powerups.append(self.powerups[i])

        # Remove collected powerups
        for powerup in collected_powerups:
            self.powerups.remove(powerup)

        return collected_powerups

    def is_completed(self):
        """Check if level is completed"""
        # Completion is checked in Game via goal collision
        return False

    def get_goal_rect(self):
        """Get goal rectangle"""
        return pygame.Rect(self.goal_pos[0], self.goal_pos[1], 32, 64)

    def to_dict(self) -> dict:
        return {
            "tiles": self.tiles,
            "coins": self.coins,
            "enemies": self.enemies,
            "powerups": self.powerups,
            "player_start": list(self.player_start_pos),
            "goal": list(self.goal_pos),
        }

    @staticmethod
    def generate_and_save_levels(count: int, out_dir: str | Path):
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for i in range(1, count + 1):
            lvl = Level.__new__(Level)
            # minimal init
            lvl.level_num = i
            lvl.assets_dir = Path(__file__).resolve().parent.parent / "assets"
            lvl.width = Level.LEVEL_WIDTH * Level.TILE_SIZE
            lvl.height = Level.LEVEL_HEIGHT * Level.TILE_SIZE
            lvl.coins = []
            lvl.enemies = []
            lvl.powerups = []
            lvl.player_start_pos = (100, 500)
            lvl.goal_pos = (lvl.width - 100, 400)
            # generate
            Level._generate_level(lvl)
            # save
            with open(out / f"level_{i}.json", "w", encoding="utf-8") as f:
                json.dump(lvl.to_dict(), f, ensure_ascii=False, indent=2)
