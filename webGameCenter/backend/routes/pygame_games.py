# -*- coding: utf-8 -*-
"""
Pygame 游戏 API 路由 — 提供本地 Pygame 游戏的发现、启动和状态管理接口

蓝图前缀: /api/pygame
"""
import logging
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

pygame_bp = Blueprint('pygame', __name__, url_prefix='/api/pygame')


def _get_scanner():
    """从 app 扩展中获取 GameScanner 实例"""
    return current_app.config['GAME_SCANNER']


def _get_launcher():
    """从 app 扩展中获取 PygameLauncherService 实例"""
    return current_app.config['PYGAME_LAUNCHER']


@pygame_bp.route('/games', methods=['GET'])
def list_pygame_games():
    """获取所有 Pygame 游戏列表

    Returns:
        JSON 列表，每项包含游戏元数据
    """
    try:
        scanner = _get_scanner()
        games = scanner.scan_pygame_games()
        return jsonify({'games': games, 'total': len(games)}), 200
    except Exception as exc:
        logger.error("获取 Pygame 游戏列表失败: %s", exc)
        return jsonify({'error': '获取游戏列表失败'}), 500


@pygame_bp.route('/games/<game_id>', methods=['GET'])
def get_pygame_game(game_id: str):
    """获取单个 Pygame 游戏详情

    Args:
        game_id: 游戏标识符

    Returns:
        游戏元数据 JSON
    """
    try:
        scanner = _get_scanner()
        game = scanner.get_game_by_id(game_id)
        if game is None:
            return jsonify({'error': '游戏不存在'}), 404
        return jsonify(game), 200
    except Exception as exc:
        logger.error("获取 Pygame 游戏详情失败: %s", exc)
        return jsonify({'error': '获取游戏详情失败'}), 500


@pygame_bp.route('/launch/<game_id>', methods=['POST'])
def launch_pygame_game(game_id: str):
    """启动指定的 Pygame 游戏

    game_id 必须存在于扫描白名单中，否则返回 403。

    Args:
        game_id: 游戏标识符

    Returns:
        启动结果 JSON
    """
    try:
        launcher = _get_launcher()
        result = launcher.launch_game(game_id)
        if result['status'] == 'error':
            return jsonify(result), 409
        return jsonify(result), 200
    except ValueError as exc:
        logger.warning("非法启动请求: %s", exc)
        return jsonify({'error': str(exc)}), 403
    except Exception as exc:
        logger.error("启动 Pygame 游戏失败: %s", exc)
        return jsonify({'error': '启动游戏失败'}), 500


@pygame_bp.route('/status', methods=['GET'])
def get_pygame_status():
    """获取当前 Pygame 游戏运行状态

    Returns:
        运行状态 JSON（running, game_id, elapsed_seconds 等）
    """
    try:
        launcher = _get_launcher()
        status = launcher.get_status()
        return jsonify(status), 200
    except Exception as exc:
        logger.error("获取 Pygame 状态失败: %s", exc)
        return jsonify({'error': '获取状态失败'}), 500


@pygame_bp.route('/stop', methods=['POST'])
def stop_pygame_game():
    """停止当前正在运行的 Pygame 游戏

    Returns:
        停止结果 JSON
    """
    try:
        launcher = _get_launcher()
        result = launcher.stop_game()
        return jsonify(result), 200
    except Exception as exc:
        logger.error("停止 Pygame 游戏失败: %s", exc)
        return jsonify({'error': '停止游戏失败'}), 500


@pygame_bp.route('/refresh', methods=['POST'])
def refresh_pygame_cache():
    """刷新 Pygame 游戏扫描缓存

    Returns:
        刷新后的游戏列表 JSON
    """
    try:
        scanner = _get_scanner()
        games = scanner.refresh_cache()
        logger.info("Pygame 游戏缓存已刷新: %d 个游戏", len(games))
        return jsonify({'games': games, 'total': len(games), 'refreshed': True}), 200
    except Exception as exc:
        logger.error("刷新 Pygame 缓存失败: %s", exc)
        return jsonify({'error': '刷新缓存失败'}), 500
