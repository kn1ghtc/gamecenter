# -*- coding: utf-8 -*-
"""
积分排行相关API路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database.db import db, Score, User, Game, GameRecord
from sqlalchemy import desc, func

scores_bp = Blueprint('scores', __name__, url_prefix='/api/scores')


@scores_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """获取全局积分排行榜"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # 获取用户总分排行
        leaderboard = db.session.query(
            User.id,
            User.username,
            User.avatar,
            User.total_score,
            func.count(GameRecord.id).label('games_played')
        ).outerjoin(GameRecord).group_by(User.id).order_by(
            desc(User.total_score)
        ).limit(limit).all()
        
        result = []
        for rank, (user_id, username, avatar, total_score, games_played) in enumerate(leaderboard, 1):
            result.append({
                'rank': rank,
                'user_id': user_id,
                'username': username,
                'avatar': avatar,
                'total_score': total_score,
                'games_played': games_played or 0
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scores_bp.route('/game/<game_id>', methods=['GET'])
def get_game_leaderboard(game_id):
    """获取指定游戏的积分排行"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        game = Game.query.filter_by(game_id=game_id).first()
        
        if not game:
            return jsonify({'error': '游戏不存在'}), 404
        
        # 获取该游戏的最高分排行
        records = db.session.query(
            GameRecord.user_id,
            User.username,
            User.avatar,
            func.max(GameRecord.score).label('max_score'),
            func.count(GameRecord.id).label('play_count'),
            func.avg(GameRecord.score).label('avg_score')
        ).join(User).filter(
            GameRecord.game_id == game.id
        ).group_by(
            GameRecord.user_id
        ).order_by(
            desc(func.max(GameRecord.score))
        ).limit(limit).all()
        
        result = []
        for rank, (user_id, username, avatar, max_score, play_count, avg_score) in enumerate(records, 1):
            result.append({
                'rank': rank,
                'user_id': user_id,
                'username': username,
                'avatar': avatar,
                'max_score': max_score,
                'avg_score': float(avg_score) if avg_score else 0,
                'play_count': play_count
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scores_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """获取用户的统计数据"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 获取用户游戏统计
        stats = db.session.query(
            func.count(GameRecord.id).label('total_games'),
            func.sum(GameRecord.score).label('total_score'),
            func.avg(GameRecord.score).label('avg_score'),
            func.sum(GameRecord.time_played).label('total_time'),
            func.max(GameRecord.score).label('max_score')
        ).filter(
            GameRecord.user_id == user_id
        ).first()
        
        # 获取用户的最佳游戏
        best_games = db.session.query(
            Game.name,
            Game.game_id,
            func.max(GameRecord.score).label('max_score'),
            func.count(GameRecord.id).label('play_count')
        ).join(GameRecord).filter(
            GameRecord.user_id == user_id
        ).group_by(
            Game.id
        ).order_by(
            desc(func.max(GameRecord.score))
        ).limit(5).all()
        
        return jsonify({
            'user': user.to_dict(),
            'stats': {
                'total_games': stats.total_games or 0,
                'total_score': stats.total_score or 0,
                'avg_score': float(stats.avg_score) if stats.avg_score else 0,
                'total_time': stats.total_time or 0,
                'max_score': stats.max_score or 0
            },
            'best_games': [
                {
                    'name': name,
                    'game_id': game_id,
                    'max_score': max_score,
                    'play_count': play_count
                }
                for name, game_id, max_score, play_count in best_games
            ]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scores_bp.route('/user/rank', methods=['GET'])
@jwt_required()
def get_user_rank():
    """获取当前用户的排名"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 计算用户的排名
        rank = db.session.query(func.count(User.id)).filter(
            User.total_score > user.total_score
        ).scalar() + 1
        
        # 获取用户的百分位排名
        total_users = User.query.count()
        percentile = ((total_users - rank + 1) / total_users * 100) if total_users > 0 else 0
        
        return jsonify({
            'user_id': user_id,
            'username': user.username,
            'total_score': user.total_score,
            'rank': rank,
            'total_users': total_users,
            'percentile': round(percentile, 2)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
