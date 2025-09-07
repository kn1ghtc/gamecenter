"""
子弹系统模块
包含不同类型的子弹类
"""
import pygame
import math
from config import BULLET_TYPES, COLORS

class Bullet(pygame.sprite.Sprite):
    """基础子弹类"""
    def __init__(self, x, y, angle, owner, bullet_type='NORMAL'):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner  # 'player' 或 'enemy'
        self.bullet_type = bullet_type

        # 从配置获取子弹属性
        config = BULLET_TYPES[bullet_type]
        self.radius = config['RADIUS']
        self.speed = config['SPEED']
        self.damage = config['DAMAGE']
        self.can_pierce_wall = config['CAN_PIERCE_WALL']
        self.wall_damage = config['WALL_DAMAGE']

        # 掩体弹特殊属性
        self.creates_wall = config.get('CREATES_WALL', False)
        if self.creates_wall:
            self.barricade_health = config['BARRICADE_HEALTH']
            self.barricade_size = config['BARRICADE_SIZE']

        # 确定子弹颜色
        if config['COLOR']:
            self.color = config['COLOR']
        else:
            self.color = COLORS['PLAYER'] if owner == 'player' else COLORS['ENEMY']

        # 碰撞矩形
        self.rect = pygame.Rect(x - self.radius, y - self.radius,
                               self.radius * 2, self.radius * 2)

        # 爆炸属性（如果是爆炸弹）
        self.explosion_radius = config.get('EXPLOSION_RADIUS', 0)
        self.explosion_damage = config.get('EXPLOSION_DAMAGE', 0)

        # 是否已经爆炸
        self.exploded = False

    def update(self):
        """更新子弹位置"""
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        """绘制子弹"""
        pygame.draw.circle(surface, self.color,
                          (int(self.x), int(self.y)), self.radius)

        # 如果是特殊类型，添加额外效果
        if self.bullet_type == 'PIERCING':
            # 穿甲弹添加内圈
            pygame.draw.circle(surface, COLORS['WHITE'],
                              (int(self.x), int(self.y)), self.radius // 2)
        elif self.bullet_type == 'EXPLOSIVE':
            # 爆炸弹添加闪烁效果
            import random
            if random.randint(0, 5) == 0:
                pygame.draw.circle(surface, COLORS['YELLOW'],
                                  (int(self.x), int(self.y)), self.radius + 2)

    def explode(self, game_objects):
        """爆炸效果（仅爆炸弹使用）"""
        if self.bullet_type != 'EXPLOSIVE' or self.exploded:
            return []

        self.exploded = True
        damaged_objects = []

        # 检查爆炸范围内的对象
        explosion_rect = pygame.Rect(
            self.x - self.explosion_radius,
            self.y - self.explosion_radius,
            self.explosion_radius * 2,
            self.explosion_radius * 2
        )

        for obj in game_objects:
            if hasattr(obj, 'rect') and explosion_rect.colliderect(obj.rect):
                # 计算距离
                dx = obj.rect.centerx - self.x
                dy = obj.rect.centery - self.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance <= self.explosion_radius:
                    # 根据距离计算伤害
                    damage_ratio = 1 - (distance / self.explosion_radius)
                    damage = int(self.explosion_damage * damage_ratio)
                    if damage > 0:
                        damaged_objects.append((obj, damage))

        return damaged_objects

    def create_barricade_wall(self, environment_manager, hit_wall):
        """为掩体弹创建一个对齐网格的普通迷宫墙

        规则:
        - 使用当前屏幕网格大小对齐到网格单元
        - 在命中的墙体的子弹射击方向一侧相邻单元生成
        - 如果目标单元已有任何墙体，则不创建（避免覆盖/重复）
        - 生成普通墙（与迷宫墙一致），使用默认墙体生命值
        """
        if not self.creates_wall or environment_manager is None or hit_wall is None:
            return None

        from environment import Wall
        from config import MAP_CONFIG, GAME_CONFIG

        cell = MAP_CONFIG['CELL_SIZE']
        game_w = GAME_CONFIG['WIDTH']
        game_h = GAME_CONFIG['HEIGHT']

        # 根据子弹角度判断主方向（水平/垂直）
        dx = math.cos(self.angle)
        dy = math.sin(self.angle)

        # 目标单元左上角
        target_left = 0
        target_top = 0

        if abs(dx) >= abs(dy):
            # 水平方向为主
            if dx >= 0:
                # 命中墙体右侧的相邻单元
                target_left = ((hit_wall.rect.right + 0) // cell) * cell
            else:
                # 命中墙体左侧的相邻单元
                target_left = ((hit_wall.rect.left - cell) // cell) * cell

            # 与子弹所在的行对齐
            target_top = int(self.y // cell) * cell
        else:
            # 垂直方向为主
            if dy >= 0:
                # 命中墙体下侧相邻单元
                target_top = ((hit_wall.rect.bottom + 0) // cell) * cell
            else:
                # 命中墙体上侧相邻单元
                target_top = ((hit_wall.rect.top - cell) // cell) * cell

            # 与子弹所在的列对齐
            target_left = int(self.x // cell) * cell

        # 边界裁剪
        target_left = max(0, min(target_left, game_w - cell))
        target_top = max(0, min(target_top, game_h - cell))

        candidate = pygame.Rect(target_left, target_top, cell, cell)

        # 如果该单元已有墙体（任意类型），则不创建
        for w in environment_manager.get_all_walls():
            if w.rect.colliderect(candidate):
                return None

        # 创建普通墙
        return Wall(candidate, None)

class BulletManager:
    """子弹管理器"""
    def __init__(self):
        self.bullets = []

    def add_bullet(self, bullet):
        """添加子弹"""
        self.bullets.append(bullet)

    def update(self, game_width, game_height):
        """更新所有子弹"""
        for bullet in self.bullets[:]:
            bullet.update()

            # 移除超出边界的子弹
            if not (0 < bullet.x < game_width and 0 < bullet.y < game_height):
                self.bullets.remove(bullet)

    def draw(self, surface):
        """绘制所有子弹"""
        for bullet in self.bullets:
            bullet.draw(surface)

    def get_bullets(self):
        """获取所有子弹"""
        return self.bullets

    def remove_bullet(self, bullet):
        """移除子弹"""
        if bullet in self.bullets:
            self.bullets.remove(bullet)

    def clear(self):
        """清空所有子弹"""
        self.bullets.clear()
