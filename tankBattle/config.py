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
    'SPEED': 4,
    'ROTATION_SPEED': 0.005,  # 弧度
    'RELOAD_TIME': 60,  # 帧数 - 显著减少冷却时间，更快响应
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
    'SPEED': 2,  # 提高AI移动速度，增强机动性
    'ROTATION_SPEED': 0.025,  # 提高旋转速度，更快响应
    'RELOAD_TIME': 30,  # 减少冷却时间，增加射击频率
    'TURRET_LENGTH': 28,
    'TURRET_WIDTH': 7,
    'COLOR': COLORS['ENEMY'],
    'IMAGE': os.path.join('assets', 'PNG', 'Tanks', 'tankRed.png'),
    'FIRE_RATE': 0.35,  # 大幅提高射击频率，让AI更积极攻击
    'AI_ROTATION_THRESHOLD': 0.15,  # 稍微放宽旋转阈值，更流畅
    'AI_VISION_RANGE': 380,  # 扩大视野范围
    'AI_ATTACK_RANGE': 350,  # 主要攻击范围
    'AI_CLOSE_COMBAT_RANGE': 100,  # 近战范围
    'AI_OBSTACLE_DETECTION_DISTANCE': 80,  # 增强障碍物检测
    'AI_STUCK_THRESHOLD': 20,  # 降低被困阈值，更快脱困
    'AI_PATH_PLANNING_COOLDOWN': 60,  # 减少路径规划冷却时间
    'AI_PURSUIT_RANGE': 350,  # 追击范围
    'AI_MIN_FIRE_DISTANCE': 5,  # 减少最小开火距离
    'AI_MAX_FIRE_DISTANCE': 380,  # 最大开火距离，与视野范围匹配
    'AI_AGGRESSIVE_THRESHOLD': 0.8,  # 提高攻击性阈值
    'AI_DECISION_FREQUENCY': 1,  # 每帧都进行决策，更快响应
    'AI_MOVEMENT_DECISIVENESS': 0.7,  # 移动决策的坚决程度
    'AI_COMBAT_AGGRESSIVENESS': 0.8,  # 战斗积极性
}

