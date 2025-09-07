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

    def create_barricade_wall(self):
        """为掩体弹创建掩体墙"""
        if not self.creates_wall:
            return None

        from environment import Wall
        from config import BULLET_TYPES

        # 获取掩体弹配置
        barricade_config = BULLET_TYPES.get('BARRICADE', {})
        barricade_health = barricade_config.get('BARRICADE_HEALTH', 15)

        # 计算掩体墙的位置（在子弹碰撞位置前方）
        wall_size = 30  # 掩体墙大小
        wall_x = self.x - wall_size // 2
        wall_y = self.y - wall_size // 2

        # 创建矩形对象
        wall_rect = (wall_x, wall_y, wall_size, wall_size)

        # 创建掩体墙
        barricade_wall = Wall(wall_rect, barricade_health)

        return barricade_wall

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
