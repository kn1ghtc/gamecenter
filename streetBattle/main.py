from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
import random
import math


# ---------------------------------------------------------------------------
# Bootstrap: ensure ``gamecenter`` 绝对导入在脚本直接运行时可用
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT_STR = str(_PROJECT_ROOT)
if _PROJECT_ROOT_STR not in sys.path:
	sys.path.insert(0, _PROJECT_ROOT_STR)

if "gamecenter" not in sys.modules:
	gamecenter_module = ModuleType("gamecenter")
	gamecenter_module.__path__ = [_PROJECT_ROOT_STR]
	sys.modules["gamecenter"] = gamecenter_module


from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4, Vec3, ClockObject, WindowProperties, CardMaker, NodePath, Texture, PNMImage
from direct.task import Task
from direct.actor.Actor import Actor

from gamecenter.streetBattle.player import Player
from gamecenter.streetBattle.combat import CombatSystem
from gamecenter.streetBattle.net import NetPeer
from gamecenter.streetBattle.ai import SimpleAI
from gamecenter.streetBattle.vfx import VFX
from gamecenter.streetBattle.enhanced_audio_system import AudioSystem
from gamecenter.streetBattle.ui import HUD
from gamecenter.streetBattle.enhanced_character_manager import EnhancedCharacterManager as CharacterManager
from gamecenter.streetBattle.game_state import GameStateManager, GameState
from gamecenter.streetBattle.kof_animation_system import KOFAnimationSystem
from gamecenter.streetBattle.game_mode_selector import GameModeSelector
from gamecenter.streetBattle.character_selector import CharacterSelector
from gamecenter.streetBattle.character_animator import CharacterAnimator
from gamecenter.streetBattle.special_moves import SpecialMovesSystem, enhance_player_with_special_moves
from gamecenter.streetBattle.config import SettingsManager
from gamecenter.streetBattle.sprite_system import SpriteSystem
from gamecenter.streetBattle.enhanced_3d_animation_system import Animation3DManager, AnimationState
from gamecenter.streetBattle.performance_optimizer import SmartLoadingSystem
from gamecenter.streetBattle.smart_console import setup_optimized_console, console_info, console_error, console_debug, console_warning


def safe_node_check(node_path, operation_name="NodePath operation"):
    """安全地检查NodePath的有效性，避免isEmpty()断言错误"""
    if not node_path:
        print(f"[DEBUG] {operation_name}: NodePath is None")
        return False
    
    try:
        # 首先尝试获取节点
        if not node_path.getNode():
            print(f"[DEBUG] {operation_name}: NodePath has no node")
            return False
        
        # 然后安全地检查是否为空
        if node_path.isEmpty():
            print(f"[DEBUG] {operation_name}: NodePath is empty")
            return False
        
        return True
    except Exception as check_error:
        print(f"[DEBUG] {operation_name}: NodePath check failed - {check_error}")
        return False

