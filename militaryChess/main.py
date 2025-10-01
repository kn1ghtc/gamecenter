"""Pygame implementation of Chinese Military Chess (Junqi).

This module contains the main game application and user interface.
The core game logic, AI engine, and evaluation functions are in separate modules.
"""

from __future__ import annotations

import array
import math
import platform
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

# Ensure repository root is on sys.path for shared utilities if needed.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

# Use absolute imports consistently
from gamecenter.militaryChess.ai_engine import AIController, AIMovePlanner, SettingsManager
from gamecenter.militaryChess.game_logic import (
    ALL_COORDS, BOARD_COLS, BOARD_ROWS, Coord, GameState, GameStatus,
    GameTermination, IllegalMove, JunqiBoard, Move, MoveKind, Piece, Player,
    create_logic_state
)


class FontManager:
	"""Simplified cross-platform Chinese font manager."""

	def __init__(self) -> None:
		if not pygame.font.get_init():
			pygame.font.init()

		self.system = platform.system()
		self.fonts: Dict[Tuple[int, bool], pygame.font.Font] = {}
		self.font_name = self._get_platform_font()

	def _get_platform_font(self) -> str:
		"""Get the best Chinese font for current platform."""
		if self.system == "Darwin":
			# Use pygame font name (lowercase without spaces) for macOS
			return "hiraginosansgb"  # Hiragino Sans GB - best Chinese support on macOS
		elif self.system == "Windows":
			return "microsoftyahei"
		else:  # Linux and others
			return "notosanscjksc"

	def get_font(self, size: int, bold: bool = False) -> pygame.font.Font:
		"""Get a Chinese-compatible font with given size and style."""
		key = (size, bold)
		if key in self.fonts:
			return self.fonts[key]

		font = pygame.font.SysFont(self.font_name, size, bold=bold)
		self.fonts[key] = font
		return font
class SoundManager:
	def __init__(self, volume: float = 0.6) -> None:
		self.enabled = False
		self.sounds: Dict[str, Optional[pygame.mixer.Sound]] = {}
		self.volume = max(0.0, min(1.0, volume))
		try:
			if not pygame.mixer.get_init():
				pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
			self.enabled = True
		except Exception:
			self.enabled = False
		if self.enabled:
			self.sounds = {
				"move": self._create_tone(660, 0.08),
				"attack": self._create_tone(520, 0.12),
				"flip": self._create_tone(880, 0.05),
				"victory": self._create_tone(440, 0.3),
			}

	def _create_tone(self, freq: int, duration: float) -> Optional[pygame.mixer.Sound]:
		if not self.enabled:
			return None
		sample_rate = 22050
		n_samples = int(sample_rate * duration)
		buf = array.array("h")
		amplitude = int(32767 * self.volume)
		for i in range(n_samples):
			t = i / sample_rate
			value = int(amplitude * math.sin(2 * math.pi * freq * t))
			buf.append(value)
		try:
			sound = pygame.mixer.Sound(buffer=buf.tobytes())
			sound.set_volume(self.volume)
			return sound
		except Exception:
			return None

	def play(self, name: str) -> None:
		if not self.enabled:
			return
		sound = self.sounds.get(name)
		if sound is not None:
			try:
				sound.play()
			except Exception:
				pass


class NetworkStub:
	"""Placeholder for future online multiplayer support."""

	def __init__(self) -> None:
		self.connected = False

	def connect(self, _host: str, _port: int) -> bool:
		return False

	def send_move(self, _move: Move) -> None:
		pass

	def receive_moves(self) -> List[Move]:
		return []


