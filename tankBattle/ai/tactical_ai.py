"""
智能战术AI系统
=============
实现多层决策、行为预测和战场分析

功能：
- 多层决策框架
- 玩家行为预测
- 战场态势分析
- 战术执行引擎
- 性能监控
"""

import math
import random
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# 导入配置和调试设置
try:
    from ..config import AI_CONFIG
    DEBUG_CONFIG = AI_CONFIG.get('DEBUG_CONFIG', {})
except ImportError:
    AI_CONFIG = {}
    DEBUG_CONFIG = {
        'enable_ai_debug': False,
        'enable_decision_logging': False,
        'enable_shooting_debug': False,
        'enable_movement_debug': False,
        'enable_target_debug': False,
        'debug_output_frequency': 60,
        'debug_tank_id': None,
        'log_to_file': False,
        'debug_log_path': 'ai_debug.log'
    }
from collections import deque

# 条件导入机器学习组件
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("scikit-learn未安装，部分机器学习功能将不可用")

class TacticalContext(Enum):
    """战术上下文"""
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    AMBUSH = "ambush"
    RETREAT = "retreat"
    PATROL = "patrol"
    SUPPORT = "support"

@dataclass
class TacticalState:
    """战术状态"""
    position: Tuple[int, int]
    angle: float
    health_ratio: float
    ammo_status: float
    threat_level: float
    map_control: float
    objective_priority: str

class PlayerBehaviorPredictor:
    """玩家行为预测器"""
    
    def __init__(self):
        self.movement_history = deque(maxlen=50)
        self.action_patterns = {}
        self.preference_model = {
            'aggression': 0.5,
            'defensiveness': 0.5,
            'movement_speed': 0.5,
            'shooting_frequency': 0.5
        }
        
        # 机器学习分类器
        if SKLEARN_AVAILABLE:
            self.behavior_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
            self.trained = False
        else:
            self.behavior_classifier = None
            self.trained = False
    
    def update_player_data(self, player_state: Dict):
        """更新玩家数据"""
        if not player_state:
            return
            
        self.movement_history.append({
            'position': (player_state.get('x', 0), player_state.get('y', 0)),
            'angle': player_state.get('angle', 0),
            'action': player_state.get('last_action', 'none'),
            'timestamp': time.time(),
            'health': player_state.get('health', 100)
        })
        
        # 更新偏好模型
        self._update_preference_model()
        
        # 尝试训练分类器
        if SKLEARN_AVAILABLE and len(self.movement_history) >= 20:
            self._train_behavior_classifier()
    
    def _update_preference_model(self):
        """更新偏好模型"""
        if len(self.movement_history) < 5:
            return
        
        recent_actions = [entry['action'] for entry in list(self.movement_history)[-5:]]
        
        # 统计射击频率
        shoot_actions = sum(1 for action in recent_actions if 'fire' in action)
        self.preference_model['shooting_frequency'] = shoot_actions / len(recent_actions)
        
        # 统计移动模式
        move_actions = sum(1 for action in recent_actions if 'move' in action)
        self.preference_model['movement_speed'] = move_actions / len(recent_actions)
        
        # 统计攻击性
        aggressive_actions = sum(1 for action in recent_actions 
                               if action in ['fire_normal', 'fire_piercing', 'fire_explosive', 'move_forward'])
        self.preference_model['aggression'] = aggressive_actions / len(recent_actions)
        
        # 统计防守性
        defensive_actions = sum(1 for action in recent_actions 
                              if action in ['move_backward', 'rotate_left', 'rotate_right'])
        self.preference_model['defensiveness'] = defensive_actions / len(recent_actions)
    
    def _train_behavior_classifier(self):
        """训练行为分类器"""
        if not self.behavior_classifier or len(self.movement_history) < 10:
            return
        
        try:
            # 准备训练数据
            features = []
            labels = []
            
            for i in range(1, len(self.movement_history)):
                prev_entry = list(self.movement_history)[i-1]
                curr_entry = list(self.movement_history)[i]
                
                # 特征：位置变化、角度变化、时间间隔
                pos_change = (
                    curr_entry['position'][0] - prev_entry['position'][0],
                    curr_entry['position'][1] - prev_entry['position'][1]
                )
                angle_change = curr_entry['angle'] - prev_entry['angle']
                time_diff = curr_entry['timestamp'] - prev_entry['timestamp']
                
                feature = [
                    pos_change[0], pos_change[1], angle_change, time_diff,
                    curr_entry['health'], prev_entry['health']
                ]
                features.append(feature)
                labels.append(curr_entry['action'])
            
            if len(features) >= 5:  # 最少需要5个样本
                features = np.array(features)
                self.behavior_classifier.fit(features, labels)
                self.trained = True
        except Exception as e:
            print(f"行为分类器训练失败: {e}")
    
    def predict_next_action(self) -> Dict:
        """预测玩家下一个动作"""
        if len(self.movement_history) < 2:
            return {'action': 'unknown', 'confidence': 0.0}
        
        # 基于历史模式的简单预测
        recent_actions = [entry['action'] for entry in list(self.movement_history)[-5:]]
        
        if recent_actions:
            # 统计最频繁的动作
            action_counts = {}
            for action in recent_actions:
                action_counts[action] = action_counts.get(action, 0) + 1
            
            most_frequent = max(action_counts.items(), key=lambda x: x[1])
            confidence = most_frequent[1] / len(recent_actions)
            
            return {
                'action': most_frequent[0],
                'confidence': confidence,
                'predicted_position': self._predict_position(),
                'aggression_level': self.preference_model['aggression']
            }
        
        return {'action': 'unknown', 'confidence': 0.0}
    
    def _predict_position(self) -> Tuple[int, int]:
        """预测玩家位置"""
        if len(self.movement_history) < 2:
            return (0, 0)
        
        history_list = list(self.movement_history)
        last_pos = history_list[-1]['position']
        prev_pos = history_list[-2]['position']
        
        # 计算速度向量
        velocity = (last_pos[0] - prev_pos[0], last_pos[1] - prev_pos[1])
        
        # 预测位置（线性外推）
        predicted_x = last_pos[0] + velocity[0] * 3
        predicted_y = last_pos[1] + velocity[1] * 3
        
        return (int(predicted_x), int(predicted_y))

