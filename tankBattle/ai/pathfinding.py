"""
高级路径规划算法
==============
实现A*算法、威胁评估和战术路径规划

功能：
- A*路径搜索
- 威胁地图生成
- 战术位置评估
- 动态避障
- 埋伏点识别
"""

import heapq
import math
import numpy as np
from typing import List, Tuple, Optional, Set, Dict
from dataclasses import dataclass
from enum import Enum

class TerrainType(Enum):
    """地形类型"""
    OPEN = 0
    WALL = 1
    BARRIER = 2
    COVER = 3
    DANGEROUS = 4

@dataclass
class PathNode:
    """路径节点"""
    x: int
    y: int
    g_cost: float = 0.0  # 起点到当前点的代价
    h_cost: float = 0.0  # 当前点到终点的启发式代价
    f_cost: float = 0.0  # 总代价
    parent: Optional['PathNode'] = None
    terrain_type: TerrainType = TerrainType.OPEN
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))

class AdvancedPathfinding:
    """高级路径规划算法"""
    
    def __init__(self, map_width: int = 800, map_height: int = 600, grid_size: int = 20):
        self.map_width = map_width
        self.map_height = map_height
        self.grid_size = grid_size
        self.grid_width = map_width // grid_size
        self.grid_height = map_height // grid_size
        
        # 威胁地图和缓存
        self.threat_map = np.zeros((self.grid_height, self.grid_width))
        self.terrain_cache = {}
        self.path_cache = {}
        
        # 路径搜索参数
        self.max_search_nodes = 5000
        self.cache_timeout = 60  # 缓存超时（帧数）
        
    def update_threat_map(self, bullets, enemies, player_position):
        """更新威胁地图"""
        self.threat_map.fill(0.0)
        
        # 子弹威胁
        for bullet in bullets:
            if not hasattr(bullet, 'owner'):
                continue
                
            if bullet.owner != 'enemy':
                continue
                
            bullet_pos = self._get_bullet_position(bullet)
            grid_x = int(bullet_pos[0] // self.grid_size)
            grid_y = int(bullet_pos[1] // self.grid_size)
            
            if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                # 预测子弹轨迹
                trajectory = self._predict_bullet_trajectory(bullet)
                for pos in trajectory:
                    gx, gy = int(pos[0] // self.grid_size), int(pos[1] // self.grid_size)
                    if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                        self.threat_map[gy, gx] += 0.8
        
        # 玩家威胁区域
        if player_position:
            px, py = int(player_position[0] // self.grid_size), int(player_position[1] // self.grid_size)
            if 0 <= px < self.grid_width and 0 <= py < self.grid_height:
                # 玩家周围的威胁区域
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                            distance = math.sqrt(dx*dx + dy*dy)
                            if distance <= 3:
                                threat_level = max(0, 0.6 - distance * 0.2)
                                self.threat_map[ny, nx] += threat_level
    
    def find_tactical_path(self, start: Tuple[int, int], goal: Tuple[int, int], 
                          walls, tank_size: Tuple[int, int], 
                          preferences: Dict[str, float] = None) -> List[Tuple[int, int]]:
        """寻找战术路径"""
        if preferences is None:
            preferences = {
                'safety': 0.8,      # 安全性权重
                'speed': 0.6,       # 速度权重
                'cover': 0.7,       # 掩体权重
                'stealth': 0.5      # 隐蔽性权重
            }
        
        # 转换为网格坐标
        start_grid = (int(start[0] // self.grid_size), int(start[1] // self.grid_size))
        goal_grid = (int(goal[0] // self.grid_size), int(goal[1] // self.grid_size))
        
        # 检查缓存
        cache_key = (start_grid, goal_grid, tuple(sorted(preferences.items())))
        if cache_key in self.path_cache:
            cached_path, timestamp = self.path_cache[cache_key]
            # 简化的缓存失效检查
            return cached_path
        
        # A*搜索
        open_set = []
        closed_set = set()
        nodes_expanded = 0
        
        start_node = PathNode(start_grid[0], start_grid[1])
        start_node.h_cost = self._heuristic_distance(start_grid, goal_grid)
        start_node.f_cost = start_node.h_cost
        
        heapq.heappush(open_set, start_node)
        
        while open_set and nodes_expanded < self.max_search_nodes:
            current = heapq.heappop(open_set)
            nodes_expanded += 1
            
            if (current.x, current.y) == goal_grid:
                path = self._reconstruct_path(current)
                # 缓存结果
                self.path_cache[cache_key] = (path, 0)  # 简化时间戳
                return path
            
            closed_set.add((current.x, current.y))
            
            # 检查8个方向的邻居
            for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                neighbor_x, neighbor_y = current.x + dx, current.y + dy
                
                if (neighbor_x, neighbor_y) in closed_set:
                    continue
                
                if not self._is_valid_position(neighbor_x, neighbor_y, walls, tank_size):
                    continue
                
                neighbor = PathNode(neighbor_x, neighbor_y)
                neighbor.parent = current
                
                # 计算移动代价
                move_cost = math.sqrt(dx*dx + dy*dy)
                
                # 添加地形和威胁代价
                terrain_cost = self._calculate_terrain_cost(neighbor_x, neighbor_y, walls)
                threat_cost = self._get_threat_cost(neighbor_x, neighbor_y, preferences['safety'])
                cover_bonus = self._calculate_cover_bonus(neighbor_x, neighbor_y, walls) * preferences['cover']
                
                neighbor.g_cost = current.g_cost + move_cost + terrain_cost + threat_cost - cover_bonus
                neighbor.h_cost = self._heuristic_distance((neighbor_x, neighbor_y), goal_grid)
                neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                
                # 检查开放列表中是否已有更好的路径
                better_path_exists = False
                for i, open_node in enumerate(open_set):
                    if (open_node.x, open_node.y) == (neighbor_x, neighbor_y):
                        if open_node.g_cost <= neighbor.g_cost:
                            better_path_exists = True
                        else:
                            # 移除旧节点
                            del open_set[i]
                            heapq.heapify(open_set)
                        break
                
                if not better_path_exists:
                    heapq.heappush(open_set, neighbor)
        
        return []  # 未找到路径
    
    def find_ambush_positions(self, target_position: Tuple[int, int], 
                             walls, max_distance: int = 200) -> List[Tuple[int, int]]:
        """寻找埋伏位置"""
        target_grid = (int(target_position[0] // self.grid_size), int(target_position[1] // self.grid_size))
        ambush_positions = []
        
        search_radius = int(max_distance // self.grid_size)
        
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                x, y = int(target_grid[0] + dx), int(target_grid[1] + dy)
                
                if not self._is_valid_position(x, y, walls, (40, 40)):
                    continue
                
                distance = math.sqrt(dx*dx + dy*dy) * self.grid_size
                if distance > max_distance:
                    continue
                
                # 评估埋伏价值
                ambush_score = self._evaluate_ambush_position(
                    (x * self.grid_size, y * self.grid_size),
                    target_position, walls
                )
                
                if ambush_score > 0.6:  # 阈值
                    ambush_positions.append((x * self.grid_size, y * self.grid_size))
        
        # 按分数排序
        ambush_positions.sort(
            key=lambda pos: self._evaluate_ambush_position(pos, target_position, walls), 
            reverse=True
        )
        
        return ambush_positions[:5]  # 返回最好的5个位置
    
    def plan_flanking_maneuver(self, tank_pos: Tuple[int, int], target_pos: Tuple[int, int],
                              target_angle: float, walls) -> List[Tuple[int, int]]:
        """规划侧翼包抄"""
        # 计算目标的侧翼位置
        target_front = np.array([math.cos(target_angle), math.sin(target_angle)])
        target_right = np.array([-target_front[1], target_front[0]])
        
        # 候选侧翼位置
        flank_distance = 150
        candidates = [
            np.array(target_pos) + target_right * flank_distance,  # 右侧
            np.array(target_pos) - target_right * flank_distance,  # 左侧
            np.array(target_pos) - target_front * flank_distance   # 后方
        ]
        
        best_path = []
        best_score = -1
        
        for candidate in candidates:
            candidate_pos = (int(candidate[0]), int(candidate[1]))
            
            # 检查位置有效性
            if not self._is_valid_world_position(candidate_pos, walls, (40, 40)):
                continue
            
            # 寻找到该位置的路径
            path = self.find_tactical_path(tank_pos, candidate_pos, walls, (40, 40))
            
            if path:
                # 评估侧翼位置的价值
                score = self._evaluate_flanking_position(candidate_pos, target_pos, target_angle, walls)
                
                if score > best_score:
                    best_score = score
                    best_path = path
        
        return best_path
    
    def get_safe_retreat_position(self, current_pos: Tuple[int, int], 
                                threat_source: Tuple[int, int], walls) -> Optional[Tuple[int, int]]:
        """获取安全撤退位置"""
        # 计算撤退方向（远离威胁源）
        retreat_vector = np.array(current_pos) - np.array(threat_source)
        retreat_vector = retreat_vector / np.linalg.norm(retreat_vector)
        
        # 搜索安全位置
        for distance in [80, 120, 160]:
            retreat_pos = np.array(current_pos) + retreat_vector * distance
            retreat_pos = (int(retreat_pos[0]), int(retreat_pos[1]))
            
            if self._is_valid_world_position(retreat_pos, walls, (40, 40)):
                # 检查是否足够安全
                threat_distance = np.linalg.norm(np.array(retreat_pos) - np.array(threat_source))
                if threat_distance > 150:  # 安全距离
                    return retreat_pos
        
        return None
    
    def _predict_bullet_trajectory(self, bullet) -> List[Tuple[int, int]]:
        """预测子弹轨迹"""
        trajectory = []
        
        # 获取子弹位置和速度
        bullet_pos = self._get_bullet_position(bullet)
        velocity = self._get_bullet_velocity(bullet)
        
        current_pos = np.array(bullet_pos, dtype=float)
        
        for step in range(20):  # 预测20帧
            current_pos += velocity
            trajectory.append((int(current_pos[0]), int(current_pos[1])))
            
            # 检查是否超出边界
            if (current_pos[0] < 0 or current_pos[0] >= self.map_width or
                current_pos[1] < 0 or current_pos[1] >= self.map_height):
                break
        
        return trajectory
    
    def _get_bullet_position(self, bullet) -> Tuple[int, int]:
        """获取子弹位置"""
        if hasattr(bullet, 'rect'):
            return (bullet.rect.centerx, bullet.rect.centery)
        else:
            return (getattr(bullet, 'x', 0), getattr(bullet, 'y', 0))
    
    def _get_bullet_velocity(self, bullet) -> np.ndarray:
        """获取子弹速度向量"""
        if hasattr(bullet, 'dx') and hasattr(bullet, 'dy'):
            return np.array([bullet.dx, bullet.dy])
        elif hasattr(bullet, 'angle') and hasattr(bullet, 'speed'):
            return np.array([
                math.cos(bullet.angle) * bullet.speed,
                math.sin(bullet.angle) * bullet.speed
            ])
        else:
            return np.array([0.0, 0.0])
    
    def _is_valid_position(self, grid_x: int, grid_y: int, walls, tank_size: Tuple[int, int]) -> bool:
        """检查网格位置是否有效"""
        if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
            return False
        
        # 转换为世界坐标
        world_x = grid_x * self.grid_size
        world_y = grid_y * self.grid_size
        
        return self._is_valid_world_position((world_x, world_y), walls, tank_size)
    
    def _is_valid_world_position(self, pos: Tuple[int, int], walls, tank_size: Tuple[int, int]) -> bool:
        """检查世界坐标位置是否有效"""
        if pos[0] < 0 or pos[0] >= self.map_width or pos[1] < 0 or pos[1] >= self.map_height:
            return False
        
        # 创建坦克矩形（简化版pygame.Rect）
        tank_left, tank_top = pos
        tank_right = tank_left + tank_size[0]
        tank_bottom = tank_top + tank_size[1]
        
        # 检查与墙体的碰撞
        for wall in walls:
            if hasattr(wall, 'rect'):
                wall_rect = wall.rect
                # 简化的矩形碰撞检测
                if (tank_left < wall_rect.right and tank_right > wall_rect.left and
                    tank_top < wall_rect.bottom and tank_bottom > wall_rect.top):
                    return False
        
        return True
    
    def _calculate_terrain_cost(self, grid_x: int, grid_y: int, walls) -> float:
        """计算地形代价"""
        world_x = grid_x * self.grid_size
        world_y = grid_y * self.grid_size
        
        # 基础地形代价
        base_cost = 1.0
        
        # 边缘惩罚
        edge_margin = 2
        if (grid_x < edge_margin or grid_x >= self.grid_width - edge_margin or
            grid_y < edge_margin or grid_y >= self.grid_height - edge_margin):
            base_cost += 2.0
        
        # 检查附近的墙体类型
        for wall in walls:
            if hasattr(wall, 'rect'):
                distance = math.sqrt(
                    (world_x - wall.rect.centerx)**2 + (world_y - wall.rect.centery)**2
                )
                if distance < 50:  # 50像素内
                    if hasattr(wall, 'wall_type'):
                        if wall.wall_type == 'barrier':
                            base_cost += 0.5  # 隔离墙附近稍微增加代价
                        elif wall.wall_type == 'special':
                            base_cost -= 0.3  # 特殊墙附近减少代价
        
        return base_cost
    
    def _get_threat_cost(self, grid_x: int, grid_y: int, safety_weight: float) -> float:
        """获取威胁代价"""
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.threat_map[grid_y, grid_x] * safety_weight
        return 0.0
    
    def _calculate_cover_bonus(self, grid_x: int, grid_y: int, walls) -> float:
        """计算掩体奖励"""
        world_x = grid_x * self.grid_size
        world_y = grid_y * self.grid_size
        
        cover_score = 0.0
        
        # 检查四个主要方向的掩体
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dx, dy in directions:
            for distance in range(1, 4):  # 检查3个网格的距离
                check_x = int(grid_x + dx * distance)
                check_y = int(grid_y + dy * distance)
                
                if (check_x < 0 or check_x >= self.grid_width or
                    check_y < 0 or check_y >= self.grid_height):
                    cover_score += 0.2  # 边界也算部分掩体
                    break
                
                check_world_x = check_x * self.grid_size
                check_world_y = check_y * self.grid_size
                
                for wall in walls:
                    if hasattr(wall, 'rect') and wall.rect.collidepoint(check_world_x, check_world_y):
                        cover_score += 0.5 / distance  # 距离越近，掩体价值越高
                        break
        
        return cover_score
    
    def _heuristic_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """启发式距离（对角线距离）"""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)
    
    def _reconstruct_path(self, end_node: PathNode) -> List[Tuple[int, int]]:
        """重构路径"""
        path = []
        current = end_node
        
        while current:
            # 转换回世界坐标
            world_pos = (current.x * self.grid_size, current.y * self.grid_size)
            path.append(world_pos)
            current = current.parent
        
        path.reverse()
        return path
    
    def _evaluate_ambush_position(self, pos: Tuple[int, int], target_pos: Tuple[int, int], walls) -> float:
        """评估埋伏位置价值"""
        score = 0.0
        
        # 距离目标的合适性
        distance = math.sqrt((pos[0] - target_pos[0])**2 + (pos[1] - target_pos[1])**2)
        optimal_distance = 120  # 最佳埋伏距离
        distance_score = max(0, 1.0 - abs(distance - optimal_distance) / optimal_distance)
        score += distance_score * 0.4
        
        # 掩体评估
        grid_x, grid_y = pos[0] // self.grid_size, pos[1] // self.grid_size
        cover_score = self._calculate_cover_bonus(grid_x, grid_y, walls)
        score += cover_score * 0.3
        
        # 视线清晰度
        line_of_sight = self._check_line_of_sight(pos, target_pos, walls)
        score += line_of_sight * 0.3
        
        return score
    
    def _evaluate_flanking_position(self, pos: Tuple[int, int], target_pos: Tuple[int, int], 
                                   target_angle: float, walls) -> float:
        """评估侧翼位置价值"""
        score = 0.0
        
        # 计算相对于目标朝向的角度
        to_flanker = np.array(pos) - np.array(target_pos)
        to_flanker_angle = math.atan2(to_flanker[1], to_flanker[0])
        
        angle_diff = abs((to_flanker_angle - target_angle + math.pi) % (2 * math.pi) - math.pi)
        
        # 侧面或后方位置得分更高
        if angle_diff > math.pi / 2:  # 90度以上
            score += 0.8
        elif angle_diff > math.pi / 4:  # 45-90度
            score += 0.6
        
        # 距离评估
        distance = np.linalg.norm(to_flanker)
        if 80 <= distance <= 200:  # 理想距离范围
            score += 0.2
        
        return score
    
    def _check_line_of_sight(self, pos1: Tuple[int, int], pos2: Tuple[int, int], walls) -> float:
        """检查两点间的视线清晰度"""
        # 简化的射线检测
        steps = 20
        dx = (pos2[0] - pos1[0]) / steps
        dy = (pos2[1] - pos1[1]) / steps
        
        blocked_steps = 0
        
        for i in range(1, steps):
            check_x = pos1[0] + dx * i
            check_y = pos1[1] + dy * i
            
            for wall in walls:
                if hasattr(wall, 'rect') and wall.rect.collidepoint(check_x, check_y):
                    blocked_steps += 1
                    break
        
        return max(0, 1.0 - blocked_steps / steps)
    
    def clear_cache(self):
        """清除缓存"""
        self.path_cache.clear()
        self.terrain_cache.clear()
    
    def get_debug_info(self) -> Dict:
        """获取调试信息"""
        return {
            'grid_size': f"{self.grid_width}x{self.grid_height}",
            'cached_paths': len(self.path_cache),
            'max_threat': float(np.max(self.threat_map)),
            'avg_threat': float(np.mean(self.threat_map))
        }
