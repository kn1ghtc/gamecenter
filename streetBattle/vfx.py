from panda3d.core import NodePath, Vec3, Vec4, CardMaker
import random

from direct.interval.IntervalGlobal import Sequence, Func, Wait, LerpScaleInterval, LerpColorScaleInterval, LerpPosInterval, LerpHprInterval, Parallel
from direct.task import Task


class VFX:
    def __init__(self, base):
        self.base = base
        self.cam = getattr(base, 'camera', None)
        self.loader = getattr(base, 'loader', None)
        self.taskMgr = getattr(base, 'taskMgr', None)
        self.render = getattr(base, 'render', None)
        self._shake_timer = 0.0
        # enabled only if we have essential Panda3D pieces
        self.enabled = all([self.cam is not None, self.loader is not None, self.taskMgr is not None, self.render is not None])
        
        # Enhanced particle management for performance
        self.active_particles = []
        self.max_particles = 50  # Limit concurrent particles for performance
        
        # particle parent
        try:
            if self.render is not None:
                self.particles_root = self.render.attachNewNode('vfx_particles')
            else:
                self.particles_root = None
        except Exception:
            self.particles_root = None
        
        # Pre-load textures to avoid repeated loading
        self._hit_spark_texture = None
        self._energy_texture = None
        self._load_textures()
        
        # Enhanced shader effects
        self._setup_shaders()

    def _setup_shaders(self):
        """Setup enhanced shader effects for better visual quality"""
        try:
            if self.particles_root:
                # Enable transparency and alpha blending for particles
                from panda3d.core import TransparencyAttrib, RenderState
                self.particles_root.setTransparency(TransparencyAttrib.MAlpha)
                # Enable better blending
                from panda3d.core import ColorBlendAttrib
                self.particles_root.setAttrib(ColorBlendAttrib.make(
                    ColorBlendAttrib.MAdd,
                    ColorBlendAttrib.OIncomingAlpha,
                    ColorBlendAttrib.OOne
                ))
                print("✅ Enhanced VFX shaders enabled")
        except Exception as e:
            print(f"⚠️  Shader setup warning: {e}")

    def _load_textures(self):
        """Pre-load all VFX textures to avoid repeated loading during gameplay"""
        if not self.loader:
            return
        
        # Load hit spark texture
        try:
            self._hit_spark_texture = self.loader.loadTexture('assets/vfx/hit_spark.png')
            print("✅ Loaded high-quality generated hit spark texture")
        except Exception:
            try:
                self._hit_spark_texture = self.loader.loadTexture('assets/hit_spark.png')
                print("✅ Loaded basic hit spark texture")
            except Exception:
                try:
                    self._hit_spark_texture = self.loader.loadTexture('assets/images/effects/particle.png')
                    print("✅ Loaded basic particle texture")
                except Exception:
                    self._hit_spark_texture = None
                    print("⚠️  No particle texture available")
        
        # Load energy texture
        try:
            self._energy_texture = self.loader.loadTexture('assets/particles/energy.png')
            print("✅ Loaded energy particle texture")
        except Exception:
            try:
                self._energy_texture = self.loader.loadTexture('assets/vfx/hit_spark.png')
                print("✅ Using hit spark as energy texture")
            except Exception:
                self._energy_texture = None

    def play_hit(self, pos):
        """Play enhanced hit effect with performance optimization"""
        try:
            # normalize pos to Vec3 (accept tuple/list or LVector3)
            if not pos:
                pos = Vec3(0, 0, 0)
            else:
                try:
                    if isinstance(pos, (list, tuple)):
                        pos = Vec3(*pos)
                    else:
                        pos = Vec3(pos)
                except Exception:
                    pos = Vec3(0, 0, 0)
            
            print('💥 VFX: Enhanced hit effect at', pos)
            self._shake_timer = 0.25  # Slightly longer shake for impact
            
            if not self.enabled:
                return
            
            # Clean up old particles if we have too many
            self._cleanup_old_particles()
            
            # Use pre-loaded texture
            particle_tex = self._hit_spark_texture
            
            # Create more dynamic hit effect
            num_particles = 12  # Increased for better visual
            for i in range(num_particles):
                cm = CardMaker(f'hit_particle_{i}')
                cm.setFrame(-0.2, 0.2, -0.2, 0.2)
                node = self.render.attachNewNode(cm.generate())
                
                if particle_tex:
                    try:
                        node.setTexture(particle_tex, 1)
                        # Enable transparency for better blending
                        from panda3d.core import TransparencyAttrib
                        node.setTransparency(TransparencyAttrib.MAlpha)
                    except Exception:
                        pass
                
                # More dynamic offset pattern
                import math
                angle = (i / num_particles) * 2 * math.pi
                distance = 0.3 + random.random() * 0.4
                offset = Vec3(
                    distance * math.cos(angle),
                    (random.random() - 0.5) * 0.3,
                    distance * math.sin(angle) * 0.5 + random.random() * 0.3
                )
                
                node.setPos(pos + offset)
                node.setScale(0.5 + random.random() * 0.4)
                
                try:
                    if self.particles_root:
                        node.reparentTo(self.particles_root)
                except Exception:
                    pass
                
                # Enhanced velocity with outward burst
                vel = Vec3(
                    offset.x * 3.5 + (random.random() - 0.5) * 1.0,
                    (random.random() - 0.5) * 1.5,
                    offset.z * 2.0 + 1.5 + random.random() * 1.5
                )
                
                try:
                    node.setPythonTag('vfx_velocity', vel)
                    node.setPythonTag('vfx_life', 0.4 + random.random() * 0.3)
                    # Enhanced color effects - orange/red for hit impact
                    colors = [
                        (1.0, 0.8, 0.2, 0.9),  # Golden
                        (1.0, 0.5, 0.1, 0.9),  # Orange
                        (1.0, 0.3, 0.0, 0.9),  # Red-orange
                        (1.0, 1.0, 0.6, 0.9),  # Bright yellow
                    ]
                    color = random.choice(colors)
                    node.setColorScale(*color)
                except Exception:
                    pass
                
                # Add to active particles for management
                self.active_particles.append(node)
                
                # Enhanced animation sequence
                try:
                    # Scale animation with better timing
                    scale_seq = LerpScaleInterval(node, 0.35, Vec3(0.02, 0.02, 0.02))
                    fade_seq = LerpColorScaleInterval(node, 0.3, (0.5, 0.2, 0.0, 0.0))
                    cleanup_func = Func(self._remove_particle, node)
                    
                    seq = Sequence(Parallel(scale_seq, fade_seq), cleanup_func)
                    seq.start()
                except Exception:
                    if self.taskMgr:
                        def _remove_task(t, n=node):
                            self._remove_particle(n)
                            return Task.done
                        self.taskMgr.doMethodLater(0.4, _remove_task, f'remove-hit-particle-{i}')
                        
        except Exception as e:
            print('❌ VFX.play_hit error:', e)

    def _cleanup_old_particles(self):
        """Clean up old particles to maintain performance"""
        if len(self.active_particles) > self.max_particles:
            # Remove oldest particles
            particles_to_remove = self.active_particles[:len(self.active_particles) - self.max_particles]
            for particle in particles_to_remove:
                self._remove_particle(particle)

    def _remove_particle(self, particle):
        """Safely remove a particle node"""
        try:
            if particle in self.active_particles:
                self.active_particles.remove(particle)
            if particle and not particle.isEmpty():
                particle.removeNode()
        except Exception:
            pass

    def play_combo_effect(self, pos):
        """Play enhanced combo effect using generated particles"""
        try:
            if not pos:
                pos = Vec3(0, 0, 0)
            else:
                try:
                    if isinstance(pos, (list, tuple)):
                        pos = Vec3(*pos)
                    else:
                        pos = Vec3(pos)
                except Exception:
                    pos = Vec3(0, 0, 0)
            
            print('VFX: combo effect at', pos)
            self._shake_timer = 0.15
            
            if not self.enabled:
                return
            
            # Use pre-loaded energy texture
            energy_tex = self._energy_texture
            
            # Create energy particles in a spiral pattern
            num_particles = 12
            for i in range(num_particles):
                cm = CardMaker(f'energy_particle_{i}')
                cm.setFrame(-0.25, 0.25, -0.25, 0.25)
                node = self.render.attachNewNode(cm.generate())
                
                if energy_tex:
                    try:
                        node.setTexture(energy_tex, 1)
                    except Exception:
                        pass
                
                # Spiral pattern
                import math
                angle = (i / num_particles) * 2 * math.pi
                radius = 0.5 + (i % 3) * 0.3
                offset = Vec3(
                    radius * math.cos(angle),
                    radius * math.sin(angle) * 0.3,
                    0.2 + (i % 4) * 0.15
                )
                
                node.setPos(pos + offset)
                node.setScale(0.3 + random.random() * 0.2)
                
                try:
                    if self.particles_root:
                        node.reparentTo(self.particles_root)
                except Exception:
                    pass
                
                # Upward spiral velocity
                vel = Vec3(
                    -math.sin(angle) * 1.5,
                    math.cos(angle) * 0.5,
                    2.0 + random.random() * 1.0
                )
                
                try:
                    node.setPythonTag('vfx_velocity', vel)
                    node.setPythonTag('vfx_life', 0.8 + random.random() * 0.4)
                    # Blue/cyan energy color
                    node.setColorScale(0.3, 0.7 + random.random()*0.3, 1.0, 0.9)
                except Exception:
                    pass
                
                # Scale and fade animation
                try:
                    seq = Sequence(
                        LerpScaleInterval(node, 0.6, Vec3(0.1, 0.1, 0.1)),
                        Func(self._remove_particle, node)
                    )
                    seq.start()
                except Exception:
                    if self.taskMgr:
                        def _remove_task(t, n=node):
                            self._remove_particle(n)
                            return Task.done
                        self.taskMgr.doMethodLater(0.8, _remove_task, f'remove-energy-particle-{i}')
                        
        except Exception as e:
            print('❌ VFX.play_combo_effect error:', e)

    def play_special_move_effect(self, position, move_name):
        """Play effect for special moves based on move name
        
        Args:
            position: Vec3 position for effect
            move_name: Name of the special move
        """
        try:
            if not position:
                position = Vec3(0, 0, 0)
            else:
                try:
                    if isinstance(position, (list, tuple)):
                        position = Vec3(*position)
                    else:
                        position = Vec3(position)
                except Exception:
                    position = Vec3(0, 0, 0)
            
            print(f'🔥 VFX: Special move effect ({move_name}) at {position}')
            self._shake_timer = 0.4  # Strong shake for special moves
            
            if not self.enabled:
                return
            
            # Clean up old particles
            self._cleanup_old_particles()
            
            if move_name in ['fireball', 'hadoken', 'qcf']:
                self._create_fireball_effect(position)
            elif move_name in ['uppercut', 'shoryuken', 'dp']:
                self._create_uppercut_effect(position)
            elif move_name in ['hurricane_kick', 'tatsu', 'qcb']:
                self._create_energy_burst_effect(position, color=(0.7, 0.9, 1, 1))
            elif move_name in ['lightning', 'electric', 'thunder']:
                self._create_lightning_effect(position)
            else:
                # Default special effect
                self._create_energy_burst_effect(position)
                
        except Exception as e:
            print(f"Special move effect failed for {move_name}: {e}")
            # Fallback to basic hit effect
            self.play_hit(position)

    def _create_fireball_effect(self, pos):
        """Create fireball special move effect"""
        import math
        
        # Create fire particles in expanding circle
        num_particles = 16
        for i in range(num_particles):
            cm = CardMaker(f'fire_particle_{i}')
            cm.setFrame(-0.3, 0.3, -0.3, 0.3)
            node = self.render.attachNewNode(cm.generate())
            
            if self._energy_texture:
                try:
                    node.setTexture(self._energy_texture, 1)
                    from panda3d.core import TransparencyAttrib
                    node.setTransparency(TransparencyAttrib.MAlpha)
                except Exception:
                    pass
            
            # Circular expansion pattern
            angle = (i / num_particles) * 2 * math.pi
            layer = i % 3
            radius = 0.2 + layer * 0.3
            
            offset = Vec3(
                radius * math.cos(angle),
                radius * math.sin(angle) * 0.4,
                0.1 + layer * 0.2
            )
            
            node.setPos(pos + offset)
            node.setScale(0.4 + random.random() * 0.3)
            
            if self.particles_root:
                node.reparentTo(self.particles_root)
            
            # Fire colors - red/orange/yellow
            fire_colors = [
                (1.0, 0.2, 0.0, 0.9),  # Red
                (1.0, 0.5, 0.0, 0.9),  # Orange  
                (1.0, 0.8, 0.1, 0.9),  # Yellow-orange
                (1.0, 1.0, 0.3, 0.9),  # Yellow
            ]
            color = fire_colors[i % len(fire_colors)]
            node.setColorScale(*color)
            
            self.active_particles.append(node)
            
            # Animated scaling and fading
            try:
                scale_seq = LerpScaleInterval(node, 0.8, Vec3(0.05, 0.05, 0.05))
                fade_seq = LerpColorScaleInterval(node, 0.7, (0.3, 0.1, 0.0, 0.0))
                cleanup_func = Func(self._remove_particle, node)
                
                seq = Sequence(Parallel(scale_seq, fade_seq), cleanup_func)
                seq.start()
            except Exception:
                if self.taskMgr:
                    self.taskMgr.doMethodLater(0.8, lambda t: self._remove_particle(node), f'remove-fire-{i}')

    def _create_energy_burst_effect(self, pos):
        """Create energy burst effect for generic special moves"""
        import math
        
        # Central energy core
        core_cm = CardMaker('energy_core')
        core_cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        core_node = self.render.attachNewNode(core_cm.generate())
        
        if self._energy_texture:
            try:
                core_node.setTexture(self._energy_texture, 1)
                from panda3d.core import TransparencyAttrib
                core_node.setTransparency(TransparencyAttrib.MAlpha)
            except Exception:
                pass
        
        core_node.setPos(pos)
        core_node.setScale(0.1)
        core_node.setColorScale(0.2, 0.8, 1.0, 1.0)  # Cyan energy
        
        if self.particles_root:
            core_node.reparentTo(self.particles_root)
        
        self.active_particles.append(core_node)
        
        # Core expansion animation
        try:
            core_scale = LerpScaleInterval(core_node, 0.3, Vec3(1.5, 1.5, 1.5))
            core_fade = LerpColorScaleInterval(core_node, 0.5, (0.0, 0.3, 0.8, 0.0))
            core_cleanup = Func(self._remove_particle, core_node)
            
            core_seq = Sequence(core_scale, Parallel(core_fade), core_cleanup)
            core_seq.start()
        except Exception:
            if self.taskMgr:
                self.taskMgr.doMethodLater(0.6, lambda t: self._remove_particle(core_node), 'remove-energy-core')

    def update(self, dt):
        try:
            if self._shake_timer > 0 and self.cam is not None:
                self._shake_timer -= dt
                # small random jitter
                jitter = (random.random() - 0.5) * 0.15
                # keep original camera offset used by main.py
                self.cam.setPos(0 + jitter, -20, 6)
            else:
                if self.cam is not None:
                    self.cam.setPos(0, -20, 6)
            # advance particle positions if any (only those under particles_root)
            if self.enabled and self.particles_root is not None:
                try:
                    for node in list(self.particles_root.getChildren()):
                        try:
                            vel = node.getPythonTag('vfx_velocity')
                            life = node.getPythonTag('vfx_life')
                            if life is None:
                                life = 0.0
                            # advance
                            if vel is not None:
                                node.setPos(node.getPos() + vel * dt)
                            # reduce life and fade
                            life -= dt
                            if life <= 0:
                                try:
                                    node.removeNode()
                                except Exception:
                                    pass
                            else:
                                node.setPythonTag('vfx_life', life)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception as e:
            print('VFX.update error:', e)

    def _create_uppercut_effect(self, pos):
        """Create uppercut special move effect with rising energy"""
        import math
        
        # Create rising energy particles
        num_particles = 12
        for i in range(num_particles):
            cm = CardMaker(f'uppercut_particle_{i}')
            cm.setFrame(-0.2, 0.2, -0.4, 0.4)
            node = self.render.attachNewNode(cm.generate())
            
            if self._energy_texture:
                try:
                    node.setTexture(self._energy_texture, 1)
                except:
                    pass
            
            # Set position at base
            node.setPos(pos.x + (i - 6) * 0.1, pos.y, pos.z)
            
            # Blue-white energy colors
            if i % 3 == 0:
                node.setColor(0.3, 0.6, 1, 0.8)  # Blue
            elif i % 3 == 1:
                node.setColor(0.6, 0.8, 1, 0.8)  # Light blue
            else:
                node.setColor(1, 1, 1, 0.8)      # White
            
            # Rising animation
            rise_sequence = Sequence(
                # Quick rise with rotation
                Parallel(
                    LerpPosInterval(node, 0.8, pos + Vec3((i-6)*0.2, 0, 3.5)),
                    LerpHprInterval(node, 0.8, Vec3(0, 0, i * 45)),
                    LerpScaleInterval(node, 0.8, Vec3(2.0, 2.0, 2.0))
                ),
                # Fade out
                LerpColorScaleInterval(node, 0.3, Vec4(1, 1, 1, 0)),
                Func(self._safe_remove_node, node)
            )
            rise_sequence.start()
            
            self.active_particles.append(node)

    def _create_lightning_effect(self, pos):
        """Create lightning special move effect with electric bolts"""
        import math
        import random
        
        # Create lightning bolts
        num_bolts = 8
        for i in range(num_bolts):
            cm = CardMaker(f'lightning_bolt_{i}')
            cm.setFrame(-0.1, 0.1, -1.0, 1.0)
            node = self.render.attachNewNode(cm.generate())
            
            if self._energy_texture:
                try:
                    node.setTexture(self._energy_texture, 1)
                except:
                    pass
            
            # Random position around target
            angle = i * (360 / num_bolts) + random.uniform(-30, 30)
            radius = random.uniform(0.5, 1.5)
            x_offset = math.cos(math.radians(angle)) * radius
            y_offset = math.sin(math.radians(angle)) * radius
            
            node.setPos(pos.x + x_offset, pos.y + y_offset, pos.z + random.uniform(0, 2))
            
            # Electric colors - purple/blue/white
            if i % 4 == 0:
                node.setColor(0.8, 0.3, 1, 0.9)    # Purple
            elif i % 4 == 1:
                node.setColor(0.4, 0.7, 1, 0.9)    # Blue
            elif i % 4 == 2:
                node.setColor(1, 1, 1, 1)          # White
            else:
                node.setColor(0.7, 0.5, 1, 0.9)    # Light purple
            
            # Lightning strike animation
            lightning_sequence = Sequence(
                # Quick flash
                LerpColorScaleInterval(node, 0.05, Vec4(2, 2, 2, 1)),
                LerpColorScaleInterval(node, 0.05, Vec4(1, 1, 1, 1)),
                # Strike down
                Parallel(
                    LerpPosInterval(node, 0.3, pos + Vec3(x_offset*0.5, y_offset*0.5, -0.5)),
                    LerpScaleInterval(node, 0.3, Vec3(0.5, 0.5, 3.0)),
                    LerpHprInterval(node, 0.3, Vec3(random.uniform(-180, 180), 0, 0))
                ),
                # Multiple flashes
                LerpColorScaleInterval(node, 0.05, Vec4(3, 3, 3, 1)),
                LerpColorScaleInterval(node, 0.05, Vec4(1, 1, 1, 1)),
                LerpColorScaleInterval(node, 0.05, Vec4(2, 2, 2, 1)),
                # Fade out
                LerpColorScaleInterval(node, 0.4, Vec4(1, 1, 1, 0)),
                Func(self._safe_remove_node, node)
            )
            lightning_sequence.start()
            
            self.active_particles.append(node)

    def cleanup(self):
        """Clean up all VFX resources"""
        # Remove all active particles
        for particle in self.active_particles.copy():
            try:
                particle.removeNode()
            except:
                pass
        self.active_particles.clear()
        
        # Stop all ongoing sequences
        self.interval_manager.clearIntervals()
        
        print("🧹 VFX cleanup completed")
