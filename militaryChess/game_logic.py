"""Game Logic for Chinese Military Chess.

This module contains the core game mechanics, board representation,
piece definitions, and game state management.
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

Coord = Tuple[int, int]


class Player(Enum):
	"""Two players: RED (human, bottom) and BLUE (AI, top)."""

	RED = auto()
	BLUE = auto()

	@property
	def opponent(self) -> "Player":
		return Player.BLUE if self is Player.RED else Player.RED

	@property
	def direction(self) -> int:
		"""Return +1 for RED (upwards in array index), -1 for BLUE."""
		return -1 if self is Player.BLUE else 1

	@property
	def name_cn(self) -> str:
		return "红方" if self is Player.RED else "蓝方"


class MoveKind(Enum):
	"""Kinds of moves supported by the engine."""
	MOVE = auto()
	ATTACK = auto()
	FLIP = auto()


@dataclass(frozen=True)
class PieceSpec:
	code: str
	label: str
	rank: int
	count: int
	movable: bool
	value: int


PIECE_SPECS: Dict[str, PieceSpec] = {
	"FLAG": PieceSpec("FLAG", "军旗", rank=0, count=1, movable=False, value=2000),
	"LANDMINE": PieceSpec("LANDMINE", "地雷", rank=11, count=3, movable=False, value=350),
	"BOMB": PieceSpec("BOMB", "炸弹", rank=0, count=2, movable=True, value=400),
	"ENGINEER": PieceSpec("ENGINEER", "工兵", rank=1, count=3, movable=True, value=220),
	"LIEUTENANT": PieceSpec("LIEUTENANT", "排长", rank=3, count=3, movable=True, value=260),
	"CAPTAIN": PieceSpec("CAPTAIN", "连长", rank=4, count=3, movable=True, value=300),
	"MAJOR": PieceSpec("MAJOR", "营长", rank=5, count=2, movable=True, value=360),
	"COLONEL": PieceSpec("COLONEL", "团长", rank=6, count=2, movable=True, value=420),
	"BRIGADIER": PieceSpec("BRIGADIER", "旅长", rank=7, count=2, movable=True, value=470),
	"MAJOR_GENERAL": PieceSpec("MAJOR_GENERAL", "师长", rank=8, count=2, movable=True, value=520),
	"GENERAL": PieceSpec("GENERAL", "军长", rank=9, count=1, movable=True, value=650),
	"MARSHAL": PieceSpec("MARSHAL", "司令", rank=10, count=1, movable=True, value=900),
}

# Board geometry
BOARD_ROWS = 12
BOARD_COLS = 5

# Preset layouts
PRESET_LAYOUT_BLUE: Dict[Coord, str] = {
	(0, 0): "LANDMINE", (0, 1): "FLAG", (0, 2): "CAPTAIN", (0, 3): "LANDMINE", (0, 4): "LANDMINE",
	(1, 0): "CAPTAIN", (1, 1): "LIEUTENANT", (1, 2): "BRIGADIER", (1, 3): "ENGINEER", (1, 4): "ENGINEER",
	(2, 0): "MAJOR_GENERAL", (2, 2): "LIEUTENANT", (2, 4): "MAJOR",
	(3, 0): "GENERAL", (3, 1): "BOMB", (3, 3): "LIEUTENANT", (3, 4): "MARSHAL",
	(4, 0): "MAJOR", (4, 2): "ENGINEER", (4, 4): "BOMB",
	(5, 0): "MAJOR_GENERAL", (5, 1): "COLONEL", (5, 2): "BRIGADIER", (5, 3): "CAPTAIN", (5, 4): "COLONEL",
}

PRESET_LAYOUT_RED: Dict[Coord, str] = {
	(6, 0): "MAJOR_GENERAL", (6, 1): "ENGINEER", (6, 2): "CAPTAIN", (6, 3): "MARSHAL", (6, 4): "COLONEL",
	(7, 0): "BOMB", (7, 2): "ENGINEER", (7, 4): "BOMB",
	(8, 0): "CAPTAIN", (8, 1): "MAJOR", (8, 3): "BRIGADIER", (8, 4): "LIEUTENANT",
	(9, 0): "MAJOR", (9, 2): "BRIGADIER", (9, 4): "GENERAL",
	(10, 0): "LANDMINE", (10, 1): "LIEUTENANT", (10, 2): "ENGINEER", (10, 3): "MAJOR_GENERAL", (10, 4): "LANDMINE",
	(11, 0): "CAPTAIN", (11, 1): "LIEUTENANT", (11, 2): "COLONEL", (11, 3): "FLAG", (11, 4): "LANDMINE",
}

# Special positions
HEADQUARTERS: Set[Coord] = {(0, 1), (0, 3), (11, 1), (11, 3)}
CAMPS: Set[Coord] = {(2, 1), (2, 3), (3, 2), (4, 1), (4, 3), (7, 1), (7, 3), (8, 2), (9, 1), (9, 3)}

# Railroad posts
RAILROAD_POSTS: Set[Coord] = set()
for r in range(1, 11):
	RAILROAD_POSTS.add((r, 0))
	RAILROAD_POSTS.add((r, 4))
for c in range(BOARD_COLS):
	RAILROAD_POSTS.add((1, c))
	RAILROAD_POSTS.add((5, c))
	RAILROAD_POSTS.add((6, c))
	RAILROAD_POSTS.add((10, c))

RAIL_INTERSECTIONS: Set[Coord] = {(5, 1), (5, 3), (6, 1), (6, 3)}
ALL_COORDS: Tuple[Coord, ...] = tuple((r, c) for r in range(BOARD_ROWS) for c in range(BOARD_COLS))


def is_inside(coord: Coord) -> bool:
	r, c = coord
	return 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS


def tile_is_camp(coord: Coord) -> bool:
	return coord in CAMPS


def tile_is_headquarter(coord: Coord) -> bool:
	return coord in HEADQUARTERS


def tile_on_rail(coord: Coord) -> bool:
	return coord in RAILROAD_POSTS


def player_side_rows(player: Player) -> Sequence[int]:
	"""Return rows belonging to the player's territory (inclusive)."""
	return range(0, 6) if player is Player.BLUE else range(6, 12)