class BattlefieldAnalyzer:
    """战场分析器"""
    
    def __init__(self):
        self.heat_map = np.zeros((30, 40))  # 战场热力图
        self.control_zones = {}
        self.strategic_points = []
        self.activity_map = np.zeros((30, 40))  # 活动密度图
    
    def update_battlefield_state(self, tanks: List, bullets: List, walls: List):
        """更新战场状态"""
        # 重置热力图
        self.heat_map.fill(0)
        self.activity_map *= 0.95  # 衰减历史活动
        
        # 标记坦克控制区域
        for tank in tanks:
            self._mark_control_zone(tank)
            self._mark_activity(tank)
        
        # 标记危险区域（子弹轨迹）
        for bullet in bullets:
            self._mark_danger_zone(bullet)
        
        # 识别战略要点
        self._identify_strategic_points(walls)
    
    def _mark_control_zone(self, tank):
        """标记坦克控制区域"""
        grid_x = getattr(tank, 'x', 0) // 20
        grid_y = getattr(tank, 'y', 0) // 20
        
        # 坦克周围的控制区域
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                nx, ny = grid_x + dx, grid_y + dy
                if 0 <= nx < 40 and 0 <= ny < 30:
                    distance = math.sqrt(dx*dx + dy*dy)
                    influence = max(0, 1.0 - distance / 3.0)
                    
                    # 根据坦克类型设置影响
                    owner = getattr(tank, 'owner', 'unknown')
                    if owner == 'enemy':
                        self.heat_map[ny, nx] += influence
                    else:
                        self.heat_map[ny, nx] -= influence
    
    def _mark_activity(self, tank):
        """标记活动密度"""
        grid_x = getattr(tank, 'x', 0) // 20
        grid_y = getattr(tank, 'y', 0) // 20
        
        if 0 <= grid_x < 40 and 0 <= grid_y < 30:
            self.activity_map[grid_y, grid_x] += 0.1
    
    def _mark_danger_zone(self, bullet):
        """标记子弹危险区域"""
        bullet_x = getattr(bullet, 'x', 0) if hasattr(bullet, 'x') else getattr(bullet, 'rect', type('obj', (object,), {'centerx': 0})).centerx
        bullet_y = getattr(bullet, 'y', 0) if hasattr(bullet, 'y') else getattr(bullet, 'rect', type('obj', (object,), {'centery': 0})).centery
        
        grid_x = bullet_x // 20
        grid_y = bullet_y // 20
        
        if 0 <= grid_x < 40 and 0 <= grid_y < 30:
            owner = getattr(bullet, 'owner', 'unknown')
            if owner != 'enemy':  # 对AI来说，非敌方子弹是威胁
                self.heat_map[grid_y, grid_x] += 0.5
    
    def _identify_strategic_points(self, walls):
        """识别战略要点"""
        # 简化实现：识别关键通道和掩体位置
        self.strategic_points.clear()
        
        # 查找狭窄通道
        for y in range(1, 29):
            for x in range(1, 39):
                if self._is_chokepoint(x, y, walls):
                    self.strategic_points.append({
                        'type': 'chokepoint',
                        'position': (x * 20, y * 20),
                        'importance': 0.8
                    })
    
    def _is_chokepoint(self, grid_x: int, grid_y: int, walls) -> bool:
        """判断是否是关键通道"""
        # 简化的通道检测逻辑
        open_directions = 0
        
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            check_x, check_y = grid_x + dx, grid_y + dy
            if 0 <= check_x < 40 and 0 <= check_y < 30:
                # 检查是否有墙
                world_x, world_y = check_x * 20, check_y * 20
                blocked = False
                
                for wall in walls:
                    if hasattr(wall, 'rect') and wall.rect.collidepoint(world_x, world_y):
                        blocked = True
                        break
                
                if not blocked:
                    open_directions += 1
        
        # 如果只有1-2个方向开放，可能是关键通道
        return open_directions <= 2
    
    def get_safest_position(self, current_pos: Tuple[int, int], 
                          search_radius: int = 100) -> Tuple[int, int]:
        """获取最安全的位置"""
        grid_x = current_pos[0] // 20
        grid_y = current_pos[1] // 20
        
        min_threat = float('inf')
        safest_pos = current_pos
        
        search_range = search_radius // 20
        
        for dy in range(-search_range, search_range + 1):
            for dx in range(-search_range, search_range + 1):
                nx, ny = grid_x + dx, grid_y + dy
                if 0 <= nx < 40 and 0 <= ny < 30:
                    threat_level = self.heat_map[ny, nx]
                    if threat_level < min_threat:
                        min_threat = threat_level
                        safest_pos = (nx * 20, ny * 20)
        
        return safest_pos
    
    def identify_ambush_opportunities(self, enemy_positions: List[Tuple[int, int]]) -> List[Dict]:
        """识别伏击机会"""
        opportunities = []
        
        for enemy_pos in enemy_positions:
            # 分析敌人周围的地形
            grid_x, grid_y = enemy_pos[0] // 20, enemy_pos[1] // 20
            
            # 检查周围的威胁等级
            if 0 <= grid_x < 40 and 0 <= grid_y < 30:
                local_threat = self.heat_map[max(0, grid_y-2):min(30, grid_y+3), 
                                           max(0, grid_x-2):min(40, grid_x+3)]
                
                avg_threat = np.mean(local_threat)
                
                if avg_threat < 0.3:  # 低威胁区域适合伏击
                    opportunities.append({
                        'target_position': enemy_pos,
                        'threat_level': avg_threat,
                        'priority': 1.0 - avg_threat
                    })
        
        # 按优先级排序
        opportunities.sort(key=lambda x: x['priority'], reverse=True)
        return opportunities[:3]  # 返回前3个机会
    
    def evaluate_position_control(self, position: Tuple[int, int]) -> float:
        """评估位置控制价值"""
        grid_x, grid_y = position[0] // 20, position[1] // 20
        
        if not (0 <= grid_x < 40 and 0 <= grid_y < 30):
            return 0.0
        
        # 考虑热力图值和活动密度
        control_value = abs(self.heat_map[grid_y, grid_x])
        activity_value = self.activity_map[grid_y, grid_x]
        
        return (control_value + activity_value) / 2

