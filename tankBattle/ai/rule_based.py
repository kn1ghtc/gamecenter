"""
规则AI
======
提供两种规则难度：
- easy: 直接锁定玩家或基地，A* 绕障靠近，能打就打，不能打就清障。
- medium: 在 easy 基础上，优先争取有利的特殊墙效果（穿甲/爆炸/多发/护盾/加速），主要以消灭玩家为目标。

该AI使用上帝视角：可以访问所有墙、玩家/基地状态、特殊墙与通道信息。

接口与 SmartTankAI 保持一致：提供 get_decision(game_state) → dict。
"""
import math
import random
from typing import Dict, Any, Optional, List, Tuple

try:
    from .pathfinding import AdvancedPathfinding
    PATH_OK = True
except Exception:
    PATH_OK = False

PREFERRED_EFFECTS = [
    'piercing_ammo', 'explosive_ammo', 'multi_shot', 'shield', 'speed_boost'
]


class RuleBasedAI:
    def __init__(self, tank_instance, mode: str = 'easy'):
        self.tank = tank_instance
        self.mode = mode  # 'easy' | 'medium'
        self.pathfinder = AdvancedPathfinding() if PATH_OK else None
        self.current_path: List[Tuple[int, int]] = []
        self.path_step = 0
        
        # 路径规划超时和强制移动机制
        self.path_stale_frames = 0  # 当前路径使用了多少帧
        self.no_movement_frames = 0  # 连续多少帧没有有效移动
        self.last_position = (0, 0)  # 上一帧的位置
        self.max_path_stale_frames = 180  # 路径最大使用时间（3秒@60fps）
        self.max_no_movement_frames = 120  # 最大原地停留时间（2秒@60fps）
        self.force_clear_obstacles = False  # 是否强制清障模式

    def get_decision(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        player = game_state.get('player')
        walls = game_state.get('walls', [])
        env = game_state.get('environment_manager')
        special_walls = game_state.get('special_walls', [])

        tank_cx = self.tank.x + self.tank.size[0] // 2
        tank_cy = self.tank.y + self.tank.size[1] // 2
        tank_pos = (tank_cx, tank_cy)

        # 监控移动状态
        self._update_movement_tracking(tank_pos)

        # 1) 目标选择
        target_pos, target_type = self._choose_target(player, env, special_walls, tank_pos)

        # 2) 角度与直线可打判断
        fire_ok, angle_to_target, distance = self._can_fire_line(walls, tank_pos, target_pos)

        # 3) 检查是否需要强制清障或强制移动
        if self._should_force_action():
            return self._get_force_action(walls, tank_pos, angle_to_target, target_pos)

        # 4) 移动与路径规划
        move_forward = 0
        rotate = 0
        
        if fire_ok:
            # 可以直打时：对准目标并靠近
            angle_diff = self._angle_diff(self.tank.angle, angle_to_target)
            if abs(angle_diff) > 0.12:
                rotate = 3 if angle_diff > 0 else -3
            else:
                # 保持适当距离，不要太近也不要太远
                if distance > 180:
                    move_forward = 1
                elif distance < 80:
                    move_forward = -1  # 后退
                else:
                    move_forward = 0  # 保持距离
        else:
            # 不能直打时：使用路径规划或直接朝目标前进
            move_forward, rotate = self._handle_pathfinding(tank_pos, target_pos, walls, angle_to_target)

        # 5) 清障逻辑（easy/medium 均适用）
        fire = False
        if not fire_ok:
            blocking = self._find_blocking_wall_to_target(walls, tank_pos, angle_to_target)
            if blocking is not None:
                # 瞄准该墙体快速清除
                bx, by = blocking
                wall_angle = math.atan2(by - tank_cy, bx - tank_cx)
                diff = self._angle_diff(self.tank.angle, wall_angle)
                if abs(diff) > 0.15:
                    rotate = 3 if diff > 0 else -3
                else:
                    fire = True

        # 6) 开火判定
        if fire_ok and abs(self._angle_diff(self.tank.angle, angle_to_target)) <= 0.2:
            fire = True

        return {
            'move_forward': move_forward,
            'rotate': rotate,
            'fire': fire
        }

    def _choose_target(self, player, env, special_walls, tank_pos):
        # hard 需求不在此文件处理。此处处理 easy/medium
        # easy: 先打玩家基地（若存在），否则跟踪玩家
        # medium: 主要打玩家；若附近存在高价值特殊墙则先去拿
        if self.mode == 'medium' and special_walls:
            sw = self._pick_best_special(special_walls, tank_pos)
            if sw is not None:
                return (sw[0], sw[1]), 'special'

        if env and getattr(env, 'player_base', None):
            base = env.player_base
            if base and base.health > 0:
                return (base.rect.centerx, base.rect.centery), 'player_base'

        if player and player.health > 0:
            pcx = player.x + player.size[0] // 2
            pcy = player.y + player.size[1] // 2
            return (pcx, pcy), 'player'

        if env and getattr(env, 'enemy_base', None):
            base = env.enemy_base
            return (base.rect.centerx, base.rect.centery), 'fallback_base'

        return tank_pos, 'none'

    def _pick_best_special(self, special_walls, tank_pos):
        # 选择最近的高价值特殊墙
        best = None
        best_score = -1
        tx, ty = tank_pos
        for sw in special_walls:
            if not hasattr(sw, 'rect'):
                continue
            cx, cy = sw.rect.centerx, sw.rect.centery
            d = (cx - tx) ** 2 + (cy - ty) ** 2
            effect = getattr(sw, 'effect_type', 'unknown')
            value = (len(PREFERRED_EFFECTS) - PREFERRED_EFFECTS.index(effect)) if effect in PREFERRED_EFFECTS else 0
            score = value / max(1, d)
            if score > best_score:
                best_score = score
                best = (cx, cy)
        return best

    def _can_fire_line(self, walls, tank_pos, target_pos):
        # 检查射线是否被普通墙阻挡（隔离墙需要穿甲穿透，这里交给弹种选择，不在规则AI中复杂化）
        tx, ty = tank_pos
        gx, gy = target_pos
        angle = math.atan2(gy - ty, gx - tx)
        dist = math.hypot(gx - tx, gy - ty)
        step = 16
        for d in range(step, int(dist) + step, step):
            cx = tx + d * math.cos(angle)
            cy = ty + d * math.sin(angle)
            probe = (cx - 10, cy - 10, 20, 20)
            for w in walls:
                if getattr(w, 'health', 1) <= 0:
                    continue
                if hasattr(w, 'rect') and w.rect.colliderect(probe):
                    # 碰到墙
                    if getattr(w, 'wall_type', 'normal') == 'barrier':
                        # 视为不可直打
                        return False, angle, dist
                    else:
                        return False, angle, dist
        return True, angle, dist

    def _find_blocking_wall_to_target(self, walls, tank_pos, angle):
        # 找到第一块阻挡的普通墙中心，供清障瞄准
        tx, ty = tank_pos
        step = 16
        max_dist = 300
        for d in range(step, max_dist + step, step):
            cx = tx + d * math.cos(angle)
            cy = ty + d * math.sin(angle)
            probe = (cx - 14, cy - 14, 28, 28)
            for w in walls:
                if getattr(w, 'health', 1) <= 0:
                    continue
                if hasattr(w, 'rect') and w.rect.colliderect(probe):
                    if getattr(w, 'wall_type', 'normal') != 'barrier':
                        return (w.rect.centerx, w.rect.centery)
                    else:
                        return None
        return None

    @staticmethod
    def _angle_diff(current, target):
        diff = (target - current + math.pi) % (2 * math.pi) - math.pi
        return diff

    def _update_movement_tracking(self, tank_pos):
        """更新移动跟踪状态"""
        # 检查是否有有效移动
        movement_threshold = 5  # 像素阈值
        if (abs(tank_pos[0] - self.last_position[0]) > movement_threshold or 
            abs(tank_pos[1] - self.last_position[1]) > movement_threshold):
            self.no_movement_frames = 0  # 重置无移动计数
        else:
            self.no_movement_frames += 1
        
        self.last_position = tank_pos
        
        # 增加路径过期计数
        if self.current_path:
            self.path_stale_frames += 1

    def _should_force_action(self):
        """判断是否需要强制行动"""
        # 路径规划超时或长时间无移动时强制行动
        return (self.path_stale_frames > self.max_path_stale_frames or 
                self.no_movement_frames > self.max_no_movement_frames)

    def _get_force_action(self, walls, tank_pos, angle_to_target, target_pos):
        """获取强制行动决策"""
        self.force_clear_obstacles = True
        
        # 清空当前路径，强制重新规划或直接移动
        self.current_path = []
        self.path_step = 0
        self.path_stale_frames = 0
        
        # 尝试清除前方障碍
        blocking_wall = self._find_blocking_wall_to_target(walls, tank_pos, angle_to_target)
        if blocking_wall is not None:
            # 瞄准障碍墙并开火
            bx, by = blocking_wall
            tank_cx, tank_cy = tank_pos
            wall_angle = math.atan2(by - tank_cy, bx - tank_cx)
            angle_diff = self._angle_diff(self.tank.angle, wall_angle)
            
            if abs(angle_diff) > 0.1:
                return {
                    'move_forward': 0,
                    'rotate': 3 if angle_diff > 0 else -3,
                    'fire': False
                }
            else:
                return {
                    'move_forward': 0,
                    'rotate': 0,
                    'fire': True
                }
        
        # 如果没有可清除的障碍，尝试强制移动
        return self._get_force_movement(tank_pos, target_pos)

    def _get_force_movement(self, tank_pos, target_pos):
        """强制移动决策"""
        tank_cx, tank_cy = tank_pos
        target_x, target_y = target_pos
        
        # 尝试绕行：选择一个偏移角度
        base_angle = math.atan2(target_y - tank_cy, target_x - tank_cx)
        
        # 尝试左右偏移90度的方向
        offset_angles = [base_angle + math.pi/2, base_angle - math.pi/2, base_angle + math.pi]
        
        for offset_angle in offset_angles:
            angle_diff = self._angle_diff(self.tank.angle, offset_angle)
            if abs(angle_diff) > 0.15:
                return {
                    'move_forward': 0,
                    'rotate': 3 if angle_diff > 0 else -3,
                    'fire': False
                }
            else:
                return {
                    'move_forward': 1,
                    'rotate': 0,
                    'fire': False
                }
        
        # 最后手段：后退
        return {
            'move_forward': -1,
            'rotate': 0,
            'fire': False
        }

    def _handle_pathfinding(self, tank_pos, target_pos, walls, angle_to_target):
        """处理路径规划逻辑"""
        move_forward = 0
        rotate = 0
        
        if self.pathfinder is not None:
            # 检查是否需要重新规划路径
            if (not self.current_path or self.path_step >= len(self.current_path) or
                self.path_stale_frames > self.max_path_stale_frames // 2):  # 中途检查
                
                self.current_path = self.pathfinder.find_tactical_path(
                    tank_pos, target_pos, walls, self.tank.size
                ) or []
                self.path_step = 0
                self.path_stale_frames = 0

            waypoint = None
            if self.current_path:
                waypoint = self.current_path[min(self.path_step, len(self.current_path)-1)]

            if waypoint:
                tank_cx, tank_cy = tank_pos
                wpx, wpy = waypoint
                to_wp_angle = math.atan2(wpy - tank_cy, wpx - tank_cx)
                angle_diff = self._angle_diff(self.tank.angle, to_wp_angle)
                
                if abs(angle_diff) > 0.15:
                    rotate = 3 if angle_diff > 0 else -3
                else:
                    move_forward = 1
                    # 前进到近处则推进下一个路点
                    if (abs(wpx - tank_cx) < 18 and abs(wpy - tank_cy) < 18):
                        self.path_step += 1
            else:
                # 无路径时，使用强化的直接移动策略
                move_forward, rotate = self._fallback_direct_movement(tank_pos, target_pos, angle_to_target)
        else:
            # 无路径规划器时，使用直接移动
            move_forward, rotate = self._fallback_direct_movement(tank_pos, target_pos, angle_to_target)
        
        return move_forward, rotate

    def _fallback_direct_movement(self, tank_pos, target_pos, angle_to_target):
        """回退的直接移动策略"""
        angle_diff = self._angle_diff(self.tank.angle, angle_to_target)
        
        if abs(angle_diff) > 0.2:
            return 0, 3 if angle_diff > 0 else -3
        else:
            # 根据无移动时间决定移动策略
            if self.no_movement_frames > self.max_no_movement_frames // 2:
                # 尝试随机方向移动
                random_angle = angle_to_target + (random.random() - 0.5) * math.pi
                random_diff = self._angle_diff(self.tank.angle, random_angle)
                if abs(random_diff) > 0.2:
                    return 0, 3 if random_diff > 0 else -3
            
            return 1, 0  # 直接前进
