#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Font System
Handles Chinese font loading and rendering for cross-platform support
"""

import pygame
import platform
import os
from pathlib import Path

class FontManager:
    """Manages fonts for the game, with special support for Chinese characters"""

    def __init__(self, assets_dir="assets"):
        """Initialize font manager"""
        self.assets_dir = Path(assets_dir)
        self.fonts_dir = self.assets_dir / "fonts"

        # Font cache
        self.font_cache = {}

        # System info
        self.system = platform.system().lower()

        # Default font sizes
        self.default_sizes = {
            "small": 16,
            "medium": 24,
            "large": 36,
            "title": 48
        }

        # Load fonts
        if not pygame.font.get_init():
            pygame.font.init()
        self._load_fonts()

    def _load_fonts(self):
        """Load available fonts"""
        # Try to load Chinese font first
        chinese_font_path = self._get_chinese_font_path()
        self.chinese_font_path = None

        def _test_font_path(path: Path) -> bool:
            try:
                f = pygame.font.Font(str(path), 18)
                # Render both EN + CN to ensure glyph coverage
                f.render("Test", True, (255, 255, 255))
                f.render("中文测试", True, (255, 255, 255))
                return True
            except Exception as e:
                return False

        tried_paths = []
        if chinese_font_path and chinese_font_path.exists():
            tried_paths.append(chinese_font_path)
            if _test_font_path(chinese_font_path):
                self.chinese_font_path = chinese_font_path
                print(f"Loaded Chinese font: {chinese_font_path.name}")
            else:
                print(f"Failed to use downloaded Chinese font: {chinese_font_path}")

        # If failed, try system fonts by path list and name matching
        if self.chinese_font_path is None:
            # Try platform-specific paths
            for candidate in self._get_system_chinese_font_paths():
                if candidate.exists() and _test_font_path(candidate):
                    self.chinese_font_path = candidate
                    print(f"Loaded system Chinese font: {candidate}")
                    break

        if self.chinese_font_path is None:
            # Try match_font with common CN font names
            for name in self._get_system_chinese_font_names():
                try:
                    matched = pygame.font.match_font(name)
                    if matched and _test_font_path(Path(matched)):
                        self.chinese_font_path = Path(matched)
                        print(f"Loaded matched Chinese font: {name} -> {matched}")
                        break
                except Exception:
                    continue

        if self.chinese_font_path is None:
            print("Chinese font not available, will use fallback fonts")

        # Load fallback fonts
        self._load_fallback_fonts()

    def _get_chinese_font_path(self):
        """Get the path to Chinese font based on platform"""
        # First try our downloaded font
        downloaded_font = self.fonts_dir / "chinese_font.otf"
        if downloaded_font.exists():
            return downloaded_font

        # Also try the Noto font name
        noto_font = self.fonts_dir / "NotoSansCJKsc-Regular.otf"
        if noto_font.exists():
            return noto_font

        # Platform-specific system fonts
        if self.system == "windows":
            # Windows common Chinese fonts
            system_fonts = [
                "C:\\Windows\\Fonts\\msyh.ttc",
                "C:\\Windows\\Fonts\\msyhbd.ttc",
                "C:\\Windows\\Fonts\\simhei.ttf",
                "C:\\Windows\\Fonts\\simsun.ttc",
                "C:\\Windows\\Fonts\\SourceHanSansSC-Regular.otf",
            ]
        elif self.system == "darwin":  # macOS
            # macOS Chinese fonts
            system_fonts = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/Library/Fonts/Microsoft/Simplified Chinese/Microsoft YaHei.ttf",
                "/Library/Fonts/Arial Unicode.ttf",
                "/System/Library/Fonts/Supplemental/Songti.ttc",
            ]
        else:  # Linux and others
            # Linux common Chinese fonts
            system_fonts = [
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
            ]

        # Try each system font
        for font_path in system_fonts:
            if os.path.exists(font_path):
                return Path(font_path)

        return None

    def _get_system_chinese_font_paths(self):
        """Return a list of likely system Chinese font paths as Path objects"""
        paths = []
        base_path = self._get_chinese_font_path()
        # Collect platform-specific candidates
        if self.system == "windows":
            cands = [
                "C:\\Windows\\Fonts\\msyh.ttc",
                "C:\\Windows\\Fonts\\msyhbd.ttc",
                "C:\\Windows\\Fonts\\simhei.ttf",
                "C:\\Windows\\Fonts\\simsun.ttc",
            ]
        elif self.system == "darwin":
            cands = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ]
        else:
            cands = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
            ]
        for p in cands:
            if os.path.exists(p):
                paths.append(Path(p))
        return paths

    def _get_system_chinese_font_names(self):
        """Return common Chinese font family names for SysFont/match_font"""
        return [
            "Microsoft YaHei", "微软雅黑", "SimSun", "宋体", "SimHei", "黑体",
            "PingFang SC", "苹方", "STHeiti", "Heiti SC", "Heiti TC",
            "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei"
        ]

    def _load_fallback_fonts(self):
        """Load fallback fonts for different languages"""
        self.fallback_fonts = []

        # English fonts (always available)
        try:
            self.fallback_fonts.append(pygame.font.SysFont("arial", 12))
            self.fallback_fonts.append(pygame.font.SysFont("verdana", 12))
            self.fallback_fonts.append(pygame.font.SysFont("times", 12))
        except:
            pass

        # System default font
        try:
            self.fallback_fonts.append(pygame.font.Font(None, 12))
        except:
            pass

    def get_font(self, size_name="medium", language="chinese"):
        """Get a font object for the specified size and language"""
        size = self.default_sizes.get(size_name, 24)
        cache_key = f"{language}_{size_name}_{size}"

        if cache_key in self.font_cache:
            return self.font_cache[cache_key]

        font = None

        if language == "chinese" and self.chinese_font_path:
            try:
                font = pygame.font.Font(str(self.chinese_font_path), size)
            except Exception as e:
                print(f"Failed to create Chinese font: {e}")

        # Fallback to system fonts
        if font is None:
            # Try Chinese names via SysFont first
            for name in self._get_system_chinese_font_names():
                try:
                    font = pygame.font.SysFont(name, size)
                    # Quick test to ensure Chinese renders
                    font.render("中文", True, (255, 255, 255))
                    break
                except Exception:
                    font = None
                    continue
            # Then generic fallbacks
            if font is None:
                for fallback_font in self.fallback_fonts:
                    try:
                        if hasattr(fallback_font, 'name') and fallback_font.name:
                            font = pygame.font.Font(fallback_font.name, size)
                        else:
                            font = fallback_font
                        break
                    except Exception:
                        continue

        # Last resort: default font
        if font is None:
            try:
                font = pygame.font.Font(None, size)
            except:
                # Ultimate fallback
                font = pygame.font.SysFont("monospace", size)

        self.font_cache[cache_key] = font
        return font

    def render_text(self, text, size_name="medium", color=(255, 255, 255), language="chinese", shadow=True, outline=True):
        """Render text with optional shadow and outline for better UI"""
        font = self.get_font(size_name, language)
        base_surface = font.render(text, True, color)
        if not shadow and not outline:
            return base_surface

        # Shadow effect
        shadow_offset = 2
        shadow_color = (0, 0, 0, 180)
        outline_color = (0, 0, 0)
        outline_offset = 1
        w, h = base_surface.get_size()
        surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        # Draw shadow
        if shadow:
            shadow_surf = font.render(text, True, shadow_color)
            surf.blit(shadow_surf, (shadow_offset + 2, shadow_offset + 2))
        # Draw outline
        if outline:
            for dx in [-outline_offset, 0, outline_offset]:
                for dy in [-outline_offset, 0, outline_offset]:
                    if dx == 0 and dy == 0:
                        continue
                    outline_surf = font.render(text, True, outline_color)
                    surf.blit(outline_surf, (dx + 2, dy + 2))
        # Draw main text
        surf.blit(base_surface, (2, 2))
        return surf

    def render_multiline_text(self, text, size_name="medium", color=(255, 255, 255),
                            language="chinese", line_spacing=5):
        """Render multiline text"""
        lines = text.split('\n')
        font = self.get_font(size_name, language)
        line_height = font.get_height() + line_spacing

        surfaces = []
        total_height = 0

        for line in lines:
            surface = font.render(line, True, color)
            surfaces.append(surface)
            total_height += line_height

        # Create combined surface
        if surfaces:
            max_width = max(surface.get_width() for surface in surfaces)
            combined_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)

            y_offset = 0
            for surface in surfaces:
                combined_surface.blit(surface, (0, y_offset))
                y_offset += line_height

            return combined_surface

        return None

    def get_text_size(self, text, size_name="medium", language="chinese"):
        """Get the size of rendered text"""
        font = self.get_font(size_name, language)
        return font.size(text)

    def get_font_height(self, size_name="medium", language="chinese"):
        """Get font height"""
        font = self.get_font(size_name, language)
        return font.get_height()

    def create_text_button(self, text, size_name="medium", color=(255, 255, 255),
                          hover_color=(255, 255, 0), language="chinese"):
        """Create a text button with hover effect"""
        normal_surface = self.render_text(text, size_name, color, language)
        hover_surface = self.render_text(text, size_name, hover_color, language)

        return {
            "normal": normal_surface,
            "hover": hover_surface,
            "rect": normal_surface.get_rect() if normal_surface else None
        }

class TextRenderer:
    """High-level text rendering utility"""

    def __init__(self, font_manager):
        """Initialize text renderer"""
        self.font_manager = font_manager

    def draw_text(self, screen, text, position, size_name="medium",
                  color=(255, 255, 255), language="chinese", centered=False, shadow=True, outline=True):
        """Draw text on screen with shadow/outline"""
        surface = self.font_manager.render_text(text, size_name, color, language, shadow=shadow, outline=outline)
        if surface:
            if centered:
                rect = surface.get_rect(center=position)
                screen.blit(surface, rect)
            else:
                screen.blit(surface, position)

    def draw_multiline_text(self, screen, text, position, size_name="medium",
                           color=(255, 255, 255), language="chinese", centered=False, shadow=True, outline=True):
        """Draw multiline text on screen with shadow/outline"""
        # Render each line with shadow/outline
        lines = text.split('\n')
        y = position[1]
        for line in lines:
            surf = self.font_manager.render_text(line, size_name, color, language, shadow=shadow, outline=outline)
            if centered:
                rect = surf.get_rect(center=(position[0], y + surf.get_height() // 2))
                screen.blit(surf, rect)
            else:
                screen.blit(surf, (position[0], y))
            y += surf.get_height() + 5

    def draw_button(self, screen, button, position, mouse_pos):
        """Draw a text button with hover effect"""
        rect = button["rect"].copy()
        rect.topleft = position

        if rect.collidepoint(mouse_pos):
            surface = button["hover"]
        else:
            surface = button["normal"]

        screen.blit(surface, position)
        return rect

# Global font manager instance
_font_manager = None

def get_font_manager(assets_dir="assets"):
    """Get the global font manager instance"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager(assets_dir)
    return _font_manager

def get_text_renderer(assets_dir="assets"):
    """Get a text renderer instance"""
    font_manager = get_font_manager(assets_dir)
    return TextRenderer(font_manager)