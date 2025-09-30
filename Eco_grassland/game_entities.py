# Eco_grassland 生态模拟游戏
# 小羊吃草 - 生态平衡模拟器

import pygame
import random
import math
import time
import sys
from enum import Enum
from typing import List, Tuple, Optional

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
MAP_WIDTH = 2000
MAP_HEIGHT = 1500

# 颜色定义 - 更自然的颜色搭配
COLORS = {
    # 草地颜色 - 使用更自然的绿色系
    'grass_rich': (46, 125, 50),      # 深绿色茂盛草地
    'grass_normal': (76, 175, 80),    # 中绿色普通草地
    'grass_poor': (129, 199, 132),    # 浅绿色贫瘠草地
    'grass_dead': (141, 110, 99),     # 棕色枯萎草地

    # 环境颜色
    'water': (33, 150, 243),          # 自然蓝色水源
    'rock': (120, 144, 156),          # 灰蓝色岩石
    'tree': (62, 142, 65),            # 深绿色树木

    # 动物颜色 - 更真实的动物色彩
    'sheep': (245, 245, 245),         # 白色羊
    'rabbit': (121, 85, 72),          # 棕色兔子
    'cow': (62, 39, 35),              # 深棕色牛

    # UI颜色 - 更现代的UI配色
    'ui_bg': (250, 250, 250),         # 浅灰白色UI背景
    'ui_bg_dark': (240, 240, 240),    # 深色UI背景
    'ui_text': (33, 33, 33),          # 深灰色文字
    'ui_text_light': (117, 117, 117), # 浅灰色文字
    'ui_accent': (76, 175, 80),       # 绿色强调色
    'ui_border': (224, 224, 224),     # 边框颜色
}

# 草地状态枚举
class GrassState(Enum):
    DEAD = 0
    POOR = 1
    NORMAL = 2
    RICH = 3

# 物种类型枚举
class AnimalType(Enum):
    SHEEP = 'sheep'
    RABBIT = 'rabbit'
    COW = 'cow'

# 物种状态枚举
class AnimalState(Enum):
    WANDERING = 'wandering'
    SEEKING_FOOD = 'seeking_food'
    EATING = 'eating'
    SEEKING_WATER = 'seeking_water'
    DRINKING = 'drinking'
    RESTING = 'resting'
    REPRODUCING = 'reproducing'

class GrassTile:
    """草地瓦片类"""

    def __init__(self, x: int, y: int, initial_state: GrassState = GrassState.NORMAL):
        self.x = x
        self.y = y
        self.state = initial_state

        # 生长相关属性
        self.growth_rate = random.uniform(0.8, 1.2)  # 生长速度差异
        self.last_eaten_time = 0
        self.regrowth_time = random.randint(5000, 8000)  # 5-8秒恢复时间（毫秒）

        # 营养和健康属性
        self.nutrition = self.state.value * 25  # 营养值 (0-75)
        self.soil_quality = random.uniform(0.8, 1.2)  # 土壤质量
        self.water_level = random.uniform(0.5, 1.0)   # 水分含量
        self.age = 0  # 草地年龄（天）

        # 环境适应性
        self.stress_resistance = random.uniform(0.7, 1.3)  # 抗压能力
        self.season_factor = 1.0  # 季节影响因子
        self.disease_resistance = random.uniform(0.8, 1.2)  # 抗病能力

        # 生态影响
        self.grazing_pressure = 0.0  # 放牧压力
        self.recovery_bonus = 0.0    # 恢复加成

    def update(self, current_time: int, ecosystem_pressure: float):
        """更新草地状态"""
        # 更新年龄
        time_delta = (current_time - self.last_eaten_time) / 86400000  # 转换为天
        self.age += time_delta

        # 更新营养值
        self.nutrition = self.state.value * 25 * self.soil_quality

        # 计算放牧压力衰减
        self.grazing_pressure *= 0.99  # 放牧压力缓慢衰减

        # 更新水分含量（简化的水循环）
        self.water_level = max(0.3, min(1.0, self.water_level + random.uniform(-0.05, 0.05)))

        # 生长条件检查
        if self.state != GrassState.RICH and current_time - self.last_eaten_time > self.regrowth_time:
            # 计算生长概率，考虑多种因素
            growth_factor = (
                self.growth_rate *
                self.soil_quality *
                self.water_level *
                self.stress_resistance *
                (1 - ecosystem_pressure * 0.3) *
                (1 - self.grazing_pressure * 0.2)
            )

            if random.random() < 0.02 * growth_factor:
                self.state = GrassState(min(self.state.value + 1, GrassState.RICH.value))
                # 恢复时重置一些属性
                if self.state == GrassState.RICH:
                    self.recovery_bonus = 0.1

    def eat(self, current_time: int, amount: int = 1):
        """被啃食"""
        self.last_eaten_time = current_time

        # 增加放牧压力
        self.grazing_pressure += 0.1 * amount
        self.grazing_pressure = min(1.0, self.grazing_pressure)

        # 计算实际被吃掉的量
        old_value = self.state.value
        new_value = max(self.state.value - amount, GrassState.DEAD.value)
        self.state = GrassState(new_value)

        # 更新营养值
        self.nutrition = max(0, self.nutrition - amount * 10)

        # 土壤质量轻微下降（过度放牧影响）
        if self.grazing_pressure > 0.7:
            self.soil_quality *= 0.999

        return old_value - new_value  # 返回实际获得的食物量

    def get_color(self):
        """获取草地颜色"""
        color_map = {
            GrassState.DEAD: COLORS['grass_dead'],
            GrassState.POOR: COLORS['grass_poor'],
            GrassState.NORMAL: COLORS['grass_normal'],
            GrassState.RICH: COLORS['grass_rich']
        }
        return color_map[self.state]

