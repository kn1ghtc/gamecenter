# -*- coding: utf-8 -*-
"""
游戏设置 API 路由 — 全局及游戏级别设置的读写接口

蓝图前缀: /api/settings
"""
import logging
from flask import Blueprint, request, jsonify
from backend.database.db import db, GameSetting

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_bp.route('', methods=['GET'])
def get_global_settings():
    """获取全局设置列表

    Returns:
        JSON 字典，键为 setting_key，值为 setting_value
    """
    try:
        settings = GameSetting.query.filter_by(game_id=None).all()
        result = {s.setting_key: s.setting_value for s in settings}
        return jsonify(result), 200
    except Exception as exc:
        logger.error("获取全局设置失败: %s", exc)
        return jsonify({'error': '获取设置失败'}), 500


@settings_bp.route('', methods=['PUT'])
def update_global_settings():
    """批量更新全局设置

    请求体为 JSON 字典: {"key1": "value1", "key2": "value2"}

    Returns:
        更新结果 JSON
    """
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': '请求体必须为 JSON 字典'}), 400

        for key, value in data.items():
            setting = GameSetting.query.filter_by(game_id=None, setting_key=key).first()
            if setting:
                setting.setting_value = str(value)
            else:
                setting = GameSetting(
                    game_id=None,
                    setting_key=key,
                    setting_value=str(value),
                )
                db.session.add(setting)

        db.session.commit()
        logger.info("全局设置已更新: %d 项", len(data))
        return jsonify({'message': '设置已更新', 'updated': len(data)}), 200
    except Exception as exc:
        db.session.rollback()
        logger.error("更新全局设置失败: %s", exc)
        return jsonify({'error': '更新设置失败'}), 500


@settings_bp.route('/game/<game_id>', methods=['GET'])
def get_game_settings(game_id: str):
    """获取指定游戏的专属设置

    Args:
        game_id: 游戏标识符

    Returns:
        JSON 字典，键为 setting_key，值为 setting_value
    """
    try:
        settings = GameSetting.query.filter_by(game_id=game_id).all()
        result = {s.setting_key: s.setting_value for s in settings}
        return jsonify(result), 200
    except Exception as exc:
        logger.error("获取游戏设置失败 (%s): %s", game_id, exc)
        return jsonify({'error': '获取游戏设置失败'}), 500


@settings_bp.route('/game/<game_id>', methods=['PUT'])
def update_game_settings(game_id: str):
    """批量更新指定游戏的专属设置

    Args:
        game_id: 游戏标识符

    请求体为 JSON 字典: {"key1": "value1", "key2": "value2"}

    Returns:
        更新结果 JSON
    """
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': '请求体必须为 JSON 字典'}), 400

        for key, value in data.items():
            setting = GameSetting.query.filter_by(
                game_id=game_id, setting_key=key
            ).first()
            if setting:
                setting.setting_value = str(value)
            else:
                setting = GameSetting(
                    game_id=game_id,
                    setting_key=key,
                    setting_value=str(value),
                )
                db.session.add(setting)

        db.session.commit()
        logger.info("游戏 %s 设置已更新: %d 项", game_id, len(data))
        return jsonify({'message': '游戏设置已更新', 'updated': len(data)}), 200
    except Exception as exc:
        db.session.rollback()
        logger.error("更新游戏设置失败 (%s): %s", game_id, exc)
        return jsonify({'error': '更新游戏设置失败'}), 500
