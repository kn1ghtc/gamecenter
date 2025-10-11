# 生态系统管理器
# 管理整个游戏世界的生态环境

import pygame
import random
import math
from typing import List, Tuple
from gamecenter.Eco_grassland.game_entities import *

class EcoSystem:
    """生态系统管理器"""

    def __init__(self):
        self.grass_grid = []
        self.animals = []
        self.water_sources = []
        self.obstacles = []

        # 生态统计
        self.total_grass_tiles = 0
        self.dead_grass_count = 0
        self.carrying_capacity = 0
        self.ecosystem_pressure = 0.0

        # 时间管理
        self.current_time = 0
        self.last_ecosystem_update = 0

        self._initialize_world()

    def _initialize_world(self):
        """初始化游戏世界"""
        # 创建草地网格（20x20像素per tile）
        grid_width = MAP_WIDTH // 20
        grid_height = MAP_HEIGHT // 20

        for y in range(grid_height):
            row = []
            for x in range(grid_width):
                # 随机生成不同状态的草地
                state_rand = random.random()
                if state_rand < 0.1:
                    state = GrassState.DEAD
                elif state_rand < 0.3:
                    state = GrassState.POOR
                elif state_rand < 0.7:
                    state = GrassState.NORMAL
                else:
                    state = GrassState.RICH

                grass = GrassTile(x * 20 + 10, y * 20 + 10, state)
                row.append(grass)
            self.grass_grid.append(row)

        self.total_grass_tiles = grid_width * grid_height

        # 创建水源
        for _ in range(8):
            x = random.randint(50, MAP_WIDTH - 50)
            y = random.randint(50, MAP_HEIGHT - 50)
            water = WaterSource(x, y, random.randint(25, 40))
            self.water_sources.append(water)

        # 创建障碍物（岩石和树木）
        for _ in range(30):
            x = random.randint(0, MAP_WIDTH - 40)
            y = random.randint(0, MAP_HEIGHT - 40)
            width = random.randint(20, 60)
            height = random.randint(20, 60)
            obstacle_type = random.choice(['rock', 'tree'])
            obstacle = Obstacle(x, y, width, height, obstacle_type)
            self.obstacles.append(obstacle)

        # 初始化动物
        self._spawn_initial_animals()

        # 计算承载能力
        self.carrying_capacity = self.total_grass_tiles // 200  # 每200个草地瓦片支持1只动物

    def _spawn_initial_animals(self):
        """生成初始动物"""
        # 生成羊群
        for _ in range(8):
            x, y = self._find_safe_spawn_location()
            sheep = Animal(x, y, AnimalType.SHEEP)
            self.animals.append(sheep)

        # 生成兔子
        for _ in range(12):
            x, y = self._find_safe_spawn_location()
            rabbit = Animal(x, y, AnimalType.RABBIT)
            self.animals.append(rabbit)

        # 生成牛
        for _ in range(4):
            x, y = self._find_safe_spawn_location()
            cow = Animal(x, y, AnimalType.COW)
            self.animals.append(cow)

    def _find_safe_spawn_location(self) -> Tuple[int, int]:
        """寻找安全的生成位置"""
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(50, MAP_WIDTH - 50)
            y = random.randint(50, MAP_HEIGHT - 50)

            # 检查是否与障碍物碰撞
            spawn_rect = pygame.Rect(x - 20, y - 20, 40, 40)
            collision = False

            for obstacle in self.obstacles:
                if spawn_rect.colliderect(obstacle.rect):
                    collision = True
                    break

            if not collision:
                return x, y

        # 如果找不到安全位置，返回地图中心
        return MAP_WIDTH // 2, MAP_HEIGHT // 2

    def update(self, current_time: int):
        """更新整个生态系统"""
        self.current_time = current_time

        # 更新生态压力
        self._update_ecosystem_pressure()

        # 更新草地（每秒更新一次）
        if current_time - self.last_ecosystem_update > 1000:
            self._update_grass()
            self.last_ecosystem_update = current_time

        # 更新动物
        for animal in self.animals[:]:  # 使用切片防止在迭代时修改列表
            alive = animal.update(self, current_time)

            # 移除死亡的动物
            if not alive or animal.health <= 0:
                self.animals.remove(animal)

    def _update_ecosystem_pressure(self):
        """更新生态压力"""
        # 计算动物密度压力
        animal_count = len(self.animals)
        density_pressure = max(0, (animal_count - self.carrying_capacity) / self.carrying_capacity) if self.carrying_capacity > 0 else 0

        # 计算草地枯萎压力
        self.dead_grass_count = sum(1 for row in self.grass_grid for grass in row if grass.state == GrassState.DEAD)
        grass_pressure = self.dead_grass_count / self.total_grass_tiles

        # 综合生态压力（权重：密度70%，草地30%）
        self.ecosystem_pressure = min(1.0, density_pressure * 0.7 + grass_pressure * 0.3)

        # 应用生态压力效果
        for animal in self.animals:
            base_consumption = getattr(animal, 'base_energy_consumption', animal.energy_consumption)
            stress_factor = 0.5 if grass_pressure > 0.3 else 0.2
            multiplier = 1 + self.ecosystem_pressure * stress_factor
            animal.energy_consumption = base_consumption * multiplier

    def _update_grass(self):
        """更新草地状态"""
        for row in self.grass_grid:
            for grass in row:
                grass.update(self.current_time, self.ecosystem_pressure)

    def add_animal(self, animal_type: AnimalType, x: int = None, y: int = None):
        """添加新动物"""
        if x is None or y is None:
            x, y = self._find_safe_spawn_location()

        animal = Animal(x, y, animal_type)
        self.animals.append(animal)

    def get_grass_at_position(self, x: float, y: float) -> GrassTile:
        """获取指定位置的草地"""
        grid_x = int(x // 20)
        grid_y = int(y // 20)

        if 0 <= grid_x < len(self.grass_grid[0]) and 0 <= grid_y < len(self.grass_grid):
            return self.grass_grid[grid_y][grid_x]
        return None

    def get_animals_in_area(self, x: int, y: int, radius: int) -> List[Animal]:
        """获取指定区域内的动物"""
        animals_in_area = []
        for animal in self.animals:
            distance = math.sqrt((animal.x - x) ** 2 + (animal.y - y) ** 2)
            if distance <= radius:
                animals_in_area.append(animal)
        return animals_in_area

    def get_ecosystem_stats(self) -> dict:
        """获取生态系统统计信息"""
        # 统计各种动物数量
        sheep_count = sum(1 for animal in self.animals if animal.animal_type == AnimalType.SHEEP)
        rabbit_count = sum(1 for animal in self.animals if animal.animal_type == AnimalType.RABBIT)
        cow_count = sum(1 for animal in self.animals if animal.animal_type == AnimalType.COW)

        # 统计草地状态
        grass_stats = {state: 0 for state in GrassState}
        for row in self.grass_grid:
            for grass in row:
                grass_stats[grass.state] += 1

        return {
            'total_animals': len(self.animals),
            'sheep_count': sheep_count,
            'rabbit_count': rabbit_count,
            'cow_count': cow_count,
            'carrying_capacity': self.carrying_capacity,
            'ecosystem_pressure': self.ecosystem_pressure,
            'grass_stats': grass_stats,
            'dead_grass_percentage': (self.dead_grass_count / self.total_grass_tiles) * 100
        }

    def is_ecosystem_collapsed(self) -> bool:
        """检查生态系统是否崩溃（游戏结束条件）"""
        # 条件1：所有动物死亡 - 立即游戏结束
        all_animals_dead = len(self.animals) == 0

        # 条件2：超过90%的草地枯萎
        dead_grass_ratio = self.dead_grass_count / self.total_grass_tiles
        ecosystem_destroyed = dead_grass_ratio > 0.9

        return all_animals_dead or ecosystem_destroyed

    def is_ecosystem_endangered(self) -> bool:
        """检查生态系统是否濒危（警告状态）"""
        # 所有动物死亡或草地严重枯萎
        all_animals_dead = len(self.animals) == 0
        dead_grass_ratio = self.dead_grass_count / self.total_grass_tiles
        serious_degradation = dead_grass_ratio > 0.8

        return all_animals_dead or serious_degradation

    def get_collapse_reason(self) -> str:
        """获取生态系统崩溃的原因"""
        if len(self.animals) == 0:
            return "所有动物都已死亡！生态系统失去了生命力。"

        dead_grass_ratio = self.dead_grass_count / self.total_grass_tiles
        if dead_grass_ratio > 0.9:
            return f"草地严重枯萎（{dead_grass_ratio*100:.1f}%）！生态环境无法维持生命。"

        return "生态系统面临严重危机。"

    def draw_grass(self, screen: pygame.Surface, camera):
        """绘制草地（使用摄像机对象进行坐标转换与缩放自适应）"""
        # 可见区域（世界坐标）
        vis_x, vis_y, vis_w, vis_h = camera.get_visible_rect()

        # 扩展一点边距以避免边缘闪烁
        margin = 40 / max(0.001, camera.zoom)

        start_x = max(0, int((vis_x - margin) // 20))
        end_x = min(len(self.grass_grid[0]), int((vis_x + vis_w + margin) // 20) + 1)
        start_y = max(0, int((vis_y - margin) // 20))
        end_y = min(len(self.grass_grid), int((vis_y + vis_h + margin) // 20) + 1)

        screen_w = screen.get_width()
        screen_h = screen.get_height()

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                grass = self.grass_grid[y][x]
                screen_x, screen_y = camera.world_to_screen(grass.x, grass.y)

                # 简单可见性裁剪（使用屏幕尺寸）
                if -40 <= screen_x <= screen_w + 40 and -40 <= screen_y <= screen_h + 40:
                    self._draw_grass_tile(screen, grass, screen_x, screen_y, camera.zoom)

    def _draw_grass_tile(self, screen: pygame.Surface, grass, draw_x: int, draw_y: int, zoom: float):
        """绘制单个草地块"""
        # 使用草地位置作为随机种子，确保每次绘制一致
        random.seed(grass.x * 1000 + grass.y)

        base_color = grass.get_color()
        # 绘制时根据缩放调整像素尺寸
        tile_size = max(1, int(20 * zoom))
        half = tile_size // 2

        # 绘制地面基色（略深一些）
        ground_color = tuple(max(0, c - 30) for c in base_color)
        pygame.draw.rect(screen, ground_color, (draw_x - half, draw_y - half, tile_size, tile_size))

        # 如果缩放很小，绘制简化版本以提升性能
        if tile_size < 4:
            random.seed()
            return

        if grass.state == GrassState.DEAD:
            # 死草 - 绘制枯黄的残茬（缩放后宽度为1-3）
            for i in range(3):
                stub_x = draw_x - int(8 * zoom) + i * int(8 * zoom) + random.randint(-2, 2)
                stub_y = draw_y - int(5 * zoom) + random.randint(-3, 3)
                pygame.draw.line(screen, (139, 119, 101), (stub_x, stub_y + int(5*zoom)), (stub_x, stub_y), max(1, int(2*zoom)))

        elif grass.state == GrassState.POOR:
            for i in range(3):
                grass_x = draw_x - int(6 * zoom) + i * int(6 * zoom) + random.randint(-1, 1)
                grass_y = draw_y - int(2 * zoom) + random.randint(-2, 2)
                grass_height = max(1, int(random.randint(3, 5) * zoom))
                grass_color = (120, 140, 60)
                pygame.draw.line(screen, grass_color, (grass_x, grass_y + int(3*zoom)), (grass_x, grass_y + int(3*zoom) - grass_height), max(1, int(2*zoom)))

        elif grass.state == GrassState.NORMAL:
            for i in range(5):
                grass_x = draw_x - int(8 * zoom) + i * int(4 * zoom) + random.randint(-1, 1)
                grass_y = draw_y - int(3 * zoom) + random.randint(-2, 2)
                grass_height = max(1, int(random.randint(4, 7) * zoom))
                green_base = random.randint(100, 140)
                grass_color = (40, green_base, 50)
                pygame.draw.line(screen, grass_color, (grass_x, grass_y + int(4*zoom)), (grass_x, grass_y + int(4*zoom) - grass_height), max(1, int(2*zoom)))

        elif grass.state == GrassState.RICH:
            for i in range(7):
                grass_x = draw_x - int(8 * zoom) + int(i * 2.5 * zoom) + random.randint(-1, 1)
                grass_y = draw_y - int(3 * zoom) + random.randint(-2, 2)
                grass_height = max(1, int(random.randint(6, 9) * zoom))
                green_base = random.randint(140, 180)
                grass_color = (20, green_base, 30)
                pygame.draw.line(screen, grass_color, (grass_x, grass_y + int(4*zoom)), (grass_x, grass_y + int(4*zoom) - grass_height), max(1, int(2*zoom)))
                tip_color = tuple(min(255, c + 20) for c in grass_color)
                pygame.draw.circle(screen, tip_color, (grass_x, grass_y + int(4*zoom) - grass_height), max(1, int(1*zoom)))

            if random.random() < 0.15:
                flower_x = draw_x + random.randint(-int(6*zoom), int(6*zoom))
                flower_y = draw_y + random.randint(-int(6*zoom), int(6*zoom))
                flower_colors = [(255, 255, 100), (255, 200, 200), (200, 200, 255), (255, 255, 255)]
                flower_color = random.choice(flower_colors)
                pygame.draw.circle(screen, flower_color, (flower_x, flower_y), max(1, int(2*zoom)))

        # 根据草地状态添加发光效果
        if grass.state == GrassState.RICH and zoom >= 0.6:
            glow_surface = pygame.Surface((int(24*zoom), int(24*zoom)), pygame.SRCALPHA)
            glow_color = (*base_color, max(10, int(30 * zoom)))
            pygame.draw.circle(glow_surface, glow_color, (glow_surface.get_width()//2, glow_surface.get_height()//2), glow_surface.get_width()//2)
            screen.blit(glow_surface, (draw_x - glow_surface.get_width()//2, draw_y - glow_surface.get_height()//2))

        random.seed()

    def draw_water(self, screen: pygame.Surface, camera):
        """绘制水源（使用摄像机对象）"""
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        for water in self.water_sources:
            water.draw(screen, camera)

    def draw_obstacles(self, screen: pygame.Surface, camera):
        """绘制障碍物（使用摄像机对象）"""
        for obstacle in self.obstacles:
            obstacle.draw(screen, camera)

    def draw_animals(self, screen: pygame.Surface, camera):
        """绘制动物（使用摄像机对象）"""
        for animal in self.animals:
            animal.draw(screen, camera)
