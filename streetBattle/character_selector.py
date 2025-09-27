#!/usr/bin/env python3
"""
Character Selection Interface for StreetBattle
Provides character selection with portraits and information
"""

from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenText, DirectScrolledFrame, OnscreenImage
from panda3d.core import TextNode, Vec4, Texture, PNMImage, TransparencyAttrib, Filename, getModelPath
from direct.task import Task
import math
import random
import json
import os

from .portrait_manager import PortraitManager
from .ui_asset_manager import UIAssetManager


class CharacterSelector:
    """Character selection interface"""
    
    def __init__(self, base_app, character_manager):
        self.base_app = base_app
        self.char_manager = character_manager
        self.callback = None
        self.ui_elements = []
        self.selected_character = None
        self.character_buttons = []
        self.character_cards = []
        self.card_lookup = {}
        self.card_portrait_nodes = {}
        self.mode = 'single'  # 'single' or 'versus' (for P1/P2)
        self.player_number = 1
        self.current_selection_index = 0  # For keyboard navigation
        self.all_characters = []  # Store character list for keyboard navigation
        self.assets_root = os.path.join(os.path.dirname(__file__), 'assets')
        self.profile_data = self._load_profile_data()
        self.portrait_cache = {}
        self.visible = False
        self._nav_bindings: set[str] = set()
        self._random_spin_state = None
        self._auto_confirm_task_name = f'auto-confirm-selection-{id(self)}'
        self._random_task_name = f'random-selection-{id(self)}'
        self.card_colors = {
            'default': (0.82, 0.9, 1.0, 0.92),
            'hover': (0.95, 0.98, 1.0, 0.98),
            'selected': (1.0, 0.85, 0.6, 0.98)
        }
        self.grid_cols = 7
        self.fonts = self._load_fonts()
        self.ui_asset_manager = UIAssetManager(
            loader=self.base_app.loader,
            assets_dir=self.assets_root
        )
        self._init_visual_assets()
        self.portrait_manager = PortraitManager(
            loader=self.base_app.loader,
            assets_dir=self.assets_root
        )

    def _load_profile_data(self):
        """Load optional character profile metadata for bios and color schemes."""
        profiles_path = os.path.join(self.assets_root, 'character_profiles.json')
        if os.path.exists(profiles_path):
            try:
                with open(profiles_path, 'r', encoding='utf-8') as fp:
                    return json.load(fp)
            except Exception as exc:
                print(f"Failed to load character profiles: {exc}")
        return {}

    def _canonical_key(self, name):
        """Generate a normalized key for profile lookup (lowercase underscore)."""
        if not name:
            return ''
        cleaned = ''.join(ch if ch.isalnum() else '_' for ch in name.lower())
        while '__' in cleaned:
            cleaned = cleaned.replace('__', '_')
        return cleaned.strip('_')

    def _get_profile(self, character_name):
        key = self._canonical_key(character_name)
        return self.profile_data.get(key, {})

    # ------------------------------------------------------------------
    # visual helpers
    # ------------------------------------------------------------------
    def _load_fonts(self):
        fonts = {}

        def load_font(candidate: str | None):
            if not candidate:
                return None
            filename = Filename(candidate)
            resolved = getModelPath().findFile(filename)
            if not resolved:
                return None
            try:
                return self.base_app.loader.loadFont(resolved)
            except Exception:
                return None

        fonts['heading'] = load_font('cmtt12.egg')
        fonts['body'] = load_font('cmss12.egg')
        fonts['accent'] = load_font('cmr12.egg') or fonts['heading']

        if not any(fonts.values()):
            print("[CharacterSelector] Custom fonts unavailable; falling back to Panda3D defaults")

        return fonts

    def _init_visual_assets(self):
        self.background_texture = self._make_vertical_gradient_texture(
            (0.04, 0.05, 0.11, 0.98),
            (0.02, 0.03, 0.07, 0.98)
        )
        self.info_panel_texture = self._make_vertical_gradient_texture(
            (0.10, 0.12, 0.20, 0.96),
            (0.05, 0.06, 0.13, 0.93)
        )
        self.grid_texture = self._make_vertical_gradient_texture(
            (0.07, 0.09, 0.16, 0.88),
            (0.04, 0.05, 0.11, 0.88)
        )
        fallback_gradients = {
            'default': self._make_rounded_card_texture((0.22, 0.26, 0.38, 0.95)),
            'hover': self._make_rounded_card_texture((0.32, 0.42, 0.58, 0.97)),
            'selected': self._make_rounded_card_texture((0.48, 0.36, 0.24, 0.97))
        }
        self.card_state_gradients = fallback_gradients
        self.card_panel_texture = self.ui_asset_manager.get_texture(
            'card_panel',
            fallback_factory=lambda: fallback_gradients['default']
        )
        self.portrait_frame_texture = self._make_rounded_card_texture((0.9, 0.95, 1.0, 0.98), radius=28, glow=True)
        self.thumbnail_mask_texture = self._make_rounded_card_texture((1.0, 1.0, 1.0, 1.0), radius=20)

    def _make_vertical_gradient_texture(self, top_color, bottom_color, size=(512, 512)):
        width, height = size
        image = PNMImage(width, height, 4)
        for y in range(height):
            t = y / max(1, height - 1)
            r = top_color[0] * (1 - t) + bottom_color[0] * t
            g = top_color[1] * (1 - t) + bottom_color[1] * t
            b = top_color[2] * (1 - t) + bottom_color[2] * t
            a = top_color[3] * (1 - t) + bottom_color[3] * t
            for x in range(width):
                image.setXelA(x, y, r, g, b, a)
        texture = Texture()
        texture.load(image)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinear)
        return texture

    def _make_rounded_card_texture(self, color, size=(256, 320), radius=24, glow=False):
        width, height = size
        image = PNMImage(width, height, 4)
        for y in range(height):
            t = y / max(1, height - 1)
            fade = 0.85 + 0.15 * (1 - t)
            base_r = color[0] * fade
            base_g = color[1] * fade
            base_b = color[2] * fade
            for x in range(width):
                alpha = self._rounded_alpha(x, y, width, height, radius)
                r = base_r
                g = base_g
                b = base_b
                if glow:
                    glow_strength = 0.12 * (1 - abs((y - height / 2) / (height / 2)))
                    r = min(1.0, r + glow_strength)
                    g = min(1.0, g + glow_strength)
                    b = min(1.0, b + glow_strength)
                image.setXelA(x, y, r, g, b, color[3] * alpha)
        texture = Texture()
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMinfilter(Texture.FTLinear)
        texture.setMagfilter(Texture.FTLinear)
        return texture

    @staticmethod
    def _rounded_alpha(x, y, width, height, radius):
        if radius <= 0:
            return 1.0
        dx = min(x, width - 1 - x)
        dy = min(y, height - 1 - y)
        if dx >= radius or dy >= radius:
            return 1.0
        distance_sq = (radius - dx) ** 2 + (radius - dy) ** 2
        if distance_sq >= radius ** 2:
            return 0.0
        # Smooth edge using normalized distance
        return max(0.0, min(1.0, 1 - distance_sq / (radius ** 2)))

    def _generate_portrait_texture(self, profile):
        """Generate a simple gradient portrait texture using profile colors."""
        base_color = profile.get('color_scheme', {})
        r = float(base_color.get('r', 0.65))
        g = float(base_color.get('g', 0.65))
        b = float(base_color.get('b', 0.8))

        width, height = 196, 196
        img = PNMImage(width, height)
        for y in range(height):
            t = y / max(1, height - 1)
            fade = 0.15 + 0.85 * (1 - t)
            for x in range(width):
                wave = 0.05 * math.sin((x / width) * math.pi * 4)
                img.setXelA(x, y, min(1.0, r * fade + wave),
                            min(1.0, g * fade + wave),
                            min(1.0, b * fade + wave),
                            1.0)

        tex = Texture()
        tex.load(img)
        tex.setMinfilter(Texture.FTLinearMipmapLinear)
        tex.setMagfilter(Texture.FTLinear)
        return tex

    def _adjust_image_node_scale(self, image_node, texture, max_width, max_height):
        """Uniformly scale an OnscreenImage so it fits within the provided bounds while preserving aspect ratio."""
        if not image_node:
            return

        if not texture:
            image_node.setScale(max_width, 1, max_height)
            return

        try:
            width = max(1, texture.getXSize())
            height = max(1, texture.getYSize())
        except Exception:
            width = height = 1

        aspect = width / height if height else 1.0
        target_width = max_width
        target_height = target_width / aspect if aspect else max_height
        if target_height > max_height:
            target_height = max_height
            target_width = target_height * aspect

        image_node.setScale(target_width, 1, target_height)

    def _set_image_with_scale(self, image_node, texture, max_width, max_height):
        """Assign a texture to an image node and clamp its dimensions inside the requested bounding box."""
        if not image_node:
            return

        if texture:
            try:
                image_node.setImage(texture)
            except Exception:
                image_node['image'] = texture

        self._adjust_image_node_scale(image_node, texture, max_width, max_height)

    def _get_portrait_texture(self, character_name):
        key = self._canonical_key(character_name)
        if key in self.portrait_cache:
            return self.portrait_cache[key]
        profile = self._get_profile(character_name).copy() if character_name else {}
        char_record = self.char_manager.get_character_by_name(character_name) if character_name else None
        if char_record and 'id' not in profile:
            profile['id'] = char_record.get('id')

        if not character_name:
            texture = self._generate_portrait_texture(profile)
        else:
            texture = self.portrait_manager.get_texture(
                key,
                profile,
                fallback_factory=lambda: self._generate_portrait_texture(profile)
            )

        self.portrait_cache[key] = texture
        return texture
        
    def _create_character_grid(self):
        """Create the enhanced character selection stage."""
        heading_font = self.fonts.get('heading')
        body_font = self.fonts.get('body')
        accent_font = self.fonts.get('accent') or heading_font or body_font

        self.bg_frame = DirectFrame(
            parent=self.base_app.render2d,
            frameColor=(1, 1, 1, 0.98),
            frameTexture=self.background_texture,
            frameSize=(-1.15, 1.15, -0.9, 0.9),
            relief=0
        )
        self.bg_frame.setBin("gui-popup", 200)
        self.bg_frame.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.bg_frame)

        title_text = f"Player {self.player_number} — Select Your Fighter" if self.mode == 'versus' else "Choose Your Fighter"
        self.title = OnscreenText(
            text=title_text,
            pos=(0.0, 0.78),
            scale=0.068,
            fg=(1, 0.92, 0.4, 1),
            shadow=(0, 0, 0, 1),
            align=TextNode.ACenter,
            parent=self.bg_frame,
            font=accent_font
        )
        self.ui_elements.append(self.title)

        self.subtitle = OnscreenText(
            text="Arrow / WASD navigate • Enter lock-in • Esc back",
            pos=(0.0, 0.69),
            scale=0.032,
            fg=(0.85, 0.9, 1, 0.95),
            shadow=(0, 0, 0, 0.9),
            align=TextNode.ACenter,
            parent=self.bg_frame,
            font=body_font
        )
        self.ui_elements.append(self.subtitle)

        self.info_frame = DirectFrame(
            parent=self.bg_frame,
            frameColor=(1, 1, 1, 0.15),
            frameTexture=self.info_panel_texture,
            frameSize=(-0.46, 0.46, -0.62, 0.62),
            pos=(0.74, 0, 0.02),
            relief=0
        )
        self.info_frame.setTransparency(TransparencyAttrib.MAlpha)
        self.info_frame.setBin("gui-popup", 201)
        self.ui_elements.append(self.info_frame)

        self.char_portrait = DirectFrame(
            parent=self.info_frame,
            frameColor=(1, 1, 1, 0),
            frameSize=(-0.28, 0.28, -0.28, 0.28),
            pos=(0, 0, 0.28),
            relief=0
        )
        self.char_portrait.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.char_portrait)

        initial_portrait = self._get_portrait_texture('')
        self.char_portrait_image = OnscreenImage(
            image=initial_portrait,
            pos=(0, 0, 0),
            parent=self.char_portrait
        )
        self.char_portrait_image.setTransparency(TransparencyAttrib.MAlpha)
        self.char_portrait_image.setBin("gui-popup", 202)
        self._set_image_with_scale(self.char_portrait_image, initial_portrait, 0.26, 0.26)
        self.ui_elements.append(self.char_portrait_image)

        self.char_name = OnscreenText(
            text="Select a character",
            pos=(0.0, 0.5),
            scale=0.052,
            fg=(1, 0.95, 0.85, 1),
            shadow=(0, 0, 0, 1),
            align=TextNode.ACenter,
            parent=self.info_frame,
            wordwrap=18,
            font=accent_font,
            mayChange=True
        )
        self.ui_elements.append(self.char_name)

        self.char_bio = OnscreenText(
            text="Mouse: click to preview\nNumbers 1-9 quick select",
            pos=(0.0, 0.18),
            scale=0.030,
            fg=(0.82, 0.88, 1, 0.95),
            align=TextNode.ACenter,
            parent=self.info_frame,
            wordwrap=26,
            font=body_font,
            mayChange=True
        )
        self.ui_elements.append(self.char_bio)

        self.char_stats = OnscreenText(
            text='',
            pos=(0.0, -0.05),
            scale=0.027,
            fg=(0.75, 0.95, 0.85, 0.95),
            align=TextNode.ACenter,
            parent=self.info_frame,
            wordwrap=24,
            font=body_font,
            mayChange=True
        )
        self.ui_elements.append(self.char_stats)

        self.char_moves = OnscreenText(
            text='',
            pos=(0.0, -0.38),
            scale=0.025,
            fg=(1, 0.86, 0.6, 0.95),
            align=TextNode.ACenter,
            parent=self.info_frame,
            wordwrap=30,
            font=body_font,
            mayChange=True
        )
        self.ui_elements.append(self.char_moves)

        self.grid_frame = DirectScrolledFrame(
            parent=self.bg_frame,
            frameColor=(1, 1, 1, 0.05),
            frameTexture=self.grid_texture,
            frameSize=(-1.05, 0.25, -0.7, 0.7),
            canvasSize=(-1.0, 0.9, -2.0, 0.8),
            pos=(-0.52, 0, 0.02),
            scrollBarWidth=0.024,
            autoHideScrollBars=True,
            relief=0
        )
        self.grid_frame.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.grid_frame)
        self.grid_canvas = self.grid_frame.getCanvas()
        self.grid_canvas.setPos(0, 0, 0)

        self._create_character_buttons()

        button_font = accent_font or body_font
        self.confirm_btn = DirectButton(
            parent=self.bg_frame,
            text='Lock In',
            text_scale=0.044,
            text_fg=(1, 1, 1, 1),
            text_font=button_font,
            frameColor=(0.2, 0.65, 0.4, 0.88),
            frameSize=(-0.14, 0.14, -0.048, 0.048),
            pos=(0.74, 0, -0.74),
            command=self._confirm_selection,
            pressEffect=1,
            relief=1
        )
        self.ui_elements.append(self.confirm_btn)
        self.confirm_btn.hide()

        self.random_btn = DirectButton(
            parent=self.bg_frame,
            text='Random',
            text_scale=0.038,
            text_fg=(1, 1, 1, 1),
            text_font=button_font,
            frameColor=(0.48, 0.38, 0.75, 0.88),
            frameSize=(-0.11, 0.11, -0.042, 0.042),
            pos=(0.0, 0, -0.78),
            command=self._random_selection
        )
        self.ui_elements.append(self.random_btn)

        self.back_btn = DirectButton(
            parent=self.bg_frame,
            text='Back',
            text_scale=0.038,
            text_fg=(1, 1, 1, 1),
            text_font=button_font,
            frameColor=(0.7, 0.32, 0.32, 0.88),
            frameSize=(-0.11, 0.11, -0.042, 0.042),
            pos=(-0.74, 0, -0.74),
            command=self._back_to_menu
        )
        self.ui_elements.append(self.back_btn)
        
    def _create_character_buttons(self):
        """Populate the roster grid with card-style buttons."""
        teams = self.char_manager.get_characters_by_team()
        all_characters = []
        for team_chars in teams.values():
            all_characters.extend(team_chars)
        
        print(f"Character selector: Found {len(all_characters)} characters")
        if len(all_characters) == 0:
            print("ERROR: No characters found for selection!")
            return
        filtered_characters = [
            name for name in all_characters
            if name and name.lower() not in {'butter', 'placeholder', 'empty'}
        ]
        self.all_characters = filtered_characters

        roster_count = len(filtered_characters)
        cols = 7
        rows = max(1, math.ceil(roster_count / cols))
        self.grid_cols = cols

        base_card_w = 0.25
        base_card_h = 0.30
        base_spacing_x = 0.29
        base_spacing_y = 0.32

        max_width = 1.52
        max_height = 1.36
        padding = 0.12

        grid_width = base_card_w + (cols - 1) * base_spacing_x
        grid_height = base_card_h + (rows - 1) * base_spacing_y
        scale = min(1.0, max_width / grid_width, max_height / grid_height)

        card_w = base_card_w * scale
        card_h = base_card_h * scale
        spacing_x = base_spacing_x * scale
        spacing_y = base_spacing_y * scale

        portrait_max_w = card_w * 0.74
        portrait_max_h = card_h * 0.52
        portrait_offset_z = card_h * 0.06

        self.character_buttons = []
        self.character_cards = []
        self.card_lookup = {}
        self.card_portrait_nodes = {}

        title_scale = max(0.024, card_w * 0.12)

        total_width = card_w + (cols - 1) * spacing_x
        total_height = card_h + (rows - 1) * spacing_y
        start_x = -total_width / 2.0 + card_w / 2.0
        start_y = total_height / 2.0 - card_h / 2.0

        frame_width = min(max_width, total_width + padding)
        frame_height = min(max_height, total_height + padding)
        frame_half_w = frame_width / 2.0
        frame_half_h = frame_height / 2.0
        canvas_half_w = total_width / 2.0 + padding / 2.0
        canvas_half_h = total_height / 2.0 + padding / 2.0

        self.grid_frame['frameSize'] = (-frame_half_w, frame_half_w, -frame_half_h, frame_half_h)
        self.grid_frame['canvasSize'] = (-canvas_half_w, canvas_half_w, -canvas_half_h, canvas_half_h)
        self.grid_frame['scrollBarWidth'] = 0.0 if canvas_half_h <= frame_half_h + 1e-3 else 0.022
        try:
            self.grid_frame.verticalScrollBar.hide()
            self.grid_frame.horizontalScrollBar.hide()
        except Exception:
            pass

        for idx, char_name in enumerate(filtered_characters):
            row = idx // cols
            col = idx % cols
            x = start_x + col * spacing_x
            y = start_y - row * spacing_y

            card = DirectFrame(
                parent=self.grid_canvas,
                frameColor=(1, 1, 1, 0),
                frameSize=(-card_w/2, card_w/2, -card_h/2, card_h/2),
                pos=(x, 0, y),
                relief=0
            )
            card.setBin("gui-popup", 201)  # 统一层级管理，避免渲染冲突
            card.setTransparency(TransparencyAttrib.MAlpha)
            card.character_name = char_name
            self.character_cards.append(card)
            self.card_lookup[char_name] = card
            self.ui_elements.append(card)

            portrait_texture = self._get_portrait_texture(char_name)
            portrait_node = OnscreenImage(
                image=portrait_texture,
                parent=card,
                pos=(0, 0, portrait_offset_z)
            )
            portrait_node.setTransparency(TransparencyAttrib.MAlpha)
            self._set_image_with_scale(portrait_node, portrait_texture, portrait_max_w, portrait_max_h)
            self.card_portrait_nodes[char_name] = portrait_node
            self.ui_elements.append(portrait_node)

            self._set_card_state(card, 'default')

            profile = self._get_profile(char_name)
            display_name = profile.get('display_name', char_name)

            label = OnscreenText(
                text=display_name,
                parent=card,
                pos=(0, -card_h/2 + title_scale * 1.6),
                scale=title_scale,
                fg=(1, 1, 1, 0.78),
                align=TextNode.ACenter,
                font=self.fonts.get('accent') or self.fonts.get('body'),
                shadow=(0, 0, 0, 0.65),
                wordwrap=max(10, int(16 * (card_w / base_card_w)))
            )
            self.ui_elements.append(label)

            def make_click_handler(name):
                def handler():
                    self._cancel_random_task()
                    self._select_character(name)
                return handler

            button = DirectButton(
                parent=card,
                text='',
                frameColor=(0, 0, 0, 0),
                frameSize=(-card_w/2, card_w/2, -card_h/2, card_h/2),
                pos=(0, 0, 0),
                command=make_click_handler(char_name),
                relief=0
            )
            button.character_name = char_name

            def make_hover(name, card_ref):
                def on_enter(event=None):
                    if self.selected_character != name:
                        self._set_card_state(card_ref, 'hover')
                    self._preview_character(name)
                def on_exit(event=None):
                    if self.selected_character != name:
                        self._set_card_state(card_ref, 'default')
                return on_enter, on_exit

            enter_cb, exit_cb = make_hover(char_name, card)
            button.bind("DGG.WITHIN", enter_cb)
            button.bind("DGG.WITHOUT", exit_cb)

            self.character_buttons.append(button)
            self.ui_elements.append(button)
    
    def _set_card_state(self, card, state):
        """Apply a consistent color style to a card."""
        if not card:
            return
        texture = self.card_panel_texture or self.card_state_gradients.get(state)
        portrait_node = None
        if hasattr(card, 'character_name'):
            portrait_node = self.card_portrait_nodes.get(card.character_name)
        if texture:
            card['frameTexture'] = texture
        tint = self.card_colors.get(state, self.card_colors['default'])
        card['frameColor'] = tint
        if portrait_node:
            if state == 'selected':
                portrait_node.setColorScale(1.0, 1.0, 1.0, 1.0)
            elif state == 'hover':
                portrait_node.setColorScale(0.9, 0.9, 0.9, 1.0)
            else:
                portrait_node.setColorScale(0.75, 0.75, 0.75, 1.0)

    def _cancel_auto_confirm(self):
        try:
            self.base_app.taskMgr.remove(self._auto_confirm_task_name)
        except Exception:
            pass

    def _cancel_random_task(self):
        self._random_spin_state = None
        try:
            self.base_app.taskMgr.remove(self._random_task_name)
        except Exception:
            pass

    def _select_character(self, character_name):
        """Handle character selection"""
        print(f"Character selected: {character_name}")
        self.selected_character = character_name
        if character_name in self.all_characters:
            self.current_selection_index = self.all_characters.index(character_name)
        
        # Update card appearances
        for btn in self.character_buttons:
            card = self.card_lookup.get(btn.character_name)
            if btn.character_name == character_name:
                self._set_card_state(card, 'selected')
            else:
                self._set_card_state(card, 'default')
        
        # Show character info
        self._preview_character(character_name)
        if getattr(self, 'confirm_btn', None):
            self.confirm_btn.show()
        self._cancel_auto_confirm()
    
    def _preview_character(self, character_name):
        """Preview character information"""
        char_data = self.char_manager.get_character_by_name(character_name)
        if not char_data:
            return
        
        # Extract nationality/country with proper fallback
        nationality = self._get_character_nationality(char_data)
        profile = self._get_profile(character_name)

        display_name = profile.get('display_name', char_data.get('name', character_name))
        difficulty = profile.get('difficulty')
        description = profile.get('description', char_data.get('description', 'Ready to fight!'))
        origin = profile.get('origin', nationality)

        portrait_texture = self._get_portrait_texture(character_name)
        if portrait_texture:
            self._set_image_with_scale(self.char_portrait_image, portrait_texture, 0.26, 0.26)
        self.char_name.setText(display_name)

        bio_lines = [origin]
        if description:
            bio_lines.append(description)
        if difficulty:
            bio_lines.append(f"Difficulty: {difficulty}/5")
        self.char_bio.setText('\n'.join(bio_lines))
        
        # Update character stats with enhanced compatibility
        stats_text = self._build_character_stats_text(char_data)
        self.char_stats.setText(stats_text)
        
        # Update special moves
        moves_text = "Signature Techniques:\n"
        special_moves = char_data.get('special_moves', {})
        count = 0
        for move_name, move_data in special_moves.items():
            if count >= 3:  # Limit display
                moves_text += "..."
                break
            desc = move_data.get('description', '')
            moves_text += f"• {move_name} ({move_data.get('input', '??')})\n"
            if desc:
                moves_text += f"  {desc}\n"
            count += 1
        
        if not special_moves:
            moves_text += "Basic fighting skills"
            
        self.char_moves.setText(moves_text)
    
    def _get_character_nationality(self, char_data):
        """Extract character nationality/country with intelligent fallback"""
        # Priority: nationality -> country -> derive from team/name -> default
        if 'nationality' in char_data:
            return char_data['nationality']
        elif 'country' in char_data:
            return char_data['country']
        
        # Intelligent derivation based on character data
        team = char_data.get('team', '')
        name = char_data.get('name', '')
        
        # Derive nationality from team name patterns
        if 'Japan' in team or 'Sacred' in team:
            return 'Japan'
        elif 'Fatal Fury' in team or 'Terry' in name or 'Andy' in name:
            return 'USA'
        elif 'Art of Fighting' in team or 'Sakazaki' in name or 'Garcia' in name:
            return 'USA'  # South Town setting
        elif 'Ikari' in team:
            return 'International'
        elif 'Psycho Soldier' in team or 'Athena' in name:
            return 'Japan'
        elif 'Women Fighters' in team or 'Mai' in name:
            return 'Japan'
        elif 'Kim Team' in team or 'Kim' in name:
            return 'Korea'
        elif 'NESTS' in team:
            return 'Unknown'
        elif 'Boss' in team or 'Geese' in name or 'Rugal' in name:
            return 'International'
        
        # Character-specific intelligent mapping
        character_nationality_map = {
            'Kyo Kusanagi': 'Japan',
            'Iori Yagami': 'Japan', 
            'Terry Bogard': 'USA',
            'Mai Shiranui': 'Japan',
            'Athena Asamiya': 'Japan',
            'Leona Heidern': 'Brazil',
            'Ryo Sakazaki': 'USA',
            'Kim Kaphwan': 'Korea',
            'Geese Howard': 'USA',
            'Rugal Bernstein': 'Germany'
        }
        
        return character_nationality_map.get(name, 'International')
    
    def _build_character_stats_text(self, char_data):
        """Build character stats text with enhanced compatibility"""
        # Fighting style with fallback
        fighting_style = char_data.get('fighting_style', 
                                      char_data.get('style', 'Mixed Martial Arts'))
        
        stats_text = f"Fighting Style: {fighting_style}\\n\\n"
        
        # Handle different stats data structures
        stats = char_data.get('stats', {})
        if stats:
            # New comprehensive database format
            stats_text += f"Attack: {stats.get('attack', 5)}/10\\n"
            stats_text += f"Defense: {stats.get('defense', 5)}/10\\n"
            stats_text += f"Speed: {stats.get('speed', 5)}/10\\n"
            stats_text += f"Health: {stats.get('health', 5)}/10\\n"
            stats_text += f"Range: {stats.get('range', 5)}/10"
        else:
            # Legacy database format or missing stats
            power = char_data.get('power', 5)
            speed = char_data.get('speed', 5)
            health = char_data.get('health', 100)
            
            # Convert to 10-point scale if needed
            if health > 10:
                health = min(10, health // 10)
            
            stats_text += f"Power: {power}/10\\n"
            stats_text += f"Speed: {speed}/10\\n"
            stats_text += f"Health: {health}/10\\n"
            stats_text += f"Defense: {5}/10\\n"
            stats_text += f"Range: {5}/10"
        
        return stats_text
    
    def _random_selection(self):
        """Randomly highlight characters with a brief spin before settling on a choice."""
        if not self.all_characters:
            return
        if self._random_spin_state:
            return

        roster_count = len(self.all_characters)
        final_index = random.randrange(roster_count)
        self._cancel_auto_confirm()
        self._cancel_random_task()

        sequence = self._build_random_spin_sequence(final_index, roster_count)
        self._random_spin_state = {
            'sequence': sequence,
            'delay': 0.05
        }
        self.base_app.taskMgr.doMethodLater(0.0, self._random_spin_step, self._random_task_name)

    def _build_random_spin_sequence(self, final_index, roster_count):
        spin_length = max(18, roster_count * 3)
        sequence = []
        index = self.current_selection_index if 0 <= self.current_selection_index < roster_count else random.randrange(roster_count)
        for _ in range(spin_length):
            step = random.randint(1, min(3, roster_count))
            index = (index + step) % roster_count
            sequence.append(index)
        sequence.append(final_index)
        return sequence

    def _random_spin_step(self, task):
        if not self._random_spin_state:
            return Task.done

        sequence = self._random_spin_state['sequence']
        if not sequence:
            self._random_spin_state = None
            return Task.done

        next_index = sequence.pop(0)
        if next_index < len(self.all_characters):
            self.current_selection_index = next_index
            if sequence:
                self._highlight_current_selection()
            else:
                self._random_spin_state = None
                self._highlight_current_selection()
                self._select_character(self.all_characters[next_index])
                return Task.done

        delay = self._random_spin_state['delay']
        self._random_spin_state['delay'] = min(0.12, delay * 1.12)
        task.delayTime = delay
        return Task.again
    
    def _confirm_selection(self):
        """Confirm character selection"""
        self._cancel_random_task()
        self._cancel_auto_confirm()
        if self.selected_character and self.callback:
            print(f"Locking in character: {self.selected_character}")
            self.callback(self.selected_character)
    
    def _back_to_menu(self):
        """Return to main menu"""
        self._cancel_random_task()
        self._cancel_auto_confirm()
        if hasattr(self.base_app, '_return_to_mode_selection'):
            self.base_app._return_to_mode_selection()
        else:
            self.hide()
    
    def _setup_keyboard_navigation(self):
        """Setup keyboard navigation for character selection"""
        if not self.all_characters:
            return

        self._teardown_keyboard_navigation()
        
        # Arrow keys and WASD for navigation
        for key, handler in (
            ('arrow_left', self._navigate_left),
            ('arrow_right', self._navigate_right),
            ('arrow_up', self._navigate_up),
            ('arrow_down', self._navigate_down),
            ('a', self._navigate_left),
            ('d', self._navigate_right),
            ('w', self._navigate_up),
            ('s', self._navigate_down),
            ('enter', self._confirm_current_selection),
            ('space', self._confirm_current_selection),
            ('r', self._random_selection),
        ):
            self.base_app.accept(key, handler)
            self._nav_bindings.add(key)
        
        # Number keys for direct selection
        for i in range(min(10, len(self.all_characters))):
            key = str(i + 1)
            self.base_app.accept(key, self._direct_select, [i])
            self._nav_bindings.add(key)
        
        # Initial highlight
        self._highlight_current_selection()

    def _teardown_keyboard_navigation(self):
        """Remove keyboard bindings for character selection."""
        for key in list(self._nav_bindings):
            try:
                self.base_app.ignore(key)
            except Exception:
                pass
        self._nav_bindings.clear()
    
    def _navigate_left(self):
        """Navigate left in character grid"""
        if self.current_selection_index > 0:
            self.current_selection_index -= 1
            self._highlight_current_selection()
    
    def _navigate_right(self):
        """Navigate right in character grid"""
        if self.current_selection_index < len(self.all_characters) - 1:
            self.current_selection_index += 1
            self._highlight_current_selection()
    
    def _navigate_up(self):
        """Navigate up in character grid"""
        cols = self.grid_cols
        new_index = self.current_selection_index - cols
        if new_index >= 0:
            self.current_selection_index = new_index
            self._highlight_current_selection()
    
    def _navigate_down(self):
        """Navigate down in character grid"""
        cols = self.grid_cols
        new_index = self.current_selection_index + cols
        if new_index < len(self.all_characters):
            self.current_selection_index = new_index
            self._highlight_current_selection()
    
    def _highlight_current_selection(self):
        """Highlight the currently selected character button"""
        for i, btn in enumerate(self.character_buttons):
            card = self.card_lookup.get(btn.character_name)
            if i == self.current_selection_index:
                if self.selected_character != btn.character_name:
                    self._set_card_state(card, 'hover')
                if i < len(self.all_characters):
                    self._preview_character(self.all_characters[i])
            elif btn.character_name != self.selected_character:
                self._set_card_state(card, 'default')
    
    def _confirm_current_selection(self):
        """Confirm the currently highlighted character"""
        if self.current_selection_index < len(self.all_characters):
            character_name = self.all_characters[self.current_selection_index]
            self._cancel_random_task()
            self._select_character(character_name)
            self._confirm_selection()
    
    def _direct_select(self, index):
        """Direct selection by number key"""
        if 0 <= index < len(self.all_characters):
            self.current_selection_index = index
            self._highlight_current_selection()
            character_name = self.all_characters[index]
            self._cancel_random_task()
            self._select_character(character_name)
    
    def show(self, callback=None, mode='single', player_number=1):
        """Show character selection interface"""
        self.callback = callback
        self.mode = mode
        self.player_number = player_number
        
        # Create UI if not exists
        if not self.ui_elements:
            self._create_character_grid()
        
        # Show all elements
        for element in self.ui_elements:
            element.show()

        if getattr(self, 'confirm_btn', None) and not self.selected_character:
            self.confirm_btn.hide()
        
        # Setup keyboard navigation
        self._setup_keyboard_navigation()
        self.visible = True
    
    def hide(self):
        """Hide character selection interface"""
        self._cancel_random_task()
        self._cancel_auto_confirm()
        for element in self.ui_elements:
            element.hide()
        self._teardown_keyboard_navigation()
        self.selected_character = None
        self.current_selection_index = 0
        self.visible = False
        
        # Remove keyboard bindings
        self._cleanup_keyboard_navigation()
    
    def _cleanup_keyboard_navigation(self):
        """Clean up keyboard navigation bindings"""
        keys_to_cleanup = [
            'arrow_left', 'arrow_right', 'arrow_up', 'arrow_down',
            'a', 'd', 'w', 's', 'enter', 'space'
        ]
        
        for key in keys_to_cleanup:
            try:
                self.base_app.ignore(key)
            except:
                pass
        
        # Clean up number keys
        for i in range(10):
            try:
                self.base_app.ignore(str(i + 1))
            except:
                pass
    
    def destroy(self):
        """Clean up character selection interface"""
        self._cancel_random_task()
        
        self._cleanup_keyboard_navigation()
            
        for element in self.ui_elements:
            try:
                element.removeNode()
            except:
                pass
        self.ui_elements.clear()
        self.character_buttons.clear()