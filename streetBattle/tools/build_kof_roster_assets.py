#!/usr/bin/env python3
"""Generate the expanded KOF-inspired roster for StreetBattle's 2.5D mode.

The script produces three types of artefacts rooted in the existing martial hero
sprite pack:

* Per-fighter sprite manifests with unique colour palettes and timing tweaks
* ``config/roster.json`` describing metadata for all playable fighters
* ``config/skills.json`` entries matching each fighter's move set

It derives new manifests from the base ``assets/sprites/hero/manifest.json`` and
keeps the original hero/shadow definitions.  Running it is idempotent –
subsequent executions refresh the artefacts with the same deterministic output.
"""

from __future__ import annotations

import colorsys
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPRITES_ROOT = PROJECT_ROOT / "assets" / "sprites"
CONFIG_ROOT = PROJECT_ROOT / "config"
BASE_MANIFEST_PATH = SPRITES_ROOT / "hero" / "manifest.json"
ROSTER_CONFIG_PATH = CONFIG_ROOT / "roster.json"
SKILL_CONFIG_PATH = CONFIG_ROOT / "skills.json"


@dataclass(frozen=True)
class FighterSpec:
    key: str
    display_name: str
    team: str
    tempo: float
    power: float
    technique: float
    guard: float
    light_skill: str
    heavy_skill: str
    palette_hint: Tuple[float, float, float] | None = None  # hue (0-1), sat (0-1), val (0-1)