# UI Layout Configuration with responsive scaling
class UIConfig:
	def __init__(self, screen_width: int, screen_height: int, fullscreen: bool = False):
		self.fullscreen = fullscreen
		self.base_screen_width = 1200
		self.base_screen_height = 840

		if fullscreen:
			# Get display info for fullscreen scaling
			display_info = pygame.display.Info()
			self.screen_width = display_info.current_w
			self.screen_height = display_info.current_h
		else:
			self.screen_width = screen_width
			self.screen_height = screen_height

		# Calculate scaling factors
		self.scale_x = self.screen_width / self.base_screen_width
		self.scale_y = self.screen_height / self.base_screen_height
		self.scale = min(self.scale_x, self.scale_y)

		# Scaled board dimensions
		self.board_origin = (int(80 * self.scale), int(60 * self.scale))
		self.cell_w = int(90 * self.scale)
		self.cell_h = int(58 * self.scale)
		self.board_width = self.cell_w * BOARD_COLS
		self.board_height = self.cell_h * BOARD_ROWS
		self.side_panel_width = int(360 * self.scale)

		# Font sizes based on scale
		self.title_font_size = int(44 * self.scale)
		self.font_size = int(26 * self.scale)
		self.small_font_size = int(20 * self.scale)
		self.tiny_font_size = int(16 * self.scale)

	def scaled(self, value: int) -> int:
		"""Scale a value based on current scale factor."""
		return int(value * self.scale)


# Enhanced modern color scheme
COLORS = {
	"background": (15, 20, 30),
	"board_bg": (45, 60, 85),
	"cell_normal": (95, 115, 145),
	"piece_red": (220, 85, 85),
	"piece_blue": (85, 125, 235),
	"face_down": (55, 70, 95),
	"highlight": (255, 220, 100),
	"move_target": (120, 220, 140),
	"camp": (140, 180, 140),
	"camp_border": (100, 150, 100),
	"hq": (180, 120, 120),
	"hq_border": (150, 80, 80),
	"rail": (200, 200, 200),
	"rail_bg": (65, 80, 105),
	"panel_bg": (35, 45, 65),
	"text_primary": (240, 240, 240),
	"text_secondary": (200, 200, 200),
	"text_dim": (160, 160, 160),
	"button_bg": (70, 110, 160),
	"button_border": (220, 230, 240),
	"menu_title": (240, 225, 180),
	"menu_subtitle": (210, 200, 170),
	"shadow": (0, 0, 0, 80),
}

RULES_TEXT = [
	"• 暗棋模式：所有棋子随机朝下，翻面后方可行动。",
	"• 棋盘为 5×12，军旗需放置在己方司令部。",
	"• 工兵可沿铁路任意转弯前进；其它可沿铁路直行多格。",
	"• 军旗、地雷不可移动；工兵拆雷，炸弹遇敌同归于尽。",
	"• 占领敌军旗或让对手无棋可走即可胜利。",
	"• 鼠标左键选择己方棋子，再点击合法位置移动或攻击。",
	"• 右侧日志将记录所有翻面、移动与战斗结果。",
]


