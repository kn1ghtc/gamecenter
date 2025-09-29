from __future__ import annotations

"""User interface helpers for the StreetBattle 2.5D mode."""

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - optional during import
    import pygame
except ImportError:  # pragma: no cover
    pygame = None  # type: ignore


if TYPE_CHECKING:  # pragma: no cover - hints only
    from .fighter import Fighter


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class UITheme:
    name: str
    background_top: Color
    background_bottom: Color
    floor: Color
    panel: Color
    panel_outline: Color
    accent: Color
    text_primary: Color
    text_secondary: Color
    timer_background: Tuple[int, int, int, int]


THEMES: Dict[str, UITheme] = {
    "arena": UITheme(
        name="arena",
        background_top=(18, 24, 36),
        background_bottom=(12, 14, 24),
        floor=(40, 52, 78),
        panel=(28, 34, 52),
        panel_outline=(76, 96, 140),
        accent=(189, 68, 95),
        text_primary=(236, 240, 255),
        text_secondary=(160, 176, 210),
        timer_background=(14, 18, 32, 230),
    ),
    "neon": UITheme(
        name="neon",
        background_top=(18, 6, 36),
        background_bottom=(6, 4, 18),
        floor=(52, 24, 72),
        panel=(32, 16, 48),
        panel_outline=(120, 64, 180),
        accent=(255, 110, 190),
        text_primary=(244, 244, 252),
        text_secondary=(190, 168, 220),
        timer_background=(35, 10, 50, 220),
    ),
}
FONT_CANDIDATES: Tuple[str, ...] = (
    "noto sans cjk sc",
    "noto sans sc",
    "source han sans cn",
    "source han sans sc",
    "microsoft yahei ui",
    "microsoft yahei",
    "pingfang sc",
    "hiragino sans gb",
    "simhei",
    "arial unicode ms",
    "segoe ui",
    "dejavu sans",
)


class _FontManager:
    def __init__(self) -> None:
        self._cache: Dict[Tuple[int, bool], Any] = {}
        if pygame is not None:
            try:
                pygame.font.init()
            except Exception:  # pragma: no cover - defensive fallback
                pass

    def get(self, size: int, bold: bool = False) -> Any:
        key = (size, bold)
        if key in self._cache:
            return self._cache[key]
        if pygame is None:
            self._cache[key] = None
            return None
        font_obj: Any = None
        for candidate in FONT_CANDIDATES:
            try:
                matched = pygame.font.match_font(candidate, bold=bold)
            except Exception:
                matched = None
            if matched:
                try:
                    font_obj = pygame.font.Font(matched, size)
                    break
                except Exception:
                    font_obj = None
        if font_obj is None:
            try:
                font_obj = pygame.font.SysFont("sansserif", size, bold=bold)
            except Exception:
                font_obj = None
        if font_obj is None:
            font_obj = pygame.font.Font(None, size)
        self._cache[key] = font_obj
        return font_obj


_FONT_MANAGER = _FontManager()


def _load_font(size: int, bold: bool = False) -> Any:
    return _FONT_MANAGER.get(size, bold=bold)


