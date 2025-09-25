import random
import time


class SimpleAI:
    def __init__(self, difficulty=1):
        self.difficulty = difficulty
        self.last_decision_time = 0
        self.decision_cooldown = 0.1  # Think every 100ms for more human-like behavior
        self.last_attack_time = 0
        self.attack_cooldown = 1.0  # Don't spam attacks
        self.retreat_timer = 0
        self.combo_chance = 0.3 * difficulty  # Higher difficulty = more combos
        self.last_enemy_pos = None
        self.enemy_velocity = (0, 0)
        
    def _predict_enemy_position(self, enemy_player, prediction_time=0.2):
        """Predict where enemy will be in prediction_time seconds"""
        if self.last_enemy_pos is None:
            self.last_enemy_pos = enemy_player.pos
            return enemy_player.pos
            
        # Calculate enemy velocity
        current_pos = enemy_player.pos
        dt = 0.016  # Approximate frame time
        self.enemy_velocity = (
            (current_pos.x - self.last_enemy_pos.x) / dt,
            (current_pos.y - self.last_enemy_pos.y) / dt
        )
        self.last_enemy_pos = current_pos
        
        # Predict future position
        predicted_pos = (
            current_pos.x + self.enemy_velocity[0] * prediction_time,
            current_pos.y + self.enemy_velocity[1] * prediction_time
        )
        return predicted_pos

    def decide(self, self_player, enemy_player):
        current_time = time.time()
        
        # Throttle decision making for more realistic AI
        if current_time - self.last_decision_time < self.decision_cooldown:
            return {}
        self.last_decision_time = current_time
        
        inputs = {}
        dist = self_player.distance_to(enemy_player)
        
        # Update retreat timer
        if self.retreat_timer > 0:
            self.retreat_timer -= self.decision_cooldown
        
        # Check if we're hurt and should retreat
        if self_player.health < 30 and random.random() < 0.7:
            self.retreat_timer = 2.0  # Retreat for 2 seconds
        
        # Retreat behavior
        if self.retreat_timer > 0:
            if enemy_player.pos.x > self_player.pos.x:
                inputs['left'] = True
            else:
                inputs['right'] = True
            # Occasional jump/dodge
            if random.random() < 0.2:
                inputs['up'] = True
            return inputs
        
        # Predict enemy movement for better positioning
        predicted_enemy_pos = self._predict_enemy_position(enemy_player)
        predicted_dist = ((predicted_enemy_pos[0] - self_player.pos.x)**2 + 
                         (predicted_enemy_pos[1] - self_player.pos.y)**2)**0.5
        
        # Movement logic with prediction
        optimal_distance = 2.0  # Preferred fighting distance
        
        if predicted_dist > optimal_distance + 1.0:
            # Move toward predicted position
            if predicted_enemy_pos[0] > self_player.pos.x:
                inputs['right'] = True
            else:
                inputs['left'] = True
        elif predicted_dist < optimal_distance - 0.5:
            # Too close, back off slightly
            if predicted_enemy_pos[0] > self_player.pos.x:
                inputs['left'] = True
            else:
                inputs['right'] = True
        
        # Vertical movement for dodging
        if abs(enemy_player.pos.y - self_player.pos.y) > 0.5:
            if enemy_player.pos.y > self_player.pos.y:
                inputs['up'] = True
            else:
                inputs['down'] = True
        
        # Attack decision system
        if current_time - self.last_attack_time > self.attack_cooldown:
            attack_range = 2.8
            
            if dist <= attack_range:
                # Check if enemy is in attacking state (vulnerable)
                enemy_attacking = getattr(enemy_player, 'state', 'idle') in ('light_atk', 'heavy_atk')
                enemy_hurt = getattr(enemy_player, 'state', 'idle') == 'hurt'
                
                attack_probability = 0.6 * self.difficulty
                
                # Increase attack chance if enemy is vulnerable
                if enemy_hurt:
                    attack_probability += 0.4
                elif enemy_attacking:
                    attack_probability += 0.2
                
                # Combo system - chance for heavy attack after light
                if hasattr(self_player, 'state') and self_player.state == 'idle':
                    if random.random() < attack_probability:
                        # Choose attack type based on situation
                        if enemy_player.health < 20 and random.random() < self.combo_chance:
                            inputs['heavy'] = True  # Finish with heavy attack
                        elif dist <= 2.0:
                            inputs['light'] = True  # Quick light attack
                        elif random.random() < 0.3:
                            inputs['heavy'] = True  # Occasional heavy attack
                        else:
                            inputs['light'] = True
                        
                        self.last_attack_time = current_time
                        # Adjust cooldown based on attack type
                        self.attack_cooldown = 0.8 if inputs.get('light') else 1.5
        
        # Defensive positioning - try to stay at optimal angle
        if not any(inputs.values()):  # If not doing anything else
            # Small random movements to avoid being too predictable
            if random.random() < 0.1:
                if random.random() < 0.5:
                    inputs['up'] = True
                else:
                    inputs['down'] = True
        
        return inputs
