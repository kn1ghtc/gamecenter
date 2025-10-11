"""
游戏板类模块

管理游戏区域、碰撞检测、消行动画等
"""
import pygame
import random
import math
from .settings import (
    BOARD_WIDTH, BOARD_HEIGHT, BLOCK_SIZE, COLORS,
    CLEAR_LINE_ANIMATION_DURATION, PARTICLE_COUNT, PARTICLE_LIFETIME
)

class Particle:
    """粒子效果类"""
    
    def __init__(self, x, y, color):
        """
        初始化粒子
        
        参数:
            x, y: 粒子初始位置
            color: 粒子颜色
        """
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.color = color
        self.lifetime = PARTICLE_LIFETIME
        self.age = 0
        self.size = random.randint(2, 5)
    
    def update(self, dt):
        """
        更新粒子状态
        
        参数:
            dt: 时间增量（毫秒）
        """
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # 重力
        self.age += dt
    
    def is_alive(self):
        """检查粒子是否还存活"""
        return self.age < self.lifetime
    
    def draw(self, surface, offset_x, offset_y):
        """
        绘制粒子
        
        参数:
            surface: pygame绘制表面
            offset_x, offset_y: 绘制偏移量
        """
        # 计算透明度（随生命周期减少）
        alpha = int(255 * (1 - self.age / self.lifetime))
        color_with_alpha = (*self.color[:3], alpha)
        
        # 创建带透明度的表面
        particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color_with_alpha, (self.size, self.size), self.size)
        
        surface.blit(particle_surf, (int(self.x + offset_x), int(self.y + offset_y)))


class Board:
    """
    游戏板类

    属性:
        grid: 游戏板网格
        width: 宽度
        height: 高度
        clearing_lines: 正在消除的行列表
        clear_animation_timer: 消行动画计时器
        particles: 粒子效果列表
    """

    def __init__(self):
        """初始化空游戏板"""
        self.width = BOARD_WIDTH
        self.height = BOARD_HEIGHT
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        # 消行动画相关
        self.clearing_lines = []
        self.clear_animation_timer = 0
        self.is_clearing = False
        
        # 粒子效果
        self.particles = []
    
    def is_valid_move(self, tetromino, x, y):
        """
        检查移动是否有效

        参数:
            tetromino: Tetromino对象
            x: 目标x坐标
            y: 目标y坐标

        返回:
            bool: 移动是否有效
        """
        # 保存原始位置
        original_x, original_y = tetromino.x, tetromino.y
        
        # 临时设置新位置
        tetromino.x = x
        tetromino.y = y
        
        # 获取新位置的所有格子
        positions = tetromino.get_positions()
        
        # 恢复原始位置
        tetromino.x = original_x
        tetromino.y = original_y
        
        # 检查每个格子是否有效
        for px, py in positions:
            # 检查是否超出边界
            if px < 0 or px >= self.width or py >= self.height:
                return False
            
            # 允许方块从顶部进入（py < 0）
            if py < 0:
                continue
            
            # 检查是否与已存在的方块碰撞
            if self.grid[py][px] is not None:
                return False
        
        return True
    
    def lock_piece(self, tetromino):
        """
        锁定方块到游戏板
        
        参数:
            tetromino: 要锁定的方块
        """
        positions = tetromino.get_positions()
        for x, y in positions:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x] = tetromino.color
    
    def find_full_lines(self):
        """
        查找所有填满的行
        
        返回:
            填满的行号列表
        """
        full_lines = []
        for y in range(self.height):
            if all(cell is not None for cell in self.grid[y]):
                full_lines.append(y)
        return full_lines
    
    def start_clear_animation(self, lines):
        """
        开始消行动画
        
        参数:
            lines: 要消除的行号列表
        """
        if not lines:
            return
        
        self.clearing_lines = lines
        self.clear_animation_timer = CLEAR_LINE_ANIMATION_DURATION
        self.is_clearing = True
        
        # 生成粒子效果
        for line_y in lines:
            for x in range(self.width):
                if self.grid[line_y][x]:
                    color = COLORS.get(self.grid[line_y][x], COLORS['WHITE'])
                    # 每个方块生成多个粒子
                    for _ in range(PARTICLE_COUNT // self.width):
                        px = x * BLOCK_SIZE + random.randint(0, BLOCK_SIZE)
                        py = line_y * BLOCK_SIZE + random.randint(0, BLOCK_SIZE)
                        self.particles.append(Particle(px, py, color))
    
    def update_clear_animation(self, dt):
        """
        更新消行动画
        
        参数:
            dt: 时间增量（毫秒）
            
        返回:
            bool: 动画是否完成
        """
        if not self.is_clearing:
            return True
        
        self.clear_animation_timer -= dt
        
        if self.clear_animation_timer <= 0:
            # 动画完成，实际清除行
            self._remove_lines(self.clearing_lines)
            self.clearing_lines = []
            self.is_clearing = False
            return True
        
        return False
    
    def _remove_lines(self, lines):
        """
        实际移除行
        
        参数:
            lines: 要移除的行号列表
        """
        # 从上到下排序
        lines = sorted(lines, reverse=True)
        
        for line in lines:
            # 删除该行
            del self.grid[line]
            # 在顶部添加新行
            self.grid.insert(0, [None] * self.width)
    
    def update_particles(self, dt):
        """
        更新粒子效果
        
        参数:
            dt: 时间增量（毫秒）
        """
        # 更新所有粒子
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.is_alive():
                self.particles.remove(particle)
    
    def draw_particles(self, surface, offset_x, offset_y):
        """
        绘制粒子效果
        
        参数:
            surface: pygame绘制表面
            offset_x, offset_y: 绘制偏移量
        """
        for particle in self.particles:
            particle.draw(surface, offset_x, offset_y)
    
    def get_clear_animation_progress(self):
        """
        获取消行动画进度
        
        返回:
            进度值 (0.0 到 1.0)
        """
        if not self.is_clearing:
            return 1.0
        
        return 1.0 - (self.clear_animation_timer / CLEAR_LINE_ANIMATION_DURATION)
    
    def get_height_map(self):
        """
        获取每列的最高方块位置
        
        返回:
            列表，包含每列的最高点（从底部算起）
        """
        height_map = [0] * self.width
        
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[y][x] is not None:
                    height_map[x] = self.height - y
                    break
        
        return height_map
    
    def get_holes_count(self):
        """
        获取空洞数量（用于AI评估）
        
        返回:
            空洞数量
        """
        holes = 0
        
        for x in range(self.width):
            block_found = False
            for y in range(self.height):
                if self.grid[y][x] is not None:
                    block_found = True
                elif block_found:
                    holes += 1
        
        return holes
    
    def is_game_over(self):
        """
        检查游戏是否结束（顶部有方块）
        
        返回:
            bool: 是否游戏结束
        """
        # 检查顶部几行是否有方块
        for y in range(min(2, self.height)):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    return True
        return False
    
    def clear(self):
        """清空游戏板"""
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.clearing_lines = []
        self.clear_animation_timer = 0
        self.is_clearing = False
        self.particles = []
