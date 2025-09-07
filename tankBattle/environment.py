"""
游戏环境模块
包含墙壁、基地等环境对象
"""
import pygame
from config import WALL_CONFIG, BASE_CONFIG, COLORS

class Wall(pygame.sprite.Sprite):
    """墙壁类"""
    def __init__(self, rect, health=None):
        super().__init__()
        self.rect = pygame.Rect(rect)
        self.max_health = health if health else WALL_CONFIG['HEALTH']
        self.health = self.max_health
        self.color = WALL_CONFIG['COLOR']

    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        return self.health <= 0

    def draw(self, surface):
        """绘制墙壁"""
        if self.health > 0:
            # 根据生命值调整颜色深度
            health_ratio = self.health / self.max_health
            color = tuple(int(c * health_ratio) for c in self.color)
            pygame.draw.rect(surface, color, self.rect)

            # 如果生命值低，添加裂纹效果
            if health_ratio < 0.5:
                pygame.draw.rect(surface, (50, 50, 50), self.rect, 1)

class Base(pygame.sprite.Sprite):
    """基地基类"""
    def __init__(self, x, y, base_type='PLAYER_BASE'):
        super().__init__()

        # 从配置获取属性
        config = BASE_CONFIG[base_type]
        self.size = config['SIZE']
        self.max_health = config['MAX_HEALTH']
        self.health = config['HEALTH']
        self.color = config['COLOR']
        self.base_type = base_type

        self.rect = pygame.Rect(x, y, *self.size)

    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        return self.health <= 0

    def draw(self, surface):
        """绘制基地"""
        if self.health <= 0:
            return

        # 绘制基地主体
        pygame.draw.rect(surface, self.color, self.rect)

        # 绘制边框
        pygame.draw.rect(surface, COLORS['WHITE'], self.rect, 2)

        # 绘制生命条
        self._draw_health_bar(surface)

        # 绘制基地类型标识
        self._draw_base_icon(surface)

    def _draw_health_bar(self, surface):
        """绘制生命条"""
        bar_width = self.rect.width
        bar_height = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - 12

        # 背景
        pygame.draw.rect(surface, COLORS['RED'],
                        (bar_x, bar_y, bar_width, bar_height))

        # 生命条
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, COLORS['GREEN'],
                        (bar_x, bar_y, bar_width * health_ratio, bar_height))

    def _draw_base_icon(self, surface):
        """绘制基地图标"""
        center_x = self.rect.centerx
        center_y = self.rect.centery

        if self.base_type == 'PLAYER_BASE':
            # 绘制玩家基地标识（十字）
            pygame.draw.line(surface, COLORS['WHITE'],
                           (center_x - 10, center_y),
                           (center_x + 10, center_y), 3)
            pygame.draw.line(surface, COLORS['WHITE'],
                           (center_x, center_y - 10),
                           (center_x, center_y + 10), 3)
        else:
            # 绘制敌方基地标识（X）
            pygame.draw.line(surface, COLORS['WHITE'],
                           (center_x - 10, center_y - 10),
                           (center_x + 10, center_y + 10), 3)
            pygame.draw.line(surface, COLORS['WHITE'],
                           (center_x - 10, center_y + 10),
                           (center_x + 10, center_y - 10), 3)

class PlayerBase(Base):
    """玩家基地"""
    def __init__(self, x, y):
        super().__init__(x, y, 'PLAYER_BASE')

class EnemyBase(Base):
    """敌方基地"""
    def __init__(self, x, y):
        super().__init__(x, y, 'ENEMY_BASE')

class EnvironmentManager:
    """环境管理器"""
    def __init__(self):
        self.walls = []
        self.player_base = None
        self.enemy_base = None

    def add_wall(self, wall):
        """添加墙壁"""
        self.walls.append(wall)

    def set_player_base(self, base):
        """设置玩家基地"""
        self.player_base = base

    def set_enemy_base(self, base):
        """设置敌方基地"""
        self.enemy_base = base

    def get_all_walls(self):
        """获取所有存活的墙壁"""
        return [wall for wall in self.walls if wall.health > 0]

    def remove_destroyed_walls(self):
        """移除被摧毁的墙壁"""
        self.walls = [wall for wall in self.walls if wall.health > 0]

    def draw(self, surface):
        """绘制所有环境对象"""
        # 绘制墙壁
        for wall in self.walls:
            if wall.health > 0:
                wall.draw(surface)

        # 绘制基地
        if self.player_base and self.player_base.health > 0:
            self.player_base.draw(surface)

        if self.enemy_base and self.enemy_base.health > 0:
            self.enemy_base.draw(surface)

    def clear(self):
        """清空所有环境对象"""
        self.walls.clear()
        self.player_base = None
        self.enemy_base = None