# AI系统配置
AI_CONFIG = {
    # 全局AI设置
    'ENABLED': True,  # 是否启用AI系统
    'DEFAULT_LEVEL': 'auto',  # 默认AI级别: 'basic', 'smart', 'enhanced', 'auto'
    'AUTO_SWITCH': True,  # 是否根据性能自动切换AI级别
    'PERFORMANCE_MONITOR': True,  # 是否启用性能监控

    # AI决策配置 - 新增更激进的参数
    'DECISION_CONFIG': {
        'decision_timeout': 5,  # 极大减少决策超时时间，更快响应
        'strategy_timeout': 10,  # 减少策略超时时间
        'tactical_timeout': 5,   # 减少战术超时时间
        'operational_timeout': 3,  # 减少操作超时时间
        'reactive_timeout': 1,   # 反应层超时时间最短，快速响应
        'stuck_recovery_timeout': 15,  # 减少脱困时间
        'pathfinding_timeout': 10,  # 减少路径查找时间
        'decision_interval': 1,  # 每帧都决策，让AI更活跃
        'learning_interval': 300,  # 学习间隔保持不变
        'max_concurrent_decisions': 3,  # 允许更多并发决策
        'min_decision_confidence': 0.4,  # 降低决策置信度要求，更容易做决策
        'threat_response_priority': 0.9,  # 威胁响应优先级
        'target_acquisition_priority': 0.8,  # 目标获取优先级
        'movement_priority': 0.7,  # 移动优先级
        'combat_priority': 0.9,  # 战斗优先级
        'exploration_priority': 0.5,  # 探索优先级
        'aggressive_behavior_multiplier': 1.5,  # 攻击性行为倍数
        'defensive_behavior_multiplier': 0.6,  # 防御性行为倍数
        'pursuit_tenacity': 0.9,  # 追击坚持度
        'evasion_sensitivity': 0.5,  # 闪避敏感度
    },

    # AI调试配置 - 新增调试开关
    'DEBUG_CONFIG': {
        'enable_ai_debug': False,  # 主调试开关
        'enable_decision_logging': False,  # 决策过程日志
        'enable_shooting_debug': False,  # 射击决策调试
        'enable_movement_debug': False,  # 移动决策调试
        'enable_target_debug': False,  # 目标识别调试
        'debug_output_frequency': 60,  # 调试输出频率（帧数）
        'debug_tank_id': None,  # 调试特定坦克ID，None表示调试所有
        'log_to_file': False,  # 是否将调试信息输出到文件
        'debug_log_path': 'ai_debug.log',  # 调试日志文件路径
    },

    # 强化学习配置
    'RL_CONFIG': {
        'LEARNING_RATE': 0.001,
        'EPSILON_START': 1.0,
        'EPSILON_END': 0.01,
        'EPSILON_DECAY': 0.995,
        'MEMORY_SIZE': 10000,
        'BATCH_SIZE': 32,
        'TARGET_UPDATE_FREQUENCY': 100,
        'TRAINING_ENABLED': False,  # 游戏中禁用实时训练，只进行离线训练
        'MODEL_SAVE_FREQUENCY': 1000  # 每N步保存一次模型
    },

    # 路径规划配置
    'PATHFINDING_CONFIG': {
        'ALGORITHM': 'A_STAR',  # 'A_STAR', 'DIJKSTRA'
        'CACHE_SIZE': 1000,
        'THREAT_WEIGHT': 2.0,
        'DISTANCE_WEIGHT': 1.0,
        'MAX_SEARCH_NODES': 5000,
        'TIMEOUT_MS': 30
    },

    # 战术AI配置
    'TACTICAL_CONFIG': {
        'DECISION_LAYERS': ['strategic', 'tactical', 'operational', 'reactive'],
        'DECISION_TIMEOUT_MS': 30,
        'BEHAVIOR_PREDICTION': True,
        'BATTLEFIELD_ANALYSIS': True,
        'MULTI_TARGET_TRACKING': True,
        'ADAPTIVE_DIFFICULTY': True
    },

    # 性能优化配置
    'PERFORMANCE_CONFIG': {
        'MAX_AI_INSTANCES': 40,  # 最大AI实例数
        'UPDATE_FREQUENCY': 1,  # AI更新频率（每N帧）
        'BACKGROUND_PROCESSING': False,  # 是否启用后台处理
        'MEMORY_CLEANUP_FREQUENCY': 500,  # 内存清理频率
        'CACHE_ENABLED': True,
        'PROFILING_ENABLED': False  # 性能分析
    }
}

# 子弹类型配置
BULLET_TYPES = {
    'NORMAL': {
        'RADIUS': 5,
        'SPEED': 3,
        'DAMAGE': 1,
        'CAN_PIERCE_WALL': False,
        'COLOR': None,  # 根据所有者决定
        'WALL_DAMAGE': 1,
        'MAX_RANGE': 400,  # 最大射程
        'LIFETIME': 57  # 生命周期(帧数) = MAX_RANGE / SPEED
    },
    'PIERCING': {
        'RADIUS': 6,
        'SPEED': 8,
        'DAMAGE': 3,
        'CAN_PIERCE_WALL': True,
        'COLOR': (255, 255, 0),  # 黄色
        'WALL_DAMAGE': 2,
        'MAX_RANGE': 1600,  # 全屏射程
        'LIFETIME': 100  # 1600 / 8 = 200
    },
    'EXPLOSIVE': {
        'RADIUS': 8,
        'SPEED': 5,
        'DAMAGE': 3,
        'CAN_PIERCE_WALL': False,
        'COLOR': (255, 128, 0),  # 橙色
        'WALL_DAMAGE': 3,
        'EXPLOSION_RADIUS': 50,
        'EXPLOSION_DAMAGE': 6,
        'MAX_RANGE': 300,  # 较短射程但爆炸伤害
        'LIFETIME': 60  # 300 / 5 = 60
    },
    'RAPID': {
        'RADIUS': 4,
        'SPEED': 10,
        'DAMAGE': 1,
        'CAN_PIERCE_WALL': False,
        'COLOR': (100, 255, 100),  # 绿色
        'WALL_DAMAGE': 1,
        'MAX_RANGE': 350,  # 中等射程
        'LIFETIME': 35  # 350 / 10 = 35
    },
    'HEAVY': {
        'RADIUS': 10,
        'SPEED': 4,
        'DAMAGE': 5,
        'CAN_PIERCE_WALL': False,
        'COLOR': (255, 50, 50),  # 红色
        'WALL_DAMAGE': 4,
        'MAX_RANGE': 250,  # 短射程但高伤害
        'LIFETIME': 62  # 250 / 4 ≈ 62
    },
    'BARRICADE': {
        'RADIUS': 7,
        'SPEED': 6,
        'DAMAGE': 0,  # 掩体弹不造成伤害
        'CAN_PIERCE_WALL': False,
        'COLOR': (150, 75, 0),  # 棕色
        'WALL_DAMAGE': 0,
        'CREATES_WALL': True,  # 标记为创建墙体的子弹
        'BARRICADE_HEALTH': 5,  # 生成的掩体墙血量
        'BARRICADE_SIZE': (50, 25),  # 掩体墙尺寸 (宽, 高)
        'COOLDOWN': 180,  # 冷却时间(帧数) - 3秒@60FPS
        'MAX_RANGE': 200,  # 短射程，用于近距离部署
        'LIFETIME': 33  # 200 / 6 ≈ 33
    }
}