def base_rows_from_home(player: Player) -> List[int]:
	"""Return rows ordered from home base outward."""
	if player is Player.BLUE:
		return [0, 1, 2, 3, 4, 5]
	return [11, 10, 9, 8, 7, 6]


# Build connection maps
def _build_road_connections() -> Dict[Coord, Set[Coord]]:
	connections: Dict[Coord, Set[Coord]] = {}
	for coord in ALL_COORDS:
		neighbors: Set[Coord] = set()
		r, c = coord
		for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			nr, nc = r + dr, c + dc
			if is_inside((nr, nc)):
				neighbors.add((nr, nc))
		if tile_is_camp(coord):
			for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
				nr, nc = r + dr, c + dc
				if is_inside((nr, nc)):
					neighbors.add((nr, nc))
		connections[coord] = neighbors
	return connections


def _build_rail_neighbors() -> Dict[Coord, Set[Coord]]:
	neighbors: Dict[Coord, Set[Coord]] = {coord: set() for coord in ALL_COORDS}
	for coord in RAILROAD_POSTS:
		r, c = coord
		for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			nr, nc = r + dr, c + dc
			nxt = (nr, nc)
			if nxt in RAILROAD_POSTS:
				neighbors[coord].add(nxt)
	return neighbors


def _build_rail_line_targets() -> Dict[Coord, Set[Coord]]:
	targets: Dict[Coord, Set[Coord]] = {coord: set() for coord in ALL_COORDS}
	for coord in RAILROAD_POSTS:
		r, c = coord
		# Horizontal scan
		for dc in (-1, 1):
			nr, nc = r, c
			while True:
				nc += dc
				nxt = (nr, nc)
				if nxt not in RAILROAD_POSTS:
					break
				targets[coord].add(nxt)
		# Vertical scan
		for dr in (-1, 1):
			nr, nc = r, c
			while True:
				nr += dr
				nxt = (nr, nc)
				if nxt not in RAILROAD_POSTS:
					break
				targets[coord].add(nxt)
	return targets


