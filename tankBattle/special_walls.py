"""
特殊围墙系统
包含各种特殊效果的围墙
"""
import pygame
import random
import math
from config import WALL_CONFIG, COLORS

class SpecialWall(pygame.sprite.Sprite):
    """特殊围墙基类"""
    def __init__(self, rect, health=None, effect_type='normal'):
        super().__init__()
        self.rect = pygame.Rect(rect)
        self.max_health = health if health else WALL_CONFIG['HEALTH']
        self.health = self.max_health
        self.effect_type = effect_type
        self.effect_triggered = False

        # 特殊效果颜色映射
        self.effect_colors = {
            'normal': (120, 120, 120),
            'piercing_ammo': (255, 255, 100),     # 黄色 - 穿甲弹
            'explosive_ammo': (255, 128, 0),      # 橙色 - 爆炸弹
            'wall_destroyer': (255, 50, 50),      # 红色 - 围墙消除
            'teleport': (100, 255, 255),          # 青色 - 传送
            'health_swap': (255, 100, 255),       # 紫色 - 生命互换
            'speed_boost': (100, 255, 100),       # 绿色 - 速度提升
            'shield': (200, 200, 255),            # 淡蓝色 - 护盾
            'multi_shot': (255, 200, 100),        # 浅橙色 - 多重射击
            'ghost_mode': (150, 150, 255),        # 浅紫色 - 幽灵模式
        }

        self.color = self.effect_colors.get(effect_type, self.effect_colors['normal'])

        # 动画效果
        self.animation_timer = 0
        self.pulse_intensity = 0

    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        if self.health <= 0 and not self.effect_triggered:
            self.effect_triggered = True
            return True, self.effect_type
        return self.health <= 0, None

    def update(self):
        """更新特殊围墙动画"""
        self.animation_timer += 1
        self.pulse_intensity = abs(math.sin(self.animation_timer * 0.1)) * 50

    def draw(self, surface):
        """绘制特殊围墙"""
        if self.health <= 0:
            return

        # 基础颜色
        base_color = self.color

        # 脉冲效果
        if self.effect_type != 'normal':
            pulse_color = tuple(min(255, c + int(self.pulse_intensity)) for c in base_color)
            pygame.draw.rect(surface, pulse_color, self.rect)

            # 特殊边框
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)

            # 特殊符号
            self._draw_effect_symbol(surface)
        else:
            # 普通围墙
            health_ratio = self.health / self.max_health
            color = tuple(int(c * health_ratio) for c in base_color)
            pygame.draw.rect(surface, color, self.rect)

    def _draw_effect_symbol(self, surface):
        """绘制效果符号"""
        center_x = self.rect.centerx
        center_y = self.rect.centery

        if self.effect_type == 'piercing_ammo':
            # 箭头符号
            points = [
                (center_x - 8, center_y),
                (center_x + 8, center_y),
                (center_x + 4, center_y - 4),
                (center_x + 4, center_y + 4)
            ]
            # 绘制箭头主体（线条）
            pygame.draw.line(surface, (255, 255, 255), points[0], points[1], 3)
            # 绘制箭头头部（三角形）
            arrow_head = [points[1], points[2], points[3]]
            pygame.draw.polygon(surface, (255, 255, 255), arrow_head)

        elif self.effect_type == 'explosive_ammo':
            # 爆炸符号
            pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), 6, 2)
            for angle in range(0, 360, 45):
                x = center_x + 10 * math.cos(math.radians(angle))
                y = center_y + 10 * math.sin(math.radians(angle))
                pygame.draw.line(surface, (255, 255, 255),
                               (center_x, center_y), (x, y), 2)

        elif self.effect_type == 'wall_destroyer':
            # X符号
            pygame.draw.line(surface, (255, 255, 255),
                           (center_x - 8, center_y - 8),
                           (center_x + 8, center_y + 8), 3)
            pygame.draw.line(surface, (255, 255, 255),
                           (center_x - 8, center_y + 8),
                           (center_x + 8, center_y - 8), 3)

        elif self.effect_type == 'teleport':
            # 传送门符号
            pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), 8, 2)
            pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), 4, 2)

        elif self.effect_type == 'health_swap':
            # 心形符号
            pygame.draw.circle(surface, (255, 255, 255), (center_x - 3, center_y - 2), 4, 2)
            pygame.draw.circle(surface, (255, 255, 255), (center_x + 3, center_y - 2), 4, 2)
            pygame.draw.polygon(surface, (255, 255, 255), [
                (center_x - 6, center_y + 2),
                (center_x, center_y + 8),
                (center_x + 6, center_y + 2)
            ], 2)

        elif self.effect_type == 'speed_boost':
            # 闪电符号
            points = [
                (center_x - 4, center_y - 8),
                (center_x + 2, center_y - 2),
                (center_x - 2, center_y - 2),
                (center_x + 4, center_y + 8),
                (center_x - 2, center_y + 2),
                (center_x + 2, center_y + 2)
            ]
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)

        elif self.effect_type == 'shield':
            # 盾牌符号
            points = [
                (center_x, center_y - 8),
                (center_x - 6, center_y - 4),
                (center_x - 6, center_y + 4),
                (center_x, center_y + 8),
                (center_x + 6, center_y + 4),
                (center_x + 6, center_y - 4)
            ]
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)

        elif self.effect_type == 'multi_shot':
            # 三个点符号
            for i, offset in enumerate([-4, 0, 4]):
                pygame.draw.circle(surface, (255, 255, 255),
                                 (center_x + offset, center_y), 2)

        elif self.effect_type == 'ghost_mode':
            # 幽灵符号
            pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), 6, 2)
            pygame.draw.circle(surface, (255, 255, 255), (center_x - 3, center_y - 2), 1)
            pygame.draw.circle(surface, (255, 255, 255), (center_x + 3, center_y - 2), 1)
            pygame.draw.arc(surface, (255, 255, 255),
                          (center_x - 4, center_y + 1, 8, 4), 0, math.pi, 2)