class WaterSource:
    """水源类"""

    def __init__(self, x: int, y: int, radius: int = 30):
        self.x = x
        self.y = y
        self.radius = radius
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制水源"""
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        if -50 <= draw_x <= SCREEN_WIDTH + 50 and -50 <= draw_y <= SCREEN_HEIGHT + 50:
            pygame.draw.circle(screen, COLORS['water'], (draw_x, draw_y), self.radius)

class Obstacle:
    """障碍物类"""

    def __init__(self, x: int, y: int, width: int, height: int, obstacle_type: str = 'rock'):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制障碍物"""
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        if -50 <= draw_x <= SCREEN_WIDTH + 50 and -50 <= draw_y <= SCREEN_HEIGHT + 50:
            color = COLORS['rock'] if self.type == 'rock' else COLORS['tree']
            pygame.draw.rect(screen, color, (draw_x, draw_y, self.width, self.height))

class Animal(pygame.sprite.Sprite):
    """动物基类"""

    def __init__(self, x: int, y: int, animal_type: AnimalType):
        super().__init__()
        self.animal_type = animal_type
        self.x = float(x)
        self.y = float(y)
        self.state = AnimalState.WANDERING

        # 基础生理属性
        self.max_energy = 100
        self.energy = 80
        self.max_health = 100
        self.health = 100

        # 新增：生态系统相关属性
        self.hunger = 20  # 饥饿值 (0-100，越高越饿)
        self.thirst = 15  # 口渴值 (0-100，越高越渴)
        self.tiredness = 10  # 疲劳值 (0-100，越高越累)
        self.age = 0  # 年龄 (天数)
        self.max_age = 365  # 最大年龄 (天数)

        # 生理阈值
        self.hunger_threshold = 30
        self.thirst_threshold = 20
        self.tiredness_threshold = 70
        self.health_critical = 20

        # 繁殖相关
        self.reproduction_age = 30  # 成熟年龄
        self.reproduction_energy = 60  # 繁殖所需能量
        self.reproduction_cooldown = 0  # 繁殖冷却时间
        self.pregnancy_time = 0  # 怀孕时间

        # 移动相关
        self.speed = 1.0
        self.direction = random.uniform(0, 2 * math.pi)
        self.target_x = None
        self.target_y = None

        # 时间相关
        self.last_update_time = pygame.time.get_ticks()
        self.state_change_time = 0
        self.eating_time = 0
        self.last_reproduction_time = 0

        # 视觉相关
        self.size = 10
        self.color = (255, 255, 255)

        # 行为相关
        self.wander_change_time = 0
        self.group_members = []  # 群体成员
        self.stress_level = 0  # 压力水平
        self.social_need = 50  # 社交需求

        self._setup_species_traits()

    def _setup_species_traits(self):
        """设置物种特性"""
        if self.animal_type == AnimalType.SHEEP:
            self.speed = 1.2
            self.size = 12
            self.color = COLORS['sheep']
            self.max_energy = 100
            self.energy_consumption = 0.15
            self.group_distance = 80
            self.detection_range = 100
            self.max_age = 2555  # 羊的平均寿命约7年
            self.reproduction_age = 365  # 1岁成熟
            self.eating_amount = 1
            self.social_need = 70  # 羊是群居动物

        elif self.animal_type == AnimalType.RABBIT:
            self.speed = 2.0
            self.size = 8
            self.color = COLORS['rabbit']
            self.max_energy = 80
            self.energy_consumption = 0.12
            self.group_distance = 40
            self.detection_range = 80
            self.max_age = 1825  # 兔子寿命约5年
            self.reproduction_age = 120  # 4个月成熟
            self.eating_amount = 1
            self.social_need = 40  # 兔子相对独立

        elif self.animal_type == AnimalType.COW:
            self.speed = 0.8
            self.size = 16
            self.color = COLORS['cow']
            self.max_energy = 120
            self.energy_consumption = 0.2
            self.group_distance = 60
            self.detection_range = 90
            self.max_age = 5475  # 牛的寿命约15年
            self.reproduction_age = 730  # 2岁成熟
            self.eating_amount = 2
            self.hunger_threshold = 40
            self.social_need = 50  # 牛有一定社交需求

    def update(self, ecosystem, current_time: int):
        """更新动物状态"""
        # 计算时间差
        time_delta = (current_time - self.last_update_time) / 1000.0

        # 更新生理状态
        self._update_physiology(time_delta)

        # 更新年龄
        self.age += time_delta / 86400  # 转换为天数

        # 更新繁殖冷却
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= time_delta / 86400  # 转换为天数

        # 检查生存状态
        if self.age >= self.max_age or self.health <= 0:
            return False  # 动物死亡

        # 更新能量消耗
        self.energy -= self.energy_consumption * time_delta * 60
        self.last_update_time = current_time

        # 状态机 - 优先级检查
        self._update_state_machine()

        # 根据状态执行行为
        if self.state == AnimalState.WANDERING:
            self._wander(ecosystem)
        elif self.state == AnimalState.SEEKING_FOOD:
            self._seek_food(ecosystem)
        elif self.state == AnimalState.EATING:
            self._eat(ecosystem, current_time)
        elif self.state == AnimalState.DRINKING:
            self._drink(ecosystem, current_time)
        elif self.state == AnimalState.RESTING:
            self._rest(time_delta)
        elif self.state == AnimalState.REPRODUCING:
            self._reproduce(ecosystem, current_time)

        # 群体行为
        if self.animal_type == AnimalType.SHEEP:
            self._update_group_behavior(ecosystem)

        # 边界检查
        self.x = max(self.size, min(MAP_WIDTH - self.size, self.x))
        self.y = max(self.size, min(MAP_HEIGHT - self.size, self.y))

        return True  # 动物存活

    def _update_physiology(self, time_delta):
        """更新生理状态"""
        # 饥饿增长
        self.hunger += 5 * time_delta  # 每秒增加5点饥饿

        # 口渴增长
        self.thirst += 3 * time_delta  # 每秒增加3点口渴

        # 疲劳增长
        if self.state in [AnimalState.SEEKING_FOOD, AnimalState.WANDERING]:
            self.tiredness += 2 * time_delta  # 活动时疲劳增加

        # 限制数值范围
        self.hunger = min(100, max(0, self.hunger))
        self.thirst = min(100, max(0, self.thirst))
        self.tiredness = min(100, max(0, self.tiredness))

        # 健康状态影响
        if self.hunger > 80 or self.thirst > 80:
            self.health -= 10 * time_delta  # 饥饿或口渴时健康下降
        elif self.hunger < 30 and self.thirst < 30:
            self.health += 5 * time_delta   # 良好状态时健康恢复

        # 压力计算
        self.stress_level = (self.hunger + self.thirst + self.tiredness) / 3

        # 限制健康值
        self.health = min(self.max_health, max(0, self.health))

    def _update_state_machine(self):
        """更新状态机"""
        # 危急状态检查
        if self.health < self.health_critical:
            self.state = AnimalState.RESTING
            return

        # 饥饿检查
        if self.hunger > self.hunger_threshold:
            self.state = AnimalState.SEEKING_FOOD
            self.target_x = None
            self.target_y = None
            return

        # 口渴检查
        if self.thirst > self.thirst_threshold:
            self.state = AnimalState.SEEKING_WATER
            self.target_x = None
            self.target_y = None
            return

        # 疲劳检查
        if self.tiredness > self.tiredness_threshold:
            self.state = AnimalState.RESTING
            return

        # 繁殖检查
        if (self.age > self.reproduction_age and
            self.energy > self.reproduction_energy and
            self.reproduction_cooldown <= 0):
            self.state = AnimalState.REPRODUCING
            return

        # 默认状态
        if self.state not in [AnimalState.EATING, AnimalState.DRINKING]:
            self.state = AnimalState.WANDERING

    def _rest(self, time_delta):
        """休息行为"""
        # 恢复疲劳和少量健康
        self.tiredness -= 20 * time_delta
        self.health += 2 * time_delta

        # 限制数值
        self.tiredness = max(0, self.tiredness)
        self.health = min(self.max_health, self.health)

    def _reproduce(self, ecosystem, current_time):
        """繁殖行为"""
        # 简化的繁殖逻辑
        if self.reproduction_cooldown <= 0:
            # 寻找附近的同类
            nearby_animals = ecosystem.get_animals_in_area(int(self.x), int(self.y), self.detection_range)
            mates = [a for a in nearby_animals if a.animal_type == self.animal_type and a != self]

            if mates:
                # 消耗能量进行繁殖
                self.energy -= 30
                self.reproduction_cooldown = 30  # 30天冷却

                # 有一定概率产生后代
                if random.random() < 0.3:  # 30%概率成功
                    offspring_x = self.x + random.randint(-20, 20)
                    offspring_y = self.y + random.randint(-20, 20)
                    ecosystem.add_animal(self.animal_type, int(offspring_x), int(offspring_y))

                self.state = AnimalState.WANDERING

    def _wander(self, ecosystem):
        """随机漫步行为"""
        current_time = pygame.time.get_ticks()

        if current_time - self.wander_change_time > 2000:  # 每2秒改变方向
            self.direction = random.uniform(0, 2 * math.pi)
            self.wander_change_time = current_time

        # 移动
        dx = math.cos(self.direction) * self.speed
        dy = math.sin(self.direction) * self.speed

        new_x = self.x + dx
        new_y = self.y + dy

        # 检查碰撞
        if not self._check_collision(new_x, new_y, ecosystem):
            self.x = new_x
            self.y = new_y
        else:
            # 遇到障碍物时随机转向
            self.direction = random.uniform(0, 2 * math.pi)

    def _seek_food(self, ecosystem):
        """寻找食物行为"""
        if self.target_x is None or self.target_y is None:
            # 寻找最近的食物源
            best_grass = None
            best_distance = float('inf')

            search_radius = self.detection_range
            start_x = max(0, int((self.x - search_radius) // 20))
            end_x = min(len(ecosystem.grass_grid[0]), int((self.x + search_radius) // 20) + 1)
            start_y = max(0, int((self.y - search_radius) // 20))
            end_y = min(len(ecosystem.grass_grid), int((self.y + search_radius) // 20) + 1)

            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    grass = ecosystem.grass_grid[y][x]
                    if grass.state.value >= 1:  # 有食物的草地
                        distance = math.sqrt((grass.x - self.x) ** 2 + (grass.y - self.y) ** 2)
                        if distance < best_distance:
                            best_distance = distance
                            best_grass = grass

            if best_grass:
                self.target_x = best_grass.x
                self.target_y = best_grass.y
            else:
                # 没找到食物，随机游走
                self.state = AnimalState.WANDERING
                return

        # 向目标移动
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < self.size:
            # 到达目标，开始进食
            self.state = AnimalState.EATING
            self.eating_time = pygame.time.get_ticks()
        else:
            # 继续移动
            move_speed = self.speed * (0.5 if self.energy < 20 else 1.0)  # 低能量时移动变慢
            dx = (dx / distance) * move_speed
            dy = (dy / distance) * move_speed

            new_x = self.x + dx
            new_y = self.y + dy

            if not self._check_collision(new_x, new_y, ecosystem):
                self.x = new_x
                self.y = new_y

    def _eat(self, ecosystem, current_time: int):
        """进食行为"""
        eating_duration = 2000  # 2秒进食时间

        if current_time - self.eating_time > eating_duration:
            # 结束进食
            grass_x = int(self.x // 20)
            grass_y = int(self.y // 20)

            if 0 <= grass_x < len(ecosystem.grass_grid[0]) and 0 <= grass_y < len(ecosystem.grass_grid):
                grass = ecosystem.grass_grid[grass_y][grass_x]
                eating_amount = getattr(self, 'eating_amount', 1)
                food_gained = grass.eat(current_time, eating_amount)

                # 恢复能量
                energy_gain = food_gained * 15
                self.energy = min(self.max_energy, self.energy + energy_gain)

            # 进食后状态转换
            if self.energy > self.hunger_threshold + 20:
                self.state = AnimalState.WANDERING
            else:
                self.state = AnimalState.SEEKING_FOOD

            self.target_x = None
            self.target_y = None

    def _drink(self, ecosystem, current_time: int):
        """饮水行为"""
        # 恢复能量
        self.energy = min(self.max_energy, self.energy + 0.5)

        if self.energy > self.thirst_threshold + 30:
            self.state = AnimalState.WANDERING

    def _update_group_behavior(self, ecosystem):
        """更新群体行为（仅适用于羊）"""
        if self.state == AnimalState.WANDERING:
            # 寻找附近的同类
            nearby_sheep = []
            for animal in ecosystem.animals:
                if (animal != self and
                    animal.animal_type == AnimalType.SHEEP and
                    math.sqrt((animal.x - self.x) ** 2 + (animal.y - self.y) ** 2) < self.group_distance):
                    nearby_sheep.append(animal)

            if nearby_sheep:
                # 计算群体中心
                center_x = sum(sheep.x for sheep in nearby_sheep) / len(nearby_sheep)
                center_y = sum(sheep.y for sheep in nearby_sheep) / len(nearby_sheep)

                # 向群体中心移动
                dx = center_x - self.x
                dy = center_y - self.y
                distance = math.sqrt(dx ** 2 + dy ** 2)

                if distance > self.group_distance * 0.6:  # 距离过远时靠近
                    influence = 0.3  # 群体影响强度
                    self.direction += influence * math.atan2(dy, dx)

    def _check_collision(self, x: float, y: float, ecosystem) -> bool:
        """检查碰撞"""
        # 检查边界
        if x < self.size or x > MAP_WIDTH - self.size or y < self.size or y > MAP_HEIGHT - self.size:
            return True

        # 检查障碍物
        animal_rect = pygame.Rect(x - self.size, y - self.size, self.size * 2, self.size * 2)
        for obstacle in ecosystem.obstacles:
            if animal_rect.colliderect(obstacle.rect):
                return True

        return False

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """绘制动物"""
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)

        if -50 <= draw_x <= SCREEN_WIDTH + 50 and -50 <= draw_y <= SCREEN_HEIGHT + 50:
            # 绘制阴影
            shadow_offset = 3
            pygame.draw.ellipse(screen, (0, 0, 0, 50),
                              (draw_x - self.size + shadow_offset,
                               draw_y - self.size//2 + shadow_offset,
                               self.size * 2, self.size))

            # 根据动物类型绘制不同形状
            if self.animal_type == AnimalType.SHEEP:
                # 绘制羊 - 蓬松的圆形身体
                body_color = (245, 245, 245)  # 白色
                pygame.draw.circle(screen, body_color, (draw_x, draw_y), self.size)
                pygame.draw.circle(screen, (220, 220, 220), (draw_x, draw_y), self.size, 2)

                # 绘制头部
                head_color = (200, 180, 160)  # 浅棕色
                head_x = draw_x + int(self.size * 0.7 * math.cos(self.direction))
                head_y = draw_y + int(self.size * 0.7 * math.sin(self.direction))
                pygame.draw.circle(screen, head_color, (head_x, head_y), self.size//2)

                # 绘制耳朵
                ear_size = 4
                ear1_x = head_x + int(ear_size * math.cos(self.direction + math.pi/3))
                ear1_y = head_y + int(ear_size * math.sin(self.direction + math.pi/3))
                ear2_x = head_x + int(ear_size * math.cos(self.direction - math.pi/3))
                ear2_y = head_y + int(ear_size * math.sin(self.direction - math.pi/3))
                pygame.draw.circle(screen, head_color, (ear1_x, ear1_y), 3)
                pygame.draw.circle(screen, head_color, (ear2_x, ear2_y), 3)

            elif self.animal_type == AnimalType.RABBIT:
                # 绘制兔子 - 椭圆形身体
                body_color = (160, 120, 80)  # 棕色
                body_rect = pygame.Rect(draw_x - self.size, draw_y - self.size//2,
                                      self.size * 2, self.size)
                pygame.draw.ellipse(screen, body_color, body_rect)
                pygame.draw.ellipse(screen, (140, 100, 60), body_rect, 2)

                # 绘制头部
                head_x = draw_x + int(self.size * 0.8 * math.cos(self.direction))
                head_y = draw_y + int(self.size * 0.8 * math.sin(self.direction))
                pygame.draw.circle(screen, body_color, (head_x, head_y), self.size//2)

                # 绘制长耳朵
                ear_length = 8
                ear1_x = head_x + int(ear_length * math.cos(self.direction + math.pi/4))
                ear1_y = head_y + int(ear_length * math.sin(self.direction + math.pi/4))
                ear2_x = head_x + int(ear_length * math.cos(self.direction - math.pi/4))
                ear2_y = head_y + int(ear_length * math.sin(self.direction - math.pi/4))
                pygame.draw.line(screen, body_color, (head_x, head_y), (ear1_x, ear1_y), 3)
                pygame.draw.line(screen, body_color, (head_x, head_y), (ear2_x, ear2_y), 3)

                # 绘制尾巴
                tail_x = draw_x - int(self.size * 0.8 * math.cos(self.direction))
                tail_y = draw_y - int(self.size * 0.8 * math.sin(self.direction))
                pygame.draw.circle(screen, (255, 255, 255), (tail_x, tail_y), 3)

            elif self.animal_type == AnimalType.COW:
                # 绘制牛 - 矩形身体
                body_color = (80, 60, 40)  # 深棕色
                body_rect = pygame.Rect(draw_x - self.size, draw_y - self.size//2,
                                      self.size * 2, self.size)
                pygame.draw.rect(screen, body_color, body_rect, border_radius=5)
                pygame.draw.rect(screen, (60, 40, 20), body_rect, 2, border_radius=5)

                # 绘制斑点
                spot_color = (40, 30, 20)
                for i in range(3):
                    spot_x = draw_x + random.randint(-self.size//2, self.size//2)
                    spot_y = draw_y + random.randint(-self.size//3, self.size//3)
                    pygame.draw.circle(screen, spot_color, (spot_x, spot_y), 4)

                # 绘制头部
                head_color = (100, 80, 60)
                head_x = draw_x + int(self.size * 0.9 * math.cos(self.direction))
                head_y = draw_y + int(self.size * 0.9 * math.sin(self.direction))
                head_rect = pygame.Rect(head_x - self.size//2, head_y - self.size//3,
                                      self.size, self.size//1.5)
                pygame.draw.rect(screen, head_color, head_rect, border_radius=3)

                # 绘制角
                horn_length = 6
                horn1_x = head_x + int(horn_length * math.cos(self.direction + math.pi/6))
                horn1_y = head_y + int(horn_length * math.sin(self.direction + math.pi/6))
                horn2_x = head_x + int(horn_length * math.cos(self.direction - math.pi/6))
                horn2_y = head_y + int(horn_length * math.sin(self.direction - math.pi/6))
                pygame.draw.line(screen, (240, 240, 240), (head_x, head_y), (horn1_x, horn1_y), 2)
                pygame.draw.line(screen, (240, 240, 240), (head_x, head_y), (horn2_x, horn2_y), 2)

            # 绘制健康状态条
            health_bar_width = self.size * 2
            health_bar_height = 4
            health_bar_x = draw_x - health_bar_width // 2
            health_bar_y = draw_y - self.size - 10

            # 背景
            pygame.draw.rect(screen, (100, 100, 100),
                           (health_bar_x, health_bar_y, health_bar_width, health_bar_height))

            # 健康值
            health_ratio = self.health / 100.0
            health_width = int(health_bar_width * health_ratio)
            if health_ratio > 0.6:
                health_color = (0, 200, 0)
            elif health_ratio > 0.3:
                health_color = (255, 165, 0)
            else:
                health_color = (255, 0, 0)

            pygame.draw.rect(screen, health_color,
                           (health_bar_x, health_bar_y, health_width, health_bar_height))

            # 绘制状态指示器
            indicator_y = draw_y - self.size - 20
            if self.state == AnimalState.EATING:
                pygame.draw.circle(screen, (0, 255, 0), (draw_x, indicator_y), 4)
                # 绘制小草图标
                pygame.draw.line(screen, (0, 200, 0), (draw_x-2, indicator_y+1), (draw_x+2, indicator_y-1), 2)
            elif self.state == AnimalState.SEEKING_FOOD:
                pygame.draw.circle(screen, (255, 255, 0), (draw_x, indicator_y), 4)
                # 绘制搜索图标
                pygame.draw.circle(screen, (255, 255, 0), (draw_x, indicator_y), 3, 1)
            elif self.state == AnimalState.RESTING:
                pygame.draw.circle(screen, (100, 100, 255), (draw_x, indicator_y), 4)
                # 绘制休息图标
                for i in range(3):
                    pygame.draw.circle(screen, (100, 100, 255), (draw_x-4+i*2, indicator_y), 1)
            elif self.state == AnimalState.WANDERING:
                pygame.draw.circle(screen, (200, 200, 200), (draw_x, indicator_y), 4)
                # 绘制移动箭头
                arrow_end_x = draw_x + int(3 * math.cos(self.direction))
                arrow_end_y = indicator_y + int(3 * math.sin(self.direction))
                pygame.draw.line(screen, (200, 200, 200), (draw_x, indicator_y), (arrow_end_x, arrow_end_y), 2)

            # 绘制健康指示器（角落的小点）
            health_ratio = self.health / self.max_health
            if health_ratio > 0.7:
                health_indicator_color = (0, 255, 0)  # 绿色 - 健康
            elif health_ratio > 0.3:
                health_indicator_color = (255, 255, 0)  # 黄色 - 一般
            else:
                health_indicator_color = (255, 0, 0)  # 红色 - 危险
            pygame.draw.circle(screen, health_indicator_color, (draw_x + self.size - 5, draw_y - self.size + 5), 2)

            # 绘制能量条
            bar_width = self.size * 2
            bar_height = 4
            bar_x = draw_x - bar_width // 2
            bar_y = draw_y - self.size - 15

            # 背景
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # 能量条
            energy_width = int(bar_width * (self.energy / self.max_energy))
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, energy_width, bar_height))

def main():
    """游戏主函数"""
    # 这里只是动物类的定义，主游戏循环将在后续文件中实现
    pass

if __name__ == "__main__":
    main()