CORE_ROSTER: List[FighterSpec] = [
    FighterSpec("kyo_kusanagi", "Kyo Kusanagi", "Japan Team", 1.05, 1.10, 1.00, 0.98, "oni_yaki", "orochinagi", (0.03, 0.78, 0.95)),
    FighterSpec("benimaru_nikaido", "Benimaru Nikaido", "Japan Team", 1.08, 0.98, 1.12, 0.94, "ryusei_ken", "thunder_god_fist", (0.63, 0.70, 0.92)),
    FighterSpec("goro_daimon", "Goro Daimon", "Japan Team", 0.88, 1.30, 0.86, 1.18, "judo_chop", "earthquake_throw", (0.09, 0.52, 0.78)),
    FighterSpec("iori_yagami", "Iori Yagami", "Rival Team", 1.02, 1.18, 1.05, 0.99, "yamibarai", "yaotome", (0.76, 0.72, 0.88)),
    FighterSpec("chizuru_kagura", "Chizuru Kagura", "Sacred Treasures", 0.97, 0.92, 1.20, 1.02, "shinsoku_no_norito", "san_ate", (0.02, 0.42, 0.96)),
    FighterSpec("terry_bogard", "Terry Bogard", "Fatal Fury", 1.04, 1.16, 1.02, 0.97, "burn_knuckle", "buster_wolf", (0.00, 0.84, 0.90)),
    FighterSpec("andy_bogard", "Andy Bogard", "Fatal Fury", 1.06, 1.02, 1.08, 0.96, "zan_ei_ken", "shoryudan", (0.58, 0.62, 0.94)),
    FighterSpec("joe_higashi", "Joe Higashi", "Fatal Fury", 1.09, 0.96, 1.06, 0.95, "bakuretsu_punch", "screw_upper", (0.12, 0.76, 0.98)),
    FighterSpec("mai_shiranui", "Mai Shiranui", "Fatal Fury", 1.07, 0.94, 1.11, 0.93, "ryuenbu", "phoenix_fan", (0.97, 0.68, 0.96)),
    FighterSpec("ryo_sakazaki", "Ryo Sakazaki", "Art of Fighting", 1.00, 1.14, 1.02, 1.01, "ko_ou_ken", "hienshippukyaku", (0.08, 0.64, 0.90)),
    FighterSpec("robert_garcia", "Robert Garcia", "Art of Fighting", 1.03, 1.06, 1.05, 0.99, "ryu_ga", "gen_ei_kyaku", (0.58, 0.58, 0.88)),
    FighterSpec("yuri_sakazaki", "Yuri Sakazaki", "Art of Fighting", 1.10, 0.92, 1.14, 0.91, "ko_ouken", "haoh_shoukouken", (0.02, 0.52, 0.99)),
    FighterSpec("leona_heidern", "Leona Heidern", "Ikari Warriors", 1.08, 1.04, 1.08, 0.95, "moon_slash", "v_slasher", (0.55, 0.66, 0.92)),
    FighterSpec("ralf_jones", "Ralf Jones", "Ikari Warriors", 0.99, 1.24, 0.92, 1.08, "vulcan_punch", "galactica_phantom", (0.99, 0.76, 0.88)),
    FighterSpec("clark_still", "Clark Still", "Ikari Warriors", 0.94, 1.28, 0.90, 1.12, "gatling_attack", "argentine_backbreaker", (0.61, 0.54, 0.80)),
    FighterSpec("athena_asamiya", "Athena Asamiya", "Psycho Soldiers", 1.12, 0.90, 1.16, 0.90, "psycho_ball", "shining_crystal_bit", (0.85, 0.62, 0.96)),
    FighterSpec("sie_kensou", "Sie Kensou", "Psycho Soldiers", 1.05, 0.98, 1.05, 0.97, "dragon_punch", "senpuu_kyaku", (0.36, 0.68, 0.92)),
    FighterSpec("chin_gentsai", "Chin Gentsai", "Psycho Soldiers", 0.92, 1.00, 1.02, 1.05, "drunken_palm", "gourd_blast", (0.10, 0.38, 0.78)),
    FighterSpec("kim_kaphwan", "Kim Kaphwan", "Korea Justice", 1.13, 1.02, 1.10, 0.94, "hangetsu_zan", "houou_tenbu_kyaku", (0.53, 0.74, 0.96)),
    FighterSpec("chang_koehan", "Chang Koehan", "Korea Justice", 0.86, 1.32, 0.86, 1.22, "iron_ball_swing", "typhoon_crush", (0.08, 0.50, 0.72)),
    FighterSpec("choi_bounge", "Choi Bounge", "Korea Justice", 1.18, 0.94, 1.08, 0.90, "slash_saber", "mad_blade", (0.46, 0.78, 0.94)),
    FighterSpec("heidern", "Heidern", "Ikari Command", 0.98, 1.12, 1.05, 1.06, "cross_cutter", "final_bringer", (0.55, 0.50, 0.84)),
    FighterSpec("takuma_sakazaki", "Takuma Sakazaki", "Masters Team", 0.95, 1.26, 0.92, 1.10, "kyokugen_ryu_renbu", "haoh_shikouken", (0.05, 0.60, 0.78)),
    FighterSpec("king", "King", "Masters Team", 1.04, 0.96, 1.15, 0.92, "venom_strike", "double_strike", (0.14, 0.46, 0.88)),
    FighterSpec("kasumi_todo", "Kasumi Todoh", "Masters Team", 1.07, 0.94, 1.12, 0.94, "kasane_ate", "musou_shinza", (0.58, 0.52, 0.90)),
    FighterSpec("blue_mary", "Blue Mary", "Agents Team", 1.09, 1.00, 1.10, 0.93, "mary_tornado", "super_mary_typhoon", (0.13, 0.72, 0.96)),
    FighterSpec("ryuji_yamazaki", "Ryuji Yamazaki", "Agents Team", 1.00, 1.20, 1.02, 1.04, "serpent_slap", "guillotine", (0.09, 0.58, 0.82)),
    FighterSpec("geese_howard", "Geese Howard", "Agents Team", 0.96, 1.30, 1.00, 1.08, "reppuken", "raigun_storm", (0.58, 0.56, 0.86)),
    FighterSpec("billy_kane", "Billy Kane", "Outlaw Squad", 1.03, 1.08, 1.02, 0.99, "senpuukon", "power_cane", (0.02, 0.76, 0.92)),
    FighterSpec("yashiro_nanakase", "Yashiro Nanakase", "New Faces", 1.02, 1.18, 1.00, 1.00, "jet_counter", "final_impact", (0.02, 0.68, 0.80)),
    FighterSpec("shermie", "Shermie", "New Faces", 1.08, 0.98, 1.08, 0.95, "axel_spiral", "thunder_clap", (0.86, 0.58, 0.96)),
    FighterSpec("chris", "Chris", "New Faces", 1.15, 0.94, 1.12, 0.92, "dash_elbow", "twilight_blaze", (0.03, 0.58, 0.94)),
    FighterSpec("orochi_yashiro", "Orochi Yashiro", "Orochi", 1.00, 1.24, 1.04, 1.02, "void_counter", "hell_thrust", (0.65, 0.72, 0.90)),
    FighterSpec("orochi_shermie", "Orochi Shermie", "Orochi", 1.08, 1.00, 1.14, 0.96, "thunder_kiss", "storm_lariat", (0.81, 0.72, 0.96)),
    FighterSpec("orochi_chris", "Orochi Chris", "Orochi", 1.20, 1.02, 1.16, 0.94, "dark_dash", "catastrophe_spark", (0.58, 0.62, 0.94)),
    FighterSpec("orochi_leona", "Orochi Leona", "Orochi", 1.14, 1.10, 1.12, 0.96, "blood_moon_slash", "riot_of_blood", (0.92, 0.70, 0.92)),
    FighterSpec("orochi_iori", "Orochi Iori", "Orochi", 1.10, 1.26, 1.08, 0.98, "dark_flame_slash", "blood_yaotome", (0.80, 0.76, 0.90)),
    FighterSpec("rugal_bernstein", "Rugal Bernstein", "Boss", 0.99, 1.28, 1.06, 1.10, "dark_barrier", "gigantic_pressure", (0.62, 0.58, 0.80)),
    FighterSpec("omega_rugal", "Omega Rugal", "Boss", 1.04, 1.36, 1.04, 1.12, "genocide_cutter", "god_press", (0.72, 0.62, 0.82)),
    FighterSpec("shingo_yabuki", "Shingo Yabuki", "Rookie", 1.06, 0.96, 1.02, 0.94, "misogi_slap", "flame_strike", (0.04, 0.66, 0.92)),
    FighterSpec("whip", "Whip", "Ikari Command", 1.07, 1.04, 1.08, 0.97, "sonic_shot", "desert_trigger", (0.06, 0.46, 0.86)),
    FighterSpec("k_dash", "K'", "NESTS", 1.12, 1.10, 1.10, 0.96, "iron_trigger", "heat_drive", (0.08, 0.60, 0.90)),
    FighterSpec("maxima", "Maxima", "NESTS", 0.92, 1.32, 0.94, 1.18, "m24_blaster", "maxima_press", (0.55, 0.48, 0.82)),
]


