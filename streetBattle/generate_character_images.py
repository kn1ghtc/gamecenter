#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenAI 图像模型驱动的 StreetBattle 角色资源生成器.

该脚本利用 OpenAI 的最新图像模型批量生成角色肖像和 2.5D 精灵帧, 同时
输出完整的提示词与元数据, 方便在美术审核或后续再训练时追踪来源。
"""

from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - optional dependency is validated at runtime
    from openai import OpenAI
    from openai import OpenAIError
except ImportError:  # pragma: no cover - handled gracefully in class
    OpenAI = None  # type: ignore[assignment]
    OpenAIError = Exception  # type: ignore[assignment]

from gamecenter.streetBattle.config import SettingsManager


@dataclass(slots=True)
class CharacterSpec:
    """角色图像生成所需的最小数据集."""

    identifier: str
    display_name: str
    description: str
    appearance: str
    fighting_style: str
    colors: str
    signature_moves: Tuple[str, ...] = field(default_factory=tuple)


class CharacterImageGenerator:
    """封装 OpenAI 图像生成流程, 输出高质量素材与元数据."""

    DEFAULT_POSES: Tuple[str, ...] = (
        "combat stance",
        "signature attack pose",
        "victory celebration",
        "defensive guard position",
        "special move preparation",
        "jumping attack pose",
    )

    SPRITE_STATES: Dict[str, Tuple[str, ...]] = {
        "idle": ("neutral stance", "breathing animation", "ready position"),
        "walk": ("step forward", "mid stride", "step back", "weight shift"),
        "attack": ("wind up", "strike", "follow through", "recovery"),
        "hit": ("impact reaction", "stagger back", "recovery stance"),
        "jump": ("crouch", "leap", "peak", "landing"),
        "block": ("guard up", "blocking stance", "deflection"),
        "victory": ("arms raised", "celebration pose", "triumphant stance"),
    }

    def __init__(
        self,
    *,
    settings_manager: Optional[SettingsManager] = None,
    client: Optional[Any] = None,
    ) -> None:
        self.settings_manager = settings_manager or SettingsManager()
        self.assets_dir = Path(__file__).resolve().parent / "assets"
        self.output_dir = self.assets_dir / "images" / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sprite_root = self.assets_dir / "sprites"
        self.sprite_root.mkdir(parents=True, exist_ok=True)

        # AI / 图像配置
        ai_config = self.settings_manager.get("ai", {}) or {}
        self.image_model = str(ai_config.get("image_model", "gpt-image-1"))
        self.image_size = str(ai_config.get("image_size", "1024x1024"))
        self.sprite_size = str(ai_config.get("sprite_size", "256x256"))
        self.image_quality = str(ai_config.get("image_quality", "high"))
        self.rate_limit_delay = float(ai_config.get("rate_limit_delay", 1.0))
        self.generate_sprite_frames = bool(ai_config.get("generate_sprite_frames", False))
        self.sprite_rate_limit_delay = float(ai_config.get("sprite_rate_limit_delay", 0.8))
        self.user_tag = str(ai_config.get("user_tag", "streetbattle-image-generator"))

        self.client = client or self._create_openai_client(ai_config)
        self.characters: Dict[str, CharacterSpec] = self._load_character_specs()

    # ------------------------------------------------------------------
    # OpenAI client utilities
    # ------------------------------------------------------------------
    def _create_openai_client(self, ai_config: Dict[str, object]) -> Optional[Any]:
        if OpenAI is None:
            print("[CharacterImageGenerator] ⚠️ 未安装 openai 包，请执行 `pip install openai` 后重试。")
            return None

        api_key = os.getenv("OPENAI_API_KEY") or ai_config.get("api_key")
        if not api_key:
            print("[CharacterImageGenerator] ⚠️ 未检测到 OPENAI_API_KEY，生成将退化为只写入提示词。")
            return None

        try:
            return OpenAI(api_key=str(api_key))
        except Exception as exc:  # pragma: no cover - network/auth errors handled gracefully
            print(f"[CharacterImageGenerator] ⚠️ OpenAI 客户端初始化失败: {exc}")
            return None

    # ------------------------------------------------------------------
    # Character data loading
    # ------------------------------------------------------------------
    def _load_character_specs(self) -> Dict[str, CharacterSpec]:
        """从本地角色清单中加载描述信息, 并提供默认回退."""

        manifest_candidates: Iterable[Path] = (
            self.assets_dir / "characters_manifest_complete.json",
            self.assets_dir / "characters_manifest.json",
            Path(__file__).resolve().parent / "characters_manifest_complete.json",
        )

        specs: Dict[str, CharacterSpec] = {}
        moves_index = self._load_move_index()
        move_lookup = self._build_move_lookup(moves_index)

        for manifest_path in manifest_candidates:
            if not manifest_path.exists():
                continue
            try:
                with manifest_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                characters = []
                if isinstance(payload, dict) and "characters" in payload:
                    characters = payload["characters"]
                elif isinstance(payload, list):
                    characters = payload
                elif isinstance(payload, dict):
                    characters = list(payload.values())

                for entry in characters:
                    if not isinstance(entry, dict):
                        continue
                    identifier = str(entry.get("id") or entry.get("identifier") or "").strip()
                    if not identifier:
                        continue
                    description = str(entry.get("description") or entry.get("bio") or "" )
                    appearance = str(entry.get("appearance") or entry.get("look") or "")
                    fighting_style = str(entry.get("fighting_style") or entry.get("style") or "mixed martial arts")
                    colors = str(entry.get("palette") or entry.get("colors") or entry.get("primary_color") or "vibrant accent colors")
                    signature_moves_raw = entry.get("signature_moves") or entry.get("moves") or []
                    if isinstance(signature_moves_raw, dict):
                        signature_moves_list = list(signature_moves_raw.keys())
                    elif isinstance(signature_moves_raw, (list, tuple, set)):
                        signature_moves_list = [str(move) for move in signature_moves_raw if move]
                    elif signature_moves_raw:
                        signature_moves_list = [str(signature_moves_raw)]
                    else:
                        signature_moves_list = []

                    move_entry = self._resolve_moves_for_character(identifier, entry, move_lookup)
                    if move_entry:
                        derived_moves: List[str] = []
                        derived_moves.extend(move_entry.get("special_moves", {}).keys())
                        derived_moves.extend(move_entry.get("super_moves", {}).keys())
                        if signature_moves_list:
                            signature_moves_list = list(dict.fromkeys(signature_moves_list + derived_moves))
                        else:
                            signature_moves_list = list(dict.fromkeys(derived_moves))
                    specs[identifier] = CharacterSpec(
                        identifier=identifier,
                        display_name=str(entry.get("name") or identifier.replace("_", " ").title()),
                        description=description or "Elite tournament fighter",
                        appearance=appearance or "athletic fighter in tournament attire",
                        fighting_style=fighting_style,
                        colors=colors,
                        signature_moves=tuple(signature_moves_list),
                    )
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[CharacterImageGenerator] ⚠️ 无法解析 {manifest_path.name}: {exc}")

        if specs:
            return specs

        # Fallback defaults to guarantee generator usability
        print("[CharacterImageGenerator] ⚠️ 未找到角色清单, 使用默认角色集。")
        default_pool = {
            "mr_big": CharacterSpec(
                identifier="mr_big",
                display_name="Mr. Big",
                description="Elegant crime boss from Fatal Fury",
                appearance="tall gentleman in expensive business suit, slicked back dark hair, confident stance with arms crossed",
                fighting_style="street fighting with cane techniques",
                colors="dark navy suit, white shirt, red tie",
                signature_moves=("Ground Blaster", "Tornado Upper", "California Romance"),
            ),
            "ramon": CharacterSpec(
                identifier="ramon",
                display_name="Ramon",
                description="Lucha libre wrestler from King of Fighters",
                appearance="muscular luchador with colourful mask and dynamic wrestling attire",
                fighting_style="lucha libre wrestling and aerial techniques",
                colors="bright blue and yellow mask, green wrestling outfit",
                signature_moves=("Tiger Road", "Feint Step", "Rolling Sobat"),
            ),
            "wolfgang": CharacterSpec(
                identifier="wolfgang",
                display_name="Wolfgang Krauser",
                description="German nobleman wielding overwhelming power",
                appearance="imposing tall nobleman with long blonde hair, aristocratic armour and cape",
                fighting_style="brutal power attacks and royal combat techniques",
                colors="deep navy armour, gold trim, white cape",
                signature_moves=("Kaiser Wave", "Leg Tomahawk", "Phoenix Throw"),
            ),
        }
        return default_pool

    def _load_move_index(self) -> Dict[str, Dict[str, Any]]:
        """Load curated move definitions so prompts can reference signature skills."""
        moves_path = self.assets_dir / "character_moves.json"
        if not moves_path.exists():
            return {}

        try:
            with moves_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception as exc:
            print(f"[CharacterImageGenerator] ⚠️ 无法读取 character_moves.json: {exc}")
            return {}

        characters = payload.get("characters")
        if isinstance(characters, dict):
            return characters
        return {}

    def _build_move_lookup(self, moves_index: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        lookup: Dict[str, Dict[str, Any]] = {}
        for char_id, payload in moves_index.items():
            if not isinstance(payload, dict):
                continue

            candidate_keys = {char_id}
            name = payload.get("name")
            if name:
                candidate_keys.add(name)

            for alias in payload.get("aliases", []) or []:
                if alias:
                    candidate_keys.add(alias)

            for candidate in candidate_keys:
                key = self._normalise_key(candidate)
                if key:
                    lookup[key] = payload

        return lookup

    def _resolve_moves_for_character(
        self,
        identifier: str,
        entry: Dict[str, Any],
        move_lookup: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        candidates = [identifier, entry.get("name")]

        for field in ("aliases", "alt_names", "nicknames"):
            values = entry.get(field)
            if isinstance(values, str):
                candidates.append(values)
            elif isinstance(values, (list, tuple, set)):
                candidates.extend([v for v in values if v])

        for candidate in candidates:
            key = self._normalise_key(candidate)
            if key and key in move_lookup:
                return move_lookup[key]

        return None

    @staticmethod
    def _normalise_key(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return str(value).strip().lower().replace(" ", "_")

    # ------------------------------------------------------------------
    # Prompt builders & persistence helpers
    # ------------------------------------------------------------------
    def _build_portrait_prompt(self, spec: CharacterSpec, pose: str) -> str:
        signature = ", ".join(spec.signature_moves) if spec.signature_moves else "signature techniques"
        template = f"""Professional full-body portrait of {spec.display_name}, {spec.description},
{spec.appearance}, performing {pose}, {spec.fighting_style} style,
highly detailed fighting game concept art, {spec.colors},
clean studio lighting, {self.image_size} resolution,
full body centred composition, no other characters, premium character sheet quality,
references: {signature}."""
        return " ".join(template.split())

    def _build_sprite_prompt(self, spec: CharacterSpec, state: str, frame_desc: str) -> str:
        template = f"""Pixel art sprite of {spec.display_name}, {spec.appearance}, {frame_desc},
