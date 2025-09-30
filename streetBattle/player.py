from panda3d.core import Vec3
from direct.actor.Actor import Actor

# 导入新的控制台系统
try:
	from gamecenter.streetBattle.smart_console import console_debug, console_error, console_position
except ImportError:
	# 如果导入失败，使用普通print作为备选
	def console_debug(msg, category=None): print(f"[DEBUG] {msg}")
	def console_error(msg, category=None): print(f"[ERROR] {msg}")
	def console_position(name, pos): print(f"[POS] {name}: {pos}")

# 导入动画状态枚举
try:
	from gamecenter.streetBattle.enhanced_3d_animation_system import AnimationState
except ImportError:
	# 如果导入失败，创建简单的备选
	class AnimationState:
		IDLE = "idle"
		WALK = "walk"
		JUMP = "jump"
		ATTACK_LIGHT = "light_attack"
		ATTACK_HEAVY = "heavy_attack"
		HURT = "hurt"


class Player:
	"""Player with simple state timings and cooldowns."""
	def __init__(self, render, loader, name='Player', model_actor=None, pos=Vec3(0, 0, 0), character_data=None, actor_instance=None, character_id=None):
		self.name = name
		self.render = render
		self.loader = loader
		
		# 如果提供了character_id，则使用它作为角色名称
		if character_id:
			self.character_name = character_id
		else:
			self.character_name = name
		
		# Load character stats from config file
		self._load_character_stats()
		
		# Set health from character stats or defaults
		char_stats = self._get_character_stats(self.character_name)
		self.max_health = char_stats.get('max_health', 1000)
		self.health = char_stats.get('health', self.max_health)
		self.state = 'idle'
		self.facing = 1
		self.speed = 6.0
		
		# Combat attributes
		self.hit_radius = char_stats.get('hit_radius', 1.5)  # Default hit radius
		
		# 处理pos参数，支持tuple和Vec3
		if isinstance(pos, tuple):
			self.pos = Vec3(pos[0], pos[1], pos[2])
		else:
			self.pos = Vec3(pos)
		
		self.ground_y = self.pos.z  # Ground level for jumping
		self.velocity = Vec3(0, 0, 0)  # For jump physics
		self.node = None
		self.model = None  # For 3D character model
		self.state_timer = 0.0
		self.attack_cooldown = 0.0
		self.last_state = None
		self.character_data = character_data
		self.combo = 0
		self.power_gauge = 0
		self.is_jumping = False
		self.jump_strength = 8.0
		self.gravity = -20.0
		
		# Add missing attributes for interpolation
		self.target_pos = None  # Target position for smooth movement
		self.interpolate_speed = 5.0  # Interpolation speed
		
		# 🎭 3D动画状态机引用（将在main.py中设置）
		self.animation_state_machine = None
		
		# Initialize with empty node first
		self.node = self.render.attachNewNode(f"{self.name}_root")
		self.model = self.node
		
		# optional animation mapping
		self.anims = model_actor.get('anims', {}) if model_actor else {}

		# 1) If a pre-created Actor instance is provided, use it directly
		if actor_instance and isinstance(actor_instance, Actor):
			try:
				if not actor_instance.isEmpty():
					# Remove placeholder safely and use provided Actor
					old_node = self.node
					self.node = actor_instance
					self.model = actor_instance
					self.node.reparentTo(self.render)
					
					# Cleanup old node after successful replacement
					if old_node and not old_node.isEmpty():
						if hasattr(old_node, 'cleanup') and isinstance(old_node, Actor):
							old_node.cleanup()
						old_node.removeNode()
					
					print(f"[PlayerModel] Using provided Actor instance for {self.name}")
					
					# List available animations
					if hasattr(actor_instance, 'getAnimNames'):
						anim_names = actor_instance.getAnimNames()
						if anim_names:
							print(f"[PlayerModel] Available animations for {self.name}: {list(anim_names)}")
							# Update anims dict with available animations
							self.anims.update({name: name for name in anim_names})
				else:
					print(f"[PlayerModel] Provided Actor instance is empty for {self.name}")
			except Exception as e:
				print(f"[PlayerModel] Failed to use provided Actor instance for {self.name}: {e}")
		
		# 2) Fallback: Prefer asset-based Actor model if provided
		elif model_actor:
			try:
				actor = Actor(model_actor['model'], model_actor.get('anims', {}))
				if actor and not actor.isEmpty():
					# Remove placeholder safely and use Actor directly
					old_node = self.node
					self.node = actor
					self.model = actor
					self.node.reparentTo(self.render)
					
					# Cleanup old node after successful replacement
					if old_node and not old_node.isEmpty():
						if hasattr(old_node, 'cleanup') and isinstance(old_node, Actor):
							old_node.cleanup()
						old_node.removeNode()
					
					print(f"[PlayerModel] Successfully loaded Actor model for {self.name}: {model_actor['model']}")
					
					# List available animations
					if hasattr(actor, 'getAnimNames'):
						anim_names = actor.getAnimNames()
						if anim_names:
							print(f"[PlayerModel] Available animations for {self.name}: {list(anim_names)}")
				else:
					print(f"[PlayerModel] Actor model is empty for {self.name}")
			except Exception as e:
				print(f"[PlayerModel] Failed to load Actor model for {self.name}: {e}")

		# Set position - 只在真实Panda3D环境中调用setPos
		if self.node and hasattr(self.node, 'setPos'):
			self.node.setPos(self.pos)
			# 确保3D模型被正确父化到render节点
			if hasattr(self.node, 'reparentTo') and self.render:
				self.node.reparentTo(self.render)
				console_debug(f"[Player] Reparented {self.name} 3D model to render node", "player")
			
			# 确保模型在地面上，而不是漂浮
			self._ensure_ground_contact()
	
	def _load_character_stats(self):
		"""Load character statistics from config file"""
		try:
			import json
			from pathlib import Path
			
			config_path = Path(__file__).parent / "config" / "character_stats.json"
			if config_path.exists():
				with open(config_path, 'r', encoding='utf-8') as f:
					self.character_stats_config = json.load(f)
				print(f"[Player] Loaded character stats configuration")
			else:
				print(f"[Player] Character stats config not found: {config_path}")
				self.character_stats_config = None
		except Exception as e:
			print(f"[Player] Failed to load character stats: {e}")
			self.character_stats_config = None
	
	def _get_character_stats(self, character_name: str) -> dict:
		"""Get stats for specific character"""
		if not self.character_stats_config:
			return {"max_health": 1000, "health": 1000}
		
		# Normalize character name for lookup
		normalized_name = character_name.lower().replace(' ', '_')
		
		# Try to find character-specific stats
		character_stats = self.character_stats_config.get("character_stats", {})
		if normalized_name in character_stats:
			return character_stats[normalized_name]
		
		# Fall back to default stats
		default_stats = self.character_stats_config.get("default_stats", {})
		print(f"[Player] Using default stats for {character_name}: HP={default_stats.get('max_health', 1000)}")
		return default_stats
	
	def get_skill_damage(self, skill_name: str) -> int:
		"""Get damage value for a specific skill"""
		if not self.character_stats_config:
			return 50  # Default damage
		
		skill_damage = self.character_stats_config.get("skill_damage", {})
		return skill_damage.get(skill_name, 50)
	
	def request_animation_state(self, animation_state, force=False):
		"""请求3D动画状态改变"""
		try:
			if hasattr(self, 'animation_state_machine') and self.animation_state_machine:
				# 使用新的3D动画状态机
				success = self.animation_state_machine.request_state_change(animation_state, force)
				if success:
					console_debug(f"Animation state changed to: {animation_state.value}", "animation")
				return success
			else:
				# 如果没有3D动画状态机，记录调试信息
				console_debug(f"No 3D animation state machine for {self.name}, requested: {animation_state.value if hasattr(animation_state, 'value') else animation_state}", "animation")
				return False
		except Exception as e:
			console_error(f"Failed to request animation state {animation_state}: {e}", "animation")
			return False
	
	def get_current_animation_state(self):
		"""获取当前3D动画状态"""
		try:
			if hasattr(self, 'animation_state_machine') and self.animation_state_machine:
				return self.animation_state_machine.get_current_state()
			else:
				return None
		except Exception as e:
			console_error(f"Failed to get animation state: {e}", "animation")
			return None
	
	def play_animation(self, anim_name, loop=True):
		"""播放指定的动画"""
		try:
			if isinstance(self.node, Actor) and hasattr(self.node, 'play'):
				available_anims = list(self.node.getAnimNames()) if hasattr(self.node, 'getAnimNames') else []
				
				if anim_name in available_anims:
					self.node.stop()  # 停止当前动画
					self.node.play(anim_name, loop=loop)
					console_debug(f"Playing animation: {anim_name} (loop: {loop})", "animation")
					return True
				else:
					# 尝试寻找相似的动画名称
					for available in available_anims:
						if anim_name.lower() in available.lower() or available.lower() in anim_name.lower():
							self.node.stop()
							self.node.play(available, loop=loop)
							console_debug(f"Playing similar animation: {available} for requested: {anim_name}", "animation")
							return True
					
					console_debug(f"Animation '{anim_name}' not found. Available: {available_anims}", "animation")
					return False
			else:
				console_debug(f"Node is not an Actor or has no play method: {type(self.node)}", "animation")
				return False
		except Exception as e:
			console_error(f"Failed to play animation {anim_name}: {e}", "animation")
			return False
	
	def update_3d_animation_based_on_state(self):
		"""根据玩家状态更新3D动画"""
		try:
			# 将游戏状态映射到动画状态
			state_mapping = {
				'idle': AnimationState.IDLE,
				'walking': AnimationState.WALK,
				'running': AnimationState.RUN,
				'jumping': AnimationState.JUMP,
				'attacking': AnimationState.ATTACK_LIGHT,
				'heavy_attack': AnimationState.ATTACK_HEAVY,
				'hurt': AnimationState.HURT,
				'blocking': AnimationState.BLOCK,
				'victory': AnimationState.VICTORY,
				'defeat': AnimationState.DEFEAT
			}
			
			# 获取对应的动画状态
			animation_state = state_mapping.get(self.state, AnimationState.IDLE)
			
			# 请求动画状态改变
			if hasattr(self, 'animation_state_machine') and self.animation_state_machine:
				current_state = self.animation_state_machine.get_current_state()
				if current_state != animation_state:
					self.request_animation_state(animation_state)
			
		except Exception as e:
			console_error(f"Failed to update 3D animation for {self.name}: {e}", "animation")
	
	def get_attack_frame_data(self, attack_type: str) -> dict:
		"""Get frame data for attack type"""
		if not self.character_stats_config:
			return {"startup_frames": 4, "active_frames": 3, "recovery_frames": 8}
		
		frame_data = self.character_stats_config.get("attack_frame_data", {})
		return frame_data.get(attack_type, {"startup_frames": 4, "active_frames": 3, "recovery_frames": 8})
		
		print(f"[PlayerModel] Model positioned for {self.name}: {self.pos}")

		# apply character-specific customization if available
		try:
			self._apply_character_customization()
		except Exception as e:
			print(f"[PlayerModel] Character customization failed for {self.name}: {e}")

		# start idle animation if available (use animation key, not file path)
		try:
			if self.node and hasattr(self.node, 'loop') and isinstance(self.node, Actor):
				# Only loop animations that actually exist on this Actor
				existing = set(self.node.getAnimNames()) if hasattr(self.node, 'getAnimNames') else set()
				if 'idle' in self.anims and 'idle' in existing:
					self.node.loop('idle')
					print(f"[PlayerModel] Started idle animation for {self.name}")
				elif 'walk' in self.anims and 'walk' in existing:
					self.node.loop('walk')
					print(f"[PlayerModel] Started walk animation for {self.name}")
				elif existing:
					# Try the first available animation
					first_anim = list(existing)[0]
					self.node.loop(first_anim)
					print(f"[PlayerModel] Started default animation '{first_anim}' for {self.name}")
		except Exception as e:
			print(f"[PlayerModel] Animation setup failed for {self.name}: {e}")

		self.hit_radius = 1.0
		# interpolation target (used by clients to smooth remote player)
		self.target_pos = None

	def _ensure_ground_contact(self):
		"""确保3D角色模型正确站在地面上"""
		if not self.node or not hasattr(self.node, 'getTightBounds'):
			return
		
		try:
			# 获取模型的边界框
			bounds = self.node.getTightBounds()
			if bounds and bounds[0] and bounds[1]:
				min_point = bounds[0]
				max_point = bounds[1]
				model_bottom_y = min_point.getZ()
				
				# 如果模型底部不在地面上，调整位置
				if model_bottom_y != self.ground_y:
					adjustment = self.ground_y - model_bottom_y
					current_pos = self.node.getPos()
					self.node.setPos(current_pos.getX(), current_pos.getY(), current_pos.getZ() + adjustment)
					self.pos.z = current_pos.getZ() + adjustment
					print(f"[Player] Adjusted {self.name} ground contact: y_offset = {adjustment:.2f}")
		except Exception as e:
			print(f"[Player] Ground contact adjustment failed for {self.name}: {e}")

	# Removed programmatic cartoon character creation: Actor-only pipeline
	
	def _apply_character_customization(self):
		"""Apply character-specific visual customizations"""
		if not self.model or not self.character_data:
			return
			
		try:
			# Apply color variations based on character
			colors = self.character_data.get('color_variations', [{}])
			if colors and self.model:
				primary_color = colors[0].get('primary', '#FFFFFF')
				# Convert hex to RGB
				try:
					r = int(primary_color[1:3], 16) / 255.0
					g = int(primary_color[3:5], 16) / 255.0
					b = int(primary_color[5:7], 16) / 255.0
					self.model.setColorScale(r, g, b, 1.0)
				except:
					pass
			
			# Apply scaling based on character stats
			stats = self.character_data.get('stats', {})
			speed = stats.get('speed', 5)
			scale_factor = 0.8 + (speed / 10.0 * 0.4)  # 0.8 to 1.2 range
			if self.model:
				self.model.setScale(scale_factor)
				
		except Exception as e:
			print(f"Error applying character customization: {e}")

	def apply_input(self, inputs, dt):
		"""处理玩家输入，增强安全性和错误处理以防止崩溃"""
		try:
			# If stunned/hurt -> ignore inputs
			if self.state in ('hurt', 'knockdown'):
				return

			# Jump input (only when on ground)
			if inputs.get('jump') and not self.is_jumping and abs(self.pos.z - self.ground_y) < 0.1:
				self.is_jumping = True
				self.velocity.z = self.jump_strength
				self.state = 'jump'
				self.state_timer = 0.5

			# Horizontal movement
			move = Vec3(0, 0, 0)
			if inputs.get('left'):
				move.x -= self.speed * dt
				self.facing = -1
			if inputs.get('right'):
				move.x += self.speed * dt
				self.facing = 1
			if inputs.get('up'):
				move.y += self.speed * dt
			if inputs.get('down'):
				move.y -= self.speed * dt

			# Apply horizontal movement with enhanced safety checks
			if move.lengthSquared() > 0 and self.attack_cooldown <= 0:
				old_pos = Vec3(self.pos)
				self.pos += move
				
				# 安全更新3D模型位置 - 防止崩溃的关键改进
				if self._safe_update_position():
					# Clear any target position to avoid interpolation conflicts
					self.target_pos = None
				else:
					# 如果位置更新失败，回滚到原位置
					self.pos = old_pos

			# attacks are edge-triggered
			if inputs.get('light') and self.attack_cooldown <= 0:
				if self.is_jumping:
					self.state = 'jump_atk'
					self.state_timer = 0.3
					self.attack_cooldown = 0.5
					# 🎭 更新3D动画状态机
					self._update_animation_state(AnimationState.ATTACK_LIGHT)
				else:
					self.state = 'light_atk'
					self.state_timer = 0.25
					self.attack_cooldown = 0.4
					# 🎭 更新3D动画状态机
					self._update_animation_state(AnimationState.ATTACK_LIGHT)
			elif inputs.get('heavy') and self.attack_cooldown <= 0:
				if self.is_jumping:
					self.state = 'jump_heavy_atk'
					self.state_timer = 0.4
					self.attack_cooldown = 0.7
					# 🎭 更新3D动画状态机
					self._update_animation_state(AnimationState.ATTACK_HEAVY)
				else:
					self.state = 'heavy_atk'
					self.state_timer = 0.5
					self.attack_cooldown = 0.8
					# 🎭 更新3D动画状态机
					self._update_animation_state(AnimationState.ATTACK_HEAVY)
			else:
				if self.state not in ('light_atk', 'heavy_atk', 'jump', 'jump_atk', 'jump_heavy_atk'):
					if move.lengthSquared() > 0:
						self.state = 'walk'
						# 🎭 更新3D动画状态机
						self._update_animation_state(AnimationState.WALK)
					else:
						self.state = 'idle'
						# 🎭 更新3D动画状态机
						self._update_animation_state(AnimationState.IDLE)
		
		except Exception as e:
			console_error(f"Player {self.name} input processing error: {e}", "input")
			# 安全恢复：确保状态仍然有效
			if hasattr(self, 'state') and self.state not in ('idle', 'walk', 'hurt', 'knockdown'):
				self.state = 'idle'
				self._update_animation_state(AnimationState.IDLE)
	
	def _update_animation_state(self, new_state):
		"""更新3D动画状态机状态"""
		try:
			if hasattr(self, 'animation_state_machine') and self.animation_state_machine:
				self.animation_state_machine.request_state_change(new_state)
		except Exception as e:
			console_debug(f"{self.name} 动画状态更新失败: {e}", "animation")
	
	def _safe_update_position(self) -> bool:
		"""安全更新角色位置，包含全面的错误处理"""
		try:
			# 基本安全检查
			if not self.node:
				print(f"⚠️  {self.name}: node is None, skipping position update")
				return False
			
			# 检查node是否为有效的Panda3D对象
			if not hasattr(self.node, 'setPos'):
				print(f"⚠️  {self.name}: node lacks setPos method")
				return False
			
			# 检查node是否已被删除
			if hasattr(self.node, 'isEmpty') and callable(self.node.isEmpty):
				if self.node.isEmpty():
					console_debug(f"{self.name}: node is empty", "position")
					return False
			
			# 验证位置参数的有效性
			if not isinstance(self.pos, Vec3):
				console_debug(f"{self.name}: position is not Vec3", "position")
				return False
			
			# 检查位置数值是否合理（防止NaN或无穷大）
			if not (abs(self.pos.x) < 1000 and abs(self.pos.y) < 1000 and abs(self.pos.z) < 1000):
				console_debug(f"{self.name}: position values out of reasonable range: {self.pos}", "position")
				return False
			
			# 尝试更新位置
			self.node.setPos(self.pos)
			
			# 使用新的控制台系统，减少输出频率
			if not hasattr(self, '_debug_counter'):
				self._debug_counter = 0
			self._debug_counter += 1
			if self._debug_counter % 120 == 0:  # 每2秒打印一次（假设60FPS）
				console_position(self.name, self.pos)
			
			return True
			
		except AttributeError as e:
			console_error(f"{self.name} position update failed (AttributeError): {e}", "position")
			return False
		except Exception as e:
			console_error(f"{self.name} position update failed (Exception): {e}", "position")
			return False

	def take_damage(self, amount):
		self.health = max(0, self.health - amount)
		self.state = 'hurt'
		self.state_timer = 0.35
		self.attack_cooldown = max(self.attack_cooldown, 0.2)

	def distance_to(self, other: 'Player'):
		return (self.pos - other.pos).length()

	def update(self, dt):
		# Jump physics
		if self.is_jumping:
			# Apply gravity
			self.velocity.z += self.gravity * dt
			self.pos.z += self.velocity.z * dt
			
			# Check for landing
			if self.pos.z <= self.ground_y:
				self.pos.z = self.ground_y
				self.velocity.z = 0
				self.is_jumping = False
				if self.state == 'jump':
					self.state = 'idle'
		
		# Update model position only if no input movement is happening
		# This prevents conflicts between input-driven movement and interpolation
		if self.node:
			try:
				# Always ensure the 3D model position matches logical position
				current_model_pos = self.node.getPos() if hasattr(self.node, 'getPos') else None
				if current_model_pos is None or (current_model_pos - self.pos).length() > 0.01:
					self.node.setPos(self.pos)
				
				# 🎭 Update 3D animation based on current state
				self.update_3d_animation_based_on_state()
			except Exception as e:
				console_error(f"Failed to update {self.name} node position/animation: {e}", "player")
		
		# timers
		if self.state_timer > 0:
			self.state_timer -= dt
			if self.state_timer <= 0:
				# revert from transient states
				if self.state in ('light_atk', 'heavy_atk', 'hurt'):
					self.state = 'idle'
		if self.attack_cooldown > 0:
			self.attack_cooldown -= dt
		# animation playback on state change
		if self.last_state != self.state:
			self.last_state = self.state
			if self.node and hasattr(self.node, 'play') and isinstance(self.node, Actor):
				# map logical states to animation names
				anim_name = None
				existing = set(self.node.getAnimNames()) if hasattr(self.node, 'getAnimNames') else set()
				if self.state == 'walk':
					anim_name = 'walk' if ('walk' in self.anims and 'walk' in existing) else None
				elif self.state in ('idle',):
					anim_name = 'idle' if ('idle' in self.anims and 'idle' in existing) else None
				elif self.state in ('jump', 'jump_atk', 'jump_heavy_atk'):
					anim_name = 'jump' if ('jump' in self.anims and 'jump' in existing) else (('idle' if ('idle' in self.anims and 'idle' in existing) else None))
				elif self.state == 'light_atk':
					if 'light' in self.anims and 'light' in existing:
						anim_name = 'light'
					elif 'attack' in self.anims and 'attack' in existing:
						anim_name = 'attack'
					elif 'idle' in self.anims and 'idle' in existing:
						anim_name = 'idle'
				elif self.state == 'heavy_atk':
					if 'heavy' in self.anims and 'heavy' in existing:
						anim_name = 'heavy'
					elif 'attack' in self.anims and 'attack' in existing:
						anim_name = 'attack'
					elif 'idle' in self.anims and 'idle' in existing:
						anim_name = 'idle'
				elif self.state == 'hurt':
					anim_name = 'hurt' if ('hurt' in self.anims and 'hurt' in existing) else (('idle' if ('idle' in self.anims and 'idle' in existing) else None))
				if anim_name:
					try:
						self.node.play(anim_name)
						console_debug(f"Playing animation: {anim_name} for state: {self.state}", "animation")
					except Exception as e:
						console_error(f"Failed to play animation {anim_name}: {e}", "animation")
		# ensure node follows pos
		# client-side interpolation: only use if no direct input movement is happening
		if self.target_pos is not None and not hasattr(self, '_direct_movement_frame'):
			# move towards target position
			delta = self.target_pos - self.pos
			step = delta * min(1.0, dt * self.interpolate_speed)
			if step.lengthSquared() > 0:
				self.pos += step
				# snap if very close
				if (self.target_pos - self.pos).length() < 0.01:
					self.pos = Vec3(self.target_pos)
					self.target_pos = None

		# Final position sync to ensure 3D model is always in sync
		if self.node:
			try:
				self.node.setPos(self.pos)
			except Exception:
				pass

	def set_target_pos(self, pos):
		try:
			self.target_pos = Vec3(pos)
		except Exception:
			self.target_pos = None

	def debug_status(self):
		"""Debug method to check player status"""
		status = {
			'name': self.name,
			'pos': f"({self.pos.x:.2f}, {self.pos.y:.2f}, {self.pos.z:.2f})",
			'node_exists': self.node is not None,
			'node_type': type(self.node).__name__ if self.node else None,
			'node_empty': self.node.isEmpty() if self.node and hasattr(self.node, 'isEmpty') else "N/A",
			'state': self.state,
			'speed': self.speed
		}
		
		if self.node and hasattr(self.node, 'getPos'):
			try:
				model_pos = self.node.getPos()
				status['model_pos'] = f"({model_pos.x:.2f}, {model_pos.y:.2f}, {model_pos.z:.2f})"
			except:
				status['model_pos'] = "Error getting position"
		else:
			status['model_pos'] = "No getPos method"
			
		return status

	def serialize_state(self):
		# Return a JSON-serializable snapshot of the player's state
		return {
			'pos': [self.pos.x, self.pos.y, self.pos.z],
			'health': self.health,
			'state': self.state,
			'state_timer': float(self.state_timer),
			'attack_cooldown': float(self.attack_cooldown),
			'facing': int(self.facing),
		}

	def restore_state(self, s: dict):
		# Restore from a serialized snapshot
		try:
			if not s:
				return
			pos = s.get('pos')
			if pos:
				self.pos = Vec3(*pos)
				if self.node:
					try:
						self.node.setPos(self.pos)
					except Exception:
						pass
			health = s.get('health')
			if health is not None:
				self.health = health
			state = s.get('state')
			if state:
				self.state = state
			self.state_timer = float(s.get('state_timer', 0.0))
			self.attack_cooldown = float(s.get('attack_cooldown', 0.0))
			self.facing = int(s.get('facing', 1))
		except Exception:
			# best-effort restore, ignore errors
			pass