CORE_SKILLS: Dict[str, Dict[str, Any]] = {
    "hero": {
        "default_skill": "light_strike",
        "input_map": {"attack": "light_strike", "special": "heavy_strike"},
        "skills": [
            {
                "name": "light_strike",
                "animation": "attack_light",
                "damage": 10,
                "cooldown": 0.65,
                "hit_frames": [2, 3],
                "hitstop": 0.18,
                "followups": {"special": "heavy_strike"},
            },
            {
                "name": "heavy_strike",
                "animation": "attack_heavy",
                "damage": 18,
                "cooldown": 1.25,
                "hit_frames": [3, 4],
                "hitstop": 0.24,
            },
        ],
    },
    "shadow": {
        "default_skill": "shadow_jab",
        "input_map": {"attack": "shadow_jab", "special": "void_spike"},
        "skills": [
            {
                "name": "shadow_jab",
                "animation": "attack_light",
                "damage": 9,
                "cooldown": 0.6,
                "hit_frames": [2, 3],
                "hitstop": 0.17,
            },
            {
                "name": "void_spike",
                "animation": "attack_heavy",
                "damage": 16,
                "cooldown": 1.1,
                "hit_frames": [2, 3, 4],
                "hitstop": 0.22,
            },
        ],
    },
}


def _load_base_manifest() -> Dict[str, Any]:
    if not BASE_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Base manifest not found: {BASE_MANIFEST_PATH}")
    with BASE_MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _build_palette(index: int, spec: FighterSpec) -> Dict[str, Iterable[float | int]]:
    hue, sat, val = spec.palette_hint if spec.palette_hint else (
        (index * 0.079) % 1.0,
        0.58 + ((index % 5) * 0.07),
        0.74 + ((index % 3) * 0.08),
    )
    hue = hue % 1.0
    sat = _clamp(sat, 0.35, 0.92)
    val = _clamp(val, 0.65, 0.98)
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    multiply = [round(0.70 + r * 0.55, 3), round(0.70 + g * 0.55, 3), round(0.70 + b * 0.55, 3)]
    add = [int(6 + r * 60), int(6 + g * 60), int(6 + b * 60)]
    return {"multiply": multiply, "add": add}


