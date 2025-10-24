"""HUD rendering for Delta Operation.

This implementation replaces the legacy HUD module that contained
stale attributes and null-byte artifacts. It integrates the
cross-platform FontManager so that Chinese glyphs render correctly,
and it aligns with the current Player/Mission APIs.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pygame

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gamecenter.deltaOperation.utils.font import FontManager


Color = Tuple[int, int, int]


@dataclass
class HudMessage:
    """Transient on-screen prompt."""

    text: str
    time_left: float
    color: Color


class HUD:
    """Heads-up display with player stats, mission info and minimap.
    
    Optimized layout philosophy:
    - Top bar: Horizontal single-line display (HP | Ammo | Score | Mission | Timer)
    - Right sidebar: Compact minimap (100x100) + objectives (auto-height)
    - Bottom: Weapon details panel (only when switching/reloading)
    - Messages: Centered mid-screen notifications
    - Maximized viewport: HUD elements use ~12% screen real estate
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        if not pygame.font.get_init():
            pygame.font.init()

        self.screen_width = screen_width
        self.screen_height = screen_height

        self._font_manager = FontManager()
        self._font_large = self._font_manager.get_font(28, bold=True)  # Reduced from 36
        self._font_medium = self._font_manager.get_font(20, bold=True)  # Reduced from 26
        self._font_small = self._font_manager.get_font(16)  # Reduced from 18

        # Top bar configuration (single-line layout)
        self.top_bar_height = 42  # Compact height
        self.padding = 8  # Reduced from 16
        self.health_bar_width = 120  # Reduced from 200
        self.health_bar_height = 14  # Reduced from 20
        
        # Right sidebar configuration
        self.minimap_size = 100  # Reduced from 150
        self.minimap_pos = (
            self.screen_width - self.minimap_size - self.padding,
            self.top_bar_height + self.padding * 2,  # Below top bar
        )

        # UI state
        self.show_minimap = True
        self.show_weapon_details = False  # Only show when relevant
        self.weapon_details_timer = 0.0
        self.weapon_details_duration = 2.0  # Auto-hide after 2s
        self.message_duration = 3.0
        self.messages: List[HudMessage] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render(self, surface: pygame.Surface, player, mission, level_manager) -> None:
        if surface is None or player is None:
            return

        # Top bar: unified single-line display (HP | Ammo | Score | Timer)
        self._render_top_bar(surface, player, mission)

        # Right sidebar: minimap + objectives (compact vertical stack)
        if self.show_minimap and level_manager is not None:
            self._render_minimap(surface, player, level_manager)
        
        if mission is not None:
            self._render_mission_panel(surface, mission)

        # Bottom: weapon details (only when switching/reloading)
        if self.show_weapon_details:
            self._render_weapon_details(surface, player)

        # Messages: centered mid-screen
        self._render_messages(surface)

    def update(self, delta_time: float) -> None:
        # Update messages
        if self.messages:
            updated: List[HudMessage] = []
            for message in self.messages:
                remaining = message.time_left - delta_time
                if remaining > 0:
                    updated.append(HudMessage(message.text, remaining, message.color))
            self.messages = updated
        
        # Auto-hide weapon details after timeout
        if self.show_weapon_details:
            self.weapon_details_timer -= delta_time
            if self.weapon_details_timer <= 0:
                self.show_weapon_details = False

    def show_message(self, text: str, color: Color = (255, 255, 255), duration: Optional[float] = None) -> None:
        lifespan = duration if duration is not None else self.message_duration
        self.messages.append(HudMessage(text, lifespan, color))

    def show_checkpoint_activated(self, checkpoint_id: int) -> None:
        self.show_message(f"检查点 #{checkpoint_id} 已激活", (0, 220, 0))

    def show_objective_completed(self, objective_text: str) -> None:
        self.show_message(f"✓ {objective_text}", (255, 220, 0))

    def show_mission_completed(self) -> None:
        self.show_message("任务完成!", (0, 230, 0), duration=5.0)

    def show_mission_failed(self, reason: str) -> None:
        message = f"任务失败: {reason}" if reason else "任务失败"
        self.show_message(message, (255, 80, 80), duration=5.0)

    def on_weapon_switch(self) -> None:
        """Show weapon details for 2 seconds after switching."""
        self.show_weapon_details = True
        self.weapon_details_timer = self.weapon_details_duration

    def on_reload_start(self) -> None:
        """Show weapon details during reload."""
        self.show_weapon_details = True
        self.weapon_details_timer = self.weapon_details_duration

    def toggle_minimap(self) -> None:
        self.show_minimap = not self.show_minimap

    # ------------------------------------------------------------------
    # Rendering primitives
    # ------------------------------------------------------------------
    def _draw_panel(self, surface: pygame.Surface, rect: pygame.Rect, alpha: int = 170) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, alpha))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=8)

    def _render_top_bar(self, surface: pygame.Surface, player, mission) -> None:
        """Unified top bar with HP | Ammo | Score | Timer in single horizontal line."""
        bar_rect = pygame.Rect(0, 0, self.screen_width, self.top_bar_height)
        panel = pygame.Surface(bar_rect.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        surface.blit(panel, bar_rect.topleft)
        pygame.draw.line(surface, (80, 80, 100), (0, self.top_bar_height), 
                        (self.screen_width, self.top_bar_height), 2)

        x_offset = self.padding

        # 1. HP bar (compact inline)
        max_health = getattr(player, "max_health", 0) or getattr(player, "health", 0)
        health = max(0, getattr(player, "health", 0))
        ratio = 0 if max_health == 0 else max(0.0, min(1.0, health / max_health))

        hp_label = self._font_small.render("HP", True, (200, 200, 200))
        surface.blit(hp_label, (x_offset, (self.top_bar_height - hp_label.get_height()) // 2))
        x_offset += hp_label.get_width() + 6

        bar_y = (self.top_bar_height - self.health_bar_height) // 2
        bg_rect = pygame.Rect(x_offset, bar_y, self.health_bar_width, self.health_bar_height)
        pygame.draw.rect(surface, (40, 40, 40), bg_rect, border_radius=4)

        fg_width = int(self.health_bar_width * ratio)
        color = (0, 200, 90) if ratio >= 0.6 else (240, 210, 60) if ratio >= 0.3 else (220, 70, 70)
        fg_rect = pygame.Rect(x_offset, bar_y, fg_width, self.health_bar_height)
        pygame.draw.rect(surface, color, fg_rect, border_radius=4)
        pygame.draw.rect(surface, (180, 180, 180), bg_rect, 1, border_radius=4)

        hp_text = self._font_small.render(f"{int(health)}/{int(max_health)}", True, (255, 255, 255))
        surface.blit(hp_text, (x_offset + self.health_bar_width + 6, bar_y - 1))
        x_offset += self.health_bar_width + hp_text.get_width() + 24

        # 2. Ammo indicator (icon + numbers)
        weapon = getattr(player, "current_weapon", None) or getattr(player, "weapon", None)
        if weapon is not None:
            current_ammo = getattr(weapon, "current_ammo", getattr(weapon, "ammo_in_mag", 0))
            reserve_ammo = getattr(weapon, "reserve_ammo", 0)
            magazine = getattr(weapon, "magazine_size", 1)
            
            ammo_label = self._font_small.render("弹药", True, (200, 200, 200))
            surface.blit(ammo_label, (x_offset, (self.top_bar_height - ammo_label.get_height()) // 2))
            x_offset += ammo_label.get_width() + 6

            if current_ammo == 0:
                ammo_color = (255, 90, 90)
            elif current_ammo <= max(1, magazine // 3):
                ammo_color = (240, 210, 60)
            else:
                ammo_color = (255, 255, 255)

            ammo_text = self._font_medium.render(f"{current_ammo}/{reserve_ammo}", True, ammo_color)
            surface.blit(ammo_text, (x_offset, (self.top_bar_height - ammo_text.get_height()) // 2))
            x_offset += ammo_text.get_width() + 24

            if getattr(weapon, "is_reloading", False):
                reload_text = self._font_small.render("[装填中]", True, (255, 220, 0))
                surface.blit(reload_text, (x_offset, (self.top_bar_height - reload_text.get_height()) // 2))
                x_offset += reload_text.get_width() + 16

        # 3. Kill count / Score
        if mission is not None:
            kills = getattr(mission, "enemies_killed", 0)
            score_label = self._font_small.render("击杀", True, (200, 200, 200))
            surface.blit(score_label, (x_offset, (self.top_bar_height - score_label.get_height()) // 2))
            x_offset += score_label.get_width() + 6

            score_text = self._font_medium.render(str(kills), True, (255, 220, 100))
            surface.blit(score_text, (x_offset, (self.top_bar_height - score_text.get_height()) // 2))
            x_offset += score_text.get_width() + 24

        # 4. Mission timer (right-aligned)
        if mission is not None:
            remaining = mission.get_time_remaining()
            if remaining not in (None, 0):
                minutes = remaining // 60
                seconds = remaining % 60
                color = (255, 90, 90) if remaining <= 30 else (255, 255, 255)
                timer_text = self._font_medium.render(f"{minutes:02d}:{seconds:02d}", True, color)
                
                timer_x = self.screen_width - timer_text.get_width() - self.padding
                surface.blit(timer_text, (timer_x, (self.top_bar_height - timer_text.get_height()) // 2))

    def _render_weapon_details(self, surface: pygame.Surface, player) -> None:
        """Bottom weapon details panel (only shown when switching/reloading)."""
        weapon = getattr(player, "current_weapon", None) or getattr(player, "weapon", None)
        if weapon is None:
            return

        width = 240
        height = 70
        rect = pygame.Rect(
            (self.screen_width - width) // 2,  # Centered horizontally
            self.screen_height - height - self.padding,
            width,
            height
        )
        
        # Semi-transparent panel with fade-out effect
        alpha = int(170 * min(1.0, self.weapon_details_timer / 0.5))  # Fade in last 0.5s
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, alpha))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, (255, 255, 255, alpha), rect, 2, border_radius=8)

        name = getattr(weapon, "name", "Weapon")
        name_text = self._font_medium.render(name, True, (255, 255, 255))
        name_text.set_alpha(alpha)
        surface.blit(name_text, (rect.x + 12, rect.y + 8))

        current_ammo = getattr(weapon, "current_ammo", getattr(weapon, "ammo_in_mag", 0))
        reserve_ammo = getattr(weapon, "reserve_ammo", 0)
        ammo_text = self._font_small.render(f"弹药: {current_ammo} / 备弹: {reserve_ammo}", True, (200, 200, 200))
        ammo_text.set_alpha(alpha)
        surface.blit(ammo_text, (rect.x + 12, rect.y + 36))

    def _render_minimap(self, surface: pygame.Surface, player, level_manager) -> None:
        """Compact minimap in right sidebar below top bar."""
        bounds = getattr(level_manager, "level_bounds", None)
        if bounds is None or bounds.width <= 0 or bounds.height <= 0:
            return

        rect = pygame.Rect(self.minimap_pos, (self.minimap_size, self.minimap_size))
        self._draw_panel(surface, rect, alpha=190)

        inset = 8  # Reduced from 12
        scale = min(
            (rect.width - inset * 2) / bounds.width,
            (rect.height - inset * 2) / bounds.height,
        )

        level_rect = pygame.Rect(0, 0, int(bounds.width * scale), int(bounds.height * scale))
        level_rect.center = rect.center
        pygame.draw.rect(surface, (50, 50, 60), level_rect, border_radius=3)
        pygame.draw.rect(surface, (120, 120, 140), level_rect, 1, border_radius=3)

        def project(world_pos: Tuple[float, float]) -> Tuple[int, int]:
            return (
                level_rect.x + int(world_pos[0] * scale),
                level_rect.y + int(world_pos[1] * scale),
            )

        # Player position
        player_pos = project((player.position.x, player.position.y))
        pygame.draw.circle(surface, (0, 255, 0), player_pos, 3)  # Reduced from 4

        # Enemies
        for enemy in level_manager.get_alive_enemies():
            enemy_pos = project((enemy.position.x, enemy.position.y))
            pygame.draw.circle(surface, (255, 90, 90), enemy_pos, 2)  # Reduced from 3

        # Checkpoints
        for checkpoint in getattr(level_manager, "checkpoints", []):
            cp_pos = project(checkpoint.position)
            color = (0, 220, 0) if checkpoint.activated else (240, 220, 60)
            pygame.draw.circle(surface, color, cp_pos, 2)  # Reduced from 3

        # Extraction point
        extraction = getattr(level_manager, "extraction_point", None)
        if extraction:
            ex_pos = project(extraction)
            pygame.draw.circle(surface, (0, 220, 220), ex_pos, 3)  # Reduced from 4

    def _render_mission_panel(self, surface: pygame.Surface, mission) -> None:
        """Compact mission objectives panel in right sidebar below minimap."""
        objectives = getattr(mission.config, "objectives", None)
        if not objectives:
            return

        width = self.minimap_size  # Match minimap width
        base_height = 60
        line_height = self._font_small.get_linesize() + 4  # Reduced from +6
        content_height = len(objectives) * line_height + 20
        height = min(base_height + content_height, self.screen_height - self.minimap_pos[1] - self.minimap_size - 32)
        
        rect = pygame.Rect(
            self.screen_width - width - self.padding,
            self.minimap_pos[1] + self.minimap_size + self.padding,
            width,
            height,
        )
        self._draw_panel(surface, rect, alpha=190)

        title = self._font_medium.render("任务", True, (255, 235, 120))
        surface.blit(title, (rect.x + 8, rect.y + 6))

        y = rect.y + 32
        for objective in objectives:
            if y + line_height > rect.bottom - 8:
                break  # Prevent overflow
            
            status = "✓" if objective.completed else "○"
            desc = objective.description[:18] + "..." if len(objective.description) > 20 else objective.description  # Truncate long text
            text_color = (0, 210, 0) if objective.completed else (220, 220, 220)
            if objective.optional and not objective.completed:
                text_color = (140, 140, 140)
            
            line = self._font_small.render(f"{status} {desc}", True, text_color)
            surface.blit(line, (rect.x + 8, y))
            y += line_height

        # Completion percentage at bottom
        completion = mission.get_completion_percentage()
        completion_surface = self._font_small.render(
            f"{completion:.0f}%", True, (180, 180, 180)
        )
        surface.blit(
            completion_surface,
            (rect.right - completion_surface.get_width() - 8, rect.bottom - 20),
        )

    def _render_messages(self, surface: pygame.Surface) -> None:
        """Centered mid-screen notification messages."""
        if not self.messages:
            return

        base_y = self.screen_height // 2 - 100  # Mid-screen instead of bottom
        for index, message in enumerate(reversed(self.messages)):
            alpha_ratio = max(0.0, min(1.0, message.time_left / self.message_duration))
            text_surface = self._font_medium.render(message.text, True, message.color)
            text_surface.set_alpha(int(255 * alpha_ratio))
            x = (self.screen_width - text_surface.get_width()) // 2
            y = base_y + index * (text_surface.get_height() + 6)  # Reduced from +8
            
            # Semi-transparent background for better readability
            text_rect = text_surface.get_rect(topleft=(x, y))
            bg_rect = text_rect.inflate(16, 8)
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, int(140 * alpha_ratio)))
            surface.blit(bg_surface, bg_rect.topleft)
            
            surface.blit(text_surface, (x, y))


__all__ = ["HUD"]
