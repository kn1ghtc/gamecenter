#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Player Class
Handles Mario's movement, physics, and animations
"""

import pygame
from pathlib import Path

class Player:
    """Player character (Mario) class"""

    # Player constants
    SPEED = 200  # pixels per second
    JUMP_FORCE = -400  # negative because y increases downward
    GRAVITY = 800  # pixels per second squared
    MAX_FALL_SPEED = 400

    # Animation constants
    ANIMATION_SPEED = 0.1  # seconds per frame

    def __init__(self, start_pos, assets_dir, config: dict | None = None):
        """Initialize the player"""
        self.assets_dir = Path(assets_dir)
        cfg = config or {}

        # Position and physics
        self.x, self.y = start_pos
        self.start_pos = start_pos
        self.width = 32
        self.height = 32

        # Velocity
        self.vx = 0  # horizontal velocity
        self.vy = 0  # vertical velocity

        # State
        self.on_ground = False
        self.facing_right = True
        self.is_big = False  # Super Mario state

        # Animation
        self.animation_timer = 0
        self.current_frame = 0
        self.animation_state = "idle"  # idle, walking, jumping

        # Input state (avoid name collision with methods)
        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.can_double_jump = bool(cfg.get("skills", {}).get("double_jump", False))
        self.has_dashed = False
        self.enable_dash = bool(cfg.get("skills", {}).get("dash", False))

        # Apply physics config
        try:
            self.SPEED = float(cfg.get("speed", self.SPEED))
            self.JUMP_FORCE = float(cfg.get("jump_force", self.JUMP_FORCE))
            self.GRAVITY = float(cfg.get("gravity", self.GRAVITY))
            self.MAX_FALL_SPEED = float(cfg.get("max_fall_speed", self.MAX_FALL_SPEED))
        except Exception:
            pass

        # Default color for fallback rendering
        self.color = (255, 0, 0)

        # Load sprites
        self._load_sprites()

    def _load_sprites(self):
        """Load player sprites"""
        try:
            # Prefer our generated 3D-style single sprite
            single_sprite = self.assets_dir / "images" / "mario.png"
            if single_sprite.exists():
                self.sprite_image = pygame.image.load(str(single_sprite)).convert_alpha()
                self.sprite_sheet = None
            else:
                # Fallback: try sprite sheet
                sprites_path = self.assets_dir / "images" / "mario_sprites.png"
                if sprites_path.exists():
                    self.sprite_sheet = pygame.image.load(str(sprites_path)).convert_alpha()
                    self.sprite_image = None
                else:
                    # Final fallback: simple colored rectangle
                    self.sprite_sheet = None
                    self.sprite_image = None
                    self.color = (255, 0, 0)  # Red for Mario
        except Exception as e:
            print(f"Failed to load player sprites: {e}")
            self.sprite_sheet = None
            self.sprite_image = None

    def reset(self, position):
        """Reset player to starting position"""
        self.x, self.y = position
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.is_big = False

    def move_left(self):
        """Start moving left"""
        self.left_pressed = True
        self.right_pressed = False
        self.facing_right = False

    def move_right(self):
        """Start moving right"""
        self.right_pressed = True
        self.left_pressed = False
        self.facing_right = True

    def stop_moving(self):
        """Stop horizontal movement"""
        self.left_pressed = False
        self.right_pressed = False
        self.vx = 0
        self.animation_state = "idle"

    def jump(self):
        """Make the player jump"""
        if self.on_ground:
            self.vy = self.JUMP_FORCE
            self.on_ground = False
            self.animation_state = "jumping"
            self.jump_pressed = True
            self.has_dashed = False
        elif self.can_double_jump and self.jump_pressed:
            # perform double jump once per air time
            self.vy = self.JUMP_FORCE * 0.9
            self.jump_pressed = False

    def grow(self):
        """Make Mario grow into Super Mario"""
        if not self.is_big:
            self.is_big = True
            self.height = 64  # Double height
            self.y -= 32  # Adjust position

    def shrink(self):
        """Make Super Mario shrink back to normal"""
        if self.is_big:
            self.is_big = False
            self.height = 32
            self.y += 32

    def update(self, dt, level):
        """Update player physics and animation"""
        # Handle input
        self._handle_input(dt)

        # Apply physics
        self._apply_physics(dt, level)

        # Update animation
        self._update_animation(dt)

        # Check bounds
        self._check_bounds(level)

    def _handle_input(self, dt):
        """Handle player input"""
        # Horizontal movement
        if self.left_pressed:
            self.vx = -self.SPEED
            self.animation_state = "walking"
        elif self.right_pressed:
            self.vx = self.SPEED
            self.animation_state = "walking"
        else:
            self.vx = 0
            self.animation_state = "idle"

        # Dash (simple burst)
        if self.enable_dash and (self.left_pressed or self.right_pressed) and not self.on_ground and not self.has_dashed:
            self.vx *= 1.5
            self.has_dashed = True

    def _apply_physics(self, dt, level):
        """Apply physics to the player"""
        # Apply gravity
        if not self.on_ground:
            self.vy += self.GRAVITY * dt
            if self.vy > self.MAX_FALL_SPEED:
                self.vy = self.MAX_FALL_SPEED

        # Update position
        old_x, old_y = self.x, self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Check collisions with level
        self._check_level_collisions(level, old_x, old_y)

    def _check_level_collisions(self, level, old_x, old_y):
        """Check collisions with level tiles"""
        # Get player rect
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Check collision with ground/platforms
        self.on_ground = False

        # Simple collision detection with level tiles
        tiles = level.get_collidable_tiles()

        for tile_rect in tiles:
            if player_rect.colliderect(tile_rect):
                # Determine collision direction
                dx = (player_rect.centerx - tile_rect.centerx)
                dy = (player_rect.centery - tile_rect.centery)

                if abs(dx) > abs(dy):
                    # Horizontal collision
                    if dx > 0:
                        # Player is to the right of tile
                        self.x = tile_rect.right
                    else:
                        # Player is to the left of tile
                        self.x = tile_rect.left - self.width
                    self.vx = 0
                else:
                    # Vertical collision
                    if dy > 0:
                        # Player is below tile (landing)
                        self.y = tile_rect.top - self.height
                        self.vy = 0
                        self.on_ground = True
                        if self.animation_state == "jumping":
                            self.animation_state = "idle"
                    else:
                        # Player hit tile from below
                        self.y = tile_rect.bottom
                        self.vy = 0

                player_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def _check_bounds(self, level):
        """Check if player is within level bounds"""
        # Prevent going off screen horizontally
        if self.x < 0:
            self.x = 0
            self.vx = 0
        elif self.x > level.width - self.width:
            self.x = level.width - self.width
            self.vx = 0

        # Vertical bounds checking is handled by collision detection
        if self.on_ground:
            self.jump_pressed = False

    def _update_animation(self, dt):
        """Update player animation"""
        self.animation_timer += dt

        if self.animation_timer >= self.ANIMATION_SPEED:
            self.animation_timer = 0

            if self.animation_state == "walking":
                self.current_frame = (self.current_frame + 1) % 3  # 3 walking frames
            elif self.animation_state == "idle":
                self.current_frame = 0
            elif self.animation_state == "jumping":
                self.current_frame = 1  # Jumping frame

    def render(self, screen):
        """Render the player"""
        if getattr(self, 'sprite_image', None):
            # Render using generated sprite image; scale to current size
            try:
                if self.sprite_image.get_width() != self.width or self.sprite_image.get_height() != self.height:
                    img = pygame.transform.smoothscale(self.sprite_image, (int(self.width), int(self.height)))
                else:
                    img = self.sprite_image
                screen.blit(img, (self.x, self.y))
            except Exception:
                color = (0, 255, 0) if self.is_big else getattr(self, 'color', (255, 0, 0))
                pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        elif self.sprite_sheet:
            # Render with sprite sheet (fallback placeholder)
            self._render_with_sprites(screen)
        else:
            # Render as colored rectangle
            color = (0, 255, 0) if self.is_big else self.color  # Green for Super Mario
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))

    def _render_with_sprites(self, screen):
        """Render player using sprite sheet"""
        # This would extract frames from the sprite sheet
        # For now, just render a colored rectangle
        color = (0, 255, 0) if self.is_big else self.color
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))

        # Add simple eyes for Mario
        eye_color = (255, 255, 255)
        eye_size = 4
        if self.facing_right:
            pygame.draw.circle(screen, eye_color, (int(self.x + 20), int(self.y + 10)), eye_size)
            pygame.draw.circle(screen, eye_color, (int(self.x + 12), int(self.y + 10)), eye_size)
        else:
            pygame.draw.circle(screen, eye_color, (int(self.x + 12), int(self.y + 10)), eye_size)
            pygame.draw.circle(screen, eye_color, (int(self.x + 20), int(self.y + 10)), eye_size)

    def get_rect(self):
        """Get player's collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_center(self):
        """Get player's center position"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def position(self):
        """Get current position as tuple"""
        return (self.x, self.y)