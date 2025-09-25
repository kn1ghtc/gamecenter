from panda3d.core import Vec3
from direct.actor.Actor import Actor


class Player:
	"""Player with simple state timings and cooldowns."""
	def __init__(self, render, loader, name='Player', model_actor=None, pos=Vec3(0, 0, 0), character_data=None):
		self.name = name
		self.render = render
		self.loader = loader
		self.health = 100
		self.max_health = 100
		self.state = 'idle'
		self.facing = 1
		self.speed = 6.0
		self.pos = Vec3(pos)
		self.ground_y = pos.z  # Ground level for jumping
		self.velocity = Vec3(0, 0, 0)  # For jump physics
		self.node = None
		self.model = None  # For 3D character model
		self.state_timer = 0.0
		self.attack_cooldown = 0.0
		self.last_state = None
		self.character_data = character_data
		self.character_name = name
		self.combo = 0
		self.power_gauge = 0
		self.is_jumping = False
		self.jump_strength = 8.0
		self.gravity = -20.0
		
		# optional animation mapping
		self.anims = model_actor.get('anims', {}) if model_actor else {}

		# 1) Prefer asset-based Actor model if provided
		if model_actor:
			try:
				self.node = Actor(model_actor['model'], model_actor.get('anims', {}))
				self.node.reparentTo(self.render)
				self.model = self.node  # Keep reference
				print(f"[PlayerModel] Using Actor model for {self.name}: {model_actor['model']}")
			except Exception:
				self.node = None

		# 2) No procedural fallback: if no Actor model, keep a placeholder NodePath (no geometry)
		if not self.node:
			try:
				self.node = self.render.attachNewNode(f"{self.name}_root")
				self.model = self.node
				print(f"[PlayerModel] No Actor model provided for {self.name}; using empty root node (no visual fallback)")
			except Exception:
				self.node = None

		if self.node:
			self.node.setPos(self.pos)
			print(f"[PlayerModel] Model ready for {self.name}: node={type(self.node).__name__}")

		# apply character-specific customization if available
		try:
			self._apply_character_customization()
		except Exception:
			pass

		# start idle animation if available (use animation key, not file path)
		try:
			if self.node and hasattr(self.node, 'loop') and isinstance(self.node, Actor):
				# Only loop animations that actually exist on this Actor
				existing = set(self.node.getAnimNames()) if hasattr(self.node, 'getAnimNames') else set()
				if 'idle' in self.anims and 'idle' in existing:
					self.node.loop('idle')
				elif 'walk' in self.anims and 'walk' in existing:
					self.node.loop('walk')
		except Exception:
			pass

		self.hit_radius = 1.0
		# interpolation target (used by clients to smooth remote player)
		self.target_pos = None
		self.interpolate_speed = 12.0

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

		# Apply horizontal movement
		if move.lengthSquared() > 0 and self.attack_cooldown <= 0:
			self.pos += move

		# attacks are edge-triggered
		if inputs.get('light') and self.attack_cooldown <= 0:
			if self.is_jumping:
				self.state = 'jump_atk'
				self.state_timer = 0.3
				self.attack_cooldown = 0.5
			else:
				self.state = 'light_atk'
				self.state_timer = 0.25
				self.attack_cooldown = 0.4
		elif inputs.get('heavy') and self.attack_cooldown <= 0:
			if self.is_jumping:
				self.state = 'jump_heavy_atk'
				self.state_timer = 0.4
				self.attack_cooldown = 0.7
			else:
				self.state = 'heavy_atk'
				self.state_timer = 0.5
				self.attack_cooldown = 0.8
		else:
			if self.state not in ('light_atk', 'heavy_atk', 'jump', 'jump_atk', 'jump_heavy_atk'):
				if move.lengthSquared() > 0:
					self.state = 'walk'
				else:
					self.state = 'idle'

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
		
		# Update model position
		if self.node:
			try:
				self.node.setPos(self.pos)
			except Exception:
				pass
		
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
					except Exception:
						pass
		# ensure node follows pos
		# client-side interpolation: if a target_pos exists, move smoothly
		if self.target_pos is not None:
			# move towards target position
			delta = self.target_pos - self.pos
			step = delta * min(1.0, dt * self.interpolate_speed)
			if step.lengthSquared() > 0:
				self.pos += step
				# snap if very close
				if (self.target_pos - self.pos).length() < 0.01:
					self.pos = Vec3(self.target_pos)

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

