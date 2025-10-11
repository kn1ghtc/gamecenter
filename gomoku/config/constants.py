"""游戏常量配置
Game constants for Gomoku.
"""

from typing import Tuple

# 棋盘配置
BOARD_SIZE = 15  # 标准15×15棋盘
CELL_SIZE = 40   # 每个格子的像素大小

# 颜色方案（RGB）
COLORS = {
    # 棋盘
    'board_bg': (220, 179, 92),          # 木色背景
    'board_line': (50, 50, 50),          # 棋盘线（深灰）
    'board_border': (139, 90, 43),       # 棋盘边框（深棕）
    'board_star': (100, 100, 100),       # 星位点（灰色）
    
    # 棋子
    'black_stone': (20, 20, 20),         # 黑子（近黑）
    'black_highlight': (60, 60, 60),     # 黑子高光
    'white_stone': (245, 245, 245),      # 白子（象牙白）
    'white_highlight': (255, 255, 255),  # 白子高光
    'stone_shadow': (100, 100, 100),     # 棋子阴影
    
    # 特殊标记
    'last_move': (255, 0, 0),            # 最后一步标记（红色）
    'winning_line': (255, 215, 0),       # 获胜线（金色）
    'preview': (128, 128, 128, 128),     # 预览棋子（半透明灰）
    
    # UI背景
    'ui_bg': (40, 40, 45),               # 深色UI背景
    'ui_panel': (50, 50, 55),            # 面板背景
    'ui_text': (220, 220, 220),          # 浅色文字
    'ui_text_dim': (150, 150, 150),      # 暗淡文字
    
    # 按钮
    'button_normal': (70, 130, 180),     # 钢青色
    'button_hover': (100, 149, 237),     # 淡蓝色
    'button_pressed': (50, 100, 150),    # 深蓝色
    'button_disabled': (100, 100, 100),  # 灰色（禁用）
    'button_text': (255, 255, 255),      # 按钮文字
    
    # 状态颜色
    'success': (34, 139, 34),            # 成功（绿色）
    'warning': (255, 165, 0),            # 警告（橙色）
    'error': (220, 20, 60),              # 错误（红色）
    'info': (70, 130, 180),              # 信息（蓝色）
}

# 窗口配置
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 700
WINDOW_DEFAULT_WIDTH = 1000
WINDOW_DEFAULT_HEIGHT = 900

# 游戏配置
MAX_UNDO_COUNT = 3  # 最大悔棋次数
AI_TIME_LIMIT = 10.0  # AI思考时间限制（秒）

# 音效配置
SOUND_VOLUME = 0.7  # 默认音量（0.0-1.0）

# 文件路径
SETTINGS_FILE = "settings.json"
SAVE_DIR = "saves"
