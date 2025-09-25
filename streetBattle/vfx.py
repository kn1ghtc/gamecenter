from panda3d.core import NodePath, Vec3, CardMaker
import random

from direct.interval.IntervalGlobal import Sequence, Func, Wait, LerpScaleInterval
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

    def _load_textures(self):
        """Pre-load all VFX textures to avoid repeated loading during gameplay"""
        if not self.loader:
            return
        
        # Load hit spark texture
        try:
            self._hit_spark_texture = self.loader.loadTexture('assets/vfx/hit_spark.png')
            print("Loaded high-quality generated hit spark texture")
        except Exception:
            try:
                self._hit_spark_texture = self.loader.loadTexture('assets/hit_spark.png')
                print("Loaded basic hit spark texture")
            except Exception:
                try:
                    self._hit_spark_texture = self.loader.loadTexture('assets/images/effects/particle.png')
                    print("Loaded basic particle texture")
                except Exception:
                    self._hit_spark_texture = None
                    print("No particle texture available")
        
        # Load energy texture
        try:
            self._energy_texture = self.loader.loadTexture('assets/particles/energy.png')
            print("Loaded energy particle texture")
        except Exception:
            try:
                self._energy_texture = self.loader.loadTexture('assets/vfx/hit_spark.png')
                print("Using hit spark as energy texture")
            except Exception:
                self._energy_texture = None

    def play_hit(self, pos):
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
            print('VFX: hit at', pos)
            self._shake_timer = 0.2
            if not self.enabled:
                return
            # Skip BAM model loading, use textures directly
            particle_model = None
            
            # Use pre-loaded texture
            particle_tex = self._hit_spark_texture
            num = 8
            for i in range(num):
                if particle_model:
                    node = particle_model.copyTo(self.render)
                else:
                    cm = CardMaker('p')
                    cm.setFrame(-0.18, 0.18, -0.18, 0.18)
                    node = self.render.attachNewNode(cm.generate())
                    if particle_tex:
                        try:
                            node.setTexture(particle_tex, 1)
                        except Exception:
                            pass
                offset = Vec3((random.random() - 0.5) * 0.7, (random.random() - 0.5) * 0.2, random.random() * 0.7)
                node.setPos(pos + offset)
                node.setScale(0.45 + random.random() * 0.35)
                try:
                    if self.particles_root:
                        node.reparentTo(self.particles_root)
                except Exception:
                    pass
                vel = Vec3((random.random() - 0.5) * 2.8, (random.random() - 0.5) * 1.2, 1.2 + random.random() * 2.2)
                try:
                    node.setPythonTag('vfx_velocity', vel)
                    node.setPythonTag('vfx_life', 0.32 + random.random() * 0.22)
                except Exception:
                    pass
                # add glow effect for realism
                try:
                    node.setColorScale(1, 0.9 + random.random()*0.1, 0.3 + random.random()*0.7, 0.85)
                except Exception:
                    pass
                try:
                    seq = Sequence(LerpScaleInterval(node, 0.28, Vec3(0.01, 0.01, 0.01)), Func(node.removeNode))
                    seq.start()
                except Exception:
                    if self.taskMgr:
                        def _remove_task(t, n=node):
                            try:
                                n.removeNode()
                            except Exception:
                                pass
                            return Task.done
                        self.taskMgr.doMethodLater(0.32, _remove_task, 'remove-particle')
        except Exception as e:
            print('VFX.play_hit error:', e)

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
                        Func(node.removeNode)
                    )
                    seq.start()
                except Exception:
                    if self.taskMgr:
                        def _remove_task(t, n=node):
                            try:
                                n.removeNode()
                            except Exception:
                                pass
                            return Task.done
                        self.taskMgr.doMethodLater(0.8, _remove_task, 'remove-energy-particle')
                        
        except Exception as e:
            print('VFX.play_combo_effect error:', e)

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