class StreetBattleGame(ShowBase):
	def __init__(self, settings_manager: SettingsManager | None = None):
		# 🚀 初始化优化控制台输出系统
		self.console = setup_optimized_console(quiet_mode=True)  # 启用安静模式，减少输出
		console_info("启动Street Battle引擎", "startup")
		
		self.settings_manager = settings_manager or SettingsManager()
		graphics_settings = self.settings_manager.get("graphics", {}) or {}
		resolution = graphics_settings.get("resolution", [1024, 768])
		if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
			resolution = [1024, 768]
		fullscreen = bool(graphics_settings.get("fullscreen", False))
		vsync_enabled = bool(graphics_settings.get("vsync", True))

		super().__init__()
		self.disableMouse()
		self.window_title = "StreetBattle - Fighting Game"
		try:
			props = WindowProperties()
			props.setSize(int(resolution[0]), int(resolution[1]))
			props.setFullscreen(fullscreen)
			props.setTitle(self.window_title)
			# Avoid forcing the window to the foreground to prevent SetForegroundWindow warnings
			try:
				props.setForeground(False)
			except Exception:
				pass
			self.win.requestProperties(props)
			if not vsync_enabled:
				try:
					self.win.setSwapInterval(0)
				except Exception:
					pass
		except Exception:
			pass
		
		# 🚀 初始化智能加载系统
		self.smart_loader = SmartLoadingSystem(self)
		
		# 🎭 初始化3D动画管理器
		self.animation_3d_manager = Animation3DManager()
		
		# Game state management
		self.current_game_mode = None
		self.selected_character = None
		self.selected_opponent = None
		self.game_initialized = False
		self.help_overlay = None
		
		# Initialize character management system
		from gamecenter.streetBattle.enhanced_character_manager import EnhancedCharacterManager as FixedEnhancedCharacterManager
		self.char_manager = FixedEnhancedCharacterManager(self)
		
		# Initialize 2.5D sprite system
		self.sprite_system = SpriteSystem(self)
		
		# Display professional system information
		total_chars = len(self.char_manager.comprehensive_characters)
		console_info(f"角色数据库: {total_chars} 名战士已加载", "startup")
		console_info("游戏模式: 冒险 • 对战 • 网络", "startup") 
		console_info("增强图形: KOF动画系统激活", "startup")
		console_info("音频系统: 高级音效就绪", "startup")
		
		# UI systems
		self.mode_selector = GameModeSelector(self)
		self.character_selector = CharacterSelector(self, self.char_manager)
		self.stage_backdrop = None
		
		# 🚀 启动优化加载流程
		self.smart_loader.start_optimized_loading()
		
		# Show mode selection immediately
		self.mode_selector.show(callback=self._on_game_mode_selected)
		
		# Basic input handling for menus
		self.accept('escape', self._handle_escape)
	
	def _handle_escape(self):
		"""Handle escape key - return to previous menu or exit"""
		if hasattr(self, 'help_overlay') and self.help_overlay:
			self._hide_help()
		elif self.game_initialized:
			# Return to character selection
			self._return_to_character_selection()
		else:
			selector_visible = bool(getattr(self.character_selector, 'visible', False))
			mode_visible = bool(getattr(self.mode_selector, 'visible', False))
			if selector_visible:
				self._return_to_mode_selection()
			elif mode_visible:
				# Clean up and exit game from top-level menu
				self._cleanup_and_exit()
			else:
				# Default back to mode selector
				self._return_to_mode_selection()
	
	def _cleanup_and_exit(self):
		"""Clean up resources and exit game"""
		try:
			print("Starting game cleanup...")
			
			# Clean up audio system first (prevent AL lib warnings)
			if hasattr(self, 'audio') and self.audio:
				print("Cleaning up audio system...")
				self.audio.cleanup()
			
			# Clean up VFX system
			if hasattr(self, 'vfx') and self.vfx:
				try:
					print("Cleaning up VFX system...")
					self.vfx.cleanup()
				except Exception as e:
					print(f"VFX cleanup warning: {e}")
			
			# Clean up KOF animation system
			if hasattr(self, 'kof_animator') and self.kof_animator:
				try:
					print("Cleaning up KOF animation system...")
					self.kof_animator.cleanup()
				except Exception as e:
					print(f"KOF animator cleanup warning: {e}")
			
			# Clean up character models to release resources
			if hasattr(self, 'char_manager') and self.char_manager:
				try:
					print("Cleaning up character models...")
					for character_name, model in self.char_manager.character_models.items():
						if model:
							try:
								model.removeNode()
							except:
								pass
					self.char_manager.character_models.clear()
					print("Character models cleaned up")
				except Exception as e:
					print(f"Character cleanup warning: {e}")
			
			# Force Panda3D audio manager cleanup
			try:
				import panda3d.core as p3d
				audio_manager = p3d.AudioManager.createAudioManager()
				if audio_manager:
					audio_manager.shutdown()
					print("Panda3D audio manager shutdown")
			except Exception as e:
				print(f"Audio manager shutdown warning: {e}")
			
			print("Game cleanup completed successfully")
		except Exception as e:
			print(f"Cleanup error: {e}")
		finally:
			# Give the system a moment to complete cleanup
			import time
			time.sleep(0.1)
			sys.exit()
	
	def _return_to_mode_selection(self):
		"""Return to game mode selection"""
		if hasattr(self, 'character_selector'):
			self.character_selector.hide()
		if hasattr(self, 'mode_selector'):
			self.mode_selector.show(callback=self._on_game_mode_selected)
	
	def _return_to_character_selection(self):
		"""Return to character selection"""
		# Clean up game
		for task_name in [
			'update-task',
			'light-anim',
			'start-first-round',
			'end-game-action',
			'hud-flash',
			'show-fight-text',
			'hide-fight-text',
			'victory-flash'
		]:
			try:
				self.taskMgr.remove(task_name)
			except Exception:
				pass
		
		if hasattr(self, 'players'):
			for player in self.players:
				try:
					node = getattr(player, 'node', None)
					if node:
						node.removeNode()
				except Exception:
					pass
			self.players = []

		if hasattr(self, 'combat'):
			self.combat = None
		if hasattr(self, 'special_moves'):
			self.special_moves = None

		for light_attr in ('ambientNP', 'directionalNP'):
			node = getattr(self, light_attr, None)
			if node:
				try:
					self.render.clearLight(node)
				except Exception:
					pass
				try:
					node.removeNode()
				except Exception:
					pass
			setattr(self, light_attr, None)

		for node_attr in ('ground', 'stage_backdrop'):
			node = getattr(self, node_attr, None)
			if node:
				try:
					node.removeNode()
				except Exception:
					pass
			setattr(self, node_attr, None)

		if hasattr(self, 'vfx'):
			try:
				root = getattr(self.vfx, 'particles_root', None)
				if root:
					root.removeNode()
			except Exception:
				pass
			self.vfx = None

		if hasattr(self, 'audio') and self.audio:
			try:
				self.audio.cleanup()
			except Exception:
				pass
			self.audio = None

		if hasattr(self, 'hud') and self.hud:
			try:
				self.hud.ui_root.hide()
			except Exception:
				pass
			self.hud = None

		if hasattr(self, 'netpeer') and self.netpeer:
			try:
				self.netpeer.stop()
			except Exception:
				pass
			self.netpeer = None

		self.game_initialized = False
		self.selected_character = None
		self.selected_opponent = None
		
		# Show character selection again
		if self.current_game_mode == 'adventure':
			self.character_selector.show(callback=self._on_character_selected, mode='single')
		elif self.current_game_mode == 'versus':
			self.character_selector.show(callback=self._on_character_selected, mode='single')
		elif self.current_game_mode == 'network':
			self.character_selector.show(callback=self._on_character_selected, mode='single')
	
	def _on_game_mode_selected(self, mode):
		"""Handle game mode selection and proceed to character selection"""
		self.current_game_mode = mode
		self.mode_selector.hide()
		
		print(f"Selected game mode: {mode}")
		
		# Show character selection
		if mode == 'adventure':
			self.character_selector.show(callback=self._on_character_selected, mode='single')
		elif mode == 'versus':
			self.character_selector.show(callback=self._on_character_selected, mode='single')
		elif mode == 'network':
			self.character_selector.show(callback=self._on_character_selected, mode='single')
	
	def _on_character_selected(self, character_name):
		"""Handle character selection and initialize game"""
		# 检查是否取消选择
		if character_name is None:
			print("Character selection cancelled")
			self._return_to_mode_selection()
			return
		
		self.selected_character = character_name
		self.character_selector.hide()
		
		print(f"Selected character: {character_name}")
		
		# Handle different game modes
		if self.current_game_mode == 'adventure':
			self._initialize_adventure_mode()
		elif self.current_game_mode == 'versus':
			self._initialize_versus_mode()
		elif self.current_game_mode == 'network':
			self._initialize_network_mode()
	
	def _initialize_adventure_mode(self):
		"""Initialize adventure (story) mode"""
		print("Initializing Adventure Mode...")
		# For now, start with first opponent
		self.selected_opponent = "Iori Yagami"  # Will be dynamic later
		self.current_level = 1
		self._initialize_game()
	
	def _initialize_versus_mode(self):
		"""Initialize versus mode with random opponent"""
		print("Initializing Versus Mode...")
		# Random opponent selection with animation
		self.selected_opponent = self.char_manager.get_random_character()
		while self.selected_opponent == self.selected_character:
			self.selected_opponent = self.char_manager.get_random_character()
		
		print(f"Random opponent selected: {self.selected_opponent}")
		self._initialize_game()
	
	def _initialize_network_mode(self):
		"""Initialize network mode"""
		print("Initializing Network Mode...")
		# For now, use AI opponent until network is connected
		self.selected_opponent = "Kyo Kusanagi"
		self._initialize_game()
	
	def _initialize_game(self):
		"""Initialize the game scene and systems"""
		if self.game_initialized:
			return
		
		# 🧹 在游戏初始化前先清理旧模型，防止重复创建
		print("🧹 游戏初始化前清理重复的3D模型...")
		try:
			# 清除缓存的角色模型
			self.char_manager.clear_character_models()
			# 清理场景中的重复模型
			self.char_manager.cleanup_scene_duplicates(self.render)
		except Exception as e:
			print(f"⚠️  模型清理失败: {e}")
		
		# Camera
		self.camera.setPos(0, -20, 6)
		self.camera.lookAt(0, 0, 2)
		
		# Lights: add dynamic color cycling for realism
		ambient = AmbientLight('ambient')
		ambient.setColor(Vec4(0.3, 0.3, 0.35, 1))
		self.ambientNP = self.render.attachNewNode(ambient)
		self.render.setLight(self.ambientNP)

		self.directional = DirectionalLight('directional')
		self.directional.setColor(Vec4(0.9, 0.85, 0.8, 1))
		self.directional.setShadowCaster(True, 1024, 1024)
		self.directionalNP = self.render.attachNewNode(self.directional)
		self.directionalNP.setHpr(-30, -60, 0)
		self.render.setLight(self.directionalNP)

		# Add a task to animate light color for dynamic effect
		def _light_anim(task):
			import math
			t = self.clock.getFrameTime()
			c = 0.7 + 0.3 * math.sin(t * 0.7)
			self.directional.setColor(Vec4(0.7 + 0.2 * math.sin(t), 0.7 + 0.2 * math.cos(t*0.8), c, 1))
			return Task.cont
		self.taskMgr.add(_light_anim, 'light-anim')

		# Ground: build Panda3D-textured arena purely from local assets
		try:
			self._build_textured_arena()
		except Exception:
			self._create_procedural_ground()
		self._finalize_scene_setup()

	def _build_textured_arena(self):
		"""Construct a lightweight arena using Panda3D default textures only."""
		if getattr(self, 'ground', None):
			if safe_node_check(self.ground, "Ground node removal"):
				try:
					self.ground.removeNode()
				except Exception as remove_error:
					print(f"[DEBUG] Ground removal failed: {remove_error}")
			self.ground = None
		arena_root = NodePath('arena_root')

		# Floor
		floor_maker = CardMaker('arena_floor')
		floor_maker.setFrame(-14, 14, -8, 8)
		floor_np = arena_root.attachNewNode(floor_maker.generate())
		floor_np.setP(-90)
		floor_np.setTwoSided(True)
		floor_tex = self.loader.loadTexture('assets/textures/arena_floor.png')
		if floor_tex:
			floor_tex.setAnisotropicDegree(2)
			floor_np.setTexture(floor_tex)
		else:
			floor_np.setColor(0.18, 0.18, 0.2, 1)

		# Center ring
		ring_maker = CardMaker('arena_ring')
		ring_maker.setFrame(-6, 6, -6, 6)
		ring_np = arena_root.attachNewNode(ring_maker.generate())
		ring_np.setP(-90)
		ring_np.setPos(0, 0, 0.02)
		ring_np.setTwoSided(True)
		ring_tex = self.loader.loadTexture('assets/textures/arena_ring.png')
		if ring_tex:
			ring_tex.setAnisotropicDegree(2)
			ring_np.setTexture(ring_tex)
		else:
			ring_np.setColor(0.35, 0.25, 0.22, 1)

		# Lighting reference pillars
		pillar_maker = CardMaker('arena_pillar')
		pillar_maker.setFrame(-0.6, 0.6, 0, 5)
		pillar_tex = self.loader.loadTexture('assets/textures/arena_pillar.png')
		for pos in [(-10, -6, 0), (-10, 6, 0), (10, -6, 0), (10, 6, 0)]:
			pillar_np = arena_root.attachNewNode(pillar_maker.generate())
			pillar_np.setPos(*pos)
			pillar_np.setTwoSided(True)
			if pillar_tex:
				pillar_np.setTexture(pillar_tex)
			else:
				pillar_np.setColor(0.5, 0.45, 0.4, 1)

		arena_root.flattenStrong()
		arena_root.reparentTo(self.render)
		arena_root.setPos(0, 0, 0)
		self.ground = arena_root
		self._build_stage_backdrop()
		print("Built local textured arena")

	def _create_procedural_ground(self):
		"""Fallback: create flat-colored arena geometry."""
		cm = CardMaker('fallback_ground')
		cm.setFrame(-14, 14, -8, 8)
		card = self.render.attachNewNode(cm.generate())
		card.setP(-90)
		card.setTwoSided(True)
		card.setColor(0.15, 0.15, 0.16, 1)
		self.ground = card
		print("Created fallback procedural arena surface")
		self._build_stage_backdrop()

	def _build_stage_backdrop(self):
		"""Create a non-blocking scenic backdrop behind the arena."""
		if getattr(self, 'stage_backdrop', None):
			if safe_node_check(self.stage_backdrop, "Stage backdrop removal"):
				try:
					self.stage_backdrop.removeNode()
				except Exception as backdrop_error:
					print(f"[DEBUG] Stage backdrop removal failed: {backdrop_error}")

			self.stage_backdrop = None

		backdrop_root = NodePath('stage_backdrop')
		backdrop_root.reparentTo(self.render)
		backdrop_root.setPos(0, 18, 5.5)
		backdrop_root.setScale(1, 1, 1)

		cm = CardMaker('stage_background_card')
		cm.setFrame(-16, 16, -9, 9)
		card_np = backdrop_root.attachNewNode(cm.generate())
		card_np.setTwoSided(True)
		card_np.setDepthWrite(False)
		card_np.setDepthTest(False)
		card_np.setBin('background', 0)
		card_np.setColor(0.05, 0.08, 0.15, 1)

		tex = self._generate_backdrop_texture()
		if tex:
			card_np.setTexture(tex)

		# Add a subtle floor horizon strip for depth
		floor_cm = CardMaker('stage_horizon')
		floor_cm.setFrame(-16, 16, -2.5, -1.5)
		floor_np = backdrop_root.attachNewNode(floor_cm.generate())
		floor_np.setTwoSided(True)
		floor_np.setDepthWrite(False)
		floor_np.setDepthTest(False)
		floor_np.setBin('background', 1)
		floor_np.setColor(0.15, 0.12, 0.2, 1)

		self.stage_backdrop = backdrop_root

	def _generate_backdrop_texture(self):
		"""Procedurally create a gradient backdrop texture."""
		try:
			styles = [
				{'top': (0.04, 0.07, 0.18), 'mid': (0.18, 0.25, 0.45), 'bottom': (0.45, 0.35, 0.25), 'glow': (0.9, 0.75, 0.45)},
				{'top': (0.03, 0.05, 0.12), 'mid': (0.16, 0.26, 0.46), 'bottom': (0.32, 0.18, 0.3), 'glow': (0.78, 0.55, 0.8)},
				{'top': (0.02, 0.04, 0.1), 'mid': (0.12, 0.25, 0.4), 'bottom': (0.25, 0.36, 0.42), 'glow': (0.65, 0.85, 0.95)}
			]
			style = random.choice(styles)

			width, height = 512, 512
			img = PNMImage(width, height)

			def blend(a, b, t):
				return tuple(max(0.0, min(1.0, a_i * (1 - t) + b_i * t)) for a_i, b_i in zip(a, b))

			for y in range(height):
				t = y / float(height - 1)
				if t < 0.45:
					color = blend(style['top'], style['mid'], t / 0.45)
				else:
					color = blend(style['mid'], style['bottom'], (t - 0.45) / 0.55)
				for x in range(width):
					wave = 0.02 * math.sin((x / width) * math.pi * 4)
					img.setXel(x, y,
						max(0.0, min(1.0, color[0] + wave)),
						max(0.0, min(1.0, color[1] + wave)),
						max(0.0, min(1.0, color[2] + wave)))

			# Add glowing skyline strips near horizon
			horizon_y = int(height * 0.62)
			for x in range(width):
				glow_strength = 0.6 + 0.4 * math.sin((x / width) * math.pi * 3)
				for dy in range(6):
					y = min(height - 1, horizon_y + dy)
					current = tuple(img.getXel(x, y)[i] for i in range(3))
					blended = blend(current, style['glow'], glow_strength * (1 - dy / 6.0) * 0.4)
					img.setXel(x, y, *blended)

			tex = Texture()
			tex.load(img)
			tex.setMagfilter(Texture.FTLinear)
			tex.setMinfilter(Texture.FTLinearMipmapLinear)
			return tex
		except Exception as exc:
			print(f"Backdrop generation failed: {exc}")
			return None

	def _finalize_scene_setup(self):
		"""Finish initializing gameplay systems once the arena exists."""
		# Get preferred rendering mode from settings
		preferred_mode = self.settings_manager.get("preferred_version", "3d")
		print(f"🎮 Initializing in {preferred_mode.upper()} mode")
		
		# Gameplay systems
		self.mode = 'local'  # Will be updated based on game mode
		self.netpeer = None
		self.remote_addr = None
		self.vfx = VFX(self)
		self.audio = AudioSystem(self)
		self.hud = HUD(self)
		
		# Animation systems
		self.animator = CharacterAnimator(self)
		self.kof_animator = KOFAnimationSystem(self)
		
		# Game state management
		self.game_state = GameStateManager(self)
		self.game_state.on_state_change = self._on_state_change
		self.game_state.on_round_start = self._on_round_start
		self.game_state.on_round_end = self._on_round_end
		self.game_state.on_game_end = self._on_game_end

		# Create players based on preferred mode
		self.players = []
		self.sprite_characters = []
		
		print(f"\\n🎭 LOADING {preferred_mode.upper()} BATTLE CHARACTERS")
		print(f"   Player 1: {self.selected_character}")
		print(f"   Player 2: {self.selected_opponent}")
		print(f"   Mode: {self.current_game_mode.title()}")
		
		if preferred_mode == "2.5d":
			self._initialize_2_5d_mode()
		else:
			self._initialize_3d_mode()

		# Initialize special moves system
		self.special_moves = SpecialMovesSystem(self)
		
		# Enhance players with special moves
		for i, player in enumerate(self.players):
			enhance_player_with_special_moves(player, self.special_moves)
			# bind player id to character for per-character move detection
			try:
				char_name = getattr(player, 'character_name', None)
				self.special_moves.register_player_with_character(id(player), char_name)
			except Exception:
				pass
			print(f"Player {i+1} enhanced with special moves system")

		self.combat = CombatSystem(self.players)

		# Movement state
		self.key_map = {'left': False, 'right': False, 'up': False, 'down': False, 'light': False, 'heavy': False, 'jump': False}
		# global clock
		self.clock = ClockObject.getGlobalClock()
		
		# Movement keys
		self.accept('a', self.set_key, ['left', True])
		self.accept('a-up', self.set_key, ['left', False])
		self.accept('d', self.set_key, ['right', True])
		self.accept('d-up', self.set_key, ['right', False])
		self.accept('w', self.set_key, ['up', True])
		self.accept('w-up', self.set_key, ['up', False])
		self.accept('s', self.set_key, ['down', True])
		self.accept('s-up', self.set_key, ['down', False])
		
		# Attack keys
		self.accept('space', self.set_key, ['light', True])
		self.accept('space-up', self.set_key, ['light', False])
		self.accept('mouse1', self.set_key, ['light', True])
		self.accept('mouse1-up', self.set_key, ['light', False])
		self.accept('mouse3', self.set_key, ['heavy', True])
		self.accept('mouse3-up', self.set_key, ['heavy', False])
		
		# Jump key
		self.accept('j', self.set_key, ['jump', True])
		self.accept('j-up', self.set_key, ['jump', False])
		
		# Help key
		self.accept('h', self.show_help)

		self.frame = 0
		# simple input buffer for host: map addr -> list of (frame, inputs)
		self._client_input_buffer = {}
		# host authoritative state history: frame -> snapshot
		# only used when mode == 'host'
		self._state_history = {}
		# local input history for client-side prediction and reconciliation: frame -> inputs
		self._local_input_history = {}
		self.update_task = self.taskMgr.add(self.update, 'update-task')
		
		# Setup AI for opponent based on game mode
		if self.current_game_mode in ['adventure', 'versus']:
			self.ai = SimpleAI(difficulty=1)
		
		# Start the first round after a brief delay for initialization
		self.taskMgr.doMethodLater(1.0, self._start_first_round, 'start-first-round')

		# Load enhanced audio assets (non-fatal)
		try:
			audio_candidates = [
				Path('assets/audio/bgm_loop.ogg'),
				Path('assets/audio/bgm_loop.wav'),
			]
			bgm_loaded = False
			bgm_track_name = None
			for bgm_path in audio_candidates:
				if bgm_path.exists():
					# 使用文件名作为track名称
					bgm_track_name = bgm_path.stem  # 获取不含扩展名的文件名
					self.audio.load_bgm(str(bgm_path), name=bgm_track_name)
					bgm_loaded = True
					print(f"Loaded background music: {bgm_path}")
					break
			if not bgm_loaded:
				print("No background music available")

			hit_candidates = [
				Path('assets/audio/hit_generated.wav'),
				Path('assets/audio/hit.wav'),
			]
			for hit_path in hit_candidates:
				if hit_path.exists():
					self.audio.load_sfx(str(hit_path), name='hit')
					print(f"Loaded hit sound: {hit_path}")
					break
			else:
				print("No hit sound available")

			combo_candidates = [
				Path('assets/audio/combo_generated.wav'),
				Path('assets/audio/combo_enhanced.wav'),
				Path('assets/audio/combo.wav'),
			]
			for combo_path in combo_candidates:
				if combo_path.exists():
					self.audio.load_sfx(str(combo_path), name='combo')
					print(f"Loaded combo sound: {combo_path}")
					break
			else:
				print("No combo sound available")

			# play bgm in local mode
			if self.mode == 'local' and bgm_loaded and bgm_track_name:
				self.audio.play_bgm(bgm_track_name, loop=True)
		except Exception as e:
			print(f"Audio loading failed: {e}")
		
		self.game_initialized = True
		print(f"✅ {preferred_mode.upper()} Game mode initialized successfully!")
	
	def _initialize_2_5d_mode(self):
		"""Initialize 2.5D sprite-based rendering mode"""
		print("   Initializing 2.5D sprite characters...")
		
		# Create sprite characters
		try:
			# Player 1 sprite
			char_id_p0 = self.selected_character.lower().replace(' ', '_')
			sprite_p0 = self.sprite_system.create_sprite_character(
				char_id_p0, self.selected_character, Vec3(-3, 0, 0)
			)
			
			if sprite_p0:
				print(f"Player 1 sprite created: {self.selected_character}")
				self.sprite_characters.append(sprite_p0)
			else:
				print(f"Failed to create sprite for {self.selected_character}")
				
		except Exception as e:
			print(f"Failed to create player 1 sprite: {e}")
		
		try:
			# Player 2 sprite
			char_id_p1 = self.selected_opponent.lower().replace(' ', '_')
			sprite_p1 = self.sprite_system.create_sprite_character(
				char_id_p1, self.selected_opponent, Vec3(3, 0, 0)
			)
			
			if sprite_p1:
				print(f"Player 2 sprite created: {self.selected_opponent}")
				# Make opponent face left
				sprite_p1.set_facing(False)
				self.sprite_characters.append(sprite_p1)
			else:
				print(f"Failed to create sprite for {self.selected_opponent}")
				
		except Exception as e:
			print(f"Failed to create player 2 sprite: {e}")
		
		# Create basic Player objects for game logic (without 3D models)
		try:
			p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
			p0.character_name = self.selected_character
			p0.character_id = char_id_p0
			p0.sprite_character = sprite_p0 if len(self.sprite_characters) > 0 else None
			p0.render_mode = "2.5d"
			p0.character_data = self.char_manager.get_character_by_name(self.selected_character)
			self.players.append(p0)
			print(f"Player 1 logic created: {self.selected_character}")
		except Exception as e:
			print(f"Failed to create player 1 logic: {e}")
		
		try:
			p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
			p1.character_name = self.selected_opponent
			p1.character_id = char_id_p1
			p1.sprite_character = sprite_p1 if len(self.sprite_characters) > 1 else None
			p1.render_mode = "2.5d"
			p1.character_data = self.char_manager.get_character_by_name(self.selected_opponent)
			self.players.append(p1)
			print(f"Player 2 logic created: {self.selected_opponent}")
		except Exception as e:
			print(f"Failed to create player 2 logic: {e}")
			
		print(f"🎮 2.5D Mode: {len(self.players)} players, {len(self.sprite_characters)} sprites")
		
		# Register players for sprite animation system only
		try:
			for i, player in enumerate(self.players):
				# Only register with 2.5D systems
				if hasattr(player, 'sprite_character') and player.sprite_character:
					print(f"Registered Player {i+1} for 2.5D sprite animations")
		except Exception as e:
			print(f"2.5D animation registration failed: {e}")
	
	def _initialize_3d_mode(self):
		"""Initialize 3D model-based rendering mode"""
		print("   Initializing 3D model characters...")
		
		# 确保有默认角色
		if not self.selected_character:
			self.selected_character = "Kyo Kusanagi"
			print(f"⚠️  No character selected, using default: {self.selected_character}")
			
		if not self.selected_opponent:
			self.selected_opponent = "Iori Yagami"
			print(f"⚠️  No opponent selected, using default: {self.selected_opponent}")
		
		# 🧹 在创建新模型前先清理旧模型，避免重复
		print("🧹 清理旧的3D模型...")
		try:
			self.char_manager.clear_character_models()
			self.char_manager.cleanup_scene_duplicates(self.render)
		except Exception as e:
			print(f"⚠️  模型清理失败: {e}")
		
		# Create 3D characters using character manager
		try:
			# Player 1 - 3D model only
			char_id_p0 = self.selected_character.lower().replace(' ', '_')
			print(f"\\n🎮 正在创建Player 1: {self.selected_character}")
			model_p0 = self.char_manager.create_character_model(
				self.selected_character, Vec3(-3, 0, 0)
			)
			
			if model_p0:
				# Create Player object with 3D model
				try:
					p0 = Player(self.render, self.loader, name=self.selected_character, 
							   actor_instance=model_p0, pos=Vec3(-3, 0, 0))
					p0.character_name = self.selected_character
					p0.character_id = char_id_p0
					p0.render_mode = "3d"
					p0.model_3d = model_p0
					
					# 添加角色数据用于UI显示
					p0.character_data = self.char_manager.get_character_by_name(self.selected_character)
					
					# 🔧 确保Player 1模型可见性
					self._ensure_player_visibility(p0, model_p0, "Player 1")
					
					self.players.append(p0)
					print(f"✅ Player 1 3D model created: {self.selected_character}")
				except Exception as e:
					print(f"❌ Failed to create Player 1 with 3D model: {e}")
					# Fallback to basic player without 3D model
					p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
					p0.character_name = self.selected_character
					p0.character_id = char_id_p0
					p0.render_mode = "fallback"
					p0.character_data = self.char_manager.get_character_by_name(self.selected_character)
					self.players.append(p0)
					print(f"✅ Player 1 fallback created: {self.selected_character}")
			else:
				print(f"⚠️  Player 1 3D model creation failed: {self.selected_character}")
				# 创建一个基础的Player对象作为fallback
				p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
				p0.character_name = self.selected_character
				p0.character_id = char_id_p0
				p0.render_mode = "fallback"
				p0.character_data = self.char_manager.get_character_by_name(self.selected_character)
				self.players.append(p0)
				print(f"✅ Player 1 fallback created: {self.selected_character}")
				
		except Exception as e:
			print(f"❌ Failed to create player 1 3D model: {e}")
			# 作为最后的fallback - 确保至少有一个Player对象
			try:
				p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
				p0.character_name = self.selected_character
				p0.character_id = self.selected_character.lower().replace(' ', '_')
				p0.render_mode = "emergency"
				p0.character_data = self.char_manager.get_character_by_name(self.selected_character)
				self.players.append(p0)
				print(f"✅ Player 1 emergency fallback created")
			except Exception as fallback_e:
				print(f"❌ Complete failure creating player 1: {fallback_e}")
				# 创建最基础的Player对象，不能让players列表为空
				p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
				p0.character_data = {}  # 空数据避免UI错误
				self.players.append(p0)
		
		try:
			# Player 2 - 3D model with same enhancements as Player 1  
			char_id_p1 = self.selected_opponent.lower().replace(' ', '_')
			print(f"\\n🎮 正在创建Player 2: {self.selected_opponent}")
			model_p1 = self.char_manager.create_character_model(
				self.selected_opponent, Vec3(3, 0, 0)
			)
			
			if model_p1:
				# Create Player object with 3D model using same logic as Player 1
				try:
					p1 = Player(self.render, self.loader, name=self.selected_opponent,
							   actor_instance=model_p1, pos=Vec3(3, 0, 0))
					p1.character_name = self.selected_opponent
					p1.character_id = char_id_p1
					p1.render_mode = "3d"
					p1.model_3d = model_p1
					
					# 添加角色数据用于UI显示
					p1.character_data = self.char_manager.get_character_by_name(self.selected_opponent)
					
					# 🔧 确保Player 2模型可见性 - 与Player 1使用相同的处理
					self._ensure_player_visibility(p1, model_p1, "Player 2")
					
					self.players.append(p1)
					print(f"✅ Player 2 3D model created: {self.selected_opponent}")
				except Exception as e:
					print(f"❌ Failed to create Player 2 with 3D model: {e}")
					# Fallback to basic player without 3D model
					p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
					p1.character_name = self.selected_opponent
					p1.character_id = char_id_p1
					p1.render_mode = "fallback"
					p1.character_data = self.char_manager.get_character_by_name(self.selected_opponent)
					self.players.append(p1)
					print(f"✅ Player 2 fallback created: {self.selected_opponent}")
			else:
				print(f"⚠️  Player 2 3D model creation failed: {self.selected_opponent}")
				# 创建一个基础的Player对象作为fallback
				p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
				p1.character_name = self.selected_opponent
				p1.character_id = char_id_p1
				p1.render_mode = "fallback"
				p1.character_data = self.char_manager.get_character_by_name(self.selected_opponent)
				self.players.append(p1)
				print(f"✅ Player 2 fallback created: {self.selected_opponent}")
				
		except Exception as e:
			print(f"❌ Failed to create player 2 3D model: {e}")
			# 作为最后的fallback - 确保至少有两个Player对象
			try:
				p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
				p1.character_name = self.selected_opponent
				p1.character_id = self.selected_opponent.lower().replace(' ', '_')
				p1.render_mode = "emergency"
				p1.character_data = self.char_manager.get_character_by_name(self.selected_opponent)
				self.players.append(p1)
				print(f"✅ Player 2 emergency fallback created")
			except Exception as fallback_e:
				print(f"❌ Complete failure creating player 2: {fallback_e}")
				# 创建最基础的Player对象，不能让players列表只有一个
				p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
				p1.character_data = {}  # 空数据避免UI错误
				self.players.append(p1)
			
		print(f"🎮 3D Mode: {len(self.players)} players with 3D models")
		
		# Register players for 3D animation systems only
		try:
			for i, player in enumerate(self.players):
				char_name = player.character_name
				char_id = player.character_id
				
				if hasattr(player, 'model_3d') and player.model_3d:
					# 🎭 注册到新的3D动画管理器
					state_machine = self.animation_3d_manager.register_character(
						f"player_{i}", player.model_3d, char_name
					)
					if state_machine:
						# 为玩家保存状态机引用，方便控制
						player.animation_state_machine = state_machine
						console_info(f"Player {i+1} 3D动画状态机注册成功: {char_name}", "animation")
					
					# Extract body parts for original animator (保持兼容性)
					if hasattr(self, 'animator') and self.animator:
						body_parts = self._extract_body_parts(player)
						self.animator.register_character(f"player_{i}", player.model_3d, body_parts)
					
					# Register with KOF animation system (保持兼容性)
					if hasattr(self, 'kof_animator') and self.kof_animator:
						actor_instance = player.model_3d if isinstance(player.model_3d, Actor) else None
						self.kof_animator.register_character(char_id, player.model_3d, actor_instance)
					
					console_info(f"Player {i+1} 完整3D动画系统注册: {char_name}", "animation")
				else:
					console_warning(f"Player {i+1} 没有3D模型，跳过动画注册", "animation")
		except Exception as e:
			console_error(f"3D动画注册失败: {e}", "animation")
	
	def _ensure_player_visibility(self, player: Player, model: Actor, player_name: str):
		"""确保玩家模型可见性 - 统一的处理逻辑"""
		try:
			# 强制设置不透明度和可见性
			model.setTransparency(False)  # 禁用透明度
			model.clearColor()  # 清除任何颜色覆盖
			model.setColorScale(1.0, 1.0, 1.0, 1.0)  # 完全不透明的白色
			
			# 确保模型在正确的渲染队列中
			model.setBin('opaque', 0)  # 设置为不透明渲染队列
			model.setDepthTest(True)  # 启用深度测试
			model.setDepthWrite(True)  # 启用深度写入
			
			# 确保双面渲染
			model.setTwoSided(True)
			
			# 检查并应用材质
			if hasattr(self.char_manager, '_ensure_model_visibility'):
				char_data = self.char_manager.get_character_by_name(player.character_name)
				if char_data:
					self.char_manager._ensure_model_visibility(model, char_data)
			
			# 确保缩放正确
			current_scale = model.getScale()
			if abs(current_scale.x - 1.0) > 0.9:  # 如果缩放太小或接近默认
				# 重新应用智能缩放
				bounds = model.getTightBounds()
				if bounds:
					min_p, max_p = bounds
					size = max_p - min_p
					max_dim = max(size.x, size.y, size.z)
					if max_dim > 2.5:  # 需要缩放
						auto_scale = 2.0 / max_dim
						model.setScale(auto_scale)
						print(f"🔧 {player_name}重新应用缩放: {auto_scale:.3f}")
			
			print(f"✅ {player_name}可见性确保完成")
			
		except Exception as e:
			print(f"❌ {player_name}可见性设置失败: {e}")

	def start_network(self, mode='local', host_ip=None, port=12000):
		self.mode = mode
		if mode == 'host':
			self.netpeer = NetPeer(bind_port=port)
			def on_msg(msg, addr):
				# msg expected: {'type':'input','inputs':{...}}
				if not msg:
					return
				if msg.get('type') == 'input':
					# buffer client inputs by frame to avoid out-of-order application
					frm = msg.get('frame', None)
					inputs = msg.get('inputs', {})
					buf = self._client_input_buffer.setdefault(addr, [])
					buf.append((frm, inputs))
			self.netpeer.on_message = on_msg
			self.netpeer.start()
		elif mode == 'client' and host_ip:
			self.netpeer = NetPeer(bind_port=port)
			self.remote_addr = (host_ip, port)
			def client_on_msg(msg, addr):
				if not msg:
					return
				if msg.get('type') == 'state':
					# host broadcasts authoritative state: map host p0->opponent, p1->local
					p0 = msg.get('p0', {})
					p1 = msg.get('p1', {})
					# update opponent (players[1]) from host's p0
					if p0:
						pos = p0.get('pos')
						if pos:
							self.players[1].set_target_pos(pos)
							health = p0.get('health')
							if health is not None:
								self.players[1].health = health
							state = p0.get('state')
							if state:
								self.players[1].state = state
					# update local representation from host's p1
					if p1:
						pos = p1.get('pos')
						if pos:
							self.players[0].set_target_pos(pos)
						health = p1.get('health')
						if health is not None:
							self.players[0].health = health
						state = p1.get('state')
						if state:
							self.players[0].state = state
							# refined reconciliation: use fixed timestep deterministic replay from host frame
							try:
								if pos:
									recv_frame = msg.get('frame', None)
									if recv_frame is not None:
										host_pos = Vec3(*pos)
										local_pos = self.players[0].pos
										# threshold correction
										if (host_pos - local_pos).length() > 0.6:
											# apply authoritative snapshot for local player
											self.players[0].pos = Vec3(host_pos)
											# now replay saved local inputs deterministically from recv_frame+1 to current frame
											fixed_dt = 1.0 / 60.0
											for f in sorted(k for k in list(self._local_input_history.keys()) if k > recv_frame):
												ins = self._local_input_history.get(f)
												if ins:
													self.players[0].apply_input(ins, fixed_dt)
												self.players[0].update(fixed_dt)
											# prune history up to recv_frame
											for k in [k for k in list(self._local_input_history.keys()) if k <= recv_frame]:
												try:
													del self._local_input_history[k]
												except Exception:
													pass
							except Exception:
								pass
			self.netpeer.on_message = client_on_msg
			self.netpeer.start()
		elif mode == 'local':
			# create AI for second player
			if not hasattr(self, 'ai'):
				self.ai = SimpleAI(difficulty=1)

	def send_local_input(self, inputs):
		if self.mode == 'client' and self.netpeer and self.remote_addr:
			# record inputs for potential reconciliation
			try:
				self._local_input_history[self.frame] = dict(inputs)
			except Exception:
				pass
			self.netpeer.send({'type': 'input', 'inputs': inputs, 'frame': self.frame}, self.remote_addr)

	def set_key(self, key, value):
		self.key_map[key] = value
	
	def show_help(self):
		"""Show help overlay with controls and character moves"""
		if hasattr(self, 'help_overlay') and self.help_overlay:
			# Hide help if already shown
			self._hide_help()
			return
		
		from direct.gui.DirectGui import DirectFrame, OnscreenText, DirectButton
		from panda3d.core import TextNode
		
		# Create help overlay
		self.help_overlay = DirectFrame(
			frameColor=(0, 0, 0, 0.8),
			frameSize=(-1, 1, -1, 1),
			parent=self.render2d
		)
		
		# Help title
		OnscreenText(
			text='Game Help (Press H to close)',
			pos=(0, 0.8),
			scale=0.08,
			fg=(1, 1, 0.3, 1),
			align=TextNode.ACenter,
			parent=self.help_overlay
		)
		
		# Controls section
		controls_text = """Basic Controls:
WASD - Character Movement
Space/Left Mouse - Light Attack
Right Mouse - Heavy Attack
J - Jump
H - Show/Hide Help
ESC - Return to Previous Menu

Special Moves (KOF97 Style):
↓↘→ + Attack = Hadoken
→↓↘ + Attack = Shoryuken
↓↙← + Attack = Tatsumaki
→→ + Attack = Dash Attack
Jump + Attack = Air Attack"""
		
		OnscreenText(
			text=controls_text,
			pos=(-0.5, 0.2),
			scale=0.04,
			fg=(1, 1, 1, 1),
			align=TextNode.ALeft,
			parent=self.help_overlay
		)
		
		# Character-specific moves
		char_moves_text = """角色招式表:"""
		if hasattr(self, 'special_moves'):
			try:
				p1_name = getattr(self.players[0], 'character_name', 'Player 1')
				p2_name = getattr(self.players[1], 'character_name', 'Player 2')
				p1_moves = self.special_moves.get_move_list_text(p1_name)
				p2_moves = self.special_moves.get_move_list_text(p2_name)
				char_moves_text = p1_moves + "\n\n" + p2_moves
			except Exception:
				char_moves_text += "\n\nSpecial moves system loading..."
		else:
			char_moves_text += "\n\nSpecial moves system loading..."
		
		OnscreenText(
			text=char_moves_text,
			pos=(0.5, 0.2),
			scale=0.035,
			fg=(0.8, 1, 0.8, 1),
			align=TextNode.ALeft,
			parent=self.help_overlay,
			wordwrap=25
		)
		
		# Close button
		DirectButton(
			text='Close Help (H)',
			text_scale=0.04,
			text_fg=(1, 1, 1, 1),
			frameColor=(0.3, 0.3, 0.6, 0.8),
			frameSize=(-0.12, 0.12, -0.04, 0.04),
			pos=(0, 0, -0.7),
			command=self._hide_help,
			parent=self.help_overlay
		)
		
		# Accept H key to close help
		self.accept('h', self._hide_help)
	
	def _hide_help(self):
		"""Hide help overlay"""
		if hasattr(self, 'help_overlay') and self.help_overlay:
			self.help_overlay.removeNode()
			self.help_overlay = None
		
		# Re-bind H key to show help
		self.accept('h', self.show_help)

	def update(self, task: Task):
		dt = self.clock.getDt()
		
		# 🎭 更新3D动画管理器
		try:
			if hasattr(self, 'animation_3d_manager') and self.animation_3d_manager:
				self.animation_3d_manager.update_all(dt)
		except Exception as e:
			console_error(f"3D动画管理器更新失败: {e}", "animation")
		
		# Update game state first
		self.game_state.update(self.players)
		
		# Only process input and combat during fighting state
		if self.game_state.is_fighting():
			# Debug input handling
			speed = 6.0
			move = Vec3(0, 0, 0)
			if self.key_map['left']:
				move.x -= speed * dt
			if self.key_map['right']:
				move.x += speed * dt
			if self.key_map['up']:
				move.y += speed * dt
			if self.key_map['down']:
				move.y -= speed * dt

			# apply to local player inputs
			local_inputs = {k: self.key_map.get(k, False) for k in ['left', 'right', 'up', 'down', 'light', 'heavy', 'jump']}
			
			# 使用新的控制台系统进行调试输出
			active_keys = [k for k, v in local_inputs.items() if v]
			if active_keys and self.frame % 60 == 0:  # 降低频率到每秒一次
				console_debug(f"Player input detected: {active_keys}", "input")
			
			# Ensure we have players before applying input
			if len(self.players) > 0:
				try:
					self.players[0].apply_input(local_inputs, dt)
					if active_keys and self.frame % 60 == 0:
						console_debug(f"Applied input to player 0: pos={self.players[0].pos}", "input")
				except Exception as e:
					console_error(f"Error applying input to player 0: {e}", "input")
				
				# send inputs to host if client
				self.send_local_input(local_inputs)

			# AI or network-driven opponent
			if self.mode == 'local' and hasattr(self, 'ai') and len(self.players) > 1:
				try:
					opp_inputs = self.ai.decide(self.players[1], self.players[0])
					self.players[1].apply_input(opp_inputs, dt)
				except Exception as e:
					print(f"❌ Error applying AI input: {e}")
		elif self.mode == 'host' and self.netpeer:
			# consume buffered inputs from clients (we may need rollback if inputs are late)
			for addr, buf in list(self._client_input_buffer.items()):
				# sort by frame
				buf.sort(key=lambda x: (x[0] if x[0] is not None else -1))
				# find earliest late frame that is < current frame
				late_frames = [frm for frm, ins in buf if frm is not None and frm < self.frame]
				if late_frames:
					# we need to rollback to earliest late frame
					rollback_frame = min(late_frames)
					# restore authoritative snapshot at rollback_frame if available
					snap = self._state_history.get(rollback_frame)
					if snap:
						# restore both players state from snapshot
						try:
							self.players[0].restore_state(snap.get('p0'))
							self.players[1].restore_state(snap.get('p1'))
						except Exception:
							pass
						# Replay deterministically using fixed timestep
						fixed_dt = 1.0 / 60.0
						# replay frames from rollback_frame up to current-1 (current frame will be processed normally this tick)
						for f in range(rollback_frame, self.frame):
							# apply any client inputs for frame f
							for frm, inputs in [it for it in list(buf) if it[0] == f]:
								# inputs from clients are applied to player[1]
								self.players[1].apply_input(inputs, fixed_dt)
							# apply server-side AI or other deterministic inputs for server tick if mode==host
							if hasattr(self, 'ai'):
								ai_ins = self.ai.decide(self.players[1], self.players[0])
								self.players[1].apply_input(ai_ins, fixed_dt)
							# advance player simulation deterministically
							for p in self.players:
								p.update(fixed_dt)
				# remove any applied/old entries
				applied = []
				for frm, inputs in list(buf):
					if frm is None or frm <= self.frame:
						applied.append((frm, inputs))
				for item in applied:
					try:
						buf.remove(item)
					except ValueError:
						pass

		# Combat only during fighting state
		if self.game_state.is_fighting():
			hits = self.combat.apply_results()
			for h in hits:
				# play VFX / audio based on hit type
				hit_type = h.get('type', 'normal')
				pos = h.get('pos')
				damage = h.get('damage', 0)
				
				if hit_type == 'combo' or damage > 15:
					# Enhanced combo effect
					self.vfx.play_combo_effect(pos) 
					self.audio.play_sfx('combo')
					print("💥 Combo hit!")
				elif hit_type == 'special':
					# Special move effect
					move_name = h.get('move_name', 'fireball')
					self.vfx.play_special_move_effect(pos, move_name)
					self.audio.play_sfx('combo')
					print(f"🔥 Special move: {move_name}")
				else:
					# Normal hit effect
					self.vfx.play_hit(pos)
					self.audio.play_sfx('hit')
				
				# HUD feedback
				try:
					self.hud.on_hit()
				except Exception:
					pass
				
				# Trigger hit reaction animation
				try:
					hit_target = h.get('target')
					hit_attacker = h.get('attacker')
					if hit_target is not None and hit_attacker is not None:
						# Find the target player index
						target_idx = None
						attacker_idx = None
						for idx, player in enumerate(self.players):
							if player == hit_target:
								target_idx = idx
							if player == hit_attacker:
								attacker_idx = idx
						
						if target_idx is not None and attacker_idx is not None:
							# Determine hit direction
							attacker_pos = hit_attacker.pos
							target_pos = hit_target.pos
							hit_direction = (target_pos - attacker_pos).normalized()
							
							self.animator.start_hit_reaction(f"player_{target_idx}", hit_direction)
				except Exception as e:
					print(f"Hit animation failed: {e}")

		# Always update players and sprites
		for i, p in enumerate(self.players):
			p.update(dt)
			
			# Get current preferred rendering mode
			preferred_mode = self.settings_manager.get("preferred_version", "3d")
			
			# Update rendering based on mode
			if preferred_mode == "2.5d":
				# Update 2.5D sprite animations based on player state
				if hasattr(p, 'sprite_character') and p.sprite_character:
					self._update_sprite_animation(p, i)
					# Update sprite position
					p.sprite_character.set_position(p.pos)
			else:
				# Update 3D model animations during fighting for performance
				if self.game_state.is_fighting():
					player_inputs = None
					if i == 0:  # Player 1 (local input)
						player_inputs = {k: self.key_map.get(k, False) for k in ['left', 'right', 'up', 'down', 'light', 'heavy', 'jump']}
					
					# Update original animation system (less frequently to improve performance)
					if self.frame % 2 == 0:  # Update every other frame
						try:
							self.animator.update_animation_state(f"player_{i}", p.state, player_inputs)
						except Exception as e:
							if self.frame % 300 == 0:  # Only log every 5 seconds
								print(f"Animation update error: {e}")
					
					# Update KOF animation system (primary animation system for 3D)
					char_name = self.selected_character if i == 0 else self.selected_opponent
					if hasattr(self, 'kof_animator') and char_name:
						try:
							char_id = char_name.lower().replace(' ', '_')
							self.kof_animator.update_animation(char_id, player_inputs, p.state)
						except Exception as e:
							if self.frame % 300 == 0:  # Only log every 5 seconds
								print(f"KOF animation update error: {e}")

		# camera shake for VFX
		if hasattr(self.vfx, '_shake_timer') and self.vfx._shake_timer > 0 and self.cam:
			import random
			mag = 0.18 * self.vfx._shake_timer
			self.camera.setPos(0 + (random.random()-0.5)*mag, -20 + (random.random()-0.5)*mag, 6 + (random.random()-0.5)*mag)
			self.vfx._shake_timer -= dt
		else:
			self.camera.setPos(0, -20, 6)

		# vfx update
		self.vfx.update(dt)

		# update HUD with game state information
		game_info = self.game_state.get_game_info()
		self.hud.update(
			self.players, 
			game_time=game_info['remaining_time'],
			game_state=game_info['state']
		)
		
		# Update character info display (only once at start)
		if self.frame == 1:  # Do it on frame 1 to ensure players are loaded
			self.hud.update_character_info(self.players)

		# host broadcasts authoritative state
		if self.mode == 'host' and self.netpeer:
			p0 = self.players[0]
			p1 = self.players[1]
			snap = {
				'type': 'state',
				'frame': self.frame,
				'p0': {'pos': [p0.pos.x, p0.pos.y, p0.pos.z], 'health': p0.health, 'state': p0.state},
				'p1': {'pos': [p1.pos.x, p1.pos.y, p1.pos.z], 'health': p1.health, 'state': p1.state},
			}
			# save authoritative snapshot for potential rollback (keep history bounded)
			try:
				self._state_history[self.frame] = {'p0': p0.serialize_state(), 'p1': p1.serialize_state()}
			except Exception:
				pass
			# prune history older than 300 frames
			try:
				min_keep = max(0, self.frame - 300)
				for k in [k for k in list(self._state_history.keys()) if k < min_keep]:
					del self._state_history[k]
			except Exception:
				pass
			self.netpeer.broadcast(snap)

		# advance frame counter
		self.frame += 1

		return Task.cont
	
	def _on_state_change(self, new_state, previous_state):
		"""Handle game state changes"""
		print(f"Game state changed: {previous_state.value if previous_state else 'None'} -> {new_state.value}")
		
		if new_state == GameState.ROUND_START:
			# Reset player positions and health for new round
			self._reset_round()
		elif new_state == GameState.FIGHTING:
			# Enable input processing
			pass
		elif new_state == GameState.ROUND_END:
			# Disable input processing
			pass
		elif new_state == GameState.GAME_OVER:
			# Show final results
			pass
	
	def _on_round_start(self, round_num):
		"""Handle round start"""
		print(f"Round {round_num} starting!")
		self.hud.show_round_start(round_num)
		
		# Reset players for new round
		self._reset_round()
	
	def _on_round_end(self, winner_idx, result_type):
		"""Handle round end"""
		if winner_idx is not None:
			winner_name = getattr(self.players[winner_idx], 'character_name', f'Player {winner_idx + 1}')
			result_text = "KO" if result_type.value == "ko" else "TIME UP"
			print(f"Round ended: {winner_name} wins by {result_text}")
			self.hud.show_game_result(winner_name, result_text)
			
			# Play victory/defeat animations
			try:
				self.animator.start_victory_animation(f"player_{winner_idx}")
				loser_idx = 1 - winner_idx
				self.animator.start_defeat_animation(f"player_{loser_idx}")
			except Exception as e:
				print(f"Animation trigger failed: {e}")
		else:
			print("Round ended in draw")
			self.hud.show_game_result("DRAW", "DRAW")
	
	def _on_game_end(self, winner_idx):
		"""Handle game end"""
		if winner_idx is not None:
			winner_name = getattr(self.players[winner_idx], 'character_name', f'Player {winner_idx + 1}')
			print(f"Game Over! {winner_name} wins the match!")
			self.hud.show_game_result(f"{winner_name} WINS THE MATCH!", "VICTORY")
		else:
			print("Game ended in draw")
			self.hud.show_game_result("DRAW MATCH", "DRAW")
		
		# Schedule game restart or return to menu
		def end_game_action():
			if self.current_game_mode == 'adventure':
				# Progress to next level or return to menu
				self._handle_adventure_progression(winner_idx)
			else:
				# Return to character selection
				self._return_to_character_selection()
		
		self.taskMgr.doMethodLater(3.0, lambda task: end_game_action(), 'end-game-action')
	
	def _handle_adventure_progression(self, winner_idx):
		"""Handle adventure mode progression"""
		if winner_idx == 0:  # Player won
			self.current_level += 1
			if self.current_level % 10 == 1 and self.current_level > 1:
				print(f"BOSS LEVEL {self.current_level}!")
				# Select a boss character
				boss_chars = ["Geese Howard", "Orochi", "Rugal Bernstein"]
				import random 
				self.selected_opponent = random.choice(boss_chars)
			else:
				# Select next regular opponent
				self.selected_opponent = self.char_manager.get_random_character()
				while self.selected_opponent == self.selected_character:
					self.selected_opponent = self.char_manager.get_random_character()
			
			print(f"Adventure Mode Level {self.current_level}: Next opponent is {self.selected_opponent}")
			# Restart with new opponent
			self._restart_adventure_level()
		else:
			# Player lost, return to character selection
			self._return_to_character_selection()
	
	def _restart_adventure_level(self):
		"""Restart adventure level with new opponent"""
		# Clean up current game
		if hasattr(self, 'update_task'):
			self.taskMgr.remove('update-task')
		
		self.game_initialized = False
		
		# Re-initialize with new opponent
		self._initialize_adventure_mode()
	
	def _reset_round(self):
		"""Reset players for new round"""
		try:
			# 确保有足够的玩家
			if len(self.players) < 2:
				print(f"⚠️ Warning: Only {len(self.players)} players available, cannot reset round properly")
				return
			
			# Reset positions
			self.players[0].pos = Vec3(-3, 0, 0)
			self.players[1].pos = Vec3(3, 0, 0)
			
			# Reset health
			self.players[0].health = self.players[0].max_health
			self.players[1].health = self.players[1].max_health
			
			# Reset states
			for player in self.players:
				player.state = 'idle'
				player.is_jumping = False
				player.velocity = Vec3(0, 0, 0)
				if hasattr(player, 'combo'):
					player.combo = 0
				if hasattr(player, 'model') and player.model:
					player.model.setPos(player.pos)
				elif hasattr(player, 'node') and player.node:
					player.node.setPos(player.pos)
			
			print("Round reset complete")
			
		except Exception as e:
			print(f"Error resetting round: {e}")
	
	def _start_first_round(self, task):
		"""Start the first round after initialization"""
		self.game_state.change_state(GameState.ROUND_START)
		return task.done
	
	def _update_sprite_animation(self, player, player_idx):
		"""Update enhanced sprite animation based on player state with smooth transitions"""
		try:
			# Enhanced animation mapping with priority handling
			animation_map = {
				'idle': 'idle',
				'walking': 'walk', 
				'running': 'walk',
				'move': 'walk',
				'moving': 'walk',
				'attacking': 'attack',
				'attack': 'attack',
				'hit': 'hit',
				'hurt': 'hit',  # Map hurt to hit for consistency
				'damaged': 'hit',
				'jumping': 'jump',
				'jump': 'jump',
				'blocking': 'block',
				'block': 'block',
				'victory': 'victory',
				'win': 'victory',
				'defeat': 'hit',
				'ko': 'hit'
			}
			
			if not hasattr(player, 'sprite_character') or not player.sprite_character:
				return
			
			sprite_char = player.sprite_character
			current_state = getattr(player, 'state', 'idle')
			sprite_anim = animation_map.get(current_state, 'idle')
			
			# Enhanced animation control based on player input and state
			if player_idx == 0:  # Player 1 (local input)
				inputs = {k: self.key_map.get(k, False) for k in ['left', 'right', 'up', 'down', 'light', 'heavy', 'jump']}
				
				# Movement animation logic
				if inputs.get('left') or inputs.get('right'):
					if sprite_anim == 'idle':
						sprite_anim = 'walk'
				
				# Attack animation priority
				if inputs.get('light') or inputs.get('heavy'):
					if sprite_char.can_cancel_animation():
						sprite_anim = 'attack'
						# Play attack animation with high priority
						sprite_char.play_animation(sprite_anim, force_restart=False, priority_override=True)
						return
				
				# Jump animation
				if inputs.get('jump'):
					if sprite_char.can_cancel_animation():
						sprite_anim = 'jump'
						sprite_char.play_animation(sprite_anim, force_restart=False, priority_override=True)
						return
			
			# State-based animation updates
			if current_state == 'attacking':
				# Force attack animation
				sprite_char.play_animation('attack', force_restart=False, priority_override=True)
			elif current_state in ['hit', 'hurt', 'damaged']:
				# Force hit reaction
				sprite_char.interrupt_animation('hit')
			elif current_state == 'jumping':
				# Jump animation
				sprite_char.play_animation('jump', force_restart=False)
			elif current_state == 'blocking':
				# Block animation
				sprite_char.play_animation('block', force_restart=False)
			else:
				# Regular state-based animation
				sprite_char.play_animation(sprite_anim, force_restart=False)
			
			# Update facing direction based on player movement
			if hasattr(player, 'velocity') and player.velocity:
				if player.velocity.x > 0.1:
					sprite_char.set_facing(True)
				elif player.velocity.x < -0.1:
					sprite_char.set_facing(False)
				
		except Exception as e:
			if self.frame % 300 == 0:  # Only log every 5 seconds
				print(f"Enhanced sprite animation update error for player {player_idx}: {e}")

	def _extract_body_parts(self, player):
		"""Extract body parts from player model for animation"""
		body_parts = {}
		try:
			if hasattr(player, 'model') and player.model:
				# Try to find body parts by name
				for child in player.model.getChildren():
					child_name = child.getName().lower()
					if 'head' in child_name:
						body_parts['head'] = child
					elif 'torso' in child_name or 'body' in child_name:
						body_parts['torso'] = child
					elif 'arm' in child_name:
						if 'left' in child_name:
							body_parts['left_arm'] = child
						elif 'right' in child_name:
							body_parts['right_arm'] = child
						else:
							body_parts['right_arm'] = child  # Default
					elif 'leg' in child_name:
						if 'left' in child_name:
							body_parts['left_leg'] = child
						elif 'right' in child_name:
							body_parts['right_leg'] = child
						else:
							body_parts['right_leg'] = child  # Default
					elif 'eye' in child_name:
						if 'left' in child_name:
							body_parts['left_eye'] = child
						elif 'right' in child_name:
							body_parts['right_eye'] = child
		except Exception as e:
			print(f"Failed to extract body parts: {e}")
		
		return body_parts


def main():
	from streetBattle.launcher import launch

	launch()


if __name__ == '__main__':
	main()