"""
游戏配置文件
"""
import pygame


# 屏幕设置
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# 物理参数
GRAVITY = 0.8
JUMP_FORCE = 18  # 增加跳跃力度以适应更高的平台
MOVE_SPEED = 5

# 玩家设置
PLAYER_SIZE = 40
MAX_HEALTH = 1000

# 武器设置
BULLET_SPEED = 10
BULLET_DAMAGE = 25
BOMB_DAMAGE = 50
BOMB_RADIUS = 120
FIRE_COOLDOWN = 0.2
BOMB_COOLDOWN = 1.0

# 敌人设置
ENEMY_SIZE = 35
ENEMY_HEALTH = 60
ENEMY_DAMAGE = 30
ENEMY_SPEED = 2

# 关卡设置
TOTAL_LEVELS = 30
ENEMIES_PER_LEVEL = 6  # 每关基础敌人数量

# 全屏模式增强设置
FULLSCREEN_WEAPON_SPEED_BOOST = 1.5  # 全屏模式武器速度增强
FULLSCREEN_WEAPON_RANGE_BOOST = 1.4  # 全屏模式武器射程增强
FULLSCREEN_JUMP_BOOST = 1.3          # 全屏模式跳跃力增强
FULLSCREEN_ENEMY_DETECTION_BOOST = 1.5  # 全屏模式敌人检测范围增强

# 游戏机制配置
GROUND_OFFSET = 50  # 地面偏移量
KNIFE_DEFAULT_RANGE = 150  # 匕首默认射程
WEAPON_SWITCH_COOLDOWN = 0.3  # 武器切换冷却时间
ENEMY_ATTACK_COOLDOWN = 60  # 敌人攻击冷却时间（帧数）

# 关卡时间配置
BASE_TIME_LIMIT = 240  # 基础时间限制（秒）
MIN_TIME_LIMIT = 120  # 最小时间限制（秒）
TIME_REDUCTION_PER_LEVEL = 3  # 每关减少的时间（秒）

# 分数配置
BASE_KILL_SCORE = 100  # 基础击杀分数
LEVEL_SCORE_MULTIPLIER = 10  # 关卡分数倍数
EXPLOSION_KILL_SCORE = 150  # 爆炸击杀分数
EXPLOSION_LEVEL_BONUS = 20  # 爆炸关卡奖励
COMPLETION_BASE_BONUS = 500  # 完成关卡基础奖励
COMPLETION_LEVEL_MULTIPLIER = 50  # 完成关卡等级倍数

# 敌人AI配置
ENEMY_BASE_DETECTION_RANGE = 100  # 敌人基础检测范围
ENEMY_BASE_CHASE_RANGE = 200  # 敌人基础追逐范围
ENEMY_FULLSCREEN_THRESHOLD = 1000  # 全屏模式检测阈值

# 平台配置
PLATFORM_COUNT_DIVISOR = 400  # 平台数量除数
PLATFORM_BASE_WIDTH = 120  # 平台基础宽度
PLATFORM_MARGIN = 50  # 平台边距
PLATFORM_MIN_Y = 100  # 平台最小Y坐标
PLATFORM_Y_OFFSET = 200  # 平台Y坐标偏移

# 玩家起始位置配置
PLAYER_START_X = 100  # 玩家起始X坐标
PLAYER_START_Y_OFFSET = 200  # 玩家起始Y坐标偏移

# UI配置
HEALTH_BAR_WIDTH = 200  # 生命条宽度
HEALTH_BAR_HEIGHT = 20  # 生命条高度
UI_MARGIN = 10  # UI边距
CONTROL_INFO_WIDTH = 200  # 控制信息宽度
CONTROL_INFO_MIN_X = 500  # 控制信息最小X坐标

# 游戏界面配置
GLOW_CYCLE_TIME = 500  # 发光效果循环时间（毫秒）
BOOST_INFO_Y_OFFSET = 60  # 增强信息Y偏移
SCORE_Y_POSITION = 100  # 分数显示Y坐标
CONTROLS_Y_POSITION = 200  # 控制说明Y坐标

# 菜单UI偏移配置
MENU_VERTICAL_OFFSET = 50  # 菜单垂直偏移
MENU_ITEM_SPACING = 100  # 菜单项间距

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
BROWN = (139, 69, 19)
PINK = (255, 192, 203)
LIME = (0, 255, 0)
NAVY = (0, 0, 128)
TEAL = (0, 128, 128)
SILVER = (192, 192, 192)
GOLD = (255, 215, 0)
GOLD_COLOR = GOLD  # 别名
CRIMSON = (220, 20, 60)

