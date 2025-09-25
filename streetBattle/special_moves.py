#!/usr/bin/env python3
"""
Special Moves System for StreetBattle
Implements KOF97-style special move combinations
"""

from panda3d.core import Vec3
from direct.task import Task
import time
import os
import json


class SpecialMovesSystem:
    """Manages special move inputs and execution"""
    
    def __init__(self, base_app):
        self.base_app = base_app
        self.input_buffer = {}  # Player -> list of (timestamp, input)
        self.buffer_time = 1.0  # 1 second input buffer
        self.special_moves = self._load_special_moves()  # generic fallback moves
        # character-specific move db from kof97_characters.json
        self.character_moves = {}
        self.player_character = {}  # player_id -> character_name
        try:
            self._load_character_moves_db()
        except Exception as e:
            print(f"[SpecialMoves] Failed to load character move DB: {e}")
    
    def _load_special_moves(self):
        """Load KOF97-style special moves"""
        return {
            # Basic special moves
            'hadoken': {
                'input': ['down', 'down-right', 'right', 'light'],
                'input_alt': ['down', 'down-right', 'right', 'heavy'],
                'name': '波动拳',
                'damage': 25,
                'animation_time': 0.8,
                'description': '发射能量波'
            },
            'shoryuken': {
                'input': ['right', 'down', 'down-right', 'light'],
                'input_alt': ['right', 'down', 'down-right', 'heavy'],
                'name': '昇龙拳',
                'damage': 30,
                'animation_time': 1.0,
                'description': '上升龙拳攻击'
            },
            'tatsumaki': {
                'input': ['down', 'down-left', 'left', 'heavy'],
                'name': '旋风腿',
                'damage': 20,
                'animation_time': 1.2,
                'description': '旋转踢击'
            },
            'dash_attack': {
                'input': ['right', 'right', 'light'],
                'input_alt': ['left', 'left', 'light'],
                'name': '突进技',
                'damage': 18,
                'animation_time': 0.6,
                'description': '快速突进攻击'
            },
            # Super moves (require power gauge)
            'super_hadoken': {
                'input': ['down', 'down-right', 'right', 'down', 'down-right', 'right', 'heavy'],
                'name': '真空波动拳',
                'damage': 50,
                'power_cost': 50,
                'animation_time': 1.5,
                'description': '强化的能量波'
            },
            'super_combo': {
                'input': ['down', 'down-right', 'right', 'left', 'down', 'down-right', 'right', 'light'],
                'name': '超必杀连击',
                'damage': 70,
                'power_cost': 100,
                'animation_time': 2.0,
                'description': '终极连击技能'
            },
            # Air specials
            'air_hadoken': {
                'input': ['down', 'down-right', 'right', 'light'],
                'name': '空中波动拳',
                'damage': 22,
                'requires_air': True,
                'animation_time': 0.7,
                'description': '空中释放的能量波'
            },
            'dive_kick': {
                'input': ['down', 'heavy'],
                'name': '俯冲踢',
                'damage': 28,
                'requires_air': True,
                'animation_time': 0.8,
                'description': '从空中俯冲攻击'
            }
        }
    
    def register_player(self, player_id):
        """Register a player for input tracking"""
        self.input_buffer[player_id] = []

    def register_player_with_character(self, player_id, character_name: str):
        """Register player and bind character name for per-character moves"""
        self.register_player(player_id)
        if character_name:
            self.player_character[player_id] = character_name
    
    def process_input(self, player_id, input_key, pressed):
        """Process player input for special move detection"""
        if player_id not in self.input_buffer:
            self.register_player(player_id)
        
        current_time = time.time()
        
        # Clean old inputs from buffer
        self.input_buffer[player_id] = [
            (timestamp, inp) for timestamp, inp in self.input_buffer[player_id]
            if current_time - timestamp <= self.buffer_time
        ]
        
        # Add new input if pressed
        if pressed:
            # Convert input to direction/action format
            direction_map = {
                'left': 'left',
                'right': 'right', 
                'up': 'up',
                'down': 'down'
            }
            
            # Handle diagonal inputs
            current_inputs = {k: v for k, v in self.base_app.key_map.items() if v}
            
            if 'down' in current_inputs and 'right' in current_inputs:
                input_key = 'down-right'
            elif 'down' in current_inputs and 'left' in current_inputs:
                input_key = 'down-left'
            elif 'up' in current_inputs and 'right' in current_inputs:
                input_key = 'up-right'
            elif 'up' in current_inputs and 'left' in current_inputs:
                input_key = 'up-left'
            elif input_key in direction_map:
                input_key = direction_map[input_key]
            
            self.input_buffer[player_id].append((current_time, input_key))
            
            # Check for special move patterns
            return self._check_special_moves(player_id)
        
        return None
    
    def _check_special_moves(self, player_id):
        """Check if recent inputs match any special move patterns"""
        if player_id not in self.input_buffer:
            return None
        
        # Get recent inputs in chronological order
        recent_inputs = [inp for _, inp in sorted(self.input_buffer[player_id], key=lambda x: x[0])]
        
        # Determine the active move set (character-specific if available)
        char_name = self.player_character.get(player_id)
        active_moves = self.get_character_moves(char_name) if char_name else self.special_moves

        # Check each special move pattern
        for move_name, move_data in active_moves.items():
            pattern = move_data['input']
            alt_pattern = move_data.get('input_alt')
            
            if self._matches_pattern(recent_inputs, pattern):
                return move_name
            elif alt_pattern and self._matches_pattern(recent_inputs, alt_pattern):
                return move_name
        
        return None
    
    def _matches_pattern(self, inputs, pattern):
        """Check if input sequence matches a pattern"""
        if len(inputs) < len(pattern):
            return False
        
        # Check if the last N inputs match the pattern
        recent = inputs[-len(pattern):]
        return recent == pattern
    
    def execute_special_move(self, player, move_name):
        """Execute a special move using character-specific data when available"""
        # resolve active move set
        char_name = getattr(player, 'character_name', None)
        active_moves = self.get_character_moves(char_name) if char_name else self.special_moves
        move_data = active_moves.get(move_name)
        if not move_data:
            return False
        
        # Check requirements
        if move_data.get('requires_air', False) and not player.is_jumping:
            return False
        
        power_cost = move_data.get('power_cost', 0)
        if hasattr(player, 'power_gauge') and player.power_gauge < power_cost:
            return False
        
        # Execute move
        damage = move_data['damage']
        animation_time = move_data['animation_time']
        
        # Apply power cost
        if power_cost > 0 and hasattr(player, 'power_gauge'):
            player.power_gauge -= power_cost
        
        # Set player state
        player.state = f'special_{move_name}'
        player.state_timer = animation_time
        player.attack_cooldown = animation_time + 0.2
        
        # Create projectile or effect if needed
        if 'hadoken' in move_name:
            self._create_projectile(player, move_name, damage)
        
        # Apply damage multiplier for combos
        if hasattr(player, 'combo') and player.combo > 1:
            damage = int(damage * (1 + player.combo * 0.1))
        
        print(f"Special move executed: {move_data['name']} (Damage: {damage})")
        return True
    
    def _create_projectile(self, player, move_name, damage):
        """Create a projectile for ranged special moves"""
        try:
            # Create simple projectile effect
            projectile_pos = Vec3(player.pos)
            projectile_pos.x += 2 if player.facing > 0 else -2
            projectile_pos.z += 1
            
            # For now, just trigger VFX at projectile position
            if hasattr(self.base_app, 'vfx'):
                self.base_app.vfx.play_combo_effect(projectile_pos)
            
            # TODO: Implement actual projectile physics and collision
            
        except Exception as e:
            print(f"Failed to create projectile: {e}")
    
    def get_character_moves(self, character_name):
        """Get character-specific special+super moves; fallback to generic basics"""
        if not character_name:
            return self.special_moves
        moves = self.character_moves.get(character_name)
        if moves:
            return moves
        # fallback: generic core moves
        basic_moves = {
            name: data for name, data in self.special_moves.items()
            if not data.get('power_cost', 0) > 50
        }
        return basic_moves
    
    def get_move_list_text(self, character_name=None):
        """Get formatted text of available moves for help overlay"""
        moves = self.get_character_moves(character_name) if character_name else self.special_moves
        lines = []
        title = f"{character_name} 的技能列表:" if character_name else "特殊技能:"
        lines.append(title)
        for move_key, move_data in moves.items():
            # pretty input
            seq = move_data.get('input', [])
            seq_alt = move_data.get('input_alt')
            in_str = ' + '.join(seq)
            if seq_alt:
                in_str += f"  或  {' + '.join(seq_alt)}"
            nm = move_data.get('name', move_key)
            desc = move_data.get('description', '')
            power = move_data.get('power_cost')
            if power:
                lines.append(f"- {nm}: {in_str} (能量:{power})")
            else:
                lines.append(f"- {nm}: {in_str}")
            if desc:
                lines.append(f"  {desc}")
        return "\n".join(lines)

    # ---- Internal: load and parse per-character move DB ----
    def _load_character_moves_db(self):
        """Read kof97_characters.json and build per-character move patterns"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_file = os.path.join(current_dir, 'kof97_characters.json')
            if not os.path.exists(db_file):
                return
            with open(db_file, 'r', encoding='utf-8') as f:
                chars = json.load(f)
            for char in chars:
                name = char.get('name')
                if not name:
                    continue
                spec = {}
                # special moves
                for mname, mdata in (char.get('special_moves') or {}).items():
                    notation = (mdata.get('input') or '').strip()
                    if not notation:
                        continue
                    patterns, requires_air = self._parse_notation(notation)
                    # create two entries if there are multiple patterns (due to P mapping)
                    # We'll store primary under mname
                    entry = {
                        'name': mname,
                        'damage': int(mdata.get('damage', 20)),
                        'animation_time': 0.9,
                        'description': mname,
                        'requires_air': requires_air,
                    }
                    # patterns may have 1 or 2 alternatives
                    if len(patterns) == 2:
                        entry['input'] = patterns[0]
                        entry['input_alt'] = patterns[1]
                    else:
                        entry['input'] = patterns[0]
                    spec[mname] = entry
                # super moves
                for mname, mdata in (char.get('super_moves') or {}).items():
                    notation = (mdata.get('input') or '').strip()
                    if not notation:
                        continue
                    patterns, requires_air = self._parse_notation(notation)
                    entry = {
                        'name': mname,
                        'damage': int(mdata.get('damage', 50)),
                        'animation_time': 1.6,
                        'description': mname,
                        'power_cost': int(mdata.get('power_cost', 1)) * 50,
                        'requires_air': requires_air,
                    }
                    if len(patterns) == 2:
                        entry['input'] = patterns[0]
                        entry['input_alt'] = patterns[1]
                    else:
                        entry['input'] = patterns[0]
                    spec[mname] = entry
                if spec:
                    self.character_moves[name] = spec
        except Exception as e:
            print(f"[SpecialMoves] Error parsing character moves: {e}")

    def _parse_notation(self, notation: str):
        """Parse KOF/FGC notation like 'QCF+P', 'QCB,HCF+P', 'Charge D,U+P', 'QCF+P (air)'.
        Returns (patterns: List[List[str]], requires_air: bool)
        P -> light/heavy alternatives; K -> light/heavy as well.
        Facing assumed to the right.
        """
        requires_air = False
        s = notation
        if '(' in s:
            # handle '(air)'
            if 'air' in s.lower():
                requires_air = True
            s = s.split('(')[0].strip()
        parts = [p.strip() for p in s.replace(' ', '').split(',') if p.strip()]
        sequence_dirs = []
        # mapping helpers
        def qcf():
            return ['down', 'down-right', 'right']
        def qcb():
            return ['down', 'down-left', 'left']
        def hcf():
            return ['left', 'down-left', 'down', 'down-right', 'right']
        def hcb():
            return ['right', 'down-right', 'down', 'down-left', 'left']
        def dp():
            return ['right', 'down', 'down-right']
        dir_map = {
            'F': ['right'], 'B': ['left'], 'U': ['up'], 'D': ['down'],
            'DF': ['down-right'], 'DB': ['down-left'], 'UF': ['up-right'], 'UB': ['up-left']
        }
        for part in parts:
            # split by + to find terminal button
            if '+' in part:
                left, button = part.split('+', 1)
            else:
                left, button = part, ''
            # decode left
            dirs = []
            i = 0
            while i < len(left):
                if left.startswith('Charge', i):
                    i += len('Charge')
                    continue
                if left.startswith('QCF', i):
                    dirs += qcf(); i += 3
                elif left.startswith('QCB', i):
                    dirs += qcb(); i += 3
                elif left.startswith('HCF', i):
                    dirs += hcf(); i += 3
                elif left.startswith('HCB', i):
                    dirs += hcb(); i += 3
                elif left.startswith('DP', i):
                    dirs += dp(); i += 2
                elif left.startswith('DF', i) or left.startswith('DB', i) or left.startswith('UF', i) or left.startswith('UB', i):
                    token = left[i:i+2]; dirs += dir_map.get(token, []); i += 2
                else:
                    token = left[i]
                    dirs += dir_map.get(token, [])
                    i += 1
            sequence_dirs += dirs
            # handle button at the end of the last part only
            if button:
                # P/K -> allow light or heavy
                if 'P' in button or 'K' in button:
                    # We'll return two alternative patterns differing by last element
                    p1 = sequence_dirs + ['light']
                    p2 = sequence_dirs + ['heavy']
                    return [p1, p2], requires_air
                # else if explicit L/H
                if 'L' in button:
                    sequence_dirs += ['light']
                if 'H' in button:
                    sequence_dirs += ['heavy']
        # default single pattern
        return [sequence_dirs], requires_air


# Enhanced Player class integration
def enhance_player_with_special_moves(player, special_moves_system):
    """Add special moves capability to a player"""
    player.special_moves = special_moves_system
    player.power_gauge = 0
    player.max_power = 100
    
    # Override apply_input to include special move detection
    original_apply_input = player.apply_input
    
    def enhanced_apply_input(inputs, dt):
        # Check for special moves first  
        for key, pressed in inputs.items():
            if pressed:
                special_move = player.special_moves.process_input(id(player), key, pressed)
                if special_move:
                    if player.special_moves.execute_special_move(player, special_move):
                        # Special move executed, skip normal input processing
                        return
        
        # Build power gauge during combat
        if any(inputs.values()):  # Any input pressed
            player.power_gauge = min(player.max_power, player.power_gauge + dt * 5)
        
        # Call original input processing
        original_apply_input(inputs, dt)
    
    player.apply_input = enhanced_apply_input
    return player