def _build_engineer_reach() -> Dict[Coord, Set[Coord]]:
	reach: Dict[Coord, Set[Coord]] = {coord: set() for coord in ALL_COORDS}
	rail_step_neighbors = _build_rail_neighbors()
	for coord in RAILROAD_POSTS:
		visited: Set[Coord] = set()
		queue: deque[Coord] = deque([coord])
		visited.add(coord)
		while queue:
			current = queue.popleft()
			for nxt in rail_step_neighbors[current]:
				if nxt not in visited:
					visited.add(nxt)
					queue.append(nxt)
		visited.remove(coord)
		reach[coord] = visited
	return reach


ROAD_CONNECTIONS: Dict[Coord, Set[Coord]] = _build_road_connections()
RAIL_STEP_NEIGHBORS: Dict[Coord, Set[Coord]] = _build_rail_neighbors()
RAIL_LINE_TARGETS: Dict[Coord, Set[Coord]] = _build_rail_line_targets()
ENGINEER_RAIL_REACH: Dict[Coord, Set[Coord]] = _build_engineer_reach()


def heuristic_neighbors_for_piece(code: str, coord: Coord) -> Set[Coord]:
	if tile_is_headquarter(coord):
		return set()

	neighbors = set(ROAD_CONNECTIONS.get(coord, ()))
	if coord in RAILROAD_POSTS:
		if code == "ENGINEER":
			neighbors.update(ENGINEER_RAIL_REACH.get(coord, ()))
		else:
			neighbors.update(RAIL_LINE_TARGETS.get(coord, ()))
	return neighbors


def estimate_shortest_path_to_target(code: str, start: Coord, target: Coord) -> float:
	if start == target:
		return 0.0
	visited: Set[Coord] = {start}
	queue: deque[Tuple[Coord, int]] = deque([(start, 0)])
	while queue:
		coord, dist = queue.popleft()
		for nxt in heuristic_neighbors_for_piece(code, coord):
			if nxt == target:
				return float(dist + 1)
			if nxt not in visited:
				visited.add(nxt)
				queue.append((nxt, dist + 1))
	return math.inf


@dataclass
class Piece:
	spec: PieceSpec
	owner: Player
	face_up: bool = False
	position: Optional[Coord] = None
	revealed_turn: Optional[int] = None

	@property
	def code(self) -> str:
		return self.spec.code

	@property
	def rank(self) -> int:
		return self.spec.rank

	@property
	def movable(self) -> bool:
		return self.spec.movable


@dataclass
class Tile:
	coord: Coord
	occupant: Optional[Piece] = None

	@property
	def is_camp(self) -> bool:
		return tile_is_camp(self.coord)

	@property
	def is_headquarter(self) -> bool:
		return tile_is_headquarter(self.coord)

	@property
	def on_rail(self) -> bool:
		return tile_on_rail(self.coord)


@dataclass
class Move:
	kind: MoveKind
	player: Player
	src: Optional[Coord]
	dst: Optional[Coord]
	note: str = ""
	score_hint: float = 0.0


@dataclass
class BattleResolution:
	attacker: Piece
	defender: Piece
	winner: Optional[Piece]
	both_destroyed: bool
	captured_flag: bool
	note: str


class IllegalMove(Exception):
	pass


class GameTermination(Enum):
	ONGOING = auto()
	VICTORY = auto()
	STALEMATE = auto()
	DRAW = auto()


@dataclass
class GameStatus:
	outcome: GameTermination
	winner: Optional[Player]
	reason: str = ""