class SpecialEffectManager:
    """特殊效果管理器"""
    def __init__(self):
        self.active_effects = {}  # 玩家当前激活的效果
        self.effect_durations = {
            'piercing_ammo': 300,      # 5秒（60fps）
            'explosive_ammo': 300,
            'speed_boost': 600,        # 10秒
            'shield': 450,             # 7.5秒
            'multi_shot': 450,
            'ghost_mode': 300,
        }

    def trigger_effect(self, effect_type, player, environment_manager, bullet_manager=None):
        """触发特殊效果"""
        if effect_type == 'piercing_ammo':
            self._apply_piercing_ammo(player)

        elif effect_type == 'explosive_ammo':
            self._apply_explosive_ammo(player)

        elif effect_type == 'wall_destroyer':
            self._apply_wall_destroyer(environment_manager, player)

        elif effect_type == 'teleport':
            self._apply_teleport(player, environment_manager)

        elif effect_type == 'health_swap':
            self._apply_health_swap(player, environment_manager)

        elif effect_type == 'speed_boost':
            self._apply_speed_boost(player)

        elif effect_type == 'shield':
            self._apply_shield(player)

        elif effect_type == 'multi_shot':
            self._apply_multi_shot(player)

        elif effect_type == 'ghost_mode':
            self._apply_ghost_mode(player)

    def _apply_piercing_ammo(self, player):
        """应用穿甲弹效果"""
        self.active_effects['piercing_ammo'] = self.effect_durations['piercing_ammo']
        player.bullet_type = 'PIERCING'

    def _apply_explosive_ammo(self, player):
        """应用爆炸弹效果"""
        self.active_effects['explosive_ammo'] = self.effect_durations['explosive_ammo']
        player.bullet_type = 'EXPLOSIVE'

    def _apply_wall_destroyer(self, environment_manager, player):
        """应用围墙消除效果"""
        # 消除玩家周围的围墙
        player_center = (player.x + player.size[0] // 2, player.y + player.size[1] // 2)
        destruction_radius = 100

        walls_to_remove = []
        for wall in environment_manager.walls:
            if wall.health > 0:
                wall_center = wall.rect.center
                distance = math.sqrt(
                    (player_center[0] - wall_center[0]) ** 2 +
                    (player_center[1] - wall_center[1]) ** 2
                )
                if distance <= destruction_radius:
                    walls_to_remove.append(wall)

        # 随机选择一些围墙进行销毁
        num_to_destroy = min(random.randint(3, 8), len(walls_to_remove))
        if walls_to_remove:
            selected_walls = random.sample(walls_to_remove, num_to_destroy)
            for wall in selected_walls:
                wall.health = 0

    def _apply_teleport(self, player, environment_manager):
        """应用传送效果"""
        # 传送到基地附近
        if environment_manager.player_base:
            base_x = environment_manager.player_base.rect.centerx
            base_y = environment_manager.player_base.rect.centery

            # 在基地周围寻找安全位置
            for distance in range(50, 150, 10):
                for angle in range(0, 360, 30):
                    new_x = base_x + distance * math.cos(math.radians(angle)) - player.size[0] // 2
                    new_y = base_y + distance * math.sin(math.radians(angle)) - player.size[1] // 2

                    # 检查位置是否安全
                    test_rect = pygame.Rect(new_x, new_y, *player.size)
                    is_safe = True

                    # 检查边界
                    from config import GAME_CONFIG
                    if (test_rect.left < 0 or test_rect.right > GAME_CONFIG['WIDTH'] or
                        test_rect.top < 0 or test_rect.bottom > GAME_CONFIG['HEIGHT']):
                        is_safe = False

                    # 检查墙壁
                    if is_safe:
                        for wall in environment_manager.walls:
                            if wall.health > 0 and test_rect.colliderect(wall.rect):
                                is_safe = False
                                break

                    if is_safe:
                        player.x = new_x
                        player.y = new_y
                        player.rect.topleft = (new_x, new_y)
                        return

    def _apply_health_swap(self, player, environment_manager):
        """应用生命互换效果"""
        # 与玩家基地互换生命值
        if environment_manager.player_base:
            player_health = player.health
            base_health = environment_manager.player_base.health

            player.health = min(base_health, player.max_health)
            environment_manager.player_base.health = min(player_health, environment_manager.player_base.max_health)

    def _apply_speed_boost(self, player):
        """应用速度提升效果"""
        self.active_effects['speed_boost'] = self.effect_durations['speed_boost']
        if not hasattr(player, 'original_speed'):
            player.original_speed = player.speed
        player.speed = player.original_speed * 2

    def _apply_shield(self, player):
        """应用护盾效果"""
        self.active_effects['shield'] = self.effect_durations['shield']
        player.has_shield = True

    def _apply_multi_shot(self, player):
        """应用多重射击效果"""
        self.active_effects['multi_shot'] = self.effect_durations['multi_shot']
        player.multi_shot = True

    def _apply_ghost_mode(self, player):
        """应用幽灵模式效果"""
        self.active_effects['ghost_mode'] = self.effect_durations['ghost_mode']
        player.ghost_mode = True

    def update(self, player):
        """更新特殊效果"""
        effects_to_remove = []

        for effect_type, remaining_time in self.active_effects.items():
            remaining_time -= 1
            if remaining_time <= 0:
                self._remove_effect(effect_type, player)
                effects_to_remove.append(effect_type)
            else:
                self.active_effects[effect_type] = remaining_time

        # 移除过期效果
        for effect_type in effects_to_remove:
            del self.active_effects[effect_type]

    def _remove_effect(self, effect_type, player):
        """移除特殊效果"""
        if effect_type in ['piercing_ammo', 'explosive_ammo']:
            player.bullet_type = 'NORMAL'
        elif effect_type == 'speed_boost':
            if hasattr(player, 'original_speed'):
                player.speed = player.original_speed
        elif effect_type == 'shield':
            player.has_shield = False
        elif effect_type == 'multi_shot':
            player.multi_shot = False
        elif effect_type == 'ghost_mode':
            player.ghost_mode = False

    def get_active_effects_info(self):
        """获取当前激活效果信息"""
        return self.active_effects.copy()

    def clear_all_effects(self, player):
        """清除所有效果"""
        for effect_type in list(self.active_effects.keys()):
            self._remove_effect(effect_type, player)
        self.active_effects.clear()

class SpecialWallGenerator:
    """特殊围墙生成器"""
    def __init__(self):
        self.special_wall_types = [
            'piercing_ammo', 'explosive_ammo', 'wall_destroyer',
            'teleport', 'health_swap', 'speed_boost',
            'shield', 'multi_shot', 'ghost_mode'
        ]

        # 各种特殊围墙的出现概率
        self.spawn_probabilities = {
            'piercing_ammo': 0.15,
            'explosive_ammo': 0.15,
            'wall_destroyer': 0.12,
            'teleport': 0.08,
            'health_swap': 0.08,
            'speed_boost': 0.15,
            'shield': 0.12,
            'multi_shot': 0.10,
            'ghost_mode': 0.05
        }

    def generate_special_walls(self, normal_walls, special_wall_ratio=0.1):
        """从普通围墙中生成特殊围墙"""
        if not normal_walls:
            return []

        num_special = max(1, int(len(normal_walls) * special_wall_ratio))
        selected_walls = random.sample(normal_walls, min(num_special, len(normal_walls)))

        special_walls = []
        for wall in selected_walls:
            effect_type = self._choose_effect_type()
            special_wall = SpecialWall(
                wall.rect,
                wall.health,
                effect_type
            )
            special_walls.append(special_wall)

        return special_walls

    def _choose_effect_type(self):
        """根据概率选择特殊效果类型"""
        rand_val = random.random()
        cumulative_prob = 0

        for effect_type, prob in self.spawn_probabilities.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return effect_type

        # 如果没有选中任何效果，返回第一个
        return self.special_wall_types[0]
