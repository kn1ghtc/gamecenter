# -*- coding: utf-8 -*-
"""
pytest 配置文件
"""
import pytest
import os
import sys
from pathlib import Path

# 添加项目路径到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from backend.database.db import db, User, Game
from datetime import datetime


@pytest.fixture(scope='session')
def app():
    """创建测试应用"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建测试命令行运行器"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_games(app):
    """创建测试游戏"""
    games_data = [
        {'game_id': 'flappy_bird', 'name': '飞鸟', 'category': 'casual', 'difficulty': 'hard', 'icon': 'fas fa-dove'},
        {'game_id': 'snake', 'name': '贪吃蛇', 'category': 'arcade', 'difficulty': 'easy', 'icon': 'fas fa-angle-right'},
        {'game_id': '2048', 'name': '2048', 'category': 'puzzle', 'difficulty': 'easy', 'icon': 'fas fa-th'},
        {'game_id': 'tetris', 'name': '俄罗斯方块', 'category': 'puzzle', 'difficulty': 'medium', 'icon': 'fas fa-th'},
        {'game_id': 'minesweeper', 'name': '扫雷', 'category': 'puzzle', 'difficulty': 'medium', 'icon': 'fas fa-bomb'},
    ]
    
    with app.app_context():
        games = []
        for game_data in games_data:
            game = Game(**game_data)
            db.session.add(game)
            games.append(game)
        db.session.commit()
        return games
