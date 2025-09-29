from __future__ import annotations

"""Combatant logic for the 2.5D StreetBattle mode."""

import random
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

try:  # pragma: no cover - pygame optional during import
    import pygame
except ImportError:  # pragma: no cover - handled when 2.5D mode requested
    pygame = None  # type: ignore

from .sprites import SpriteAnimation

Vector2 = Tuple[float, float]


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    animation: str
    damage: int
    hit_frames: Tuple[int, ...]
    cooldown: float
    hitstop: float
    followups: Dict[str, str]


class Fighter:
    """State-driven combatant with configurable skill system."""

    def __init__(
        self,
        name: str,
        position: Vector2,
        animations: Optional[Dict[str, SpriteAnimation]] = None,
        skills: Optional[Dict[str, SkillDefinition]] = None,
        input_map: Optional[Dict[str, str]] = None,
        default_skill: Optional[str] = None,
        facing: int = 1,
        stage_width: int = 1280,
    ) -> None:
        if pygame is None:
            raise RuntimeError("Pygame must be installed to use Fighter")
        if not animations:
            raise ValueError("Fighter animations must be provided; procedural fallbacks are no longer available")
        if "idle" not in animations:
            raise ValueError(f"Fighter '{name}' is missing an 'idle' animation state")
        if not skills:
            raise ValueError(f"Fighter '{name}' requires at least one configured skill")
        normalized_map = {action: skill for action, skill in (input_map or {}).items() if skill in skills}
        if not normalized_map:
            raise ValueError(f"Fighter '{name}' needs an input map that references existing skills")
        self.name = name
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.facing = facing
        self.stage_width = stage_width
        # Load character stats from config
        self._load_character_stats()
        char_stats = self._get_character_stats(name)
        self.max_health = char_stats.get('max_health', 1000)
        self.health = char_stats.get('health', self.max_health)
        self.walk_speed = 220.0
        self.hitstop = 0.0
        self.animations = animations
        self.state = "idle"
        self.current_anim = self.animations[self.state]
        self.skills = skills
        self.input_map = normalized_map
        self.default_skill_name = default_skill if default_skill in self.skills else self.input_map.get("attack", next(iter(self.skills)))
        self.skill_cooldowns: Dict[str, float] = {name: 0.0 for name in self.skills}
        self.active_skill: Optional[SkillDefinition] = None
        self.skill_queue: Optional[SkillDefinition] = None
        self.attack_landed = False
        self.active_attack_frames: set[int] = set()
        self.altitude = 0.0
        self.vertical_velocity = 0.0
        self.damage_multiplier = 1.0
        self.cooldown_multiplier = 1.0
        self.hitstop_multiplier = 1.0
        self.guard_multiplier = 1.0
        self.jump_speed = 460.0
        self.gravity = 980.0
    
    def _load_character_stats(self):
        """Load character statistics from config file"""
        try:
            import json
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent / "config" / "character_stats.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.character_stats_config = json.load(f)
                print(f"[Fighter] Loaded character stats configuration")
            else:
                print(f"[Fighter] Character stats config not found: {config_path}")
                self.character_stats_config = None
        except Exception as e:
            print(f"[Fighter] Failed to load character stats: {e}")
            self.character_stats_config = None
    
    def _get_character_stats(self, character_name: str) -> dict:
        """Get stats for specific character"""
        if not self.character_stats_config:
            return {"max_health": 1000, "health": 1000}
        
        # Normalize character name for lookup
        normalized_name = character_name.lower().replace(' ', '_')
        
        # Try to find character-specific stats
        character_stats = self.character_stats_config.get("character_stats", {})
        if normalized_name in character_stats:
            return character_stats[normalized_name]
        
        # Fall back to default stats
        default_stats = self.character_stats_config.get("default_stats", {})
        print(f"[Fighter] Using default stats for {character_name}: HP={default_stats.get('max_health', 1000)}")
        return default_stats
    
    def get_skill_damage(self, skill_name: str) -> int:
        """Get damage value for a specific skill"""
        if not self.character_stats_config:
            return 50  # Default damage
        
        skill_damage = self.character_stats_config.get("skill_damage", {})
        return skill_damage.get(skill_name, 50)

    def change_state(self, state: str) -> None:
        if self.state == state:
            return
        if state not in self.animations:
            raise KeyError(f"State '{state}' is not defined for fighter {self.name}")
        self.state = state
        self.current_anim = self.animations[state]
        self.current_anim.reset()
        if state in {"hit", "ko"}:  # Use "hit" instead of "hurt"
            self.hitstop = 0.28 if state == "hit" else 0.0
            self.active_skill = None
            self.skill_queue = None
            self.attack_landed = False

    @property
    def hurtbox(self) -> Any:
        width, height = 86, 180
        rect = pygame.Rect(0, 0, width, height)
        rect.midbottom = (self.position.x, self.position.y - self.altitude)
        return rect

    def attack_hitbox(self) -> Any:
        rect = pygame.Rect(0, 0, 110, 80)
        offset_x = 58 * (1 if self.facing >= 0 else -1)
        rect.midleft = (self.position.x + offset_x, self.position.y - self.altitude - 90)
        if self.facing < 0:
            rect.x -= rect.width
        return rect

    def apply_damage(self, value: int) -> None:
        mitigation = max(0.25, self.guard_multiplier)
        adjusted = max(1, int(round(value / mitigation)))
        self.health = max(0, self.health - adjusted)
        self.active_skill = None
        self.skill_queue = None
        self.attack_landed = False
        self.active_attack_frames.clear()
        if self.health <= 0 and "ko" in self.animations:
            self.change_state("ko")
        else:
            self.change_state("hit")  # Use "hit" instead of "hurt" to match sprite system

    def get_skill_for_action(self, action: str) -> Optional[SkillDefinition]:
        skill_name = self.input_map.get(action)
        if not skill_name:
            return None
        return self.skills.get(skill_name)

    def can_use_action(self, action: str) -> bool:
        skill = self.get_skill_for_action(action)
        if not skill:
            return False
        return self.skill_cooldowns.get(skill.name, 0.0) <= 0.0

    def _activate_skill(self, skill: SkillDefinition) -> None:
        if skill.animation not in self.animations:
            raise KeyError(f"Animation '{skill.animation}' is not defined for fighter {self.name}")
        self.skill_cooldowns.setdefault(skill.name, 0.0)
        cooldown = max(0.1, skill.cooldown * self.cooldown_multiplier)
        self.skill_cooldowns[skill.name] = cooldown
        self.active_skill = skill
        self.skill_queue = None
        self.attack_landed = False
        self.active_attack_frames = set(skill.hit_frames)
        self.change_state(skill.animation)

    def _queue_followup(self, inputs: Dict[str, bool]) -> None:
        if not self.active_skill or not self.active_skill.followups or self.skill_queue:
            return
        for action, target in self.active_skill.followups.items():
            if not inputs.get(action):
                continue
            next_skill = self.skills.get(target)
            if not next_skill:
                continue
            if self.skill_cooldowns.get(next_skill.name, 0.0) > 0.0:
                continue
            self.skill_queue = next_skill
            break

    def _determine_skill_from_inputs(self, inputs: Dict[str, bool]) -> Optional[SkillDefinition]:
        for action in ("special", "attack"):
            if not inputs.get(action):
                continue
            skill = self.get_skill_for_action(action)
            if not skill:
                continue
            if self.skill_cooldowns.get(skill.name, 0.0) <= 0.0:
                return skill
        return None

    def update(self, dt: float, inputs: Dict[str, bool], opponent: "Fighter") -> Optional[str]:
        if self.health <= 0:
            if "ko" in self.animations:
                if self.state != "ko":
                    self.change_state("ko")
                self.current_anim.update(dt)
            return "ko"
        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            self.current_anim.update(dt * 0.2)
            return None

        for name in self.skill_cooldowns:
            self.skill_cooldowns[name] = max(0.0, self.skill_cooldowns[name] - dt)

        if opponent.position.x < self.position.x - 6:
            self.facing = -1
        elif opponent.position.x > self.position.x + 6:
            self.facing = 1

        if self.state == "hit":  # Use "hit" instead of "hurt"
            self.current_anim.update(dt)
            if self.current_anim.finished:
                self.change_state("idle")
            return None

        if self.active_skill:
            self._queue_followup(inputs)
            self.current_anim.update(dt)
            if self.current_anim.current_index in self.active_attack_frames and not self.attack_landed:
                if self.attack_hitbox().colliderect(opponent.hurtbox):
                    damage = max(1, int(round(self.active_skill.damage * self.damage_multiplier)))
                    opponent.apply_damage(damage)
                    opponent.hitstop = self.active_skill.hitstop * self.hitstop_multiplier
                    self.attack_landed = True
            if self.current_anim.finished:
                queued = self.skill_queue
                self.skill_queue = None
                self.active_skill = None
                if queued:
                    self._activate_skill(queued)
                else:
                    self.change_state("idle")
            return None

        if inputs.get("jump", False) and self.altitude <= 0.0 and not self.active_skill and self.state not in {"hit", "ko"}:  # Use "hit" instead of "hurt"
            self.vertical_velocity = self.jump_speed
            self.altitude = 1.0
            if "jump" in self.animations:
                self.change_state("jump")

        move_left = inputs.get("left", False)
        move_right = inputs.get("right", False)
        movement = 0.0
        if move_left and not move_right:
            movement = -1.0
        elif move_right and not move_left:
            movement = 1.0
        if movement != 0.0:
            self.change_state("walk")
            self.position.x += movement * self.walk_speed * dt
            self.position.x = max(120, min(self.stage_width - 120, self.position.x))
        else:
            self.change_state("idle")

        if self.altitude > 0.0 or self.vertical_velocity != 0.0:
            self.altitude = max(0.0, self.altitude + self.vertical_velocity * dt)
            self.vertical_velocity -= self.gravity * dt
            if self.altitude <= 0.0:
                self.altitude = 0.0
                self.vertical_velocity = 0.0
                if self.state == "jump":
                    self.change_state("idle")

        skill = self._determine_skill_from_inputs(inputs)
        if skill:
            self._activate_skill(skill)
        self.current_anim.update(dt)
        return None

    def draw(self, surface: Any, floor_y: int, offset: Tuple[int, int] = (0, 0)) -> None:
        frame = self.current_anim.current_surface
        sprite = frame
        if self.facing < 0:
            sprite = pygame.transform.flip(frame, True, False)
        rect = sprite.get_rect()
        ground_line = min(floor_y, int(self.position.y))
        offset_x, offset_y = offset
        rect.midbottom = (
            self.position.x + offset_x,
            ground_line - int(self.altitude) + offset_y,
        )
        surface.blit(sprite, rect)

    @property
    def is_hurt(self) -> bool:
        return self.state == "hit"  # Use "hit" instead of "hurt"

    def apply_tuning(
        self,
        *,
        speed: float = 1.0,
        damage: float = 1.0,
        cooldown: float = 1.0,
        stamina: float = 1.0,
        guard: float = 1.0,
        hitstop: float = 1.0,
        jump: float = 1.0,
    ) -> None:
        self.walk_speed *= speed
        self.damage_multiplier = damage
        self.cooldown_multiplier = cooldown
        self.hitstop_multiplier = hitstop
        self.guard_multiplier = guard
        self.jump_speed *= jump
        self.max_health = int(self.max_health * stamina)
        self.health = self.max_health