# 玩家和敌方子弹配置
PLAYER_BULLET_CONFIG = {
    'DEFAULT_TYPE': 'PIERCING',  # 默认子弹类型
    'AVAILABLE_TYPES': ['NORMAL', 'PIERCING', 'EXPLOSIVE', 'RAPID', 'HEAVY', 'BARRICADE'],  # 玩家可用的所有子弹类型
    'UNLIMITED_AMMO': True,  # 玩家弹药无限制
    'FREE_SWITCHING': True,  # 可以自由切换子弹类型，无冷却
}

ENEMY_BULLET_CONFIG = {
    'DEFAULT_TYPE': 'NORMAL',  # 默认子弹类型
    'BASE_AVAILABLE_TYPES': ['NORMAL'],  # AI坦克基础可用类型（只有普通弹）
    'UNLIMITED_AMMO': True,  # AI弹药无限制
    'SPECIAL_EFFECTS_REQUIRED': True,  # 需要特殊效果才能使用特殊子弹
}

# 墙壁配置
WALL_CONFIG = {
    'HEALTH': 3,
    'COLOR': COLORS['WALL']
}

# 隔离围墙配置
BARRIER_WALL_CONFIG = {
    'HEALTH': 20,  # 可被攻击的围墙（按需调整）
    'COLOR': (80, 80, 150),  # 深蓝色，区别于普通围墙
    'THICKNESS': 2,  # 双排围墙厚度
    'PASSAGE_COUNT': 3,  # 随机预留3个通道
    'PASSAGE_WIDTH': 2,  # 每个通道宽度（网格单位）
    'DESTRUCTIBLE': True,  # 允许被攻击摧毁
    'PIERCING_PASSABLE': True  # 穿甲子弹可以穿过
}

