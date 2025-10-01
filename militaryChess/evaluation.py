"""Game evaluation functions for Chinese Military Chess AI.

This module contains position evaluation, heuristics, and analysis
functions used by the AI engine to make strategic decisions.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Setup path for absolute imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if TYPE_CHECKING:
    from gamecenter.militaryChess.game_logic import GameState, Player, JunqiBoard


def _material_value(board: "JunqiBoard", player: "Player") -> int:
	return sum(piece.spec.value for piece in board.pieces(player))


def _shortest_flag_distance(board: "JunqiBoard", player: "Player") -> float:
    from gamecenter.militaryChess.game_logic import estimate_shortest_path_to_target

    target_player = player.opponent
    target_coord = board.flag_position(target_player)
    if target_coord is None:
        return math.inf

    best = math.inf
    for piece in board.pieces(player):
        if not piece.movable or piece.position is None:
            continue
        dist = estimate_shortest_path_to_target(piece.code, piece.position, target_coord)
        if dist < best:
            best = dist
    return best


def evaluate_state(state: "GameState", perspective: "Player") -> float:
	board = state.board
	opponent = perspective.opponent

	material = _material_value(board, perspective) - _material_value(board, opponent)
	mobility = board.mobility(perspective) - board.mobility(opponent)

	dist_self = _shortest_flag_distance(board, perspective)
	dist_opponent = _shortest_flag_distance(board, opponent)

	score = material
	score += 20.0 * mobility
	if dist_self != math.inf:
		score += 150.0 / (1.0 + dist_self)
	if dist_opponent != math.inf:
		score -= 150.0 / (1.0 + dist_opponent)

	# Encourage revealed high-rank pieces controlling camps/railroads
	central_bonus = 0.0
	for coord, tile in board.tiles.items():
		piece = tile.occupant
		if not piece or not piece.face_up:
			continue
		weight = 25 if tile.on_rail else 10
		if piece.owner is perspective:
			central_bonus += weight * (1 if piece.spec.rank >= 5 else 0.5)
		else:
			central_bonus -= weight * (1 if piece.spec.rank >= 5 else 0.5)
	score += 0.1 * central_bonus

	return score