class JunqiBoard:
	"""Pure game-logic board implementation."""

	def __init__(self) -> None:
		self.tiles: Dict[Coord, Tile] = {
			(r, c): Tile((r, c)) for r in range(BOARD_ROWS) for c in range(BOARD_COLS)
		}
		self.move_counter: int = 0
		self.turn_counter: int = 0
		self.last_capture_turn: int = 0

	def reset(self, rng: Optional[random.Random] = None, randomize: bool = True) -> None:
		"""Reset the board with heuristic or preset layouts for both sides."""
		rng = rng or random.Random()
		for tile in self.tiles.values():
			tile.occupant = None
		self.move_counter = 0
		self.turn_counter = 0
		self.last_capture_turn = 0
		for player in (Player.BLUE, Player.RED):
			if randomize:
				layout = self._generate_layout(player, rng)
			else:
				layout = self._preset_layout(player)
			for coord, code in layout.items():
				spec = PIECE_SPECS[code]
				piece = Piece(spec=spec, owner=player, face_up=False)
				piece.position = coord
				self.tiles[coord].occupant = piece

	def _generate_layout(self, player: Player, rng: random.Random) -> Dict[Coord, str]:
		"""Generate a heuristic-compliant initial layout for a player."""
		territory = [coord for coord in self._territory_squares(player)]
		available: Set[Coord] = set(territory)
		layout: Dict[Coord, str] = {}

		def choose_position(options: Iterable[Coord]) -> Coord:
			candidates = [coord for coord in options if coord in available]
			if not candidates:
				raise RuntimeError("No available positions satisfy layout constraints")
			choice = rng.choice(candidates)
			available.remove(choice)
			return choice

		# Flag placement (must be inside HQ on player's side)
		hq_options = [coord for coord in HEADQUARTERS if self._coord_belongs_to(coord, player)]
		layout[choose_position(hq_options)] = "FLAG"

		# Landmines: must start on the rear two ranks (closest to base)
		home_rows = base_rows_from_home(player)
		rear_rows = home_rows[:2]
		landmine_positions = [coord for coord in territory if coord[0] in rear_rows]
		for _ in range(PIECE_SPECS["LANDMINE"].count):
			coord = choose_position(landmine_positions)
			layout[coord] = "LANDMINE"

		# Bombs: any territory except the foremost rank (contact line)
		front_row = home_rows[-1]
		bomb_positions = [coord for coord in territory if coord[0] != front_row]
		for _ in range(PIECE_SPECS["BOMB"].count):
			coord = choose_position(bomb_positions)
			layout[coord] = "BOMB"

		# Remaining movable ranks distributed heuristically with slight shuffling
		remaining_specs = [
			"ENGINEER", "ENGINEER", "ENGINEER", "LIEUTENANT", "LIEUTENANT", "LIEUTENANT",
			"CAPTAIN", "CAPTAIN", "CAPTAIN", "MAJOR", "MAJOR", "COLONEL", "COLONEL",
			"BRIGADIER", "BRIGADIER", "MAJOR_GENERAL", "MAJOR_GENERAL", "GENERAL", "MARSHAL",
		]

		rng.shuffle(remaining_specs)
		remaining_positions = list(available)
		rng.shuffle(remaining_positions)
		for spec_code, coord in zip(remaining_specs, remaining_positions):
			layout[coord] = spec_code
			available.remove(coord)

		return layout

	def _preset_layout(self, player: Player) -> Dict[Coord, str]:
		if player is Player.BLUE:
			return PRESET_LAYOUT_BLUE.copy()
		return PRESET_LAYOUT_RED.copy()

	def _territory_squares(self, player: Player) -> Iterable[Coord]:
		rows = player_side_rows(player)
		for r in rows:
			for c in range(BOARD_COLS):
				yield (r, c)

	def _coord_belongs_to(self, coord: Coord, player: Player) -> bool:
		r, _ = coord
		if player is Player.BLUE:
			return 0 <= r <= 5
		return 6 <= r <= 11

	def piece_at(self, coord: Coord) -> Optional[Piece]:
		return self.tiles[coord].occupant if coord in self.tiles else None

	def legal_moves_for(self, player: Player, coord: Coord) -> List[Move]:
		piece = self.piece_at(coord)
		if piece is None or piece.owner is not player or not piece.movable:
			return []
		if not piece.face_up:
			return []

		tile = self.tiles[coord]
		moves: List[Move] = []

		# Headquarter restriction: pieces can move into HQ but cannot move out once inside.
		if tile.is_headquarter and piece.code != "FLAG":
			pass  # They are effectively trapped; no moves available.
		else:
			for neighbor in self._adjacent_roads(coord):
				if not is_inside(neighbor):
					continue
				dest_tile = self.tiles[neighbor]
				occ = dest_tile.occupant
				if occ is None:
					moves.append(Move(MoveKind.MOVE, player, coord, neighbor))
				elif occ.owner is not player:
					if dest_tile.is_camp:
						continue
					moves.append(Move(MoveKind.ATTACK, player, coord, neighbor))

			if tile.on_rail:
				moves.extend(self._railway_moves(coord))

		return moves

	def _adjacent_roads(self, coord: Coord) -> Iterable[Coord]:
		if tile_is_headquarter(coord):
			return ()
		return ROAD_CONNECTIONS.get(coord, ())

	def _rail_neighbors(self, coord: Coord) -> List[Coord]:
		r, c = coord
		neighbors: List[Coord] = []
		for dr, dc in ((1, 0), (-1, 0)):
			nr, nc = r + dr, c + dc
			if (nr, nc) in RAILROAD_POSTS:
				neighbors.append((nr, nc))
		for dr, dc in ((0, 1), (0, -1)):
			nr, nc = r + dr, c + dc
			if (nr, nc) in RAILROAD_POSTS:
				neighbors.append((nr, nc))
		return neighbors

	def _railway_moves(self, coord: Coord) -> List[Move]:
		piece = self.piece_at(coord)
		if piece is None or not self.tiles[coord].on_rail:
			return []

		moves: List[Move] = []
		player = piece.owner

		if piece.code == "ENGINEER":
			# Engineers can turn at intersections; breadth-first traversal.
			frontier = [coord]
			visited = {coord}
			while frontier:
				current = frontier.pop()
				for nxt in self._rail_neighbors(current):
					if nxt in visited:
						continue
					tile = self.tiles[nxt]
					occ = tile.occupant
					if occ is None:
						moves.append(Move(MoveKind.MOVE, player, coord, nxt))
						frontier.append(nxt)
						visited.add(nxt)
					elif occ.owner is not player:
						moves.append(Move(MoveKind.ATTACK, player, coord, nxt))
						visited.add(nxt)
		else:
			# Non-engineers can move in straight lines along rails.
			for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
				path_coord = coord
				while True:
					nr, nc = path_coord[0] + dr, path_coord[1] + dc
					next_coord = (nr, nc)
					if next_coord not in RAILROAD_POSTS:
						break
					tile = self.tiles[next_coord]
					occ = tile.occupant
					if occ is None:
						moves.append(Move(MoveKind.MOVE, player, coord, next_coord))
						path_coord = next_coord
						continue
					if occ.owner is player:
						break
					moves.append(Move(MoveKind.ATTACK, player, coord, next_coord))
					break
		return moves

	def resolve_attack(self, src: Coord, dst: Coord) -> BattleResolution:
		attacker = self.piece_at(src)
		defender = self.piece_at(dst)
		if attacker is None or defender is None:
			raise IllegalMove("Attack requires both attacker and defender")

		defender.face_up = True
		attacker.face_up = True

		if defender.code == "FLAG":
			note = f"{attacker.owner.name_cn}夺取军旗"
			return BattleResolution(attacker, defender, attacker, False, True, note)

		if defender.code == "LANDMINE":
			if attacker.code == "ENGINEER":
				note = "工兵排除了地雷"
				return BattleResolution(attacker, defender, attacker, False, False, note)
			if attacker.code == "BOMB":
				note = "炸弹引爆地雷，双方同归于尽"
				return BattleResolution(attacker, defender, None, True, False, note)
			note = "非工兵踩雷被炸毁"
			return BattleResolution(attacker, defender, defender, False, False, note)

		if attacker.code == "BOMB":
			note = "炸弹同归于尽"
			return BattleResolution(attacker, defender, None, True, False, note)

		if attacker.rank > defender.rank:
			note = f"{attacker.spec.label} 击败 {defender.spec.label}"
			return BattleResolution(attacker, defender, attacker, False, False, note)
		if attacker.rank < defender.rank:
			note = f"{attacker.spec.label} 被 {defender.spec.label} 击败"
			return BattleResolution(attacker, defender, defender, False, False, note)

		note = "双方同级互毙"
		return BattleResolution(attacker, defender, None, True, False, note)

	def apply_move(self, move: Move) -> Optional[BattleResolution]:
		if move.kind is MoveKind.FLIP:
			if move.dst is None:
				raise IllegalMove("Flip move must specify target")
			piece = self.piece_at(move.dst)
			if piece is None:
				raise IllegalMove("No piece to flip")
			piece.face_up = True
			piece.revealed_turn = self.turn_counter
			return None

		if move.src is None or move.dst is None:
			raise IllegalMove("Move requires both source and destination")

		src_tile = self.tiles[move.src]
		dst_tile = self.tiles[move.dst]
		attacker = src_tile.occupant
		if attacker is None:
			raise IllegalMove("No piece at source")

		attacker.face_up = True
		attacker.revealed_turn = attacker.revealed_turn or self.turn_counter

		battle: Optional[BattleResolution] = None
		if dst_tile.occupant is None:
			dst_tile.occupant = attacker
			src_tile.occupant = None
			attacker.position = move.dst
		else:
			battle = self.resolve_attack(move.src, move.dst)
			self._apply_battle(move, battle)
			self.last_capture_turn = self.turn_counter

		self.move_counter += 1
		return battle

	def _apply_battle(self, move: Move, battle: BattleResolution) -> None:
		src_tile = self.tiles[move.src]  # type: ignore[index]
		dst_tile = self.tiles[move.dst]  # type: ignore[index]
		attacker = battle.attacker
		defender = battle.defender

		if battle.both_destroyed or battle.winner is None:
			src_tile.occupant = None
			dst_tile.occupant = None
			attacker.position = None
			defender.position = None
			return

		if battle.winner is attacker:
			src_tile.occupant = None
			dst_tile.occupant = attacker
			defender.position = None
			attacker.position = move.dst
			return

		# Defender wins, attacker removed.
		src_tile.occupant = None
		attacker.position = None

	def mobility(self, player: Player) -> int:
		count = 0
		for tile in self.tiles.values():
			piece = tile.occupant
			if piece and piece.owner is player and piece.movable:
				if self.legal_moves_for(player, piece.position or tile.coord):
					count += 1
		return count

	def pieces(self, player: Player) -> List[Piece]:
		return [tile.occupant for tile in self.tiles.values() if tile.occupant and tile.occupant.owner is player]

	def clone(self) -> "JunqiBoard":
		board = JunqiBoard()
		for coord, tile in self.tiles.items():
			if tile.occupant:
				spec = PIECE_SPECS[tile.occupant.code]
				cloned_piece = Piece(
					spec=spec,
					owner=tile.occupant.owner,
					face_up=tile.occupant.face_up,
					position=coord,
					revealed_turn=tile.occupant.revealed_turn,
				)
				board.tiles[coord].occupant = cloned_piece
		board.move_counter = self.move_counter
		board.turn_counter = self.turn_counter
		board.last_capture_turn = self.last_capture_turn
		return board

	def flag_position(self, player: Player) -> Optional[Coord]:
		for coord, tile in self.tiles.items():
			if tile.occupant and tile.occupant.owner is player and tile.occupant.code == "FLAG":
				return coord
		return None


