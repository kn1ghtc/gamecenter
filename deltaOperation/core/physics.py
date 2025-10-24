"""
物理引擎 - 处理碰撞检测、重力、弹道计算
"""

import sys
from pathlib import Path
# 添加项目根目录到sys.path
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pygame
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import math

from gamecenter.deltaOperation import config


class Vector2D:
    """二维向量类"""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def length(self) -> float:
        """向量长度"""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalize(self) -> 'Vector2D':
        """归一化向量"""
        length = self.length()
        if length > 0:
            return Vector2D(self.x / length, self.y / length)
        return Vector2D(0, 0)
    
    def dot(self, other: 'Vector2D') -> float:
        """点积"""
        return self.x * other.x + self.y * other.y
    
    def tuple(self) -> Tuple[float, float]:
        """转换为元组"""
        return (self.x, self.y)


@dataclass
class CollisionResult:
    """碰撞检测结果"""
    collided: bool = False
    normal: Tuple[float, float] = (0, 0)  # 碰撞法线
    overlap: float = 0.0  # 重叠距离
    collision_point: Tuple[float, float] = (0, 0)


class AABB:
    """
    轴对齐包围盒(Axis-Aligned Bounding Box)
    用于快速碰撞检测
    """
    
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self) -> float:
        return self.x
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def top(self) -> float:
        return self.y
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def overlaps(self, other: 'AABB') -> bool:
        """检测是否与另一个AABB重叠"""
        return (self.left < other.right and
                self.right > other.left and
                self.top < other.bottom and
                self.bottom > other.top)
    
    def contains_point(self, x: float, y: float) -> bool:
        """检测点是否在AABB内"""
        return (self.left <= x <= self.right and
                self.top <= y <= self.bottom)
    
    def to_rect(self) -> pygame.Rect:
        """转换为Pygame Rect"""
        return pygame.Rect(int(self.x), int(self.y), 
                          int(self.width), int(self.height))


class PhysicsBody:
    """
    物理实体基类
    包含位置、速度、加速度等物理属性
    """
    
    def __init__(self, x: float, y: float, width: float, height: float):
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)
        
        self.width = width
        self.height = height
        
        # 物理属性
        self.mass = 1.0
        self.gravity_enabled = True
        self.friction = 0.9  # 摩擦系数
        
        # 碰撞状态
        self.on_ground = False
        self.on_wall = False
    
    @property
    def aabb(self) -> AABB:
        """获取碰撞盒"""
        return AABB(self.position.x, self.position.y, 
                   self.width, self.height)
    
    @property
    def rect(self) -> pygame.Rect:
        """获取Pygame矩形"""
        return pygame.Rect(int(self.position.x), int(self.position.y),
                          int(self.width), int(self.height))
    
    def apply_force(self, force: pygame.math.Vector2):
        """施加力(根据牛顿第二定律: F = ma)"""
        self.acceleration += force / self.mass
    
    def apply_impulse(self, impulse: pygame.math.Vector2):
        """施加冲量(瞬间改变速度)"""
        self.velocity += impulse / self.mass


