from panda3d.core import Vec3


class CombatSystem:
    def __init__(self, players):
        self.players = players
        # track which player's current attack has already hit to prevent multiple hits per attack
        self._attack_hit_flags = {}  # player_id -> has_hit_this_attack

    def check_hits(self):
        results = []
        
        for i, a in enumerate(self.players):
            # Reset hit flag when player is not attacking
            if a.state not in ('light_atk', 'heavy_atk'):
                self._attack_hit_flags[i] = False
                continue
            
            # If this attack has already hit, skip
            if self._attack_hit_flags.get(i, False):
                continue
                
            for j, b in enumerate(self.players):
                if i == j:
                    continue
                    
                dist = a.distance_to(b)
                if dist <= (a.hit_radius + b.hit_radius + 1.0):
                    dmg = 8 if a.state == 'light_atk' else 18
                    results.append({'attacker': a, 'target': b, 'damage': dmg, 'pos': (b.pos.x, b.pos.y, b.pos.z)})
                    # Mark this attack as having hit
                    self._attack_hit_flags[i] = True
                    break  # One hit per attack
        
        return results

    def apply_results(self):
        hits = self.check_hits()
        for h in hits:
            t = h['target']
            t.take_damage(h['damage'])
        return hits