class GameState:
	"""Wrap JunqiBoard with turn management and logging."""

	def __init__(self, board: Optional[JunqiBoard] = None) -> None:
		self.board = board or JunqiBoard()
		self.current_player: Player = Player.RED
		self.turn_index: int = 0
		self.logs: List[str] = []
		self.status = GameStatus(GameTermination.ONGOING, None)

	def new_game(self, rng: Optional[random.Random] = None) -> None:
		self.board.reset(rng)
		self.current_player = Player.RED
		self.turn_index = 0
		self.logs.clear()
		self.status = GameStatus(GameTermination.ONGOING, None)

	def clone(self) -> "GameState":
		cloned = GameState(self.board.clone())
		cloned.current_player = self.current_player
		cloned.turn_index = self.turn_index
		cloned.board.turn_counter = self.board.turn_counter
		cloned.board.last_capture_turn = self.board.last_capture_turn
		cloned.logs = list(self.logs)
		cloned.status = GameStatus(self.status.outcome, self.status.winner, self.status.reason)
		return cloned

	def legal_moves(self, coord: Coord) -> List[Move]:
		return self.board.legal_moves_for(self.current_player, coord)

	def all_legal_moves(self, player: Optional[Player] = None) -> List[Move]:
		player = player or self.current_player
		moves: List[Move] = []
		for coord, tile in self.board.tiles.items():
			if tile.occupant and tile.occupant.owner is player:
				moves.extend(self.board.legal_moves_for(player, coord))
		return moves

	def flip_piece(self, coord: Coord) -> None:
		piece = self.board.piece_at(coord)
		if piece is None:
			raise IllegalMove("选中的格子没有棋子")
		if piece.owner is not self.current_player:
			raise IllegalMove("无法翻开敌方已掌控的棋子")
		if piece.face_up:
			raise IllegalMove("该棋子已被翻开")
		move = Move(MoveKind.FLIP, self.current_player, None, coord, note="翻面")
		self.board.apply_move(move)
		self._log(f"{self.current_player.name_cn} 翻开 {piece.spec.label}")

	def play_move(self, move: Move) -> GameStatus:
		battle = self.board.apply_move(move)
		capture_happened = battle is not None
		if battle:
			self._on_battle(battle)
		else:
			piece = self.board.piece_at(move.dst) if move.dst else None
			if piece:
				self._log(f"{move.player.name_cn}{'移动' if move.kind is MoveKind.MOVE else ''} {piece.spec.label}")

		# Update counters
		self.turn_index += 1
		self.board.turn_counter = self.turn_index
		if capture_happened:
			self.board.last_capture_turn = self.turn_index

		# Evaluate termination
		status = self._evaluate_status(battle)
		if status.outcome is GameTermination.ONGOING:
			self.current_player = self.current_player.opponent
		else:
			self.status = status
		return status

	def _on_battle(self, battle: BattleResolution) -> None:
		self._log(battle.note)

	def _evaluate_status(self, battle: Optional[BattleResolution]) -> GameStatus:
		# Primary victory condition: flag capture
		if battle and battle.captured_flag:
			winner = battle.attacker.owner
			return GameStatus(GameTermination.VICTORY, winner, "夺旗胜利")

		# Check if either player's flag is missing (captured in previous moves)
		for player in (Player.RED, Player.BLUE):
			flag_pos = self.board.flag_position(player)
			if flag_pos is None:
				winner = player.opponent
				return GameStatus(GameTermination.VICTORY, winner, "夺旗胜利")

		# Secondary condition: opponent has no legal moves (stalemate leads to victory)
		opponent = self.current_player.opponent
		opponent_moves = self.all_legal_moves(opponent)
		if not opponent_moves:
			mobility = self.board.mobility(opponent)
			if mobility == 0:
				return GameStatus(GameTermination.VICTORY, self.current_player, "对手无子可动")

		# Draw condition: long game without captures
		if self.turn_index - self.board.last_capture_turn > 120:
			return GameStatus(GameTermination.DRAW, None, "长回合无战斗判和")

		return GameStatus(GameTermination.ONGOING, None)

	def _log(self, text: str) -> None:
		timestamp = time.strftime("%H:%M:%S")
		self.logs.append(f"[{timestamp}] {text}")


def create_logic_state(seed: Optional[int] = None, randomize: bool = True) -> GameState:
	"""Helper for tests: create a deterministic GameState."""
	rng = random.Random(seed)
	board = JunqiBoard()
	board.reset(rng, randomize=randomize)
	state = GameState(board)
	state.current_player = Player.RED
	return state
