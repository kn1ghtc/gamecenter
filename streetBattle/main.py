from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4, Vec3, ClockObject, WindowProperties
from direct.task import Task
from direct.actor.Actor import Actor
import sys
import argparse

from gamecenter.streetBattle.player import Player
from gamecenter.streetBattle.combat import CombatSystem
from gamecenter.streetBattle.net import NetPeer
from gamecenter.streetBattle.ai import SimpleAI
from gamecenter.streetBattle.vfx import VFX
from gamecenter.streetBattle.audio import AudioSystem
from gamecenter.streetBattle.ui import HUD
from gamecenter.streetBattle.enhanced_character_manager import EnhancedCharacterManager as CharacterManager
from gamecenter.streetBattle.game_state import GameStateManager, GameState
from gamecenter.streetBattle.character_animator import CharacterAnimator
from gamecenter.streetBattle.game_mode_selector import GameModeSelector
from gamecenter.streetBattle.character_selector import CharacterSelector
from gamecenter.streetBattle.special_moves import SpecialMovesSystem, enhance_player_with_special_moves


class StreetBattleGame(ShowBase):
	def __init__(self):
		super().__init__()
		self.disableMouse()
		self.window_title = "StreetBattle - KOF97 Style Fighting Game"
		try:
			props = WindowProperties()
			props.setSize(1280, 720)
			props.setTitle(self.window_title)
			self.win.requestProperties(props)
		except Exception:
			pass
		
		# Game state management
		self.current_game_mode = None
		self.selected_character = None
		self.selected_opponent = None
		self.game_initialized = False
		self.help_overlay = None
		
		# Initialize fixed character manager with simple model fallback
		from gamecenter.streetBattle.enhanced_character_manager import EnhancedCharacterManager as FixedEnhancedCharacterManager
		self.char_manager = FixedEnhancedCharacterManager(self)
		print("[StreetBattle] Using Fixed Character Manager with simple model fallback for placeholders")
		
		# UI systems
		self.mode_selector = GameModeSelector(self)
		self.character_selector = CharacterSelector(self, self.char_manager)
		
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
		elif self.character_selector and not self.mode_selector:
			# Return to mode selection
			self._return_to_mode_selection()
		else:
			# Clean up and exit game
			self._cleanup_and_exit()
	
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
		self.character_selector.hide()
		self.mode_selector.show(callback=self._on_game_mode_selected)
	
	def _return_to_character_selection(self):
		"""Return to character selection"""
		# Clean up game
		if hasattr(self, 'update_task'):
			self.taskMgr.remove('update-task')
		
		self.game_initialized = False
		
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

		# Ground: use high-quality Arena FPS model, fallback to simpler options
		try:
			# Try to load high-quality arena from Arena FPS sample
			self.ground = self.loader.loadModel('assets/models/arena_1.bam')
			if not self.ground:
				self.ground = self.loader.loadModel('assets/models/arena_1.gltf')
			self.ground.reparentTo(self.render)
			self.ground.setScale(1.0)
			self.ground.setPos(0, 0, 0)
			print("Loaded high-quality arena model")
		except Exception as e:
			try:
				# Fallback to basic arena
				self.ground = self.loader.loadModel('assets/arena.bam')
				self.ground.setTexture(self.loader.loadTexture('assets/arena.png'), 1)
				self.ground.reparentTo(self.render)
				self.ground.setScale(1.0)
				self.ground.setPos(0, 0, 0)
				print("Loaded basic arena model")
			except Exception:
				try:
					self.ground = self.loader.loadModel('models/environment')
					self.ground.reparentTo(self.render)
					self.ground.setScale(0.25)
					self.ground.setPos(-8, 42, 0)
					print("Loaded default Panda3D environment")
				except Exception:
					from panda3d.core import CardMaker
					cm = CardMaker('ground')
					cm.setFrame(-20, 20, -10, 10)
					card = self.render.attachNewNode(cm.generate())
					card.setP(-90)
					card.setPos(0, 0, 0)
					card.setColor(0.1, 0.6, 0.1, 1)
					print("Created basic ground plane")

		# Gameplay systems
		self.mode = 'local'  # Will be updated based on game mode
		self.netpeer = None
		self.remote_addr = None
		self.vfx = VFX(self)
		self.audio = AudioSystem(self)
		self.hud = HUD(self)
		
		# Animation system
		self.animator = CharacterAnimator(self)
		
		# Game state management
		self.game_state = GameStateManager(self)
		self.game_state.on_state_change = self._on_state_change
		self.game_state.on_round_start = self._on_round_start
		self.game_state.on_round_end = self._on_round_end
		self.game_state.on_game_end = self._on_game_end

		# Create players with selected characters
		self.players = []
		
		print(f"\\n=== CREATING GAME CHARACTERS ===")
		print(f"Player: {self.selected_character}")
		print(f"Opponent: {self.selected_opponent}")
		
		try:
			p0 = self.char_manager.create_enhanced_player(self.selected_character, Vec3(-3, 0, 0))
			print(f"Player 1 created as {self.selected_character}")
		except Exception as e:
			print(f"Failed to create player character: {e}")
			# Fallback: try enhanced character manager with legacy mode
			try:
				if hasattr(self.char_manager, 'create_enhanced_character_model'):
					model = self.char_manager.create_enhanced_character_model(self.selected_character, Vec3(-3, 0, 0))
					if model:
						p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
						if hasattr(p0, 'model') and p0.model:
							p0.model.removeNode()
						p0.model = model
						p0.node = model
					else:
						p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
				else:
					p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
			except Exception:
				p0 = Player(self.render, self.loader, name=self.selected_character, pos=Vec3(-3, 0, 0))
		
		try:
			p1 = self.char_manager.create_enhanced_player(self.selected_opponent, Vec3(3, 0, 0))
			print(f"Player 2 created as {self.selected_opponent}")
			# Apply different color tint for opponent
			if hasattr(p1, 'model') and p1.model:
				p1.model.setColorScale(0.8, 0.9, 1.1, 1.0)  # Slightly bluish tint
		except Exception as e:
			print(f"Failed to create opponent character: {e}")
			# Fallback: try enhanced character manager with legacy mode
			try:
				if hasattr(self.char_manager, 'create_enhanced_character_model'):
					model = self.char_manager.create_enhanced_character_model(self.selected_opponent, Vec3(3, 0, 0))
					if model:
						p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
						if hasattr(p1, 'model') and p1.model:
							p1.model.removeNode()
						p1.model = model
						p1.node = model
						# Apply different color tint for opponent
						p1.model.setColorScale(0.8, 0.9, 1.1, 1.0)
					else:
						p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
				else:
					p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
			except Exception:
				p1 = Player(self.render, self.loader, name=self.selected_opponent, pos=Vec3(3, 0, 0))
		
		self.players.append(p0)
		self.players.append(p1)

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

		# Register players for animation
		try:
			# Extract body parts from cartoon characters if available
			p0_parts = self._extract_body_parts(p0)
			p1_parts = self._extract_body_parts(p1)
			
			self.animator.register_character("player_0", p0.model if hasattr(p0, 'model') else p0.node, p0_parts)
			self.animator.register_character("player_1", p1.model if hasattr(p1, 'model') else p1.node, p1_parts)
			print("Players registered for animation")
		except Exception as e:
			print(f"Animation registration failed: {e}")

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
			# Try to load generated or downloaded audio files from optimized audio directory
			try:
				self.audio.load_bgm('assets/audio/bgm_loop.ogg')
			except Exception:
				# Fallback to WAV if OGG fails
				self.audio.load_bgm('assets/audio/bgm_loop.wav')
			
			try:
				# Prefer generated hit sound if available from optimized audio directory
				self.audio.load_sfx('assets/audio/hit_generated.wav', name='hit')
				print("Loaded generated hit sound")
			except Exception:
				try:
					self.audio.load_sfx('assets/hit.wav', name='hit')
					print("Loaded basic hit sound")
				except Exception:
					print("No hit sound available")
			
			try:
				# Load combo sound
				self.audio.load_sfx('assets/sounds/combo_generated.wav', name='combo')
				print("Loaded generated combo sound")
			except Exception:
				try:
					self.audio.load_sfx('assets/combo.wav', name='combo')
					print("Loaded basic combo sound")
				except Exception:
					print("No combo sound available")
			
			# play bgm in local mode
			if self.mode == 'local':
				self.audio.play_bgm(loop=True)
		except Exception as e:
			print(f"Audio loading failed: {e}")
		
		self.game_initialized = True
		print("Game initialized successfully!")

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
		
		# Update game state first
		self.game_state.update(self.players)
		
		# Only process input and combat during fighting state
		if self.game_state.is_fighting():
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
			
			# Debug: Print inputs when keys are pressed
			active_keys = [k for k, v in local_inputs.items() if v]
			if active_keys:
				print(f"Player input: {active_keys}")
			
			self.players[0].apply_input(local_inputs, dt)
			# send inputs to host if client
			self.send_local_input(local_inputs)

			# AI or network-driven opponent
			if self.mode == 'local' and hasattr(self, 'ai'):
				opp_inputs = self.ai.decide(self.players[1], self.players[0])
				self.players[1].apply_input(opp_inputs, dt)
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
				
				if hit_type == 'combo' or h.get('damage', 0) > 15:
					# Enhanced combo effect
					self.vfx.play_combo_effect(pos) 
					self.audio.play_sfx('combo')
					print("Combo hit!")
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

		# Always update players for animations, but combat only during fighting
		for i, p in enumerate(self.players):
			p.update(dt)
			
			# Update character animations based on player state
			if self.game_state.is_fighting():
				player_inputs = None
				if i == 0:  # Player 1 (local input)
					player_inputs = {k: self.key_map.get(k, False) for k in ['left', 'right', 'up', 'down', 'light', 'heavy', 'jump']}
				
				self.animator.update_animation_state(f"player_{i}", p.state, player_inputs)

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
	parser = argparse.ArgumentParser()
	parser.add_argument('--mode', choices=['local', 'host', 'client'], default='local', help='Deprecated: Use in-game mode selection')
	parser.add_argument('--host', help='Deprecated: Use in-game network mode')
	parser.add_argument('--port', type=int, default=12000, help='Deprecated: Use in-game network mode')
	args = parser.parse_args()

	# Ignore command line arguments and use in-game selection
	app = StreetBattleGame()
	app.run()


if __name__ == '__main__':
	main()