class HudRenderer:
    """Draws the battle HUD, timer, and overlays."""

    def __init__(self, width: int, height: int, floor_y: int, theme_name: str = "arena") -> None:
        if pygame is None:
            raise RuntimeError("HudRenderer requires pygame to be installed")
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.theme = THEMES.get(theme_name, THEMES["arena"])
        self.background = self._build_background()
        self.health_font = _load_font(24, bold=True)
        self.timer_font = _load_font(64, bold=True)
        self.skill_font = _load_font(20)
        self.message_font = _load_font(34, bold=True)
        self.small_font = _load_font(18)

    def _build_background(self) -> Any:
        surface = pygame.Surface((self.width, self.height))
        gradient = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(self.theme.background_top[0] * (1 - t) + self.theme.background_bottom[0] * t),
                int(self.theme.background_top[1] * (1 - t) + self.theme.background_bottom[1] * t),
                int(self.theme.background_top[2] * (1 - t) + self.theme.background_bottom[2] * t),
            )
            pygame.draw.line(gradient, color, (0, y), (self.width, y))
        surface.blit(gradient, (0, 0))
        pygame.draw.rect(surface, self.theme.floor, (0, self.floor_y, self.width, self.height - self.floor_y))
        stripe_color = tuple(min(255, c + 14) for c in self.theme.background_top)
        for x in range(-80, self.width + 160, 120):
            pygame.draw.line(surface, stripe_color, (x, self.floor_y), (x + 120, self.height), 2)
        glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.circle(glow, (self.theme.accent[0], self.theme.accent[1], self.theme.accent[2], 60), (self.width // 2, self.floor_y), self.width // 2)
        surface.blit(glow, (0, 0))
        return surface

    def draw_background(self, screen: Any, offset: Tuple[int, int] = (0, 0)) -> None:
        screen.blit(self.background, offset)

    def draw(
        self,
        screen: Any,
        *,
        player: Fighter,
        cpu: Fighter,
        time_remaining: float,
        match_over: bool,
        winner: Optional[str],
        sprite_sources: Dict[str, str],
        help_overlay: Iterable[str],
        show_help: bool,
        help_hint: str,
        banner_text: Optional[str] = None,
    ) -> None:
        self._draw_health_bar(screen, player, (80, 50), (230, 110, 120))
        self._draw_health_bar(screen, cpu, (self.width - 80 - 360, 50), (110, 180, 240))
        self._draw_timer(screen, time_remaining)
        self._draw_skill(screen, player, (80, 108))
        self._draw_skill(screen, cpu, (self.width - 80, 108), align_right=True)
        if banner_text:
            self._draw_banner(screen, banner_text)
        if show_help:
            self._draw_help_overlay(screen, help_overlay, sprite_sources)
        else:
            self._draw_help_hint(screen, help_hint)
        if match_over:
            self._draw_match_result(screen, winner)

    def _draw_health_bar(self, screen: Any, fighter: Fighter, position: Tuple[int, int], color: Color) -> None:
        x, y = position
        width, height = 360, 26
        ratio = max(0.0, min(1.0, fighter.health / max(1, fighter.max_health)))
        pygame.draw.rect(screen, self.theme.panel_outline, (x - 2, y - 2, width + 4, height + 4), border_radius=10)
        pygame.draw.rect(screen, self.theme.panel, (x, y, width, height), border_radius=10)
        if ratio > 0:
            pygame.draw.rect(screen, color, (x + 3, y + 3, int((width - 6) * ratio), height - 6), border_radius=8)
        name_label = self.health_font.render(fighter.name, True, self.theme.text_primary)
        txt_rect = name_label.get_rect()
        txt_rect.midleft = (x, y - 18)
        screen.blit(name_label, txt_rect)
        health_label = self.health_font.render(f"HP {fighter.health:03d}", True, self.theme.text_secondary)
        hp_rect = health_label.get_rect()
        hp_rect.midright = (x + width, y - 18)
        screen.blit(health_label, hp_rect)

    def _draw_timer(self, screen: Any, time_remaining: float) -> None:
        clamped_time = max(0.0, time_remaining)
        minutes = int(clamped_time // 60)
        seconds = int(clamped_time % 60)
        pulse = 1.0
        if clamped_time <= 10:
            blink = (math.sin(pygame.time.get_ticks() / 160) + 1.2) / 2.2
            pulse = max(0.5, min(1.0, blink))
        color = (
            int(self.theme.accent[0] * pulse + self.theme.text_primary[0] * (1 - pulse)),
            int(self.theme.accent[1] * pulse + self.theme.text_primary[1] * (1 - pulse)),
            int(self.theme.accent[2] * pulse + self.theme.text_primary[2] * (1 - pulse)),
        )
        label = self.timer_font.render(f"{minutes:02d}:{seconds:02d}", True, color)
        rect = label.get_rect(center=(self.width // 2, 72))
        backdrop = pygame.Surface(rect.inflate(80, 28).size, pygame.SRCALPHA)
        backdrop.fill(self.theme.timer_background)
        screen.blit(backdrop, rect.inflate(80, 28).topleft)
        screen.blit(label, rect)

    def _draw_skill(self, screen: Any, fighter: Fighter, anchor: Tuple[int, int], align_right: bool = False) -> None:
        if not fighter.active_skill:
            return
        label = self.skill_font.render(fighter.active_skill.name.replace("_", " ").title(), True, self.theme.text_primary)
        rect = label.get_rect()
        if align_right:
            rect.topright = anchor
        else:
            rect.topleft = anchor
        padded = rect.inflate(18, 10)
        pill = pygame.Surface(padded.size, pygame.SRCALPHA)
        pill.fill((self.theme.panel[0], self.theme.panel[1], self.theme.panel[2], 200))
        screen.blit(pill, padded.topleft)
        screen.blit(label, rect)

    def _draw_help_overlay(self, screen: Any, overlay_lines: Iterable[str], sources: Dict[str, str]) -> None:
        lines = [line for line in overlay_lines]
        if sources:
            if lines and lines[-1]:
                lines.append("")
            lines.append("资源版权 / Credits")
            for name, src in sources.items():
                lines.append(f"{name}: {src}")
        if not lines:
            return
        start_y = self.height - 180
        padding = 14
        max_width = 0
        rendered: List[Tuple[Optional[Any], Any]] = []
        for line in lines:
            if not line:
                rect = pygame.Rect(0, 0, 0, 20)
                rect.topleft = (44, start_y)
                rendered.append((None, rect))
                start_y += rect.height
                continue
            label = self.small_font.render(line, True, self.theme.text_secondary)
            rect = label.get_rect()
            rect.topleft = (44, start_y)
            rendered.append((label, rect))
            max_width = max(max_width, rect.width)
            start_y += rect.height + 6
        top_edge = rendered[0][1].top if rendered else self.height - 180
        bottom_edge = rendered[-1][1].bottom if rendered else top_edge + 10
        panel_height = max(40, bottom_edge - top_edge + padding * 2)
        panel_width = max(260, max_width + padding * 2)
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((8, 10, 20, 180))
        screen.blit(panel, (32, top_edge - padding))
        for label, rect in rendered:
            if label is None:
                continue
            screen.blit(label, rect)

    def _draw_help_hint(self, screen: Any, hint: str) -> None:
        if not hint:
            return
        label = self.small_font.render(hint, True, self.theme.text_secondary)
        rect = label.get_rect()
        rect.bottomleft = (34, self.height - 34)
        padded = rect.inflate(16, 10)
        overlay = pygame.Surface(padded.size, pygame.SRCALPHA)
        overlay.fill((10, 12, 22, 150))
        screen.blit(overlay, padded.topleft)
        screen.blit(label, rect)

    def _draw_sources(self, screen: Any, sources: Dict[str, str]) -> None:
        # Retained for compatibility; now invoked via _draw_help_overlay
        self._draw_help_overlay(screen, [], sources)

    def _draw_banner(self, screen: Any, text: str) -> None:
        label = self.message_font.render(text, True, self.theme.text_primary)
        rect = label.get_rect(center=(self.width // 2, int(self.floor_y * 0.35)))
        halo = pygame.Surface(rect.inflate(220, 120).size, pygame.SRCALPHA)
        halo.fill((self.theme.panel[0], self.theme.panel[1], self.theme.panel[2], 200))
        screen.blit(halo, rect.inflate(220, 120).topleft)
        screen.blit(label, rect)

    def _draw_match_result(self, screen: Any, winner: Optional[str]) -> None:
        text = "Time Up!" if not winner else f"{winner} Wins!"
        label = self.message_font.render(text, True, self.theme.text_primary)
        rect = label.get_rect(center=(self.width // 2, self.height // 2 - 40))
        backdrop = pygame.Surface(rect.inflate(160, 80).size, pygame.SRCALPHA)
        backdrop.fill((self.theme.panel[0], self.theme.panel[1], self.theme.panel[2], 220))
        screen.blit(backdrop, rect.inflate(160, 80).topleft)
        screen.blit(label, rect)
        hint = self.small_font.render("Enter: Rematch   Esc: Back to Selection", True, self.theme.text_secondary)
        hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 20))
        screen.blit(hint, hint_rect)


class MatchSetupScreen:
    """Simple keyboard-driven roster picker."""

    def __init__(
        self,
        screen: Any,
        clock: Any,
        roster_map: Dict[str, Dict[str, Any]],
        roster_order: List[str],
        theme_name: str = "arena",
    ) -> None:
        if pygame is None:
            raise RuntimeError("MatchSetupScreen requires pygame to be installed")
        self.screen = screen
        self.clock = clock
        self.roster_map = roster_map
        self.roster_order = roster_order
        self.theme = THEMES.get(theme_name, THEMES["arena"])
        self.title_font = _load_font(46, bold=True)
        self.card_font = _load_font(24, bold=True)
        self.body_font = _load_font(20)
        self.stat_font = _load_font(18)
        self.info_font = _load_font(18)

    def run(self, player_key: str, cpu_key: str) -> Optional[Tuple[str, str]]:
        focus = 0  # 0 = player, 1 = cpu
        selections = [self._validate(player_key) or self.roster_order[0], self._validate(cpu_key) or self._next_alternative(player_key)]
        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE,):
                        return None
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if selections[0] == selections[1]:
                            selections[1] = self._next_alternative(selections[0])
                        return selections[0], selections[1]
                    if event.key in (pygame.K_TAB, pygame.K_UP, pygame.K_DOWN):
                        focus = 1 - focus
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        selections[focus] = self._move_selection(selections[focus], -1)
                        if selections[0] == selections[1]:
                            selections[focus] = self._move_selection(selections[focus], -1)
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        selections[focus] = self._move_selection(selections[focus], 1)
                        if selections[0] == selections[1]:
                            selections[focus] = self._move_selection(selections[focus], 1)
                    if event.key in (pygame.K_r, pygame.K_SPACE):
                        selections[focus] = self._random_choice(exclude=selections[1 - focus])
            self._render(selections, focus)
        # loop never reaches here

    def _validate(self, key: Optional[str]) -> Optional[str]:
        if not key:
            return None
        key = str(key)
        return key if key in self.roster_map else None

    def _move_selection(self, current: str, offset: int) -> str:
        if not self.roster_order:
            return current
        idx = self.roster_order.index(current)
        idx = (idx + offset) % len(self.roster_order)
        return self.roster_order[idx]

    def _next_alternative(self, exclude: str) -> str:
        candidates = [key for key in self.roster_order if key != exclude]
        return candidates[0] if candidates else exclude

    def _random_choice(self, exclude: Optional[str]) -> str:
        pool = [key for key in self.roster_order if key != exclude]
        return random.choice(pool) if pool else self.roster_order[0]

    def _render(self, selections: List[str], focus: int) -> None:
        self.screen.fill((10, 12, 18))
        title = self.title_font.render("选择对战角色", True, self.theme.text_primary)
        self.screen.blit(title, title.get_rect(center=(self.screen.get_width() // 2, 80)))
        spacing = self.screen.get_width() // 3
        base_x = spacing
        for index, key in enumerate(selections):
            entry = self.roster_map.get(key) or {}
            card_rect = pygame.Rect(0, 0, spacing * 0.9, 260)
            card_rect.center = (base_x + index * spacing, self.screen.get_height() // 2)
            self._draw_card(card_rect, entry, focus == index, label="PLAYER 1" if index == 0 else "CPU")
        hint = self.info_font.render("←/→ 切换  |  Enter 确认  |  Tab 切换选择  |  R 随机", True, self.theme.text_secondary)
        hint_rect = hint.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 60))
        self.screen.blit(hint, hint_rect)
        pygame.display.flip()

    def _draw_card(self, rect: Any, entry: Dict[str, Any], focused: bool, label: str) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((self.theme.panel[0], self.theme.panel[1], self.theme.panel[2], 220 if focused else 180))
        pygame.draw.rect(panel, self.theme.panel_outline, panel.get_rect(), 2, border_radius=18)
        self.screen.blit(panel, rect.topleft)
        label_font = self.stat_font.render(label, True, self.theme.text_secondary)
        self.screen.blit(label_font, (rect.x + 18, rect.y + 16))
        name = entry.get("display_name", "Unknown")
        name_label = self.card_font.render(str(name), True, self.theme.text_primary)
        self.screen.blit(name_label, (rect.x + 18, rect.y + 52))
        team = entry.get("team")
        if team:
            team_label = self.body_font.render(str(team), True, self.theme.text_secondary)
            self.screen.blit(team_label, (rect.x + 18, rect.y + 96))
        stats = {
            "Tempo": entry.get("tempo"),
            "Power": entry.get("power"),
            "Technique": entry.get("technique"),
            "Guard": entry.get("guard"),
        }
        bar_width = rect.width - 120
        y = rect.y + 130
        for stat, value in stats.items():
            text = self.stat_font.render(f"{stat}", True, self.theme.text_secondary)
            self.screen.blit(text, (rect.x + 18, y))
            bar_rect = pygame.Rect(rect.x + 120, y + 4, bar_width, 14)
            pygame.draw.rect(self.screen, (26, 30, 44), bar_rect, border_radius=8)
            if value is not None:
                normalized = max(0.0, min(1.0, float(value) / 5.0))
                fill_rect = pygame.Rect(bar_rect.x + 2, bar_rect.y + 2, int((bar_rect.width - 4) * normalized), bar_rect.height - 4)
                pygame.draw.rect(self.screen, self.theme.accent, fill_rect, border_radius=6)
            y += 34


__all__ = ["HudRenderer", "MatchSetupScreen", "UITheme", "THEMES"]