class PhysicsEngine:
    """
    物理引擎
    处理重力、碰撞检测、弹道计算等
    """
    
    def __init__(self):
        self.gravity = config.PLAYER_CONFIG["gravity"]
        self.max_fall_speed = config.PLAYER_CONFIG["max_fall_speed"]
        
        # 碰撞层(用于分层碰撞检测)
        self.collision_layers: Dict[str, List[AABB]] = {
            "tiles": [],
            "entities": [],
            "projectiles": []
        }
    
    def update_body(self, body: PhysicsBody, delta_time: float):
        """
        更新物理实体
        
        Args:
            body: 物理实体
            delta_time: 时间步长(秒)
        """
        # 应用重力
        if body.gravity_enabled:
            body.acceleration.y += self.gravity
        
        # 更新速度
        body.velocity += body.acceleration * delta_time
        
        # 限制最大下落速度
        if body.velocity.y > self.max_fall_speed:
            body.velocity.y = self.max_fall_speed
        
        # 应用摩擦力(地面)
        if body.on_ground:
            body.velocity.x *= body.friction
        
        # 更新位置
        body.position += body.velocity * delta_time
        
        # 重置加速度
        body.acceleration = pygame.math.Vector2(0, 0)
    
    def check_aabb_collision(self, aabb1: AABB, aabb2: AABB) -> CollisionResult:
        """
        检测两个AABB是否碰撞
        
        Args:
            aabb1: 第一个包围盒
            aabb2: 第二个包围盒
            
        Returns:
            碰撞结果
        """
        result = CollisionResult()
        
        if not aabb1.overlaps(aabb2):
            return result
        
        # 计算重叠
        overlap_x = min(aabb1.right, aabb2.right) - max(aabb1.left, aabb2.left)
        overlap_y = min(aabb1.bottom, aabb2.bottom) - max(aabb1.top, aabb2.top)
        
        result.collided = True
        
        # 确定碰撞法线(最小重叠方向)
        if overlap_x < overlap_y:
            result.overlap = overlap_x
            # 左右碰撞
            if aabb1.center[0] < aabb2.center[0]:
                result.normal = (-1, 0)  # 从左侧碰撞
            else:
                result.normal = (1, 0)   # 从右侧碰撞
        else:
            result.overlap = overlap_y
            # 上下碰撞
            if aabb1.center[1] < aabb2.center[1]:
                result.normal = (0, -1)  # 从上方碰撞
            else:
                result.normal = (0, 1)   # 从下方碰撞
        
        # 碰撞点(两个AABB中心连线与边界交点)
        result.collision_point = (
            (aabb1.center[0] + aabb2.center[0]) / 2,
            (aabb1.center[1] + aabb2.center[1]) / 2
        )
        
        return result
    
    def resolve_collision(self, body: PhysicsBody, collision: CollisionResult):
        """
        解决碰撞(分离物体)
        
        Args:
            body: 物理实体
            collision: 碰撞结果
        """
        if not collision.collided:
            return
        
        # 沿法线方向分离
        body.position.x += collision.normal[0] * collision.overlap
        body.position.y += collision.normal[1] * collision.overlap
        
        # 修正速度(防止穿透)
        if collision.normal[0] != 0:
            body.velocity.x = 0
            body.on_wall = True
        
        if collision.normal[1] != 0:
            body.velocity.y = 0
            if collision.normal[1] < 0:  # 从上方碰撞(站在地面)
                body.on_ground = True
    
    def check_tilemap_collision(self, body: PhysicsBody, 
                                tilemap: List[List[int]],
                                tile_size: int = 32) -> List[CollisionResult]:
        """
        检测与瓦片地图的碰撞
        
        Args:
            body: 物理实体
            tilemap: 瓦片地图(2D数组, 0=空气, 1=固体)
            tile_size: 瓦片尺寸
            
        Returns:
            碰撞结果列表
        """
        collisions = []
        body_aabb = body.aabb
        
        # 计算需要检测的瓦片范围
        start_col = max(0, int(body_aabb.left // tile_size))
        end_col = min(len(tilemap[0]) - 1, int(body_aabb.right // tile_size) + 1)
        start_row = max(0, int(body_aabb.top // tile_size))
        end_row = min(len(tilemap) - 1, int(body_aabb.bottom // tile_size) + 1)
        
        # 检测每个邻近瓦片
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                if tilemap[row][col] != 0:  # 固体瓦片
                    tile_aabb = AABB(col * tile_size, row * tile_size,
                                    tile_size, tile_size)
                    collision = self.check_aabb_collision(body_aabb, tile_aabb)
                    if collision.collided:
                        collisions.append(collision)
        
        return collisions
    
    def calculate_bullet_trajectory(self, start_pos: Tuple[float, float],
                                   velocity: pygame.math.Vector2,
                                   gravity_factor: float = 0.0) -> List[Tuple[float, float]]:
        """
        计算子弹轨迹(抛物线)
        
        Args:
            start_pos: 起始位置
            velocity: 初速度向量
            gravity_factor: 重力影响因子(0=无重力, 1=完全重力)
            
        Returns:
            轨迹点列表
        """
        trajectory = [start_pos]
        pos = pygame.math.Vector2(start_pos)
        vel = velocity.copy()
        
        # 模拟最多100帧
        for _ in range(100):
            # 应用重力
            vel.y += self.gravity * gravity_factor * 0.016  # 假设60fps
            
            # 更新位置
            pos += vel * 0.016
            trajectory.append((pos.x, pos.y))
            
            # 超出屏幕则停止
            if (pos.x < 0 or pos.x > config.WINDOW_WIDTH or
                pos.y < 0 or pos.y > config.WINDOW_HEIGHT):
                break
        
        return trajectory
    
    def raycast(self, start: Tuple[float, float], 
               end: Tuple[float, float],
               obstacles: List[AABB]) -> Optional[Tuple[float, float]]:
        """
        射线投射(用于视线检测、激光瞄准等)
        
        Args:
            start: 起点
            end: 终点
            obstacles: 障碍物列表
            
        Returns:
            第一个碰撞点,如果没有碰撞返回None
        """
        direction = pygame.math.Vector2(end[0] - start[0], end[1] - start[1])
        distance = direction.length()
        
        if distance == 0:
            return None
        
        direction.normalize_ip()
        
        # 沿射线方向步进检测
        step_size = 2.0  # 每次步进2像素
        current_dist = 0
        
        while current_dist < distance:
            current_pos = (
                start[0] + direction.x * current_dist,
                start[1] + direction.y * current_dist
            )
            
            # 检测是否与障碍物碰撞
            for obstacle in obstacles:
                if obstacle.contains_point(*current_pos):
                    return current_pos
            
            current_dist += step_size
        
        return None
    
    def apply_explosion_force(self, explosion_pos: Tuple[float, float],
                             explosion_radius: float,
                             explosion_force: float,
                             bodies: List[PhysicsBody]):
        """
        应用爆炸力(影响范围内所有物体)
        
        Args:
            explosion_pos: 爆炸中心
            explosion_radius: 爆炸半径
            explosion_force: 爆炸力度
            bodies: 受影响的物理实体列表
        """
        for body in bodies:
            body_center = body.aabb.center
            
            # 计算距离
            dx = body_center[0] - explosion_pos[0]
            dy = body_center[1] - explosion_pos[1]
            distance = math.sqrt(dx * dx + dy * dy)
            
            # 在爆炸半径内
            if distance < explosion_radius and distance > 0:
                # 力度随距离衰减
                force_magnitude = explosion_force * (1 - distance / explosion_radius)
                
                # 计算力的方向
                force_direction = pygame.math.Vector2(dx, dy).normalize()
                force = force_direction * force_magnitude
                
                # 施加力
                body.apply_impulse(force)
