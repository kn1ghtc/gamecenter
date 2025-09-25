#!/usr/bin/env python3
"""
Character Selection Interface for StreetBattle
Provides character selection with portraits and information
"""

from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenText, DirectScrolledFrame
from panda3d.core import TextNode, Vec4
from direct.task import Task
import math
import random


class CharacterSelector:
    """Character selection interface"""
    
    def __init__(self, base_app, character_manager):
        self.base_app = base_app
        self.char_manager = character_manager
        self.callback = None
        self.ui_elements = []
        self.selected_character = None
        self.character_buttons = []
        self.mode = 'single'  # 'single' or 'versus' (for P1/P2)
        self.player_number = 1
        self.current_selection_index = 0  # For keyboard navigation
        self.all_characters = []  # Store character list for keyboard navigation
        
    def _create_character_grid(self):
        """Create character selection grid"""
        # Background (more visible color for testing)
        self.bg_frame = DirectFrame(
            parent=self.base_app.render2d,
            frameColor=(0.1, 0.1, 0.3, 0.95),  # More visible blue background
            frameSize=(-1, 1, -1, 1)
        )
        self.ui_elements.append(self.bg_frame)
        
        # Title
        title_text = f"Select Character (Player {self.player_number})" if self.mode == 'versus' else "Choose Your Fighter"
        self.title = OnscreenText(
            text=title_text,
            pos=(0, 0.85),
            scale=0.08,
            fg=(1, 0.9, 0.3, 1),
            shadow=(0, 0, 0, 1),
            align=TextNode.ACenter,
            parent=self.bg_frame
        )
        self.ui_elements.append(self.title)
        
        # Character info panel (right side)
        self.info_frame = DirectFrame(
            parent=self.bg_frame,
            frameColor=(0.1, 0.1, 0.15, 0.8),
            frameSize=(0.4, 0.95, -0.7, 0.7),
            pos=(0, 0, 0)
        )
        self.ui_elements.append(self.info_frame)
        
        # Character portrait placeholder
        self.char_portrait = DirectFrame(
            parent=self.info_frame,
            frameColor=(0.2, 0.2, 0.3, 0.9),
            frameSize=(-0.2, 0.2, -0.25, 0.25),
            pos=(0.675, 0, 0.3)
        )
        self.ui_elements.append(self.char_portrait)
        
        # Character name
        self.char_name = OnscreenText(
            text='Select a character\n\nMouse: Click character buttons\nKeyboard: WASD/Arrow keys + Enter\nNumbers 1-9: Direct select\n\nPress ESC to return to menu',
            pos=(0.675, 0.0),
            scale=0.032,
            fg=(1, 1, 0.8, 1),
            align=TextNode.ACenter,
            parent=self.info_frame,
            wordwrap=18
        )
        self.ui_elements.append(self.char_name)
        
        # Character stats
        self.char_stats = OnscreenText(
            text='',
            pos=(0.675, -0.15),
            scale=0.025,
            fg=(0.8, 0.9, 1, 1),
            align=TextNode.ACenter,
            parent=self.info_frame,
            wordwrap=20
        )
        self.ui_elements.append(self.char_stats)
        
        # Character special moves
        self.char_moves = OnscreenText(
            text='',
            pos=(0.675, -0.4),
            scale=0.022,
            fg=(0.9, 0.8, 0.6, 1),
            align=TextNode.ACenter,
            parent=self.info_frame,
            wordwrap=25
        )
        self.ui_elements.append(self.char_moves)
        
        # Character grid (left side)
        self._create_character_buttons()
        
        # Confirm button
        self.confirm_btn = DirectButton(
            text='Confirm Selection',
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.3, 0.6, 0.3, 0.8),
            frameSize=(-0.15, 0.15, -0.05, 0.05),
            pos=(0, 0, -0.85),
            command=self._confirm_selection,
            parent=self.bg_frame,
            pressEffect=1,
            relief=1
        )
        self.ui_elements.append(self.confirm_btn)
        self.confirm_btn.hide()  # Hidden until character selected
        
        # Random select button
        self.random_btn = DirectButton(
            text='Random Select',
            text_scale=0.035,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.6, 0.4, 0.6, 0.8),
            frameSize=(-0.1, 0.1, -0.04, 0.04),
            pos=(-0.25, 0, -0.85),
            command=self._random_selection,
            parent=self.bg_frame
        )
        self.ui_elements.append(self.random_btn)
        
        # Back to mode selection button  
        self.back_btn = DirectButton(
            text='Back to Menu',
            text_scale=0.035,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.6, 0.3, 0.3, 0.8),
            frameSize=(-0.1, 0.1, -0.04, 0.04),
            pos=(0.25, 0, -0.85),
            command=self._back_to_menu,
            parent=self.bg_frame
        )
        self.ui_elements.append(self.back_btn)
        
    def _create_character_buttons(self):
        """Create character selection buttons in a grid"""
        teams = self.char_manager.get_characters_by_team()
        all_characters = []
        for team_chars in teams.values():
            all_characters.extend(team_chars)
        
        self.all_characters = all_characters  # Store for keyboard navigation
        
        print(f"Character selector: Found {len(all_characters)} characters")
        if len(all_characters) == 0:
            print("ERROR: No characters found for selection!")
            return
        
        # Grid layout: 5 columns, multiple rows
        cols = 5
        rows = (len(all_characters) + cols - 1) // cols
        
        start_x = -0.35
        start_y = 0.6
        btn_width = 0.13
        btn_height = 0.18
        spacing_x = 0.15
        spacing_y = 0.2
        
        for i, char_name in enumerate(all_characters):
            row = i // cols
            col = i % cols
            
            x = start_x + col * spacing_x
            y = start_y - row * spacing_y
            
            # Create character button with simplified text
            btn_text = char_name.split(' ')[0] if ' ' in char_name else char_name[:8]  # First name or first 8 chars
            btn = DirectButton(
                text=btn_text,
                text_scale=0.04,
                text_fg=(1, 1, 1, 1),
                text_pos=(0, -0.02),  # Center text vertically
                frameColor=(0.3, 0.4, 0.6, 0.9),
                frameSize=(-btn_width/2, btn_width/2, -btn_height/2, btn_height/2),
                pos=(x, 0, y),
                command=self._select_character,
                extraArgs=[char_name],
                parent=self.bg_frame,
                pressEffect=1,  # Add press effect
                relief=1  # Make button more visible
            )
            
            btn.character_name = char_name
            self.character_buttons.append(btn)
            self.ui_elements.append(btn)
            
            # Hover effects
            def create_hover_effects(button, name):
                def on_enter():
                    button['frameColor'] = (0.3, 0.4, 0.6, 0.9)
                    button['text_fg'] = (1, 1, 0.8, 1)
                    self._preview_character(name)
                
                def on_exit():
                    if self.selected_character != name:
                        button['frameColor'] = (0.15, 0.2, 0.3, 0.8)
                        button['text_fg'] = (1, 1, 1, 1)
                
                return on_enter, on_exit
            
            on_enter, on_exit = create_hover_effects(btn, char_name)
            btn.bind("DGG.WITHIN", lambda event, f=on_enter: f())
            btn.bind("DGG.WITHOUT", lambda event, f=on_exit: f())
    
    def _select_character(self, character_name):
        """Handle character selection"""
        print(f"Character selected: {character_name}")
        self.selected_character = character_name
        
        # Update button appearances
        for btn in self.character_buttons:
            if btn.character_name == character_name:
                btn['frameColor'] = (0.5, 0.7, 0.3, 0.9)
                btn['text_fg'] = (1, 1, 1, 1)
            else:
                btn['frameColor'] = (0.3, 0.4, 0.6, 0.9)  # Reset to original color
                btn['text_fg'] = (0.8, 0.8, 0.8, 1)
        
        # Show character info
        self._preview_character(character_name)
        
        # Automatically confirm selection after brief preview
        self.base_app.taskMgr.doMethodLater(0.5, self._auto_confirm_selection, 'auto-confirm-selection')
    
    def _preview_character(self, character_name):
        """Preview character information"""
        char_data = self.char_manager.get_character_by_name(character_name)
        if not char_data:
            return
        
        # Extract nationality/country with proper fallback
        nationality = self._get_character_nationality(char_data)
        
        # Update character name
        self.char_name.setText(f"{char_data['name']}\\n{nationality}")
        
        # Update character stats with enhanced compatibility
        stats_text = self._build_character_stats_text(char_data)
        self.char_stats.setText(stats_text)
        
        # Update special moves
        moves_text = "Special Moves:\\n"
        special_moves = char_data.get('special_moves', {})
        count = 0
        for move_name, move_data in special_moves.items():
            if count >= 3:  # Limit display
                moves_text += "..."
                break
            moves_text += f"• {move_name}: {move_data['input']}\\n"
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
        """Randomly select a character"""
        all_chars = self.char_manager.get_character_names()
        if all_chars:
            # Random selection animation
            self._animate_random_selection(all_chars)
    
    def _animate_random_selection(self, all_chars):
        """Animate random character selection"""
        selection_count = 0
        max_selections = 10
        
        def random_step(task):
            nonlocal selection_count
            
            if selection_count < max_selections:
                # Highlight random character
                random_char = random.choice(all_chars)
                self._preview_character(random_char)
                
                # Highlight button briefly
                for btn in self.character_buttons:
                    if btn.character_name == random_char:
                        btn['frameColor'] = (1, 1, 0.3, 0.9)
                        break
                
                selection_count += 1
                return task.cont
            else:
                # Final selection
                final_char = random.choice(all_chars)
                self._select_character(final_char)
                return task.done
        
        self.base_app.taskMgr.add(random_step, 'random-selection', delay=0.1)
    
    def _auto_confirm_selection(self, task=None):
        """Auto confirm character selection after brief preview"""
        if self.selected_character and self.callback:
            print(f"Confirming selection: {self.selected_character}")
            self.callback(self.selected_character)
        return None
    
    def _confirm_selection(self):
        """Confirm character selection"""
        if self.selected_character and self.callback:
            self.callback(self.selected_character)
    
    def _back_to_menu(self):
        """Return to main menu"""
        if hasattr(self.base_app, '_handle_escape'):
            self.base_app._handle_escape()
    
    def _setup_keyboard_navigation(self):
        """Setup keyboard navigation for character selection"""
        if not self.all_characters:
            return
        
        # Arrow keys and WASD for navigation
        self.base_app.accept('arrow_left', self._navigate_left)
        self.base_app.accept('arrow_right', self._navigate_right)
        self.base_app.accept('arrow_up', self._navigate_up)
        self.base_app.accept('arrow_down', self._navigate_down)
        
        # WASD navigation
        self.base_app.accept('a', self._navigate_left)
        self.base_app.accept('d', self._navigate_right)
        self.base_app.accept('w', self._navigate_up)
        self.base_app.accept('s', self._navigate_down)
        
        # Enter and Space to select
        self.base_app.accept('enter', self._confirm_current_selection)
        self.base_app.accept('space', self._confirm_current_selection)
        
        # Number keys for direct selection
        for i in range(min(10, len(self.all_characters))):
            self.base_app.accept(str(i + 1), self._direct_select, [i])
        
        # Initial highlight
        self._highlight_current_selection()
    
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
        cols = 5
        new_index = self.current_selection_index - cols
        if new_index >= 0:
            self.current_selection_index = new_index
            self._highlight_current_selection()
    
    def _navigate_down(self):
        """Navigate down in character grid"""
        cols = 5
        new_index = self.current_selection_index + cols
        if new_index < len(self.all_characters):
            self.current_selection_index = new_index
            self._highlight_current_selection()
    
    def _highlight_current_selection(self):
        """Highlight the currently selected character button"""
        for i, btn in enumerate(self.character_buttons):
            if i == self.current_selection_index:
                btn['frameColor'] = (0.6, 0.7, 0.9, 1.0)  # Highlighted color
                btn['text_fg'] = (1, 1, 0.8, 1)
                # Preview character
                if i < len(self.all_characters):
                    self._preview_character(self.all_characters[i])
            else:
                btn['frameColor'] = (0.3, 0.4, 0.6, 0.9)  # Normal color
                btn['text_fg'] = (1, 1, 1, 1)
    
    def _confirm_current_selection(self):
        """Confirm the currently highlighted character"""
        if self.current_selection_index < len(self.all_characters):
            character_name = self.all_characters[self.current_selection_index]
            self._select_character(character_name)
    
    def _direct_select(self, index):
        """Direct selection by number key"""
        if 0 <= index < len(self.all_characters):
            self.current_selection_index = index
            self._highlight_current_selection()
            character_name = self.all_characters[index]
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
        
        # Setup keyboard navigation
        self._setup_keyboard_navigation()
    
    def hide(self):
        """Hide character selection interface"""
        for element in self.ui_elements:
            element.hide()
        
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
        try:
            self.base_app.taskMgr.remove('random-selection')
        except:
            pass
        
        self._cleanup_keyboard_navigation()
            
        for element in self.ui_elements:
            try:
                element.removeNode()
            except:
                pass
        self.ui_elements.clear()
        self.character_buttons.clear()