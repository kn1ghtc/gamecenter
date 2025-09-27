from __future__ import annotations

"""Pygame-based 2.5D fighting experience for StreetBattle.

The goal of this prototype is to emulate the snappy cadence of classic KOF
sprites: distinct loops for idle/breathing, directional walk cycles, explosive
multi-hit attacks, and responsive hit-stun feedback.  The implementation is
fully self-contained and falls back to procedural sprites when high-fidelity
assets are unavailable.  When real sprite sheets are provided (see
``sprite_pipeline.py``), the same animation system can play them without code
changes.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # Import lazily so the 3D mode can run without pygame installed.
    import pygame
except ImportError:  # pragma: no cover - handled at runtime via launcher
    pygame = None  # type: ignore

from ..config import SettingsManager


Vector2 = Tuple[float, float]
_THEME_DARK = (18, 24, 36)
_THEME_ACCENT = (189, 68, 95)
_FLOOR_COLOR = (40, 52, 78)
SPRITE_ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets" / "sprites"


@dataclass
class SpriteFrame:
    surface: Any
    duration: float  # seconds


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    animation: str
    damage: int
    hit_frames: Tuple[int, ...]
    cooldown: float
    hitstop: float
    followups: Dict[str, str]


class SpriteAnimation:
    """Simple frame-based animation compatible with sprite sheets or procedural art."""

    def __init__(self, name: str, frames: List[SpriteFrame], loop: bool = True) -> None:
        if pygame is None:
            raise RuntimeError("Pygame must be available to create animations")
        self.name = name
        self.frames = frames
        self.loop = loop
        self.index = 0
        self.timer = 0.0
        self.finished = False

    def reset(self) -> None:
        self.index = 0
        self.timer = 0.0
        self.finished = False

    def update(self, dt: float) -> None:
        if not self.frames:
            return
        if self.finished and not self.loop:
            return
        self.timer += dt
        while self.timer >= self.frames[self.index].duration:
            self.timer -= self.frames[self.index].duration
            if self.index + 1 < len(self.frames):
                self.index += 1
            elif self.loop:
                self.index = 0
            else:
                self.finished = True
                self.index = len(self.frames) - 1
                self.timer = 0.0
                break

    @property
    def current_surface(self) -> Any:
        return self.frames[self.index].surface

    @property
    def current_index(self) -> int:
        return self.index

    @property
    def total_duration(self) -> float:
        return sum(frame.duration for frame in self.frames)


def _load_sprite_manifest(name: str) -> Optional[Dict[str, Any]]:
    manifest_path = SPRITE_ASSET_ROOT / name / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        with manifest_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                data["__manifest_path__"] = manifest_path  # type: ignore[index]
                return data
    except Exception:
        return None
    return None


def _apply_color_mod(surface: Any, color_mod: Optional[Dict[str, Any]]) -> Any:
    if not color_mod:
        return surface
    result = surface.copy()
    multiply = color_mod.get("multiply") if isinstance(color_mod, dict) else None
    if multiply:
        mul = [max(0.0, float(value)) for value in multiply[:3]]
        multiplier = pygame.Surface(result.get_size(), pygame.SRCALPHA)
        multiplier.fill(
            (
                min(255, int(mul[0] * 255)),
                min(255, int((mul[1] if len(mul) > 1 else mul[0]) * 255)),
                min(255, int((mul[2] if len(mul) > 2 else mul[0]) * 255)),
                255,
            )
        )
        result.blit(multiplier, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    add = color_mod.get("add") if isinstance(color_mod, dict) else None
    if add:
        add_values = [max(0.0, float(value)) for value in add[:3]]
        additive = pygame.Surface(result.get_size(), pygame.SRCALPHA)
        additive.fill(
            (
                min(255, int(add_values[0])),
                min(255, int((add_values[1] if len(add_values) > 1 else add_values[0]))),
                min(255, int((add_values[2] if len(add_values) > 2 else add_values[0]))),
                0,
            )
        )
        result.blit(additive, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return result


def _slice_sheet(
    image: Any,
    frame_size: Tuple[int, int],
    sequence: List[int],
    duration: float,
    durations: Optional[List[float]] = None,
    color_mod: Optional[Dict[str, Any]] = None,
) -> List[SpriteFrame]:
    frames: List[SpriteFrame] = []
    width, height = image.get_size()
    frame_w, frame_h = frame_size
    columns = max(1, width // frame_w)
    for idx, frame_index in enumerate(sequence):
        row = frame_index // columns
        col = frame_index % columns
        rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
        surface = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        surface.blit(image, (0, 0), rect)
        if color_mod:
            surface = _apply_color_mod(surface, color_mod)
        frame_duration = durations[idx] if durations and idx < len(durations) else duration
        frames.append(SpriteFrame(surface, frame_duration))
    return frames


def load_sprite_animations(name: str) -> Optional[Tuple[Dict[str, SpriteAnimation], Dict[str, Any]]]:
    if pygame is None:
        return None
    manifest = _load_sprite_manifest(name)
    if not manifest:
        return None
    manifest_dir = manifest["__manifest_path__"].parent  # type: ignore[index]
    states = manifest.get("states", {})
    animations: Dict[str, SpriteAnimation] = {}
    metadata: Dict[str, Any] = {}
    top_color_mod = manifest.get("color_mod") if isinstance(manifest, dict) else None
    hit_frame_map: Dict[str, Iterable[int]] = {}
    for state, cfg in states.items():
        sheet_name = cfg.get("sheet")
        if not sheet_name:
            continue
        sheet_path = manifest_dir / sheet_name
        if not sheet_path.exists():
            continue
        try:
            surface = pygame.image.load(sheet_path.as_posix()).convert_alpha()
        except Exception:
            continue
        frame_size = cfg.get("frame_size") or [surface.get_width(), surface.get_height()]
        if not isinstance(frame_size, (list, tuple)) or len(frame_size) != 2:
            frame_size = [surface.get_width(), surface.get_height()]
        frame_size_tuple = (int(frame_size[0]), int(frame_size[1]))
        sequence = cfg.get("sequence") or list(range(cfg.get("frames", 1)))
        if not sequence:
            total_frames = (surface.get_width() // frame_size_tuple[0]) * (surface.get_height() // frame_size_tuple[1])
            sequence = list(range(total_frames))
        fps = cfg.get("fps", 8)
        base_duration = 1.0 / max(1, fps)
        durations = cfg.get("durations")
        state_color_mod = cfg.get("color_mod") if isinstance(cfg, dict) else None
        frames = _slice_sheet(
            surface,
            frame_size_tuple,
            sequence,
            base_duration,
            durations,
            color_mod=state_color_mod or top_color_mod,
        )
        loop = bool(cfg.get("loop", True))
        animations[state] = SpriteAnimation(state, frames, loop=loop)
        if "hit_frames" in cfg:
            frames_value = cfg["hit_frames"]
            if isinstance(frames_value, (list, tuple)):
                hit_frame_map[state] = tuple(int(i) for i in frames_value)
    metadata["source"] = manifest.get("source")
    license_value = manifest.get("license")
    if license_value:
        metadata["license"] = license_value
    if hit_frame_map:
        metadata["hit_frames"] = hit_frame_map
        if "attack" not in metadata and "attack_light" in hit_frame_map:
            metadata["attack_frames"] = tuple(hit_frame_map["attack_light"])
    if "attack" not in animations and "attack_light" in animations:
        animations["attack"] = animations["attack_light"]
    return animations, metadata


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
        self.health = 100
        self.max_health = 100
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

    def change_state(self, state: str) -> None:
        if self.state == state:
            return
        if state not in self.animations:
            raise KeyError(f"State '{state}' is not defined for fighter {self.name}")
        self.state = state
        self.current_anim = self.animations[state]
        self.current_anim.reset()
        if state in {"hurt", "ko"}:
            self.hitstop = 0.28 if state == "hurt" else 0.0
            self.active_skill = None
            self.skill_queue = None
            self.attack_landed = False

    @property
    def hurtbox(self) -> Any:
        width, height = 86, 180
        rect = pygame.Rect(0, 0, width, height)
        rect.midbottom = (self.position.x, self.position.y)
        return rect

    def attack_hitbox(self) -> Any:
        rect = pygame.Rect(0, 0, 110, 80)
        offset_x = 58 * (1 if self.facing >= 0 else -1)
        rect.midleft = (self.position.x + offset_x, self.position.y - 90)
        if self.facing < 0:
            rect.x -= rect.width
        return rect

    def apply_damage(self, value: int) -> None:
        self.health = max(0, self.health - value)
        self.active_skill = None
        self.skill_queue = None
        self.attack_landed = False
        self.active_attack_frames.clear()
        if self.health <= 0 and "ko" in self.animations:
            self.change_state("ko")
        else:
            self.change_state("hurt")

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
        self.skill_cooldowns[skill.name] = skill.cooldown
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

        # Automatically face opponent
        if opponent.position.x < self.position.x - 6:
            self.facing = -1
        elif opponent.position.x > self.position.x + 6:
            self.facing = 1

        if self.state == "hurt":
            self.current_anim.update(dt)
            if self.current_anim.finished:
                self.change_state("idle")
            return None

        if self.active_skill:
            self._queue_followup(inputs)
            self.current_anim.update(dt)
            if self.current_anim.current_index in self.active_attack_frames and not self.attack_landed:
                if self.attack_hitbox().colliderect(opponent.hurtbox):
                    opponent.apply_damage(self.active_skill.damage)
                    opponent.hitstop = self.active_skill.hitstop
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

        skill = self._determine_skill_from_inputs(inputs)
        if skill:
            self._activate_skill(skill)
        self.current_anim.update(dt)
        return None

    def draw(self, surface: Any, floor_y: int) -> None:
        frame = self.current_anim.current_surface
        sprite = frame
        if self.facing < 0:
            sprite = pygame.transform.flip(frame, True, False)
        rect = sprite.get_rect()
        rect.midbottom = (self.position.x, floor_y)
        surface.blit(sprite, rect)

    @property
    def is_hurt(self) -> bool:
        return self.state == "hurt"


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


class SpriteBattleGame:
    """Main entry point for the pygame-powered 2.5D mode."""

    def __init__(self, settings_manager: Optional[SettingsManager] = None) -> None:
        if pygame is None:
            raise RuntimeError("Pygame 未安装，无法启动 2.5D 模式。请通过 pip install pygame 安装。")
        self.settings_manager = settings_manager or SettingsManager()
        graphics = self.settings_manager.get("graphics", {}) or {}
        resolution = graphics.get("resolution", [1280, 720])
        if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
            resolution = [1280, 720]
        self.width = int(resolution[0])
        self.height = int(resolution[1])
        if self.width < 960:
            self.width = 960
        if self.height < 600:
            self.height = 600

        self.screen: Any = None
        self.clock: Any = None
        self.running = False
        self.player: Optional[Fighter] = None
        self.cpu: Optional[Fighter] = None
        self.ai: Optional[SimpleAIController] = None
        self.floor_y = self.height - 110
        self.background = self._build_background()
        self.keymap = self._build_keymap()
        self.attack_buffer = False
        self.special_buffer = False
        self.hud_font: Any = None
        self.sprite_sources: Dict[str, str] = {}
        self.skill_config = self._load_skill_config()
        self.roster_map, self.roster_order = self._load_roster_config()

    def _build_background(self) -> Any:
        surface = pygame.Surface((self.width, self.height))
        gradient = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(_THEME_DARK[0] * (1 - t) + 12 * t),
                int(_THEME_DARK[1] * (1 - t) + 18 * t),
                int(_THEME_DARK[2] * (1 - t) + 32 * t),
            )
            pygame.draw.line(gradient, color, (0, y), (self.width, y))
        surface.blit(gradient, (0, 0))
        pygame.draw.rect(surface, _FLOOR_COLOR, (0, self.floor_y, self.width, self.height - self.floor_y))
        for x in range(0, self.width, 120):
            pygame.draw.line(surface, (24, 30, 46), (x, self.floor_y), (x + 80, self.height), 2)
        return surface

    def _build_keymap(self) -> Dict[str, int]:
        if pygame is None:
            return {}
        mapping = self.settings_manager.get("controls.keyboard", {}) or {}
        default = {
            "left": "a",
            "right": "d",
            "up": "w",
            "down": "s",
            "attack": "j",
            "special": "k",
            "jump": "space",
        }
        keymap: Dict[str, int] = {}
        for action, fallback in default.items():
            key_name = str(mapping.get(action, fallback)).lower()
            try:
                keymap[action] = pygame.key.key_code(key_name)
            except (KeyError, ValueError):
                keymap[action] = pygame.key.key_code(fallback)
        return keymap

    def _load_skill_config(self) -> Dict[str, Any]:
        skills_path = Path(__file__).resolve().parents[1] / "config" / "skills.json"
        if not skills_path.exists():
            return {}
        try:
            with skills_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            raise RuntimeError(f"无法解析技能配置文件: {skills_path}") from exc

    def _load_roster_config(self) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        roster_path = Path(__file__).resolve().parents[1] / "config" / "roster.json"
        roster_map: Dict[str, Dict[str, Any]] = {}
        roster_order: List[str] = []
        if roster_path.exists():
            try:
                with roster_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                fighters = payload.get("fighters", []) if isinstance(payload, dict) else []
                if isinstance(fighters, list):
                    for entry in fighters:
                        if not isinstance(entry, dict):
                            continue
                        key = str(entry.get("key") or "").strip()
                        if not key:
                            continue
                        normalized = {
                            "key": key,
                            "display_name": str(entry.get("display_name") or key.replace("_", " ").title()),
                            "manifest": str(entry.get("manifest") or key),
                            "skill_profile": str(entry.get("skill_profile") or key),
                            "team": entry.get("team"),
                            "tempo": entry.get("tempo"),
                            "power": entry.get("power"),
                            "technique": entry.get("technique"),
                            "guard": entry.get("guard"),
                        }
                        roster_map[key] = normalized
                        roster_order.append(key)
            except Exception as exc:
                raise RuntimeError(f"无法解析角色配置文件: {roster_path}") from exc
        if not roster_map:
            fallback_entries = [
                {
                    "key": "hero",
                    "display_name": "Martial Hero",
                    "manifest": "hero",
                    "skill_profile": "hero",
                },
                {
                    "key": "shadow",
                    "display_name": "Martial Shadow",
                    "manifest": "shadow",
                    "skill_profile": "shadow",
                },
            ]
            for entry in fallback_entries:
                roster_map[entry["key"]] = entry
                roster_order.append(entry["key"])
        return roster_map, roster_order

    def _resolve_player_key(self, requested: Optional[str]) -> str:
        if requested and requested in self.roster_map:
            return requested
        return self.roster_order[0]

    def _resolve_cpu_key(self, player_key: str, requested: Optional[str]) -> str:
        if requested and requested in self.roster_map and requested != player_key:
            return requested
        candidates = [key for key in self.roster_order if key != player_key]
        if not candidates:
            return player_key
        return random.choice(candidates)

    def _spawn_fighter(self, entry: Dict[str, Any], position: Tuple[float, float], facing: int) -> Fighter:
        manifest_key = str(entry.get("manifest") or entry.get("key"))
        display_name = str(entry.get("display_name") or manifest_key.replace("_", " ").title())
        animations, metadata = self._load_fighter_assets(manifest_key, label=display_name)
        skill_key = str(entry.get("skill_profile") or manifest_key)
        skills, input_map, default_skill = self._build_skillset(skill_key, metadata or {}, animations)
        return Fighter(
            display_name,
            position,
            animations,
            skills=skills,
            input_map=input_map,
            default_skill=default_skill,
            facing=facing,
            stage_width=self.width,
        )

    def _build_skillset(
        self,
        key: str,
        metadata: Dict[str, Any],
        animations: Dict[str, SpriteAnimation],
    ) -> Tuple[Dict[str, SkillDefinition], Dict[str, str], Optional[str]]:
        spec = self.skill_config.get(key, {}) if isinstance(self.skill_config, dict) else {}
        raw_skills = spec.get("skills", []) if isinstance(spec, dict) else []
        hit_lookup: Dict[str, Iterable[int]] = metadata.get("hit_frames", {}) if metadata else {}
        skills: Dict[str, SkillDefinition] = {}

        def _default_hit_frames(animation_name: str) -> Tuple[int, ...]:
            anim = animations.get(animation_name)
            if not anim:
                return (2, 3)
            total_frames = len(anim.frames)
            if total_frames <= 2:
                return tuple(range(total_frames)) or (0,)
            mid_start = max(1, total_frames // 2 - 1)
            mid_end = min(total_frames, mid_start + 2)
            return tuple(range(mid_start, mid_end))

        for entry in raw_skills:
            if not isinstance(entry, dict):
                continue
            animation = entry.get("animation")
            if not animation or animation not in animations:
                continue
            name = str(entry.get("name") or animation)
            hit_frames_spec = entry.get("hit_frames")
            if isinstance(hit_frames_spec, (list, tuple)) and hit_frames_spec:
                hit_frames = tuple(int(i) for i in hit_frames_spec)
            else:
                fallback = hit_lookup.get(animation) or metadata.get("attack_frames") if metadata else None
                if fallback:
                    hit_frames = tuple(int(i) for i in fallback)
                else:
                    hit_frames = _default_hit_frames(animation)
            damage = int(entry.get("damage", 12))
            cooldown = float(entry.get("cooldown", 0.8))
            hitstop = float(entry.get("hitstop", 0.18))
            followups_spec = entry.get("followups", {}) if isinstance(entry.get("followups"), dict) else {}
            followups = {
                str(action): str(target)
                for action, target in followups_spec.items()
                if isinstance(action, str) and isinstance(target, str)
            }
            skills[name] = SkillDefinition(
                name=name,
                animation=animation,
                damage=damage,
                hit_frames=hit_frames,
                cooldown=cooldown,
                hitstop=hitstop,
                followups=followups,
            )

        if not skills:
            fallback_animation = None
            for candidate in ("attack", "attack_light", "attack_heavy"):
                if candidate in animations:
                    fallback_animation = candidate
                    break
            fallback_animation = fallback_animation or next(iter(animations))
            fallback_frames = hit_lookup.get(fallback_animation) or metadata.get("attack_frames") if metadata else None
            hit_frames = tuple(int(i) for i in fallback_frames) if fallback_frames else _default_hit_frames(fallback_animation)
            skills[fallback_animation] = SkillDefinition(
                name=fallback_animation,
                animation=fallback_animation,
                damage=12,
                hit_frames=hit_frames,
                cooldown=0.9,
                hitstop=0.18,
                followups={},
            )

        raw_input_map = spec.get("input_map", {}) if isinstance(spec, dict) else {}
        input_map = {
            str(action): str(skill_name)
            for action, skill_name in raw_input_map.items()
            if isinstance(action, str) and isinstance(skill_name, str) and skill_name in skills
        }
        if not input_map and skills:
            ordered = list(skills.keys())
            input_map["attack"] = ordered[0]
            if len(ordered) > 1:
                input_map["special"] = ordered[1]

        default_skill = spec.get("default_skill") if isinstance(spec, dict) else None
        if not isinstance(default_skill, str) or default_skill not in skills:
            default_skill = input_map.get("attack", next(iter(skills)))

        # Prune followups that reference unavailable skills
        for name, definition in list(skills.items()):
            valid_followups = {
                action: target
                for action, target in definition.followups.items()
                if target in skills
            }
            if valid_followups != definition.followups:
                skills[name] = SkillDefinition(
                    name=definition.name,
                    animation=definition.animation,
                    damage=definition.damage,
                    hit_frames=definition.hit_frames,
                    cooldown=definition.cooldown,
                    hitstop=definition.hitstop,
                    followups=valid_followups,
                )

        return skills, input_map, default_skill

    def _initialise(self) -> None:
        if pygame is None:
            return
        pygame.init()
        pygame.display.set_caption("StreetBattle 2.5D Prototype")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.sprite_sources.clear()
        requested_player = self.settings_manager.get("gameplay.player_character")
        requested_cpu = self.settings_manager.get("gameplay.cpu_character")
        player_key = self._resolve_player_key(str(requested_player).strip() if isinstance(requested_player, str) else None)
        cpu_key = self._resolve_cpu_key(player_key, str(requested_cpu).strip() if isinstance(requested_cpu, str) else None)
        player_entry = self.roster_map.get(player_key)
        cpu_entry = self.roster_map.get(cpu_key)
        if not player_entry or not cpu_entry:
            raise RuntimeError("Roster configuration 无法解析玩家或 CPU 角色。请检查 config/roster.json。")
        self.player = self._spawn_fighter(player_entry, (self.width * 0.35, self.floor_y), facing=1)
        self.cpu = self._spawn_fighter(cpu_entry, (self.width * 0.65, self.floor_y), facing=-1)
        self.ai = SimpleAIController(self.cpu)
        self.hud_font = pygame.font.SysFont("Segoe UI", 26)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == self.keymap.get("attack"):
                    self.attack_buffer = True
                elif event.key == self.keymap.get("special"):
                    self.special_buffer = True

    def _gather_player_inputs(self) -> Dict[str, bool]:
        pressed = pygame.key.get_pressed()
        inputs = {
            "left": pressed[self.keymap.get("left", pygame.K_a)],
            "right": pressed[self.keymap.get("right", pygame.K_d)],
            "attack": self.attack_buffer,
            "special": self.special_buffer,
        }
        self.attack_buffer = False
        self.special_buffer = False
        return inputs

    def _update(self, dt: float) -> None:
        if not self.player or not self.cpu or not self.ai:
            return
        player_inputs = self._gather_player_inputs()
        self.player.update(dt, player_inputs, self.cpu)
        ai_inputs = self.ai.compute_inputs(dt, self.player)
        self.cpu.update(dt, ai_inputs, self.player)

    def _render_health_bar(self, fighter: Fighter, position: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        x, y = position
        width, height = 360, 24
        ratio = fighter.health / fighter.max_health
        pygame.draw.rect(self.screen, (20, 24, 32), (x, y, width, height), border_radius=8)
        pygame.draw.rect(self.screen, color, (x + 2, y + 2, int((width - 4) * ratio), height - 4), border_radius=6)
        font = self.hud_font or pygame.font.SysFont("Segoe UI", 24)
        label = font.render(f"{fighter.name}  HP {fighter.health:03d}", True, (240, 240, 240))
        self.screen.blit(label, (x + 6, y - 30))

    def _render(self) -> None:
        if not self.player or not self.cpu:
            return
        self.screen.blit(self.background, (0, 0))
        self.player.draw(self.screen, self.floor_y)
        self.cpu.draw(self.screen, self.floor_y)
        self._render_health_bar(self.player, (80, 40), (230, 110, 120))
        self._render_health_bar(self.cpu, (self.width - 80 - 360, 40), (110, 180, 240))
        self._render_active_skill(self.player, (80, 90))
        self._render_active_skill(self.cpu, (self.width - 80, 90), align_right=True)
        if self.player.health <= 0 or self.cpu.health <= 0:
            winner = self.cpu.name if self.player.health <= 0 else self.player.name
            font = self.hud_font or pygame.font.SysFont("Segoe UI", 26)
            text = font.render(f"{winner} Wins! Press ESC to return", True, (255, 236, 184))
            rect = text.get_rect(center=(self.width // 2, self.height // 2))
            pygame.draw.rect(self.screen, (20, 22, 30, 200), rect.inflate(40, 20), border_radius=12)
            self.screen.blit(text, rect)
        if self.sprite_sources:
            attribution_font = pygame.font.SysFont("Segoe UI", 18)
            y = self.height - 18
            for key, src in self.sprite_sources.items():
                label = attribution_font.render(f"{key} sprites: {src}", True, (195, 210, 230))
                bg_rect = label.get_rect()
                bg_rect.bottomleft = (20, y)
                padded = bg_rect.inflate(12, 6)
                overlay = pygame.Surface(padded.size, pygame.SRCALPHA)
                overlay.fill((10, 12, 18, 160))
                self.screen.blit(overlay, padded.topleft)
                self.screen.blit(label, bg_rect)
                y -= 24
        pygame.display.flip()

    def _render_active_skill(self, fighter: Fighter, anchor: Tuple[int, int], align_right: bool = False) -> None:
        if not fighter.active_skill:
            return
        font = pygame.font.SysFont("Segoe UI", 18)
        label = font.render(fighter.active_skill.name.replace("_", " ").title(), True, (250, 232, 200))
        rect = label.get_rect()
        if align_right:
            rect.topright = anchor
        else:
            rect.topleft = anchor
        padded = rect.inflate(16, 8)
        background = pygame.Surface(padded.size, pygame.SRCALPHA)
        background.fill((14, 16, 26, 180))
        self.screen.blit(background, padded.topleft)
        self.screen.blit(label, rect)

    def _load_fighter_assets(self, key: str, label: Optional[str] = None) -> Tuple[Dict[str, SpriteAnimation], Dict[str, Any]]:
        pack = load_sprite_animations(key)
        if not pack:
            raise RuntimeError(
                f"Sprite manifest '{key}' is missing or invalid. "
                "请运行 tools/sync_sprites.py 同步资源，或确认 assets/sprites/{key}/manifest.json 正确配置。"
            )
        animations, metadata = pack
        if not animations:
            raise RuntimeError(f"Sprite manifest '{key}' did not provide any animations")
        descriptor = label or key
        source_text = ""
        if metadata and metadata.get("source"):
            source_text = str(metadata["source"])
        if metadata and metadata.get("license"):
            license_text = str(metadata["license"])
            source_text = f"{source_text} | {license_text}" if source_text else license_text
        if source_text:
            self.sprite_sources[descriptor] = source_text
        return animations, metadata

    def run(self) -> None:
        if pygame is None:
            raise RuntimeError("Pygame 未安装，无法运行 2.5D 模式。")
        self._initialise()
        self.running = True
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
        pygame.quit()


__all__ = ["SpriteBattleGame"]
