# -*- coding: utf-8 -*-
"""
网页游戏中心 - Flask 主应用
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, send_file, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from backend.database.db import db, User, Game, GameRecord, Score, Achievement, GameSetting
from backend.routes.auth import auth_bp
from backend.routes.games import games_bp
from backend.routes.scores import scores_bp
from backend.routes.pygame_games import pygame_bp
from backend.routes.settings import settings_bp
from backend.services.game_scanner import GameScanner
from backend.services.pygame_launcher import PygameLauncherService
from config import config

def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # 获取项目根目录
    base_dir = Path(__file__).parent
    
    app = Flask(
        __name__,
        static_folder=str(base_dir / 'frontend'),
        static_url_path='/static'
    )
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    CORS(app)
    JWTManager(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(scores_bp)
    app.register_blueprint(pygame_bp)
    app.register_blueprint(settings_bp)

    # 初始化 Pygame 服务
    scanner = GameScanner(
        gamecenter_root=app.config.get('GAMECENTER_ROOT', base_dir.parent),
        exclude_dirs=app.config.get('PYGAME_SCAN_EXCLUDE', []),
        pygame_games_config=app.config.get('PYGAME_GAMES', []),
    )
    launcher = PygameLauncherService(scanner)
    app.config['GAME_SCANNER'] = scanner
    app.config['PYGAME_LAUNCHER'] = launcher
    
    # 应用上下文
    with app.app_context():
        # 创建所有数据表
        db.create_all()
        
        # 初始化游戏数据
        init_games_data()
    
    # 前端页面路由 - 提供HTML文件
    @app.route('/', methods=['GET'])
    @app.route('/index.html', methods=['GET'])
    def serve_index():
        """服务首页"""
        try:
            return send_from_directory(app.static_folder, 'index.html')
        except Exception as e:
            return jsonify({'error': f'无法加载首页: {str(e)}'}), 500
    
    @app.route('/login.html', methods=['GET'])
    def serve_login():
        """服务登录页"""
        return send_from_directory(app.static_folder, 'login.html')
    
    @app.route('/game.html', methods=['GET'])
    def serve_game():
        """服务游戏页"""
        return send_from_directory(app.static_folder, 'game.html')
    
    @app.route('/dashboard.html', methods=['GET'])
    def serve_dashboard():
        """服务仪表板页"""
        return send_from_directory(app.static_folder, 'dashboard.html')
    
    @app.route('/leaderboard.html', methods=['GET'])
    def serve_leaderboard():
        """服务排行榜页"""
        return send_from_directory(app.static_folder, 'leaderboard.html')

    @app.route('/settings.html', methods=['GET'])
    def serve_settings():
        """服务设置页"""
        return send_from_directory(app.static_folder, 'settings.html')
    
    # 静态文件路由 - CSS、JS、游戏文件
    @app.route('/css/<path:path>', methods=['GET'])
    def serve_css(path):
        """服务CSS文件"""
        return send_from_directory(os.path.join(app.static_folder, 'css'), path)
    
    @app.route('/js/<path:path>', methods=['GET'])
    def serve_js(path):
        """服务JavaScript文件"""
        return send_from_directory(os.path.join(app.static_folder, 'js'), path)
    
    @app.route('/games/<path:path>', methods=['GET'])
    def serve_games(path):
        """服务游戏文件"""
        return send_from_directory(os.path.join(app.static_folder, 'games'), path)
    
    @app.route('/assets/<path:path>', methods=['GET'])
    def serve_assets(path):
        """服务资源文件"""
        return send_from_directory(os.path.join(app.static_folder, 'assets'), path)
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        # 如果是API请求，返回JSON
        if request.path.startswith('/api/'):
            return jsonify({'error': '请求的资源不存在'}), 404
        # 否则返回首页（前端路由）
        try:
            return send_from_directory(app.static_folder, 'index.html')
        except:
            return jsonify({'error': '请求的资源不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500
    
    # 健康检查端点
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Web Game Center API'
        }), 200
    
    # 首页端点
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'service': 'Web Game Center API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'games': '/api/games',
                'scores': '/api/scores',
                'health': '/api/health'
            }
        }), 200
    
    return app


def init_games_data():
    """初始化游戏数据"""
    from flask import current_app
    
    games_config = current_app.config.get('GAMES_CONFIG', {})
    
    for category_id, category_data in games_config.items():
        for game_info in category_data.get('games', []):
            # 检查游戏是否已存在
            if not Game.query.filter_by(game_id=game_info['id']).first():
                game = Game(
                    game_id=game_info['id'],
                    name=game_info['name'],
                    category=category_id,
                    description=game_info['description'],
                    difficulty=game_info['difficulty'],
                    icon=game_info['icon']
                )
                db.session.add(game)
    
    db.session.commit()

    # 初始化 Pygame 游戏数据
    pygame_games = current_app.config.get('PYGAME_GAMES', [])
    for pg in pygame_games:
        if not Game.query.filter_by(game_id=pg['id']).first():
            game = Game(
                game_id=pg['id'],
                name=pg['name'],
                category=pg.get('category', 'other'),
                description=pg.get('description', ''),
                difficulty=pg.get('difficulty', 'medium'),
                icon=pg.get('icon', 'fas fa-gamepad'),
                game_type='pygame',
            )
            db.session.add(game)

    db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
