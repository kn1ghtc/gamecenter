"""
关卡管理模块
处理关卡生成、加载和保存
"""
import os
import random
import math
import pygame
from config import (MAP_CONFIG, LEVEL_CONFIG, GAME_CONFIG, WALL_CONFIG, ENEMY_CONFIG)
from environment import Wall, PlayerBase, EnemyBase
from tank_system import EnemyTank
from special_walls import SpecialWall, SpecialWallGenerator

class LevelManager:
    """关卡管理器"""
    def __init__(self):
        self.current_level = 1
        self.max_level = MAP_CONFIG['MAX_LEVEL']
        self.special_wall_generator = SpecialWallGenerator()

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

        # 创建玩家安全区域
        player_pos = self._get_player_start_position()
        self._create_safe_zone(grid, player_pos, cell_size)

        # 清除基地位置的围墙
        self._clear_base_areas(grid, cell_size)

        # 添加中间分割线（2排围墙）
        self._create_center_barrier(grid)

        # 转换为墙壁数据 - 避免在屏幕边缘生成围墙
        normal_walls_data = []
        barrier_walls_data = []  # 隔离围墙数据
        edge_margin = 2  # 屏幕边缘2格范围内不生成围墙

        for y in range(edge_margin, grid_height - edge_margin):
            for x in range(edge_margin, grid_width - edge_margin):
                if grid[y][x] == 1:  # 普通围墙
                    normal_walls_data.append({
                        'x': x * cell_size,
                        'y': y * cell_size,
                        'width': cell_size,
                        'height': cell_size,
                        'health': WALL_CONFIG['HEALTH'],
                        'type': 'normal'
                    })
                elif grid[y][x] == 2:  # 隔离围墙
                    from config import BARRIER_WALL_CONFIG
                    barrier_walls_data.append({
                        'x': x * cell_size,
                        'y': y * cell_size,
                        'width': cell_size,
                        'height': cell_size,
                        'health': BARRIER_WALL_CONFIG['HEALTH'],
                        'type': 'barrier',
                        'destructible': BARRIER_WALL_CONFIG['DESTRUCTIBLE'],
                        'piercing_passable': BARRIER_WALL_CONFIG['PIERCING_PASSABLE']
                    })

        # 生成特殊围墙
        special_walls_data = self._generate_special_walls(normal_walls_data, level)

        # 合并普通围墙、隔离围墙和特殊围墙
        all_walls_data = normal_walls_data + barrier_walls_data + special_walls_data

        return all_walls_data

    def _create_safe_zone(self, grid, player_pos, cell_size):
        """在玩家周围创建安全区域"""
        safe_radius = LEVEL_CONFIG['PLAYER_SAFE_ZONE_RADIUS']
        grid_width = len(grid[0])
        grid_height = len(grid)

        # 计算玩家在网格中的位置
        player_grid_x = int(player_pos['x'] // cell_size)
        player_grid_y = int(player_pos['y'] // cell_size)

        # 清除安全区域内的墙壁
        safe_radius_cells = int(safe_radius // cell_size) + 1

        for dy in range(-safe_radius_cells, safe_radius_cells + 1):
            for dx in range(-safe_radius_cells, safe_radius_cells + 1):
                check_x = player_grid_x + dx
                check_y = player_grid_y + dy

                # 检查是否在网格范围内
                if 0 <= check_x < grid_width and 0 <= check_y < grid_height:
                    # 计算实际距离
                    real_x = check_x * cell_size + cell_size // 2
                    real_y = check_y * cell_size + cell_size // 2
                    distance = math.sqrt(
                        (real_x - player_pos['x']) ** 2 +
                        (real_y - player_pos['y']) ** 2
                    )

                    if distance <= safe_radius:
                        grid[check_y][check_x] = 0  # 清除墙壁

    def _clear_base_areas(self, grid, cell_size):
        """清除基地位置的围墙"""
        grid_width = len(grid[0])
        grid_height = len(grid)

        # 获取基地位置
        player_base_pos = self._get_player_base_position()
        enemy_base_pos = self._get_enemy_base_position()

        # 基地尺寸
        from config import BASE_CONFIG
        base_size = BASE_CONFIG['PLAYER_BASE']['SIZE']

        # 清除基地及周围区域的围墙（扩大清除范围确保基地周围有足够空间）
        clear_radius = max(base_size[0], base_size[1]) + 50  # 基地尺寸加50像素缓冲

        bases = [player_base_pos, enemy_base_pos]
        for base_pos in bases:
            base_center_x = base_pos['x'] + base_size[0] // 2
            base_center_y = base_pos['y'] + base_size[1] // 2

            # 计算网格范围
            grid_x = int(base_center_x // cell_size)
            grid_y = int(base_center_y // cell_size)
            clear_radius_cells = int(clear_radius // cell_size) + 1

            for dy in range(-clear_radius_cells, clear_radius_cells + 1):
                for dx in range(-clear_radius_cells, clear_radius_cells + 1):
                    check_x = grid_x + dx
                    check_y = grid_y + dy

                    # 检查是否在网格范围内
                    if 0 <= check_x < grid_width and 0 <= check_y < grid_height:
                        # 计算实际距离
                        real_x = check_x * cell_size + cell_size // 2
                        real_y = check_y * cell_size + cell_size // 2
                        distance = math.sqrt(
                            (real_x - base_center_x) ** 2 +
                            (real_y - base_center_y) ** 2
                        )

                        if distance <= clear_radius:
                            grid[check_y][check_x] = 0  # 清除墙壁

    def _create_center_barrier(self, grid):
        """在地图中间创建2排特殊隔离围墙分割线"""
        grid_width = len(grid[0])
        grid_height = len(grid)

        # 计算中间位置
        center_y = grid_height // 2

        # 创建2排隔离围墙（上下各一排）- 使用特殊标记
        barrier_rows = [center_y - 1, center_y]

        for row in barrier_rows:
            if 0 <= row < grid_height:
                for x in range(grid_width):
                    grid[row][x] = 2  # 使用2标记隔离围墙，区别于普通围墙(1)

        # 随机预留3个通道位置
        from config import BARRIER_WALL_CONFIG
        passage_count = BARRIER_WALL_CONFIG['PASSAGE_COUNT']
        passage_width = BARRIER_WALL_CONFIG['PASSAGE_WIDTH']

        # 生成随机通道位置，确保有足够间距
        min_spacing = 5  # 通道之间最小间距
        available_positions = list(range(passage_width, grid_width - passage_width))
        passage_positions = []

        # 随机选择通道位置
        for _ in range(passage_count):
            if not available_positions:
                break

            pos = random.choice(available_positions)
            passage_positions.append(pos)

            # 移除周围位置确保间距
            available_positions = [p for p in available_positions
                                 if abs(p - pos) >= min_spacing]

        # 创建通道
        for passage_x in passage_positions:
            if 0 <= passage_x < grid_width:
                for row in barrier_rows:
                    if 0 <= row < grid_height:
                        # 创建通道，宽度由配置决定
                        for offset in range(-passage_width//2, passage_width//2 + 1):
                            clear_x = passage_x + offset
                            if 0 <= clear_x < grid_width:
                                grid[row][clear_x] = 0  # 清除围墙创建通道

    def _generate_special_walls(self, normal_walls_data, level):
        """生成特殊围墙"""
        if level < 2:  # 第一关不生成特殊围墙
            return []

        # 根据关卡调整特殊围墙比例
        base_ratio = 0.05  # 基础比例 5%
        level_bonus = min(0.15, level * 0.01)  # 每关增加1%，最多15%
        special_ratio = base_ratio + level_bonus

        # 选择一些普通围墙转换为特殊围墙
        num_special = max(1, int(len(normal_walls_data) * special_ratio))
        if num_special > len(normal_walls_data):
            num_special = len(normal_walls_data)

        selected_walls = random.sample(normal_walls_data, num_special)
        special_walls_data = []

        for wall_data in selected_walls:
            effect_type = self.special_wall_generator._choose_effect_type()
            special_wall_data = wall_data.copy()
            special_wall_data['type'] = 'special'
            special_wall_data['effect_type'] = effect_type
            special_walls_data.append(special_wall_data)

            # 从普通围墙列表中移除
            normal_walls_data.remove(wall_data)

        return special_walls_data

    def _get_player_start_position(self):
        """获取玩家起始位置 - 在玩家基地附近"""
        cell_size = MAP_CONFIG['CELL_SIZE']
        # 玩家基地在底部，所以玩家在下半部分靠近基地的位置开始
        base_pos = self._get_player_base_position()
        base_grid_y = int(base_pos['y'] // cell_size)

        # 在基地上方3-5格的位置生成玩家
        player_y = max(base_grid_y - 4, MAP_CONFIG['GRID_HEIGHT'] * 3 // 4)
        player_x = MAP_CONFIG['GRID_WIDTH'] // 2  # 中间位置

        return {
            'x': player_x * cell_size + cell_size // 2,
            'y': player_y * cell_size + cell_size // 2
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
        """生成敌人数据 - 改进分布：1/3在玩家势力范围，2/3分散在敌方势力范围"""
        cell_size = MAP_CONFIG['CELL_SIZE']
        grid_width = MAP_CONFIG['GRID_WIDTH']
        grid_height = MAP_CONFIG['GRID_HEIGHT']

        # 玩家起始位置
        player_start = self._get_player_start_position()
        player_grid_x = int(player_start['x'] // cell_size)
        player_grid_y = int(player_start['y'] // cell_size)

        # 敌方基地位置
        enemy_base = self._get_enemy_base_position()
        enemy_base_grid_x = int(enemy_base['x'] // cell_size)
        enemy_base_grid_y = int(enemy_base['y'] // cell_size)

        # 定义势力范围分界线
        territory_border = grid_height // 2

        # 计算敌人数量
        base_enemies = LEVEL_CONFIG['ENEMIES_BASE']
        increment = level // LEVEL_CONFIG['ENEMIES_INCREMENT_INTERVAL']
        total_enemies = min(base_enemies + increment, LEVEL_CONFIG['MAX_ENEMIES'])

        # 分配敌人：1/3在玩家势力范围，2/3在敌方势力范围
        enemies_in_player_territory = total_enemies // 3
        enemies_in_enemy_territory = total_enemies - enemies_in_player_territory

        enemies_data = []

        # 基于坦克尺寸的可行走区域判定（避免出生即与墙/边界相撞）
        tank_w, tank_h = ENEMY_CONFIG['SIZE']

        def cell_has_clearance(cx, cy):
            # 以格中心生成坦克矩形，确保不与任何墙体相交，且完全在屏幕范围内
            px = cx * cell_size + cell_size // 2
            py = cy * cell_size + cell_size // 2
            tank_rect = pygame.Rect(px - tank_w // 2, py - tank_h // 2, tank_w, tank_h)

            # 屏幕边界检查，保留1像素容差
            if (tank_rect.left < 1 or tank_rect.top < 1 or
                tank_rect.right > GAME_CONFIG['WIDTH'] - 1 or
                tank_rect.bottom > GAME_CONFIG['HEIGHT'] - 1):
                return False

            # 与任何墙（包含普通/特殊/隔离）碰撞即不可用
            for w in walls_data:
                w_rect = pygame.Rect(w['x'], w['y'], w['width'], w['height'])
                if w_rect.colliderect(tank_rect):
                    return False
            return True

        # 生成在敌方势力范围的敌人（分散分布）
        enemy_territory_cells = []
        for y in range(territory_border):  # 上半部分
            for x in range(grid_width):
                distance_to_player = max(abs(x - player_grid_x), abs(y - player_grid_y))

                if cell_has_clearance(x, y) and distance_to_player >= 4:
                    enemy_territory_cells.append((x, y))

        # 随机打散并选择位置
        random.shuffle(enemy_territory_cells)

        # 从敌方势力范围选择分散的位置
        selected_positions = []
        for i in range(min(enemies_in_enemy_territory, len(enemy_territory_cells))):
            # 确保敌人之间有一定距离，避免扎堆
            x, y = enemy_territory_cells[i]

            # 检查与已选择位置的距离
            too_close = False
            for prev_x, prev_y in selected_positions:
                if max(abs(x - prev_x), abs(y - prev_y)) < 6:  # 至少6格距离
                    too_close = True
                    break

            if not too_close:
                selected_positions.append((x, y))
                enemy_x = x * cell_size + cell_size // 2
                enemy_y = y * cell_size + cell_size // 2
                angle = random.uniform(0, 2 * math.pi)
                enemies_data.append({
                    'x': enemy_x,
                    'y': enemy_y,
                    'angle': angle
                })

        # 生成在玩家势力范围的敌人
        player_territory_cells = []
        for y in range(territory_border, grid_height):  # 下半部分
            for x in range(grid_width):
                distance_to_player = max(abs(x - player_grid_x), abs(y - player_grid_y))

                # 在玩家势力范围但不要太靠近玩家起始位置，且需要坦克尺寸的净空
                if cell_has_clearance(x, y) and distance_to_player >= 8:
                    player_territory_cells.append((x, y))

        random.shuffle(player_territory_cells)

        # 从玩家势力范围选择位置
        for i in range(min(enemies_in_player_territory, len(player_territory_cells))):
            x, y = player_territory_cells[i]

            # 同样确保间距
            too_close = False
            for prev_x, prev_y in selected_positions:
                if max(abs(x - prev_x), abs(y - prev_y)) < 6:
                    too_close = True
                    break

            if not too_close:
                selected_positions.append((x, y))
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
                wall_type = wall.get('type', 'normal')
                if wall_type == 'special':
                    effect_type = wall.get('effect_type', 'normal')
                    f.write(f'SPECIAL_WALL {wall["x"]} {wall["y"]} {wall["width"]} {wall["height"]} {wall["health"]} {effect_type}\n')
                elif wall_type == 'barrier':
                    # 隔离围墙保存
                    destructible = wall.get('destructible', False)
                    piercing_passable = wall.get('piercing_passable', True)
                    f.write(f'BARRIER_WALL {wall["x"]} {wall["y"]} {wall["width"]} {wall["height"]} {wall["health"]} {destructible} {piercing_passable}\n')
                else:
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
                        'health': int(parts[5]),
                        'type': 'normal'
                    })
                elif parts[0] == 'SPECIAL_WALL' and len(parts) >= 7:
                    level_data['walls'].append({
                        'x': int(parts[1]),
                        'y': int(parts[2]),
                        'width': int(parts[3]),
                        'height': int(parts[4]),
                        'health': int(parts[5]),
                        'type': 'special',
                        'effect_type': parts[6]
                    })
                elif parts[0] == 'BARRIER_WALL' and len(parts) >= 8:
                    # 加载隔离围墙
                    level_data['walls'].append({
                        'x': int(parts[1]),
                        'y': int(parts[2]),
                        'width': int(parts[3]),
                        'height': int(parts[4]),
                        'health': int(parts[5]),
                        'type': 'barrier',
                        'destructible': parts[6].lower() == 'true',
                        'piercing_passable': parts[7].lower() == 'true'
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
        special_walls = []
        barrier_walls = []  # 隔离围墙
        enemies = []
        player_pos = level_data.get('player_pos')
        player_base = None
        enemy_base = None

        # 创建墙壁
        for wall_data in level_data['walls']:
            if wall_data.get('type') == 'special':
                # 创建特殊围墙
                special_wall = SpecialWall(
                    (wall_data['x'], wall_data['y'], wall_data['width'], wall_data['height']),
                    wall_data['health'],
                    wall_data.get('effect_type', 'normal')
                )
                special_walls.append(special_wall)
            elif wall_data.get('type') == 'barrier':
                # 创建隔离围墙
                from environment import BarrierWall
                barrier_wall = BarrierWall(
                    (wall_data['x'], wall_data['y'], wall_data['width'], wall_data['height']),
                    wall_data['health'],
                    wall_data.get('destructible', False),
                    wall_data.get('piercing_passable', True)
                )
                barrier_walls.append(barrier_wall)
            else:
                # 创建普通围墙
                wall = Wall((wall_data['x'], wall_data['y'],
                           wall_data['width'], wall_data['height']),
                           wall_data['health'])
                walls.append(wall)

        # 合并所有围墙
        all_walls = walls + special_walls + barrier_walls

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
            'walls': all_walls,
            'special_walls': special_walls,
            'barrier_walls': barrier_walls,  # 添加隔离围墙
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
