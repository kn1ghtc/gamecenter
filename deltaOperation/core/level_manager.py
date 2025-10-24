"""关卡管理器 - 加载地图、生成敌人、管理检查点"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from gamecenter.deltaOperation import config
from gamecenter.deltaOperation.core.enemy import Enemy
from gamecenter.deltaOperation.core.physics import AABB, PhysicsEngine


class TileType(Enum):
    """瓦片类型"""
    EMPTY = 0
    GROUND = 1
    WALL = 2
    PLATFORM = 3
    HAZARD = 4
    CHECKPOINT = 5
    EXTRACTION = 6


@dataclass
class Checkpoint:
    """检查点数据"""
    id: int
    position: Tuple[float, float]
    activated: bool = False


@dataclass
class SpawnPoint:
    """敌人生成点"""
    position: Tuple[float, float]
    enemy_type: str
    patrol_points: List[Tuple[float, float]]


class LevelManager:
    """关卡管理器"""
    
    def __init__(self, level_id: int):
        self.level_id = level_id
        self.tilemap: List[List[int]] = []
        self.tile_size = 32
        self.width = 0
        self.height = 0
        
        self.enemies: List[Enemy] = []
        self.checkpoints: List[Checkpoint] = []
        self.spawn_points: List[SpawnPoint] = []
        
        self.player_spawn: Tuple[float, float] = (100, 100)
        self.extraction_point: Optional[Tuple[float, float]] = None
        
        self.level_bounds: AABB = AABB(0, 0, 0, 0)
        
    def load_level(self, level_path: str):
        """从JSON文件加载关卡数据"""
        try:
            with open(level_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.tilemap = data["tilemap"]
            self.height = len(self.tilemap)
            self.width = len(self.tilemap[0]) if self.height > 0 else 0
            
            self.level_bounds = AABB(
                0, 0,
                self.width * self.tile_size,
                self.height * self.tile_size
            )
            
            spawn_data = data.get("player_spawn", {"x": 100, "y": 100})
            self.player_spawn = (spawn_data["x"], spawn_data["y"])
            
            if "extraction_point" in data:
                extract = data["extraction_point"]
                self.extraction_point = (extract["x"], extract["y"])
                
            self.checkpoints = []
            for i, cp in enumerate(data.get("checkpoints", [])):
                self.checkpoints.append(Checkpoint(
                    id=i,
                    position=(cp["x"], cp["y"])
                ))
                
            self.spawn_points = []
            for sp in data.get("spawn_points", []):
                patrol = [tuple(p.values()) for p in sp.get("patrol_points", [])]
                self.spawn_points.append(SpawnPoint(
                    position=(sp["x"], sp["y"]),
                    enemy_type=sp.get("enemy_type", "grunt"),
                    patrol_points=patrol
                ))
                
        except FileNotFoundError:
            print(f"警告: 未找到关卡文件 {level_path}, 使用默认地图")
            self._create_default_level()
        except json.JSONDecodeError as e:
            print(f"警告: 关卡JSON解析失败: {e}, 使用默认地图")
            self._create_default_level()
            
    def _create_default_level(self):
        """创建默认测试关卡"""
        self.width = 30
        self.height = 20
        
        self.tilemap = [[TileType.EMPTY.value for _ in range(self.width)] 
                        for _ in range(self.height)]
        
        for x in range(self.width):
            self.tilemap[self.height - 1][x] = TileType.GROUND.value
            
        for y in range(self.height):
            self.tilemap[y][0] = TileType.WALL.value
            self.tilemap[y][self.width - 1] = TileType.WALL.value
            
        for x in range(8, 15):
            self.tilemap[12][x] = TileType.PLATFORM.value
            
        self.level_bounds = AABB(
            0, 0,
            self.width * self.tile_size,
            self.height * self.tile_size
        )
        
        self.player_spawn = (100, 100)
        self.extraction_point = (self.width * self.tile_size - 100, 100)
        
        self.checkpoints = [Checkpoint(0, (400, 300))]
        
        self.spawn_points = [
            SpawnPoint((300, 100), "grunt", [(250, 100), (350, 100)]),
            SpawnPoint((500, 100), "elite", [(450, 100), (550, 100)])
        ]
        
    def spawn_enemies(self):
        """根据生成点创建所有敌人实例"""
        self.enemies.clear()
        
        for sp in self.spawn_points:
            enemy = Enemy(sp.position[0], sp.position[1], sp.enemy_type)
            
            if sp.patrol_points:
                enemy.set_patrol_points(sp.patrol_points)
                
            self.enemies.append(enemy)
            
    def activate_checkpoint(self, player_pos: Tuple[float, float], radius: float = 50):
        """激活玩家附近的检查点"""
        for cp in self.checkpoints:
            if not cp.activated:
                dx = player_pos[0] - cp.position[0]
                dy = player_pos[1] - cp.position[1]
                dist_sq = dx*dx + dy*dy
                
                if dist_sq <= radius * radius:
                    cp.activated = True
                    return cp.id
        return None
        
    def check_extraction(self, player_pos: Tuple[float, float], radius: float = 50) -> bool:
        """检查玩家是否到达撤离点"""
        if not self.extraction_point:
            return False
            
        dx = player_pos[0] - self.extraction_point[0]
        dy = player_pos[1] - self.extraction_point[1]
        dist_sq = dx*dx + dy*dy
        
        return dist_sq <= radius * radius
        
    def get_tile_at(self, x: float, y: float) -> int:
        """获取世界坐标对应的瓦片类型"""
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)
        
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tilemap[tile_y][tile_x]
        return TileType.EMPTY.value
        
    def get_tile_aabb(self, tile_x: int, tile_y: int) -> AABB:
        """获取瓦片的AABB碰撞箱"""
        return AABB(
            tile_x * self.tile_size,
            tile_y * self.tile_size,
            self.tile_size,
            self.tile_size
        )
        
    def get_collision_tiles(self, aabb: AABB) -> List[Tuple[int, int, TileType]]:
        """获取与AABB重叠的所有固体瓦片"""
        start_x = max(0, int(aabb.x // self.tile_size))
        start_y = max(0, int(aabb.y // self.tile_size))
        end_x = min(self.width - 1, int((aabb.x + aabb.width) // self.tile_size))
        end_y = min(self.height - 1, int((aabb.y + aabb.height) // self.tile_size))
        
        tiles = []
        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                tile_type = self.tilemap[ty][tx]
                
                if tile_type in [TileType.GROUND.value, TileType.WALL.value]:
                    tiles.append((tx, ty, TileType(tile_type)))
                    
        return tiles
        
    def is_out_of_bounds(self, x: float, y: float) -> bool:
        """检查坐标是否超出关卡边界"""
        return (x < 0 or x > self.level_bounds.width or
                y < 0 or y > self.level_bounds.height)
                
    def update(self, delta_time: float, physics_engine: PhysicsEngine, players: List):
        """更新关卡逻辑(主要是敌人AI)"""
        for enemy in self.enemies[:]:
            if enemy.is_alive():
                enemy.update(delta_time, physics_engine, players)
                
    def get_alive_enemies(self) -> List[Enemy]:
        """获取所有存活敌人"""
        return [e for e in self.enemies if e.is_alive()]
        
    def render(self, surface):
        """渲染关卡(瓦片地图 + 敌人 + 检查点)"""
        import pygame
        
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tilemap[y][x]
                
                color = {
                    TileType.EMPTY.value: None,
                    TileType.GROUND.value: (100, 100, 100),
                    TileType.WALL.value: (60, 60, 60),
                    TileType.PLATFORM.value: (120, 120, 80),
                    TileType.HAZARD.value: (200, 50, 50),
                    TileType.CHECKPOINT.value: (50, 200, 50),
                    TileType.EXTRACTION.value: (50, 150, 255)
                }.get(tile_type)
                
                if color:
                    rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, (0, 0, 0), rect, 1)
                    
        for cp in self.checkpoints:
            color = (0, 255, 0) if cp.activated else (255, 255, 0)
            pygame.draw.circle(surface, color, 
                             (int(cp.position[0]), int(cp.position[1])), 20, 3)
                             
        if self.extraction_point:
            pygame.draw.rect(surface, (0, 255, 255),
                           (self.extraction_point[0] - 30, self.extraction_point[1] - 30,
                            60, 60), 4)
                            
        for enemy in self.enemies:
            enemy.render(surface)
