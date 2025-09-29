#!/usr/bin/env python3
"""Lightweight animation bridge for gameplay state machines.

This module reinstates the legacy ``CharacterAnimator`` interface that
``main.py`` expects while seamlessly delegating animation updates to the
modern 2.5D sprite pipeline.  The original implementation targeted a fully
rigged 3D Actor stack that is no longer part of the current content bundle.
To keep the event flow intact we provide a compatibility layer that
translates high-level combat states into sprite animations when available
and quietly degrades to no-ops when assets are missing.

Key responsibilities
--------------------
* Preserve the public API used throughout ``main.py``: ``register_character``,
  ``start_hit_reaction``, ``update_animation_state``, ``start_victory_animation``
  and ``start_defeat_animation``.
* Resolve a ``SpriteCharacter`` instance for each registered player so that we
  can trigger the correct animation without duplicating state machines.
* Handle absent sprites gracefully (for example when a configuration entry
  lacks sprite art) by simply recording state changes instead of raising
  errors.
* Provide minimal logging to help future debugging without spamming the
  console during normal gameplay.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CharacterEntry:
    """Runtime metadata tracked for each registered character."""

    node: object
    parts: dict
    sprite: Optional[object]
    last_state: str = "idle"


class CharacterAnimator:
    """Compatibility animator that drives sprite characters when possible."""

    def __init__(self, game_app):
        self.game = game_app
        self.characters: Dict[str, CharacterEntry] = {}

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    def register_character(self, char_key: str, model_node, body_parts: Optional[dict] = None) -> None:
        """Register a gameplay character with optional sprite integration."""
        sprite = self._resolve_sprite_for(char_key)
        self.characters[char_key] = CharacterEntry(
            node=model_node,
            parts=body_parts or {},
            sprite=sprite,
        )

        if sprite:
            try:
                sprite.play_animation("idle", force_restart=True)
            except Exception:
                pass

    def _resolve_sprite_for(self, char_key: str):
        """Best-effort mapping of ``player_X`` identifiers to sprite objects."""
        players = getattr(self.game, "players", [])
        if not players:
            return None

        idx = None
        if char_key.startswith("player_"):
            try:
                idx = int(char_key.split("_", 1)[1])
            except (IndexError, ValueError):
                idx = None

        if idx is None or not (0 <= idx < len(players)):
            return None

        player = players[idx]
        return getattr(player, "sprite_character", None)

    # ------------------------------------------------------------------
    # Animation triggers
    # ------------------------------------------------------------------
    def start_hit_reaction(self, char_key: str, direction: str | None = None) -> None:
        self._play(char_key, "hit", priority_override=True)

    def start_victory_animation(self, char_key: str) -> None:
        self._play(char_key, "victory", priority_override=True)

    def start_defeat_animation(self, char_key: str) -> None:
        self._play(char_key, "defeat", priority_override=True)

    def update_animation_state(self, char_key: str, logic_state: str, inputs: Optional[dict] = None) -> None:
        entry = self.characters.get(char_key)
        if not entry:
            return

        mapped = self._map_state_to_animation(logic_state, inputs)
        entry.last_state = logic_state

        if mapped:
            priority = mapped in {"attack", "hit", "victory", "defeat", "special"}
            self._play(char_key, mapped, force_restart=priority, priority_override=priority)

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _play(self, char_key: str, animation: str, *, force_restart: bool = False, priority_override: bool = False) -> None:
        entry = self.characters.get(char_key)
        if not entry or not entry.sprite:
            return

        try:
            entry.sprite.play_animation(animation, force_restart=force_restart, priority_override=priority_override)
        except Exception:
            # Silently ignore animation errors so combat flow continues
            pass

    def _map_state_to_animation(self, logic_state: str, inputs: Optional[dict]) -> str | None:
        """Translate player logic state into sprite animation names."""
        if not logic_state:
            return None

        state = logic_state.lower()

        if state in {"idle", "neutral"}:
            return "idle"
        if state in {"walk", "run", "dash"}:
            return "walk"
        if state in {"jump", "jump_atk", "jump_heavy_atk"}:
            return "jump"
        if state in {"light_atk", "heavy_atk", "combo", "special"}:
            return "attack"
        if state in {"block", "block_stand", "block_crouch", "guard"}:
            return "block"
        if state in {"hurt", "hit", "hitstun", "knockdown"}:
            return "hit"
        if state in {"victory", "win"}:
            return "victory"
        if state in {"defeat", "lose", "ko"}:
            return "defeat"

        # Default fallback: keep previous animation to avoid jitter
        return None


__all__ = ["CharacterAnimator"]