class TargetIdentificationSystem:
    """目标识别和分类系统"""
    
    def __init__(self):
        self.target_priorities = {
            'player': 100,
            'player_base': 90,
            'enemy_base': 10,  # 己方基地，避免攻击
            'friendly_tank': 5,  # 友方坦克，避免攻击
            'special_wall': 30,
            'barrier_wall': 25,
            'normal_wall': 15
        }
        
    def identify_targets(self, tank, game_state):
        """识别所有可见目标并分类"""
        targets = {
            'primary': None,
            'secondary': [],
            'obstacles': [],
            'threats': [],
            'avoid': []  # 需要避免攻击的目标
        }
        
        tank_pos = (tank.x + tank.size[0]//2, tank.y + tank.size[1]//2)
        
        # 识别玩家
        if game_state.get('player'):
            player = game_state['player']
            player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
            distance = self._calculate_distance(tank_pos, player_pos)
            
            targets['primary'] = {
                'type': 'player',
                'object': player,
                'position': player_pos,
                'distance': distance,
                'priority': self.target_priorities['player'],
                'threat_level': self._assess_threat_level(tank, player)
            }
        
        # 识别基地
        environment_manager = game_state.get('environment_manager')
        if environment_manager:
            # 玩家基地（攻击目标）
            if environment_manager.player_base:
                base_pos = (environment_manager.player_base.rect.centerx, 
                           environment_manager.player_base.rect.centery)
                distance = self._calculate_distance(tank_pos, base_pos)
                
                targets['secondary'].append({
                    'type': 'player_base',
                    'object': environment_manager.player_base,
                    'position': base_pos,
                    'distance': distance,
                    'priority': self.target_priorities['player_base']
                })
            
            # 己方基地（避免攻击）
            if environment_manager.enemy_base:
                base_pos = (environment_manager.enemy_base.rect.centerx,
                           environment_manager.enemy_base.rect.centery)
                distance = self._calculate_distance(tank_pos, base_pos)
                
                targets['avoid'].append({
                    'type': 'enemy_base',
                    'object': environment_manager.enemy_base,
                    'position': base_pos,
                    'distance': distance,
                    'priority': self.target_priorities['enemy_base']
                })
        
        # 识别其他AI坦克（友方）
        # 注意：这需要在调用时传入所有AI坦克列表
        if 'all_enemies' in game_state:
            for enemy_tank in game_state['all_enemies']:
                if enemy_tank != tank and enemy_tank.health > 0:  # 不包括自己
                    enemy_pos = (enemy_tank.x + enemy_tank.size[0]//2,
                                enemy_tank.y + enemy_tank.size[1]//2)
                    distance = self._calculate_distance(tank_pos, enemy_pos)
                    
                    targets['avoid'].append({
                        'type': 'friendly_tank',
                        'object': enemy_tank,
                        'position': enemy_pos,
                        'distance': distance,
                        'priority': self.target_priorities['friendly_tank']
                    })
        
        # 识别特殊墙体
        if 'special_walls' in game_state:
            for wall in game_state['special_walls']:
                if wall.health > 0:
                    wall_pos = (wall.rect.centerx, wall.rect.centery)
                    distance = self._calculate_distance(tank_pos, wall_pos)
                    
                    if distance <= 200:  # 只考虑近距离的特殊墙体
                        targets['secondary'].append({
                            'type': 'special_wall',
                            'object': wall,
                            'position': wall_pos,
                            'distance': distance,
                            'priority': self.target_priorities['special_wall']
                        })
        
        return targets
    
    def select_best_target(self, targets, tank_bullet_types, tank_position):
        """选择最佳攻击目标"""
        # 优先级：玩家 > 玩家基地 > 特殊墙体 > 普通障碍
        
        # 首先检查主要目标（玩家）
        if targets['primary']:
            player_target = targets['primary']
            # 检查是否在射程内且有合适的子弹
            if self._can_engage_target(player_target, tank_bullet_types, tank_position):
                return player_target
        
        # 其次检查次要目标
        viable_targets = []
        for target in targets['secondary']:
            if self._can_engage_target(target, tank_bullet_types, tank_position):
                viable_targets.append(target)
        
        # 按优先级和距离排序
        if viable_targets:
            viable_targets.sort(key=lambda t: (t['priority'], -t['distance']), reverse=True)
            return viable_targets[0]
        
        return None
    
    def _calculate_distance(self, pos1, pos2):
        """计算两点间距离"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _assess_threat_level(self, tank, player):
        """评估玩家威胁等级"""
        tank_pos = (tank.x + tank.size[0]//2, tank.y + tank.size[1]//2)
        player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
        
        distance = self._calculate_distance(tank_pos, player_pos)
        
        # 距离威胁
        distance_threat = max(0, 1.0 - distance / 300.0)
        
        # 瞄准威胁
        dx = tank_pos[0] - player_pos[0]
        dy = tank_pos[1] - player_pos[1]
        angle_to_tank = math.atan2(dy, dx)
        angle_diff = abs((player.angle - angle_to_tank + math.pi) % (2 * math.pi) - math.pi)
        aiming_threat = max(0, 1.0 - angle_diff / (math.pi / 3))
        
        # 生命值威胁
        health_threat = (100 - player.health) / 100.0
        
        return (distance_threat + aiming_threat + health_threat) / 3.0
    
    def _can_engage_target(self, target, available_bullets, tank_position):
        """判断是否可以攻击目标"""
        distance = target['distance']
        target_type = target['type']
        
        # 距离检查
        if distance > 400:  # 超出最大攻击距离
            return False
        
        # 根据目标类型和可用子弹判断
        if target_type in ['player', 'player_base']:
            # 攻击玩家或玩家基地，任何子弹都可以
            return len(available_bullets) > 0
        elif target_type == 'special_wall':
            # 攻击特殊墙体，需要考虑收益
            return 'HEAVY' in available_bullets or distance <= 150
        elif target_type in ['barrier_wall', 'normal_wall']:
            # 攻击墙体，穿甲弹最好，其他也可以
            return True
        
        return False

class AimingControlSystem:
    """瞄准和射击控制系统"""
    
    def __init__(self):
        self.aim_precision = {
            'NORMAL': 0.1,      # 普通弹需要较高精度
            'PIERCING': 0.15,   # 穿甲弹可以稍微放松
            'EXPLOSIVE': 0.2,   # 爆炸弹精度要求最低
            'RAPID': 0.12,      # 快速弹精度中等
            'HEAVY': 0.08,      # 重弹需要很高精度
            'BARRICADE': 0.25   # 掩体弹精度要求最低
        }
        
        self.max_rotation_speed = 0.1  # 最大旋转速度
        self.min_rotation_speed = 0.02  # 最小旋转速度
        
    def calculate_aim_angle(self, tank_pos, target_pos, target_velocity=None):
        """计算瞄准角度，包括预判"""
        dx = target_pos[0] - tank_pos[0]
        dy = target_pos[1] - tank_pos[1]
        
        # 基础角度
        base_angle = math.atan2(dy, dx)
        
        # 如果有目标速度信息，进行预判
        if target_velocity:
            distance = math.sqrt(dx*dx + dy*dy)
            bullet_speed = 8  # 假设子弹速度
            time_to_target = distance / bullet_speed
            
            # 预判位置
            predicted_x = target_pos[0] + target_velocity[0] * time_to_target
            predicted_y = target_pos[1] + target_velocity[1] * time_to_target
            
            # 重新计算角度
            dx = predicted_x - tank_pos[0]
            dy = predicted_y - tank_pos[1]
            base_angle = math.atan2(dy, dx)
        
        return base_angle
    
    def get_rotation_command(self, current_angle, target_angle, bullet_type='NORMAL'):
        """获取旋转命令"""
        # 计算角度差
        angle_diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi
        
        # 获取所需精度
        required_precision = self.aim_precision.get(bullet_type, 0.1)
        
        # 如果角度差足够小，不需要旋转
        if abs(angle_diff) <= required_precision:
            return 0.0, True  # rotation, aimed
        
        # 计算旋转速度（距离目标角度越远，转得越快）
        rotation_speed = min(self.max_rotation_speed, 
                           max(self.min_rotation_speed, abs(angle_diff) * 0.5))
        
        # 确定旋转方向
        if angle_diff > 0:
            return rotation_speed, False
        else:
            return -rotation_speed, False
    
    def should_fire(self, current_angle, target_angle, bullet_type, target_info):
        """判断是否应该开火 - 修复过于严格的射击条件"""
        angle_diff = abs((target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi)
        
        # 大幅放宽瞄准精度要求，让AI更容易开火
        required_precision = self.aim_precision.get(bullet_type, 0.3)  # 从0.1提高到0.3
        if bullet_type == 'EXPLOSIVE':
            required_precision = 0.4  # 爆炸弹可以更不准确
        elif bullet_type == 'NORMAL':
            required_precision = 0.25  # 普通弹稍微严格一点
        
        # 调试输出
        if DEBUG_CONFIG.get('enable_shooting_debug', False):
            tank_id = getattr(self, 'tank_id', 'unknown')
            if DEBUG_CONFIG.get('debug_tank_id') is None or tank_id == DEBUG_CONFIG.get('debug_tank_id'):
                print(f"[射击调试] 坦克{tank_id}: 角度差={angle_diff:.3f}, 要求精度={required_precision:.3f}, 目标类型={target_info['type']}")
        
        # 基础瞄准检查 - 放宽条件
        if angle_diff > required_precision:
            if DEBUG_CONFIG.get('enable_shooting_debug', False):
                print(f"[射击调试] 拒绝射击: 角度差过大 {angle_diff:.3f} > {required_precision:.3f}")
            return False
        
        # 更精确的友方目标检查 - 只检查真正的友方目标
        target_type = target_info['type']
        if target_type in ['friendly_tank']:  # 移除了过于宽泛的检查
            if DEBUG_CONFIG.get('enable_shooting_debug', False):
                print(f"[射击调试] 拒绝射击: 友方目标 {target_type}")
            return False
        
        # 放宽距离限制，让AI在更远距离也能开火
        distance = target_info['distance']
        min_distance = 15  # 从30降低到15
        max_distance = 450  # 从400提高到450
        
        if distance < min_distance:
            if DEBUG_CONFIG.get('enable_shooting_debug', False):
                print(f"[射击调试] 拒绝射击: 距离过近 {distance:.1f} < {min_distance}")
            return False
        
        if distance > max_distance:
            if DEBUG_CONFIG.get('enable_shooting_debug', False):
                print(f"[射击调试] 拒绝射击: 距离过远 {distance:.1f} > {max_distance}")
            return False
        
        # 额外的积极射击策略
        if target_type == 'player':
            # 对玩家目标更加积极
            if distance < 200:
                if DEBUG_CONFIG.get('enable_shooting_debug', False):
                    print(f"[射击调试] 积极射击: 玩家目标在近距离 {distance:.1f}")
                return True
        
        if DEBUG_CONFIG.get('enable_shooting_debug', False):
            print(f"[射击调试] 允许射击: 角度={angle_diff:.3f}, 距离={distance:.1f}, 目标={target_type}")
        
        return True
    
    def get_optimal_bullet_for_target(self, target_info, available_bullets):
        """为目标选择最佳子弹类型"""
        target_type = target_info['type']
        distance = target_info['distance']
        
        # 根据目标类型优先选择
        if target_type == 'player':
            # 攻击玩家：近距离用爆炸弹，远距离用穿甲弹，中距离用快速弹
            if distance <= 100 and 'EXPLOSIVE' in available_bullets:
                return 'EXPLOSIVE'
            elif distance >= 200 and 'PIERCING' in available_bullets:
                return 'PIERCING'
            elif 'RAPID' in available_bullets:
                return 'RAPID'
            elif 'NORMAL' in available_bullets:
                return 'NORMAL'
        
        elif target_type == 'player_base':
            # 攻击玩家基地：优先重弹和爆炸弹
            if 'HEAVY' in available_bullets:
                return 'HEAVY'
            elif 'EXPLOSIVE' in available_bullets:
                return 'EXPLOSIVE'
            elif 'NORMAL' in available_bullets:
                return 'NORMAL'
        
        elif target_type == 'special_wall':
            # 攻击特殊墙体：优先重弹
            if 'HEAVY' in available_bullets:
                return 'HEAVY'
            elif 'EXPLOSIVE' in available_bullets:
                return 'EXPLOSIVE'
            elif 'NORMAL' in available_bullets:
                return 'NORMAL'
        
        elif target_type in ['barrier_wall', 'normal_wall']:
            # 攻击墙体：穿甲弹最好
            if 'PIERCING' in available_bullets:
                return 'PIERCING'
            elif 'HEAVY' in available_bullets:
                return 'HEAVY'
            elif 'NORMAL' in available_bullets:
                return 'NORMAL'
        
        # 默认返回第一个可用的子弹
        return available_bullets[0] if available_bullets else 'NORMAL'

class SmartTankAI:
    """智能坦克AI主控制器"""
    
    def __init__(self, tank_instance):
        self.tank = tank_instance
        
        # 添加调试配置
        self.debug_enabled = DEBUG_CONFIG.get('enable_ai_debug', False)
        self.decision_logging = DEBUG_CONFIG.get('enable_decision_logging', False)
        self.shooting_debug = DEBUG_CONFIG.get('enable_shooting_debug', False)
        self.movement_debug = DEBUG_CONFIG.get('enable_movement_debug', False)
        self.target_debug = DEBUG_CONFIG.get('enable_target_debug', False)
        self.debug_frequency = DEBUG_CONFIG.get('debug_output_frequency', 60)
        self.debug_tank_id = DEBUG_CONFIG.get('debug_tank_id', None)
        
        # 为坦克分配一个简单的ID用于调试
        self.tank_id = f"{id(tank_instance) % 10000}"
        
        # 核心组件
        self.behavior_predictor = PlayerBehaviorPredictor()
        self.battlefield_analyzer = BattlefieldAnalyzer()
        
        # 目标识别和追踪系统
        self.target_system = TargetIdentificationSystem()
        
        # 瞄准和射击控制系统
        self.aiming_system = AimingControlSystem()
        # 为瞄准系统设置tank_id用于调试
        self.aiming_system.tank_id = self.tank_id
        
        # 尝试导入高级组件
        try:
            from .reinforcement_learning import TankRLAgent
            from .pathfinding import AdvancedPathfinding
            
            self.rl_agent = TankRLAgent()
            self.pathfinder = AdvancedPathfinding()
            self.has_advanced_components = True
            
            # 启用在线学习
            self.training_enabled = True
            self.last_state = None
            self.last_action = None
            self.episode_rewards = []
            self.training_episode = 0
            
        except ImportError:
            self.rl_agent = None
            self.pathfinder = None
            self.has_advanced_components = False
            self.training_enabled = False
            print("高级AI组件未加载，使用基础智能系统")
        
        # 决策层系统
        self.decision_layers = {
            'strategic': self._strategic_decision,
            'tactical': self._tactical_decision,
            'operational': self._operational_decision,
            'reactive': self._reactive_decision
        }
        
        # 状态跟踪
        self.current_strategy = TacticalContext.PATROL
        self.target_priority_queue = []
        self.threat_assessment = {}
        self.tactical_memory = deque(maxlen=100)
        
        # 性能监控
        self.performance_metrics = {
            'decisions_made': 0,
            'successful_actions': 0,
            'average_decision_time': 0.0,
            'hits_scored': 0,
            'damage_taken': 0
        }
        
        # 训练统计和奖励机制
        self.training_stats = {
            'episodes_completed': 0,
            'total_reward': 0.0,
            'average_reward': 0.0,
            'successful_hits': 0,
            'wall_effects_acquired': 0,
            'barriers_navigated': 0,
            'special_wall_destroyed': 0
        }
        
        # 用于计算奖励的状态跟踪
        self.previous_health = getattr(tank_instance, 'health', 100)
        self.previous_player_health = 100
        self.previous_position = self._get_tank_position()
        self.stuck_timer = 0
        self.last_position = self.previous_position
        
        # 决策计时 - 优化AI响应速度
        self.last_decision_time = 0
        self.decision_interval = 1  # 每帧都做决策，更快响应
        self.decision_counter = 0
        
        # AI攻击性和机动性配置
        self.aggression_level = 0.8  # 高攻击性
        self.movement_confidence = 0.7  # 移动自信度
        self.shooting_eagerness = 0.9  # 射击积极性
        self.pursuit_persistence = 0.8  # 追击坚持度
    
    def update_ai(self, player, walls, bullet_manager, environment_manager):
        """主要AI更新入口 - 优化为每帧更新，更快响应"""
        self.decision_counter += 1
        
        # 每帧都进行决策，不再限制频率以提高响应速度
        # if self.decision_counter < self.decision_interval:
        #     return
        
        # self.decision_counter = 0  # 保留计数器用于其他用途
        
        start_time = time.perf_counter()
        
        try:
            # 1. 收集情报
            game_state = self._gather_intelligence(player, walls, bullet_manager, environment_manager)
            
            # 2. 更新战场分析 - 降低频率以保持性能
            if self.decision_counter % 2 == 0:  # 每2帧更新一次战场分析
                self._update_battlefield_analysis(player, walls, bullet_manager)
            
            # 3. 预测玩家行为 - 降低频率
            if self.decision_counter % 3 == 0:  # 每3帧更新一次行为预测
                self._update_player_prediction(player)
            
            # 4. 强化学习训练（如果启用）- 降低频率
            if self.training_enabled and self.has_advanced_components and self.rl_agent and self.decision_counter % 5 == 0:
                self._update_training(game_state, player, walls, bullet_manager, environment_manager)
            
            # 5. 多层决策 - 每帧都进行，确保快速响应
            if self.has_advanced_components and self.rl_agent:
                # 使用强化学习决策
                final_action = self._rl_decision(game_state, player, walls, bullet_manager, environment_manager)
            else:
                # 使用规则决策
                final_action = self._multi_layer_decision(game_state)
            
            # 6. 执行动作 - 每帧都执行
            self._execute_action(final_action, player, walls, bullet_manager, environment_manager)
            
            # 7. 更新性能指标 - 降低频率
            if self.decision_counter % 10 == 0:  # 每10帧更新一次性能指标
                decision_time = time.perf_counter() - start_time
                self._update_performance_metrics(decision_time, final_action)
            
        except Exception as e:
            print(f"AI决策错误: {e}")
            # 回退到基础行为
            self._execute_fallback_behavior(player, walls, bullet_manager)
    
    def get_decision(self, game_state):
        """
        获取AI决策 - 主要接口方法，集成新的目标识别和瞄准系统
        
        Args:
            game_state (dict): 包含游戏状态的字典
                - player: 玩家坦克实例
                - walls: 墙体列表
                - environment_manager: 环境管理器
                - bullet_manager: 子弹管理器
        
        Returns:
            dict: 决策结果字典
                - move_forward: 前进距离 (-1到1)
                - rotate: 旋转角度 (弧度)
                - fire: 是否射击 (bool)
        """
        try:
            player = game_state.get('player')
            walls = game_state.get('walls', [])
            environment_manager = game_state.get('environment_manager')
            bullet_manager = game_state.get('bullet_manager')
            
            if not player or player.health <= 0:
                return {'move_forward': 0, 'rotate': 0, 'fire': False}
            
            # 调试计数器初始化
            if not hasattr(self, '_debug_counter'):
                self._debug_counter = 0
            self._debug_counter += 1
            
            # 获取坦克当前子弹类型和可用类型
            available_bullets = self._get_available_bullets()
            current_bullet = self._get_current_bullet_type()
            
            # 扩展游戏状态以包含其他AI坦克信息
            extended_game_state = game_state.copy()
            extended_game_state['all_enemies'] = getattr(game_state.get('environment_manager'), 'all_enemies', [])
            extended_game_state['special_walls'] = getattr(game_state.get('environment_manager'), 'special_walls', [])
            
            # 使用目标识别系统
            targets = self.target_system.identify_targets(self.tank, extended_game_state)
            best_target = self.target_system.select_best_target(targets, available_bullets, self._get_tank_position())
            
            if not best_target:
                # 没有有效目标，执行巡逻行为
                return self._patrol_behavior()
            
            # 获取坦克位置和角度
            tank_pos = self._get_tank_position()
            current_angle = self.tank.angle
            
            # 计算目标角度（包含预判）
            target_velocity = self._estimate_target_velocity(best_target)
            target_angle = self.aiming_system.calculate_aim_angle(
                tank_pos, best_target['position'], target_velocity
            )
            
            # 选择最佳子弹类型
            optimal_bullet = self.aiming_system.get_optimal_bullet_for_target(best_target, available_bullets)
            
            # 切换到最佳子弹类型
            if optimal_bullet != current_bullet and optimal_bullet in available_bullets:
                self._switch_bullet_type(optimal_bullet)
            
            # 获取旋转命令
            rotation, aimed = self.aiming_system.get_rotation_command(current_angle, target_angle, optimal_bullet)
            
            # 判断是否开火
            should_fire = aimed and self.aiming_system.should_fire(
                current_angle, target_angle, optimal_bullet, best_target
            )
            
            # 移动决策
            move_forward = self._calculate_movement(best_target, aimed, targets)
            
            decision = {
                'move_forward': move_forward,
                'rotate': rotation,
                'fire': should_fire
            }
            
            # 调试输出 - 条件性打印，受调试开关控制
            if (self.debug_enabled and 
                self._debug_counter % self.debug_frequency == 0 and
                (self.debug_tank_id is None or self.tank_id == self.debug_tank_id)):
                
                print(f"AI坦克[{self.tank_id}]({tank_pos[0]:.0f},{tank_pos[1]:.0f}) 智能决策:")
                print(f"  目标: {best_target['type']} 距离:{best_target['distance']:.0f}")
                print(f"  子弹: {current_bullet} -> {optimal_bullet}")
                print(f"  瞄准: {'已瞄准' if aimed else '调整中'}")
                print(f"  决策: 移动={move_forward:.1f}, 旋转={rotation:.2f}, 射击={should_fire}")
                
                # 输出威胁信息
                if targets['avoid'] and self.target_debug:
                    avoid_list = [t['type'] for t in targets['avoid']]
                    print(f"  避免攻击: {avoid_list}")
                
                # 射击调试详情
                if self.shooting_debug and not should_fire and aimed:
                    print(f"  射击被拒绝原因: 检查should_fire方法")
                
                # 移动调试详情
                if self.movement_debug:
                    print(f"  移动详情: 目标距离={best_target['distance']:.0f}, 是否瞄准={aimed}")
            
            return decision
            
        except Exception as e:
            print(f"AI决策异常: {e}")
            return {'move_forward': 0, 'rotate': 0, 'fire': False}
    
    def _get_available_bullets(self):
        """获取可用的子弹类型"""
        if hasattr(self.tank, 'available_bullet_types'):
            return self.tank.available_bullet_types
        else:
            return ['NORMAL']  # 默认只有普通子弹
    
    def _get_current_bullet_type(self):
        """获取当前子弹类型"""
        return getattr(self.tank, 'bullet_type', 'NORMAL')
    
    def _switch_bullet_type(self, bullet_type):
        """切换子弹类型"""
        if hasattr(self.tank, 'bullet_type') and bullet_type in self._get_available_bullets():
            self.tank.bullet_type = bullet_type
    
    def _get_tank_position(self):
        """获取坦克位置"""
        return (self.tank.x + self.tank.size[0]//2, self.tank.y + self.tank.size[1]//2)
    
    def _estimate_target_velocity(self, target):
        """估算目标速度"""
        # 简单实现：只对玩家估算速度
        if target['type'] == 'player' and hasattr(self, 'player_position_history'):
            if len(self.player_position_history) >= 2:
                recent_pos = self.player_position_history[-1]
                previous_pos = self.player_position_history[-2]
                return (recent_pos[0] - previous_pos[0], recent_pos[1] - previous_pos[1])
        
        return None
    
    def _patrol_behavior(self):
        """巡逻行为"""
        # 简单的巡逻：缓慢旋转寻找目标
        if not hasattr(self, 'patrol_direction'):
            self.patrol_direction = random.choice([-1, 1])
        
        if not hasattr(self, 'patrol_timer'):
            self.patrol_timer = 0
        
        self.patrol_timer += 1
        
        # 每120帧改变一次巡逻方向
        if self.patrol_timer >= 120:
            self.patrol_direction = random.choice([-1, 1])
            self.patrol_timer = 0
        
        return {
            'move_forward': 0,
            'rotate': self.patrol_direction * 0.03,  # 缓慢旋转
            'fire': False
        }
    
    def _calculate_movement(self, target, aimed, targets):
        """计算移动决策"""
        distance = target['distance']
        target_type = target['type']
        
        # 检查是否需要避开友方目标
        for avoid_target in targets['avoid']:
            if avoid_target['distance'] < 80:  # 太近了，需要远离
                # 计算远离方向
                tank_pos = self._get_tank_position()
                avoid_pos = avoid_target['position']
                dx = tank_pos[0] - avoid_pos[0]
                dy = tank_pos[1] - avoid_pos[1]
                
                # 如果朝向友方目标，后退
                angle_to_avoid = math.atan2(dy, dx)
                current_angle = self.tank.angle
                angle_diff = abs((current_angle - angle_to_avoid + math.pi) % (2 * math.pi) - math.pi)
                
                if angle_diff < math.pi / 2:  # 朝向友方目标
                    return -0.5  # 后退
        
        # 根据目标类型和距离决定移动
        if target_type == 'player':
            if distance > 200:
                return 0.8 if aimed else 0.3  # 接近玩家
            elif distance < 80:
                return -0.4  # 保持距离
            else:
                return 0.1 if aimed else 0.5  # 微调位置
        
        elif target_type == 'player_base':
            if distance > 100:
                return 0.6 if aimed else 0.4  # 接近基地
            else:
                return 0.0  # 停下来射击
        
        elif target_type == 'special_wall':
            if distance > 150:
                return 0.4  # 接近特殊墙体
            else:
                return 0.0  # 停下来射击
        
        return 0.0
    
    def _convert_action_to_decision(self, action):
        """将AI动作转换为决策格式"""
        if not action:
            return {'move_forward': 0, 'rotate': 0, 'fire': False}
        
        # 如果action已经是决策格式，直接返回
        if isinstance(action, dict) and 'move_forward' in action:
            # 确保所有必需的键都存在
            decision = {
                'move_forward': action.get('move_forward', 0),
                'rotate': action.get('rotate', 0),
                'fire': action.get('fire', False)
            }
            return decision
        
        # 转换强化学习动作格式 {'type': 'xxx', ...}
        if isinstance(action, dict) and 'type' in action:
            decision = {'move_forward': 0, 'rotate': 0, 'fire': False}
            
            action_type = action.get('type', '')
            
            if action_type == 'move':
                direction = action.get('direction', 'forward')
                if direction == 'forward':
                    decision['move_forward'] = 1
                elif direction == 'backward':
                    decision['move_forward'] = -1
                    
            elif action_type == 'rotate':
                direction = action.get('direction', 'right')
                if direction == 'right':
                    decision['rotate'] = 0.05  # 右转
                elif direction == 'left':
                    decision['rotate'] = -0.05  # 左转
                    
            elif action_type == 'fire':
                decision['fire'] = True
                
            elif action_type == 'wait':
                # 保持静止
                pass
                
            return decision
        
        # 兼容旧格式转换
        decision = {
            'move_forward': action.get('move', 0),
            'rotate': action.get('turn', 0) * 0.05,  # 转换为弧度
            'fire': action.get('fire', False)
        }
        
        return decision
    
    def _gather_intelligence(self, player, walls, bullet_manager, environment_manager) -> Dict:
        """收集战场情报"""
        tank_pos = self._get_tank_position()
        
        game_state = {
            'tank_position': tank_pos,
            'tank_health': self.tank.health,
            'tank_angle': self.tank.angle,
            'can_fire': getattr(self.tank, 'can_fire', lambda: True)(),
            'player': player,
            'walls': walls,
            'bullets': bullet_manager.get_bullets() if bullet_manager else [],
            'environment': environment_manager,
            'immediate_threats': self._assess_immediate_threats(bullet_manager),
            'strategic_targets': self._identify_strategic_targets(player, environment_manager)
        }
        
        return game_state
    
    def _get_tank_position(self) -> Tuple[int, int]:
        """获取坦克位置"""
        if hasattr(self.tank, 'rect'):
            return (self.tank.rect.centerx, self.tank.rect.centery)
        else:
            return (self.tank.x + self.tank.size[0]//2, self.tank.y + self.tank.size[1]//2)
    
    def _assess_immediate_threats(self, bullet_manager) -> List[Dict]:
        """评估即时威胁"""
        threats = []
        tank_pos = self._get_tank_position()
        
        if bullet_manager:
            for bullet in bullet_manager.get_bullets():
                if getattr(bullet, 'owner', '') != 'enemy':
                    continue
                
                bullet_pos = self._get_bullet_position(bullet)
                distance = math.sqrt(
                    (tank_pos[0] - bullet_pos[0])**2 + 
                    (tank_pos[1] - bullet_pos[1])**2
                )
                
                if distance < 150:  # 威胁距离
                    threats.append({
                        'type': 'bullet',
                        'position': bullet_pos,
                        'distance': distance,
                        'severity': 1.0 - distance / 150.0
                    })
        
        return threats
    
    def _get_bullet_position(self, bullet) -> Tuple[int, int]:
        """获取子弹位置"""
        if hasattr(bullet, 'rect'):
            return (bullet.rect.centerx, bullet.rect.centery)
        else:
            return (getattr(bullet, 'x', 0), getattr(bullet, 'y', 0))
    
    def _identify_strategic_targets(self, player, environment_manager) -> List[Dict]:
        """识别战略目标"""
        targets = []
        
        # 玩家目标
        if player and player.health > 0:
            player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
            targets.append({
                'type': 'player',
                'position': player_pos,
                'priority': 0.8,
                'health': player.health
            })
        
        # 玩家基地目标
        if environment_manager and hasattr(environment_manager, 'player_base'):
            if environment_manager.player_base:
                base = environment_manager.player_base
                targets.append({
                    'type': 'player_base',
                    'position': (base.rect.centerx, base.rect.centery),
                    'priority': 0.9,
                    'health': base.health
                })
        
        # 特殊墙体目标识别
        if hasattr(self.tank, 'game_manager') and hasattr(self.tank.game_manager, 'special_walls'):
            special_walls = self.tank.game_manager.special_walls
            for wall in special_walls:
                if wall.health > 0:
                    effect_priority = self._evaluate_special_effect_priority(wall.effect_type)
                    if effect_priority > 0.3:  # 只考虑有价值的特殊效果
                        targets.append({
                            'type': 'special_wall',
                            'position': (wall.rect.centerx, wall.rect.centery),
                            'priority': effect_priority,
                            'health': wall.health,
                            'effect_type': wall.effect_type
                        })
        
        # 隔离墙通道识别
        if environment_manager and hasattr(environment_manager, 'barrier_passages'):
            passages = getattr(environment_manager, 'barrier_passages', [])
            for passage in passages:
                targets.append({
                    'type': 'barrier_passage',
                    'position': (passage['x'], passage['y']),
                    'priority': 0.6,
                    'width': passage.get('width', 50),
                    'height': passage.get('height', 50)
                })
        
        return targets
    
    def _evaluate_special_effect_priority(self, effect_type: str) -> float:
        """评估特殊效果的优先级"""
        effect_priorities = {
            'piercing_ammo': 0.8,      # 穿甲弹 - 高优先级
            'explosive_ammo': 0.7,     # 爆炸弹 - 高优先级
            'speed_boost': 0.6,        # 速度提升 - 中等优先级
            'multi_shot': 0.7,         # 多重射击 - 高优先级
            'shield': 0.5,             # 护盾 - 中等优先级
            'health_swap': 0.3,        # 生命互换 - 低优先级（风险高）
            'teleport': 0.4,           # 传送 - 中等优先级
            'wall_destroyer': 0.6,     # 围墙消除 - 中等优先级
            'ghost_mode': 0.5,         # 幽灵模式 - 中等优先级
            'normal': 0.0              # 普通墙体 - 无优先级
        }
        return effect_priorities.get(effect_type, 0.0)
    
    def _update_battlefield_analysis(self, player, walls, bullet_manager):
        """更新战场分析"""
        tanks = [self.tank]
        if player:
            tanks.append(player)
        
        bullets = bullet_manager.get_bullets() if bullet_manager else []
        
        self.battlefield_analyzer.update_battlefield_state(tanks, bullets, walls)
    
    def _update_player_prediction(self, player):
        """更新玩家行为预测"""
        if player:
            player_state = {
                'x': player.x,
                'y': player.y,
                'angle': player.angle,
                'health': player.health,
                'last_action': getattr(player, 'last_action', 'none')
            }
            self.behavior_predictor.update_player_data(player_state)
    
    def _rl_decision(self, game_state: Dict, player, walls, bullet_manager, environment_manager) -> Dict:
        """强化学习决策"""
        try:
            # 提取状态特征
            state_vector = self.rl_agent.get_state(
                self.tank, player, walls, 
                bullet_manager.get_bullets() if bullet_manager else [],
                environment_manager
            )
            
            # 选择动作（训练模式会有探索）
            action_idx = self.rl_agent.act(state_vector, training=self.training_enabled)
            
            # 存储当前动作用于训练
            if self.training_enabled:
                self.last_action = action_idx
            
            # 转换为动作字典
            action_map = {
                0: {'type': 'move', 'direction': 'forward'},
                1: {'type': 'move', 'direction': 'backward'},
                2: {'type': 'rotate', 'direction': 'left'},
                3: {'type': 'rotate', 'direction': 'right'},
                4: {'type': 'fire', 'bullet_type': 'normal'},
                5: {'type': 'fire', 'bullet_type': 'piercing'},
                6: {'type': 'fire', 'bullet_type': 'explosive'},
                7: {'type': 'wait'}
            }
            
            selected_action = action_map.get(action_idx, {'type': 'wait'})
            
            # 增强特殊墙体和隔离墙处理
            if self.training_enabled:
                selected_action = self._enhance_action_with_tactical_intelligence(
                    selected_action, game_state
                )
            
            return selected_action
            
        except Exception as e:
            print(f"强化学习决策失败: {e}")
            return self._multi_layer_decision(game_state)
    
    def _multi_layer_decision(self, game_state: Dict) -> Dict:
        """多层决策系统 - 简化版本确保正常工作"""
        try:
            # 简单但有效的决策逻辑
            player = game_state.get('player')
            tank_pos = game_state.get('tank_position', (0, 0))
            
            if not player:
                # 无玩家时巡逻
                return {
                    'move_forward': random.choice([0, 1, -1]),
                    'rotate': random.uniform(-0.1, 0.1),
                    'fire': False
                }
            
            # 计算到玩家的距离和角度
            player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
            dx = player_pos[0] - tank_pos[0]
            dy = player_pos[1] - tank_pos[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 基于距离的决策
            if distance < 200:
                # 近距离 - 攻击
                return {
                    'move_forward': 1 if distance > 80 else -0.5,  # 太近时后退
                    'rotate': random.uniform(-0.15, 0.15),
                    'fire': True
                }
            elif distance < 400:
                # 中距离 - 追击
                return {
                    'move_forward': 1,
                    'rotate': random.uniform(-0.1, 0.1),
                    'fire': random.random() < 0.4
                }
            else:
                # 远距离 - 巡逻靠近
                return {
                    'move_forward': random.choice([1, 0]),
                    'rotate': random.uniform(-0.2, 0.2),
                    'fire': random.random() < 0.2
                }
                
        except Exception as e:
            print(f"简化决策错误: {e}")
            # 回退到基础随机行为
            return {
                'move_forward': random.choice([0, 1, -1]),
                'rotate': random.uniform(-0.15, 0.15),
                'fire': random.random() < 0.3
            }
    
    def _strategic_decision(self, game_state: Dict) -> Dict:
        """战略层决策 - 优化为更主动的攻击策略"""
        # 检查基地状态 - 降低阈值，更积极攻击基地
        player_base_health = 100
        if game_state.get('environment'):
            env = game_state['environment']
            if hasattr(env, 'player_base') and env.player_base:
                player_base_health = env.player_base.health
        
        if player_base_health < 50:  # 从30提高到50，更早开始攻击基地
            return {
                'strategy': 'finish_base',
                'priority': 0.95,  # 提高优先级
                'action_type': 'attack_base'
            }
        
        # 检查玩家威胁 - 降低阈值，更积极攻击玩家
        player = game_state.get('player')
        if player and player.health < 50:  # 从30提高到50
            return {
                'strategy': 'finish_player',
                'priority': 0.9,  # 提高优先级
                'action_type': 'hunt_player'
            }
        
        # 即使在平衡状态下也更偏向攻击
        return {
            'strategy': 'aggressive_balanced',  # 更名为攻击性平衡
            'priority': 0.7,  # 提高默认优先级
            'action_type': 'aggressive_adaptive'  # 更攻击性的适应策略
        }
    
    def _tactical_decision(self, game_state: Dict) -> Dict:
        """战术层决策"""
        # 分析战术形势
        tank_pos = game_state['tank_position']
        immediate_threats = game_state.get('immediate_threats', [])
        strategic_targets = game_state.get('strategic_targets', [])
        
        if immediate_threats:
            # 有即时威胁，考虑撤退
            high_severity_threats = [t for t in immediate_threats if t['severity'] > 0.7]
            if high_severity_threats:
                safe_pos = self.battlefield_analyzer.get_safest_position(tank_pos)
                return {
                    'tactic': 'retreat',
                    'target_position': safe_pos,
                    'priority': 0.9,
                    'urgent': True
                }
        
        # 优先考虑特殊墙体目标
        special_wall_targets = [t for t in strategic_targets if t['type'] == 'special_wall']
        if special_wall_targets:
            # 选择最有价值且最近的特殊墙体
            best_special_wall = self._select_best_special_wall_target(tank_pos, special_wall_targets)
            if best_special_wall:
                return {
                    'tactic': 'acquire_special_effect',
                    'target_position': best_special_wall['position'],
                    'target_type': 'special_wall',
                    'effect_type': best_special_wall.get('effect_type', 'unknown'),
                    'priority': best_special_wall['priority'],
                    'action_type': 'attack_wall'
                }
        
        # 检查是否需要使用隔离墙通道
        player_targets = [t for t in strategic_targets if t['type'] == 'player']
        barrier_passages = [t for t in strategic_targets if t['type'] == 'barrier_passage']
        
        if player_targets and barrier_passages:
            player_pos = player_targets[0]['position']
            # 检查玩家是否在隔离墙另一侧
            if self._is_player_behind_barrier(tank_pos, player_pos, game_state.get('walls', [])):
                # 寻找最近的通道
                nearest_passage = self._find_nearest_barrier_passage(tank_pos, barrier_passages)
                if nearest_passage:
                    return {
                        'tactic': 'use_barrier_passage',
                        'target_position': nearest_passage['position'],
                        'target_type': 'barrier_passage',
                        'priority': 0.7,
                        'final_target': player_pos
                    }
        
        # 检查伏击机会
        if player_targets:
            opportunities = self.battlefield_analyzer.identify_ambush_opportunities(
                tank_pos, player_targets[0]['position']
            )
            if opportunities:
                return {
                    'tactic': 'ambush',
                    'target_position': opportunities[0],
                    'priority': 0.6
                }
        
        return {
            'tactic': 'patrol',
            'priority': 0.3
        }
    
    def _select_best_special_wall_target(self, tank_pos: Tuple[int, int], special_walls: List[Dict]) -> Optional[Dict]:
        """选择最佳特殊墙体目标"""
        if not special_walls:
            return None
        
        scored_walls = []
        for wall in special_walls:
            wall_pos = wall['position']
            distance = math.sqrt((tank_pos[0] - wall_pos[0])**2 + (tank_pos[1] - wall_pos[1])**2)
            
            # 计算综合评分：优先级 - 距离惩罚 + 效果奖励
            score = wall['priority']
            score -= min(distance / 300.0, 0.5)  # 距离惩罚，最大0.5
            
            # 根据当前坦克状态调整效果奖励
            if self.tank.health < 50:
                # 血量低时优先护盾和生命相关效果
                if wall.get('effect_type') == 'shield':
                    score += 0.3
                elif wall.get('effect_type') == 'health_swap' and hasattr(self.tank.game_manager, 'player') and self.tank.game_manager.player.health > self.tank.health:
                    score += 0.2
            
            scored_walls.append((score, wall))
        
        # 返回评分最高的墙体
        scored_walls.sort(key=lambda x: x[0], reverse=True)
        return scored_walls[0][1] if scored_walls else None
    
    def _is_player_behind_barrier(self, tank_pos: Tuple[int, int], player_pos: Tuple[int, int], walls: List) -> bool:
        """检查玩家是否在隔离墙另一侧"""
        # 简化的射线检测：检查坦克到玩家的直线路径上是否有高血量墙体
        dx = player_pos[0] - tank_pos[0]
        dy = player_pos[1] - tank_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 50:  # 距离太近，不考虑隔离墙
            return False
        
        # 归一化方向向量
        step_x = dx / distance * 10
        step_y = dy / distance * 10
        
        # 沿路径检查墙体
        steps = int(distance / 10)
        for i in range(1, steps):
            check_x = tank_pos[0] + step_x * i
            check_y = tank_pos[1] + step_y * i
            
            for wall in walls:
                if hasattr(wall, 'rect') and wall.rect.collidepoint(check_x, check_y):
                    # 检查是否是高血量墙体（可能是隔离墙）
                    if hasattr(wall, 'health') and wall.health > 200:
                        return True
                    # 检查是否标记为隔离墙
                    if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                        return True
        
        return False
    
    def _find_nearest_barrier_passage(self, tank_pos: Tuple[int, int], passages: List[Dict]) -> Optional[Dict]:
        """寻找最近的隔离墙通道"""
        if not passages:
            return None
        
        nearest_passage = None
        min_distance = float('inf')
        
        for passage in passages:
            passage_pos = passage['position']
            distance = math.sqrt((tank_pos[0] - passage_pos[0])**2 + (tank_pos[1] - passage_pos[1])**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_passage = passage
        
        return nearest_passage
    
    def _update_training(self, game_state: Dict, player, walls, bullet_manager, environment_manager):
        """更新强化学习训练"""
        if not self.rl_agent or not self.training_enabled:
            return
        
        try:
            current_state = self.rl_agent.get_state(
                self.tank, player, walls, 
                bullet_manager.get_bullets() if bullet_manager else [],
                environment_manager
            )
            
            # 计算奖励
            reward = self._calculate_reward(game_state, player, walls, environment_manager)
            
            # 如果有上一步的状态和动作，存储经验
            if self.last_state is not None and self.last_action is not None:
                # 检查是否完成一个episode（如任何一方死亡）
                done = (self.tank.health <= 0 or 
                       (player and player.health <= 0))
                
                self.rl_agent.remember(
                    self.last_state, self.last_action, reward, current_state, done
                )
                
                # 如果经验足够，进行训练
                if len(self.rl_agent.memory) > self.rl_agent.batch_size:
                    self.rl_agent.replay()
                
                # Episode结束处理
                if done:
                    self._end_training_episode(reward)
            
            # 更新状态
            self.last_state = current_state
            self.training_stats['total_reward'] += reward
            
            # 定期保存模型
            if self.training_stats['episodes_completed'] % 100 == 0 and self.training_stats['episodes_completed'] > 0:
                self._save_training_progress()
                
        except Exception as e:
            print(f"训练更新错误: {e}")
    
    def _calculate_reward(self, game_state: Dict, player, walls, environment_manager) -> float:
        """计算强化学习奖励"""
        reward = 0.0
        
        try:
            current_health = self.tank.health
            current_position = self._get_tank_position()
            
            # 1. 生存奖励
            reward += 0.1
            
            # 2. 伤害奖励/惩罚
            health_change = current_health - self.previous_health
            if health_change < 0:
                reward += health_change * 0.01  # 受伤惩罚
            
            # 3. 对玩家造成伤害的奖励
            if player:
                player_health_change = player.health - self.previous_player_health
                if player_health_change < 0:
                    reward += abs(player_health_change) * 0.02  # 击中玩家奖励
                    self.training_stats['successful_hits'] += 1
            
            # 4. 位置移动奖励（防止卡住）
            position_change = math.sqrt(
                (current_position[0] - self.last_position[0])**2 + 
                (current_position[1] - self.last_position[1])**2
            )
            if position_change < 5:  # 几乎没有移动
                self.stuck_timer += 1
                if self.stuck_timer > 20:  # 卡住太久
                    reward -= 0.05
            else:
                self.stuck_timer = 0
                reward += min(position_change * 0.001, 0.02)  # 移动奖励
            
            # 5. 特殊墙体效果奖励
            strategic_targets = game_state.get('strategic_targets', [])
            special_wall_targets = [t for t in strategic_targets if t['type'] == 'special_wall']
            
            # 检查是否接近特殊墙体
            for target in special_wall_targets:
                target_pos = target['position']
                distance = math.sqrt(
                    (current_position[0] - target_pos[0])**2 + 
                    (current_position[1] - target_pos[1])**2
                )
                if distance < 100:  # 接近特殊墙体
                    reward += 0.01 * target['priority']
            
            # 6. 隔离墙绕行奖励
            barrier_passages = [t for t in strategic_targets if t['type'] == 'barrier_passage']
            if barrier_passages and player:
                player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
                if self._is_player_behind_barrier(current_position, player_pos, walls):
                    # 正在绕行，给予奖励
                    for passage in barrier_passages:
                        passage_pos = passage['position']
                        distance = math.sqrt(
                            (current_position[0] - passage_pos[0])**2 + 
                            (current_position[1] - passage_pos[1])**2
                        )
                        if distance < 80:  # 接近通道
                            reward += 0.03
                            self.training_stats['barriers_navigated'] += 1
            
            # 7. 死亡严重惩罚
            if current_health <= 0:
                reward -= 10.0
            
            # 8. 击杀玩家大奖励
            if player and player.health <= 0 and self.previous_player_health > 0:
                reward += 20.0
            
            # 更新之前状态
            self.previous_health = current_health
            self.previous_player_health = player.health if player else 100
            self.last_position = current_position
            
            return reward
            
        except Exception as e:
            print(f"奖励计算错误: {e}")
            return 0.0
    
    def _end_training_episode(self, final_reward: float):
        """结束训练episode"""
        self.training_episode += 1
        self.training_stats['episodes_completed'] += 1
        self.episode_rewards.append(final_reward)
        
        # 计算平均奖励
        if len(self.episode_rewards) > 100:
            self.episode_rewards.pop(0)  # 保持最近100个episode
        
        self.training_stats['average_reward'] = sum(self.episode_rewards) / len(self.episode_rewards)
        
        # 重置episode状态
        self.last_state = None
        self.last_action = None
        
        # 每10个episode打印训练进度
        if self.training_episode % 10 == 0:
            print(f"训练Episode {self.training_episode}: 平均奖励={self.training_stats['average_reward']:.2f}, "
                  f"ε={self.rl_agent.epsilon:.3f}")
    
    def _save_training_progress(self):
        """保存训练进度"""
        try:
            import os
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            os.makedirs(models_dir, exist_ok=True)
            
            model_path = os.path.join(models_dir, 'tank_rl_model.pth')
            self.rl_agent.save_model(model_path)
            
            # 保存训练统计
            stats_path = os.path.join(models_dir, 'training_stats.json')
            import json
            with open(stats_path, 'w') as f:
                json.dump(self.training_stats, f, indent=2)
            
            print(f"模型已保存到 {model_path}")
            
        except Exception as e:
            print(f"保存模型失败: {e}")
    
    def get_training_status(self) -> Dict:
        """获取训练状态"""
        if not self.training_enabled:
            return {'training_enabled': False}
        
        status = {
            'training_enabled': True,
            'episodes_completed': self.training_stats['episodes_completed'],
            'average_reward': self.training_stats['average_reward'],
            'successful_hits': self.training_stats['successful_hits'],
            'wall_effects_acquired': self.training_stats['wall_effects_acquired'],
            'barriers_navigated': self.training_stats['barriers_navigated']
        }
        
        if self.rl_agent:
            rl_stats = self.rl_agent.get_training_stats()
            status.update(rl_stats)
        
        return status
    
    def _enhance_action_with_tactical_intelligence(self, base_action: Dict, game_state: Dict) -> Dict:
        """用战术智能增强基础动作"""
        strategic_targets = game_state.get('strategic_targets', [])
        tank_pos = game_state.get('tank_position', (0, 0))
        
        # 检查是否有高优先级特殊墙体目标
        special_wall_targets = [t for t in strategic_targets 
                               if t['type'] == 'special_wall' and t['priority'] > 0.6]
        
        if special_wall_targets:
            nearest_special_wall = min(special_wall_targets, 
                                     key=lambda t: math.sqrt(
                                         (tank_pos[0] - t['position'][0])**2 + 
                                         (tank_pos[1] - t['position'][1])**2
                                     ))
            
            distance = math.sqrt(
                (tank_pos[0] - nearest_special_wall['position'][0])**2 + 
                (tank_pos[1] - nearest_special_wall['position'][1])**2
            )
            
            # 如果非常接近特殊墙体，强制攻击
            if distance < 80:
                base_action = {'type': 'fire', 'bullet_type': 'normal'}
        
        # 检查隔离墙绕行需求
        player = game_state.get('player')
        if player:
            player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
            walls = game_state.get('walls', [])
            
            if self._is_player_behind_barrier(tank_pos, player_pos, walls):
                barrier_passages = [t for t in strategic_targets if t['type'] == 'barrier_passage']
                if barrier_passages:
                    nearest_passage = self._find_nearest_barrier_passage(tank_pos, barrier_passages)
                    if nearest_passage:
                        passage_distance = math.sqrt(
                            (tank_pos[0] - nearest_passage['position'][0])**2 + 
                            (tank_pos[1] - nearest_passage['position'][1])**2
                        )
                        
                        # 如果距离通道较近，优先移动到通道
                        if passage_distance < 150:
                            base_action = {'type': 'move', 'direction': 'forward'}
        
        return base_action
        
        return {
            'tactic': 'advance',
            'priority': 0.6
        }
    
    def _operational_decision(self, game_state: Dict) -> Dict:
        """作战层决策 - 优化为更主动的攻击"""
        player = game_state.get('player')
        tank_pos = game_state['tank_position']
        
        # 更积极的射击策略
        if game_state.get('can_fire', False) and player:
            player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
            distance = math.sqrt((player_pos[0] - tank_pos[0])**2 + (player_pos[1] - tank_pos[1])**2)
            
            # 扩大射击范围，更容易开火
            if distance < 400 and self._can_hit_target(tank_pos, player_pos, game_state.get('walls', [])):
                return {
                    'operation': 'engage_target',
                    'target': 'player',
                    'priority': 0.95,  # 大幅提高射击优先级
                    'bullet_type': 'explosive' if distance < 150 else 'piercing'  # 根据距离选择弹药
                }
        
        # 更主动的移动策略
        if player:
            player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
            distance = math.sqrt((player_pos[0] - tank_pos[0])**2 + (player_pos[1] - tank_pos[1])**2)
            
            # 主动寻求接敌
            if distance > 100:  # 距离较远时主动靠近
                return {
                    'operation': 'advance_to_contact',
                    'target': 'player',
                    'priority': 0.8
                }
            elif distance < 50:  # 距离过近时后退以获得射击角度
                return {
                    'operation': 'fighting_withdrawal',
                    'target': 'player', 
                    'priority': 0.7
                }
        
        return {
            'operation': 'aggressive_patrol',  # 更名为攻击性巡逻
            'priority': 0.6  # 提高默认优先级
        }
    
    def _reactive_decision(self, game_state: Dict) -> Dict:
        """反应层决策"""
        immediate_threats = game_state.get('immediate_threats', [])
        
        if immediate_threats:
            closest_threat = min(immediate_threats, key=lambda t: t['distance'])
            
            if closest_threat['distance'] < 50:
                return {
                    'reaction': 'emergency_evasion',
                    'threat': closest_threat,
                    'priority': 1.0,
                    'urgent': True
                }
        
        return {
            'reaction': 'normal',
            'priority': 0.1
        }
    
    def _can_hit_target(self, tank_pos: Tuple[int, int], target_pos: Tuple[int, int], walls) -> bool:
        """检查是否可以命中目标"""
        # 简化的视线检查
        dx = target_pos[0] - tank_pos[0]
        dy = target_pos[1] - tank_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 300:  # 超出有效射程
            return False
        
        # 检查是否有障碍物阻挡
        steps = 10
        step_x = dx / steps
        step_y = dy / steps
        
        for i in range(1, steps):
            check_x = tank_pos[0] + step_x * i
            check_y = tank_pos[1] + step_y * i
            
            for wall in walls:
                if hasattr(wall, 'rect') and wall.rect.collidepoint(check_x, check_y):
                    return False
        
        return True
    
    def _combine_decisions(self, decisions: Dict) -> Dict:
        """合并决策结果 - 返回标准决策格式，优化为更主动的行为"""
        # 找到优先级最高的决策
        best_decision = None
        max_priority = 0
        
        for layer_name, decision in decisions.items():
            if decision and decision.get('priority', 0) > max_priority:
                best_decision = decision
                max_priority = decision.get('priority', 0)
        
        if not best_decision:
            # 返回更主动的默认决策
            return {'move_forward': 1, 'rotate': 0.05, 'fire': True}
        
        # 根据决策类型转换为标准格式，提高所有动作的积极性
        action_type = best_decision.get('action_type', 'wait')
        operation = best_decision.get('operation', '')
        
        if action_type in ['attack_base', 'hunt_player'] or operation == 'engage_target':
            # 积极攻击策略 - 更主动
            return {
                'move_forward': 1,  # 持续向前移动
                'rotate': random.uniform(-0.08, 0.08),  # 适度转向寻找目标
                'fire': True  # 积极开火
            }
        elif operation == 'advance_to_contact':
            # 主动接敌
            return {
                'move_forward': 1,  # 前进
                'rotate': random.uniform(-0.12, 0.12),  # 寻找最佳攻击角度
                'fire': random.random() < 0.8  # 80%几率开火
            }
        elif operation == 'fighting_withdrawal':
            # 战斗撤退
            return {
                'move_forward': -1,  # 后退
                'rotate': random.uniform(-0.15, 0.15),  # 保持机动
                'fire': True  # 边退边打
            }
        elif action_type in ['aggressive_adaptive', 'aggressive_balanced'] or operation == 'aggressive_patrol':
            # 攻击性适应策略
            return {
                'move_forward': random.choice([1, 1, 0]),  # 66%概率前进，33%停止
                'rotate': random.uniform(-0.12, 0.12),  # 主动搜索
                'fire': random.random() < 0.7  # 70%几率开火
            }
        elif action_type == 'retreat':
            return {
                'move_forward': -1,  # 后退
                'rotate': random.uniform(-0.2, 0.2),  # 快速机动
                'fire': random.random() < 0.6  # 60%几率开火
            }
        else:
            # 默认行为 - 比原来更主动
            return {
                'move_forward': random.choice([1, 1, 0]),  # 66%概率前进
                'rotate': random.uniform(-0.1, 0.1),
                'fire': random.random() < 0.6  # 60%几率开火，比原来的40%更高
            }
    
    def _execute_action(self, action: Dict, player, walls, bullet_manager, environment_manager):
        """执行决策动作"""
        if not action:
            return
        
        action_type = action.get('type', 'wait')
        
        try:
            if action_type == 'move':
                direction = action.get('direction', 'forward')
                if direction == 'forward':
                    self.tank.move(1, walls)
                elif direction == 'backward':
                    self.tank.move(-1, walls)
            
            elif action_type == 'rotate':
                direction = action.get('direction', 'left')
                if direction == 'left':
                    self.tank.rotate(-1)
                elif direction == 'right':
                    self.tank.rotate(1)
            
            elif action_type == 'fire':
                if self.tank.can_fire():
                    bullet_type = action.get('bullet_type', 'normal')
                    original_type = getattr(self.tank, 'bullet_type', 'NORMAL')
                    
                    # 切换子弹类型
                    if bullet_type == 'piercing':
                        self.tank.bullet_type = 'PIERCING'
                    elif bullet_type == 'explosive':
                        self.tank.bullet_type = 'EXPLOSIVE'
                    else:
                        self.tank.bullet_type = 'NORMAL'
                    
                    # 射击
                    bullets = self.tank.fire()
                    if bullets and bullet_manager:
                        for bullet in bullets:
                            bullet_manager.add_bullet(bullet)
                    
                    # 恢复原始子弹类型
                    self.tank.bullet_type = original_type
            
            # 记录动作到记忆中
            self.tactical_memory.append({
                'action': action,
                'timestamp': time.time(),
                'tank_position': self._get_tank_position(),
                'result': 'executed'
            })
            
        except Exception as e:
            print(f"动作执行失败: {e}")
    
    def _execute_fallback_behavior(self, player, walls, bullet_manager):
        """执行回退行为"""
        # 简单的回退AI行为
        if player and player.health > 0:
            tank_pos = self._get_tank_position()
            player_pos = (player.x + player.size[0]//2, player.y + player.size[1]//2)
            
            # 计算到玩家的角度
            dx = player_pos[0] - tank_pos[0]
            dy = player_pos[1] - tank_pos[1]
            target_angle = math.atan2(dy, dx)
            
            angle_diff = target_angle - self.tank.angle
            
            # 调整角度
            if abs(angle_diff) > 0.1:
                if angle_diff > 0:
                    self.tank.rotate(1)
                else:
                    self.tank.rotate(-1)
            else:
                # 角度合适，尝试射击或移动
                if self.tank.can_fire() and random.random() < 0.3:
                    bullets = self.tank.fire()
                    if bullets and bullet_manager:
                        for bullet in bullets:
                            bullet_manager.add_bullet(bullet)
                elif random.random() < 0.5:
                    self.tank.move(1, walls)
    
    def _update_performance_metrics(self, decision_time: float, action: Dict):
        """更新性能指标"""
        self.performance_metrics['decisions_made'] += 1
        
        # 更新平均决策时间
        old_avg = self.performance_metrics['average_decision_time']
        count = self.performance_metrics['decisions_made']
        self.performance_metrics['average_decision_time'] = (old_avg * (count - 1) + decision_time) / count
        
        # 记录最大决策时间
        if decision_time > 0.05:  # 50ms以上的决策时间
            print(f"AI决策时间过长: {decision_time:.3f}秒")
    
    def get_ai_status(self) -> Dict:
        """获取AI状态信息"""
        return {
            'current_strategy': self.current_strategy.value,
            'has_advanced_components': self.has_advanced_components,
            'performance_metrics': self.performance_metrics.copy(),
            'memory_size': len(self.tactical_memory),
            'player_prediction': self.behavior_predictor.predict_next_action()
        }
