# -*- coding: utf-8 -*-
"""
游戏相关API路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database.db import db, Game, GameRecord, User
from datetime import datetime
import json

games_bp = Blueprint('games', __name__, url_prefix='/api/games')


@games_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取游戏分类列表"""
    try:
        categories = []
        games_config = current_app.config.get('GAMES_CONFIG', {})
        
        for category_id, category_data in games_config.items():
            categories.append({
                'id': category_id,
                'name': category_data['name'],
                'icon': category_data['icon'],
                'description': category_data['description'],
                'game_count': len(category_data.get('games', []))
            })
        
        return jsonify(categories), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@games_bp.route('/category/<category_id>', methods=['GET'])
def get_category_games(category_id):
    """获取指定分类的游戏列表"""
    try:
        games_config = current_app.config.get('GAMES_CONFIG', {})
        
        if category_id not in games_config:
            return jsonify({'error': '分类不存在'}), 404
        
        category = games_config[category_id]
        games = category.get('games', [])
        
        # 获取游戏的统计信息
        enriched_games = []
        for game_info in games:
            game = Game.query.filter_by(game_id=game_info['id']).first()
            if game:
                game_data = game.to_dict()
            else:
                game_data = {
                    'id': None,
                    'game_id': game_info['id'],
                    'name': game_info['name'],
                    'category': category_id,
                    'description': game_info['description'],
                    'difficulty': game_info['difficulty'],
                    'icon': game_info['icon'],
                    'total_plays': 0,
                    'average_score': 0.0,
                    'created_at': datetime.utcnow().isoformat()
                }
            enriched_games.append(game_data)
        
        return jsonify({
            'category_id': category_id,
            'category_name': category['name'],
            'games': enriched_games
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@games_bp.route('/list', methods=['GET'])
def get_all_games():
    """获取所有游戏列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        games = Game.query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'total': games.total,
            'pages': games.pages,
            'current_page': page,
            'games': [game.to_dict() for game in games.items]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@games_bp.route('/<game_id>', methods=['GET'])
def get_game(game_id):
    """获取游戏详细信息"""
    try:
        game = Game.query.filter_by(game_id=game_id).first()
        
        if not game:
            # 从配置中查找游戏
            games_config = current_app.config.get('GAMES_CONFIG', {})
            for category_id, category_data in games_config.items():
                for game_info in category_data.get('games', []):
                    if game_info['id'] == game_id:
                        return jsonify({
                            'game_id': game_info['id'],
                            'name': game_info['name'],
                            'category': category_id,
                            'description': game_info['description'],
                            'difficulty': game_info['difficulty'],
                            'icon': game_info['icon'],
                            'total_plays': 0,
                            'average_score': 0.0
                        }), 200
            
            return jsonify({'error': '游戏不存在'}), 404
        
        return jsonify(game.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@games_bp.route('/record', methods=['POST'])
@jwt_required()
def save_game_record():
    """保存游戏记录"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        data = request.get_json()
        game_id_str = data.get('game_id')
        score = data.get('score', 0)
        time_played = data.get('time_played', 0)
        level = data.get('level', 1)
        status = data.get('status', 'completed')
        progress = data.get('progress', 0.0)
        game_state = data.get('game_state', {})
        
        # 获取或创建游戏
        game = Game.query.filter_by(game_id=game_id_str).first()
        
        if not game:
            # 从配置中获取游戏信息
            games_config = current_app.config.get('GAMES_CONFIG', {})
            game_info = None
            category = None
            
            for cat_id, cat_data in games_config.items():
                for g in cat_data.get('games', []):
                    if g['id'] == game_id_str:
                        game_info = g
                        category = cat_id
                        break
                if game_info:
                    break
            
            if not game_info:
                return jsonify({'error': '游戏不存在'}), 404
            
            game = Game(
                game_id=game_id_str,
                name=game_info['name'],
                category=category,
                description=game_info['description'],
                difficulty=game_info['difficulty'],
                icon=game_info['icon']
            )
            db.session.add(game)
            db.session.flush()
        
        # 创建游戏记录
        record = GameRecord(
            user_id=user_id,
            game_id=game.id,
            score=score,
            time_played=time_played,
            level=level,
            status=status,
            progress=progress,
            game_state=json.dumps(game_state)
        )
        
        db.session.add(record)
        
        # 更新用户总分
        user.total_score += score
        
        # 更新游戏统计
        game.total_plays += 1
        if game.average_score == 0:
            game.average_score = score
        else:
            game.average_score = (game.average_score * (game.total_plays - 1) + score) / game.total_plays
        
        db.session.commit()
        
        return jsonify({
            'message': '游戏记录保存成功',
            'record': record.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@games_bp.route('/records', methods=['GET'])
@jwt_required()
def get_game_records():
    """获取用户的游戏记录"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        game_id = request.args.get('game_id', None)
        
        query = GameRecord.query.filter_by(user_id=user_id)
        
        if game_id:
            game = Game.query.filter_by(game_id=game_id).first()
            if game:
                query = query.filter_by(game_id=game.id)
        
        records = query.order_by(GameRecord.created_at.desc()).paginate(
            page=page, per_page=per_page
        )
        
        return jsonify({
            'total': records.total,
            'pages': records.pages,
            'current_page': page,
            'records': [record.to_dict() for record in records.items]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
