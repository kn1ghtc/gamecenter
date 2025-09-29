"""
KOF Animation System - Complete Animation Management for 3D Characters
Handles GLTF/BAM animations, KOF-style special moves, and character-specific animations
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
from direct.interval.LerpInterval import LerpPosInterval, LerpHprInterval, LerpScaleInterval, LerpColorScaleInterval
from panda3d.core import Vec3, Vec4, NodePath
import math
import random

class KOFAnimationSystem:
    """Complete KOF-style animation system for 3D characters"""
    
    def __init__(self, base):
        self.base = base
        self.characters = {}  # character_id -> character data
        self.active_animations = {}  # character_id -> active animation
        self.animation_states = {}  # character_id -> current state
        
        # Animation timing (KOF-style)
        self.frame_duration = 1/60  # 60 FPS like KOF
        
        # Standard KOF animation frames
        self.kof_timings = {
            'idle': {'frames': 60, 'loop': True},
            'walk_forward': {'frames': 20, 'loop': True},
            'walk_backward': {'frames': 24, 'loop': True},
            'jump_neutral': {'frames': 30, 'loop': False},
            'jump_forward': {'frames': 32, 'loop': False},
            'jump_backward': {'frames': 32, 'loop': False},
            'crouch': {'frames': 8, 'loop': False},
            'block_stand': {'frames': 4, 'loop': False},
            'block_crouch': {'frames': 4, 'loop': False},
            'light_punch': {'frames': 12, 'loop': False},
            'heavy_punch': {'frames': 18, 'loop': False},
            'light_kick': {'frames': 14, 'loop': False},
            'heavy_kick': {'frames': 22, 'loop': False},
            'special_move_1': {'frames': 35, 'loop': False},
            'special_move_2': {'frames': 45, 'loop': False},
            'super_move': {'frames': 60, 'loop': False},
            'hit_light': {'frames': 10, 'loop': False},
            'hit_heavy': {'frames': 16, 'loop': False},
            'knockdown': {'frames': 40, 'loop': False},
            'victory': {'frames': 80, 'loop': False},
            'defeat': {'frames': 60, 'loop': False}
        }
        
        # KOF-style movement parameters
        self.movement_params = {
            'walk_speed': 2.0,
            'run_speed': 4.5,
            'jump_height': 3.0,
            'jump_distance': 2.5,
            'dash_distance': 1.5,
            'backdash_distance': 1.2
        }
        
        # Load character-specific animation data
        self._load_character_animations()
        
        print("KOF Animation System initialized")
    
    def _load_character_animations(self):
        """Load character-specific animation configurations"""
        try:
            assets_dir = Path(__file__).parent / "assets"
            
            # Try complete configuration first
            complete_config_path = assets_dir / "character_animations_complete.json"
            fallback_config_path = assets_dir / "character_animations.json"
            
            if complete_config_path.exists():
                config_path = complete_config_path
                config_type = "complete configuration"
            elif fallback_config_path.exists():
                config_path = fallback_config_path
                config_type = "fallback"
            else:
                # Create default configuration
                self.character_animations = self._create_default_animation_config()
                config_path = fallback_config_path
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.character_animations, f, indent=2, ensure_ascii=False)
                print(f"Created default animation configuration with {len(self.character_animations)} characters")
                return
                
            with open(config_path, 'r', encoding='utf-8') as f:
                self.character_animations = json.load(f)
            print(f"Loaded {config_type} animation configuration: {len(self.character_animations)} characters")
            
        except Exception as e:
            print(f"Warning: Could not load character animations: {e}")
            self.character_animations = self._create_default_animation_config()
    
    def _create_default_animation_config(self):
        """Create default animation configuration for all characters"""
        config = {}
        
        # Standard KOF characters with known move sets
        kof_characters = [
            "kyo_kusanagi", "iori_yagami", "terry_bogard", "mai_shiranui",
            "ryo_sakazaki", "robert_garcia", "leona_heidern", "athena_asamiya",
            "sie_kensou", "joe_higashi", "andy_bogard", "goro_daimon",
            "yuri_sakazaki", "choi_bounge", "saisyu_kusanagi", "geese_howard",
            "wolfgang_krauser", "mr_big", "chizuru_kagura", "mature", "vice",
            "shermie", "chris", "shingo_yabuki", "orochi", "k_dash", "maxima",
            "whip", "lin", "vanessa", "ramon", "kula_diamond", "angel", "igniz",
            "ash_crimson", "b_jenet", "gato", "magaki", "shunei", "nakoruru",
            "isla", "dolores"
        ]
        
        for char_id in kof_characters:
            config[char_id] = self._create_character_animation_set(char_id)
        
        return config
    
    def _create_character_animation_set(self, char_id):
        """Create animation set for a specific character"""
        # Base animation set
        animations = {
            'idle': {'file': 'idle.bam', 'loop': True, 'speed': 1.0},
            'walk': {'file': 'walk.bam', 'loop': True, 'speed': 1.2},
            'run': {'file': 'run.bam', 'loop': True, 'speed': 1.5},
            'jump': {'file': 'jump.bam', 'loop': False, 'speed': 1.0},
            'crouch': {'file': 'crouch.bam', 'loop': False, 'speed': 1.0},
            'block': {'file': 'block.bam', 'loop': False, 'speed': 1.0},
            'light_attack': {'file': 'light_punch.bam', 'loop': False, 'speed': 1.3},
            'heavy_attack': {'file': 'heavy_punch.bam', 'loop': False, 'speed': 1.1},
            'light_kick': {'file': 'light_kick.bam', 'loop': False, 'speed': 1.2},
            'heavy_kick': {'file': 'heavy_kick.bam', 'loop': False, 'speed': 1.0},
            'hit_light': {'file': 'hit_light.bam', 'loop': False, 'speed': 1.5},
            'hit_heavy': {'file': 'hit_heavy.bam', 'loop': False, 'speed': 1.2},
            'knockdown': {'file': 'knockdown.bam', 'loop': False, 'speed': 1.0},
            'victory': {'file': 'victory.bam', 'loop': False, 'speed': 0.8},
            'defeat': {'file': 'defeat.bam', 'loop': False, 'speed': 1.0}
        }
        
        # Character-specific special moves
        special_moves = self._get_character_special_moves(char_id)
        animations.update(special_moves)
        
        return {
            'animations': animations,
            'special_properties': self._get_character_properties(char_id)
        }
    
    def _get_character_special_moves(self, char_id):
        """Get character-specific special moves"""
        special_moves = {}
        
        if char_id == "kyo_kusanagi":
            special_moves.update({
                'fireball': {'file': 'kyo_fireball.bam', 'loop': False, 'speed': 1.0},
                'dp_punch': {'file': 'kyo_dp.bam', 'loop': False, 'speed': 1.2},
                'rekka_ken': {'file': 'kyo_rekka.bam', 'loop': False, 'speed': 1.1},
                'super_fireball': {'file': 'kyo_super.bam', 'loop': False, 'speed': 0.9}
            })
        elif char_id == "iori_yagami":
            special_moves.update({
                'fireball': {'file': 'iori_fireball.bam', 'loop': False, 'speed': 1.0},
                'dp_punch': {'file': 'iori_dp.bam', 'loop': False, 'speed': 1.2},
                'command_grab': {'file': 'iori_grab.bam', 'loop': False, 'speed': 1.0},
                'super_grab': {'file': 'iori_super.bam', 'loop': False, 'speed': 0.8}
            })
        elif char_id == "terry_bogard":
            special_moves.update({
                'power_wave': {'file': 'terry_wave.bam', 'loop': False, 'speed': 1.0},
                'burn_knuckle': {'file': 'terry_knuckle.bam', 'loop': False, 'speed': 1.1},
                'crack_shoot': {'file': 'terry_crack.bam', 'loop': False, 'speed': 1.2},
                'power_geyser': {'file': 'terry_geyser.bam', 'loop': False, 'speed': 0.9}
            })
        elif char_id == "mai_shiranui":
            special_moves.update({
                'fan_throw': {'file': 'mai_fan.bam', 'loop': False, 'speed': 1.1},
                'phoenix_dance': {'file': 'mai_phoenix.bam', 'loop': False, 'speed': 1.0},
                'butterfly_fan': {'file': 'mai_butterfly.bam', 'loop': False, 'speed': 1.2},
                'super_phoenix': {'file': 'mai_super.bam', 'loop': False, 'speed': 0.8}
            })
        
        # Add generic special moves for characters without specific ones
        if not special_moves:
            special_moves = {
                'special_1': {'file': 'special_1.bam', 'loop': False, 'speed': 1.0},
                'special_2': {'file': 'special_2.bam', 'loop': False, 'speed': 1.1},
                'super_move': {'file': 'super_move.bam', 'loop': False, 'speed': 0.9}
            }
        
        return special_moves
    
    def _get_character_properties(self, char_id):
        """Get character-specific properties"""
        # Default properties
        properties = {
            'walk_speed': 1.0,
            'jump_height': 1.0,
            'attack_speed': 1.0,
            'defense': 1.0,
            'special_meter_gain': 1.0
        }
        
        # Character-specific modifications
        if char_id in ["goro_daimon", "wolfgang_krauser", "maxima"]:
            # Heavy characters
            properties.update({
                'walk_speed': 0.8,
                'jump_height': 0.7,
                'attack_speed': 0.9,
                'defense': 1.3
            })
        elif char_id in ["choi_bounge", "yuri_sakazaki", "kula_diamond"]:
            # Fast characters
            properties.update({
                'walk_speed': 1.3,
                'jump_height': 1.2,
                'attack_speed': 1.2,
                'defense': 0.8
            })
        elif char_id in ["kyo_kusanagi", "iori_yagami", "terry_bogard"]:
            # Balanced protagonists
            properties.update({
                'walk_speed': 1.1,
                'jump_height': 1.0,
                'attack_speed': 1.1,
                'defense': 1.0,
                'special_meter_gain': 1.2
            })
        
        return properties
    
    def register_character(self, char_id, model_node, actor=None):
        """Register a character for animation management"""
        try:
            # Try to load as Actor first (for BAM files with animations)
            character_data = {
                'id': char_id,
                'model': model_node,
                'actor': actor,
                'current_animation': 'idle',
                'animation_speed': 1.0,
                'properties': self.character_animations.get(char_id, {}).get('special_properties', {}),
                'available_animations': set()
            }
            
            # Scan for available animation files
            self._scan_character_animations(char_id, character_data)
            
            self.characters[char_id] = character_data
            self.animation_states[char_id] = {
                'state': 'idle',
                'frame': 0,
                'loop_count': 0,
                'blend_weight': 1.0
            }
            
            # Start idle animation
            self.play_animation(char_id, 'idle')
            
            print(f"Registered character {char_id} with {len(character_data['available_animations'])} animations")
            
        except Exception as e:
            print(f"Error registering character {char_id}: {e}")
    
    def _scan_character_animations(self, char_id, character_data):
        """Scan for available animation files for a character"""
        available_animations = set()
        
        # First, try to get animations directly from the Actor
        actor = character_data.get('actor')
        if actor and hasattr(actor, 'getAnimNames'):
            try:
                actor_animations = actor.getAnimNames()
                if actor_animations:
                    available_animations.update(actor_animations)
                    print(f"🎭 Found {len(actor_animations)} animations in Actor for {char_id}: {list(actor_animations)}")
            except Exception as e:
                print(f"Could not get animations from Actor for {char_id}: {e}")
        
        # Also scan filesystem for additional animations
        char_dir = Path(__file__).parent / "assets" / "characters" / char_id
        search_paths = [
            char_dir / "sketchfab" / "animations",
            char_dir / "animations",
            char_dir / "sketchfab"
        ]
        
        for path in search_paths:
            if path.exists():
                # Look for BAM animation files
                for bam_file in path.glob("*.bam"):
                    anim_name = bam_file.stem
                    if anim_name != char_id:  # Skip the main character file
                        available_animations.add(anim_name)
                
                # Look for GLTF animations (extract from main file)
                gltf_file = path / "scene.gltf"
                if gltf_file.exists():
                    try:
                        with open(gltf_file, 'r') as f:
                            gltf_data = json.load(f)
                        
                        # Extract animation names from GLTF
                        if 'animations' in gltf_data:
                            for anim in gltf_data['animations']:
                                if 'name' in anim:
                                    available_animations.add(anim['name'])
                    except Exception as e:
                        print(f"Could not parse GLTF animations for {char_id}: {e}")
        
        character_data['available_animations'] = available_animations
        
        # If no specific animations found, use defaults for procedural animation
        if not available_animations:
            available_animations = {
                'idle', 'walk', 'attack', 'hit', 'victory', 'defeat'
            }
            character_data['available_animations'] = available_animations
            print(f"🤖 No specific animations found for {char_id}, using procedural defaults")
        else:
            print(f"✅ Total {len(available_animations)} animations available for {char_id}")
    
    def play_animation(self, char_id, animation_name, loop=None, speed=1.0, blend_time=0.1):
        """Play a specific animation for a character"""
        if char_id not in self.characters:
            print(f"Character {char_id} not registered")
            return False
        
        character = self.characters[char_id]
        actor = character['actor']
        model = character['model']
        
        # Stop current animation
        self.stop_animation(char_id)
        
        try:
            # Try to play the animation if it's an Actor
            if actor and hasattr(actor, 'play'):
                # Map common animation names to available ones
                actual_anim_name = self._map_animation_name(char_id, animation_name)
                
                if actual_anim_name and actual_anim_name in character['available_animations']:
                    # Play the actual animation
                    if loop is None:
                        loop = self._should_loop_animation(animation_name)
                    
                    if loop:
                        actor.loop(actual_anim_name)
                    else:
                        actor.play(actual_anim_name)
                    
                    if speed != 1.0:
                        actor.setPlayRate(speed, actual_anim_name)
                    
                    character['current_animation'] = animation_name
                    character['animation_speed'] = speed
                    
                    # Update animation state
                    self.animation_states[char_id]['state'] = animation_name
                    self.animation_states[char_id]['frame'] = 0
                    
                    print(f"🎭 Playing animation '{actual_anim_name}' for {char_id} (requested: {animation_name})")
                    return True
                else:
                    print(f"⚠️  Animation '{animation_name}' not found for {char_id}, using procedural")
                    # Fallback to procedural animation
                    return self._play_procedural_animation(char_id, animation_name, loop, speed)
            else:
                # Use procedural animation for non-Actor models
                print(f"🤖 Using procedural animation for {char_id} ({animation_name})")
                return self._play_procedural_animation(char_id, animation_name, loop, speed)
                
        except Exception as e:
            print(f"❌ Error playing animation {animation_name} for {char_id}: {e}")
            return self._play_procedural_animation(char_id, animation_name, loop, speed)
    
    def _map_animation_name(self, char_id, animation_name):
        """Map requested animation name to available animation"""
        character = self.characters[char_id]
        available = character['available_animations']
        
        if not available:
            return None
            
        # Direct match (case insensitive)
        for anim in available:
            if anim.lower() == animation_name.lower():
                return anim
        
        # Enhanced mappings with common 3D model animation names
        mapping = {
            'idle': ['idle', 'stand', 'neutral', 'standby', 'rest', 'breathing', 'stance'],
            'walk': ['walk', 'move', 'walking', 'forward', 'step', 'advance'],
            'run': ['run', 'running', 'dash', 'sprint', 'charge'],
            'attack': ['attack', 'punch', 'light_punch', 'light_attack', 'jab', 'strike', 'hit', 'combo1'],
            'heavy_attack': ['heavy_punch', 'strong_punch', 'heavy_attack', 'power_punch', 'combo2', 'uppercut'],
            'kick': ['kick', 'light_kick', 'low_kick', 'front_kick'],
            'heavy_kick': ['heavy_kick', 'strong_kick', 'high_kick', 'roundhouse'],
            'jump': ['jump', 'jumping', 'leap', 'hop', 'air'],
            'hit': ['hit', 'hurt', 'damage', 'pain', 'stun', 'flinch'],
            'block': ['block', 'guard', 'blocking', 'defend', 'parry'],
            'victory': ['victory', 'win', 'celebrate', 'cheer', 'triumph', 'pose'],
            'defeat': ['defeat', 'lose', 'ko', 'death', 'down', 'fall', 'knocked']
        }
        
        # Try to find a suitable match (case insensitive)
        candidates = mapping.get(animation_name, [animation_name])
        for candidate in candidates:
            for anim in available:
                if candidate.lower() in anim.lower() or anim.lower() in candidate.lower():
                    return anim
        
        # Partial match fallback
        for candidate in candidates:
            for anim in available:
                # Check if any word in candidate matches any word in anim
                candidate_words = candidate.lower().split('_')
                anim_words = anim.lower().split('_')
                if any(word in anim_words for word in candidate_words):
                    return anim
        
        # Return the first available animation as ultimate fallback
        if available:
            fallback = list(available)[0]
            print(f"🔄 Using fallback animation '{fallback}' for requested '{animation_name}' on {char_id}")
            return fallback
        
        return None
    
    def _should_loop_animation(self, animation_name):
        """Determine if an animation should loop"""
        looping_animations = {
            'idle', 'walk', 'run', 'block', 'crouch'
        }
        return animation_name in looping_animations
    
    def _play_procedural_animation(self, char_id, animation_name, loop, speed):
        """Play procedural animation for characters without BAM animations"""
        character = self.characters[char_id]
        model = character['model']
        
        if not model:
            return False
        
        # Create procedural animations based on type
        animation_sequence = None
        
        if animation_name == 'idle':
            animation_sequence = self._create_idle_animation(model, speed)
        elif animation_name in ['walk', 'run']:
            animation_sequence = self._create_walk_animation(model, speed)
        elif animation_name in ['attack', 'light_attack', 'heavy_attack']:
            animation_sequence = self._create_attack_animation(model, animation_name, speed)
        elif animation_name == 'hit':
            animation_sequence = self._create_hit_animation(model, speed)
        elif animation_name == 'jump':
            animation_sequence = self._create_jump_animation(model, speed)
        elif animation_name == 'victory':
            animation_sequence = self._create_victory_animation(model, speed)
        elif animation_name == 'defeat':
            animation_sequence = self._create_defeat_animation(model, speed)
        
        if animation_sequence:
            # Stop any existing animation
            if char_id in self.active_animations:
                self.active_animations[char_id].pause()
            
            # Start new animation
            if loop:
                animation_sequence.loop()
            else:
                animation_sequence.start()
                # Set up callback to return to idle
                def return_to_idle():
                    if char_id in self.characters:
                        self.play_animation(char_id, 'idle')
                
                animation_sequence.setDoneEvent(f'anim_done_{char_id}')
                self.base.accept(f'anim_done_{char_id}', return_to_idle)
            
            self.active_animations[char_id] = animation_sequence
            character['current_animation'] = animation_name
            
            return True
        
        return False
    
    def _create_idle_animation(self, model, speed):
        """Create enhanced KOF-style idle animation"""
        if not model:
            return None
            
        # Enhanced breathing and stance with character personality
        original_pos = model.getPos()
        original_hpr = model.getHpr()
        original_scale = model.getScale()
        
        # Subtle breathing effect
        breath_up = LerpPosInterval(model, 1.2/speed, 
                                   original_pos + Vec3(0, 0, 0.03))
        breath_down = LerpPosInterval(model, 1.0/speed, 
                                     original_pos + Vec3(0, 0, -0.01))
        breath_return = LerpPosInterval(model, 0.8/speed, original_pos)
        
        # Stance adjustment with personality
        sway_left = LerpHprInterval(model, 2.0/speed, 
                                   original_hpr + Vec3(-2, 0, 1))
        sway_right = LerpHprInterval(model, 2.2/speed, 
                                    original_hpr + Vec3(2, 1, -1))
        sway_center = LerpHprInterval(model, 1.5/speed, original_hpr)
        
        # Subtle scale pulse for "life"
        scale_up = LerpScaleInterval(model, 1.8/speed, 
                                    original_scale * 1.01)
        scale_down = LerpScaleInterval(model, 1.6/speed, original_scale)
        
        # Combine all elements into a complex idle sequence
        breath_seq = Sequence(breath_up, breath_down, breath_return)
        sway_seq = Sequence(sway_left, sway_right, sway_center)
        scale_seq = Sequence(scale_up, scale_down)
        
        return Parallel(breath_seq, sway_seq, scale_seq)
    
    def _create_walk_animation(self, model, speed):
        """Create enhanced KOF-style walking animation"""
        if not model:
            return None
            
        original_pos = model.getPos()
        original_hpr = model.getHpr()
        
        # More dynamic bouncing walk cycle
        step_up1 = LerpPosInterval(model, 0.2/speed, 
                                  original_pos + Vec3(0, 0, 0.12))
        step_down1 = LerpPosInterval(model, 0.15/speed, 
                                    original_pos + Vec3(0, 0, 0.02))
        step_up2 = LerpPosInterval(model, 0.2/speed, 
                                  original_pos + Vec3(0, 0, 0.10))
        step_down2 = LerpPosInterval(model, 0.15/speed, original_pos)
        
        # Body sway and rhythm
        sway_left = LerpHprInterval(model, 0.35/speed, 
                                   original_hpr + Vec3(-3, -2, 2))
        sway_right = LerpHprInterval(model, 0.35/speed, 
                                    original_hpr + Vec3(3, -1, -2))
        
        # Combine into walking rhythm
        step_sequence = Sequence(step_up1, step_down1, step_up2, step_down2)
        sway_sequence = Sequence(sway_left, sway_right)
        
        return Parallel(step_sequence, sway_sequence)
    
    def _create_attack_animation(self, model, attack_type, speed):
        """Create KOF-style attack animation"""
        if not model:
            return None
            
        original_pos = model.getPos()
        original_hpr = model.getHpr()
        original_scale = model.getScale()
        
        if 'heavy' in attack_type:
            # Heavy attack - longer windup and recovery with dramatic effect
            windup = LerpPosInterval(model, 0.15/speed, 
                                    original_pos + Vec3(0, -0.15, 0.05))
            strike = LerpPosInterval(model, 0.12/speed, 
                                    original_pos + Vec3(0, 0.4, 0.1))
            hold = LerpPosInterval(model, 0.08/speed, 
                                  original_pos + Vec3(0, 0.3, 0.05))
            recover = LerpPosInterval(model, 0.35/speed, original_pos)
            
            # Add dramatic rotation and scale
            wind_rotate = LerpHprInterval(model, 0.15/speed, 
                                         original_hpr + Vec3(0, 0, -15))
            strike_rotate = LerpHprInterval(model, 0.12/speed, 
                                           original_hpr + Vec3(0, 0, 20))
            recover_rotate = LerpHprInterval(model, 0.35/speed, original_hpr)
            
            # Scale for impact effect
            wind_scale = LerpScaleInterval(model, 0.15/speed, 
                                          original_scale * 0.95)
            strike_scale = LerpScaleInterval(model, 0.12/speed, 
                                            original_scale * 1.15)
            recover_scale = LerpScaleInterval(model, 0.35/speed, original_scale)
            
            return Parallel(
                Sequence(windup, strike, hold, recover),
                Sequence(wind_rotate, strike_rotate, recover_rotate),
                Sequence(wind_scale, strike_scale, recover_scale)
            )
        else:
            # Light attack - quick and snappy with subtle effects
            windup = LerpPosInterval(model, 0.06/speed, 
                                    original_pos + Vec3(0, -0.08, 0))
            strike = LerpPosInterval(model, 0.08/speed, 
                                    original_pos + Vec3(0, 0.25, 0.02))
            recover = LerpPosInterval(model, 0.18/speed, original_pos)
            
            # Quick rotation
            wind_rotate = LerpHprInterval(model, 0.06/speed, 
                                         original_hpr + Vec3(0, 0, -8))
            strike_rotate = LerpHprInterval(model, 0.08/speed, 
                                           original_hpr + Vec3(0, 0, 12))
            recover_rotate = LerpHprInterval(model, 0.18/speed, original_hpr)
            
            return Parallel(
                Sequence(windup, strike, recover),
                Sequence(wind_rotate, strike_rotate, recover_rotate)
            )
    
    def _create_hit_animation(self, model, speed):
        """Create enhanced KOF-style hit reaction"""
        if not model:
            return None
            
        original_pos = model.getPos()
        original_hpr = model.getHpr()
        original_scale = model.getScale()
        
        # Enhanced knockback sequence
        initial_knockback = LerpPosInterval(model, 0.08/speed, 
                                           original_pos + Vec3(-0.25, 0, 0.05))
        secondary_knockback = LerpPosInterval(model, 0.06/speed, 
                                             original_pos + Vec3(-0.15, 0, 0))
        recover_pos = LerpPosInterval(model, 0.4/speed, original_pos)
        
        # Hit rotation (recoil effect)
        hit_rotate = LerpHprInterval(model, 0.08/speed, 
                                    original_hpr + Vec3(0, 8, -5))
        recover_rotate = LerpHprInterval(model, 0.4/speed, original_hpr)
        
        # Scale compression for impact
        hit_compress = LerpScaleInterval(model, 0.06/speed, 
                                        original_scale * Vec3(0.9, 1.1, 0.95))
        hit_expand = LerpScaleInterval(model, 0.08/speed, 
                                      original_scale * 1.05)
        recover_scale = LerpScaleInterval(model, 0.3/speed, original_scale)
        
        # Color flash effect
        flash_red = LerpColorScaleInterval(model, 0.05/speed, 
                                          Vec4(1.8, 0.6, 0.6, 1))
        flash_white = LerpColorScaleInterval(model, 0.08/speed, 
                                            Vec4(1.3, 1.3, 1.3, 1))
        flash_normal = LerpColorScaleInterval(model, 0.25/speed, 
                                             Vec4(1, 1, 1, 1))
        
        return Parallel(
            Sequence(initial_knockback, secondary_knockback, recover_pos),
            Sequence(hit_rotate, recover_rotate),
            Sequence(hit_compress, hit_expand, recover_scale),
            Sequence(flash_red, flash_white, flash_normal)
        )
    
    def _create_jump_animation(self, model, speed):
        """Create enhanced KOF-style jump animation"""
        if not model:
            return None
            
        original_pos = model.getPos()
        original_hpr = model.getHpr()
        original_scale = model.getScale()
        
        # Pre-jump crouch with anticipation
        crouch_pos = LerpPosInterval(model, 0.12/speed, 
                                    original_pos + Vec3(0, 0, -0.1))
        crouch_scale = LerpScaleInterval(model, 0.12/speed, 
                                        original_scale * Vec3(1.05, 1.05, 0.75))
        
        # Launch phase
        launch_pos = LerpPosInterval(model, 0.2/speed, 
                                    original_pos + Vec3(0, 0, 1.8))
        launch_scale = LerpScaleInterval(model, 0.15/speed, 
                                        original_scale * Vec3(0.95, 0.95, 1.2))
        launch_rotate = LerpHprInterval(model, 0.2/speed, 
                                       original_hpr + Vec3(0, -5, 0))
        
        # Peak of jump
        peak_pause = LerpPosInterval(model, 0.15/speed, 
                                    original_pos + Vec3(0, 0, 2.0))
        peak_scale = LerpScaleInterval(model, 0.15/speed, original_scale)
        
        # Descent
        descend_pos = LerpPosInterval(model, 0.25/speed, 
                                     original_pos + Vec3(0, 0, 0.1))
        descend_rotate = LerpHprInterval(model, 0.25/speed, original_hpr)
        
        # Landing impact
        land_pos = LerpPosInterval(model, 0.1/speed, original_pos)
        land_scale = LerpScaleInterval(model, 0.08/speed, 
                                      original_scale * Vec3(1.1, 1.1, 0.9))
        recover_scale = LerpScaleInterval(model, 0.12/speed, original_scale)
        
        return Sequence(
            Parallel(crouch_pos, crouch_scale),
            Parallel(launch_pos, launch_scale, launch_rotate),
            Parallel(peak_pause, peak_scale),
            Parallel(descend_pos, descend_rotate),
            Parallel(land_pos, land_scale),
            recover_scale
        )
    
    def _create_victory_animation(self, model, speed):
        """Create enhanced KOF-style victory animation"""
        if not model:
            return None
            
        original_pos = model.getPos()
        original_hpr = model.getHpr()
        original_scale = model.getScale()
        
        # Victory sequence with dramatic flair
        # Phase 1: Victory jump
        jump_up = LerpPosInterval(model, 0.35/speed, 
                                 original_pos + Vec3(0, 0, 0.6))
        jump_scale = LerpScaleInterval(model, 0.35/speed, 
                                      original_scale * 1.1)
        jump_rotate = LerpHprInterval(model, 0.35/speed, 
                                     original_hpr + Vec3(0, 0, 15))
        
        # Phase 2: Land with pose
        land_pos = LerpPosInterval(model, 0.25/speed, original_pos)
        land_scale = LerpScaleInterval(model, 0.25/speed, original_scale)
        pose_rotate = LerpHprInterval(model, 0.25/speed, 
                                     original_hpr + Vec3(0, 0, -20))
        
        # Phase 3: Final triumphant pose
        final_rotate = LerpHprInterval(model, 0.4/speed, original_hpr)
        final_scale = LerpScaleInterval(model, 0.4/speed, 
                                       original_scale * 1.05)
        
        # Phase 4: Victory flash effect
        victory_flash = LerpColorScaleInterval(model, 0.3/speed, 
                                              Vec4(1.5, 1.3, 1.0, 1))
        flash_return = LerpColorScaleInterval(model, 0.5/speed, 
                                             Vec4(1, 1, 1, 1))
        
        return Sequence(
            Parallel(jump_up, jump_scale, jump_rotate),
            Parallel(land_pos, land_scale, pose_rotate),
            Parallel(final_rotate, final_scale, victory_flash),
            flash_return,
            Wait(1.5/speed)
        )
    
    def _create_defeat_animation(self, model, speed):
        """Create enhanced KOF-style defeat animation"""
        if not model:
            return None
            
        original_pos = model.getPos()
        original_hpr = model.getHpr()
        original_scale = model.getScale()
        
        # Defeat sequence with dramatic impact
        # Phase 1: Initial impact stagger
        stagger_back = LerpPosInterval(model, 0.15/speed, 
                                      original_pos + Vec3(-0.2, 0, 0))
        stagger_rotate = LerpHprInterval(model, 0.15/speed, 
                                        original_hpr + Vec3(0, -10, 5))
        impact_compress = LerpScaleInterval(model, 0.15/speed, 
                                           original_scale * Vec3(0.9, 1.1, 0.95))
        
        # Phase 2: Stumble forward
        stumble_forward = LerpPosInterval(model, 0.2/speed, 
                                         original_pos + Vec3(0.1, 0, -0.05))
        stumble_rotate = LerpHprInterval(model, 0.2/speed, 
                                        original_hpr + Vec3(0, 15, -10))
        
        # Phase 3: Final collapse
        collapse_pos = LerpPosInterval(model, 0.8/speed, 
                                      original_pos + Vec3(0, 0, -0.6))
        collapse_rotate = LerpHprInterval(model, 0.8/speed, 
                                         original_hpr + Vec3(0, 85, 0))
        collapse_scale = LerpScaleInterval(model, 0.8/speed, 
                                          original_scale * 0.9)
        
        # Phase 4: Defeat fade
        defeat_fade = LerpColorScaleInterval(model, 1.2/speed, 
                                            Vec4(0.6, 0.6, 0.7, 0.8))
        
        return Sequence(
            Parallel(stagger_back, stagger_rotate, impact_compress),
            Parallel(stumble_forward, stumble_rotate),
            Parallel(collapse_pos, collapse_rotate, collapse_scale, defeat_fade)
        )
    
    def stop_animation(self, char_id):
        """Stop current animation for character"""
        if char_id in self.active_animations:
            animation = self.active_animations[char_id]
            if animation:
                animation.pause()
                animation.finish()
            del self.active_animations[char_id]
        
        # Stop Actor animation
        if char_id in self.characters:
            character = self.characters[char_id]
            actor = character.get('actor')
            if actor and hasattr(actor, 'stop'):
                actor.stop()
    
    def update_animation(self, char_id, player_inputs=None, player_state=None):
        """Update character animation based on inputs and state"""
        if char_id not in self.characters:
            return
        
        character = self.characters[char_id]
        current_anim = character['current_animation']
        
        # Don't interrupt non-interruptible animations
        non_interruptible = {'attack', 'heavy_attack', 'hit', 'victory', 'defeat', 'special_move'}
        if any(anim in current_anim for anim in non_interruptible):
            return
        
        # Determine new animation based on inputs
        new_animation = 'idle'
        
        if player_inputs:
            # Movement
            if player_inputs.get('left') or player_inputs.get('right') or \
               player_inputs.get('up') or player_inputs.get('down'):
                new_animation = 'walk'
            
            # Attacks
            elif player_inputs.get('light'):
                new_animation = 'attack'
            elif player_inputs.get('heavy'):
                new_animation = 'heavy_attack'
            elif player_inputs.get('jump'):
                new_animation = 'jump'
        
        # Only change animation if different
        if new_animation != current_anim:
            self.play_animation(char_id, new_animation)
    
    def play_special_move(self, char_id, move_name):
        """Play a character-specific special move animation"""
        if char_id not in self.characters:
            return False
        
        character = self.characters[char_id]
        char_config = self.character_animations.get(char_id, {})
        special_moves = char_config.get('animations', {})
        
        if move_name in special_moves:
            return self.play_animation(char_id, move_name, loop=False, speed=1.0)
        else:
            # Generic special move animation
            return self.play_animation(char_id, 'special_move', loop=False, speed=1.0)
    
    def cleanup(self):
        """Clean up the animation system"""
        # Stop all animations
        for char_id in list(self.active_animations.keys()):
            self.stop_animation(char_id)
        
        # Clear all data
        self.characters.clear()
        self.active_animations.clear()
        self.animation_states.clear()
        
        print("KOF Animation System cleaned up")