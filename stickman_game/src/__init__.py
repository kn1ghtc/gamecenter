#!/usr/bin/env python3
"""
简化版火柴人动作冒险游戏
src包初始化文件
"""

__version__ = "3.0.0"
__author__ = "GitHub Copilot"
__description__ = "简化版火柴人动作冒险游戏 - 单人模式、方向键控制、30关卡"

# 导出主要类和函数
from .config import *
from .game import Game
from .player import Player
from .entities import Enemy, Explosion
from .level_platform_system import LevelPlatformSystem
from .core import InputManager

__all__ = [
    'Game', 
    'Player',
    'Enemy',
    'Explosion',
    'LevelPlatformSystem',
    'InputManager'
]