side-on camera, crisp silhouette, arcade fighting game animation for state '{state}',
{self.sprite_size} resolution, vibrant {spec.colors}, clean alpha background."""
        return " ".join(template.split())

    def _write_metadata(
        self,
        output_path: Path,
        prompt: str,
        *,
        status: str,
        metadata: Optional[Dict[str, object]] = None,
        error: Optional[str] = None,
    ) -> None:
        payload = {
            "prompt": prompt,
            "status": status,
            "model": self.image_model,
            "size": self.image_size,
            "quality": self.image_quality,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
        if metadata:
            payload.update(metadata)
        if error:
            payload["error"] = error
        output_path.with_suffix(output_path.suffix + ".json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _save_image_bytes(self, output_path: Path, base64_payload: str) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image_bytes = base64.b64decode(base64_payload)
        output_path.write_bytes(image_bytes)

    def call_openai_image_api(
        self,
        prompt: str,
        output_path: Path,
        *,
        size: Optional[str] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> bool:
        """调用 OpenAI 接口生成图像; 若缺少凭据则仅输出提示词。"""

        if self.client is None:
            self._write_metadata(output_path, prompt, status="skipped_no_client", metadata=metadata)
            return False

        try:
            response = self.client.images.generate(
                model=self.image_model,
                prompt=prompt,
                size=size or self.image_size,
                quality=self.image_quality,
                user=self.user_tag,
                n=1,
            )
            data = response.data[0]
            self._save_image_bytes(output_path, data.b64_json)
            details = metadata or {}
            if getattr(data, "revised_prompt", None):
                details["revised_prompt"] = data.revised_prompt
            self._write_metadata(output_path, prompt, status="success", metadata=details)
            return True
        except OpenAIError as exc:  # pragma: no cover - external API failure
            self._write_metadata(output_path, prompt, status="error", metadata=metadata, error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Image generation flows
    # ------------------------------------------------------------------
    def generate_character_images(self, char_id: str) -> None:
        spec = self.characters.get(char_id)
        if not spec:
            print(f"❌ 未知角色: {char_id}")
            return

        print(f"\n🥷 正在生成 {spec.display_name} 的立绘与姿势图像")
        char_dir = self.output_dir / spec.identifier
        char_dir.mkdir(parents=True, exist_ok=True)

        main_prompt = self._build_portrait_prompt(spec, "signature combat stance")
        portrait_path = char_dir / f"{spec.identifier}_portrait.png"
        self.call_openai_image_api(
            main_prompt,
            portrait_path,
            metadata={"character": spec.display_name, "pose": "signature combat stance"},
        )

        for index, pose in enumerate(self.DEFAULT_POSES, start=1):
            prompt = self._build_portrait_prompt(spec, pose)
            pose_path = char_dir / f"{spec.identifier}_pose_{index:02d}_{pose.replace(' ', '_')}.png"
            self.call_openai_image_api(
                prompt,
                pose_path,
                metadata={"character": spec.display_name, "pose": pose, "index": index},
            )
            time.sleep(self.rate_limit_delay)

    def generate_sprite_animation_frames(self, char_id: str) -> None:
        spec = self.characters.get(char_id)
        if not spec:
            return

        print(f"🎬 生成 {spec.display_name} 的 2.5D 精灵帧资产")
        sprite_dir = self.sprite_root / spec.identifier
        sprite_dir.mkdir(parents=True, exist_ok=True)

        manifest: Dict[str, Dict[str, object]] = {
            "character_id": spec.identifier,
            "display_name": spec.display_name,
            "description": spec.description,
            "states": {},
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "image_model": self.image_model,
            "sprite_size": self.sprite_size,
        }

        for state, frames in self.SPRITE_STATES.items():
            state_dir = sprite_dir / state
            state_dir.mkdir(parents=True, exist_ok=True)
            durations = []

            for idx, frame_desc in enumerate(frames):
                prompt = self._build_sprite_prompt(spec, state, frame_desc)
                frame_path = state_dir / f"frame_{idx:02d}.png"
                metadata = {
                    "character": spec.display_name,
                    "state": state,
                    "frame_index": idx,
                    "description": frame_desc,
                    "size": self.sprite_size,
                }

                if self.generate_sprite_frames:
                    self.call_openai_image_api(
                        prompt,
                        frame_path,
                        size=self.sprite_size,
                        metadata=metadata,
                    )
                    time.sleep(self.sprite_rate_limit_delay)
                else:
                    self._write_metadata(
                        frame_path,
                        prompt,
                        status="skipped_config_only",
                        metadata=metadata,
                    )
                durations.append(0.1)

            manifest["states"][state] = {
                "sequence": list(range(len(frames))),
                "fps": 12 if state in {"walk", "attack"} else 8,
                "loop": state in {"idle", "walk", "block"},
                "frames": len(frames),
                "durations": durations,
            }

        manifest_path = sprite_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    def generate_all_missing_characters(self) -> None:
        print("🚀 开始批量生成 StreetBattle 角色图像资源")
        print("=" * 72)
        for spec in self.characters.values():
            print(f"\n⭐ 处理角色: {spec.display_name}")
            self.generate_character_images(spec.identifier)
            self.generate_sprite_animation_frames(spec.identifier)
        print("\n✨ 所有角色图像生成任务完成!")
        print("请在 assets/images/generated/ 下查阅生成结果。")


def main() -> None:
    generator = CharacterImageGenerator()
    generator.generate_all_missing_characters()

    metadata_files = list(generator.output_dir.rglob("*.json"))
    print(f"\n📁 已生成 {len(metadata_files)} 份提示词/元数据文件。")
    for path in metadata_files[:10]:
        print(f"  - {path.relative_to(Path.cwd())}")
    if len(metadata_files) > 10:
        print(f"  ... 以及其他 {len(metadata_files) - 10} 个文件")


if __name__ == "__main__":
    main()