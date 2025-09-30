from __future__ import annotations

"""Pygame-powered 2.5D fighting mode for StreetBattle."""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - allow running 3D mode without pygame
    import pygame
except ImportError:  # pragma: no cover - handled by launcher at runtime
    pygame = None  # type: ignore
from ..config import SettingsManager
from .fighter import Fighter, SimpleAIController, SkillDefinition
from .sprites import _load_sprite_manifest, clone_animations_with_color, load_sprite_animations
from .ui import HudRenderer, MatchSetupScreen

DEFAULT_TIMER_SECONDS = 120.0
DEFAULT_THEME = "arena"
_SECONDARY_KEY_NAMES: Dict[str, List[str]] = {
    "left": ["left", "a"],
    "right": ["right", "d"],
    "up": ["up", "w"],
    "down": ["down", "s"],
    "attack": ["j", "z", "lctrl"],
    "special": ["k", "x", "lalt"],
    "jump": ["space", "w", "up"],
    "help": ["h", "f1"],
}
_PALETTE_VARIANTS: List[Dict[str, Iterable[float]]] = [
    {"multiply": [1.08, 0.92, 1.0], "add": [12, 6, 18]},
    {"multiply": [0.9, 1.05, 1.15], "add": [0, 12, 32]},
    {"multiply": [1.02, 1.0, 0.88], "add": [18, 10, 6]},
]


class _SkillProfile:
    def __init__(self, skills: Dict[str, SkillDefinition], input_map: Dict[str, str], default_skill: str) -> None:
        self.skills = skills
        self.input_map = input_map
        self.default_skill = default_skill


@dataclass(frozen=True)
class _HelpContent:
    overlay: List[str]
    hint: str


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _stat_multiplier(value: Any, *, step: float = 0.12) -> float:
    if value is None:
        return 1.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 1.0
    normalized = _clamp(numeric, 1.0, 5.0)
    return 1.0 + (normalized - 3.0) * step


def _palette_for_index(entry: Dict[str, Any], variant_index: int) -> Optional[Dict[str, Iterable[float]]]:
    palette_config = entry.get("palette")
    if isinstance(palette_config, list) and palette_config:
        return palette_config[variant_index % len(palette_config)]
    if isinstance(palette_config, dict):
        return palette_config
    if not _PALETTE_VARIANTS:
        return None
    return _PALETTE_VARIANTS[variant_index % len(_PALETTE_VARIANTS)]


def _format_keys(key_codes: Iterable[int]) -> str:
    if pygame is None:
        return ""
    names: List[str] = []
    for code in key_codes:
        try:
            names.append(pygame.key.name(code).upper())
        except ValueError:
            continue
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} / {names[1]}"
    return ", ".join(names[:-1]) + f" / {names[-1]}"


