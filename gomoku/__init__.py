"""五子棋游戏包
Gomoku (Five in a Row) Game Package

现代化五子棋游戏，包含智能AI、优雅UI、完整游戏功能。
"""

from gamecenter.gomoku.game_logic import Board, GameManager, GameState, Player, create_game
from gamecenter.gomoku.ai_engine import OptimizedAIController, create_optimized_ai
from gamecenter.gomoku.config.config_loader import get_difficulty_config, DifficultyConfig
from gamecenter.gomoku.main import run_game

__version__ = "1.0.0"
__author__ = "kn1ghtc"

__all__ = [
    # 游戏逻辑
    'Board',
    'GameManager',
    'GameState',
    'Player',
    'create_game',
    
    # AI引擎
    'OptimizedAIController',
    'create_optimized_ai',
    
    # 配置系统
    'get_difficulty_config',
    'DifficultyConfig',
    
    # 主程序
    'run_game',
]
