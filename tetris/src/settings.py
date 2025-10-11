"""
俄罗斯方块游戏配置文件

包含所有游戏相关的常量和配置项，支持100关卡系统、
自适应屏幕尺寸、关卡速度递增等特性
"""
import pygame

# 获取屏幕信息实现自适应
def get_screen_info():
    """获取屏幕信息"""
    pygame.init()
    info = pygame.display.Info()
    return info.current_w, info.current_h

# 屏幕尺寸（自适应）
SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_info()
WINDOW_WIDTH = min(1200, int(SCREEN_WIDTH * 0.8))
WINDOW_HEIGHT = min(900, int(SCREEN_HEIGHT * 0.85))

# 游戏板尺寸
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# 方块大小（根据窗口高度自适应）
BLOCK_SIZE = min(35, (WINDOW_HEIGHT - 100) // BOARD_HEIGHT)

# 游戏板偏移量（使游戏板居中偏左）
BOARD_OFFSET_X = int(WINDOW_WIDTH * 0.25)
BOARD_OFFSET_Y = (WINDOW_HEIGHT - BOARD_HEIGHT * BLOCK_SIZE) // 2

# 颜色定义（增强配色方案）
COLORS = {
    'BLACK': (15, 15, 25),
    'WHITE': (245, 245, 250),
    'GRAY': (100, 100, 110),
    'LIGHT_GRAY': (180, 180, 190),
    'DARK_GRAY': (50, 50, 60),
    
    # 方块颜色（更鲜艳饱和的配色）
    'RED': (255, 65, 65),
    'GREEN': (50, 220, 100),
    'BLUE': (65, 130, 255),
    'CYAN': (50, 220, 220),
    'MAGENTA': (220, 50, 220),
    'YELLOW': (255, 220, 50),
    'ORANGE': (255, 150, 50),
    'PURPLE': (180, 80, 220),
    
    # UI配色
    'UI_BG': (25, 25, 40),
    'UI_BORDER': (100, 150, 255),
    'TEXT_PRIMARY': (245, 245, 250),
    'TEXT_SECONDARY': (150, 150, 170),
    'BUTTON_HOVER': (80, 120, 200),
    'LEVEL_UP': (255, 215, 0),
    'COMBO': (255, 100, 255),
}

# 方块渐变色配置（用于3D效果）
GRADIENT_COLORS = {
    'RED': [(255, 65, 65), (200, 40, 40)],
    'GREEN': [(50, 220, 100), (30, 170, 70)],
    'BLUE': [(65, 130, 255), (40, 90, 200)],
    'CYAN': [(50, 220, 220), (30, 170, 170)],
    'MAGENTA': [(220, 50, 220), (170, 30, 170)],
    'YELLOW': [(255, 220, 50), (200, 170, 30)],
    'ORANGE': [(255, 150, 50), (200, 110, 30)],
    'PURPLE': [(180, 80, 220), (130, 50, 170)],
}

# 关卡配置（1-100关）
MAX_LEVEL = 100
BASE_FALL_SPEED = 1000  # 基础下落速度（毫秒）
LEVEL_SPEED_DECREASE = 15  # 每关速度增加（毫秒减少）
MIN_FALL_SPEED = 100  # 最小下落速度

def get_level_speed(level):
    """根据关卡获取下落速度"""
    speed = BASE_FALL_SPEED - (level - 1) * LEVEL_SPEED_DECREASE
    return max(MIN_FALL_SPEED, speed)

# 分数系统配置
SCORE_SINGLE_LINE = 100
SCORE_DOUBLE_LINE = 300
SCORE_TRIPLE_LINE = 500
SCORE_TETRIS = 800  # 四行消除
SCORE_SOFT_DROP = 1  # 软下落每格得分
SCORE_HARD_DROP = 2  # 硬下落每格得分
COMBO_MULTIPLIER = 1.5  # 连击倍数

# 关卡升级条件
LINES_PER_LEVEL = 10  # 每消除10行升一级

# 游戏配置
FPS = 60
MOVE_DELAY = 150  # 移动延迟（毫秒）
ROTATE_DELAY = 200  # 旋转延迟（毫秒）
LOCK_DELAY = 500  # 锁定延迟（毫秒）

# 动画配置
CLEAR_LINE_ANIMATION_DURATION = 500  # 消行动画时长（毫秒）
PARTICLE_COUNT = 30  # 粒子效果数量
PARTICLE_LIFETIME = 1000  # 粒子生命周期（毫秒）

# UI布局配置
UI_PANEL_WIDTH = WINDOW_WIDTH - BOARD_OFFSET_X - BOARD_WIDTH * BLOCK_SIZE - 80
UI_PANEL_X = BOARD_OFFSET_X + BOARD_WIDTH * BLOCK_SIZE + 40
PREVIEW_SIZE = 6 * BLOCK_SIZE  # 预览区域大小

# 字体配置
FONT_SIZES = {
    'TITLE': 48,
    'LARGE': 36,
    'MEDIUM': 28,
    'SMALL': 22,
    'TINY': 18,
}

# 资源路径
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')

# 确保资源目录存在
for dir_path in [ASSETS_DIR, FONTS_DIR, SOUNDS_DIR, IMAGES_DIR]:
    os.makedirs(dir_path, exist_ok=True)
