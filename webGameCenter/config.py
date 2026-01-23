# -*- coding: utf-8 -*-
"""
配置文件
"""
import os
from datetime import timedelta

class Config:
    """基础配置"""
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///game_center.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 游戏配置 (JS游戏 - 在浏览器中运行)
    # 注意: kof, tetris, tankbattle 已移至pygame版本 (gamecenter目录)
    GAMES_CONFIG = {
        'action': {
            'name': '动作游戏',
            'icon': 'fas fa-gamepad',
            'description': '刺激的动作类游戏',
            'games': [
                {
                    'id': 'contra',
                    'name': '魂斗罗',
                    'description': '经典的横版射击游戏',
                    'difficulty': 'medium',
                    'icon': 'fas fa-gun'
                }
            ]
        },
        'shooting': {
            'name': '射击游戏',
            'icon': 'fas fa-crosshairs',
            'description': '紧张刺激的射击游戏',
            'games': [
                {
                    'id': 'space_shooter',
                    'name': '太空射击',
                    'description': '纵版射击游戏',
                    'difficulty': 'easy',
                    'icon': 'fas fa-rocket'
                }
            ]
        },
        'puzzle': {
            'name': '益智游戏',
            'icon': 'fas fa-puzzle-piece',
            'description': '考验智慧的益智游戏',
            'games': [
                {
                    'id': '2048',
                    'name': '2048',
                    'description': '经典的数字合并游戏',
                    'difficulty': 'easy',
                    'icon': 'fas fa-th'
                },
                {
                    'id': 'sokoban',
                    'name': '推箱子',
                    'description': '经典的益智解谜游戏',
                    'difficulty': 'medium',
                    'icon': 'fas fa-box'
                }
            ]
        },
        'arcade': {
            'name': '街机游戏',
            'icon': 'fas fa-coins',
            'description': '怀旧的街机游戏',
            'games': [
                {
                    'id': 'pacman',
                    'name': '吃豆人',
                    'description': '经典的吃豆人游戏',
                    'difficulty': 'easy',
                    'icon': 'fas fa-circle'
                },
                {
                    'id': 'snake',
                    'name': '贪吃蛇',
                    'description': '经典的贪吃蛇游戏',
                    'difficulty': 'easy',
                    'icon': 'fas fa-angle-right'
                }
            ]
        },
        'casual': {
            'name': '休闲游戏',
            'icon': 'fas fa-star',
            'description': '轻松休闲的小游戏',
            'games': [
                {
                    'id': 'flappy_bird',
                    'name': '飞鸟',
                    'description': '考验反应的飞行游戏',
                    'difficulty': 'hard',
                    'icon': 'fas fa-dove'
                },
                {
                    'id': 'dinosaur',
                    'name': '恐龙跑酷',
                    'description': 'Chrome离线恐龙游戏',
                    'difficulty': 'easy',
                    'icon': 'fas fa-lizard'
                }
            ]
        }
    }


    # Pygame游戏配置 (本地运行)
    PYGAME_GAMES = [
        {
            'id': 'chess',
            'name': '中国象棋',
            'description': 'AI对弈中国象棋，支持语音输入',
            'category': 'strategy',
            'icon': 'fas fa-chess',
            'difficulty': 'medium',
            'module': 'gamecenter.chess'
        },
        {
            'id': 'gomoku',
            'name': '五子棋',
            'description': '人机对战五子棋',
            'category': 'strategy',
            'icon': 'fas fa-circle',
            'difficulty': 'easy',
            'module': 'gamecenter.gomoku'
        },
        {
            'id': 'militaryChess',
            'name': '军旗',
            'description': '双人对战军棋游戏',
            'category': 'strategy',
            'icon': 'fas fa-flag',
            'difficulty': 'hard',
            'module': 'gamecenter.militaryChess'
        },
        {
            'id': 'tankBattle',
            'name': '坦克大战',
            'description': '经典坦克对战，支持AI训练',
            'category': 'shooting',
            'icon': 'fas fa-crosshairs',
            'difficulty': 'medium',
            'module': 'gamecenter.tankBattle'
        },
        {
            'id': 'tetris',
            'name': '俄罗斯方块',
            'description': '经典益智游戏',
            'category': 'puzzle',
            'icon': 'fas fa-th-large',
            'difficulty': 'easy',
            'module': 'gamecenter.tetris'
        },
        {
            'id': 'superMario',
            'name': '超级玛丽',
            'description': '30关平台跳跃游戏',
            'category': 'action',
            'icon': 'fas fa-running',
            'difficulty': 'medium',
            'module': 'gamecenter.superMario'
        },
        {
            'id': 'deltaOperation',
            'name': '三角洲行动',
            'description': '12关闯关枪战游戏',
            'category': 'shooting',
            'icon': 'fas fa-gun',
            'difficulty': 'hard',
            'module': 'gamecenter.deltaOperation'
        },
        {
            'id': 'streetBattle',
            'name': '街头霸王',
            'description': '2.5D/3D格斗游戏',
            'category': 'action',
            'icon': 'fas fa-fist-raised',
            'difficulty': 'hard',
            'module': 'gamecenter.streetBattle'
        },
        {
            'id': 'stickman_game',
            'name': '火柴人格斗',
            'description': '火柴人动作游戏',
            'category': 'action',
            'icon': 'fas fa-user',
            'difficulty': 'easy',
            'module': 'gamecenter.stickman_game'
        },
        {
            'id': 'Eco_grassland',
            'name': '生态草原',
            'description': '生态模拟经营游戏',
            'category': 'simulation',
            'icon': 'fas fa-leaf',
            'difficulty': 'medium',
            'module': 'gamecenter.Eco_grassland'
        },
        {
            'id': 'alien_invasion',
            'name': '外星人入侵',
            'description': '太空射击游戏',
            'category': 'shooting',
            'icon': 'fas fa-rocket',
            'difficulty': 'easy',
            'module': 'gamecenter.alien_invasion'
        }
    ]


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