def _scale_fps(base: int, tempo: float, bias: float = 1.0) -> int:
    scaled = base * (0.85 + tempo * 0.25 * bias)
    return int(_clamp(round(scaled), max(4, int(base * 0.7)), min(20, int(base * 1.5))))


def _scale_durations(durations: Iterable[float], tempo: float, weight: float) -> List[float]:
    result: List[float] = []
    modifier = _clamp((1.0 / tempo) * (0.9 + weight * 0.15), 0.5, 1.5)
    for value in durations:
        result.append(round(_clamp(value * modifier, 0.04, 0.32), 3))
    return result


def _build_manifest(base_manifest: Dict[str, Any], spec: FighterSpec, index: int) -> Dict[str, Any]:
    manifest = deepcopy(base_manifest)
    manifest["name"] = spec.key
    manifest["display_name"] = spec.display_name
    manifest.setdefault("metadata", {})
    manifest["metadata"]["team"] = spec.team
    manifest["metadata"]["tempo"] = spec.tempo
    manifest["metadata"]["power"] = spec.power
    manifest["metadata"]["technique"] = spec.technique
    manifest["color_mod"] = _build_palette(index, spec)
    for state_name, state in manifest.get("states", {}).items():
        sheet = state.get("sheet")
        if isinstance(sheet, str) and not sheet.startswith("../"):
            state["sheet"] = f"../hero/{sheet}"
        fps = state.get("fps")
        if isinstance(fps, (int, float)):
            bias = 1.0
            if state_name in {"idle", "walk"}:
                bias = 1.05 if spec.tempo > 1.05 else 0.95
            if state_name.startswith("attack"):
                bias = 1.1 if spec.power >= 1.15 else 0.98
            if state_name in {"hurt", "ko"}:
                bias = 0.85 + (spec.guard - 1.0) * 0.3
            state["fps"] = _scale_fps(int(fps), spec.tempo, bias=bias)
        if "durations" in state:
            durations = state.get("durations")
            if isinstance(durations, list) and durations:
                state["durations"] = _scale_durations(durations, spec.tempo, spec.guard)
        if state_name.startswith("attack"):
            base_hits = state.get("hit_frames")
            if isinstance(base_hits, list) and base_hits:
                tweaked: List[int] = []
                lead = -1 if spec.technique > 1.1 else 0
                for frame in base_hits:
                    tweaked.append(int(max(1, frame + lead)))
                state["hit_frames"] = sorted(set(tweaked))
    return manifest


