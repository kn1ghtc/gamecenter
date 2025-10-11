"""
俄罗斯方块形状类模块

定义所有方块形状、旋转逻辑和渲染效果
"""
import random
import pygame
from .settings import COLORS, GRADIENT_COLORS, BLOCK_SIZE

class Tetromino:
    """
    俄罗斯方块形状类

    属性:
        shape: 方块形状矩阵
        color: 方块颜色名称
        x: 当前x坐标
        y: 当前y坐标
        rotation_state: 当前旋转状态（0-3）
        shape_type: 方块类型名称
    """

    # 定义所有方块形状的旋转状态（SRS - Super Rotation System）
    SHAPES = {
        'I': {
            'shapes': [
                [[0, 0, 0, 0],
                 [1, 1, 1, 1],
                 [0, 0, 0, 0],
                 [0, 0, 0, 0]],
                
                [[0, 0, 1, 0],
                 [0, 0, 1, 0],
                 [0, 0, 1, 0],
                 [0, 0, 1, 0]],
                
                [[0, 0, 0, 0],
                 [0, 0, 0, 0],
                 [1, 1, 1, 1],
                 [0, 0, 0, 0]],
                
                [[0, 1, 0, 0],
                 [0, 1, 0, 0],
                 [0, 1, 0, 0],
                 [0, 1, 0, 0]]
            ],
            'color': 'CYAN'
        },
        'O': {
            'shapes': [
                [[1, 1],
                 [1, 1]]
            ],
            'color': 'YELLOW'
        },
        'T': {
            'shapes': [
                [[0, 1, 0],
                 [1, 1, 1],
                 [0, 0, 0]],
                
                [[0, 1, 0],
                 [0, 1, 1],
                 [0, 1, 0]],
                
                [[0, 0, 0],
                 [1, 1, 1],
                 [0, 1, 0]],
                
                [[0, 1, 0],
                 [1, 1, 0],
                 [0, 1, 0]]
            ],
            'color': 'PURPLE'
        },
        'L': {
            'shapes': [
                [[0, 0, 1],
                 [1, 1, 1],
                 [0, 0, 0]],
                
                [[0, 1, 0],
                 [0, 1, 0],
                 [0, 1, 1]],
                
                [[0, 0, 0],
                 [1, 1, 1],
                 [1, 0, 0]],
                
                [[1, 1, 0],
                 [0, 1, 0],
                 [0, 1, 0]]
            ],
            'color': 'ORANGE'
        },
        'J': {
            'shapes': [
                [[1, 0, 0],
                 [1, 1, 1],
                 [0, 0, 0]],
                
                [[0, 1, 1],
                 [0, 1, 0],
                 [0, 1, 0]],
                
                [[0, 0, 0],
                 [1, 1, 1],
                 [0, 0, 1]],
                
                [[0, 1, 0],
                 [0, 1, 0],
                 [1, 1, 0]]
            ],
            'color': 'BLUE'
        },
        'S': {
            'shapes': [
                [[0, 1, 1],
                 [1, 1, 0],
                 [0, 0, 0]],
                
                [[0, 1, 0],
                 [0, 1, 1],
                 [0, 0, 1]],
                
                [[0, 0, 0],
                 [0, 1, 1],
                 [1, 1, 0]],
                
                [[1, 0, 0],
                 [1, 1, 0],
                 [0, 1, 0]]
            ],
            'color': 'GREEN'
        },
        'Z': {
            'shapes': [
                [[1, 1, 0],
                 [0, 1, 1],
                 [0, 0, 0]],
                
                [[0, 0, 1],
                 [0, 1, 1],
                 [0, 1, 0]],
                
                [[0, 0, 0],
                 [1, 1, 0],
                 [0, 1, 1]],
                
                [[0, 1, 0],
                 [1, 1, 0],
                 [1, 0, 0]]
            ],
            'color': 'RED'
        }
    }

    def __init__(self, shape_type=None):
        """
        初始化方块
        
        参数:
            shape_type: 指定方块类型，None则随机选择
        """
        # 随机选择或指定方块类型
        if shape_type is None:
            shape_type = random.choice(list(self.SHAPES.keys()))
        
        self.shape_type = shape_type
        self.rotation_state = 0
        self.shapes_list = self.SHAPES[shape_type]['shapes']
        self.shape = self.shapes_list[0]
        self.color = self.SHAPES[shape_type]['color']
        
        # 初始位置
        self.x = 0
        self.y = 0
        
        # 用于动画效果
        self.fall_progress = 0.0  # 0.0 到 1.0 的下落进度
    
    def rotate_clockwise(self):
        """顺时针旋转方块"""
        if len(self.shapes_list) > 1:  # O型方块不需要旋转
            self.rotation_state = (self.rotation_state + 1) % len(self.shapes_list)
            self.shape = self.shapes_list[self.rotation_state]
    
    def rotate_counterclockwise(self):
        """逆时针旋转方块"""
        if len(self.shapes_list) > 1:
            self.rotation_state = (self.rotation_state - 1) % len(self.shapes_list)
            self.shape = self.shapes_list[self.rotation_state]
    
    def get_next_rotation(self):
        """获取旋转后的形状（不改变当前状态）"""
        if len(self.shapes_list) > 1:
            next_state = (self.rotation_state + 1) % len(self.shapes_list)
            return self.shapes_list[next_state]
        return self.shape
    
    def get_positions(self):
        """
        获取方块所有格子的位置

        返回:
            list: 包含所有格子坐标的列表 [(x1,y1), (x2,y2),...]
        """
        positions = []
        for row_idx, row in enumerate(self.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    positions.append((self.x + col_idx, self.y + row_idx))
        return positions
    
    def get_ghost_positions(self, board, current_y):
        """
        获取幽灵方块位置（显示方块将要落在哪里）
        
        参数:
            board: 游戏板对象
            current_y: 当前y坐标
            
        返回:
            幽灵方块的位置列表
        """
        ghost_y = current_y
        
        # 不断向下移动直到碰撞
        while board.is_valid_move(self, self.x, ghost_y + 1):
            ghost_y += 1
        
        # 计算幽灵方块的位置
        ghost_positions = []
        for row_idx, row in enumerate(self.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    ghost_positions.append((self.x + col_idx, ghost_y + row_idx))
        
        return ghost_positions
    
    def draw_block_3d(self, surface, x, y, size, color_name, alpha=255):
        """
        绘制3D效果的方块
        
        参数:
            surface: pygame绘制表面
            x, y: 绘制位置
            size: 方块大小
            color_name: 颜色名称
            alpha: 透明度 (0-255)
        """
        if color_name not in GRADIENT_COLORS:
            # 没有渐变色配置，使用纯色
            color = COLORS.get(color_name, COLORS['WHITE'])
            rect = pygame.Rect(x, y, size, size)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, COLORS['DARK_GRAY'], rect, 2)
            return
        
        # 获取渐变色
        color_light, color_dark = GRADIENT_COLORS[color_name]
        
        # 主体（渐变效果）
        main_rect = pygame.Rect(x + 2, y + 2, size - 4, size - 4)
        
        # 绘制渐变（简化版：用两个矩形模拟）
        pygame.draw.rect(surface, color_light, main_rect)
        
        # 右下暗部
        dark_rect = pygame.Rect(x + size//2, y + size//2, size//2 - 2, size//2 - 2)
        dark_surf = pygame.Surface((dark_rect.width, dark_rect.height))
        dark_surf.fill(color_dark)
        dark_surf.set_alpha(128)
        surface.blit(dark_surf, dark_rect.topleft)
        
        # 高光（左上角）
        highlight_rect = pygame.Rect(x + 3, y + 3, size // 4, size // 4)
        highlight_color = tuple(min(c + 50, 255) for c in color_light)
        pygame.draw.rect(surface, highlight_color, highlight_rect)
        
        # 边框
        border_rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, color_dark, border_rect, 2)
        
        # 内边框（高光）
        inner_border = pygame.Rect(x + 1, y + 1, size - 2, size - 2)
        pygame.draw.rect(surface, color_light, inner_border, 1)
    
    def copy(self):
        """创建方块的副本"""
        new_tetromino = Tetromino(self.shape_type)
        new_tetromino.rotation_state = self.rotation_state
        new_tetromino.shape = self.shape
        new_tetromino.x = self.x
        new_tetromino.y = self.y
        return new_tetromino
