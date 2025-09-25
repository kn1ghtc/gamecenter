#!/usr/bin/env python3
"""
Game Mode Selection System for StreetBattle
Provides main menu with Adventure, Versus, and Network modes
"""

from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TextNode, Vec4
from direct.task import Task
import math


class GameModeSelector:
    """Game mode selection interface"""
    
    def __init__(self, base_app):
        self.base_app = base_app
        self.callback = None  # Callback when mode is selected
        self.ui_elements = []
        self.selected_mode = None
        self.animation_time = 0.0
        self.current_selection = 0  # Currently selected button index
        self.keyboard_active = False
        
        self._create_main_menu()
        
    def _create_main_menu(self):
        """Create the main menu interface"""
        # Background frame
        self.bg_frame = DirectFrame(
            parent=self.base_app.render2d,
            frameColor=(0.05, 0.05, 0.1, 0.95),
            frameSize=(-1, 1, -1, 1)
        )
        self.ui_elements.append(self.bg_frame)
        
        # Title
        self.title = OnscreenText(
            text='StreetBattle KOF97',
            pos=(0, 0.7),
            scale=0.12,
            fg=(1, 0.8, 0.2, 1),
            shadow=(0, 0, 0, 1),
            align=TextNode.ACenter,
            font=None,
            parent=self.bg_frame
        )
        self.ui_elements.append(self.title)
        
        # Subtitle
        self.subtitle = OnscreenText(
            text='Select Game Mode:',
            pos=(0, 0.45),
            scale=0.06,
            fg=(0.9, 0.9, 1, 1),
            align=TextNode.ACenter,
            parent=self.bg_frame
        )
        self.ui_elements.append(self.subtitle)
        
        # Mode buttons
        button_data = [
            {
                'text': 'Adventure Mode\nSingle Player Campaign',
                'mode': 'adventure',
                'pos': (0, 0.15),
                'desc': 'Fight through AI opponents, face a BOSS every 10 levels'
            },
            {
                'text': 'Versus Mode\nLocal Battle', 
                'mode': 'versus',
                'pos': (0, -0.05),
                'desc': 'Fight against a random AI character in best of 3 rounds'
            },
            {
                'text': 'Network Mode\nOnline Battle',
                'mode': 'network',
                'pos': (0, -0.25),
                'desc': 'Connect with other players in LAN for online battles'
            }
        ]
        
        self.mode_buttons = []
        for btn_info in button_data:
            btn = DirectButton(
                text=btn_info['text'],
                text_scale=0.04,
                text_fg=(1, 1, 1, 1),
                text_shadow=(0, 0, 0, 1),
                frameColor=(0.2, 0.3, 0.5, 0.8),
                frameSize=(-0.35, 0.35, -0.06, 0.06),
                pos=(btn_info['pos'][0], 0, btn_info['pos'][1]),  # Convert (x, y) to (x, 0, z)
                command=self._select_mode,
                extraArgs=[btn_info['mode']],
                parent=self.bg_frame,
                rolloverSound=None,
                clickSound=None
            )
            btn.mode_info = btn_info
            self.mode_buttons.append(btn)
            self.ui_elements.append(btn)
            
            # Hover effects
            def on_enter(btn=btn):
                btn['frameColor'] = (0.3, 0.5, 0.8, 0.9)
                btn['text_fg'] = (1, 1, 0.8, 1)
            
            def on_exit(btn=btn):
                btn['frameColor'] = (0.2, 0.3, 0.5, 0.8)
                btn['text_fg'] = (1, 1, 1, 1)
                
            btn.bind("DGG.WITHIN", on_enter)
            btn.bind("DGG.WITHOUT", on_exit)
        
        # Description text
        self.description = OnscreenText(
            text='Select a game mode to start playing',
            pos=(0, -0.5),
            scale=0.04,
            fg=(0.8, 0.8, 0.9, 1),
            align=TextNode.ACenter,
            parent=self.bg_frame,
            wordwrap=25
        )
        self.ui_elements.append(self.description)
        
        # Controls info
        self.controls_info = OnscreenText(
            text='Arrow Keys/WASD: Navigate | ENTER/SPACE: Select | ESC: Exit | Mouse: Click to select',
            pos=(0, -0.8),
            scale=0.03,
            fg=(0.6, 0.6, 0.7, 1),
            align=TextNode.ACenter,
            parent=self.bg_frame
        )
        self.ui_elements.append(self.controls_info)
        
        # Start animation task
        self.base_app.taskMgr.add(self._animate_ui, 'menu-animation')
        
    def _animate_ui(self, task):
        """Animate UI elements for visual appeal - optimized to prevent flickering"""
        self.animation_time += 0.016  # Fixed timestep to prevent flickering
        
        try:
            # Minimal title animation - reduced frequency
            if int(self.animation_time * 2) % 2 == 0:  # Update every 0.5 seconds only
                alpha = 0.9 + 0.1 * math.sin(self.animation_time * 0.5)
                self.title.setFg(Vec4(1, 0.8, 0.2, alpha))
            
            # Remove button scaling animation to eliminate flickering
            # Keep buttons stable
            
        except Exception:
            pass
            
        return task.cont
        
    def _select_mode(self, mode):
        """Handle mode selection"""
        self.selected_mode = mode
        
        # Update description based on selected mode
        mode_descriptions = {
            'adventure': 'Adventure Mode: Fight through AI opponents one by one!\\nEvery 10 levels you will face a powerful BOSS. Difficulty increases progressively.',
            'versus': 'Versus Mode: System will randomly select an AI character to fight against you\\nBest of 3 rounds, 120 seconds per round. Show your fighting skills!',
            'network': 'Network Mode: Search for other players in LAN\\nSend battle invitations and face real human opponents!'
        }
        
        desc = mode_descriptions.get(mode, 'Unknown mode')
        self.description.setText(desc)
        
        # Visual feedback
        for btn in self.mode_buttons:
            if btn.mode_info['mode'] == mode:
                btn['frameColor'] = (0.5, 0.8, 0.3, 0.9)
                btn['text_fg'] = (1, 1, 1, 1)
            else:
                btn['frameColor'] = (0.2, 0.3, 0.5, 0.6)
                btn['text_fg'] = (0.7, 0.7, 0.7, 1)
        
        # Immediately confirm selection - no delay needed
        print(f"Mode selected: {mode}")
        if self.callback:
            self.callback(mode)
        
    def show(self, callback=None):
        """Show the mode selection menu"""
        self.callback = callback
        for element in self.ui_elements:
            element.show()
        
        # Enable keyboard navigation
        self._setup_keyboard_navigation()
        self._highlight_current_selection()
    
    def hide(self):
        """Hide the mode selection menu"""
        for element in self.ui_elements:
            element.hide()
        
        # Clean up animation task and keyboard bindings
        try:
            self.base_app.taskMgr.remove('menu-animation')
            self.base_app.taskMgr.remove('confirm-mode-selection')
        except:
            pass
        
        # Remove keyboard bindings
        self._cleanup_keyboard_navigation()
    
    def _setup_keyboard_navigation(self):
        """Setup keyboard navigation for menu"""
        self.keyboard_active = True
        self.base_app.accept('arrow_up', self._navigate_up)
        self.base_app.accept('arrow_down', self._navigate_down)
        self.base_app.accept('w', self._navigate_up)
        self.base_app.accept('s', self._navigate_down)
        self.base_app.accept('enter', self._confirm_selection)
        self.base_app.accept('space', self._confirm_selection)
    
    def _cleanup_keyboard_navigation(self):
        """Remove keyboard navigation bindings"""
        self.keyboard_active = False
        try:
            self.base_app.ignore('arrow_up')
            self.base_app.ignore('arrow_down') 
            self.base_app.ignore('w')
            self.base_app.ignore('s')
            self.base_app.ignore('enter')
            self.base_app.ignore('space')
        except:
            pass
    
    def _navigate_up(self):
        """Navigate to previous option"""
        if not self.keyboard_active:
            return
        self.current_selection = (self.current_selection - 1) % len(self.mode_buttons)
        self._highlight_current_selection()
    
    def _navigate_down(self):
        """Navigate to next option"""
        if not self.keyboard_active:
            return
        self.current_selection = (self.current_selection + 1) % len(self.mode_buttons)
        self._highlight_current_selection()
    
    def _highlight_current_selection(self):
        """Highlight the currently selected button"""
        for i, btn in enumerate(self.mode_buttons):
            if i == self.current_selection:
                # Highlight selected button
                btn['frameColor'] = (0.5, 0.8, 0.3, 0.9)
                btn['text_fg'] = (1, 1, 1, 1)
                btn.setScale(1.1)
                
                # Update description
                desc = btn.mode_info['desc']
                self.description.setText(desc)
            else:
                # Normal appearance for other buttons
                btn['frameColor'] = (0.2, 0.3, 0.5, 0.8)
                btn['text_fg'] = (0.8, 0.8, 0.8, 1)
                btn.setScale(1.0)
    
    def _confirm_selection(self):
        """Confirm current selection"""
        if not self.keyboard_active:
            return
        
        selected_btn = self.mode_buttons[self.current_selection]
        mode = selected_btn.mode_info['mode']
        self._select_mode(mode)

    def destroy(self):
        """Clean up all UI elements"""
        self.hide()
        for element in self.ui_elements:
            try:
                element.removeNode()
            except:
                pass
        self.ui_elements.clear()