def _build_skill_entry(spec: FighterSpec, hit_frame_map: Dict[str, Iterable[int]]) -> Dict[str, Any]:
    tempo = spec.tempo
    power = spec.power
    technique = spec.technique
    guard = spec.guard

    def clamp_float(value: float, lower: float, upper: float) -> float:
        return float(_clamp(value, lower, upper))

    light_damage = int(round(9 + power * 6 + technique * 2))
    heavy_damage = int(round(16 + power * 8 + guard * 3))
    light_cooldown = clamp_float(0.5 + (1.0 - tempo) * 0.25, 0.42, 0.78)
    heavy_cooldown = clamp_float(0.95 + (1.1 - tempo) * 0.35 + (guard - 1.0) * 0.12, 0.8, 1.35)
    light_hitstop = clamp_float(0.15 + (guard - 1.0) * 0.1 + technique * 0.02, 0.14, 0.26)
    heavy_hitstop = clamp_float(0.2 + (guard - 1.0) * 0.12 + power * 0.03, 0.18, 0.32)

    light_hits = list(hit_frame_map.get("attack_light", [2, 3]))
    heavy_hits = list(hit_frame_map.get("attack_heavy", [3, 4]))

    followups = {}
    if technique >= 1.08:
        followups["special"] = spec.heavy_skill
    elif tempo >= 1.12:
        followups["attack"] = spec.light_skill

    return {
        "default_skill": spec.light_skill,
        "input_map": {"attack": spec.light_skill, "special": spec.heavy_skill},
        "skills": [
            {
                "name": spec.light_skill,
                "animation": "attack_light",
                "damage": light_damage,
                "cooldown": round(light_cooldown, 2),
                "hit_frames": [int(value) for value in light_hits],
                "hitstop": round(light_hitstop, 2),
                "followups": followups,
            },
            {
                "name": spec.heavy_skill,
                "animation": "attack_heavy",
                "damage": heavy_damage,
                "cooldown": round(heavy_cooldown, 2),
                "hit_frames": [int(value) for value in heavy_hits],
                "hitstop": round(heavy_hitstop, 2),
            },
        ],
    }


def _manifest_metadata(manifest: Dict[str, Any]) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    state_meta = manifest.get("states", {})
    for name in ("attack_light", "attack_heavy"):
        state = state_meta.get(name, {})
        if isinstance(state, dict) and "hit_frames" in state:
            metadata.setdefault("hit_frames", {})[name] = state["hit_frames"]
    if "metadata" in manifest:
        metadata.update({k: v for k, v in manifest["metadata"].items() if k not in metadata})
    if manifest.get("source"):
        metadata.setdefault("source", manifest["source"])
    if manifest.get("license"):
        metadata.setdefault("license", manifest["license"])
    return metadata


def build_assets() -> None:
    base_manifest = _load_base_manifest()
    roster_entries: List[Dict[str, Any]] = []
    skill_entries: Dict[str, Any] = deepcopy(CORE_SKILLS)

    for index, spec in enumerate(CORE_ROSTER):
        manifest = _build_manifest(base_manifest, spec, index)
        manifest_dir = SPRITES_ROOT / spec.key
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "manifest.json"
        with manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=4, ensure_ascii=False)
        roster_entries.append(
            {
                "key": spec.key,
                "display_name": spec.display_name,
                "team": spec.team,
                "manifest": spec.key,
                "skill_profile": spec.key,
                "tempo": spec.tempo,
                "power": spec.power,
                "technique": spec.technique,
                "guard": spec.guard,
            }
        )
        metadata = _manifest_metadata(manifest)
        skill_entries[spec.key] = _build_skill_entry(spec, metadata.get("hit_frames", {}))

    roster_payload = {
        "fighters": roster_entries,
        "default_player": "kyo_kusanagi",
        "default_cpu": "iori_yagami",
        "version": 1,
    }
    with ROSTER_CONFIG_PATH.open("w", encoding="utf-8") as roster_file:
        json.dump(roster_payload, roster_file, indent=4, ensure_ascii=False)

    with SKILL_CONFIG_PATH.open("w", encoding="utf-8") as skills_file:
        json.dump(skill_entries, skills_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    build_assets()
    print("Roster assets regenerated.")
