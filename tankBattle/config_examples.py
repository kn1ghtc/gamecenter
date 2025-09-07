"""
游戏配置演示文件
展示如何通过修改配置来改变游戏体验
"""

# 示例1：超级玩家模式
SUPER_PLAYER_CONFIG = {
    'SIZE': (40, 40),
    'HEALTH': 200,          # 双倍生命值
    'MAX_HEALTH': 200,
    'SPEED': 5,             # 更快的速度
    'ROTATION_SPEED': 0.02, # 更快的旋转
    'RELOAD_TIME': 15,      # 更快的射击
    'TURRET_LENGTH': 28,
    'TURRET_WIDTH': 7,
    'COLOR': (0, 200, 0),
    'IMAGE': 'assets/PNG/Tanks/tankGreen.png'
}

# 示例2：困难模式 - 强化敌人
HARD_ENEMY_CONFIG = {
    'SIZE': (40, 40),
    'HEALTH': 5,            # 更多生命值
    'MAX_HEALTH': 5,
    'SPEED': 2,             # 更快速度
    'ROTATION_SPEED': 0.015,
    'RELOAD_TIME': 30,
    'TURRET_LENGTH': 28,
    'TURRET_WIDTH': 7,
    'COLOR': (200, 0, 0),
    'IMAGE': 'assets/PNG/Tanks/tankRed.png',
    'FIRE_RATE': 0.04,      # 更高射击频率
    'AI_ROTATION_THRESHOLD': 0.05
}

# 示例3：爆炸弹模式
EXPLOSIVE_PLAYER_BULLET = {
    'TYPE': 'EXPLOSIVE'     # 玩家使用爆炸弹
}

PIERCING_ENEMY_BULLET = {
    'TYPE': 'PIERCING'      # 敌人使用穿甲弹
}

# 示例4：快节奏模式
FAST_GAME_CONFIG = {
    'WIDTH': 1200,
    'HEIGHT': 800,
    'FPS': 144,             # 更高帧率
    'TITLE': 'Tank Battle - Fast Mode',
    'BG_COLOR': (20, 20, 40)  # 深蓝色背景
}

# 示例5：只需摧毁基地的胜利条件
BASE_ONLY_WIN = {
    'DESTROY_ENEMY_BASE': True,
    'ELIMINATE_ALL_ENEMIES': False,
    'BOTH_REQUIRED': False,
    'TIME_LIMIT': None
}

# 示例6：限时模式
TIME_ATTACK_WIN = {
    'DESTROY_ENEMY_BASE': True,
    'ELIMINATE_ALL_ENEMIES': True,
    'BOTH_REQUIRED': True,
    'TIME_LIMIT': 120000    # 2分钟限制
}

# 示例7：自定义子弹类型
CUSTOM_BULLET_TYPES = {
    'NORMAL': {
        'RADIUS': 5,
        'SPEED': 7,
        'DAMAGE': 1,
        'CAN_PIERCE_WALL': False,
        'COLOR': None,
        'WALL_DAMAGE': 1
    },
    'SUPER_PIERCING': {     # 新的超级穿甲弹
        'RADIUS': 8,
        'SPEED': 12,
        'DAMAGE': 3,
        'CAN_PIERCE_WALL': True,
        'COLOR': (0, 255, 255),  # 青色
        'WALL_DAMAGE': 5
    },
    'MEGA_EXPLOSIVE': {     # 超级爆炸弹
        'RADIUS': 10,
        'SPEED': 4,
        'DAMAGE': 5,
        'CAN_PIERCE_WALL': False,
        'COLOR': (255, 0, 255),  # 紫色
        'WALL_DAMAGE': 8,
        'EXPLOSION_RADIUS': 100,
        'EXPLOSION_DAMAGE': 4
    }
}

"""
使用方法：
1. 将上述配置复制到 config.py 中对应的变量
2. 例如，要启用超级玩家模式：
   将 PLAYER_CONFIG 替换为 SUPER_PLAYER_CONFIG
3. 要启用困难模式：
   将 ENEMY_CONFIG 替换为 HARD_ENEMY_CONFIG
4. 要使用自定义子弹：
   将 BULLET_TYPES 替换为 CUSTOM_BULLET_TYPES
   然后设置 PLAYER_BULLET_CONFIG = {'TYPE': 'SUPER_PIERCING'}
"""
