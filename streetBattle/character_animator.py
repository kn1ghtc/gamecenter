"""
Character Animation System for StreetBattle
Handles character animations, facial expressions, and movement effects
"""

from panda3d.core import Vec3, Vec4
from direct.interval.IntervalGlobal import *
from direct.interval.LerpInterval import LerpPosInterval, LerpHprInterval, LerpScaleInterval, LerpColorScaleInterval
import math
import random


class CharacterAnimator:
    """Manages character animations and expressions.

    This animator never moves the character root node. It creates an
    'anim_offset' child under the character and applies visual-only offsets to
    that child so gameplay movement (Player.pos) remains authoritative.
    """
    
    def __init__(self, base):
        self.base = base
        self.active_animations = {}  # character_id -> active animation sequence
        self.animation_states = {}   # character_id -> current state and offset node
        
        # Animation parameters
        self.idle_bob_amplitude = 0.02
        self.idle_bob_period = 2.0
        self.walk_bounce_amplitude = 0.05
        self.walk_bounce_period = 0.8
        
        print("CharacterAnimator initialized")
    
    def register_character(self, character_id, character_node, body_parts=None):
        """Register a character for animation and attach an anim_offset child."""
        # Ensure there is a dedicated offset node
        try:
            offset_node = character_node.find('**/anim_offset')
            if offset_node.isEmpty():
                offset_node = character_node.attachNewNode('anim_offset')
                # Move current children under offset_node (except the new one)
                for child in list(character_node.getChildren()):
                    if child != offset_node:
                        child.wrtReparentTo(offset_node)
            # Reset offset transforms
            offset_node.setPos(0, 0, 0)
            offset_node.setHpr(0, 0, 0)
            offset_node.setScale(1, 1, 1)
        except Exception:
            # Fallback to the character node itself
            offset_node = character_node

        self.animation_states[character_id] = {
            'node': character_node,
            'offset_node': offset_node,
            'state': 'idle',
            'body_parts': body_parts or {},
            'base_pos': character_node.getPos(),
            'base_hpr': character_node.getHpr(),
            'base_scale': character_node.getScale()
        }
        
        # Start idle animation
        self.start_idle_animation(character_id)
        print(f"Registered character {character_id} for animation")
    
    def start_idle_animation(self, character_id):
        """Start idle breathing/bobbing animation (offset-node only)"""
        if character_id not in self.animation_states:
            return
        char_state = self.animation_states[character_id]
        char_node = char_state['node']
        offset_node = char_state.get('offset_node', char_node)
        # Stop any existing animation
        self.stop_animation(character_id)
        # Reset offset
        try:
            offset_node.setPos(0, 0, 0)
            offset_node.setHpr(0, 0, 0)
        except Exception:
            pass
        # Create subtle bobbing motion on offset
        bob_up = Vec3(0, 0, self.idle_bob_amplitude)
        bob_down = Vec3(0, 0, -self.idle_bob_amplitude * 0.5)
        # Create breathing sequence
        breathe_up = LerpPosInterval(offset_node, self.idle_bob_period / 2, bob_up)
        breathe_down = LerpPosInterval(offset_node, self.idle_bob_period / 2, bob_down)
        # Add subtle side-to-side sway
        sway_left = LerpHprInterval(offset_node, self.idle_bob_period / 4, Vec3(-2, 0, 0))
        sway_right = LerpHprInterval(offset_node, self.idle_bob_period / 2, Vec3(2, 0, 0))
        sway_center = LerpHprInterval(offset_node, self.idle_bob_period / 4, Vec3(0, 0, 0))
        # Combine animations
        breathe_sequence = Sequence(breathe_up, breathe_down)
        sway_sequence = Sequence(sway_left, sway_right, sway_center)
        idle_animation = Parallel(breathe_sequence, sway_sequence)
        idle_loop = Sequence(idle_animation, Wait(0.1))
        idle_loop.loop()
        self.active_animations[character_id] = idle_loop
        char_state['state'] = 'idle'
        # Add eye blinking
        self.start_eye_blinking(character_id)

    def start_walk_animation(self, character_id, direction=Vec3(1, 0, 0)):
        """Start walking animation with directional movement (offset-node only)"""
        if character_id not in self.animation_states:
            return
        char_state = self.animation_states[character_id]
        char_node = char_state['node']
        offset_node = char_state.get('offset_node', char_node)
        # Stop idle animation
        self.stop_animation(character_id)
        # Reset offset
        try:
            offset_node.setPos(0, 0, 0)
            offset_node.setHpr(0, 0, 0)
        except Exception:
            pass
        # Create walking bounce
        bounce_up = Vec3(0, 0, self.walk_bounce_amplitude)
        # Walking step sequence
        step_up = LerpPosInterval(offset_node, self.walk_bounce_period / 4, bounce_up)
        step_down = LerpPosInterval(offset_node, self.walk_bounce_period / 4, Vec3(0, 0, 0))
        # Lean slightly in walking direction
        lean_angle = 5  # degrees
        direction_hpr = Vec3(lean_angle * direction.x, 0, 0)
        lean_forward = LerpHprInterval(offset_node, self.walk_bounce_period / 4, direction_hpr)
        lean_back = LerpHprInterval(offset_node, self.walk_bounce_period / 4, Vec3(0, 0, 0))
        # Combine step and lean
        step_sequence = Sequence(step_up, step_down)
        lean_sequence = Sequence(lean_forward, lean_back)
        walk_cycle = Parallel(step_sequence, lean_sequence)
        walk_loop = Sequence(walk_cycle)
        walk_loop.loop()
        self.active_animations[character_id] = walk_loop
        char_state['state'] = 'walking'

    def start_attack_animation(self, character_id, attack_type='punch'):
        """Start attack animation (offset-node for body; limbs animate directly)"""
        if character_id not in self.animation_states:
            return
        char_state = self.animation_states[character_id]
        char_node = char_state['node']
        offset_node = char_state.get('offset_node', char_node)
        body_parts = char_state.get('body_parts', {})
        # Stop current animation
        self.stop_animation(character_id)
        # Reset offset
        try:
            offset_node.setPos(0, 0, 0)
            offset_node.setHpr(0, 0, 0)
        except Exception:
            pass
        if attack_type == 'punch':
            wind_up = LerpPosInterval(offset_node, 0.1, Vec3(0, -0.1, 0))
            strike = LerpPosInterval(offset_node, 0.15, Vec3(0, 0.3, 0))
            recover = LerpPosInterval(offset_node, 0.25, Vec3(0, 0, 0))
            arm_sequence = Sequence()
            if 'right_arm' in body_parts:
                arm = body_parts['right_arm']
                arm_wind = LerpHprInterval(arm, 0.1, Vec3(0, -30, 0))
                arm_strike = LerpHprInterval(arm, 0.15, Vec3(0, 20, 0))
                arm_recover = LerpHprInterval(arm, 0.25, Vec3(0, 0, 0))
                arm_sequence = Sequence(arm_wind, arm_strike, arm_recover)
            attack_sequence = Parallel(Sequence(wind_up, strike, recover), arm_sequence)
        elif attack_type == 'kick':
            wind_up = LerpPosInterval(offset_node, 0.1, Vec3(0, 0, 0))
            kick = LerpPosInterval(offset_node, 0.2, Vec3(0, 0.2, 0.1))
            recover = LerpPosInterval(offset_node, 0.3, Vec3(0, 0, 0))
            leg_sequence = Sequence()
            if 'right_leg' in body_parts:
                leg = body_parts['right_leg']
                leg_raise = LerpHprInterval(leg, 0.2, Vec3(0, 45, 0))
                leg_recover = LerpHprInterval(leg, 0.3, Vec3(0, 0, 0))
                leg_sequence = Sequence(Wait(0.1), leg_raise, leg_recover)
            attack_sequence = Parallel(Sequence(wind_up, kick, recover), leg_sequence)
        else:
            wind_up = LerpPosInterval(offset_node, 0.1, Vec3(0, 0, 0))
            strike = LerpPosInterval(offset_node, 0.2, Vec3(0, 0.2, 0.05))
            recover = LerpPosInterval(offset_node, 0.3, Vec3(0, 0, 0))
            attack_sequence = Sequence(wind_up, strike, recover)
        def return_to_idle():
            self.start_idle_animation(character_id)
        full_sequence = Sequence(attack_sequence, Func(return_to_idle))
        self.active_animations[character_id] = full_sequence
        full_sequence.start()
        char_state['state'] = 'attacking'

    def start_hit_reaction(self, character_id, hit_direction=Vec3(-1, 0, 0)):
        """Start hit reaction animation (offset-node knockback)"""
        if character_id not in self.animation_states:
            return
        char_state = self.animation_states[character_id]
        char_node = char_state['node']
        offset_node = char_state.get('offset_node', char_node)
        # Stop current animation
        self.stop_animation(character_id)
        # Reset offset
        try:
            offset_node.setPos(0, 0, 0)
            offset_node.setHpr(0, 0, 0)
        except Exception:
            pass
        flinch = LerpPosInterval(offset_node, 0.1, hit_direction * 0.3)
        recover = LerpPosInterval(offset_node, 0.4, Vec3(0, 0, 0))
        flash_red = LerpColorScaleInterval(char_node, 0.05, Vec4(1.5, 0.5, 0.5, 1))
        flash_normal = LerpColorScaleInterval(char_node, 0.15, Vec4(1, 1, 1, 1))
        def return_to_idle():
            self.start_idle_animation(character_id)
        hit_sequence = Sequence(Parallel(flinch, flash_red), Parallel(recover, flash_normal), Func(return_to_idle))
        self.active_animations[character_id] = hit_sequence
        hit_sequence.start()
        char_state['state'] = 'hit'

    def start_victory_animation(self, character_id):
        """Start victory celebration animation (offset-node jump/pose)"""
        if character_id not in self.animation_states:
            return
        char_state = self.animation_states[character_id]
        char_node = char_state['node']
        offset_node = char_state.get('offset_node', char_node)
        body_parts = char_state.get('body_parts', {})
        # Stop current animation
        self.stop_animation(character_id)
        # Reset offset
        try:
            offset_node.setPos(0, 0, 0)
            offset_node.setHpr(0, 0, 0)
        except Exception:
            pass
        jump_up = LerpPosInterval(offset_node, 0.3, Vec3(0, 0, 0.5))
        jump_down = LerpPosInterval(offset_node, 0.3, Vec3(0, 0, 0))
        victory_hpr = Vec3(0, 0, 15)
        victory_pose = LerpHprInterval(offset_node, 0.2, victory_hpr)
        arm_sequence = Sequence()
        if 'right_arm' in body_parts and 'left_arm' in body_parts:
            right_arm = body_parts['right_arm']
            left_arm = body_parts['left_arm']
            raise_arms = Parallel(
                LerpHprInterval(right_arm, 0.5, Vec3(0, -90, 0)),
                LerpHprInterval(left_arm, 0.5, Vec3(0, -90, 0))
            )
            arm_sequence = raise_arms
        victory_sequence = Sequence(Parallel(jump_up, victory_pose), Parallel(jump_down, arm_sequence), Wait(2.0))
        self.active_animations[character_id] = victory_sequence
        victory_sequence.start()
        char_state['state'] = 'victory'

    def start_defeat_animation(self, character_id):
        """Start defeat/KO animation (offset-node fall)"""
        if character_id not in self.animation_states:
            return
        char_state = self.animation_states[character_id]
        char_node = char_state['node']
        offset_node = char_state.get('offset_node', char_node)
        # Stop current animation
        self.stop_animation(character_id)
        # Reset offset
        try:
            offset_node.setPos(0, 0, 0)
            offset_node.setHpr(0, 0, 0)
        except Exception:
            pass
        fall_hpr = Vec3(0, 90, 0)
        stagger = LerpPosInterval(offset_node, 0.2, Vec3(0, -0.2, 0))
        fall = Parallel(
            LerpPosInterval(offset_node, 0.8, Vec3(0, 0, -0.8)),
            LerpHprInterval(offset_node, 0.8, fall_hpr)
        )
        fade = LerpColorScaleInterval(char_node, 1.0, Vec4(0.7, 0.7, 0.7, 1))
        defeat_sequence = Sequence(stagger, Parallel(fall, fade))
        self.active_animations[character_id] = defeat_sequence
        defeat_sequence.start()
        char_state['state'] = 'defeated'

    def start_eye_blinking(self, character_id):
        """Start subtle eye blinking animation"""
        if character_id not in self.animation_states:
            return
        
        char_state = self.animation_states[character_id]
        body_parts = char_state.get('body_parts', {})
        
        # Find eyes in body parts
        left_eye = body_parts.get('left_eye')
        right_eye = body_parts.get('right_eye')
        
        if not (left_eye and right_eye):
            return
        
        def blink_cycle():
            # Random blink interval
            wait_time = random.uniform(2.0, 5.0)
            
            # Quick blink
            blink_down = Parallel(
                LerpScaleInterval(left_eye, 0.05, Vec3(1, 1, 0.1)),
                LerpScaleInterval(right_eye, 0.05, Vec3(1, 1, 0.1))
            )
            blink_up = Parallel(
                LerpScaleInterval(left_eye, 0.05, Vec3(1, 1, 1)),
                LerpScaleInterval(right_eye, 0.05, Vec3(1, 1, 1))
            )
            
            blink_sequence = Sequence(
                Wait(wait_time),
                blink_down,
                blink_up,
                Func(blink_cycle)
            )
            blink_sequence.start()
        
        # Start blinking cycle
        blink_cycle()
    
    def stop_animation(self, character_id):
        """Stop current animation for character"""
        if character_id in self.active_animations:
            animation = self.active_animations[character_id]
            if animation:
                animation.pause()
                animation.finish()
            del self.active_animations[character_id]
        # Reset offset to neutral so no lingering visual offsets
        try:
            st = self.animation_states.get(character_id)
            if st:
                off = st.get('offset_node', st.get('node'))
                if off:
                    off.setPos(0, 0, 0)
                    off.setHpr(0, 0, 0)
        except Exception:
            pass
    
    def update_animation_state(self, character_id, player_state, player_inputs=None):
        """Update animation based on player state and inputs"""
        if character_id not in self.animation_states:
            return
        
        char_state = self.animation_states[character_id]
        current_anim_state = char_state['state']
        
        # Don't interrupt certain animations
        if current_anim_state in ['attacking', 'hit', 'victory', 'defeated']:
            return
        
        # Determine new animation state
        new_state = 'idle'
        
        if player_inputs:
            # Check for movement
            if player_inputs.get('left') or player_inputs.get('right') or \
               player_inputs.get('up') or player_inputs.get('down'):
                new_state = 'walking'
                
                # Determine walk direction
                direction = Vec3(0, 0, 0)
                if player_inputs.get('left'):
                    direction.x -= 1
                if player_inputs.get('right'):
                    direction.x += 1
                if player_inputs.get('up'):
                    direction.y += 1
                if player_inputs.get('down'):
                    direction.y -= 1
                
                direction.normalize()
                
                if new_state != current_anim_state:
                    self.start_walk_animation(character_id, direction)
            
            # Check for attacks
            elif player_inputs.get('light') or player_inputs.get('heavy'):
                attack_type = 'punch' if player_inputs.get('light') else 'kick'
                self.start_attack_animation(character_id, attack_type)
        
        # Return to idle if no input
        if new_state == 'idle' and current_anim_state != 'idle':
            self.start_idle_animation(character_id)
    
    def cleanup(self):
        """Clean up all animations"""
        for character_id in list(self.active_animations.keys()):
            self.stop_animation(character_id)
        
        self.active_animations.clear()
        self.animation_states.clear()
        print("CharacterAnimator cleaned up")