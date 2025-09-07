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
            return

        # 检查墙壁碰撞
        if not any(new_rect.colliderect(w.rect) for w in walls if w.health > 0):
            self.x += dx
            self.y += dy
            self.rect.topleft = (self.x, self.y)

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

    def get_owner(self):
        return 'player'

class EnemyTank(BaseTank):
    """敌方坦克"""
    def __init__(self, x, y, angle=0):
        super().__init__(x, y, angle, ENEMY_CONFIG, ENEMY_BULLET_CONFIG)

        # AI 相关属性
        self.ai_target = None
        self.ai_state = 'seek_player'  # seek_player, attack, avoid_obstacle, destroy_obstacle
        self.last_shot_time = 0
        self.stuck_timer = 0  # 被困计时器
        self.last_position = (x, y)  # 上一次位置
        self.position_unchanged_time = 0  # 位置未变化时间
        self.path_planning_cooldown = 0  # 路径规划冷却
        self.avoid_direction = 0  # 避障方向
        self.obstacle_target = None  # 要摧毁的障碍物
        self.max_stuck_time = 120  # 最大被困时间（帧数）

    def get_owner(self):
        return 'enemy'

    def update_ai(self, player, walls, bullet_manager):
        """更新AI行为 - 智能算法"""
        if not player or player.health <= 0:
            return

        # 检查是否被困
        self._check_if_stuck()

        # 计算到玩家的距离和角度
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        target_angle = math.atan2(dy, dx)

        # 更新AI状态机
        self._update_ai_state(distance, walls)

        # 根据状态执行相应行为
        if self.ai_state == 'seek_player':
            self._seek_player_behavior(target_angle, walls, bullet_manager)
        elif self.ai_state == 'attack':
            self._attack_behavior(target_angle, bullet_manager)
        elif self.ai_state == 'avoid_obstacle':
            self._avoid_obstacle_behavior(walls)
        elif self.ai_state == 'destroy_obstacle':
            self._destroy_obstacle_behavior(walls, bullet_manager)

    def _check_if_stuck(self):
        """检查坦克是否被困"""
        current_pos = (self.x, self.y)

        # 检查位置是否发生变化
        if abs(current_pos[0] - self.last_position[0]) < 1 and abs(current_pos[1] - self.last_position[1]) < 1:
            self.position_unchanged_time += 1
        else:
            self.position_unchanged_time = 0
            self.stuck_timer = 0

        self.last_position = current_pos

        # 如果位置长时间未变化，增加被困计时
        if self.position_unchanged_time > 30:  # 30帧未移动
            self.stuck_timer += 1

    def _update_ai_state(self, distance, walls):
        """更新AI状态机"""
        # 如果被困太久，切换到摧毁障碍物模式
        if self.stuck_timer > self.max_stuck_time:
            self.ai_state = 'destroy_obstacle'
            self._find_nearest_obstacle(walls)
            return

        # 检查前方是否有障碍物
        front_blocked = self._is_front_blocked(walls)

        if distance <= 100:  # 攻击范围
            if front_blocked:
                self.ai_state = 'avoid_obstacle'
            else:
                self.ai_state = 'attack'
        elif distance <= 300:  # 中等距离
            if front_blocked:
                self.ai_state = 'avoid_obstacle'
            else:
                self.ai_state = 'seek_player'
        else:  # 远距离
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

    def _seek_player_behavior(self, target_angle, walls, bullet_manager):
        """寻找玩家行为"""
        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

        # 智能路径规划
        if abs(angle_diff) > ENEMY_CONFIG['AI_ROTATION_THRESHOLD']:
            # 需要旋转
            self.rotate(1 if angle_diff > 0 else -1)
        else:
            # 尝试前进
            if self._can_move_forward(walls):
                self.move(1, walls)
            else:
                # 前方被阻挡，切换到避障模式
                self.ai_state = 'avoid_obstacle'

        # 远距离射击
        if random.random() < ENEMY_CONFIG['FIRE_RATE'] * 0.5:  # 降低远距离射击频率
            bullet = self.fire()
            if bullet:
                bullet_manager.add_bullet(bullet)

    def _attack_behavior(self, target_angle, bullet_manager):
        """攻击行为"""
        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

        # 精确瞄准
        if abs(angle_diff) > 0.05:  # 更精确的瞄准
            self.rotate(1 if angle_diff > 0 else -1)

        # 高频率射击
        if random.random() < ENEMY_CONFIG['FIRE_RATE'] * 2:  # 攻击模式下射击频率加倍
            bullet = self.fire()
            if bullet:
                bullet_manager.add_bullet(bullet)

    def _avoid_obstacle_behavior(self, walls):
        """避障行为"""
        # 尝试不同方向寻找通路
        best_direction = self._find_best_direction(walls)

        if best_direction is not None:
            direction_diff = (best_direction - self.angle + math.pi) % (2 * math.pi) - math.pi

            if abs(direction_diff) > 0.1:
                self.rotate(1 if direction_diff > 0 else -1)
            else:
                if self._can_move_forward(walls):
                    self.move(1, walls)
                    # 如果成功移动，重置被困计时
                    self.stuck_timer = max(0, self.stuck_timer - 5)

    def _find_best_direction(self, walls):
        """寻找最佳移动方向"""
        # 测试8个方向
        test_angles = [i * math.pi / 4 for i in range(8)]
        best_angle = None
        max_distance = 0

        for test_angle in test_angles:
            # 计算这个方向上的最大可移动距离
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

    def _destroy_obstacle_behavior(self, walls, bullet_manager):
        """摧毁障碍物行为"""
        if self.obstacle_target is None or self.obstacle_target.health <= 0:
            self._find_nearest_obstacle(walls)

        if self.obstacle_target:
            # 瞄准障碍物
            dx = self.obstacle_target.rect.centerx - (self.x + self.size[0] // 2)
            dy = self.obstacle_target.rect.centery - (self.y + self.size[1] // 2)
            target_angle = math.atan2(dy, dx)
            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

            if abs(angle_diff) > 0.05:
                self.rotate(1 if angle_diff > 0 else -1)
            else:
                # 连续射击摧毁障碍物
                if random.random() < 0.3:  # 高频率射击
                    bullet = self.fire()
                    if bullet:
                        bullet_manager.add_bullet(bullet)

            # 如果障碍物被摧毁，重置状态
            if self.obstacle_target.health <= 0:
                self.obstacle_target = None
                self.stuck_timer = 0
                self.ai_state = 'seek_player'

    def _find_nearest_obstacle(self, walls):
        """寻找最近的可摧毁障碍物"""
        min_distance = float('inf')
        nearest_wall = None

        center_x = self.x + self.size[0] // 2
        center_y = self.y + self.size[1] // 2

        for wall in walls:
            if wall.health > 0:
                wall_center_x = wall.rect.centerx
                wall_center_y = wall.rect.centery
                distance = math.sqrt((center_x - wall_center_x) ** 2 + (center_y - wall_center_y) ** 2)

                if distance < min_distance:
                    min_distance = distance
                    nearest_wall = wall

        self.obstacle_target = nearest_wall

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