class GameApp:
	def __init__(self) -> None:
		pygame.init()

		self.settings = SettingsManager()
		fullscreen = self.settings.data.get("fullscreen", False)

		if fullscreen:
			self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		else:
			self.screen = pygame.display.set_mode((1200, 840))

		pygame.display.set_caption("中国军棋 - 军旗夺取战")

		# Initialize UI configuration
		screen_size = self.screen.get_size()
		self.ui = UIConfig(screen_size[0], screen_size[1], fullscreen)

		self.clock = pygame.time.Clock()
		self.sound = SoundManager(self.settings.data.get("volume", 0.6))
		self.ai_controller = AIController(self.settings.as_config())
		self.ai_planner = AIMovePlanner(self.ai_controller)
		self.network = NetworkStub()

		self.state = "menu"
		self.running = True

		# Initialize cross-platform font manager for Chinese text rendering
		self.font_manager = FontManager()
		self.title_font = self.font_manager.get_font(self.ui.title_font_size, bold=True)
		self.font = self.font_manager.get_font(self.ui.font_size)
		self.small_font = self.font_manager.get_font(self.ui.small_font_size)
		self.tiny_font = self.font_manager.get_font(self.ui.tiny_font_size)

		self.message = "欢迎来到中国军棋！"
		self.ai_thinking = False
		self.ai_start_time = 0.0
		self.selected: Optional[Coord] = None
		self.highlight_moves: List[Move] = []
		self.rules_scroll = 0
		self.show_fps = self.settings.data.get("show_fps", False)

		self._build_menu()
		self.reset_game()

	def _build_menu(self) -> None:
		center_x = self.ui.screen_width // 2
		start_y = self.ui.scaled(320)
		button_w, button_h = self.ui.scaled(320), self.ui.scaled(70)
		spacing = self.ui.scaled(100)

		self.menu_buttons = [
			("开始游戏", pygame.Rect(center_x - button_w // 2, start_y, button_w, button_h), "start"),
			("规则说明", pygame.Rect(center_x - button_w // 2, start_y + spacing, button_w, button_h), "rules"),
			("设置", pygame.Rect(center_x - button_w // 2, start_y + spacing * 2, button_w, button_h), "settings"),
			("退出", pygame.Rect(center_x - button_w // 2, start_y + spacing * 3, button_w, button_h), "quit"),
		]

	def reset_game(self, randomize: Optional[bool] = None) -> None:
		rng = random.Random()
		board = JunqiBoard()

		# Use configuration to determine randomization
		use_random = self.settings.data.get("random_layout", True) if randomize is None else randomize
		board.reset(rng, randomize=use_random)

		# Initialize all pieces as face up or face down based on dark_mode setting
		dark_mode = self.settings.data.get("dark_mode", True)
		for tile in board.tiles.values():
			if tile.occupant:
				# In dark mode: face down (False), in light mode: face up (True)
				tile.occupant.face_up = not dark_mode

		self.game_state = GameState(board)
		self.game_state.current_player = Player.RED
		self.game_state.logs = []
		self.game_state.status = GameStatus(GameTermination.ONGOING, None)
		self.selected = None
		self.highlight_moves = []
		self.ai_thinking = False
		self.ai_start_time = 0.0

		if dark_mode:
			self.message = "暗棋模式：请翻开己方棋子后再行动。"
		else:
			self.message = "明棋模式：所有棋子可见，开始对弈！"

	def toggle_fullscreen(self) -> None:
		self.settings.data["fullscreen"] = not self.settings.data.get("fullscreen", False)
		self.settings.save()

		if self.settings.data["fullscreen"]:
			self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		else:
			self.screen = pygame.display.set_mode((1200, 840))

		# Reinitialize UI configuration
		screen_size = self.screen.get_size()
		self.ui = UIConfig(screen_size[0], screen_size[1], self.settings.data["fullscreen"])

		# Reinitialize fonts with new scaling
		self.title_font = self.font_manager.get_font(self.ui.title_font_size, bold=True)
		self.font = self.font_manager.get_font(self.ui.font_size)
		self.small_font = self.font_manager.get_font(self.ui.small_font_size)
		self.tiny_font = self.font_manager.get_font(self.ui.tiny_font_size)

		self._build_menu()

	def run(self) -> None:
		while self.running:
			self._game_loop_step()
		pygame.quit()

	def _game_loop_step(self) -> None:
		dt = self.clock.tick(60) / 1000.0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_F11:
					self.toggle_fullscreen()
			elif self.state == "menu":
				self._handle_menu_event(event)
			elif self.state == "rules":
				self._handle_rules_event(event)
			elif self.state in {"game", "gameover"}:
				self._handle_game_event(event)

		if self.state == "game":
			self._update_game(dt)

		self._draw()
		pygame.display.flip()

	def _handle_menu_event(self, event: pygame.event.Event) -> None:
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			for label, rect, action in self.menu_buttons:
				if rect.collidepoint(event.pos):
					if action == "start":
						self.reset_game()
						self.state = "game"
					elif action == "rules":
						self.rules_scroll = 0
						self.state = "rules"
					elif action == "settings":
						# TODO: Implement settings screen
						pass
					else:
						self.running = False
		if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
			self.reset_game()
			self.state = "game"

	def _handle_rules_event(self, event: pygame.event.Event) -> None:
		if event.type == pygame.KEYDOWN:
			if event.key in {pygame.K_ESCAPE, pygame.K_BACKSPACE}:
				self.state = "menu"
			elif event.key == pygame.K_UP:
				self.rules_scroll = max(0, self.rules_scroll - self.ui.scaled(20))
			elif event.key == pygame.K_DOWN:
				self.rules_scroll += self.ui.scaled(20)
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			self.state = "menu"

	def _handle_game_event(self, event: pygame.event.Event) -> None:
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				self.state = "menu"
			elif event.key == pygame.K_F5:
				self.reset_game()
				self.state = "game"  # Ensure we're in game state after reset
			elif event.key == pygame.K_F3:
				self.show_fps = not self.show_fps
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.state == "game":
			coord = self._coord_from_pos(event.pos)
			if coord is not None:
				self._on_board_click(coord)

	def _update_game(self, _dt: float) -> None:
		if self.game_state.status.outcome is not GameTermination.ONGOING:
			return
		if self.game_state.current_player is Player.BLUE:
			available_moves = self.game_state.all_legal_moves()
			if not available_moves:
				if self._ai_flip_face_down_piece():
					return
				self._handle_ai_no_moves()
				return
			if not self.ai_thinking and not self.ai_planner.running:
				self.ai_planner.start(self.game_state)
				self.ai_thinking = True
				self.ai_start_time = time.perf_counter()
				self.message = "蓝方思考中……"
			move, error = self.ai_planner.poll()
			if move:
				result = self.game_state.play_move(move)
				self.sound.play("attack" if move.kind is MoveKind.ATTACK else "move")
				self.ai_thinking = False
				self.selected = None
				self.highlight_moves = []
				self._post_move(result)
			elif error:
				self.message = f"AI 出错: {error}"
				self.ai_thinking = False

	def _ai_flip_face_down_piece(self) -> bool:
		face_down_coords = [
			coord
			for coord, tile in self.game_state.board.tiles.items()
			if tile.occupant and tile.occupant.owner is Player.BLUE and not tile.occupant.face_up
		]
		if not face_down_coords:
			return False
		coord = random.choice(face_down_coords)
		try:
			self.game_state.flip_piece(coord)
		except IllegalMove:
			return False
		piece = self.game_state.board.tiles[coord].occupant
		if piece:
			self.message = f"蓝方翻开 {piece.spec.label}"
		self.sound.play("flip")
		return True

	def _handle_ai_no_moves(self) -> None:
		mobility = self.game_state.board.mobility(Player.BLUE)
		if mobility == 0:
			self.ai_thinking = False
			self.ai_planner.running = False
			self.sound.play("victory")
			self.game_state.status = GameStatus(GameTermination.VICTORY, Player.RED, "对手无子可动")
			self.state = "gameover"
			self.message = "蓝方无棋可走，红方获胜！按 F5 再战或 ESC 返回菜单。"
		else:
			self.ai_thinking = False
			self.message = "蓝方暂时无棋可动，正在重新评估。"

	def _on_board_click(self, coord: Coord) -> None:
		if self.game_state.status.outcome is not GameTermination.ONGOING:
			return
		if self.game_state.current_player is not Player.RED:
			return
		tile = self.game_state.board.tiles[coord]
		piece = tile.occupant
		if self.selected and coord == self.selected:
			self.selected = None
			self.highlight_moves = []
			return
		if self.selected:
			destination_moves = [m for m in self.highlight_moves if m.dst == coord]
			if destination_moves:
				move = destination_moves[0]
				result = self.game_state.play_move(move)
				self.sound.play("attack" if move.kind is MoveKind.ATTACK else "move")
				self.selected = None
				self.highlight_moves = []
				self._post_move(result)
				return
		if piece and piece.owner is Player.RED:
			if not piece.face_up:
				try:
					self.game_state.flip_piece(coord)
					self.sound.play("flip")
				except IllegalMove:
					pass
			self.selected = coord
			self.highlight_moves = self.game_state.legal_moves(coord)
			if not self.highlight_moves:
				self.message = "此棋暂无法行动"
		else:
			self.selected = None
			self.highlight_moves = []

	def _post_move(self, status: GameStatus) -> None:
		if status.outcome is GameTermination.VICTORY:
			self.sound.play("victory")
			self.message = f"{status.winner.name_cn if status.winner else '未知'} 获胜！按 F5 再战或 ESC 返回菜单。"
			self.state = "gameover"
		elif status.outcome is GameTermination.DRAW:
			self.message = "双方僵持，和棋！按 F5 再战或 ESC 返回菜单。"
			self.state = "gameover"
		else:
			self.message = f"轮到 {self.game_state.current_player.name_cn}。"

	def _coord_from_pos(self, pos: Tuple[int, int]) -> Optional[Coord]:
		x, y = pos
		bx, by = self.ui.board_origin
		if not (bx <= x < bx + self.ui.board_width and by <= y < by + self.ui.board_height):
			return None
		col = (x - bx) // self.ui.cell_w
		row = (y - by) // self.ui.cell_h
		coord = (int(row), int(col))
		from gamecenter.militaryChess.game_logic import is_inside
		return coord if is_inside(coord) else None

	def _draw(self) -> None:
		self.screen.fill(COLORS["background"])
		if self.state == "menu":
			self._draw_menu()
		elif self.state == "rules":
			self._draw_rules()
		else:
			self._draw_game()

	def _draw_menu(self) -> None:
		title_surface = self.title_font.render("中国军棋", True, COLORS["menu_title"])
		title_rect = title_surface.get_rect(center=(self.ui.screen_width // 2, self.ui.scaled(180)))
		self.screen.blit(title_surface, title_rect)

		sub_surface = self.font.render("军旗夺取战", True, COLORS["menu_subtitle"])
		self.screen.blit(sub_surface, sub_surface.get_rect(center=(self.ui.screen_width // 2, self.ui.scaled(240))))

		for label, rect, _ in self.menu_buttons:
			# Draw button with rounded corners effect
			pygame.draw.rect(self.screen, COLORS["button_bg"], rect, border_radius=self.ui.scaled(16))
			pygame.draw.rect(self.screen, COLORS["button_border"], rect, width=3, border_radius=self.ui.scaled(16))
			text = self.font.render(label, True, COLORS["text_primary"])
			self.screen.blit(text, text.get_rect(center=rect.center))

		footer = self.small_font.render("提示：按 Enter 快速开始，F11 切换全屏", True, COLORS["text_dim"])
		self.screen.blit(footer, footer.get_rect(center=(self.ui.screen_width // 2, self.ui.screen_height - self.ui.scaled(80))))

	def _draw_rules(self) -> None:
		title = self.title_font.render("规则说明", True, COLORS["menu_title"])
		self.screen.blit(title, title.get_rect(center=(self.ui.screen_width // 2, self.ui.scaled(120))))

		instructions = [
			"• 军旗置于司令部，地雷仅能布在后两排。",
			"• 工兵拆雷，炸弹对敌自爆；同级对撞同归于尽。",
			"• 铁路连接的棋子可加速前进，占领对方军旗获胜。",
			"• 左键返回菜单，方向键上下可滚动列表。",
		]
		y = self.ui.scaled(200) - self.rules_scroll
		for line in instructions + RULES_TEXT:
			surf = self.font.render(line, True, COLORS["text_secondary"])
			rect = surf.get_rect(center=(self.ui.screen_width // 2, y))
			self.screen.blit(surf, rect)
			y += self.ui.scaled(60)

	def _draw_game(self) -> None:
		self._draw_board()
		self._draw_side_panel()
		if self.show_fps:
			fps = self.tiny_font.render(f"FPS: {self.clock.get_fps():.1f}", True, COLORS["text_dim"])
			self.screen.blit(fps, (self.ui.screen_width - self.ui.scaled(120), self.ui.scaled(20)))

	def _draw_board(self) -> None:
		bx, by = self.ui.board_origin
		board_rect = pygame.Rect(bx, by, self.ui.board_width, self.ui.board_height)

		# Draw board shadow for depth
		shadow_rect = board_rect.copy()
		shadow_rect.x += self.ui.scaled(4)
		shadow_rect.y += self.ui.scaled(4)
		shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
		pygame.draw.rect(shadow_surface, COLORS["shadow"], shadow_surface.get_rect(), border_radius=self.ui.scaled(16))
		self.screen.blit(shadow_surface, shadow_rect)

		# Draw board background
		pygame.draw.rect(self.screen, COLORS["board_bg"], board_rect, border_radius=self.ui.scaled(16))

		for r in range(BOARD_ROWS):
			for c in range(BOARD_COLS):
				x = bx + c * self.ui.cell_w
				y = by + r * self.ui.cell_h
				rect = pygame.Rect(x + self.ui.scaled(4), y + self.ui.scaled(4),
								 self.ui.cell_w - self.ui.scaled(8), self.ui.cell_h - self.ui.scaled(8))
				coord = (r, c)
				tile = self.game_state.board.tiles[coord]

				# Determine cell appearance based on tile type
				if tile.on_rail:
					# Railway cells with special styling
					color = COLORS["rail_bg"]
					pygame.draw.rect(self.screen, color, rect, border_radius=self.ui.scaled(8))
					# Draw railway pattern (cross lines)
					center_x = rect.centerx
					center_y = rect.centery
					line_length = self.ui.scaled(20)
					pygame.draw.line(self.screen, COLORS["rail"],
								   (center_x - line_length // 2, center_y),
								   (center_x + line_length // 2, center_y), 2)
					pygame.draw.line(self.screen, COLORS["rail"],
								   (center_x, center_y - line_length // 2),
								   (center_x, center_y + line_length // 2), 2)
				elif tile.is_camp:
					# Camp with gradient effect
					color = COLORS["camp"]
					pygame.draw.rect(self.screen, color, rect, border_radius=self.ui.scaled(10))
					pygame.draw.rect(self.screen, COLORS["camp_border"], rect, width=2, border_radius=self.ui.scaled(10))
					# Draw camp symbol (four corners)
					corner_size = self.ui.scaled(6)
					offset = self.ui.scaled(8)
					for dx, dy in [(offset, offset), (rect.width - offset, offset),
								 (offset, rect.height - offset), (rect.width - offset, rect.height - offset)]:
						corner_rect = pygame.Rect(rect.x + dx - corner_size // 2, rect.y + dy - corner_size // 2,
												corner_size, corner_size)
						pygame.draw.rect(self.screen, COLORS["camp_border"], corner_rect, border_radius=2)
				elif tile.is_headquarter:
					# Headquarters with special styling
					color = COLORS["hq"]
					pygame.draw.rect(self.screen, color, rect, border_radius=self.ui.scaled(10))
					pygame.draw.rect(self.screen, COLORS["hq_border"], rect, width=3, border_radius=self.ui.scaled(10))
					# Draw HQ symbol (star shape simplified as diamond)
					center_x = rect.centerx
					center_y = rect.centery
					star_size = self.ui.scaled(8)
					points = [
						(center_x, center_y - star_size),
						(center_x + star_size, center_y),
						(center_x, center_y + star_size),
						(center_x - star_size, center_y)
					]
					pygame.draw.polygon(self.screen, COLORS["hq_border"], points, width=2)
				else:
					# Normal cells
					color = COLORS["cell_normal"]
					pygame.draw.rect(self.screen, color, rect, border_radius=self.ui.scaled(10))

				# Highlight selected piece
				if self.selected == coord:
					pygame.draw.rect(self.screen, COLORS["highlight"], rect, width=4, border_radius=self.ui.scaled(10))

		# Draw move targets
		for move in self.highlight_moves:
			if move.dst is None:
				continue
			r, c = move.dst
			x = bx + c * self.ui.cell_w
			y = by + r * self.ui.cell_h
			rect = pygame.Rect(x + self.ui.scaled(12), y + self.ui.scaled(12),
							 self.ui.cell_w - self.ui.scaled(24), self.ui.cell_h - self.ui.scaled(24))
			pygame.draw.rect(self.screen, COLORS["move_target"], rect, width=3, border_radius=self.ui.scaled(10))

		# Draw pieces
		for coord in ALL_COORDS:
			tile = self.game_state.board.tiles[coord]
			if tile.occupant:
				self._draw_piece(tile.occupant, coord)

	def _draw_piece(self, piece: Piece, coord: Coord) -> None:
		bx, by = self.ui.board_origin
		r, c = coord
		x = bx + c * self.ui.cell_w + self.ui.cell_w // 2
		y = by + r * self.ui.cell_h + self.ui.cell_h // 2
		radius_x = self.ui.cell_w // 2 - self.ui.scaled(8)
		radius_y = self.ui.cell_h // 2 - self.ui.scaled(10)

		color = COLORS["piece_red"] if piece.owner is Player.RED else COLORS["piece_blue"]
		rect = pygame.Rect(0, 0, radius_x * 2, radius_y * 2)
		rect.center = (x, y)

		if not piece.face_up:
			owner_color = COLORS["piece_red"] if piece.owner is Player.RED else COLORS["piece_blue"]
			pygame.draw.ellipse(self.screen, COLORS["face_down"], rect)
			pygame.draw.ellipse(self.screen, owner_color, rect, width=3)
			question = self.small_font.render("？", True, COLORS["text_primary"])
			self.screen.blit(question, question.get_rect(center=(x, y)))
			return

		pygame.draw.ellipse(self.screen, color, rect)
		pygame.draw.ellipse(self.screen, (20, 20, 20), rect, width=2)
		label = piece.spec.label
		text = self.small_font.render(label, True, COLORS["text_primary"])
		self.screen.blit(text, text.get_rect(center=(x, y)))

	def _draw_side_panel(self) -> None:
		panel_x = self.ui.board_origin[0] + self.ui.board_width + self.ui.scaled(30)
		panel_rect = pygame.Rect(panel_x, self.ui.scaled(40), self.ui.side_panel_width, self.ui.board_height)
		pygame.draw.rect(self.screen, COLORS["panel_bg"], panel_rect, border_radius=self.ui.scaled(18))

		title = self.font.render("战局信息", True, COLORS["text_primary"])
		self.screen.blit(title, (panel_rect.x + self.ui.scaled(20), panel_rect.y + self.ui.scaled(20)))

		# Message area with word wrapping
		msg_lines = self._wrap_text(self.message, self.small_font, self.ui.side_panel_width - self.ui.scaled(40))
		msg_y = panel_rect.y + self.ui.scaled(70)
		for line in msg_lines:
			msg_surface = self.small_font.render(line, True, COLORS["text_secondary"])
			self.screen.blit(msg_surface, (panel_rect.x + self.ui.scaled(20), msg_y))
			msg_y += self.ui.scaled(25)

		self._draw_piece_count(panel_rect.x + self.ui.scaled(20), panel_rect.y + self.ui.scaled(150))

		# Game log
		log_y = panel_rect.y + self.ui.scaled(250)
		log_title = self.small_font.render("对局日志", True, COLORS["text_secondary"])
		self.screen.blit(log_title, (panel_rect.x + self.ui.scaled(20), log_y))
		log_y += self.ui.scaled(30)

		visible_logs = min(12, (self.ui.board_height - self.ui.scaled(250)) // self.ui.scaled(20))
		for entry in self.game_state.logs[-visible_logs:]:
			surf = self.tiny_font.render(entry, True, COLORS["text_dim"])
			self.screen.blit(surf, (panel_rect.x + self.ui.scaled(20), log_y))
			log_y += self.ui.scaled(20)

	def _draw_piece_count(self, x: int, y: int) -> None:
		red_count = len(self.game_state.board.pieces(Player.RED))
		blue_count = len(self.game_state.board.pieces(Player.BLUE))
		red_text = self.small_font.render(f"红方存活：{red_count}", True, COLORS["piece_red"])
		blue_text = self.small_font.render(f"蓝方存活：{blue_count}", True, COLORS["piece_blue"])
		self.screen.blit(red_text, (x, y))
		self.screen.blit(blue_text, (x, y + self.ui.scaled(28)))

	def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
		"""Word wrap text to fit within max_width."""
		words = text.split()
		lines = []
		current_line = []

		for word in words:
			test_line = " ".join(current_line + [word])
			if font.size(test_line)[0] <= max_width:
				current_line.append(word)
			else:
				if current_line:
					lines.append(" ".join(current_line))
					current_line = [word]
				else:
					lines.append(word)

		if current_line:
			lines.append(" ".join(current_line))

		return lines


def run_game() -> None:
	app = GameApp()
	app.run()


if __name__ == "__main__":  # pragma: no cover - manual launch helper
	run_game()
