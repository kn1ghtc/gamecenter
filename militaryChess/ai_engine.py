"""AI Engine for Chinese Military Chess.

This module contains AI controllers, search algorithms, and configuration
management for the military chess game.
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Dict, List, Optional, Tuple

# Setup path for absolute imports
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Use absolute imports
from gamecenter.militaryChess.game_logic import GameState, GameTermination, Move, Player


@dataclass
class AIConfig:
	difficulty: str = "standard"
	base_depth: int = 2
	max_depth: int = 4
	time_limit: float = 2.0
	random_factor: float = 0.05
	rollout_depth: int = 4
	rollout_count: int = 8


class SearchTimeout(Exception):
	"""Raised when the AI search exceeds the allocated time budget."""


class AIController:
	def __init__(self, config: Optional[AIConfig] = None) -> None:
		self.config = config or AIConfig()
		self.nodes: int = 0

		if self.config.difficulty == "easy":
			self.config.base_depth = 1
			self.config.max_depth = 2
			self.config.time_limit = min(self.config.time_limit, 1.0)
		elif self.config.difficulty == "hard":
			self.config.base_depth = max(self.config.base_depth, 3)
			self.config.max_depth = max(self.config.max_depth, 5)
			self.config.time_limit = max(self.config.time_limit, 2.5)

	def decide_move(self, state: GameState) -> Move:
		start_time = time.perf_counter()
		best_move: Optional[Move] = None
		best_score = -math.inf
		depth = self.config.base_depth
		perspective = state.current_player
		principal_variation: Optional[Move] = None

		while depth <= self.config.max_depth:
			try:
				score, move = self._negamax(
					state.clone(), depth, -math.inf, math.inf, start_time, perspective
				)
			except SearchTimeout:
				break

			if move is not None:
				best_move = move
				best_score = score
				principal_variation = move

			elapsed = time.perf_counter() - start_time
			if elapsed >= self.config.time_limit:
				break
			depth += 1

		if best_move is None:
			# Fallback: choose a move biased by heuristic ordering.
			candidates = self._ordered_moves(state)
			if not candidates:
				raise Exception("AI 无可行走步")
			# Inject slight randomness to avoid repetitive play.
			top_k = min(3, len(candidates))
			best_move = random.choice(candidates[:top_k])
			principal_variation = best_move

		if principal_variation and random.random() < self.config.random_factor:
			ordered = self._ordered_moves(state)
			if ordered:
				best_move = random.choice(ordered[: max(1, len(ordered) // 3)])

		return best_move

	def _negamax(
		self,
		state: GameState,
		depth: int,
		alpha: float,
		beta: float,
		start_time: float,
		perspective: Player,
	) -> Tuple[float, Optional[Move]]:
		if time.perf_counter() - start_time >= self.config.time_limit:
			raise SearchTimeout()

		from .evaluation import evaluate_state
		status = state.status
		current = state.current_player

		if status.outcome is GameTermination.VICTORY:
			if status.winner is perspective:
				return math.inf, None
			if status.winner is perspective.opponent:
				return -math.inf, None
		if status.outcome is GameTermination.DRAW or status.outcome is GameTermination.STALEMATE:
			return 0.0, None

		if depth == 0:
			return evaluate_state(state, perspective), None

		best_move: Optional[Move] = None
		best_score = -math.inf

		moves = self._ordered_moves(state)
		if not moves:
			# No legal moves -> opponent wins
			if current is perspective:
				return -math.inf, None
			return math.inf, None

		for move in moves:
			next_state = state.clone()
			result = next_state.play_move(move)
			self.nodes += 1

			if result.outcome is GameTermination.VICTORY:
				if result.winner is perspective:
					return math.inf, move
				if result.winner is perspective.opponent:
					score = -math.inf
				else:
					score = 0.0
			elif result.outcome is GameTermination.DRAW:
				score = 0.0
			else:
				score, _ = self._negamax(
					next_state,
					depth - 1,
					-beta,
					-alpha,
					start_time,
					perspective,
				)
				score = -score

			if score > best_score:
				best_score = score
				best_move = move

			alpha = max(alpha, score)
			if alpha >= beta:
				break

			if time.perf_counter() - start_time >= self.config.time_limit:
				raise SearchTimeout()

		return best_score, best_move

	def _ordered_moves(self, state: GameState) -> List[Move]:
		moves = state.all_legal_moves()

		def move_score(move: Move) -> float:
			score = 0.0
			piece = state.board.piece_at(move.src) if move.src else None
			if move.kind.name == "ATTACK" and move.dst:
				defender = state.board.piece_at(move.dst)
				if defender:
					score += defender.spec.value
				if piece:
					score -= piece.spec.value * 0.2
			if move.dst:
				tile = state.board.tiles[move.dst]
				if tile.on_rail:
					score += 30.0
				if tile.is_camp:
					score += 15.0
			if piece and piece.code == "ENGINEER":
				score += 5.0
			return -score

		moves.sort(key=move_score)
		return moves


class AIMovePlanner:
	def __init__(self, controller: AIController) -> None:
		self.controller = controller
		self.thread: Optional[Thread] = None
		self._pending: Optional[Move] = None
		self._error: Optional[Exception] = None
		self.running: bool = False

	def start(self, state: GameState) -> None:
		if self.running:
			return
		clone = state.clone()

		def worker() -> None:
			try:
				move = self.controller.decide_move(clone)
				self._pending = move
			except Exception as exc:  # noqa: BLE001
				self._error = exc
			finally:
				self.running = False

		self.running = True
		self._pending = None
		self._error = None
		self.thread = Thread(target=worker, daemon=True)
		self.thread.start()

	def poll(self) -> Tuple[Optional[Move], Optional[Exception]]:
		if self.running:
			return None, None
		move, error = self._pending, self._error
		self._pending = None
		self._error = None
		return move, error


DEFAULT_SETTINGS = {
	"game_mode": "dark",  # "dark" or "light"
	"board_style": "classic",
	"allow_undo": True,
	"max_undo_steps": 3,
	"volume": 0.6,
	"difficulty": "standard",
	"show_fps": False,
	"fullscreen": False,
	"ai_time_limit": 2.0,
	"ai_random_factor": 0.05,
	"random_layout": True,
	"show_legal_moves": True,
	"animation_speed": 1.0,
	"board_theme": "wooden",
}


class SettingsManager:
	def __init__(self, path: Optional[Path] = None) -> None:
		if path is None:
			path = Path(__file__).resolve().with_name("config.json")
		self.path = path
		self.data = DEFAULT_SETTINGS.copy()
		self.load()

	def load(self) -> None:
		if not self.path.exists():
			self.save()  # Create default config
			return
		try:
			with self.path.open("r", encoding="utf-8") as fh:
				payload = json.load(fh)
			if isinstance(payload, dict):
				# Update with loaded values, keep defaults for missing keys
				for key in DEFAULT_SETTINGS:
					if key in payload:
						self.data[key] = payload[key]
				# Save to ensure all new keys are added
				self.save()
		except Exception:
			self.data = DEFAULT_SETTINGS.copy()
			self.save()

	def save(self) -> None:
		try:
			with self.path.open("w", encoding="utf-8") as fh:
				json.dump(self.data, fh, indent=2, ensure_ascii=False)
		except Exception:
			pass

	def get(self, key: str, default=None):
		return self.data.get(key, default)

	def set(self, key: str, value) -> None:
		self.data[key] = value
		self.save()

	def as_config(self) -> AIConfig:
		return AIConfig(
			difficulty=self.data.get("difficulty", "standard"),
			time_limit=float(self.data.get("ai_time_limit", 2.0)),
			random_factor=float(self.data.get("ai_random_factor", 0.05)),
		)
