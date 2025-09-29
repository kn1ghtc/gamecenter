from direct.gui.DirectGui import DirectWaitBar, DirectFrame, DirectButton
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, ClockObject, CardMaker, TransparencyAttrib, Vec4


class HUD:
    def __init__(self, base):
        self.base = base
        
        # Create UI background frame with proper layering
        self.ui_root = DirectFrame(
            frameColor=(0, 0, 0, 0),  # Transparent background
            frameSize=(-1, 1, -1, 1),
            parent=base.render2d
        )
        self.ui_root.setBin("gui-popup", 0)  # Ensure proper UI layering
        
        # Timer display at the top center - remove solid background to avoid遮挡
        self.timer_bg = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.1, 0.1, -0.06, 0.06),
            pos=(0, 0, 0.95),
            parent=self.ui_root
        )
        self.timer_bg.setBin("gui-popup", 100)
        
        self.timer_text = OnscreenText(
            text='99', 
            pos=(0, 0.92), 
            scale=0.06, 
            align=TextNode.ACenter,
            fg=(1, 1, 1, 1), 
            shadow=(0, 0, 0, 1),
            parent=self.ui_root
        )
        self.timer_text.setBin("gui-popup", 101)  # Above timer background
        self.game_time = 99.0  # 99 seconds per round (classic fighting game style)
        try:
            print("[HUD] Timer background alpha=0 (transparent), text on gui-popup bin 101")
        except Exception:
            pass
        
        # Round display - positioned below timer
        self.round_text = OnscreenText(
            text='ROUND 1', 
            pos=(0, 0.85), 
            scale=0.04, 
            align=TextNode.ACenter,
            fg=(1, 1, 0.5, 1), 
            shadow=(0, 0, 0, 1),
            parent=self.ui_root
        )
        self.round_text.setBin("gui-popup", 90)
        
        # Modern Fighting Game UI Layout - Top-aligned health bars
        # Player 1 Health Bar (Left Side)
        # Remove dark background under health bars to prevent gray strips
        self.p1_health_bg = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.4, 0.01, -0.04, 0.04),
            pos=(-0.35, 0, 0.9),
            parent=self.ui_root
        )
        self.p1_health_bg.setBin("gui-popup", 20)
        try:
            print("[HUD] P1 health background alpha=0 (transparent)")
        except Exception:
            pass
        
        self.bar_p0 = DirectWaitBar(
            text='', value=100, range=100, 
            pos=(-0.35, 0, 0.9), scale=(0.4, 1, 0.07),
            barColor=(0.1, 0.8, 0.3, 1),  # Green health bar
            frameColor=(0, 0, 0, 0),
            borderWidth=(0.01, 0.01),
            parent=self.ui_root
        )
        self.bar_p0.setBin("gui-popup", 25)
        
        # Player 1 Name and Info (Top Left)
        self.name_p0 = OnscreenText(
            text='PLAYER 1', 
            pos=(-0.75, 0.95), 
            scale=0.04, 
            align=TextNode.ALeft, 
            fg=(0.2, 1, 0.5, 1), 
            shadow=(0, 0, 0, 1),
            parent=self.ui_root
        )
        self.name_p0.setBin("gui-popup", 30)
        
        # Player 2 Health Bar (Right Side) 
        self.p2_health_bg = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.01, 0.4, -0.04, 0.04),
            pos=(0.35, 0, 0.9),
            parent=self.ui_root
        )
        self.p2_health_bg.setBin("gui-popup", 20)
        try:
            print("[HUD] P2 health background alpha=0 (transparent)")
        except Exception:
            pass
        
        self.bar_p1 = DirectWaitBar(
            text='', value=100, range=100, 
            pos=(0.35, 0, 0.9), scale=(0.4, 1, 0.07),
            barColor=(0.9, 0.2, 0.1, 1),  # Red health bar
            frameColor=(0, 0, 0, 0),
            borderWidth=(0.01, 0.01),
            parent=self.ui_root
        )
        self.bar_p1.setBin("gui-popup", 25)
        
        # Player 2 Name and Info (Top Right)
        self.name_p1 = OnscreenText(
            text='PLAYER 2', 
            pos=(0.75, 0.95), 
            scale=0.04, 
            align=TextNode.ARight, 
            fg=(1, 0.3, 0.2, 1), 
            shadow=(0, 0, 0, 1),
            parent=self.ui_root
        )
        self.name_p1.setBin("gui-popup", 30)
        
        # Character portraits - positioned next to health bars
        self.portrait_p0 = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.08, 0.08, -0.08, 0.08),
            pos=(-0.85, 0, 0.9),
            parent=self.ui_root
        )
        self.portrait_p0.setBin("gui-popup", 35)
        
        self.portrait_p1 = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.08, 0.08, -0.08, 0.08),
            pos=(0.85, 0, 0.9),
            parent=self.ui_root
        )
        self.portrait_p1.setBin("gui-popup", 35)
        
        # Character info displays - positioned below health bars
        self.char_info_p0 = OnscreenText(
            text='', 
            pos=(-0.75, 0.82), 
            scale=0.03, 
            align=TextNode.ALeft, 
            fg=(0.7, 0.9, 1, 1), 
            shadow=(0, 0, 0, 0.8),
            parent=self.ui_root
        )
        self.char_info_p0.setBin("gui-popup", 30)
        
        self.char_info_p1 = OnscreenText(
            text='', 
            pos=(0.75, 0.82), 
            scale=0.03, 
            align=TextNode.ARight, 
            fg=(1, 0.8, 0.6, 1), 
            shadow=(0, 0, 0, 0.8),
            parent=self.ui_root
        )
        self.char_info_p1.setBin("gui-popup", 30)
        
        # Combo meter (center, below timer)
        self.combo = DirectWaitBar(
            text='COMBO', value=0, range=10, 
            pos=(0, 0, 0.5), scale=0.2,
            barColor=(1, 1, 0.2, 1), 
            frameColor=(0.2, 0.2, 0.05, 0.8),
            borderWidth=(0.01, 0.01),
            parent=self.ui_root
        )
        self.combo.setBin("gui-popup", 40)
        self.combo.hide()
        self.combo_timer = 0.0
        
        # Game state displays
        self.state_text = OnscreenText(
            text='', 
            pos=(0, 0.3), 
            scale=0.08, 
            align=TextNode.ACenter,
            fg=(1, 1, 1, 1), 
            shadow=(0, 0, 0, 1),
            parent=self.ui_root
        )
        self.state_text.setBin("gui-popup", 80)
        self.state_text.hide()
        
        # Victory/defeat display
        self.result_text = OnscreenText(
            text='', 
            pos=(0, 0), 
            scale=0.12, 
            align=TextNode.ACenter,
            fg=(1, 1, 0.3, 1), 
            shadow=(0, 0, 0, 1),
            parent=self.ui_root
        )
        self.result_text.setBin("gui-popup", 90)
        self.result_text.hide()
        
        # internal targets for smooth transitions
        self._target_p0 = 100.0
        self._target_p1 = 100.0
        self._smooth_speed = 8.0
        
        # hit flash overlay - redesigned with proper transparency
        try:
            self._flash = DirectFrame(
                frameColor=(1, 0.3, 0.3, 0), 
                frameSize=(-1, 1, -1, 1), 
                parent=self.ui_root
            )
            self._flash.setTransparency(TransparencyAttrib.MAlpha)
            self._flash.setBin("gui-popup", 200)  # Top layer for flash effects
            self._flash_alpha = 0.0
        except Exception:
            self._flash = None
            self._flash_alpha = 0.0

    def update(self, players, game_time=None, game_state=None):
        try:
            # 安全检查players列表
            if not players or len(players) < 2:
                # 如果没有足够的玩家，暂时隐藏UI元素
                if hasattr(self, 'bar_p0'):
                    self.bar_p0.hide()
                if hasattr(self, 'bar_p1'):
                    self.bar_p1.hide()
                if hasattr(self, 'name_p0'):
                    self.name_p0.setText("WAITING...")
                if hasattr(self, 'name_p1'):
                    self.name_p1.setText("WAITING...")
                return
            
            # 确保UI元素可见
            if hasattr(self, 'bar_p0'):
                self.bar_p0.show()
            if hasattr(self, 'bar_p1'):
                self.bar_p1.show()
            
            p0 = players[0]
            p1 = players[1]
            
            # Update timer
            if game_time is not None:
                self.game_time = game_time
                minutes = int(self.game_time // 60)
                seconds = int(self.game_time % 60)
                if minutes > 0:
                    timer_text = f"{minutes}:{seconds:02d}"
                else:
                    timer_text = f"{seconds}"
                self.timer_text.setText(timer_text)
                
                # Change timer color based on remaining time
                if self.game_time <= 10:
                    self.timer_text.setFg(Vec4(1, 0.2, 0.2, 1))  # Red when low
                elif self.game_time <= 30:
                    self.timer_text.setFg(Vec4(1, 0.8, 0.2, 1))  # Orange when medium
                else:
                    self.timer_text.setFg(Vec4(1, 1, 0.2, 1))    # Yellow when high
            
            # Update game state display
            if game_state:
                if game_state == "READY":
                    self.state_text.setText("READY?")
                    self.state_text.show()
                elif game_state == "FIGHT":
                    self.state_text.setText("FIGHT!")
                    self.state_text.show()
                elif game_state == "ROUND_END":
                    self.state_text.hide()
                elif game_state == "GAME_OVER":
                    self.state_text.hide()
                else:
                    self.state_text.hide()
            
            # smooth interpolation towards target health values
            self._target_p0 = float(p0.health)
            self._target_p1 = float(p1.health)
            cur0 = float(self.bar_p0['value'])
            cur1 = float(self.bar_p1['value'])
            
            try:
                dt = ClockObject.getGlobalClock().getDt()
            except Exception:
                dt = 1/60.0
            
            t = min(1.0, dt * self._smooth_speed)
            new0 = cur0 + (self._target_p0 - cur0) * t
            new1 = cur1 + (self._target_p1 - cur1) * t
            self.bar_p0['value'] = new0
            self.bar_p1['value'] = new1
            
            # Update player names
            self.name_p0.setText(getattr(p0, 'character_name', p0.name))
            self.name_p1.setText(getattr(p1, 'character_name', p1.name))
            
            # combo meter logic: show if combo > 1, fade out after timer
            active_combo = 0
            if hasattr(p0, 'combo') and p0.combo > 1:
                active_combo = p0.combo
            elif hasattr(p1, 'combo') and p1.combo > 1:
                active_combo = p1.combo
            
            if active_combo > 1:
                self.combo['value'] = min(active_combo, 10)
                self.combo['text'] = f'COMBO {active_combo}'
                self.combo.show()
                self.combo_timer = 1.5
            elif self.combo_timer > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0:
                    self.combo.hide()
                    
        except Exception as e:
            print(f"UI update error: {e}")
            pass

    def on_hit(self, intensity=0.8, duration=0.18):
        try:
            if not self._flash:
                return
            # set alpha and schedule fade
            self._flash_alpha = float(intensity)
            self._flash.setColorScale(1, 0.6, 0.6, self._flash_alpha)
            # schedule fade via a task
            def _fade(task):
                try:
                    dt = ClockObject.getGlobalClock().getDt()
                    self._flash_alpha -= dt / max(0.001, duration)
                    if self._flash_alpha <= 0:
                        self._flash_alpha = 0.0
                        self._flash.setColorScale(1, 1, 1, 0)
                        return task.done
                    self._flash.setColorScale(1, 0.6, 0.6, max(0.0, self._flash_alpha))
                    return task.cont
                except Exception:
                    return task.done
            # remove previous same-named task and add
            try:
                self.base.taskMgr.remove('hud-flash')
            except Exception:
                pass
            self.base.taskMgr.add(_fade, 'hud-flash')
        except Exception:
            pass
    
    def _load_character_portrait(self, character_name: str):
        """Load character portrait image"""
        if not character_name:
            return None
            
        # Convert character name to ID format
        char_id = character_name.lower().replace(' ', '_')
        
        # Try different portrait paths
        import os
        from pathlib import Path
        
        assets_dir = Path(__file__).parent / "assets"
        portraits_dir = assets_dir / "images" / "portraits"
        
        portrait_candidates = [
            portraits_dir / f"{char_id}.png",
            portraits_dir / f"{char_id}_official.png",
            portraits_dir / f"{character_name.replace(' ', '_')}.png",
        ]
        
        for portrait_path in portrait_candidates:
            if portrait_path.exists():
                try:
                    # Load texture using Panda3D
                    from panda3d.core import Texture, PNMImage, Filename
                    
                    img = PNMImage()
                    if img.read(Filename.fromOsSpecific(str(portrait_path))):
                        tex = Texture()
                        tex.load(img)
                        tex.setMagfilter(Texture.FTLinear)
                        tex.setMinfilter(Texture.FTLinearMipmapLinear)
                        print(f"[HUD] Loaded portrait: {portrait_path}")
                        return tex
                except Exception as e:
                    print(f"[HUD] Failed to load portrait {portrait_path}: {e}")
                    continue
        
        print(f"[HUD] No portrait found for {character_name} ({char_id})")
        return None
    
    def _set_portrait(self, portrait_frame, texture):
        """Set portrait texture to frame"""
        if not texture or not portrait_frame:
            return
            
        try:
            from panda3d.core import CardMaker
            
            # Clear existing portrait
            for child in portrait_frame.getChildren():
                child.removeNode()
            
            # Create card for portrait
            cm = CardMaker('portrait_card')
            cm.setFrame(-1, 1, -1, 1)  # Frame coordinates
            
            portrait_card = portrait_frame.attachNewNode(cm.generate())
            portrait_card.setTexture(texture)
            portrait_card.setTransparency(1)  # Enable transparency
            
            print(f"[HUD] Portrait texture applied successfully")
            
        except Exception as e:
            print(f"[HUD] Failed to set portrait: {e}")
    
    def update_character_info(self, players):
        """Update character information display and portraits"""
        try:
            if len(players) >= 2:
                p0, p1 = players[0], players[1]
                
                # Update P1 character info and portrait
                char_data_p0 = getattr(p0, 'character_data', None)
                char_name_p0 = getattr(p0, 'character_name', p0.name if hasattr(p0, 'name') else 'Player 1')
                
                if hasattr(p0, 'character_name') and isinstance(char_data_p0, dict):
                    fighting_style = char_data_p0.get('fighting_style', 'Unknown Style')
                    nationality = char_data_p0.get('nationality', 'Unknown')
                    info_text = f"{fighting_style}\n{nationality}"
                    self.char_info_p0.setText(info_text)
                else:
                    self.char_info_p0.setText("Street Fighter\nUnknown")
                
                # Load and set P1 portrait
                if not hasattr(self, '_p0_portrait_loaded') or self._p0_portrait_loaded != char_name_p0:
                    portrait_tex_p0 = self._load_character_portrait(char_name_p0)
                    if portrait_tex_p0:
                        self._set_portrait(self.portrait_p0, portrait_tex_p0)
                        self._p0_portrait_loaded = char_name_p0
                
                # Update P2 character info and portrait
                char_data_p1 = getattr(p1, 'character_data', None)
                char_name_p1 = getattr(p1, 'character_name', p1.name if hasattr(p1, 'name') else 'Player 2')
                
                if hasattr(p1, 'character_name') and isinstance(char_data_p1, dict):
                    fighting_style = char_data_p1.get('fighting_style', 'Unknown Style')
                    nationality = char_data_p1.get('nationality', 'Unknown')
                    info_text = f"{fighting_style}\n{nationality}"
                    self.char_info_p1.setText(info_text)
                else:
                    self.char_info_p1.setText("Street Fighter\nUnknown")
                
                # Load and set P2 portrait
                if not hasattr(self, '_p1_portrait_loaded') or self._p1_portrait_loaded != char_name_p1:
                    portrait_tex_p1 = self._load_character_portrait(char_name_p1)
                    if portrait_tex_p1:
                        self._set_portrait(self.portrait_p1, portrait_tex_p1)
                        self._p1_portrait_loaded = char_name_p1
                        
        except Exception as e:
            print(f"Failed to update character info: {e}")
    
    def show_round_start(self, round_num):
        """Display round start animation"""
        try:
            self.round_text.setText(f"ROUND {round_num}")
            self.state_text.setText("READY?")
            self.state_text.show()
            
            # Schedule FIGHT display after 2 seconds
            def show_fight():
                self.state_text.setText("FIGHT!")
                # Hide after 1 second
                def hide_state():
                    self.state_text.hide()
                self.base.taskMgr.doMethodLater(1.0, lambda task: hide_state(), 'hide-fight-text')
            
            self.base.taskMgr.doMethodLater(2.0, lambda task: show_fight(), 'show-fight-text')
        except Exception as e:
            print(f"Round start display error: {e}")
    
    def show_game_result(self, winner_name, result_type="KO"):
        """Display game end result"""
        try:
            if result_type == "TIME_UP":
                self.result_text.setText(f"TIME UP!\n{winner_name} WINS!")
            elif result_type == "KO":
                self.result_text.setText(f"K.O.!\n{winner_name} WINS!")
            else:
                self.result_text.setText(f"{winner_name} WINS!")
            
            self.result_text.show()
            
            # Add victory animation effect
            def victory_flash(task):
                import math
                t = task.time
                alpha = 0.5 + 0.5 * math.sin(t * 8)
                self.result_text.setFg(Vec4(1, 1, 0.3, alpha))
                if t < 3.0:  # Flash for 3 seconds
                    return task.cont
                return task.done
            
            self.base.taskMgr.add(victory_flash, 'victory-flash')
            
        except Exception as e:
            print(f"Game result display error: {e}")
    
    def hide_result(self):
        """Hide game result display"""
        try:
            self.result_text.hide()
            self.base.taskMgr.remove('victory-flash')
        except Exception:
            pass