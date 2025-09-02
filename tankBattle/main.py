"""
Tank Battle Game (main.py)
=========================
A classic 2D top-down tank battle game using Pygame.

Controls:
- W/S: Move forward/backward
- A/D: Rotate left/right
- Space: Fire
- P: Pause

Run: python main.py
Requires: pygame (pip install pygame)
"""
# 导入必要的模块
import pygame  # Pygame库，用于游戏开发，包括图形、声音、事件处理
import random  # 随机数模块，用于生成随机位置、角度等
import math    # 数学模块，用于三角函数计算（如角度、移动）
import sys     # 系统模块，用于退出程序
import os      # 操作系统模块，用于文件路径处理

# --- Constants ---  # 定义游戏常量，这些值在游戏中不会改变
WIDTH, HEIGHT = 1200, 800  # 游戏窗口的宽度和高度（像素）
FPS = 120  # 游戏帧率，每秒120帧，确保游戏流畅
CELL_SIZE = 25  # 迷宫单元格大小，调整为25以适应1200x800
GRID_WIDTH = WIDTH // CELL_SIZE  # 网格宽度：48
GRID_HEIGHT = HEIGHT // CELL_SIZE  # 网格高度：32
TANK_SIZE = (40, 40)  # 坦克的尺寸（宽度，高度）
BULLET_RADIUS = 5  # 子弹的半径
WALL_COLOR = (120, 120, 120)  # 墙壁的颜色（灰色）
PLAYER_COLOR = (0, 200, 0)  # 玩家坦克的颜色（绿色）
ENEMY_COLOR = (200, 0, 0)  # 敌方坦克的颜色（红色）
PLAYER_HEALTH = 100  # 玩家坦克的生命值
ENEMY_HEALTH = 3  # 敌方坦克的生命值
TANK_GREEN_IMG = os.path.join('assets', 'PNG', 'Tanks', 'tankGreen.png')  # 玩家坦克图片路径
TANK_RED_IMG = os.path.join('assets', 'PNG', 'Tanks', 'tankRed.png')  # 敌方坦克图片路径
BASE_COLOR = (0, 0, 200)  # 基地的颜色（蓝色）
BG_COLOR = (30, 30, 30)  # 背景颜色（深灰色）

# --- Classes ---  # 定义游戏中的类，每个类代表游戏中的一个对象

class Wall(pygame.sprite.Sprite):  # Wall类，继承自Pygame的Sprite类，表示游戏中的墙壁障碍物
    def __init__(self, rect, health=20):  # 初始化方法，rect是墙壁的矩形区域，health是生命值，默认20
        super().__init__()  # 调用父类Sprite的初始化
        self.rect = pygame.Rect(rect)  # 创建Pygame的Rect对象，用于碰撞检测和绘制
        self.health = health  # 墙壁的生命值
    def draw(self, surface):  # 绘制方法，在给定的surface上绘制墙壁
        if self.health > 0:  # 只有生命值大于0时才绘制
            pygame.draw.rect(surface, WALL_COLOR, self.rect)  # 使用Pygame绘制矩形，颜色为WALL_COLOR

class Bullet(pygame.sprite.Sprite):  # Bullet类，表示游戏中的子弹
    def __init__(self, x, y, angle, speed, owner):  # 初始化子弹，x,y起始位置，angle方向角度，speed速度，owner所有者（'player'或'enemy'）
        super().__init__()
        self.x = x  # 子弹的x坐标
        self.y = y  # 子弹的y坐标
        self.angle = angle  # 子弹移动的角度
        self.speed = speed  # 子弹的速度
        self.owner = owner  # 子弹的所有者，用于区分玩家或敌方子弹
        self.radius = BULLET_RADIUS  # 子弹的半径
        self.rect = pygame.Rect(x-self.radius, y-self.radius, self.radius*2, self.radius*2)  # 子弹的碰撞矩形
    def update(self):  # 更新子弹位置，每帧调用
        self.x += self.speed * math.cos(self.angle)  # 根据角度和速度更新x坐标
        self.y += self.speed * math.sin(self.angle)  # 更新y坐标
        self.rect.center = (self.x, self.y)  # 更新碰撞矩形的中心位置
    def draw(self, surface):  # 绘制子弹
        color = PLAYER_COLOR if self.owner == 'player' else ENEMY_COLOR  # 根据所有者选择颜色
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)  # 绘制圆形子弹

