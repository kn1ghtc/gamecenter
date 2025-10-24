"""
玩家系统 - 处理玩家移动、射击、动画
"""

import sys
from pathlib import Path
# 添加项目根目录到sys.path
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pygame
from typing import Optional, Dict, List
from enum import Enum

from gamecenter.deltaOperation import config
from gamecenter.deltaOperation.core.physics import PhysicsBody, PhysicsEngine


class PlayerState(Enum):
    """玩家状态枚举"""
    IDLE = "idle"
    WALK = "walk"
    JUMP = "jump"
    CROUCH = "crouch"
    SHOOT = "shoot"
    RELOAD = "reload"
    HIT = "hit"
    DEATH = "death"


class Player(PhysicsBody):
    """
    玩家类
    继承物理实体，增加游戏逻辑
    """
    
    def __init__(self, x: float, y: float, player_id: int = 1):
        """
        初始化玩家
        
        Args:
            x: 初始X坐标
            y: 初始Y坐标
            player_id: 玩家ID(1或2，用于双人模式)
        """
        super().__init__(x, y, 
                        config.PLAYER_CONFIG["width"],
                        config.PLAYER_CONFIG["height"])
        
        self.player_id = player_id
        
        # 玩家属性
        self.max_health = config.PLAYER_CONFIG["health"]
        self.health = self.max_health
        self.move_speed = config.PLAYER_CONFIG["move_speed"]
        self.jump_force = config.PLAYER_CONFIG["jump_force"]
        
        # 状态
        self.state = PlayerState.IDLE
        self.facing_right = True
        self.is_crouching = False
        self.can_jump = True
        
        # 武器系统
        self.current_weapon = None  # 当前装备的武器
        self.weapons: List = []  # 拥有的武器列表
        self.is_shooting = False
        self.is_reloading = False
        
        # 动画
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.1  # 秒/帧
        
        # 控制键位(根据玩家ID选择)
        if player_id == 1:
            self.controls = config.CONTROLS_P1
        else:
            self.controls = config.CONTROLS_P2
        
        # HUD callbacks (set by gameplay_scene)
        self.on_weapon_switch_callback = None
        self.on_reload_start_callback = None
        
        # 无敌帧(受击后短暂无敌)
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1.0  # 秒
        
        # 加载精灵图
        self._load_sprites()
    
    def _load_sprites(self):
        """加载玩家精灵图"""
        # 确保pygame字体系统已初始化
        if not pygame.font.get_init():
            pygame.font.init()
        
        self.sprites: Dict[PlayerState, List[pygame.Surface]] = {}
        
        # 尝试加载真实精灵图
        sprite_loaded = False
        sprite_path = config.ASSETS_DIR / "assets" / "images" / "characters"
        
        if self.player_id == 1:
            sprite_file = sprite_path / "player_blue.png"
        else:
            sprite_file = sprite_path / "player_red.png"
        
        if sprite_file.exists():
            try:
                # 加载精灵表 (4x2 = 8帧)
                sprite_sheet = pygame.image.load(str(sprite_file)).convert_alpha()
                frame_width = sprite_sheet.get_width() // 4
                frame_height = sprite_sheet.get_height() // 2
                
                # 提取所有8帧
                all_frames = []
                for row in range(2):
                    for col in range(4):
                        frame_rect = pygame.Rect(
                            col * frame_width,
                            row * frame_height,
                            frame_width,
                            frame_height
                        )
                        frame = sprite_sheet.subsurface(frame_rect).copy()
                        # 缩放到玩家大小
                        frame = pygame.transform.scale(frame, 
                                                      (int(self.width), int(self.height)))
                        all_frames.append(frame)
                
                # 分配帧到各个状态
                self.sprites[PlayerState.IDLE] = [all_frames[0], all_frames[1]]
                self.sprites[PlayerState.WALK] = [all_frames[2], all_frames[3], all_frames[4], all_frames[5]]
                self.sprites[PlayerState.JUMP] = [all_frames[6]]
                self.sprites[PlayerState.CROUCH] = [all_frames[7]]
                self.sprites[PlayerState.SHOOT] = [all_frames[0]]
                self.sprites[PlayerState.RELOAD] = [all_frames[1]]
                self.sprites[PlayerState.HIT] = [all_frames[0]]
                self.sprites[PlayerState.DEATH] = [all_frames[7]]
                
                sprite_loaded = True
                print(f"[Player] 加载精灵图: {sprite_file.name}")
                
            except Exception as e:
                print(f"[Player] 精灵加载失败: {e}")
                sprite_loaded = False
        
        # 如果精灵加载失败，使用颜色矩形占位
        if not sprite_loaded:
            colors = {
                PlayerState.IDLE: (0, 128, 255),      # 蓝色
                PlayerState.WALK: (0, 200, 255),      # 浅蓝
                PlayerState.JUMP: (255, 128, 0),      # 橙色
                PlayerState.CROUCH: (128, 128, 255),  # 紫蓝
                PlayerState.SHOOT: (255, 0, 0),       # 红色
                PlayerState.RELOAD: (255, 255, 0),    # 黄色
                PlayerState.HIT: (255, 128, 128),     # 浅红
                PlayerState.DEATH: (64, 64, 64)       # 深灰
            }
            
            # 创建彩色矩形占位符
            for state, color in colors.items():
                frames = []
                # 为每个状态创建4帧动画
                for i in range(4):
                    surface = pygame.Surface((int(self.width), int(self.height)), 
                                            pygame.SRCALPHA)
                    # 渐变效果(模拟动画)
                    brightness = 1.0 - (i * 0.1)
                    adjusted_color = tuple(int(c * brightness) for c in color)
                    pygame.draw.rect(surface, adjusted_color, 
                                   surface.get_rect(), border_radius=5)
                    # 绘制玩家编号
                    font = pygame.font.Font(None, 24)
                    text = font.render(f"P{self.player_id}", True, (255, 255, 255))
                    text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
                    surface.blit(text, text_rect)
                    frames.append(surface)
                
                self.sprites[state] = frames
    
    def handle_input(self, keys):
        """
        处理玩家输入
        
        Args:
            keys: 键盘状态 (pygame.key.get_pressed()的返回值)
        """
        if self.state == PlayerState.DEATH:
            return
        
        # 重置碰撞状态
        self.on_wall = False
        
        # 水平移动
        move_x = 0
        if keys[self.controls["left"]]:
            move_x -= 1
            self.facing_right = False
        if keys[self.controls["right"]]:
            move_x += 1
            self.facing_right = True
        
        # 下蹲
        if keys[self.controls["crouch"]]:
            self.is_crouching = True
            self.height = config.PLAYER_CONFIG["height"] * 0.6  # 降低高度
        else:
            self.is_crouching = False
            self.height = config.PLAYER_CONFIG["height"]
        
        # 应用移动速度 (速度单位是像素/秒，需要乘delta_time)
        # 注意：这里只是设置速度，实际位移在physics_engine.update_body中计算
        if self.is_crouching:
            self.velocity.x = move_x * self.move_speed * 0.5  # 下蹲减速
        else:
            self.velocity.x = move_x * self.move_speed
        
        # 跳跃
        if keys[self.controls["jump"]] and self.can_jump and self.on_ground:
            self.velocity.y = self.jump_force
            self.can_jump = False
            self.state = PlayerState.JUMP
        
        # 释放跳跃键后可以再次跳跃
        if not keys[self.controls["jump"]]:
            self.can_jump = True
        
        # 射击
        if keys[self.controls["shoot"]] and not self.is_reloading:
            self.is_shooting = True
        else:
            self.is_shooting = False
        
        # 换弹
        if keys[self.controls["reload"]] and not self.is_reloading:
            self.start_reload()
        
        # 武器切换
        if keys[self.controls["weapon_next"]] and len(self.weapons) > 1:
            self._switch_weapon_next()
        if keys[self.controls["weapon_prev"]] and len(self.weapons) > 1:
            self._switch_weapon_prev()
    
    def update(self, delta_time: float, physics_engine: PhysicsEngine, 
              tilemap_or_level=None):
        """
        更新玩家状态
        
        Args:
            delta_time: 时间步长
            physics_engine: 物理引擎
            tilemap_or_level: 瓦片地图(2D列表)或LevelManager对象
        """
        if self.state == PlayerState.DEATH:
            return
        
        # 更新无敌帧
        if self.invincible:
            self.invincible_timer += delta_time
            if self.invincible_timer >= self.invincible_duration:
                self.invincible = False
                self.invincible_timer = 0
        
        # 更新物理
        physics_engine.update_body(self, delta_time)
        
        # 瓦片地图碰撞
        if tilemap_or_level:
            # 获取实际的tilemap
            from gamecenter.deltaOperation.core.level_manager import LevelManager
            if isinstance(tilemap_or_level, LevelManager):
                tilemap = tilemap_or_level.tilemap
            else:
                tilemap = tilemap_or_level
            
            collisions = physics_engine.check_tilemap_collision(self, tilemap)
            for collision in collisions:
                physics_engine.resolve_collision(self, collision)
        
        # 更新状态
        self._update_state()
        
        # 更新动画
        self._update_animation(delta_time)
        
        # 更新武器
        if self.current_weapon:
            self.current_weapon.update(delta_time)
            
            # 射击
            if self.is_shooting and not self.is_reloading:
                self.current_weapon.shoot(self.get_muzzle_position(), 
                                         self.get_aim_direction())
    
    def _update_state(self):
        """更新玩家状态"""
        if self.health <= 0:
            self.state = PlayerState.DEATH
            return
        
        if self.is_reloading:
            self.state = PlayerState.RELOAD
        elif self.is_shooting:
            self.state = PlayerState.SHOOT
        elif not self.on_ground:
            self.state = PlayerState.JUMP
        elif self.is_crouching:
            self.state = PlayerState.CROUCH
        elif abs(self.velocity.x) > 0.1:
            self.state = PlayerState.WALK
        else:
            self.state = PlayerState.IDLE
    
    def _update_animation(self, delta_time: float):
        """更新动画帧"""
        self.animation_timer += delta_time
        
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.animation_frame += 1
            
            # 循环动画
            max_frames = len(self.sprites[self.state])
            if self.animation_frame >= max_frames:
                self.animation_frame = 0
                
                # 换弹完成
                if self.state == PlayerState.RELOAD:
                    self.is_reloading = False
                    if self.current_weapon:
                        self.current_weapon.reload()
    
    def render(self, screen: pygame.Surface, camera_offset: tuple = (0, 0)):
        """
        渲染玩家
        
        Args:
            screen: 渲染目标
            camera_offset: 摄像机偏移
        """
        # 获取当前帧精灵 - 添加边界检查防止索引越界
        state_sprites = self.sprites.get(self.state, [])
        if not state_sprites:
            # 如果当前状态没有精灵,使用IDLE状态
            state_sprites = self.sprites.get(PlayerState.IDLE, [])
        
        # 确保动画帧索引在有效范围内
        if self.animation_frame >= len(state_sprites):
            self.animation_frame = 0
        
        sprite = state_sprites[self.animation_frame] if state_sprites else None
        if sprite is None:
            return  # 没有可用精灵时直接返回
        
        # 水平翻转(面向方向)
        if not self.facing_right:
            sprite = pygame.transform.flip(sprite, True, False)
        
        # 无敌闪烁效果
        if self.invincible and int(self.invincible_timer * 10) % 2 == 0:
            sprite = sprite.copy()
            sprite.set_alpha(128)
        
        # 渲染位置
        render_pos = (
            int(self.position.x - camera_offset[0]),
            int(self.position.y - camera_offset[1])
        )
        
        screen.blit(sprite, render_pos)
        
        # 渲染血量条
        self._render_healthbar(screen, render_pos)
    
    def _render_healthbar(self, screen: pygame.Surface, pos: tuple):
        """渲染血量条"""
        bar_width = int(self.width)
        bar_height = 4
        bar_x = pos[0]
        bar_y = pos[1] - 8
        
        # 背景(红色)
        pygame.draw.rect(screen, (255, 0, 0),
                        (bar_x, bar_y, bar_width, bar_height))
        
        # 当前血量(绿色)
        health_ratio = max(0, self.health / self.max_health)
        current_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (0, 255, 0),
                        (bar_x, bar_y, current_width, bar_height))
    
    def get_muzzle_position(self) -> tuple:
        """获取枪口位置(子弹发射点)"""
        offset_x = 20 if self.facing_right else -20
        offset_y = 10 if self.is_crouching else 15
        
        return (
            self.position.x + self.width / 2 + offset_x,
            self.position.y + offset_y
        )
    
    def get_aim_direction(self) -> pygame.math.Vector2:
        """获取瞄准方向"""
        # 简化版: 水平射击
        # TODO: 支持鼠标瞄准
        direction = pygame.math.Vector2(1 if self.facing_right else -1, 0)
        return direction
    
    def take_damage(self, damage: int):
        """
        受到伤害
        
        Args:
            damage: 伤害值
        """
        if self.invincible or self.state == PlayerState.DEATH:
            return
        
        self.health -= damage
        self.health = max(0, self.health)
        
        if self.health > 0:
            self.state = PlayerState.HIT
            self.invincible = True
            self.invincible_timer = 0
        else:
            self.state = PlayerState.DEATH
    
    def heal(self, amount: int):
        """
        治疗
        
        Args:
            amount: 治疗量
        """
        self.health += amount
        self.health = min(self.max_health, self.health)
    
    def add_weapon(self, weapon):
        """
        添加武器
        
        Args:
            weapon: 武器对象
        """
        self.weapons.append(weapon)
        if self.current_weapon is None:
            self.current_weapon = weapon
    
    def _switch_weapon_next(self):
        """切换到下一把武器"""
        if not self.weapons:
            return
        
        current_index = self.weapons.index(self.current_weapon)
        next_index = (current_index + 1) % len(self.weapons)
        self.current_weapon = self.weapons[next_index]
        
        # Notify HUD about weapon switch
        if hasattr(self, 'on_weapon_switch_callback') and self.on_weapon_switch_callback:
            self.on_weapon_switch_callback()
    
    def _switch_weapon_prev(self):
        """切换到上一把武器"""
        if not self.weapons:
            return
        
        current_index = self.weapons.index(self.current_weapon)
        prev_index = (current_index - 1) % len(self.weapons)
        self.current_weapon = self.weapons[prev_index]
        
        # Notify HUD about weapon switch
        if hasattr(self, 'on_weapon_switch_callback') and self.on_weapon_switch_callback:
            self.on_weapon_switch_callback()
    
    def start_reload(self):
        """开始换弹"""
        if self.current_weapon and self.current_weapon.can_reload():
            self.is_reloading = True
            self.animation_frame = 0
            
            # Notify HUD about reload start
            if hasattr(self, 'on_reload_start_callback') and self.on_reload_start_callback:
                self.on_reload_start_callback()
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.health > 0
    
    def reset_position(self, x: float, y: float):
        """
        重置位置(用于检查点复活)
        
        Args:
            x: 新X坐标
            y: 新Y坐标
        """
        self.position.x = x
        self.position.y = y
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)
    
    def to_dict(self) -> Dict:
        """
        序列化为字典(用于网络同步和存档)
        
        Returns:
            玩家数据字典
        """
        return {
            "player_id": self.player_id,
            "position": {"x": self.position.x, "y": self.position.y},
            "velocity": {"x": self.velocity.x, "y": self.velocity.y},
            "health": self.health,
            "facing_right": self.facing_right,
            "is_crouching": self.is_crouching,
            "state": self.state.value,
            "current_weapon": self.current_weapon.weapon_type if self.current_weapon else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Player':
        """
        从字典反序列化
        
        Args:
            data: 玩家数据字典
            
        Returns:
            玩家对象
        """
        player = cls(data["position"]["x"], data["position"]["y"], 
                    data["player_id"])
        player.velocity.x = data["velocity"]["x"]
        player.velocity.y = data["velocity"]["y"]
        player.health = data["health"]
        player.facing_right = data["facing_right"]
        player.is_crouching = data["is_crouching"]
        
        return player