# 背景和地面颜色
BACKGROUND_COLOR = (135, 206, 250)  # 天蓝色
GROUND_COLOR = (34, 139, 34)  # 森林绿

# 主题颜色
FOREST_GREEN = (34, 139, 34)
DESERT_YELLOW = (238, 203, 173)
SNOW_WHITE = (248, 248, 255)
VOLCANO_RED = (178, 34, 34)
TECH_BLUE = (70, 130, 180)
HELL_PURPLE = (75, 0, 130)

# 键位映射（方向键控制）
CONTROLS = {
    'move_left': pygame.K_LEFT,
    'move_right': pygame.K_RIGHT,
    'jump': pygame.K_SPACE,
    'shoot': pygame.K_z,
    'bomb': pygame.K_x,
    'switch_weapon': pygame.K_c,
    'fullscreen': pygame.K_F11  # F11切换全屏
}

# 导入系统检测模块
import os
import platform

# 中文字体路径配置 - 跨平台支持
CHINESE_FONT_PATHS = {
    'Windows': [
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",    # 黑体
        "C:/Windows/Fonts/simsun.ttc",    # 宋体
        "C:/Windows/Fonts/simkai.ttf",    # 楷体
        "C:/Windows/Fonts/SIMYOU.TTF",    # 幼圆
        "C:/Windows/Fonts/STXIHEI.TTF",   # 华文细黑
    ],
    'Darwin': [  # macOS
        "/Library/Fonts/Arial Unicode MS.ttf",        # Arial Unicode MS (支持中文)
        "/System/Library/Fonts/PingFang.ttc",         # 苹方
        "/System/Library/Fonts/STHeiti Light.ttc",    # 华文黑体
        "/System/Library/Fonts/STHeiti Medium.ttc",   # 华文黑体中等
        "/System/Library/Fonts/Hiragino Sans GB.ttc", # 冬青黑体简体中文
        "/Library/Fonts/Songti.ttc",                  # 宋体
        "/System/Library/Fonts/Apple LiGothic Medium.ttc", # 苹果丽中黑
        "/Library/Fonts/Microsoft/SimHei.ttf",        # 微软黑体(如果安装了Office)
        "/Library/Fonts/Microsoft/SimSun.ttf",        # 微软宋体(如果安装了Office)
    ],
    'Linux': [  # Linux
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Android字体
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",               # 文泉驿正黑
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",             # 文泉驿微米黑
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",     # Noto Sans CJK
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Liberation
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",            # DejaVu Sans
    ]
}

# 获取可用的中文字体
def get_chinese_font(size):
    """获取可用的中文字体 - 跨平台支持"""
    # 检测当前操作系统
    system = platform.system()

    # 获取对应系统的字体路径列表
    font_paths = CHINESE_FONT_PATHS.get(system, [])

    # 尝试加载系统对应的字体
    for font_path in font_paths:
        try:
            if os.path.exists(font_path) and pygame.font.get_init():
                font = pygame.font.Font(font_path, size)
                # 验证字体是否能正确渲染中文
                test_surface = font.render("测试", True, (255, 255, 255))
                if test_surface.get_width() > 0:  # 如果能渲染出内容
                    return font
        except Exception as e:
            # 静默忽略字体加载错误，继续尝试下一个
            continue

    # 尝试使用pygame的系统字体
    try:
        if pygame.font.get_init():
            # 获取系统中的所有字体
            system_fonts = pygame.font.get_fonts()

            # 尝试常见的中文字体名称
            chinese_font_names = [
                'microsoftyahei',  # 微软雅黑
                'simhei',          # 黑体
                'simsun',          # 宋体
                'pingfang',        # 苹方 (macOS)
                'hiragino',        # 冬青黑体 (macOS)
                'notosanscjk',     # Noto Sans CJK (Linux)
                'wqyzenhei',       # 文泉驿正黑 (Linux)
                'droidsansfallback' # Android字体 (Linux)
            ]

            # 尝试找到系统中可用的中文字体
            for font_name in chinese_font_names:
                if font_name in system_fonts:
                    try:
                        font = pygame.font.SysFont(font_name, size)
                        # 验证字体是否能正确渲染中文
                        test_surface = font.render("测试", True, (255, 255, 255))
                        if test_surface.get_width() > 0:
                            return font
                    except:
                        continue
    except:
        pass

    # 最后的备用方案：使用默认字体，但尝试添加备用字符渲染
    try:
        if pygame.font.get_init():
            # 使用系统默认字体
            default_font = pygame.font.Font(None, size)
            return default_font
    except:
        pass

    # 如果所有方法都失败，返回None（调用代码需要处理这种情况）
    return None