class Tank(pygame.sprite.Sprite):  # Tank类，表示坦克对象，包括玩家和敌方坦克
    def __init__(self, x, y, angle, color, is_player=False, image=None):  # 初始化坦克，x,y位置，angle角度，color颜色，is_player是否玩家，image图片路径
        super().__init__()
        self.x = x  # 坦克的x坐标
        self.y = y  # 坦克的y坐标
        self.angle = angle  # 坦克的朝向角度（弧度）
        self.color = color  # 坦克的颜色
        self.is_player = is_player  # 是否是玩家坦克
        self.health = PLAYER_HEALTH if is_player else ENEMY_HEALTH  # 根据是否玩家设置生命值
        self.size = TANK_SIZE  # 坦克的尺寸
        self.speed = 3 if is_player else 1  # 坦克的速度，玩家更快
        self.rect = pygame.Rect(x, y, *self.size)  # 坦克的碰撞矩形
        self.reload = 0  # 射击冷却时间
        self.image = None  # 坦克的图片对象
        if image and os.path.exists(image):  # 如果图片存在，加载并缩放
            self.image = pygame.transform.scale(pygame.image.load(image), self.size)
        # 炮管长度和宽度
        self.turret_length = 28  # 炮管的长度
        self.turret_width = 7  # 炮管的宽度
    def move(self, forward, walls):  # 移动坦克，forward为1前进，-1后退，walls是墙壁列表
        dx = forward * self.speed * math.cos(self.angle)  # 计算x方向的移动距离
        dy = forward * self.speed * math.sin(self.angle)  # 计算y方向的移动距离
        new_rect = self.rect.move(dx, dy)  # 创建新的矩形位置
        # 检查屏幕边界，防止坦克移出屏幕
        if new_rect.left < 0 or new_rect.right > WIDTH or new_rect.top < 0 or new_rect.bottom > HEIGHT:
            return  # 如果超出边界，不允许移动
        # 检查墙壁碰撞
        if not any(new_rect.colliderect(w.rect) for w in walls):  # 检查是否与墙壁碰撞
            self.x += dx  # 更新x坐标
            self.y += dy  # 更新y坐标
            self.rect.topleft = (self.x, self.y)  # 更新碰撞矩形位置
    def rotate(self, direction):  # 旋转坦克，direction为1右转，-1左转
        # 单次旋转角度降低，提升操控性
        self.angle += direction * 0.0125 * math.pi  # 增加角度，0.0125*pi约为0.72度
    def fire(self):  # 发射子弹
        if self.reload == 0:  # 如果冷却时间为0，可以发射
            bx = self.x + self.size[0]//2 + 18 * math.cos(self.angle)  # 计算子弹起始x坐标（从炮管发射）
            by = self.y + self.size[1]//2 + 18 * math.sin(self.angle)  # 计算子弹起始y坐标
            self.reload = 30  # 设置冷却时间（30帧）
            return Bullet(bx, by, self.angle, 7, 'player' if self.is_player else 'enemy')  # 创建并返回子弹对象
        return None  # 否则返回None
    def update(self):  # 更新坦克状态
        if self.reload > 0:  # 如果冷却时间大于0，减少1
            self.reload -= 1
    def draw(self, surface):  # 绘制坦克
        cx = self.x + self.size[0]//2  # 坦克中心x坐标
        cy = self.y + self.size[1]//2  # 坦克中心y坐标
        # 主体
        if self.image:  # 如果有图片，使用图片绘制
            rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))  # 旋转图片
            rect = rotated.get_rect(center=(cx, cy))  # 获取旋转后的矩形
            surface.blit(rotated, rect.topleft)  # 绘制图片
        else:  # 否则绘制矩形
            pygame.draw.rect(surface, self.color, (self.x, self.y, *self.size), border_radius=8)
        # 炮管（始终指向前方）
        turret_end = (cx + self.turret_length * math.cos(self.angle), cy + self.turret_length * math.sin(self.angle))  # 炮管末端坐标
        pygame.draw.line(surface, (80,80,80), (cx, cy), turret_end, self.turret_width)  # 绘制炮管
        # 炮口高亮
        pygame.draw.circle(surface, (220,220,0), (int(turret_end[0]), int(turret_end[1])), self.turret_width//2)  # 绘制炮口高亮
        # 轮廓
        pygame.draw.rect(surface, self.color, self.rect, 2)  # 绘制坦克轮廓
        # Health bar  # 绘制生命条
        max_health = PLAYER_HEALTH if self.is_player else ENEMY_HEALTH  # 获取最大生命值
        pygame.draw.rect(surface, (255,0,0), (self.x, self.y-10, self.size[0], 6))  # 红色背景
        pygame.draw.rect(surface, (0,255,0), (self.x, self.y-10, self.size[0]*self.health/max_health, 6))  # 绿色生命条

class Base:  # Base类，表示游戏中的基地，需要保护的对象
    def __init__(self, x, y):  # 初始化基地，x,y位置
        self.rect = pygame.Rect(x, y, 50, 50)  # 基地的矩形区域
        self.health = 5  # 基地的生命值
    def draw(self, surface):  # 绘制基地
        pygame.draw.rect(surface, BASE_COLOR, self.rect)  # 绘制基地主体
        pygame.draw.rect(surface, (255,255,255), self.rect, 2)  # 绘制白色边框
        pygame.draw.rect(surface, (255,0,0), (self.rect.x, self.rect.y-10, self.rect.width, 6))  # 红色生命条背景
        pygame.draw.rect(surface, (0,255,0), (self.rect.x, self.rect.y-10, self.rect.width*self.health/5, 6))  # 绿色生命条

class Game:  # Game类，管理整个游戏的逻辑和状态
    def __init__(self):  # 初始化游戏
        pygame.init()  # 初始化Pygame
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))  # 创建游戏窗口
        pygame.display.set_caption('Tank Battle')  # 设置窗口标题
        self.clock = pygame.time.Clock()  # 创建时钟对象，用于控制帧率
        self.font = pygame.font.SysFont(None, 32)  # 创建字体对象，用于绘制文本
        self.running = True  # 游戏是否运行中
        self.paused = False  # 游戏是否暂停
        self.score = 0  # 玩家得分
        self.level = 1  # 当前关卡
        self.max_level = 30  # 最大关卡数
        self.player = None  # 玩家坦克对象
        self.enemies = []  # 敌方坦克列表
        self.bullets = []  # 子弹列表
        self.walls = []  # 墙壁列表
        self.base = None  # 基地对象
        self.start_time = pygame.time.get_ticks()  # 关卡开始时间
        self.explosion_sound = None  # 爆炸音效
        self.shoot_sound = None  # 射击音效
        self.load_sounds()  # 加载音效
        self.pre_generate_levels()  # 预生成所有关卡地图
        self.load_level(self.level)  # 加载第一关

    def pre_generate_levels(self):  # 预生成所有关卡地图
        for level in range(1, self.max_level + 1):
            map_file = os.path.join('assets', f'level{level}.map')
            # 总是重新生成以确保更新
            # 生成迷宫
            walls = self.generate_maze(level)
            
            # 玩家位置
            player_x = 1 * CELL_SIZE + CELL_SIZE // 2
            player_y = 1 * CELL_SIZE + CELL_SIZE // 2
            
            # 基地位置
            base_x = WIDTH // 2 - 25
            base_y = HEIGHT - 70
            
            # 敌人位置
            path_cells = []
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    cell_rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    if not any(w.rect.colliderect(cell_rect) for w in walls):
                        path_cells.append((x, y))
            
            num_enemies = min(4 + level // 5, 15)
            random.shuffle(path_cells)
            enemies_data = []
            for i in range(min(num_enemies, len(path_cells))):
                x, y = path_cells[i]
                enemy_x = x * CELL_SIZE + CELL_SIZE // 2
                enemy_y = y * CELL_SIZE + CELL_SIZE // 2
                angle = random.uniform(0, 2 * math.pi)
                enemies_data.append((enemy_x, enemy_y, angle))
            
            # 保存地图
            self.save_level_to_file(level, walls, player_x, player_y, base_x, base_y, enemies_data)

    def generate_maze(self, level):  # 生成迷宫，使用递归回溯算法
        # 初始化网格，所有单元格为墙壁（1=wall, 0=path）
        grid = [[1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        def carve(x, y):  # 递归雕刻函数
            grid[y][x] = 0  # 标记当前单元格为路径
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 四个方向：下、右、上、左
            random.shuffle(directions)  # 随机化方向顺序
            for dx, dy in directions:
                nx, ny = x + dx * 2, y + dy * 2  # 下一个单元格（跳过一个）
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and grid[ny][nx] == 1:
                    grid[y + dy][x + dx] = 0  # 移除中间的墙壁
                    carve(nx, ny)  # 递归雕刻
        
        # 从多个起始点开始雕刻，确保覆盖整个屏幕
        starts = [(1, 1), (GRID_WIDTH-2, 1), (1, GRID_HEIGHT-2), (GRID_WIDTH-2, GRID_HEIGHT-2)]
        for sx, sy in starts:
            if grid[sy][sx] == 1:
                carve(sx, sy)
        
        # 根据关卡添加额外雕刻，增加复杂性
        extra_carves = level // 3  # 每3关增加一次额外雕刻
        for _ in range(extra_carves):
            # 随机选择一个墙壁单元格进行额外雕刻
            wall_cells = [(x, y) for y in range(1, GRID_HEIGHT-1, 2) for x in range(1, GRID_WIDTH-1, 2) if grid[y][x] == 1]
            if wall_cells:
                x, y = random.choice(wall_cells)
                carve(x, y)
        
        # 创建墙壁列表
        walls = []
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if grid[y][x] == 1:  # 如果是墙壁
                    walls.append(Wall((x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 20))
        
        return walls

    def save_level_to_file(self, level, walls, player_x, player_y, base_x, base_y, enemies_data):  # 保存关卡到文件
        map_file = os.path.join('assets', f'level{level}.map')
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(f'# Level {level} Maze Map\n')
            f.write(f'PLAYER {player_x} {player_y}\n')
            f.write(f'BASE {base_x} {base_y}\n')
            for wall in walls:
                x, y, w, h = wall.rect
                health = wall.health
                f.write(f'WALL {x} {y} {w} {h} {health}\n')
            for enemy_x, enemy_y, angle in enemies_data:
                f.write(f'ENEMY {enemy_x} {enemy_y} {angle}\n')

    def load_sounds(self):  # 加载音效文件
        try:
            self.explosion_sound = pygame.mixer.Sound(os.path.join('assets', 'explosion.wav'))  # 加载爆炸音效
        except Exception:
            self.explosion_sound = None  # 如果加载失败，设为None
        try:
            self.shoot_sound = pygame.mixer.Sound(os.path.join('assets', 'shoot.wav'))  # 加载射击音效
        except Exception:
            self.shoot_sound = None  # 如果加载失败，设为None

    def load_level(self, level):  # 加载指定关卡
        map_file = os.path.join('assets', f'level{level}.map')  # 关卡地图文件路径
        self.walls = []  # 清空墙壁
        self.enemies = []  # 清空敌人
        self.bullets = []  # 清空子弹
        
        if os.path.exists(map_file):  # 如果地图文件存在，从文件加载
            with open(map_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts or parts[0].startswith('#'): continue  # 跳过空行或注释
                    if parts[0] == 'WALL':  # 如果是墙壁
                        if len(parts) >= 6:  # 如果有health参数
                            x, y, w, h, health = map(int, parts[1:6])
                        else:  # 否则默认health=20
                            x, y, w, h = map(int, parts[1:5])
                            health = 20
                        self.walls.append(Wall((x, y, w, h), health))  # 添加墙壁
                    elif parts[0] == 'ENEMY':  # 如果是敌人
                        x, y, angle = float(parts[1]), float(parts[2]), float(parts[3])  # 解析敌人参数
                        self.enemies.append(Tank(x, y, angle, ENEMY_COLOR, False, TANK_RED_IMG))  # 添加敌人
                    elif parts[0] == 'PLAYER':  # 如果指定玩家位置
                        x, y = float(parts[1]), float(parts[2])
                        self.player = Tank(x, y, 0, PLAYER_COLOR, True, TANK_GREEN_IMG)
                    elif parts[0] == 'BASE':  # 如果指定基地位置
                        x, y = float(parts[1]), float(parts[2])
                        self.base = Base(x, y)
            # 如果地图文件中没有指定玩家和基地，使用默认
            if self.player is None:
                self.player = Tank(100, HEIGHT//2, 0, PLAYER_COLOR, True, TANK_GREEN_IMG)
            if self.base is None:
                self.base = Base(WIDTH//2-25, HEIGHT-70)
        else:  # 如果地图文件不存在，使用迷宫生成
            # 生成迷宫墙壁
            self.walls = self.generate_maze(level)
            
            # 玩家位置：老家位置（左上角附近）
            player_x = 1 * CELL_SIZE + CELL_SIZE // 2
            player_y = 1 * CELL_SIZE + CELL_SIZE // 2
            self.player = Tank(player_x, player_y, 0, PLAYER_COLOR, True, TANK_GREEN_IMG)
            
            # 基地位置：固定在底部中心
            base_x = WIDTH // 2 - 25
            base_y = HEIGHT - 70
            self.base = Base(base_x, base_y)
            
            # 敌人随机位置：选择路径单元格
            path_cells = []
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    cell_rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    if not any(w.rect.colliderect(cell_rect) for w in self.walls):
                        path_cells.append((x, y))
            
            # 敌人数量随关卡增加
            num_enemies = min(4 + level // 5, 15)
            random.shuffle(path_cells)
            enemies_data = []
            for i in range(min(num_enemies, len(path_cells))):
                x, y = path_cells[i]
                enemy_x = x * CELL_SIZE + CELL_SIZE // 2
                enemy_y = y * CELL_SIZE + CELL_SIZE // 2
                angle = random.uniform(0, 2 * math.pi)
                self.enemies.append(Tank(enemy_x, enemy_y, angle, ENEMY_COLOR, False, TANK_RED_IMG))
                enemies_data.append((enemy_x, enemy_y, angle))
            
            # 保存地图到文件
            self.save_level_to_file(level, self.walls, player_x, player_y, base_x, base_y, enemies_data)
        
        self.start_time = pygame.time.get_ticks()  # 重置开始时间
    def run(self):  # 主游戏循环
        while self.running:  # 当游戏运行时
            self.clock.tick(FPS)  # 控制帧率
            self.handle_events()  # 处理事件
            if not self.paused:  # 如果没有暂停
                self.update()  # 更新游戏状态
            self.draw()  # 绘制游戏画面
        pygame.quit()  # 退出Pygame
        sys.exit()  # 退出程序

    def handle_events(self):  # 处理用户输入和事件
        for event in pygame.event.get():  # 获取所有事件
            if event.type == pygame.QUIT:  # 如果是退出事件
                self.running = False  # 停止游戏
            elif event.type == pygame.KEYDOWN:  # 如果是按键按下
                if event.key == pygame.K_p:  # 如果是P键
                    self.paused = not self.paused  # 切换暂停状态
                if event.key == pygame.K_SPACE and not self.paused:  # 如果是空格键且未暂停
                    bullet = self.player.fire()  # 玩家发射子弹
                    if bullet:
                        self.bullets.append(bullet)  # 添加子弹到列表
                        if self.shoot_sound:  # 如果有射击音效
                            self.shoot_sound.play()  # 播放音效
    def update(self):  # 更新游戏状态
        keys = pygame.key.get_pressed()  # 获取当前按键状态
        if keys[pygame.K_w]:  # 如果按下W键
            self.player.move(1, self.walls)  # 玩家坦克前进
        if keys[pygame.K_s]:  # 如果按下S键
            self.player.move(-1, self.walls)  # 玩家坦克后退
        if keys[pygame.K_a]:  # 如果按下A键
            self.player.rotate(-1)  # 玩家坦克左转
        if keys[pygame.K_d]:  # 如果按下D键
            self.player.rotate(1)  # 玩家坦克右转
        self.player.update()  # 更新玩家坦克状态
        # Enemy AI  # 敌方AI逻辑
        for enemy in self.enemies[:]:  # 遍历所有敌人（使用副本避免修改时出错）
            if enemy.health <= 0:  # 如果敌人生命值为0
                self.enemies.remove(enemy)  # 从列表中移除
                self.score += 10  # 增加得分
                if self.explosion_sound:  # 如果有爆炸音效
                    self.explosion_sound.play()  # 播放音效
            # Simple AI: rotate towards player, move forward, fire  # 简单AI：转向玩家，前进，射击
            dx = self.player.x - enemy.x  # 计算x方向距离
            dy = self.player.y - enemy.y  # 计算y方向距离
            target_angle = math.atan2(dy, dx)  # 计算目标角度
            diff = (target_angle - enemy.angle + math.pi) % (2*math.pi) - math.pi  # 计算角度差
            if abs(diff) > 0.1:  # 如果角度差大于0.1弧度
                enemy.rotate(1 if diff > 0 else -1)  # 旋转向玩家
            else:  # 否则
                enemy.move(1, self.walls)  # 前进
            if random.random() < 0.02:  # 2%的概率射击
                bullet = enemy.fire()  # 发射子弹
                if bullet:
                    self.bullets.append(bullet)  # 添加子弹
            enemy.update()  # 更新敌人状态
        # Bullets  # 子弹更新和碰撞检测
        for bullet in self.bullets[:]:  # 遍历所有子弹
            bullet.update()  # 更新子弹位置
            # Remove if out of bounds  # 如果超出边界，移除
            if not (0 < bullet.x < WIDTH and 0 < bullet.y < HEIGHT):
                self.bullets.remove(bullet)
                continue
            # Wall collision  # 墙壁碰撞
            wall_hit = False
            for wall in self.walls[:]:
                if bullet.rect.colliderect(wall.rect):
                    wall.health -= 1  # 墙壁生命值减1
                    if wall.health <= 0:
                        self.walls.remove(wall)  # 如果生命值为0，移除墙壁
                    wall_hit = True
                    if self.explosion_sound:  # 播放爆炸音效
                        self.explosion_sound.play()
                    break
            if wall_hit:
                self.bullets.remove(bullet)
                continue
            # Tank collision  # 坦克碰撞
            if bullet.owner == 'player':  # 如果是玩家子弹
                for enemy in self.enemies:
                    if bullet.rect.colliderect(enemy.rect):  # 如果击中敌人
                        enemy.health -= 1  # 敌人生命减1
                        self.bullets.remove(bullet)  # 移除子弹
                        if self.explosion_sound:  # 播放爆炸音效
                            self.explosion_sound.play()
                        break
            elif bullet.owner == 'enemy':  # 如果是敌方子弹
                if bullet.rect.colliderect(self.player.rect):  # 如果击中玩家
                    self.player.health -= 1  # 玩家生命减1
                    self.bullets.remove(bullet)  # 移除子弹
                    if self.explosion_sound:  # 播放爆炸音效
                        self.explosion_sound.play()
                    continue
                if bullet.rect.colliderect(self.base.rect):  # 如果击中基地
                    self.base.health -= 1  # 基地生命减1
                    self.bullets.remove(bullet)  # 移除子弹
                    if self.explosion_sound:  # 播放爆炸音效
                        self.explosion_sound.play()
                    continue
        # 关卡通关：所有敌人消灭，进入下一关
        if not self.enemies:  # 如果没有敌人了
            self.level += 1  # 关卡加1
            if self.level > self.max_level:  # 如果超过最大关卡
                self.running = False  # 游戏结束
            else:
                self.load_level(self.level)  # 加载下一关
        # Game over  # 游戏结束条件
        if self.player.health <= 0 or self.base.health <= 0:  # 如果玩家或基地生命为0
            self.running = False  # 游戏结束
        # Win condition  # 胜利条件（时间限制）
        if pygame.time.get_ticks() - self.start_time > 5*60*1000:  # 如果超过5分钟
            self.running = False  # 游戏结束
    def draw(self):  # 绘制游戏画面
        self.screen.fill(BG_COLOR)  # 填充背景色
        for wall in self.walls:  # 绘制所有墙壁
            wall.draw(self.screen)
        self.base.draw(self.screen)  # 绘制基地
        self.player.draw(self.screen)  # 绘制玩家坦克
        for enemy in self.enemies:  # 绘制所有敌人
            enemy.draw(self.screen)
        for bullet in self.bullets:  # 绘制所有子弹
            bullet.draw(self.screen)
        # Score & UI  # 绘制分数和UI
        score_text = self.font.render(f'Score: {self.score}', True, (255,255,255))  # 渲染分数文本
        health_text = self.font.render(f'Health: {self.player.health}', True, (255,255,255))  # 渲染玩家生命文本
        base_text = self.font.render(f'Base: {self.base.health}', True, (255,255,255))  # 渲染基地生命文本
        self.screen.blit(score_text, (10,10))  # 在屏幕左上角绘制分数
        self.screen.blit(health_text, (10,40))  # 绘制玩家生命
        self.screen.blit(base_text, (10,70))  # 绘制基地生命
        if self.paused:  # 如果暂停
            pause_text = self.font.render('PAUSED', True, (255,255,0))  # 渲染暂停文本
            self.screen.blit(pause_text, (WIDTH//2-50, HEIGHT//2))  # 在屏幕中央绘制暂停文本
        pygame.display.flip()  # 更新屏幕显示

if __name__ == '__main__':  # 如果直接运行此文件
    Game().run()  # 创建游戏实例并运行