class SpriteBattleGame:
    """Main coordinator for the StreetBattle 2.5D mode."""

    def __init__(self, settings_manager: Optional[SettingsManager] = None) -> None:
        if pygame is None:
            raise RuntimeError("Pygame 未安装，无法启动 2.5D 模式。请使用 `pip install pygame` 安装。")

        self.settings_manager = settings_manager or SettingsManager()
        graphics = self.settings_manager.get("graphics", {}) or {}
        resolution = graphics.get("resolution", [1280, 720])
        if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
            resolution = [1280, 720]
        self.width = int(max(960, resolution[0]))
        self.height = int(max(600, resolution[1]))
        self.fullscreen = bool(graphics.get("fullscreen", False))
        self.vsync = bool(graphics.get("vsync", True))

        ui_config = self.settings_manager.get("ui", {}) or {}
        self.theme_name = str(ui_config.get("theme", DEFAULT_THEME))
        timer_value = ui_config.get("timer_seconds", DEFAULT_TIMER_SECONDS)
        try:
            self.match_time_limit = float(timer_value)
        except (TypeError, ValueError):
            self.match_time_limit = DEFAULT_TIMER_SECONDS
        self.match_time_limit = _clamp(self.match_time_limit, 30.0, 300.0)
        self.show_hints = bool(ui_config.get("show_hints", True))

        self.screen: Any = None
        self.clock: Any = None
        self.hud: Optional[HudRenderer] = None
        self.floor_y = int(self.height * 0.82)

        self.keymap: Dict[str, List[int]] = {}
        self.help_content: _HelpContent = _HelpContent([], "H: 显示帮助 / Show Help")
        self.help_visible = False
        self.sprite_sources: Dict[str, str] = {}

        self.player: Optional[Fighter] = None
        self.cpu: Optional[Fighter] = None
        self.ai: Optional[SimpleAIController] = None

        self.attack_buffer = False
        self.special_buffer = False

        self.time_remaining = self.match_time_limit
        self.match_over = False
        self.winner_name: Optional[str] = None
        self.banner_message: Optional[str] = None
        self.banner_timer = 0.0
        self.slowmo_timer = 0.0
        self.shake_timer = 0.0
        self.shake_total = 0.0
        self.shake_strength = 0.0
        self.shake_offset = (0.0, 0.0)
        self.last_player_health: Optional[int] = None
        self.last_cpu_health: Optional[int] = None

        self.running = False
        self.keep_running = True

        self.skill_config = self._load_skill_config()
        self.roster_map, self.roster_order = self._load_roster_config()
        self.current_player_key: Optional[str] = None
        self.current_cpu_key: Optional[str] = None

    # ------------------------------------------------------------------
    # Configuration loading helpers
    # ------------------------------------------------------------------
    def _load_skill_config(self) -> Dict[str, Any]:
        skills_path = Path(__file__).resolve().parents[1] / "config" / "skills.json"
        if not skills_path.exists():
            return {}
        try:
            with skills_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:  # pragma: no cover - configuration error surface
            raise RuntimeError(f"无法解析技能配置文件: {skills_path}") from exc

    def _load_unified_roster_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Return lightweight roster metadata from the shared character configuration file."""

        roster_candidates = [
            Path(__file__).resolve().parents[1] / "config" / "characters" / "unified_roster.json",
            Path(__file__).resolve().parents[1] / "config" / "characters" / "manifest.json",
        ]

        payload: Dict[str, Dict[str, Any]] = {}
        for candidate in roster_candidates:
            if not candidate.exists():
                continue
            try:
                with candidate.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if isinstance(data, dict) and "characters" in data:
                    data = data["characters"]
                if isinstance(data, list):
                    temp: Dict[str, Dict[str, Any]] = {}
                    for entry in data:
                        if isinstance(entry, dict):
                            char_id = str(entry.get("id") or entry.get("name") or "").strip().lower()
                            if char_id:
                                temp[char_id] = entry
                    if temp:
                        payload = temp
                        break
                elif isinstance(data, dict):
                    payload = {str(k).lower(): v for k, v in data.items() if isinstance(v, dict)}
                    if payload:
                        break
            except Exception:
                continue
        return payload

    def _load_roster_config(self) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        roster_path = Path(__file__).resolve().parents[1] / "config" / "roster.json"
        roster_meta = self._load_unified_roster_metadata()

        roster_map: Dict[str, Dict[str, Any]] = {}
        order: List[str] = []
        default_player: Optional[str] = None
        default_cpu: Optional[str] = None

        def _normalise_key(value: Optional[str]) -> Optional[str]:
            if not value:
                return None
            key = str(value).strip()
            return key.lower() if key else None

        def _merge_roster_entry(char_id: str, source: Optional[Dict[str, Any]] = None) -> None:
            key = _normalise_key(char_id)
            if not key:
                return
            existing = roster_map.get(key, {}).copy()
            roster_info = roster_meta.get(key, {}) if roster_meta else {}
            source = source or {}

            display_name = source.get("display_name") or roster_info.get("display_name")
            if not display_name:
                display_name = key.replace("_", " ").title()

            manifest_name = source.get("manifest") or roster_info.get("manifest") or key
            skill_profile = source.get("skill_profile") or roster_info.get("skill_profile") or key

            def _stat(name: str, fallback: float = 3.0) -> float:
                value = source.get(name)
                if value is None:
                    value = roster_info.get(name)
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return fallback

            merged = {
                "key": key,
                "display_name": str(display_name),
                "manifest": str(manifest_name),
                "skill_profile": str(skill_profile),
                "team": source.get("team") or roster_info.get("team"),
                "tempo": _stat("tempo"),
                "power": _stat("power"),
                "technique": _stat("technique"),
                "guard": _stat("guard"),
                "palette": source.get("palette") or roster_info.get("palette"),
            }
            existing.update({k: v for k, v in merged.items() if v is not None})
            roster_map[key] = existing
            if key not in order:
                order.append(key)

        if roster_path.exists():
            try:
                with roster_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict):
                    default_player = _normalise_key(payload.get("default_player"))
                    default_cpu = _normalise_key(payload.get("default_cpu"))
                    fighters = payload.get("fighters", [])
                else:
                    fighters = []

                if isinstance(fighters, list):
                    for entry in fighters:
                        if isinstance(entry, str):
                            _merge_roster_entry(entry)
                        elif isinstance(entry, dict):
                            key = entry.get("key") or entry.get("id") or entry.get("name")
                            _merge_roster_entry(key or "", entry)
                elif isinstance(fighters, dict):
                    for key, entry in fighters.items():
                        if isinstance(entry, dict):
                            _merge_roster_entry(key, entry)
            except Exception as exc:  # pragma: no cover
                raise RuntimeError(f"无法解析角色配置文件: {roster_path}") from exc

        if not roster_map and roster_meta:
            # Fallback: use sprite-ready characters from the unified roster metadata
            for char_id, info in roster_meta.items():
                if info.get("has_sprite"):
                    _merge_roster_entry(char_id, info)
                if len(roster_map) >= 12:
                    break

        if not roster_map:
            print("Warning: No roster configuration found. Only characters with portraits will be available.")
            return {}, []

        # Ensure defaults are present and the order is stable.
        if default_player and default_player in roster_map:
            if default_player in order:
                order.remove(default_player)
            order.insert(0, default_player)

        if default_cpu and default_cpu in roster_map:
            if default_cpu in order:
                order.remove(default_cpu)
            if not order or order[0] != default_cpu:
                order.append(default_cpu)

        # Guarantee at least two roster entries to avoid startup crashes.
        if not order:
            order.extend(list(roster_map.keys())[:8])
        if len(order) == 1:
            solo = order[0]
            fallback = next((key for key in roster_map if key != solo), solo)
            if fallback not in order:
                order.append(fallback)

        return roster_map, order

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _boot_display(self) -> None:
        if pygame is None:
            return
        if not pygame.get_init():
            pygame.init()
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("StreetBattle 2.5D")
        if not self.vsync and hasattr(pygame.display, "gl_set_swap_interval"):
            try:
                pygame.display.gl_set_swap_interval(0)
            except Exception:
                pass
        self.clock = pygame.time.Clock()
        self.hud = HudRenderer(self.width, self.height, self.floor_y, theme_name=self.theme_name)
        self.keymap = self._build_keymap()
        self.help_content = self._build_help_content()

    def run(self) -> None:
        self._boot_display()
        if self.screen is None or self.clock is None:
            return
        requested_player = self.settings_manager.get("gameplay.player_character")
        requested_cpu = self.settings_manager.get("gameplay.cpu_character")
        while self.keep_running:
            selection = self._run_match_setup(
                str(requested_player) if requested_player else None,
                str(requested_cpu) if requested_cpu else None,
            )
            if selection is None:
                break
            self.current_player_key, self.current_cpu_key = selection
            requested_player, requested_cpu = selection
            if not self._battle_loop():
                break
        pygame.quit()

    # ------------------------------------------------------------------
    # Match setup
    # ------------------------------------------------------------------
    def _run_match_setup(self, player_key: Optional[str], cpu_key: Optional[str]) -> Optional[Tuple[str, str]]:
        if self.screen is None or self.clock is None:
            return None
        if not self.roster_order:
            raise RuntimeError("Roster configuration is empty. 请检查 config/roster.json 或统一角色清单。")
        if len(self.roster_order) == 1:
            base = self.roster_order[0]
            return base, base
        setup = MatchSetupScreen(
            self.screen,
            self.clock,
            self.roster_map,
            self.roster_order,
            theme_name=self.theme_name,
        )
        selection = setup.run(player_key or self.roster_order[0], cpu_key or self._alternative_key(player_key))
        if selection is None:
            self.keep_running = False
            return None
        player_key, cpu_key = selection
        self.settings_manager.set("gameplay.player_character", player_key, persist=False)
        self.settings_manager.set("gameplay.cpu_character", cpu_key, persist=False)
        return player_key, cpu_key

    def _alternative_key(self, current: Optional[str]) -> str:
        if not self.roster_order:
            return ""
        if current in self.roster_order and len(self.roster_order) > 1:
            idx = (self.roster_order.index(current) + 1) % len(self.roster_order)
            return self.roster_order[idx]
        return self.roster_order[0]

    def _battle_loop(self) -> bool:
        self.running = True
        self._initialise_match()
        while self.running and self.keep_running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
        return self.keep_running

    def _initialise_match(self) -> None:
        if pygame is None:
            return
        if not self.roster_order:
            raise RuntimeError("Roster configuration is empty，无法初始化比赛。")
        if not self.current_player_key:
            self.current_player_key = self.roster_order[0]
        if not self.current_cpu_key:
            opponent = self._alternative_key(self.current_player_key)
            self.current_cpu_key = opponent or self.roster_order[0]
        self.sprite_sources = {}
        self.player = self._spawn_fighter(
            self.current_player_key,
            (self.width * 0.32, self.floor_y),
            facing=1,
            palette_index=0,
        )
        cpu_palette = 0
        if self.current_cpu_key == self.current_player_key:
            cpu_palette = 1
        self.cpu = self._spawn_fighter(
            self.current_cpu_key,
            (self.width * 0.68, self.floor_y),
            facing=-1,
            palette_index=cpu_palette,
        )
        self.ai = SimpleAIController(self.cpu)
        self.time_remaining = self.match_time_limit
        self.match_over = False
        self.winner_name = None
        self.attack_buffer = False
        self.special_buffer = False
        self.help_visible = False
        self.banner_message = "准备！Fight!"
        self.banner_timer = 1.6
        self.slowmo_timer = 0.0
        self.shake_timer = 0.0
        self.shake_total = 0.0
        self.shake_strength = 0.0
        self.shake_offset = (0.0, 0.0)
        self.last_player_health = self.player.health if self.player else None
        self.last_cpu_health = self.cpu.health if self.cpu else None

    # ------------------------------------------------------------------
    # Fighter creation
    # ------------------------------------------------------------------
    def _spawn_fighter(self, key: str, position: Tuple[float, float], *, facing: int, palette_index: int) -> Fighter:
        entry = self.roster_map.get(key)
        if not entry:
            raise RuntimeError(f"Roster entry '{key}' 不存在，无法创建角色")
        animations, metadata = self._load_fighter_assets(entry, descriptor=entry.get("display_name", key))
        color_mod = _palette_for_index(entry, palette_index)
        if color_mod:
            animations = clone_animations_with_color(animations, color_mod)
        skill_key = str(entry.get("skill_profile") or key)
        skill_profile = self._build_skill_profile(skill_key, metadata, animations)
        fighter = Fighter(
            name=str(entry.get("display_name", key.replace("_", " ").title())),
            position=position,
            animations=animations,
            skills=skill_profile.skills,
            input_map=skill_profile.input_map,
            default_skill=skill_profile.default_skill,
            facing=facing,
            stage_width=self.width,
        )
        self._apply_attribute_modifiers(fighter, entry)
        return fighter

    def _load_fighter_assets(self, entry: Dict[str, Any], descriptor: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        manifest_key = str(entry.get("manifest") or entry.get("key"))
        pack = load_sprite_animations(manifest_key)
        if not pack:
            raise RuntimeError(
                f"Sprite manifest '{manifest_key}' 缺失或无效。请运行 tools/sync_sprites.py 同步资源。"
            )
        animations, metadata = pack
        source_text = ""
        if metadata and metadata.get("source"):
            source_text = str(metadata["source"])
        if metadata and metadata.get("license"):
            license_text = str(metadata["license"])
            source_text = f"{source_text} | {license_text}" if source_text else license_text
        if source_text:
            self.sprite_sources[descriptor] = source_text
        return animations, metadata

    def _build_skill_profile(
        self,
        key: str,
        metadata: Dict[str, Any],
        animations: Dict[str, Any],
    ) -> _SkillProfile:
        spec = self.skill_config.get(key, {}) if isinstance(self.skill_config, dict) else {}
        raw_skills = spec.get("skills", []) if isinstance(spec, dict) else []
        hit_lookup: Dict[str, Iterable[int]] = metadata.get("hit_frames", {}) if metadata else {}
        skills: Dict[str, SkillDefinition] = {}

        def _default_hit_frames(animation_name: str) -> Tuple[int, ...]:
            anim = animations.get(animation_name)
            if not anim:
                return (2, 3)
            frames = getattr(anim, "frames", [])
            total = len(frames)
            if total <= 2:
                return tuple(range(total)) or (0,)
            mid_start = max(1, total // 2 - 1)
            mid_end = min(total, mid_start + 2)
            return tuple(range(mid_start, mid_end))

        for entry in raw_skills:
            if not isinstance(entry, dict):
                continue
            animation_name = entry.get("animation")
            if not animation_name or animation_name not in animations:
                continue
            name = str(entry.get("name") or animation_name)
            hit_frames_spec = entry.get("hit_frames")
            if isinstance(hit_frames_spec, (list, tuple)) and hit_frames_spec:
                hit_frames = tuple(int(i) for i in hit_frames_spec)
            else:
                fallback = hit_lookup.get(animation_name) or metadata.get("attack_frames") if metadata else None
                hit_frames = tuple(int(i) for i in fallback) if fallback else _default_hit_frames(animation_name)
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
                animation=animation_name,
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

        # Prune invalid follow-ups to avoid stale references.
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

        return _SkillProfile(skills, input_map, default_skill)

    def _apply_attribute_modifiers(self, fighter: Fighter, entry: Dict[str, Any]) -> None:
        tempo_mult = _stat_multiplier(entry.get("tempo"), step=0.14)
        power_mult = _stat_multiplier(entry.get("power"), step=0.18)
        technique_mult = _stat_multiplier(entry.get("technique"), step=0.15)
        guard_mult = _stat_multiplier(entry.get("guard"), step=0.2)
        stamina_mult = _stat_multiplier(entry.get("guard"), step=0.18)
        cooldown_mult = _clamp(1.0 / technique_mult, 0.5, 1.2)
        fighter.apply_tuning(
            speed=_clamp(tempo_mult, 0.6, 1.5),
            damage=_clamp(power_mult, 0.7, 1.8),
            cooldown=cooldown_mult,
            stamina=_clamp(stamina_mult, 0.6, 1.8),
            guard=_clamp(guard_mult, 0.6, 1.8),
            hitstop=1.0,
            jump=_clamp(tempo_mult, 0.7, 1.4),
        )

    def _trigger_camera_shake(self, damage: int) -> None:
        self.shake_timer = 0.25
        self.shake_total = self.shake_timer
        self.shake_strength = min(18.0, 6.0 + max(0, damage) * 1.6)

    def _advance_camera_shake(self, dt: float) -> None:
        if self.shake_timer <= 0.0:
            self.shake_offset = (0.0, 0.0)
            return
        self.shake_timer = max(0.0, self.shake_timer - dt)
        duration = max(0.001, self.shake_total)
        damping = self.shake_timer / duration
        strength = self.shake_strength * damping
        self.shake_offset = (
            random.uniform(-1.0, 1.0) * strength,
            random.uniform(-0.6, 0.6) * strength * 0.6,
        )
        if self.shake_timer <= 0.0:
            self.shake_offset = (0.0, 0.0)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def _build_keymap(self) -> Dict[str, List[int]]:
        mapping = self.settings_manager.get("controls.keyboard", {}) or {}
        keymap: Dict[str, List[int]] = {}
        for action, default_names in _SECONDARY_KEY_NAMES.items():
            codes: List[int] = []
            custom = mapping.get(action)
            if custom:
                codes.extend(self._to_key_codes([str(custom)]))
            codes.extend(self._to_key_codes(default_names))
            keymap[action] = list(dict.fromkeys(codes))
        return keymap

    def _to_key_codes(self, names: Iterable[str]) -> List[int]:
        if pygame is None:
            return []
        codes: List[int] = []
        for name in names:
            try:
                codes.append(pygame.key.key_code(str(name).lower()))
            except (ValueError, KeyError):
                continue
        return codes

    def _build_help_content(self) -> _HelpContent:
        if pygame is None:
            return _HelpContent([], "")

        def _describe(action: str) -> str:
            text = _format_keys(self.keymap.get(action, []))
            return text or "未绑定"

        overlay: List[str] = []
        overlay.append("控制 / Controls")
        overlay.append(f"移动 Move: {_describe('left')} / {_describe('right')}")
        overlay.append(f"跳跃 Jump: {_describe('jump')}")
        overlay.append(f"攻击 Attack: {_describe('attack')}")
        overlay.append(f"必杀 Special: {_describe('special')}")
        overlay.append("")
        help_key = _format_keys(self.keymap.get("help", [])) or "H"
        overlay.append("系统 / System")
        overlay.append("Enter: 重新开战   Esc: 返回角色选择")
        overlay.append(f"{help_key}: 隐藏帮助 / Hide Help")
        return _HelpContent(overlay=overlay, hint=f"{help_key}: 显示帮助 / Show Help")

    def _handle_events(self) -> None:
        if pygame is None:
            return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.keep_running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                if event.key in self.keymap.get("attack", []):
                    self.attack_buffer = True
                if event.key in self.keymap.get("special", []):
                    self.special_buffer = True
                if event.key in self.keymap.get("help", []):
                    self.help_visible = not self.help_visible
                if self.match_over and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._initialise_match()

    def _gather_player_inputs(self) -> Dict[str, bool]:
        pressed = pygame.key.get_pressed()

        def _pressed(action: str) -> bool:
            return any(pressed[code] for code in self.keymap.get(action, []) if code < len(pressed))

        inputs = {
            "left": _pressed("left"),
            "right": _pressed("right"),
            "up": _pressed("up"),
            "down": _pressed("down"),
            "attack": self.attack_buffer or _pressed("attack"),
            "special": self.special_buffer or _pressed("special"),
            "jump": _pressed("jump"),
        }
        self.attack_buffer = False
        self.special_buffer = False
        return inputs

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------
    def _update(self, dt: float) -> None:
        if not self.player or not self.cpu or not self.ai:
            return
        if self.banner_timer > 0.0:
            self.banner_timer = max(0.0, self.banner_timer - dt)
            if self.banner_timer <= 0.0:
                self.banner_message = None

        if not self.match_over:
            self.time_remaining = max(0.0, self.time_remaining - dt)
            effective_dt = dt
        else:
            if self.slowmo_timer > 0.0:
                self.slowmo_timer = max(0.0, self.slowmo_timer - dt)
            effective_dt = dt * (0.35 if self.slowmo_timer > 0.0 else 1.0)

        prev_player_health = self.player.health
        prev_cpu_health = self.cpu.health

        player_inputs = self._gather_player_inputs()
        self.player.update(effective_dt, player_inputs, self.cpu)
        ai_inputs = self.ai.compute_inputs(effective_dt, self.player)
        self.cpu.update(effective_dt, ai_inputs, self.player)

        player_damage = max(0, prev_player_health - self.player.health)
        cpu_damage = max(0, prev_cpu_health - self.cpu.health)
        if player_damage > 0:
            self._trigger_camera_shake(player_damage)
        elif cpu_damage > 0:
            self._trigger_camera_shake(cpu_damage)
        self._advance_camera_shake(dt)
        self.last_player_health = self.player.health
        self.last_cpu_health = self.cpu.health

        if not self.match_over:
            if self.player.health <= 0 or self.cpu.health <= 0:
                winner = self.cpu.name if self.player.health <= 0 else self.player.name
                self._end_match(winner)
            elif self.time_remaining <= 0.0:
                if self.player.health == self.cpu.health:
                    self._end_match(None)
                elif self.player.health > self.cpu.health:
                    self._end_match(self.player.name)
                else:
                    self._end_match(self.cpu.name)

    def _end_match(self, winner: Optional[str]) -> None:
        self.match_over = True
        self.winner_name = winner
        self.banner_message = "时间到!" if winner is None else f"{winner} 胜利!"
        self.banner_timer = 3.2
        self.slowmo_timer = 1.2

    def _render(self) -> None:
        if self.screen is None or self.hud is None or not self.player or not self.cpu:
            return
        offset = (int(self.shake_offset[0]), int(self.shake_offset[1]))
        self.screen.fill((8, 10, 16))
        self.hud.draw_background(self.screen, offset)
        self.player.draw(self.screen, self.floor_y, offset)
        self.cpu.draw(self.screen, self.floor_y, offset)
        self.hud.draw(
            self.screen,
            player=self.player,
            cpu=self.cpu,
            time_remaining=self.time_remaining,
            match_over=self.match_over,
            winner=self.winner_name,
            sprite_sources=self.sprite_sources,
            help_overlay=self.help_content.overlay,
            show_help=self.help_visible,
            help_hint=self.help_content.hint,
            banner_text=self.banner_message,
        )
        pygame.display.flip()


__all__ = [
    "SpriteBattleGame",
    "SettingsManager",
    "load_sprite_animations",
    "_load_sprite_manifest",
]
