"""
游戏配置文件
包含所有游戏参数和设置
"""
import os

# 游戏窗口设置
GAME_CONFIG = {
    'WIDTH': 1600,
    'HEIGHT': 900,
    'FPS': 120,
    'TITLE': 'Tank Battle',
    'BG_COLOR': (30, 30, 30)
}

# 网格和地图设置
MAP_CONFIG = {
    'CELL_SIZE': 25,
    'GRID_WIDTH': GAME_CONFIG['WIDTH'] // 25,  # 48
    'GRID_HEIGHT': GAME_CONFIG['HEIGHT'] // 25,  # 32
    'MAX_LEVEL': 30
}

# 颜色定义
COLORS = {
    'WALL': (120, 120, 120),
    'PLAYER': (0, 200, 0),
    'ENEMY': (200, 0, 0),
    'PLAYER_BASE': (0, 0, 200),
    'ENEMY_BASE': (200, 0, 200),
    'NEUTRAL': (100, 100, 100),
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0)
}

# 玩家坦克配置
PLAYER_CONFIG = {
    'SIZE': (40, 40),
    'HEALTH': 100,
    'MAX_HEALTH': 100,
    'SPEED': 2,
    'ROTATION_SPEED': 0.0025,  # 弧度
    'RELOAD_TIME': 20,  # 帧数 - 减少冷却时间，使持续射击更流畅
    'TURRET_LENGTH': 28,
    'TURRET_WIDTH': 7,
    'COLOR': COLORS['PLAYER'],
    'IMAGE': os.path.join('assets', 'PNG', 'Tanks', 'tankGreen.png')
}

# 敌方坦克配置
ENEMY_CONFIG = {
    'SIZE': (40, 40),
    'HEALTH': 3,
    'MAX_HEALTH': 3,
    'SPEED': 1,
    'ROTATION_SPEED': 0.0125,
    'RELOAD_TIME': 60,
    'TURRET_LENGTH': 28,
    'TURRET_WIDTH': 7,
    'COLOR': COLORS['ENEMY'],
    'IMAGE': os.path.join('assets', 'PNG', 'Tanks', 'tankRed.png'),
    'FIRE_RATE': 0.03,  # 增加射击频率，每帧射击概率
    'AI_ROTATION_THRESHOLD': 0.08,  # 减小旋转阈值，让AI更精确
    'AI_VISION_RANGE': min(GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']) * 0.95,  # 视野范围为屏幕较短边的85%
    'AI_ATTACK_RANGE': min(GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']) * 0.45,  # 攻击范围为屏幕较短边的45%
    'AI_OBSTACLE_DETECTION_DISTANCE': 150,  # 增加障碍物检测距离
    'AI_STUCK_THRESHOLD': 90,  # 减少被困阈值，让AI更快重新规划
    'AI_PATH_PLANNING_COOLDOWN': 20,  # 减少路径规划冷却时间
    'AI_PURSUIT_RANGE': min(GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']) * 0.65,  # 追击范围为屏幕较短边的65%
    'AI_MIN_FIRE_DISTANCE': 120,  # 最小开火距离，避免近距离误伤
    'AI_MAX_FIRE_DISTANCE': min(GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']) * 0.4  # 最大开火距离
}

# 子弹类型配置
BULLET_TYPES = {
    'NORMAL': {
        'RADIUS': 5,
        'SPEED': 7,
        'DAMAGE': 1,
        'CAN_PIERCE_WALL': False,
        'COLOR': None,  # 根据所有者决定
        'WALL_DAMAGE': 1
    },
    'PIERCING': {
        'RADIUS': 6,
        'SPEED': 8,
        'DAMAGE': 2,
        'CAN_PIERCE_WALL': True,
        'COLOR': (255, 255, 0),  # 黄色
        'WALL_DAMAGE': 2
    },
    'EXPLOSIVE': {
        'RADIUS': 8,
        'SPEED': 5,
        'DAMAGE': 3,
        'CAN_PIERCE_WALL': False,
        'COLOR': (255, 128, 0),  # 橙色
        'WALL_DAMAGE': 3,
        'EXPLOSION_RADIUS': 50,
        'EXPLOSION_DAMAGE': 2
    },
    'RAPID': {
        'RADIUS': 4,
        'SPEED': 10,
        'DAMAGE': 1,
        'CAN_PIERCE_WALL': False,
        'COLOR': (100, 255, 100),  # 绿色
        'WALL_DAMAGE': 1
    },
    'HEAVY': {
        'RADIUS': 10,
        'SPEED': 4,
        'DAMAGE': 5,
        'CAN_PIERCE_WALL': False,
        'COLOR': (255, 50, 50),  # 红色
        'WALL_DAMAGE': 4
    }
}

# 玩家和敌方子弹配置
PLAYER_BULLET_CONFIG = {
    'TYPE': 'NORMAL',  # 可以是 'NORMAL', 'PIERCING', 'EXPLOSIVE'
}

ENEMY_BULLET_CONFIG = {
    'TYPE': 'NORMAL',
}

# 墙壁配置
WALL_CONFIG = {
    'HEALTH': 3,
    'COLOR': COLORS['WALL']
}

# 基地配置
BASE_CONFIG = {
    'PLAYER_BASE': {
        'SIZE': (50, 50),
        'HEALTH': 5,
        'MAX_HEALTH': 5,
        'COLOR': COLORS['PLAYER_BASE'],
        'POSITION': 'BOTTOM_CENTER'  # 或具体坐标
    },
    'ENEMY_BASE': {
        'SIZE': (50, 50),
        'HEALTH': 40,
        'MAX_HEALTH': 40,
        'COLOR': COLORS['ENEMY_BASE'],
        'POSITION': 'TOP_CENTER'  # 或具体坐标
    }
}

# 音效文件路径
SOUND_CONFIG = {
    'EXPLOSION': os.path.join('assets', 'explosion.wav'),
    'SHOOT': os.path.join('assets', 'shoot.wav')
}

# 胜利条件配置
WIN_CONDITION = {
    'DESTROY_ENEMY_BASE': True,
    'ELIMINATE_ALL_ENEMIES': True,
    'BOTH_REQUIRED': True,  # 如果为True，需要同时满足上述两个条件
    'TIME_LIMIT': None  # 如果设置，则为时间限制（毫秒）
}

# 关卡生成配置
LEVEL_CONFIG = {
    'ENEMIES_BASE': 8,  # 基础敌人数量
    'ENEMIES_INCREMENT': 2,  # 每5关增加的敌人数量
    'ENEMIES_INCREMENT_INTERVAL': 5,  # 每几关增加敌人
    'MAX_ENEMIES': 20,  # 最大敌人数量
    'MAZE_COMPLEXITY_INCREMENT': 2,  # 每几关增加迷宫复杂度
    'PLAYER_SAFE_ZONE_RADIUS': 125  # 玩家初始位置安全区域半径
}

# UI显示配置
UI_CONFIG = {
    'SHOW_UI': True,
    'UI_TRANSPARENCY': 0.7,
    'UI_BACKGROUND': True,
    'UI_POSITION': 'TOP_LEFT',  # TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT
    'UI_MARGIN': 10,
    'FONT_SIZE': 18,  # 缩小字体
    'BIG_FONT_SIZE': 28  # 缩小大字体
}
