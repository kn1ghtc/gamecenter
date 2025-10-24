# -*- coding: utf-8 -*-
"""
数据库初始化
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default='')
    total_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    games_played = db.relationship('GameRecord', backref='player', lazy=True, cascade='all, delete-orphan')
    scores = db.relationship('Score', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'total_score': self.total_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Game(db.Model):
    """游戏模型"""
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')
    icon = db.Column(db.String(100))
    total_plays = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    records = db.relationship('GameRecord', backref='game', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'game_id': self.game_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'difficulty': self.difficulty,
            'icon': self.icon,
            'total_plays': self.total_plays,
            'average_score': self.average_score,
            'created_at': self.created_at.isoformat()
        }


class GameRecord(db.Model):
    """游戏记录模型"""
    __tablename__ = 'game_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    score = db.Column(db.Integer, default=0)
    time_played = db.Column(db.Integer, default=0)  # 游戏时长(秒)
    level = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='completed')  # completed, failed, quit
    progress = db.Column(db.Float, default=0.0)  # 游戏进度百分比
    game_state = db.Column(db.Text, default='{}')  # JSON格式的游戏状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'score': self.score,
            'time_played': self.time_played,
            'level': self.level,
            'status': self.status,
            'progress': self.progress,
            'game_state': json.loads(self.game_state) if self.game_state else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Score(db.Model):
    """积分排行榜模型"""
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.String(50), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'score': self.score,
            'rank': self.rank,
            'created_at': self.created_at.isoformat()
        }


class Achievement(db.Model):
    """成就模型"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    achievement_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'unlocked_at': self.unlocked_at.isoformat()
        }
