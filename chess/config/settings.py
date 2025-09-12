# 国际象棋项目配置
import os

# 游戏配置
BOARD_SIZE = 8
SQUARE_SIZE = 80
WINDOW_WIDTH = BOARD_SIZE * SQUARE_SIZE + 400  # 预留侧边栏空间
WINDOW_HEIGHT = BOARD_SIZE * SQUARE_SIZE + 100
FPS = 60

# 颜色配置 (RGB)
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'LIGHT_SQUARE': (240, 217, 181),
    'DARK_SQUARE': (181, 136, 99),
    'HIGHLIGHT': (255, 255, 0, 128),
    'MOVE_HINT': (0, 255, 0, 100),
    'DANGER': (255, 0, 0, 100),
    'BACKGROUND': (50, 50, 50),
    'UI_PANEL': (70, 70, 70),
    'TEXT': (255, 255, 255),
    'BUTTON': (100, 100, 100),
    'BUTTON_HOVER': (130, 130, 130)
}

# AI 配置
AI_LEVELS = {
    'EASY': {
        'type': 'minimax',
        'depth': 5,
        'time_limit': 1.0
    },
    'MEDIUM': {
        'type': 'neural_network',
        # 统一到训练导出的默认模型路径（由 PATHS['models'] 决定）
        'model_path': None,  # 启动时用 PATHS['models']/ml_ai_model.pth 填充
        'time_limit': 2.0
    },
    'HARD': {
        'type': 'gpt',
        'model': 'gpt-4o-mini',
        'time_limit': 5.0
    }
}

# 数据库配置
import os as _os
_current_dir = _os.path.dirname(_os.path.abspath(__file__))
_chess_dir = _os.path.dirname(_current_dir)
# 仓库根目录（.. 上溯一层到 gamecenter，再上溯到仓库根）
_repo_root = _os.path.dirname(_os.path.dirname(_chess_dir))
DATABASE_PATH = _os.path.join(_chess_dir, 'data', 'chess_games.db')

# OpenAI 配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 训练配置
TRAINING_CONFIG = {
    'batch_size': 64,
    'learning_rate': 0.001,
    'epochs': 100,
    'save_interval': 10,
    # 延后到使用处根据 torch.cuda.is_available() 决定
    'device': 'auto'
}

# 文件路径
PATHS = {
    # 统一为绝对路径，避免依赖进程当前目录
    'models': _os.path.join(_chess_dir, 'training', 'models'),
    'data': _os.path.join(_chess_dir, 'data'),
    # 修正为当前 chess 模块下的 assets 目录（实际资源所在路径）
    'assets': _os.path.join(_chess_dir, 'assets')
}

# 确保目录存在
for path in PATHS.values():
    os.makedirs(path, exist_ok=True)
# 确保数据库目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# 回填 MEDIUM 模型路径（若未显式指定）
if AI_LEVELS['MEDIUM'].get('model_path') in (None, ''):
    AI_LEVELS['MEDIUM']['model_path'] = os.path.join(PATHS['models'], 'ml_ai_model.pth')
