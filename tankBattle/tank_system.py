"""
坦克系统模块
包含玩家坦克和敌方坦克类
"""
import pygame
import math
import os
import random
from config import PLAYER_CONFIG, ENEMY_CONFIG, PLAYER_BULLET_CONFIG, ENEMY_BULLET_CONFIG
from bullet_system import Bullet

class BaseTank(pygame.sprite.Sprite):
    """坦克基类"""
    def __init__(self, x, y, angle, config, bullet_config):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle

        # 从配置加载属性
        self.size = config['SIZE']
        self.max_health = config['MAX_HEALTH']
        self.health = config['HEALTH']
        self.speed = config['SPEED']
        self.rotation_speed = config['ROTATION_SPEED']
        self.reload_time = config['RELOAD_TIME']
        self.turret_length = config['TURRET_LENGTH']
        self.turret_width = config['TURRET_WIDTH']
        self.color = config['COLOR']

        # 子弹配置
        self.bullet_type = bullet_config['TYPE']

        # 游戏状态
        self.rect = pygame.Rect(x, y, *self.size)
        self.reload = 0

        # 加载图片
        self.image = None
        if 'IMAGE' in config and os.path.exists(config['IMAGE']):
            self.image = pygame.transform.scale(
                pygame.image.load(config['IMAGE']), self.size)

    def move(self, forward, walls):
        """移动坦克"""
        dx = forward * self.speed * math.cos(self.angle)
        dy = forward * self.speed * math.sin(self.angle)
        new_rect = self.rect.move(dx, dy)

        # 检查边界
        from config import GAME_CONFIG
        if (new_rect.left < 0 or new_rect.right > GAME_CONFIG['WIDTH'] or
            new_rect.top < 0 or new_rect.bottom > GAME_CONFIG['HEIGHT']):
            # 边界检测失败，检查边缘是否有障碍物需要清除
            self._handle_edge_obstacles(walls)
            return False

        # 检查墙壁碰撞
        if not any(new_rect.colliderect(w.rect) for w in walls if w.health > 0):
            self.x += dx
            self.y += dy
            self.rect.topleft = (self.x, self.y)
            return True
        else:
            # 移动被墙壁阻挡，检查是否需要清除障碍物
            self._handle_nearby_obstacles(walls, new_rect)
            return False

    def _handle_edge_obstacles(self, walls):
        """处理边缘障碍物 - 检查边缘10像素内的卡死位置"""
        from config import GAME_CONFIG
        edge_detection_range = 10

        # 检查坦克是否接近边缘
        near_left_edge = self.x <= edge_detection_range
        near_right_edge = self.x + self.size[0] >= GAME_CONFIG['WIDTH'] - edge_detection_range
        near_top_edge = self.y <= edge_detection_range
        near_bottom_edge = self.y + self.size[1] >= GAME_CONFIG['HEIGHT'] - edge_detection_range

        if any([near_left_edge, near_right_edge, near_top_edge, near_bottom_edge]):
            # 检查周围是否有障碍物
            obstacle_found = self._find_edge_obstacles(walls, edge_detection_range)
            if obstacle_found:
                # 攻击最近的障碍物
                return self._attack_nearest_obstacle(walls)

        return None

    def _find_edge_obstacles(self, walls, detection_range):
        """查找边缘附近的障碍物"""
        tank_center = (self.x + self.size[0] // 2, self.y + self.size[1] // 2)

        for wall in walls:
            if wall.health <= 0:
                continue

            wall_center = (wall.rect.centerx, wall.rect.centery)
            distance = math.sqrt(
                (tank_center[0] - wall_center[0]) ** 2 +
                (tank_center[1] - wall_center[1]) ** 2
            )

            if distance <= detection_range + 20:  # 扩大检测范围
                return True

        return False

    def _handle_nearby_obstacles(self, walls, blocked_rect):
        """处理附近的障碍物"""
        # 检查10像素范围内的障碍物
        detection_range = 10
        tank_center = (blocked_rect.centerx, blocked_rect.centery)

        nearby_obstacles = []
        for wall in walls:
            if wall.health <= 0:
                continue
            # 跳过隔离围墙（不可攻击，只能绕行）
            if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                continue

            wall_center = (wall.rect.centerx, wall.rect.centery)
            distance = math.sqrt(
                (tank_center[0] - wall_center[0]) ** 2 +
                (tank_center[1] - wall_center[1]) ** 2
            )

            if distance <= detection_range + self.size[0]:
                nearby_obstacles.append(wall)

        if nearby_obstacles:
            return self._attack_nearest_obstacle(walls, nearby_obstacles)

        return None

    def _attack_nearest_obstacle(self, walls, specific_obstacles=None):
        """攻击最近的障碍物"""
    # 只针对可破坏的墙体
        target_walls = specific_obstacles if specific_obstacles else [w for w in walls if not (hasattr(w, 'wall_type') and w.wall_type == 'barrier')]
        if not target_walls:
            return None

        tank_center = (self.x + self.size[0] // 2, self.y + self.size[1] // 2)
        nearest_wall = None
        min_distance = float('inf')

        for wall in target_walls:
            if wall.health <= 0:
                continue

            wall_center = (wall.rect.centerx, wall.rect.centery)
            distance = math.sqrt(
                (tank_center[0] - wall_center[0]) ** 2 +
                (tank_center[1] - wall_center[1]) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                nearest_wall = wall

        if nearest_wall:
            # 瞄准最近的障碍物
            wall_center = nearest_wall.rect.center
            dx = wall_center[0] - tank_center[0]
            dy = wall_center[1] - tank_center[1]
            target_angle = math.atan2(dy, dx)

            # 快速调整角度并射击
            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_diff) > 0.2:
                self.rotate(3 if angle_diff > 0 else -3)
            else:
                # 角度合适，立即射击
                if self.reload == 0:
                    return self.fire()

        return None

    def rotate(self, direction):
        """旋转坦克"""
        self.angle += direction * self.rotation_speed * math.pi

    def fire(self):
        """发射子弹"""
        if self.reload == 0:
            # 计算子弹发射位置
            bx = self.x + self.size[0] // 2 + 18 * math.cos(self.angle)
            by = self.y + self.size[1] // 2 + 18 * math.sin(self.angle)

            self.reload = self.reload_time
            return Bullet(bx, by, self.angle, self.get_owner(), self.bullet_type)
        return None

    def update(self):
        """更新坦克状态"""
        if self.reload > 0:
            self.reload -= 1

    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        return self.health <= 0

    def draw(self, surface):
        """绘制坦克"""
        cx = self.x + self.size[0] // 2
        cy = self.y + self.size[1] // 2

        # 绘制主体
        if self.image:
            rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
            rect = rotated.get_rect(center=(cx, cy))
            surface.blit(rotated, rect.topleft)
        else:
            pygame.draw.rect(surface, self.color,
                           (self.x, self.y, *self.size), border_radius=8)

        # 绘制炮管
        turret_end = (cx + self.turret_length * math.cos(self.angle),
                     cy + self.turret_length * math.sin(self.angle))
        pygame.draw.line(surface, (80, 80, 80), (cx, cy), turret_end, self.turret_width)

        # 绘制炮口
        pygame.draw.circle(surface, (220, 220, 0),
                          (int(turret_end[0]), int(turret_end[1])),
                          self.turret_width // 2)

        # 绘制生命条
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface):
        """绘制生命条"""
        bar_width = self.size[0]
        bar_height = 6
        bar_x = self.x
        bar_y = self.y - 10

        # 背景
        pygame.draw.rect(surface, (255, 0, 0),
                        (bar_x, bar_y, bar_width, bar_height))

        # 生命条
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, (0, 255, 0),
                        (bar_x, bar_y, bar_width * health_ratio, bar_height))

    def get_owner(self):
        """获取所有者类型，子类需要实现"""
        raise NotImplementedError

class PlayerTank(BaseTank):
    """玩家坦克"""
    def __init__(self, x, y, angle=0):
        super().__init__(x, y, angle, PLAYER_CONFIG, PLAYER_BULLET_CONFIG)

        # 可选择的子弹类型
        self.available_bullet_types = ['NORMAL', 'PIERCING', 'EXPLOSIVE', 'RAPID', 'HEAVY', 'BARRICADE']
        self.current_bullet_index = 0
        self.bullet_type = self.available_bullet_types[self.current_bullet_index]

        # 特殊效果属性
        self.original_speed = self.speed
        self.has_shield = False
        self.multi_shot = False
        self.ghost_mode = False

        # 快速射击模式
        self.rapid_fire_mode = False
        self.rapid_fire_timer = 0
        self.rapid_fire_cooldown = 5  # 快速射击间隔

        # 掩体弹冷却机制
        self.barricade_cooldown = 0

    def get_owner(self):
        return 'player'

    def switch_bullet_type(self, direction=1):
        """切换子弹类型"""
        self.current_bullet_index = (self.current_bullet_index + direction) % len(self.available_bullet_types)
        self.bullet_type = self.available_bullet_types[self.current_bullet_index]
        return self.bullet_type

    def set_bullet_type(self, bullet_type):
        """直接设置子弹类型"""
        if bullet_type in self.available_bullet_types:
            self.bullet_type = bullet_type
            self.current_bullet_index = self.available_bullet_types.index(bullet_type)

    def fire(self):
        """发射子弹"""
        bullets = []

        # 检查掩体弹的特殊冷却
        if self.bullet_type == 'BARRICADE':
            if self.barricade_cooldown > 0:
                return bullets  # 掩体弹还在冷却中
            else:
                # 设置掩体弹冷却
                from config import BULLET_TYPES
                self.barricade_cooldown = BULLET_TYPES['BARRICADE']['COOLDOWN']

        # 检查射击冷却
        can_fire = False
        if self.bullet_type == 'RAPID' or self.rapid_fire_mode:
            if self.rapid_fire_timer <= 0:
                can_fire = True
                self.rapid_fire_timer = self.rapid_fire_cooldown
        else:
            if self.reload == 0:
                can_fire = True
                self.reload = self.reload_time

        if not can_fire and self.bullet_type != 'BARRICADE':
            return bullets

        # 计算子弹发射位置
        bx = self.x + self.size[0] // 2 + 18 * math.cos(self.angle)
        by = self.y + self.size[1] // 2 + 18 * math.sin(self.angle)

        if self.multi_shot:
            # 多重射击模式 - 发射3发子弹
            angles = [self.angle - 0.3, self.angle, self.angle + 0.3]
            for angle in angles:
                bullet_x = self.x + self.size[0] // 2 + 18 * math.cos(angle)
                bullet_y = self.y + self.size[1] // 2 + 18 * math.sin(angle)
                bullet = Bullet(bullet_x, bullet_y, angle, self.get_owner(), self.bullet_type)
                bullets.append(bullet)
        else:
            # 普通射击
            bullet = Bullet(bx, by, self.angle, self.get_owner(), self.bullet_type)
            bullets.append(bullet)

        return bullets

    def update(self):
        """更新坦克状态"""
        super().update()

        # 更新快速射击计时器
        if self.rapid_fire_timer > 0:
            self.rapid_fire_timer -= 1

        # 更新掩体弹冷却计时器
        if self.barricade_cooldown > 0:
            self.barricade_cooldown -= 1
            self.rapid_fire_timer -= 1

    def take_damage(self, damage):
        """受到伤害（考虑护盾效果）"""
        if self.has_shield:
            # 护盾减少一半伤害
            damage = max(1, damage // 2)

        self.health -= damage
        return self.health <= 0

    def move(self, forward, walls):
        """移动坦克（考虑幽灵模式）"""
        dx = forward * self.speed * math.cos(self.angle)
        dy = forward * self.speed * math.sin(self.angle)
        new_rect = self.rect.move(dx, dy)

        # 检查边界
        from config import GAME_CONFIG
        if (new_rect.left < 0 or new_rect.right > GAME_CONFIG['WIDTH'] or
            new_rect.top < 0 or new_rect.bottom > GAME_CONFIG['HEIGHT']):
            # 边界检测失败，检查边缘是否有障碍物需要清除
            self._handle_edge_obstacles(walls)
            return False

        # 如果是幽灵模式，可以穿过墙壁
        if self.ghost_mode:
            self.x += dx
            self.y += dy
            self.rect.topleft = (self.x, self.y)
            return True
        else:
            # 检查墙壁碰撞
            if not any(new_rect.colliderect(w.rect) for w in walls if w.health > 0):
                self.x += dx
                self.y += dy
                self.rect.topleft = (self.x, self.y)
                return True
            else:
                # 移动被墙壁阻挡，检查是否需要清除障碍物
                self._handle_nearby_obstacles(walls, new_rect)
                return False

    def draw(self, surface):
        """绘制坦克（包含特殊效果）"""
        cx = self.x + self.size[0] // 2
        cy = self.y + self.size[1] // 2

        # 特殊效果光环
        if self.has_shield:
            # 护盾效果
            pygame.draw.circle(surface, (100, 150, 255), (int(cx), int(cy)), 35, 3)

        if self.ghost_mode:
            # 幽灵模式效果
            alpha_surface = pygame.Surface(self.size, pygame.SRCALPHA)
            alpha = 128  # 半透明
        else:
            alpha_surface = None
            alpha = 255

        # 绘制主体
        if self.image:
            rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
            if alpha_surface:
                rotated.set_alpha(alpha)
            rect = rotated.get_rect(center=(cx, cy))
            surface.blit(rotated, rect.topleft)
        else:
            color = self.color if not self.ghost_mode else (*self.color, alpha)
            if alpha_surface:
                pygame.draw.rect(alpha_surface, color, (0, 0, *self.size), border_radius=8)
                surface.blit(alpha_surface, (self.x, self.y))
            else:
                pygame.draw.rect(surface, color, (self.x, self.y, *self.size), border_radius=8)

        # 绘制炮管
        turret_end = (cx + self.turret_length * math.cos(self.angle),
                     cy + self.turret_length * math.sin(self.angle))
        turret_color = (80, 80, 80) if not self.ghost_mode else (80, 80, 80, alpha)
        pygame.draw.line(surface, turret_color, (cx, cy), turret_end, self.turret_width)

        # 绘制炮口（根据子弹类型改变颜色）
        from config import BULLET_TYPES
        bullet_config = BULLET_TYPES.get(self.bullet_type, BULLET_TYPES['NORMAL'])
        muzzle_color = bullet_config.get('COLOR', (220, 220, 0))
        if muzzle_color is None:
            muzzle_color = (220, 220, 0)

        pygame.draw.circle(surface, muzzle_color,
                          (int(turret_end[0]), int(turret_end[1])),
                          self.turret_width // 2)

        # 绘制生命条
        self._draw_health_bar(surface)

    def _draw_bullet_type_indicator(self, surface):
        """绘制子弹类型指示器（已禁用）"""
        pass

class EnemyTank(BaseTank):
    """敌方坦克"""
    def __init__(self, x, y, angle=0):
        super().__init__(x, y, angle, ENEMY_CONFIG, ENEMY_BULLET_CONFIG)

        # AI 相关属性
        self.ai_target = None
        self.ai_state = 'seek_player'  # seek_player, attack, avoid_obstacle, destroy_obstacle
        self.ai_mode = 'attack'  # defense: 防守模式, attack: 攻击模式 - 默认攻击模式，鼓励积极推进
        self.territory_check_timer = 0  # 领域检查计时器
        self.last_shot_time = 0
        self.stuck_timer = 0  # 被困计时器
        self.last_position = (x, y)  # 上一次位置
        self.position_unchanged_time = 0  # 位置未变化时间
        self.path_planning_cooldown = 0  # 路径规划冷却
        self.avoid_direction = 0  # 避障方向
        self.obstacle_target = None  # 要摧毁的障碍物
        self.max_stuck_time = 120  # 最大被困时间（帧数）

        # 新增：快速决策相关属性
        self.rotation_timeout = 0  # 旋转超时计时器
        self.last_action_time = 0  # 上次行动时间
        self.decision_timer = 0  # 决策计时器
        self.force_action_threshold = 30  # 强制行动阈值（帧数）

    def get_owner(self):
        return 'enemy'

    def update_ai(self, player, walls, bullet_manager, environment_manager=None):
        """更新AI行为 - 优化的智能算法"""
        if not player or player.health <= 0:
            return

        # 更新AI模式（每30帧检查一次，提高响应速度）
        self.territory_check_timer += 1
        if self.territory_check_timer >= 30 and environment_manager:
            self._update_ai_mode(player, environment_manager)
            self.territory_check_timer = 0

        # 检查是否被玩家攻击 - 最高优先级
        if self._check_under_attack(player):
            self._execute_counter_attack(player, walls, bullet_manager)
            return

        # 检查是否被困
        self._check_if_stuck()

        # 根据AI模式选择主要目标
        primary_target, target_type = self._select_primary_target(player, environment_manager)
        if not primary_target:
            return

        # 计算到目标的距离和角度
        if target_type == 'player':
            dx = primary_target.x + primary_target.size[0]//2 - (self.x + self.size[0]//2)
            dy = primary_target.y + primary_target.size[1]//2 - (self.y + self.size[1]//2)
        else:  # base
            dx = primary_target.rect.centerx - (self.x + self.size[0]//2)
            dy = primary_target.rect.centery - (self.y + self.size[1]//2)

        distance = math.sqrt(dx * dx + dy * dy)
        target_angle = math.atan2(dy, dx)

        # 执行智能AI行为
        self._execute_smart_ai(distance, target_angle, walls, bullet_manager, environment_manager, target_type)

    def _check_under_attack(self, player):
        """检查是否正在被玩家攻击"""
        if not player:
            return False

        # 计算玩家与AI坦克的距离
        player_center = (player.x + player.size[0]//2, player.y + player.size[1]//2)
        ai_center = (self.x + self.size[0]//2, self.y + self.size[1]//2)
        distance = math.sqrt((player_center[0] - ai_center[0])**2 + (player_center[1] - ai_center[1])**2)

        # 如果玩家在近距离且朝向AI坦克，认为正在被攻击
        if distance <= 150:  # 150像素内认为是威胁范围
            dx = ai_center[0] - player_center[0]
            dy = ai_center[1] - player_center[1]
            angle_to_ai = math.atan2(dy, dx)

            # 检查玩家是否大致瞄准AI坦克
            angle_diff = abs((player.angle - angle_to_ai + math.pi) % (2 * math.pi) - math.pi)
            if angle_diff <= math.pi / 3:  # 60度角度范围内
                return True

        return False

    def _execute_counter_attack(self, player, walls, bullet_manager):
        """执行反击 - 立即攻击玩家"""
        # 计算到玩家的角度
        player_center = (player.x + player.size[0]//2, player.y + player.size[1]//2)
        ai_center = (self.x + self.size[0]//2, self.y + self.size[1]//2)

        dx = player_center[0] - ai_center[0]
        dy = player_center[1] - ai_center[1]
        target_angle = math.atan2(dy, dx)

        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

        # 快速转向玩家
        if abs(angle_diff) > 0.15:
            self.rotate(4 if angle_diff > 0 else -4)  # 快速转向
        else:
            # 立即开火
            if random.random() < 0.9:  # 90%高射击频率
                bullet = self.fire()
                if bullet:
                    bullet_manager.add_bullet(bullet)

    def _select_primary_target(self, player, environment_manager):
        """根据AI模式和战场情况选择主要目标"""
        if self.ai_mode == 'defense':
            # 防守模式：根据玩家威胁程度选择目标
            if self._is_player_threatening(player):
                # 玩家构成威胁，优先攻击玩家
                return player, 'player'
            else:
                # 玩家不构成威胁，主动进攻玩家基地
                if environment_manager:
                    player_base = environment_manager.player_base
                    if player_base and player_base.health > 0:
                        return player_base, 'base'
                # 如果没有基地，攻击玩家
                return player, 'player'
        else:
            # 攻击模式：优先攻击玩家基地
            if environment_manager:
                player_base = environment_manager.player_base
                if player_base and player_base.health > 0:
                    return player_base, 'base'
            # 如果没有基地或基地已被摧毁，攻击玩家
            return player, 'player'

    def _is_player_threatening(self, player):
        """判断玩家是否构成威胁"""
        if not player:
            return False

        # 计算玩家与AI坦克的距离
        player_center = (player.x + player.size[0]//2, player.y + player.size[1]//2)
        ai_center = (self.x + self.size[0]//2, self.y + self.size[1]//2)
        distance = math.sqrt((player_center[0] - ai_center[0])**2 + (player_center[1] - ai_center[1])**2)

        # 威胁判断条件：
        # 1. 玩家在200像素威胁范围内
        # 2. 或者玩家正在瞄准AI坦克（60度角度范围内）
        if distance <= 200:
            return True

        # 检查玩家是否瞄准AI坦克
        if distance <= 300:  # 300像素内检查瞄准
            dx = ai_center[0] - player_center[0]
            dy = ai_center[1] - player_center[1]
            angle_to_ai = math.atan2(dy, dx)

            angle_diff = abs((player.angle - angle_to_ai + math.pi) % (2 * math.pi) - math.pi)
            if angle_diff <= math.pi / 3:  # 60度角度范围内认为是威胁
                return True

        return False

    def _execute_smart_ai(self, distance, target_angle, walls, bullet_manager, environment_manager, target_type='player'):
        """执行智能AI行为 - 快速果断的决策系统"""
        # 更新决策计时器
        self.decision_timer += 1

        # 优先检查边缘情况 - 如果在边缘，立即后退调整
        if self._is_at_screen_edge():
            self._execute_edge_retreat(walls)
            return

        # 基础配置
        close_combat_range = ENEMY_CONFIG['AI_CLOSE_COMBAT_RANGE']
        attack_range = ENEMY_CONFIG['AI_ATTACK_RANGE']
        vision_range = ENEMY_CONFIG['AI_VISION_RANGE']

        # 检查前方是否有障碍 - 检查朝向目标的路径
        front_blocked = self._is_path_blocked_to_target(walls, target_angle)

        # 角度差计算
        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        rotation_threshold = ENEMY_CONFIG['AI_ROTATION_THRESHOLD']

        # 快速决策：如果超过强制行动阈值，立即执行强制行动
        if self.decision_timer > self.force_action_threshold:
            bullet = self._execute_force_action(walls, target_angle, front_blocked, target_type)
            if bullet:
                bullet_manager.add_bullet(bullet)
            self.decision_timer = 0  # 重置决策计时器
            return

        # 严重被困时立即行动
        if self.stuck_timer > ENEMY_CONFIG['AI_STUCK_THRESHOLD'] // 4:
            bullet = self._execute_emergency_action(walls, target_angle, target_type)
            if bullet:
                bullet_manager.add_bullet(bullet)
            return

        # 智能目标导向的行为决策
        if distance <= close_combat_range:
            # 近战：若被隔离墙阻挡，优先绕行；若普通障碍阻挡，智能清理；否则直接攻击
            if front_blocked == 'barrier_wall':
                self._execute_barrier_avoidance(walls, target_angle)
            elif front_blocked:
                bullet = self._execute_intelligent_obstacle_clearing(walls, target_angle, angle_diff, target_type)
                if bullet:
                    bullet_manager.add_bullet(bullet)
            else:
                bullet = self._execute_target_combat(angle_diff, distance, rotation_threshold, bullet_manager, walls, target_type)
                if bullet:
                    bullet_manager.add_bullet(bullet)
        elif distance <= attack_range:
            # 攻击范围：智能处理障碍物
            if front_blocked == 'barrier_wall':
                # 遇到隔离围墙，执行绕行策略
                self._execute_barrier_avoidance(walls, target_angle)
            elif front_blocked:
                bullet = self._execute_intelligent_obstacle_clearing(walls, target_angle, angle_diff, target_type)
                if bullet:
                    bullet_manager.add_bullet(bullet)
            else:
                bullet = self._execute_target_approach(angle_diff, rotation_threshold, walls, target_type)
                if bullet:
                    bullet_manager.add_bullet(bullet)
        elif distance <= vision_range:
            # 视野范围：接近目标
            if front_blocked == 'barrier_wall':
                # 遇到隔离围墙，执行绕行策略
                self._execute_barrier_avoidance(walls, target_angle)
            else:
                bullet = self._execute_target_approach(angle_diff, rotation_threshold, walls, target_type)
                if bullet:
                    bullet_manager.add_bullet(bullet)
        else:
            # 超出视野：巡逻搜索
            self._execute_search_patrol(walls, front_blocked)

    def _is_path_blocked_to_target(self, walls, target_angle):
        """检查到目标的路径是否被障碍物阻挡（长距离射线，优先识别隔离墙）"""
        start_x = self.x + self.size[0] // 2
        start_y = self.y + self.size[1] // 2
        # 使用逐步射线检测较长距离，避免远处隔离墙未被识别的问题
        max_distance = ENEMY_CONFIG.get('AI_VISION_RANGE', 300)
        step = 20
        for distance in range(step, max_distance + step, step):
            check_x = start_x + distance * math.cos(target_angle)
            check_y = start_y + distance * math.sin(target_angle)
            check_rect = pygame.Rect(check_x - 10, check_y - 10, 20, 20)
            for wall in walls:
                if wall.health > 0 and wall.rect.colliderect(check_rect):
                    if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                        return 'barrier_wall'  # 隔离墙：必须绕行
                    return True  # 普通墙：可清理
        return False

    def _execute_target_combat(self, angle_diff, distance, rotation_threshold, bullet_manager, walls, target_type):
        """执行目标导向的战斗"""
        # 根据目标类型调整射击频率
        if target_type == 'player':
            fire_rate_multiplier = 6  # 对玩家高频射击
        else:  # base
            fire_rate_multiplier = 4  # 对基地中频射击

        if abs(angle_diff) > rotation_threshold:
            self.rotate(3 if angle_diff > 0 else -3)
        else:
            # 射击前的防呆：若目标方向上存在隔离墙，先绕行，不开火
            target_angle = self.angle + angle_diff
            path_block = self._is_path_blocked_to_target(walls, target_angle)
            if path_block == 'barrier_wall':
                self._execute_barrier_avoidance(walls, target_angle)
                return None
            # 高频射击
            if random.random() < ENEMY_CONFIG['FIRE_RATE'] * fire_rate_multiplier:
                return self.fire()
        return None

    def _execute_intelligent_obstacle_clearing(self, walls, target_angle, angle_diff, target_type):
        """智能障碍物清理 - 只清理阻挡到目标路径的障碍物"""
        # 找到阻挡到目标路径的障碍物
        blocking_wall = self._find_blocking_wall_to_target(walls, target_angle)

        if blocking_wall:
            # 瞄准阻挡的墙体
            wall_center = blocking_wall.rect.center
            dx = wall_center[0] - (self.x + self.size[0]//2)
            dy = wall_center[1] - (self.y + self.size[1]//2)
            wall_angle = math.atan2(dy, dx)

            wall_angle_diff = (wall_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            if abs(wall_angle_diff) > 0.2:
                self.rotate(3 if wall_angle_diff > 0 else -3)
            else:
                # 射击阻挡的墙体
                if random.random() < ENEMY_CONFIG['FIRE_RATE'] * 8:  # 高频清理障碍
                    return self.fire()
        else:
            # 没有找到阻挡的墙体，尝试绕行
            self._execute_target_approach(angle_diff, ENEMY_CONFIG['AI_ROTATION_THRESHOLD'], walls, target_type)

        return None

    def _find_blocking_wall_to_target(self, walls, target_angle):
        """找到阻挡到目标路径的墙体"""
        # 在目标方向上检查障碍物
        max_distance = 150  # 最大检查距离
        step = 20  # 检查步长

        for distance in range(step, max_distance, step):
            check_x = self.x + self.size[0]//2 + distance * math.cos(target_angle)
            check_y = self.y + self.size[1]//2 + distance * math.sin(target_angle)
            check_rect = pygame.Rect(check_x - 15, check_y - 15, 30, 30)

            for wall in walls:
                if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                    # 隔离墙不作为可破坏目标
                    continue
                if wall.health > 0 and wall.rect.colliderect(check_rect):
                    return wall

        return None

    def _execute_target_approach(self, angle_diff, rotation_threshold, walls, target_type):
        """执行目标导向的接近"""
        if abs(angle_diff) > rotation_threshold:
            self.rotate(2 if angle_diff > 0 else -2)
        else:
            if self._can_move_forward(walls):
                self.move(1, walls)
                self.decision_timer = 0  # 成功移动时重置决策计时器
            else:
                # 移动被阻挡，清理前方障碍
                nearest_wall = self._find_nearest_destructible_wall(walls)
                if nearest_wall:
                    return self._attack_specific_wall(nearest_wall)
        return None

    def _execute_search_patrol(self, walls, front_blocked):
        """执行搜索巡逻"""
        if front_blocked:
            # 随机转向
            self.rotate(random.choice([-2, 2]))
        else:
            # 随机移动
            if random.random() < 0.7:
                if self._can_move_forward(walls):
                    self.move(1, walls)
                else:
                    self.rotate(random.choice([-2, 2]))

    def _attack_specific_wall(self, wall):
        """攻击指定的墙体"""
        wall_center = wall.rect.center
        dx = wall_center[0] - (self.x + self.size[0]//2)
        dy = wall_center[1] - (self.y + self.size[1]//2)
        wall_angle = math.atan2(dy, dx)

        angle_diff = (wall_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) > 0.2:
            self.rotate(3 if angle_diff > 0 else -3)
        else:
            return self.fire()
        return None

    def _execute_force_action(self, walls, target_angle, front_blocked, target_type='player'):
        """强制行动：当决策时间过长时强制执行行动"""
        # 优先处理边缘情况
        if self._is_at_screen_edge():
            self._execute_edge_retreat(walls)
            return None

        if front_blocked:
            # 前方被阻挡：只攻击阻挡目标路径的障碍物
            blocking_wall = self._find_blocking_wall_to_target(walls, target_angle)
            if blocking_wall:
                return self._attack_specific_wall(blocking_wall)
            else:
                return self._execute_obstacle_destruction(walls)
        else:
            # 前方通畅：强制向目标移动
            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            # 大幅度转向或直接移动
            if abs(angle_diff) > 1.0:  # 大角度差异
                self.rotate(2 if angle_diff > 0 else -2)  # 快速转向
            else:
                # 强制移动
                if self._can_move_forward(walls):
                    self.move(1, walls)
                else:
                    # 移动失败，立即攻击障碍
                    return self._execute_obstacle_destruction(walls)
        return None

    def _execute_emergency_action(self, walls, target_angle, target_type='player'):
        """紧急行动：被困时的应急处理"""
        # 优先处理边缘情况
        if self._is_at_screen_edge():
            self._execute_edge_retreat(walls)
            return None

        # 1. 优先攻击阻挡到目标的障碍物
        blocking_wall = self._find_blocking_wall_to_target(walls, target_angle)
        if blocking_wall:
            return self._attack_specific_wall(blocking_wall)

        # 2. 如果没有阻挡墙体，攻击最近的障碍物
        nearest_wall = self._find_nearest_destructible_wall(walls)
        if nearest_wall:
            return self._attack_specific_wall(nearest_wall)

        # 3. 如果没有找到墙体，随机移动尝试脱困
        self.angle += random.uniform(-0.5, 0.5)
        if self._can_move_forward(walls):
            self.move(1, walls)

        return None

    def _execute_fast_combat(self, angle_diff, distance, rotation_threshold, bullet_manager, walls):
        """快速战斗：减少角度调整时间，提高射击频率"""
        # 放宽角度要求，减少调整时间
        loose_threshold = rotation_threshold * 2

        if abs(angle_diff) > loose_threshold:
            # 只在角度差异很大时才调整
            self.rotate(2 if angle_diff > 0 else -2)  # 快速转向
        else:
            # 角度基本正确，立即射击
            if random.random() < ENEMY_CONFIG['FIRE_RATE'] * 4:  # 高频率射击
                bullet = self.fire()
                if bullet:
                    bullet_manager.add_bullet(bullet)

        # 同时尝试移动到更好位置
        min_distance = ENEMY_CONFIG['AI_MIN_FIRE_DISTANCE']
        if distance < min_distance and self._can_move_backward(walls):
            self.move(-0.5, walls)
        elif distance > min_distance * 2 and self._can_move_forward(walls):
            self.move(1, walls)

        return None

    def _execute_quick_obstacle_decision(self, walls, target_angle, angle_diff):
        """快速障碍物决策：2秒内决定攻击还是绕行"""
        # 简化决策：如果角度差异不大，直接攻击；否则尝试绕行
        if abs(angle_diff) < 0.5:  # 角度差异较小，直接攻击障碍
            return self._execute_obstacle_destruction(walls)
        else:
            # 角度差异较大，快速寻找绕行路径
            best_direction = self._find_best_direction(walls)
            if best_direction is not None:
                direction_diff = (best_direction - self.angle + math.pi) % (2 * math.pi) - math.pi
                if abs(direction_diff) > 0.2:
                    self.rotate(2 if direction_diff > 0 else -2)  # 快速转向
                else:
                    if self._can_move_forward(walls):
                        self.move(1, walls)
                        self.stuck_timer = max(0, self.stuck_timer - 5)
            else:
                # 找不到绕行路径，立即攻击障碍
                return self._execute_obstacle_destruction(walls)

        return None

    def _execute_fast_approach(self, angle_diff, rotation_threshold, walls):
        """快速接近：减少角度调整，提高移动效率"""
        # 放宽角度要求
        loose_threshold = rotation_threshold * 1.5

        if abs(angle_diff) > loose_threshold:
            self.rotate(2 if angle_diff > 0 else -2)  # 快速转向
        else:
            # 立即尝试移动
            if self._can_move_forward(walls):
                self.move(1, walls)
                self.decision_timer = 0  # 重置决策计时器
            else:
                # 移动失败，快速决定攻击障碍
                return self._execute_obstacle_destruction(walls)

        return None

    def _execute_fast_patrol(self, walls, front_blocked):
        """快速巡逻：简化巡逻逻辑"""
        if front_blocked:
            # 被阻挡时快速转向
            self.rotate(random.choice([-2, 2]))
        else:
            # 随机改变方向
            if random.random() < 0.05:  # 5%概率改变方向
                self.angle += random.uniform(-0.3, 0.3)

            # 尝试移动
            if self._can_move_forward(walls):
                self.move(1, walls)
            else:
                self.rotate(random.choice([-2, 2]))

    def _execute_combat_behavior(self, angle_diff, distance, rotation_threshold, bullet_manager, walls, aggressive=False):
        """执行战斗行为"""
        # 瞄准调整
        if abs(angle_diff) > rotation_threshold:
            self.rotate(1 if angle_diff > 0 else -1)

        # 位置调整：保持合适的攻击距离
        min_distance = ENEMY_CONFIG['AI_MIN_FIRE_DISTANCE']
        optimal_distance = (min_distance + ENEMY_CONFIG['AI_CLOSE_COMBAT_RANGE']) / 2

        movement_blocked = False

        if distance < min_distance:
            # 距离太近，尝试后退
            if self._can_move_backward(walls):
                self.move(-0.5, walls)
            else:
                movement_blocked = True
        elif distance > optimal_distance and not aggressive:
            # 距离适中但可以更近，前进
            if self._can_move_forward(walls):
                self.move(0.8, walls)
            else:
                movement_blocked = True

        # 如果移动被阻挡且在攻击模式，考虑清除障碍
        if movement_blocked and aggressive:
            obstacle_bullet = self._execute_obstacle_destruction(walls)
            if obstacle_bullet:
                return obstacle_bullet

        # 射击决策：近距离射击频率更高
        fire_chance = ENEMY_CONFIG['FIRE_RATE']
        if aggressive:
            fire_chance *= 3  # 近战时射击频率大幅提高
        elif distance <= ENEMY_CONFIG['AI_CLOSE_COMBAT_RANGE'] * 1.5:
            fire_chance *= 2  # 较近距离时射击频率提高

        # 瞄准足够好时射击
        if abs(angle_diff) <= rotation_threshold * 1.5 and random.random() < fire_chance:
            bullet = self.fire()
            if bullet:
                bullet_manager.add_bullet(bullet)

        return None

    def _execute_approach_behavior(self, angle_diff, rotation_threshold, walls):
        """执行接近行为"""
        # 转向目标
        if abs(angle_diff) > rotation_threshold:
            self.rotate(1 if angle_diff > 0 else -1)
        else:
            # 向目标前进
            if self._can_move_forward(walls):
                self.move(1, walls)
                # 成功移动，减少被困计时
                self.stuck_timer = max(0, self.stuck_timer - 2)
            else:
                # 前方被阻挡，积极处理障碍
                self.stuck_timer += 2  # 增加被困计时

                # 如果被困时间较长，直接攻击障碍物
                if self.stuck_timer > ENEMY_CONFIG['AI_STUCK_THRESHOLD'] // 4:
                    return self._execute_obstacle_destruction(walls)
                else:
                    # 尝试绕行
                    return self._execute_obstacle_avoidance(walls)

        return None

    def _handle_stuck_situation(self, walls, target_angle):
        """处理严重被困的情况"""
        # 1. 首先尝试找到直接阻挡前进的墙体
        blocking_wall = self._find_blocking_wall(walls)

        if blocking_wall:
            # 瞄准并攻击阻挡的墙体
            wall_center = blocking_wall.rect.center
            dx = wall_center[0] - (self.x + self.size[0]//2)
            dy = wall_center[1] - (self.y + self.size[1]//2)
            wall_angle = math.atan2(dy, dx)

            angle_diff = (wall_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            if abs(angle_diff) > 0.15:
                self.rotate(1 if angle_diff > 0 else -1)
            elif random.random() < ENEMY_CONFIG['FIRE_RATE'] * 4:  # 高频率攻击
                return self.fire()
        else:
            # 2. 如果没有直接阻挡的墙，尝试朝目标方向清理路径
            # 在目标方向上寻找墙体
            path_wall = self._find_wall_in_direction(walls, target_angle)

            if path_wall:
                wall_center = path_wall.rect.center
                dx = wall_center[0] - (self.x + self.size[0]//2)
                dy = wall_center[1] - (self.y + self.size[1]//2)
                wall_angle = math.atan2(dy, dx)

                angle_diff = (wall_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

                if abs(angle_diff) > 0.15:
                    self.rotate(1 if angle_diff > 0 else -1)
                elif random.random() < ENEMY_CONFIG['FIRE_RATE'] * 3:
                    return self.fire()
            else:
                # 3. 最后手段：随机转向尝试脱困
                self.angle += random.uniform(-0.3, 0.3)

        return None

    def _should_clear_obstacle_to_target(self, walls, target_angle):
        """判断是否应该清除障碍物以到达目标"""
        # 检查目标方向上是否有墙体阻挡
        wall_in_path = self._find_wall_in_direction(walls, target_angle, max_distance=150)

        if wall_in_path:
            # 检查绕行的代价
            detour_distance = self._calculate_detour_distance(walls, target_angle)
            direct_distance = self._calculate_direct_distance_to_wall(wall_in_path)

            # 如果绕行距离太长，选择直接攻击
            return detour_distance > direct_distance * 3

        return False

    def _execute_smart_obstacle_handling(self, walls, target_angle):
        """智能障碍物处理"""
        # 1. 优先考虑清除目标路径上的障碍
        if self._should_clear_obstacle_to_target(walls, target_angle):
            return self._execute_obstacle_destruction(walls)

        # 2. 尝试绕行
        best_direction = self._find_best_direction(walls)

        if best_direction is not None:
            direction_diff = (best_direction - self.angle + math.pi) % (2 * math.pi) - math.pi
            if abs(direction_diff) > 0.1:
                self.rotate(1 if direction_diff > 0 else -1)
            else:
                if self._can_move_forward(walls):
                    self.move(1, walls)
                    self.stuck_timer = max(0, self.stuck_timer - 3)
        else:
            # 3. 绕行失败，直接攻击障碍
            return self._execute_obstacle_destruction(walls)

        return None

    def _find_blocking_wall(self, walls):
        """找到直接阻挡前进的墙体"""
        # 检测正前方较近距离的墙体
        check_distance = 20
        front_x = self.x + self.size[0]//2 + check_distance * math.cos(self.angle)
        front_y = self.y + self.size[1]//2 + check_distance * math.sin(self.angle)

        # 创建前方检测区域
        check_rect = pygame.Rect(front_x - 15, front_y - 15, 30, 30)

        closest_wall = None
        min_distance = float('inf')

        for wall in walls:
            if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                # 隔离墙不可破坏，直接跳过，交由绕行逻辑处理
                continue
            if wall.health > 0 and check_rect.colliderect(wall.rect):
                # 计算距离
                wall_center = wall.rect.center
                distance = math.sqrt((wall_center[0] - (self.x + self.size[0]//2))**2 +
                                   (wall_center[1] - (self.y + self.size[1]//2))**2)

                if distance < min_distance:
                    min_distance = distance
                    closest_wall = wall

        return closest_wall

    def _find_wall_in_direction(self, walls, direction, max_distance=200):
        """在指定方向上寻找墙体"""
        start_x = self.x + self.size[0]//2
        start_y = self.y + self.size[1]//2

        # 沿着指定方向检测
        for distance in range(40, max_distance, 20):
            check_x = start_x + distance * math.cos(direction)
            check_y = start_y + distance * math.sin(direction)
            check_rect = pygame.Rect(check_x - 10, check_y - 10, 20, 20)

            for wall in walls:
                if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                    # 隔离墙不可破坏，不计入“可清理障碍”
                    continue
                if wall.health > 0 and check_rect.colliderect(wall.rect):
                    return wall

        return None

    def _calculate_detour_distance(self, walls, target_angle):
        """计算绕行距离（简化版本）"""
        # 这里使用简化的启发式方法
        # 实际应用中可以使用A*算法等更精确的路径规划
        detour_factor = 1.5  # 绕行系数

        # 检查左右两个方向的通道
        left_angle = target_angle + math.pi / 2
        right_angle = target_angle - math.pi / 2

        left_clear = self._is_direction_clear(walls, left_angle, 100)
        right_clear = self._is_direction_clear(walls, right_angle, 100)

        if left_clear or right_clear:
            return 100 * detour_factor
        else:
            return 300 * detour_factor  # 需要更复杂的绕行

    def _calculate_direct_distance_to_wall(self, wall):
        """计算到墙体的直线距离"""
        wall_center = wall.rect.center
        my_center = (self.x + self.size[0]//2, self.y + self.size[1]//2)

        return math.sqrt((wall_center[0] - my_center[0])**2 +
                        (wall_center[1] - my_center[1])**2)

    def _is_direction_clear(self, walls, direction, distance):
        """检查指定方向是否通畅"""
        start_x = self.x + self.size[0]//2
        start_y = self.y + self.size[1]//2

        # 检查路径上是否有障碍
        for check_dist in range(20, distance, 20):
            check_x = start_x + check_dist * math.cos(direction)
            check_y = start_y + check_dist * math.sin(direction)
            check_rect = pygame.Rect(check_x - 10, check_y - 10, 20, 20)

            for wall in walls:
                if wall.health > 0 and check_rect.colliderect(wall.rect):
                    return False

        return True

    def _execute_rotation(self, angle_diff):
        """执行旋转调整"""
        self.rotate(1 if angle_diff > 0 else -1)

    def _execute_obstacle_avoidance(self, walls):
        """执行避障行为"""
        # 寻找最佳绕行方向
        best_direction = self._find_best_direction(walls)

        if best_direction is not None:
            direction_diff = (best_direction - self.angle + math.pi) % (2 * math.pi) - math.pi
            if abs(direction_diff) > 0.1:
                self.rotate(1 if direction_diff > 0 else -1)
            else:
                if self._can_move_forward(walls):
                    self.move(1, walls)
                    self.stuck_timer = max(0, self.stuck_timer - 3)  # 成功移动减少被困计时
        else:
            # 找不到好方向，尝试摧毁障碍
            if self.stuck_timer > ENEMY_CONFIG['AI_STUCK_THRESHOLD'] // 2:
                bullet = self._execute_obstacle_destruction(walls)
                return bullet  # 返回子弹供上层处理

        return None

    def _execute_patrol_behavior(self, walls):
        """执行巡逻行为"""
        # 随机改变方向，模拟巡逻
        if random.random() < 0.02:  # 2%概率改变方向
            self.angle += random.uniform(-0.5, 0.5)

        # 尝试前进
        if self._can_move_forward(walls):
            self.move(0.8, walls)
        else:
            # 被阻挡时随机转向
            self.rotate(random.choice([-1, 1]))

    def _execute_obstacle_destruction(self, walls):
        """执行障碍物破坏 - 优化版本"""
        # 寻找最近的可破坏障碍物
        nearest_wall = self._find_nearest_destructible_wall(walls)
        if nearest_wall:
            # 瞄准并射击障碍物
            wall_center = nearest_wall.rect.center
            dx = wall_center[0] - (self.x + self.size[0]//2)
            dy = wall_center[1] - (self.y + self.size[1]//2)
            target_angle = math.atan2(dy, dx)

            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            # 放宽角度要求，快速射击
            if abs(angle_diff) > 0.3:  # 放宽角度阈值
                self.rotate(3 if angle_diff > 0 else -3)  # 更快的转向速度
            else:
                # 高频率射击
                if random.random() < ENEMY_CONFIG['FIRE_RATE'] * 5:  # 进一步提高射击频率
                    return self.fire()
        else:
            # 找不到障碍物，可能是被边界阻挡，随机转向
            self.rotate(random.choice([-3, 3]))

        return None
    def _find_nearest_destructible_wall(self, walls):
        """寻找最近的可破坏墙体"""
        min_distance = float('inf')
        nearest_wall = None
        my_center = (self.x + self.size[0]//2, self.y + self.size[1]//2)

        for wall in walls:
            if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                continue
            if wall.health > 0:
                wall_center = wall.rect.center
                distance = math.sqrt((my_center[0] - wall_center[0])**2 +
                                   (my_center[1] - wall_center[1])**2)
                if distance < min_distance and distance < 100:  # 只考虑附近的墙
                    min_distance = distance
                    nearest_wall = wall

        return nearest_wall

    def _can_move_backward(self, walls):
        """检查是否可以后退"""
        dx = -self.speed * math.cos(self.angle)
        dy = -self.speed * math.sin(self.angle)
        new_rect = self.rect.move(dx, dy)

        # 检查边界
        from config import GAME_CONFIG
        if (new_rect.left < 0 or new_rect.right > GAME_CONFIG['WIDTH'] or
            new_rect.top < 0 or new_rect.bottom > GAME_CONFIG['HEIGHT']):
            return False

        # 检查墙壁碰撞
        for wall in walls:
            if wall.health > 0 and new_rect.colliderect(wall.rect):
                return False

        return True

    def _check_if_stuck(self):
        """检查坦克是否被困 - 优化版本，包含边缘检测"""
        current_pos = (self.x, self.y)

        # 检查位置是否发生变化
        position_changed = (abs(current_pos[0] - self.last_position[0]) > 1 or
                          abs(current_pos[1] - self.last_position[1]) > 1)

        if not position_changed:
            self.position_unchanged_time += 1
        else:
            self.position_unchanged_time = 0
            self.stuck_timer = max(0, self.stuck_timer - 2)  # 移动时快速减少被困计时
            self.decision_timer = max(0, self.decision_timer - 5)  # 移动时重置决策计时器

        self.last_position = current_pos

        # 更激进的被困检测
        if self.position_unchanged_time > 15:  # 15帧未移动就开始积累
            self.stuck_timer += 3  # 快速积累被困时间
        elif self.position_unchanged_time > 8:  # 8帧未移动开始轻微积累
            self.stuck_timer += 1

        # 检查是否在原地转圈（角度变化但位置不变）
        if self.position_unchanged_time > 10:
            self.rotation_timeout += 1
            if self.rotation_timeout > 20:  # 20帧的角度调整超时
                self.decision_timer = self.force_action_threshold  # 强制进入行动模式
                self.rotation_timeout = 0

        # 增强边缘检测：如果坦克在边缘附近且被困，立即标记为严重被困
        if self._is_near_edge() and self.position_unchanged_time > 5:
            self.stuck_timer += 5  # 边缘附近被困时快速积累

        # 如果坦克已经到达屏幕边缘，立即触发高优先级处理
        if self._is_at_screen_edge():
            self.stuck_timer += 10  # 边缘时大幅增加被困值，强制触发后退

    def _is_near_edge(self):
        """检查坦克是否接近屏幕边缘"""
        from config import GAME_CONFIG
        edge_threshold = 30  # 30像素边缘阈值

        return (self.x <= edge_threshold or
                self.x + self.size[0] >= GAME_CONFIG['WIDTH'] - edge_threshold or
                self.y <= edge_threshold or
                self.y + self.size[1] >= GAME_CONFIG['HEIGHT'] - edge_threshold)

    def _is_at_screen_edge(self):
        """检查坦克是否已经到达屏幕边缘矩形边界"""
        from config import GAME_CONFIG
        edge_boundary = 5  # 5像素严格边界判断

        return (self.x <= edge_boundary or
                self.x + self.size[0] >= GAME_CONFIG['WIDTH'] - edge_boundary or
                self.y <= edge_boundary or
                self.y + self.size[1] >= GAME_CONFIG['HEIGHT'] - edge_boundary)

    def _execute_edge_retreat(self, walls):
        """执行边缘后退策略 - 主动后退调整方向而不是原地转向"""
        from config import GAME_CONFIG

        # 确定坦克在哪个边缘
        at_left_edge = self.x <= 10
        at_right_edge = self.x + self.size[0] >= GAME_CONFIG['WIDTH'] - 10
        at_top_edge = self.y <= 10
        at_bottom_edge = self.y + self.size[1] >= GAME_CONFIG['HEIGHT'] - 10

        # 计算安全后退方向（远离边缘）
        retreat_angle = None

        if at_left_edge:
            # 左边缘：向右后退
            retreat_angle = 0  # 向右
        elif at_right_edge:
            # 右边缘：向左后退
            retreat_angle = math.pi  # 向左
        elif at_top_edge:
            # 上边缘：向下后退
            retreat_angle = math.pi / 2  # 向下
        elif at_bottom_edge:
            # 下边缘：向上后退
            retreat_angle = -math.pi / 2  # 向上

        # 处理角落情况
        if (at_left_edge and at_top_edge):
            retreat_angle = math.pi / 4  # 右下
        elif (at_right_edge and at_top_edge):
            retreat_angle = 3 * math.pi / 4  # 左下
        elif (at_left_edge and at_bottom_edge):
            retreat_angle = -math.pi / 4  # 右上
        elif (at_right_edge and at_bottom_edge):
            retreat_angle = -3 * math.pi / 4  # 左上

        if retreat_angle is not None:
            # 快速调整到后退角度
            angle_diff = (retreat_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            if abs(angle_diff) > 0.1:
                # 快速转向后退方向
                self.rotate(4 if angle_diff > 0 else -4)
            else:
                # 角度基本正确，开始后退
                retreat_distance = 40  # 后退40像素到安全区域

                # 执行后退移动
                for _ in range(3):  # 连续后退3次
                    if self.move(1, walls):  # 使用正向移动（因为角度已调整）
                        break

                # 后退完成后，重置AI状态
                self.stuck_timer = 0
                self.decision_timer = 0
                self.rotation_timeout = 0

    def _update_ai_state(self, distance, walls):
        """更新AI状态机"""
        # 如果被困太久，切换到摧毁障碍物模式
        if self.stuck_timer > ENEMY_CONFIG['AI_STUCK_THRESHOLD']:
            self.ai_state = 'destroy_obstacle'
            self._find_nearest_obstacle(walls)
            return

        # 使用配置文件中的动态AI参数
        attack_range = ENEMY_CONFIG['AI_ATTACK_RANGE']  # 动态计算的攻击范围
        vision_range = ENEMY_CONFIG['AI_VISION_RANGE']  # 动态计算的视野范围
        pursuit_range = ENEMY_CONFIG['AI_PURSUIT_RANGE']  # 追击范围
        min_fire_distance = ENEMY_CONFIG['AI_MIN_FIRE_DISTANCE']  # 最小开火距离
        max_fire_distance = ENEMY_CONFIG['AI_MAX_FIRE_DISTANCE']  # 最大开火距离

        # 检查前方是否有障碍物
        front_blocked = self._is_front_blocked(walls)

        # 改进的AI状态判断逻辑
        if min_fire_distance <= distance <= max_fire_distance:  # 最佳攻击距离范围
            if not front_blocked or distance <= min_fire_distance * 2:  # 前方无阻挡或距离很近
                self.ai_state = 'attack'
            else:
                self.ai_state = 'avoid_obstacle'
        elif distance <= pursuit_range:  # 追击范围内
            if front_blocked and distance > min_fire_distance * 3:  # 距离较远且被阻挡时才避障
                self.ai_state = 'avoid_obstacle'
            else:
                self.ai_state = 'seek_player'
        elif distance <= vision_range:  # 视野范围内，远距离搜寻
            if front_blocked:
                self.ai_state = 'avoid_obstacle'
            else:
                self.ai_state = 'seek_player'
        else:  # 超出视野范围，随机移动
            if front_blocked:
                self.ai_state = 'avoid_obstacle'
            else:
                self.ai_state = 'seek_player'

    def _is_front_blocked(self, walls):
        """检查前方是否被障碍物阻挡"""
        # 检测前方多个距离点
        check_distances = [30, 50, 70]

        for dist in check_distances:
            check_x = self.x + self.size[0] // 2 + dist * math.cos(self.angle)
            check_y = self.y + self.size[1] // 2 + dist * math.sin(self.angle)
            check_rect = pygame.Rect(check_x - 10, check_y - 10, 20, 20)

            # 检查是否与墙壁碰撞
            for wall in walls:
                if wall.health > 0 and check_rect.colliderect(wall.rect):
                    return True

            # 检查是否超出边界
            from config import GAME_CONFIG
            if (check_x < 20 or check_x > GAME_CONFIG['WIDTH'] - 20 or
                check_y < 20 or check_y > GAME_CONFIG['HEIGHT'] - 20):
                return True

        return False

    # 保留必要的辅助方法
    def _find_best_direction(self, walls):
        """寻找最佳移动方向"""
        test_angles = [i * math.pi / 4 for i in range(8)]
        best_angle = None
        max_distance = 0

        for test_angle in test_angles:
            distance = self._calculate_move_distance(test_angle, walls)
            if distance > max_distance:
                max_distance = distance
                best_angle = test_angle

        return best_angle if max_distance > 0 else None

    def _calculate_move_distance(self, angle, walls):
        """计算指定方向上的最大移动距离"""
        max_test_distance = 100
        step = 5

        for distance in range(step, max_test_distance, step):
            test_x = self.x + distance * math.cos(angle)
            test_y = self.y + distance * math.sin(angle)
            test_rect = pygame.Rect(test_x, test_y, *self.size)

            # 检查边界
            from config import GAME_CONFIG
            if (test_rect.left < 0 or test_rect.right > GAME_CONFIG['WIDTH'] or
                test_rect.top < 0 or test_rect.bottom > GAME_CONFIG['HEIGHT']):
                return distance - step

            # 检查墙壁碰撞
            for wall in walls:
                if wall.health > 0 and test_rect.colliderect(wall.rect):
                    return distance - step

        return max_test_distance

    def _can_move_forward(self, walls):
        """检查是否可以向前移动"""
        dx = self.speed * math.cos(self.angle)
        dy = self.speed * math.sin(self.angle)
        new_rect = self.rect.move(dx, dy)

        # 检查边界
        from config import GAME_CONFIG
        if (new_rect.left < 0 or new_rect.right > GAME_CONFIG['WIDTH'] or
            new_rect.top < 0 or new_rect.bottom > GAME_CONFIG['HEIGHT']):
            return False

        # 检查墙壁碰撞
        for wall in walls:
            if wall.health > 0 and new_rect.colliderect(wall.rect):
                return False

        return True

    # 保留领域感知相关方法（简化版）
    def _update_ai_mode(self, player, environment_manager):
        """更新AI模式：基于领域位置和战场情况决定攻防策略"""
        if not environment_manager:
            return

        enemy_base_pos = environment_manager.get_base_position('enemy')
        player_base_pos = environment_manager.get_base_position('player')

        if not enemy_base_pos or not player_base_pos:
            return

        # 计算当前位置到两个基地的距离
        tank_pos = (self.x + self.size[0] // 2, self.y + self.size[1] // 2)

        dist_to_enemy_base = math.sqrt((tank_pos[0] - enemy_base_pos[0])**2 +
                                      (tank_pos[1] - enemy_base_pos[1])**2)
        dist_to_player_base = math.sqrt((tank_pos[0] - player_base_pos[0])**2 +
                                       (tank_pos[1] - player_base_pos[1])**2)

        # 改进的模式判断逻辑：更容易进入攻击模式，更激进的推进策略
        mode_switch_threshold = 80  # 增加缓冲区，减少模式切换频率
        aggressive_threshold = 100  # 激进推进阈值

        # 检查是否需要激进推进（在敌方领域内保持攻击模式）
        in_enemy_territory = dist_to_player_base < dist_to_enemy_base

        if self.ai_mode == 'defense':
            # 在防守模式下的切换条件：
            # 1. 更接近玩家基地
            # 2. 或者距离己方基地足够远（激进推进）
            if (dist_to_player_base < dist_to_enemy_base - mode_switch_threshold or
                dist_to_enemy_base > aggressive_threshold):
                self.ai_mode = 'attack'
        else:  # attack mode
            # 在攻击模式下保持激进：只有在非常接近己方基地时才防守
            if (dist_to_enemy_base < dist_to_player_base - mode_switch_threshold and
                dist_to_enemy_base < aggressive_threshold // 2):
                self.ai_mode = 'defense'
            # 在敌方领域内始终保持攻击模式
            elif in_enemy_territory:
                self.ai_mode = 'attack'

    def _execute_barrier_avoidance(self, walls, target_angle):
        """执行隔离围墙绕行策略"""
        # 寻找隔离围墙的通道
        passage_found = self._find_barrier_passage(walls, target_angle)

        if passage_found:
            # 找到通道，朝通道方向移动
            passage_angle = passage_found['angle']
            angle_diff = (passage_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            if abs(angle_diff) > 0.1:  # 调整朝向
                self.rotate(3 if angle_diff > 0 else -3)
            else:
                # 朝通道方向移动
                if self._can_move_forward(walls):
                    self.move(1, walls)
        else:
            # 没找到通道，执行绕行策略
            self._execute_wall_following_behavior(walls, target_angle)

    def _find_barrier_passage(self, walls, target_angle):
        """寻找隔离围墙的通道"""
        tank_center = (self.x + self.size[0] // 2, self.y + self.size[1] // 2)

        # 在隔离围墙周围搜索通道
        search_radius = 200
        best_passage = None
        best_distance = float('inf')

        for search_angle in [target_angle - math.pi/3, target_angle, target_angle + math.pi/3]:
            for distance in range(50, search_radius, 25):
                check_x = tank_center[0] + distance * math.cos(search_angle)
                check_y = tank_center[1] + distance * math.sin(search_angle)

                # 检查这个位置是否是通道
                if self._is_passage_position(walls, check_x, check_y):
                    dist_to_point = math.sqrt((check_x - tank_center[0])**2 + (check_y - tank_center[1])**2)
                    if dist_to_point < best_distance:
                        best_distance = dist_to_point
                        best_passage = {
                            'x': check_x,
                            'y': check_y,
                            'angle': math.atan2(check_y - tank_center[1], check_x - tank_center[0])
                        }

        return best_passage

    def _is_passage_position(self, walls, x, y):
        """检查某个位置是否是隔离围墙的通道"""
        check_rect = pygame.Rect(x - 15, y - 15, 30, 30)

        # 检查是否与隔离围墙碰撞
        for wall in walls:
            if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                if wall.rect.colliderect(check_rect):
                    return False

        return True  # 没有碰撞，是通道

    def _execute_wall_following_behavior(self, walls, target_angle):
        """执行沿墙移动的行为"""
        # 右手法则：沿着围墙边缘移动
        follow_angle = target_angle + math.pi / 2  # 向右转90度

        # 检查右侧是否可以移动
        right_clear = self._check_direction_clear(walls, follow_angle)

        if right_clear:
            # 右侧清晰，向右移动
            angle_diff = (follow_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_diff) > 0.1:
                self.rotate(3 if angle_diff > 0 else -3)
            else:
                if self._can_move_forward(walls):
                    self.move(1, walls)
        else:
            # 右侧不清晰，向左转
            self.rotate(-3)

    def _check_direction_clear(self, walls, direction_angle):
        """检查指定方向是否畅通"""
        check_distance = 60
        tank_center = (self.x + self.size[0] // 2, self.y + self.size[1] // 2)
        check_x = tank_center[0] + check_distance * math.cos(direction_angle)
        check_y = tank_center[1] + check_distance * math.sin(direction_angle)

        check_rect = pygame.Rect(check_x - 15, check_y - 15, 30, 30)

        for wall in walls:
            if wall.health > 0 and wall.rect.colliderect(check_rect):
                return False

        return True