class SimpleAIController:
    """Heuristic opponent that mirrors classic arcade pressure strings."""

    def __init__(self, fighter: Fighter) -> None:
        self.fighter = fighter
        self.attack_timer = 0.0
        self.reposition_timer = 0.0

    def compute_inputs(self, dt: float, opponent: Fighter) -> Dict[str, bool]:
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.reposition_timer = max(0.0, self.reposition_timer - dt)
        distance = opponent.position.x - self.fighter.position.x
        commands = {"left": False, "right": False, "attack": False, "special": False}
        if abs(distance) > 260:
            commands["right" if distance > 0 else "left"] = True
        elif abs(distance) < 170:
            commands["left" if distance > 0 else "right"] = True
        else:
            if self.reposition_timer <= 0:
                jitter = random.choice([-1, 1])
                commands["left" if jitter < 0 else "right"] = True
                self.reposition_timer = 0.35
        if abs(distance) < 220 and self.attack_timer <= 0.0 and not opponent.is_hurt:
            action_choice = None
            if self.fighter.can_use_action("special") and random.random() < 0.35:
                action_choice = "special"
            elif self.fighter.can_use_action("attack"):
                action_choice = "attack"
            elif self.fighter.can_use_action("special"):
                action_choice = "special"
            if action_choice:
                commands[action_choice] = True
                chosen_skill = self.fighter.get_skill_for_action(action_choice)
                self.attack_timer = (chosen_skill.cooldown if chosen_skill else 1.0) + 0.2
        return commands


__all__ = ["Vector2", "SkillDefinition", "Fighter", "SimpleAIController"]
