"""
关卡管理模块
处理关卡生成、加载和保存
"""
import os
import random
import math
import pygame
from config import (MAP_CONFIG, LEVEL_CONFIG, GAME_CONFIG, WALL_CONFIG)
from environment import Wall, PlayerBase, EnemyBase
from tank_system import EnemyTank

class LevelManager:
    """关卡管理器"""
    def __init__(self):
        self.current_level = 1
        self.max_level = MAP_CONFIG['MAX_LEVEL']

        # 确保assets目录存在
        self.assets_dir = 'assets'
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)

    def generate_level_data(self, level):
        """生成关卡数据"""
        # 生成迷宫墙壁
        walls_data = self._generate_maze(level)

        # 玩家起始位置
        player_pos = self._get_player_start_position()

        # 基地位置
        player_base_pos = self._get_player_base_position()
        enemy_base_pos = self._get_enemy_base_position()

        # 敌人数据
        enemies_data = self._generate_enemies_data(level, walls_data)

        return {
            'walls': walls_data,
            'player_pos': player_pos,
            'player_base_pos': player_base_pos,
            'enemy_base_pos': enemy_base_pos,
            'enemies': enemies_data
        }

    def _generate_maze(self, level):
        """生成迷宫墙壁"""
        cell_size = MAP_CONFIG['CELL_SIZE']
        grid_width = MAP_CONFIG['GRID_WIDTH']
        grid_height = MAP_CONFIG['GRID_HEIGHT']

        # 初始化网格（1=墙壁，0=通路）
        grid = [[1 for _ in range(grid_width)] for _ in range(grid_height)]

        def carve(x, y):
            """递归雕刻通路"""
            grid[y][x] = 0
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = x + dx * 2, y + dy * 2
                if (0 <= nx < grid_width and 0 <= ny < grid_height and
                    grid[ny][nx] == 1):
                    grid[y + dy][x + dx] = 0
                    carve(nx, ny)

        # 从多个起始点开始雕刻
        starts = [(1, 1), (grid_width-2, 1), (1, grid_height-2), (grid_width-2, grid_height-2)]
        for sx, sy in starts:
            if grid[sy][sx] == 1:
                carve(sx, sy)

        # 根据关卡增加额外通路
        extra_carves = level // LEVEL_CONFIG['MAZE_COMPLEXITY_INCREMENT']
        for _ in range(extra_carves):
            wall_cells = [(x, y) for y in range(1, grid_height-1, 2)
                         for x in range(1, grid_width-1, 2) if grid[y][x] == 1]
            if wall_cells:
                x, y = random.choice(wall_cells)
                carve(x, y)

        # 转换为墙壁数据
        walls_data = []
        for y in range(grid_height):
            for x in range(grid_width):
                if grid[y][x] == 1:
                    walls_data.append({
                        'x': x * cell_size,
                        'y': y * cell_size,
                        'width': cell_size,
                        'height': cell_size,
                        'health': WALL_CONFIG['HEALTH']
                    })

        return walls_data

    def _get_player_start_position(self):
        """获取玩家起始位置"""
        cell_size = MAP_CONFIG['CELL_SIZE']
        return {
            'x': 1 * cell_size + cell_size // 2,
            'y': 1 * cell_size + cell_size // 2
        }

    def _get_player_base_position(self):
        """获取玩家基地位置"""
        return {
            'x': GAME_CONFIG['WIDTH'] // 2 - 25,
            'y': GAME_CONFIG['HEIGHT'] - 70
        }

    def _get_enemy_base_position(self):
        """获取敌方基地位置"""
        return {
            'x': GAME_CONFIG['WIDTH'] // 2 - 25,
            'y': 20
        }

    def _generate_enemies_data(self, level, walls_data):
        """生成敌人数据"""
        cell_size = MAP_CONFIG['CELL_SIZE']
        grid_width = MAP_CONFIG['GRID_WIDTH']
        grid_height = MAP_CONFIG['GRID_HEIGHT']

        # 找到所有可通行的位置
        path_cells = []
        for y in range(grid_height):
            for x in range(grid_width):
                cell_rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                is_blocked = any(
                    cell_rect.colliderect(pygame.Rect(w['x'], w['y'], w['width'], w['height']))
                    for w in walls_data
                )
                if not is_blocked:
                    path_cells.append((x, y))

        # 计算敌人数量
        base_enemies = LEVEL_CONFIG['ENEMIES_BASE']
        increment = level // LEVEL_CONFIG['ENEMIES_INCREMENT_INTERVAL']
        num_enemies = min(base_enemies + increment, LEVEL_CONFIG['MAX_ENEMIES'])

        # 生成敌人位置
        random.shuffle(path_cells)
        enemies_data = []

        for i in range(min(num_enemies, len(path_cells))):
            x, y = path_cells[i]
            enemy_x = x * cell_size + cell_size // 2
            enemy_y = y * cell_size + cell_size // 2
            angle = random.uniform(0, 2 * math.pi)

            enemies_data.append({
                'x': enemy_x,
                'y': enemy_y,
                'angle': angle
            })

        return enemies_data

    def save_level_to_file(self, level, level_data):
        """保存关卡到文件"""
        map_file = os.path.join(self.assets_dir, f'level{level}.map')

        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(f'# Level {level} Map Data\n')

            # 玩家位置
            player_pos = level_data['player_pos']
            f.write(f'PLAYER {player_pos["x"]} {player_pos["y"]}\n')

            # 基地位置
            player_base = level_data['player_base_pos']
            f.write(f'PLAYER_BASE {player_base["x"]} {player_base["y"]}\n')

            enemy_base = level_data['enemy_base_pos']
            f.write(f'ENEMY_BASE {enemy_base["x"]} {enemy_base["y"]}\n')

            # 墙壁
            for wall in level_data['walls']:
                f.write(f'WALL {wall["x"]} {wall["y"]} {wall["width"]} {wall["height"]} {wall["health"]}\n')

            # 敌人
            for enemy in level_data['enemies']:
                f.write(f'ENEMY {enemy["x"]} {enemy["y"]} {enemy["angle"]}\n')

    def load_level_from_file(self, level):
        """从文件加载关卡"""
        map_file = os.path.join(self.assets_dir, f'level{level}.map')

        if not os.path.exists(map_file):
            return None

        level_data = {
            'walls': [],
            'player_pos': None,
            'player_base_pos': None,
            'enemy_base_pos': None,
            'enemies': []
        }

        with open(map_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if not parts or parts[0].startswith('#'):
                    continue

                if parts[0] == 'WALL' and len(parts) >= 6:
                    level_data['walls'].append({
                        'x': int(parts[1]),
                        'y': int(parts[2]),
                        'width': int(parts[3]),
                        'height': int(parts[4]),
                        'health': int(parts[5])
                    })
                elif parts[0] == 'ENEMY' and len(parts) >= 4:
                    level_data['enemies'].append({
                        'x': float(parts[1]),
                        'y': float(parts[2]),
                        'angle': float(parts[3])
                    })
                elif parts[0] == 'PLAYER' and len(parts) >= 3:
                    level_data['player_pos'] = {
                        'x': float(parts[1]),
                        'y': float(parts[2])
                    }
                elif parts[0] == 'PLAYER_BASE' and len(parts) >= 3:
                    level_data['player_base_pos'] = {
                        'x': float(parts[1]),
                        'y': float(parts[2])
                    }
                elif parts[0] == 'ENEMY_BASE' and len(parts) >= 3:
                    level_data['enemy_base_pos'] = {
                        'x': float(parts[1]),
                        'y': float(parts[2])
                    }

        return level_data

    def create_game_objects(self, level_data):
        """根据关卡数据创建游戏对象"""
        walls = []
        enemies = []
        player_pos = level_data.get('player_pos')
        player_base = None
        enemy_base = None

        # 创建墙壁
        for wall_data in level_data['walls']:
            wall = Wall((wall_data['x'], wall_data['y'],
                        wall_data['width'], wall_data['height']),
                       wall_data['health'])
            walls.append(wall)

        # 创建敌人
        for enemy_data in level_data['enemies']:
            enemy = EnemyTank(enemy_data['x'], enemy_data['y'], enemy_data['angle'])
            enemies.append(enemy)

        # 创建基地
        if level_data.get('player_base_pos'):
            pos = level_data['player_base_pos']
            player_base = PlayerBase(pos['x'], pos['y'])

        if level_data.get('enemy_base_pos'):
            pos = level_data['enemy_base_pos']
            enemy_base = EnemyBase(pos['x'], pos['y'])

        return {
            'walls': walls,
            'enemies': enemies,
            'player_pos': player_pos,
            'player_base': player_base,
            'enemy_base': enemy_base
        }

    def prepare_level(self, level):
        """准备关卡（生成或加载）"""
        # 尝试从文件加载
        level_data = self.load_level_from_file(level)

        if level_data is None:
            # 文件不存在，生成新关卡
            level_data = self.generate_level_data(level)
            self.save_level_to_file(level, level_data)

        return self.create_game_objects(level_data)

    def prepare_all_levels(self):
        """预生成所有关卡"""
        for level in range(1, self.max_level + 1):
            map_file = os.path.join(self.assets_dir, f'level{level}.map')
            if not os.path.exists(map_file):
                level_data = self.generate_level_data(level)
                self.save_level_to_file(level, level_data)