# 基地配置
BASE_CONFIG = {
    'PLAYER_BASE': {
        'SIZE': (50, 50),
        'HEALTH': 100,
        'MAX_HEALTH': 100,
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
    'ENEMIES_BASE': 4,  # 基础敌人数量
    'ENEMIES_INCREMENT': 3,  # 每1关增加的敌人数量
    'ENEMIES_INCREMENT_INTERVAL': 2,  # 每几关增加敌人
    'MAX_ENEMIES': 20,  # 最大敌人数量
    'MAZE_COMPLEXITY_INCREMENT': 2,  # 每几关增加迷宫复杂度
    'PLAYER_SAFE_ZONE_RADIUS': 80  # 玩家初始位置安全区域半径
}

# 中文字体路径配置
import platform

def get_system_font_paths():
    """根据操作系统获取字体路径"""
    system = platform.system()

    if system == "Windows":
        return [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "C:/Windows/Fonts/simkai.ttf",    # 楷体
            "C:/Windows/Fonts/calibri.ttf",   # Calibri（备用）
            "C:/Windows/Fonts/arial.ttf",     # Arial（备用）
        ]
    elif system == "Darwin":  # macOS
        return [
            "/System/Library/Fonts/PingFang.ttc",           # 苹方字体
            "/System/Library/Fonts/Hiragino Sans GB.ttc",   # 冬青黑体简体中文
            "/System/Library/Fonts/STHeiti Light.ttc",      # 华文黑体
            "/System/Library/Fonts/STHeiti Medium.ttc",     # 华文黑体中等
            "/System/Library/Fonts/Arial Unicode.ttf",      # Arial Unicode MS
            "/Library/Fonts/Arial Unicode.ttf",             # 系统Arial Unicode MS
            "/System/Library/Fonts/Helvetica.ttc",          # Helvetica（备用）
            "/System/Library/Fonts/Times.ttc",              # Times（备用）
        ]
    elif system == "Linux":
        return [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",        # 文泉驿正黑
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",      # 文泉驿微米黑
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Noto Sans CJK
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      # DejaVu Sans
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Liberation Sans
        ]
    else:
        # 未知系统，返回通用路径
        return []

CHINESE_FONT_PATHS = get_system_font_paths()

# 字体缓存，避免重复打印
_font_loading_logged = False

def get_chinese_font(size):
    """获取可用的中文字体"""
    import pygame
    import platform
    global _font_loading_logged

    # 确保pygame字体系统已初始化
    if not pygame.font.get_init():
        pygame.font.init()

    system = platform.system()
    if not _font_loading_logged:
        print(f"[字体] 加载{system}中文字体...")
        _font_loading_logged = True

    # 首先尝试直接使用字体文件路径（最可靠）
    for i, font_path in enumerate(CHINESE_FONT_PATHS):
        try:
            if os.path.exists(font_path):
                font = pygame.font.Font(font_path, size)
                # 测试字体是否支持中文
                test_surface = font.render('测试中文', True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    if not _font_loading_logged:  # 只在第一次输出成功信息
                        print(f"[字体] 成功: {os.path.basename(font_path)}")
                    return font
        except:
            continue

    # 如果文件路径失败，尝试系统字体名称（跨平台）
    def get_system_font_names():
        if system == "Windows":
            return [
                'Microsoft YaHei',     # 微软雅黑
                'SimHei',             # 黑体
                'Microsoft YaHei UI', # 微软雅黑UI
                'SimSun',             # 宋体
                'Arial Unicode MS',   # Arial Unicode MS
            ]
        elif system == "Darwin":  # macOS
            return [
                'PingFang SC',        # 苹方-简
                'PingFang TC',        # 苹方-繁
                'Hiragino Sans GB',   # 冬青黑体简体中文
                'STHeiti',            # 华文黑体
                'Arial Unicode MS',   # Arial Unicode MS
                'Helvetica Neue',     # Helvetica Neue
            ]
        elif system == "Linux":
            return [
                'WenQuanYi Zen Hei',  # 文泉驿正黑
                'WenQuanYi Micro Hei', # 文泉驿微米黑
                'Noto Sans CJK SC',   # Noto Sans CJK 简体中文
                'DejaVu Sans',        # DejaVu Sans
                'Liberation Sans',    # Liberation Sans
            ]
        else:
            return []

    chinese_font_names = get_system_font_names()

    for font_name in chinese_font_names:
        try:
            font = pygame.font.SysFont(font_name, size)
            if font:
                # 测试字体是否支持中文
                test_surface = font.render('测试中文', True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    return font
        except:
            continue

    # 尝试pygame内置字体
    try:
        available_fonts = pygame.font.get_fonts()
        # 查找可能支持中文的字体
        chinese_candidate_fonts = []
        for font_name in available_fonts:
            if any(keyword in font_name.lower() for keyword in
                   ['cjk', 'chinese', 'zh', 'han', 'ping', 'fang', 'hei', 'unicode']):
                chinese_candidate_fonts.append(font_name)

        for font_name in chinese_candidate_fonts[:5]:  # 只测试前5个候选
            try:
                font = pygame.font.SysFont(font_name, size)
                test_surface = font.render('测试', True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    print(f"✓ 找到候选字体: {font_name}")
                    return font
            except:
                continue

    except Exception as e:
        print(f"× 获取系统字体列表失败: {e}")

    # 最终回退：使用默认字体
    print("⚠ 警告：未找到可用的中文字体，使用默认字体（中文可能显示为方框）")
    try:
        return pygame.font.Font(None, size)
    except:
        # 如果连默认字体都失败，尝试pygame的get_default_font
        try:
            default_font_name = pygame.font.get_default_font()
            return pygame.font.Font(default_font_name, size)
        except:
            # 最后的尝试
            return pygame.font.SysFont('arial', size)

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
