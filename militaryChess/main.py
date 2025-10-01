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
class BoardTextureRenderer:
	"""Helper class for drawing textured board elements."""
	
	@staticmethod
	def draw_wood_grain(surface: pygame.Surface, rect: pygame.Rect, base_color: Tuple[int, int, int]) -> None:
		"""Draw wood grain pattern on surface."""
		import random
		r, g, b = base_color
		
		# Create subtle wood grain lines
		rng = random.Random(42)  # Use seed for consistency
		for i in range(rect.height // 3):
			y = rect.y + rng.randint(0, rect.height)
			darkness = rng.randint(-15, 5)
			line_color = (max(0, r + darkness), max(0, g + darkness), max(0, b + darkness))
			pygame.draw.line(surface, line_color, 
			               (rect.x, y), (rect.right, y), 1)
	
	@staticmethod
	def draw_star_icon(surface: pygame.Surface, center: Tuple[int, int], radius: int, color: Tuple[int, int, int]) -> None:
		"""Draw a star icon for headquarters."""
		cx, cy = center
		points = []
		for i in range(10):
			angle = (i * 36 - 90) * math.pi / 180  # 5-pointed star
			r = radius if i % 2 == 0 else radius * 0.4
			x = cx + r * math.cos(angle)
			y = cy + r * math.sin(angle)
			points.append((x, y))
		pygame.draw.polygon(surface, color, points)
	
	@staticmethod
	def draw_tent_pattern(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int]) -> None:
		"""Draw tent/camp pattern."""
		# Draw triangle tent
		top = (rect.centerx, rect.y + rect.height // 4)
		left = (rect.x + rect.width // 4, rect.bottom - rect.height // 4)
		right = (rect.right - rect.width // 4, rect.bottom - rect.height // 4)
		pygame.draw.polygon(surface, color, [top, left, right], 2)
		# Draw center line
		pygame.draw.line(surface, color, top, (rect.centerx, rect.bottom - rect.height // 4), 2)


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


# Enhanced modern color scheme with wooden theme
COLORS = {
	"background": (20, 25, 35),
	"board_bg": (139, 90, 43),  # Wood color
	"board_border": (101, 67, 33),  # Dark wood
	"cell_normal": (210, 180, 140),  # Tan
	"cell_light": (230, 200, 160),  # Light tan
	"piece_red": (220, 50, 50),
	"piece_blue": (50, 100, 220),
	"piece_shadow": (0, 0, 0, 60),
	"face_down": (80, 70, 60),
	"face_down_border": (60, 50, 40),
	"highlight": (255, 215, 0),
	"highlight_glow": (255, 235, 100, 80),
	"move_target": (100, 255, 100),
	"move_target_glow": (120, 255, 120, 60),
	"camp": (100, 140, 100),
	"camp_pattern": (80, 120, 80),
	"camp_border": (70, 100, 70),
	"hq": (180, 80, 80),
	"hq_border": (140, 50, 50),
	"hq_star": (255, 215, 0),
	"rail": (120, 120, 120),
	"rail_bg": (100, 80, 60),
	"rail_wood": (130, 100, 70),
	"panel_bg": (40, 50, 70),
	"text_primary": (255, 255, 255),
	"text_secondary": (220, 220, 220),
	"text_dim": (170, 170, 170),
	"button_bg": (70, 110, 160),
	"button_hover": (90, 130, 180),
	"button_border": (220, 230, 240),
	"menu_title": (255, 235, 180),
	"menu_subtitle": (220, 200, 170),
	"shadow": (0, 0, 0, 100),
	"undo_button": (200, 150, 50),
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
		self.settings_scroll = 0
		self.show_fps = self.settings.get("show_fps", False)
		
		# Undo system
		self.move_history: List[Tuple[GameState, str]] = []  # (state_clone, description)
		self.max_undo_steps = self.settings.get("max_undo_steps", 3)
		
		# UI state
		self.hovered_button: Optional[str] = None

		self._build_menu()
		self._build_settings_ui()
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

	def _build_settings_ui(self) -> None:
		"""Build settings interface elements."""
		center_x = self.ui.screen_width // 2
		start_y = self.ui.scaled(200)
		item_h = self.ui.scaled(60)
		
		self.settings_items = [
			{
				"label": "游戏模式",
				"key": "game_mode",
				"type": "toggle",
				"options": [("暗棋", "dark"), ("明棋", "light")],
				"y": start_y
			},
			{
				"label": "允许悔棋",
				"key": "allow_undo",
				"type": "checkbox",
				"y": start_y + item_h
			},
			{
				"label": "悔棋步数",
				"key": "max_undo_steps",
				"type": "slider",
				"range": (1, 5),
				"y": start_y + item_h * 2
			},
			{
				"label": "AI难度",
				"key": "difficulty",
				"type": "toggle",
				"options": [("简单", "easy"), ("标准", "standard"), ("困难", "hard")],
				"y": start_y + item_h * 3
			},
			{
				"label": "音量",
				"key": "volume",
				"type": "slider",
				"range": (0.0, 1.0),
				"y": start_y + item_h * 4
			},
			{
				"label": "显示合法移动",
				"key": "show_legal_moves",
				"type": "checkbox",
				"y": start_y + item_h * 5
			},
		]
		
		# Build back button
		button_w, button_h = self.ui.scaled(200), self.ui.scaled(60)
		back_y = start_y + item_h * 7
		self.settings_back_button = pygame.Rect(center_x - button_w // 2, back_y, button_w, button_h)

	def reset_game(self, randomize: Optional[bool] = None) -> None:
		rng = random.Random()
		board = JunqiBoard()

		# Use configuration to determine randomization
		use_random = self.settings.get("random_layout", True) if randomize is None else randomize
		board.reset(rng, randomize=use_random)

		# Initialize all pieces as face up or face down based on game_mode setting
		dark_mode = self.settings.get("game_mode", "dark") == "dark"
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
		self.move_history = []  # Clear undo history
		self.ai_thinking = False
		self.ai_start_time = 0.0

		if dark_mode:
			self.message = "暗棋模式：请翻开己方棋子后再行动。"
		else:
			self.message = "明棋模式：所有棋子可见，开始对弈！"
	
	def _save_state_for_undo(self, description: str) -> None:
		"""Save current game state to undo history."""
		if not self.settings.get("allow_undo", True):
			return
		
		# Deep copy current state
		import copy
		state_clone = copy.deepcopy(self.game_state)
		
		self.move_history.append((state_clone, description))
		
		# Limit history size
		max_steps = self.settings.get("max_undo_steps", 3)
		if len(self.move_history) > max_steps:
			self.move_history.pop(0)
	
	def undo_move(self) -> bool:
		"""Undo last move. Returns True if successful."""
		if not self.settings.get("allow_undo", True):
			self.message = "悔棋功能已禁用"
			return False
		
		if self.ai_thinking:
			self.message = "AI思考中，无法悔棋"
			return False
		
		if not self.move_history:
			self.message = "没有可以悔棋的步骤"
			return False
		
		# Restore previous state
		self.game_state, description = self.move_history.pop()
		self.selected = None
		self.highlight_moves = []
		self.message = f"已悔棋: {description}"
		return True

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
				elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
					if self.state == "game":
						self.undo_move()
				elif event.key == pygame.K_u and self.state == "game":
					self.undo_move()
			elif self.state == "menu":
				self._handle_menu_event(event)
			elif self.state == "settings":
				self._handle_settings_event(event)
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
						self.settings_scroll = 0
						self.state = "settings"
					else:
						self.running = False
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
			self.reset_game()
			self.state = "game"
		elif event.type == pygame.MOUSEMOTION:
			self.hovered_button = None
			for label, rect, action in self.menu_buttons:
				if rect.collidepoint(event.pos):
					self.hovered_button = action

	def _handle_settings_event(self, event: pygame.event.Event) -> None:
		"""Handle settings screen events."""
		if event.type == pygame.KEYDOWN and event.key in {pygame.K_ESCAPE, pygame.K_BACKSPACE}:
			self.state = "menu"
			return
		
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			# Check back button
			if self.settings_back_button.collidepoint(event.pos):
				self.state = "menu"
				return
			
			# Check setting items
			center_x = self.ui.screen_width // 2
			for item in self.settings_items:
				item_rect = pygame.Rect(center_x - self.ui.scaled(300), item["y"], 
				                       self.ui.scaled(600), self.ui.scaled(50))
				
				if item_rect.collidepoint(event.pos):
					if item["type"] == "checkbox":
						current = self.settings.get(item["key"], False)
						self.settings.set(item["key"], not current)
						
						# Special handling
						if item["key"] == "allow_undo":
							self.max_undo_steps = self.settings.get("max_undo_steps", 3)
					
					elif item["type"] == "toggle":
						current_val = self.settings.get(item["key"])
						options = item["options"]
						
						# Find current index and switch to next
						for i, (label, val) in enumerate(options):
							if val == current_val:
								next_idx = (i + 1) % len(options)
								self.settings.set(item["key"], options[next_idx][1])
								
								# Special handling for game mode
								if item["key"] == "game_mode":
									self.reset_game()
								break
					
					elif item["type"] == "slider":
						# Click on slider to adjust value
						click_x = event.pos[0] - (center_x - self.ui.scaled(150))
						slider_width = self.ui.scaled(300)
						ratio = max(0.0, min(1.0, click_x / slider_width))
						
						min_val, max_val = item["range"]
						if isinstance(min_val, int):
							new_val = int(min_val + ratio * (max_val - min_val))
						else:
							new_val = min_val + ratio * (max_val - min_val)
						
						self.settings.set(item["key"], new_val)
						
						if item["key"] == "max_undo_steps":
							self.max_undo_steps = new_val
		
		elif event.type == pygame.MOUSEMOTION:
			# Hover effect for back button
			self.hovered_button = "back" if self.settings_back_button.collidepoint(event.pos) else None
	
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
			# Check undo button first
			if hasattr(self, 'undo_button_rect') and self.undo_button_rect.collidepoint(event.pos):
				if len(self.move_history) > 0 and not self.ai_thinking:
					self.undo_move()
				return
			
			# Then check board clicks
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
				# Save state before move for undo
				piece = self.game_state.board.tiles[move.src].occupant
				piece_name = piece.spec.label if piece else "棋子"
				self._save_state_for_undo(f"{piece_name}移动")
				
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
		elif self.state == "settings":
			self._draw_settings()
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
	
	def _draw_settings(self) -> None:
		"""Draw settings screen with interactive controls."""
		# Title
		title = self.title_font.render("游戏设置", True, COLORS["menu_title"])
		self.screen.blit(title, title.get_rect(center=(self.ui.screen_width // 2, self.ui.scaled(120))))
		
		center_x = self.ui.screen_width // 2
		
		# Draw each setting item
		for item in self.settings_items:
			y = item["y"]
			
			# Draw label
			label_surf = self.font.render(item["label"], True, COLORS["text_primary"])
			label_rect = label_surf.get_rect(midleft=(center_x - self.ui.scaled(280), y + self.ui.scaled(25)))
			self.screen.blit(label_surf, label_rect)
			
			# Draw control based on type
			if item["type"] == "checkbox":
				# Checkbox
				checked = self.settings.get(item["key"], False)
				checkbox_rect = pygame.Rect(center_x + self.ui.scaled(180), y + self.ui.scaled(10), 
				                           self.ui.scaled(35), self.ui.scaled(35))
				
				color = COLORS["highlight"] if checked else COLORS["cell_normal"]
				pygame.draw.rect(self.screen, color, checkbox_rect, border_radius=self.ui.scaled(6))
				pygame.draw.rect(self.screen, COLORS["button_border"], checkbox_rect, width=2, border_radius=self.ui.scaled(6))
				
				if checked:
					# Draw checkmark
					pygame.draw.line(self.screen, COLORS["background"], 
					               (checkbox_rect.x + self.ui.scaled(8), checkbox_rect.centery),
					               (checkbox_rect.centerx - self.ui.scaled(2), checkbox_rect.y + self.ui.scaled(22)), 3)
					pygame.draw.line(self.screen, COLORS["background"],
					               (checkbox_rect.centerx - self.ui.scaled(2), checkbox_rect.y + self.ui.scaled(22)),
					               (checkbox_rect.right - self.ui.scaled(6), checkbox_rect.y + self.ui.scaled(10)), 3)
			
			elif item["type"] == "toggle":
				# Toggle buttons
				current_val = self.settings.get(item["key"])
				options = item["options"]
				
				button_width = self.ui.scaled(80)
				button_height = self.ui.scaled(35)
				button_spacing = self.ui.scaled(10)
				total_width = len(options) * button_width + (len(options) - 1) * button_spacing
				start_x = center_x + self.ui.scaled(100)
				
				for i, (label, val) in enumerate(options):
					button_rect = pygame.Rect(start_x + i * (button_width + button_spacing), 
					                         y + self.ui.scaled(10), button_width, button_height)
					
					if val == current_val:
						button_color = COLORS["highlight"]
						text_color = COLORS["background"]
					else:
						button_color = COLORS["cell_normal"]
						text_color = COLORS["text_primary"]
					
					pygame.draw.rect(self.screen, button_color, button_rect, border_radius=self.ui.scaled(6))
					pygame.draw.rect(self.screen, COLORS["button_border"], button_rect, width=2, border_radius=self.ui.scaled(6))
					
					btn_text = self.small_font.render(label, True, text_color)
					self.screen.blit(btn_text, btn_text.get_rect(center=button_rect.center))
			
			elif item["type"] == "slider":
				# Slider
				slider_rect = pygame.Rect(center_x + self.ui.scaled(20), y + self.ui.scaled(20), 
				                         self.ui.scaled(300), self.ui.scaled(15))
				
				# Draw slider track
				pygame.draw.rect(self.screen, COLORS["cell_normal"], slider_rect, border_radius=self.ui.scaled(8))
				pygame.draw.rect(self.screen, COLORS["button_border"], slider_rect, width=2, border_radius=self.ui.scaled(8))
				
				# Get current value and calculate position
				current_val = self.settings.get(item["key"])
				min_val, max_val = item["range"]
				ratio = (current_val - min_val) / (max_val - min_val)
				
				# Draw filled portion
				filled_width = int(slider_rect.width * ratio)
				filled_rect = pygame.Rect(slider_rect.x, slider_rect.y, filled_width, slider_rect.height)
				pygame.draw.rect(self.screen, COLORS["highlight"], filled_rect, border_radius=self.ui.scaled(8))
				
				# Draw slider handle
				handle_x = slider_rect.x + filled_width
				handle_rect = pygame.Rect(handle_x - self.ui.scaled(10), slider_rect.centery - self.ui.scaled(15), 
				                         self.ui.scaled(20), self.ui.scaled(30))
				pygame.draw.rect(self.screen, COLORS["text_primary"], handle_rect, border_radius=self.ui.scaled(4))
				pygame.draw.rect(self.screen, COLORS["button_border"], handle_rect, width=2, border_radius=self.ui.scaled(4))
				
				# Draw value text
				if isinstance(min_val, int):
					value_text = self.small_font.render(str(current_val), True, COLORS["text_secondary"])
				else:
					value_text = self.small_font.render(f"{current_val:.1f}", True, COLORS["text_secondary"])
				self.screen.blit(value_text, value_text.get_rect(midleft=(slider_rect.right + self.ui.scaled(15), y + self.ui.scaled(25))))
		
		# Draw back button
		button_color = COLORS["button_hover"] if self.hovered_button == "back" else COLORS["button_bg"]
		pygame.draw.rect(self.screen, button_color, self.settings_back_button, border_radius=self.ui.scaled(12))
		pygame.draw.rect(self.screen, COLORS["button_border"], self.settings_back_button, width=3, border_radius=self.ui.scaled(12))
		
		back_text = self.font.render("返回菜单", True, COLORS["text_primary"])
		self.screen.blit(back_text, back_text.get_rect(center=self.settings_back_button.center))
		
		# Draw instructions
		footer = self.small_font.render("提示：点击设置项进行修改，ESC 返回", True, COLORS["text_dim"])
		self.screen.blit(footer, footer.get_rect(center=(self.ui.screen_width // 2, self.ui.screen_height - self.ui.scaled(60))))

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

		# Draw board background with wood texture
		pygame.draw.rect(self.screen, COLORS["board_bg"], board_rect, border_radius=self.ui.scaled(16))
		BoardTextureRenderer.draw_wood_grain(self.screen, board_rect, COLORS["board_bg"])
		pygame.draw.rect(self.screen, COLORS["board_border"], board_rect, width=self.ui.scaled(6), border_radius=self.ui.scaled(16))

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
					# Camp with gradient and tent pattern
					color = COLORS["camp"]
					pygame.draw.rect(self.screen, color, rect, border_radius=self.ui.scaled(10))
					pygame.draw.rect(self.screen, COLORS["camp_border"], rect, width=2, border_radius=self.ui.scaled(10))
					# Draw tent pattern
					BoardTextureRenderer.draw_tent_pattern(self.screen, rect, COLORS["camp_pattern"])
				elif tile.is_headquarter:
					# Headquarters with star icon
					color = COLORS["hq"]
					pygame.draw.rect(self.screen, color, rect, border_radius=self.ui.scaled(10))
					pygame.draw.rect(self.screen, COLORS["hq_border"], rect, width=3, border_radius=self.ui.scaled(10))
					# Draw star icon
					BoardTextureRenderer.draw_star_icon(self.screen, rect.center, self.ui.scaled(10), COLORS["hq_star"])
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

		# Draw piece shadow
		shadow_rect = rect.copy()
		shadow_rect.x += self.ui.scaled(2)
		shadow_rect.y += self.ui.scaled(2)
		shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
		pygame.draw.ellipse(shadow_surface, COLORS["piece_shadow"], shadow_surface.get_rect())
		self.screen.blit(shadow_surface, shadow_rect)

		if not piece.face_up:
			owner_color = COLORS["piece_red"] if piece.owner is Player.RED else COLORS["piece_blue"]
			pygame.draw.ellipse(self.screen, COLORS["face_down"], rect)
			pygame.draw.ellipse(self.screen, COLORS["face_down_border"], rect, width=2)
			pygame.draw.ellipse(self.screen, owner_color, rect, width=1)
			question = self.small_font.render("？", True, COLORS["text_primary"])
			self.screen.blit(question, question.get_rect(center=(x, y)))
			return

		# Draw piece with gradient effect (lighter center)
		pygame.draw.ellipse(self.screen, color, rect)
		# Add highlight on top half
		highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 2)
		highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
		r, g, b = color
		lighter = (min(255, r + 30), min(255, g + 30), min(255, b + 30), 40)
		pygame.draw.ellipse(highlight_surface, lighter, highlight_surface.get_rect())
		self.screen.blit(highlight_surface, highlight_rect)
		
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
		
		# Undo button (if enabled and available)
		if self.settings.get("allow_undo", True) and self.state == "game":
			undo_y = panel_rect.y + self.ui.scaled(200)
			undo_button_rect = pygame.Rect(panel_rect.x + self.ui.scaled(20), undo_y, 
			                               self.ui.side_panel_width - self.ui.scaled(40), self.ui.scaled(45))
			
			# Button enabled/disabled state
			can_undo = len(self.move_history) > 0 and not self.ai_thinking
			button_color = COLORS["undo_button"] if can_undo else COLORS["cell_normal"]
			
			pygame.draw.rect(self.screen, button_color, undo_button_rect, border_radius=self.ui.scaled(8))
			pygame.draw.rect(self.screen, COLORS["button_border"], undo_button_rect, width=2, border_radius=self.ui.scaled(8))
			
			undo_text = f"悔棋 ({len(self.move_history)}/{self.max_undo_steps})"
			undo_surf = self.small_font.render(undo_text, True, COLORS["text_primary"])
			self.screen.blit(undo_surf, undo_surf.get_rect(center=undo_button_rect.center))
			
			# Store button rect for click detection
			self.undo_button_rect = undo_button_rect

		# Game log
		log_y = panel_rect.y + self.ui.scaled(270) if self.settings.get("allow_undo", True) else panel_rect.y + self.ui.scaled(250)
		log_title = self.small_font.render("对局日志", True, COLORS["text_secondary"])
		self.screen.blit(log_title, (panel_rect.x + self.ui.scaled(20), log_y))
		log_y += self.ui.scaled(30)

		visible_logs = min(10, (panel_rect.bottom - log_y - self.ui.scaled(20)) // self.ui.scaled(20))
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
