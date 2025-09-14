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

    def get_decision(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        player = game_state.get('player')
        walls = game_state.get('walls', [])
        env = game_state.get('environment_manager')
        special_walls = game_state.get('special_walls', [])

        tank_cx = self.tank.x + self.tank.size[0] // 2
        tank_cy = self.tank.y + self.tank.size[1] // 2
        tank_pos = (tank_cx, tank_cy)

        # 1) 目标选择
        target_pos, target_type = self._choose_target(player, env, special_walls, tank_pos)

        # 2) 角度与直线可打判断
        fire_ok, angle_to_target, distance = self._can_fire_line(walls, tank_pos, target_pos)

        # 3) 移动与路径规划
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
            if self.pathfinder is not None:
                if not self.current_path or self.path_step >= len(self.current_path):
                    self.current_path = self.pathfinder.find_tactical_path(
                        tank_pos, target_pos, walls, self.tank.size
                    ) or []
                    self.path_step = 0

                waypoint = None
                if self.current_path:
                    waypoint = self.current_path[min(self.path_step, len(self.current_path)-1)]

                if waypoint:
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
                    # 无路径时，直接朝目标移动（简单AI行为）
                    angle_diff = self._angle_diff(self.tank.angle, angle_to_target)
                    if abs(angle_diff) > 0.2:
                        rotate = 3 if angle_diff > 0 else -3
                    else:
                        move_forward = 1  # 直接前进尝试绕过障碍
            else:
                # 无路径规划时，简单的直接移动
                angle_diff = self._angle_diff(self.tank.angle, angle_to_target)
                if abs(angle_diff) > 0.2:
                    rotate = 3 if angle_diff > 0 else -3
                else:
                    move_forward = 1

        # 4) 清障逻辑（easy/medium 均适用）
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

        # 5) 开火判定
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
