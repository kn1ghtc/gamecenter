# 窗口设置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# 方块大小
BLOCK_SIZE = 30

# 游戏板偏移量 (使游戏板居中)
BOARD_OFFSET_X = (WINDOW_WIDTH - 10 * BLOCK_SIZE) // 2  # 假设游戏板宽度为10个方块
BOARD_OFFSET_Y = 50  # 距离顶部50像素

# 游戏板尺寸
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# 颜色定义
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'CYAN': (0, 255, 255),
    'MAGENTA': (255, 0, 255),
    'YELLOW': (255, 255, 0),
    'ORANGE': (255, 165, 0),
    'PURPLE': (128, 0, 128)
}

# 游戏难度设置
DIFFICULTY_LEVELS = {
    'EASY': {
        'speed': 0.1,
        'score_multiplier': 1
    },
    'MEDIUM': {
        'speed': 0.5,
        'score_multiplier': 2
    },
    'HARD': {
        'speed': 1.0,
        'score_multiplier': 3
    }
}

# 分数设置
SCORE_PER_LINE = 100
