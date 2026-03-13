# -*- coding: utf-8 -*-
"""
Pygame 游戏启动服务 — 管理本地 Pygame 游戏进程生命周期

通过 subprocess.Popen 以非阻塞方式启动 Pygame 游戏，限制同时仅运行 1 个进程。
游戏进程启动/结束事件记录到数据库。game_id 必须经白名单校验后才能启动。
"""
import logging
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PygameLauncherService:
    """Pygame 游戏进程管理器

    管理单个 Pygame 游戏进程的启动、状态查询和停止。
    使用 GameScanner 提供的白名单校验 game_id 合法性。

    Args:
        game_scanner: GameScanner 实例，用于获取游戏元数据与白名单校验
        db_session_factory: 可选的数据库会话工厂（用于记录游戏事件）
    """

    def __init__(self, game_scanner, db_session_factory=None) -> None:
        self._scanner = game_scanner
        self._db_session_factory = db_session_factory
        self._current_process: Optional[subprocess.Popen] = None
        self._current_game_id: Optional[str] = None
        self._start_time: Optional[float] = None

    def launch_game(self, game_id: str) -> Dict:
        """启动指定的 Pygame 游戏

        启动前会校验 game_id 是否在扫描白名单中，并确保没有其他游戏正在运行。

        Args:
            game_id: 游戏标识符（必须存在于扫描结果白名单中）

        Returns:
            包含 status, message, game_id 等字段的结果字典

        Raises:
            ValueError: game_id 未通过白名单校验
        """
        # 白名单校验
        valid_ids = self._scanner.get_valid_game_ids()
        if game_id not in valid_ids:
            logger.warning("非法 game_id 被拒绝: %s", game_id)
            raise ValueError(f"无效的游戏 ID: {game_id}")

        # 检查是否有游戏正在运行
        self._cleanup_finished()
        if self._current_process is not None:
            return {
                'status': 'error',
                'message': f'已有游戏正在运行: {self._current_game_id}',
                'running_game': self._current_game_id,
            }

        # 获取游戏元数据
        game_meta = self._scanner.get_game_by_id(game_id)
        if game_meta is None:
            return {'status': 'error', 'message': f'游戏 {game_id} 未找到'}

        game_path = Path(game_meta['path']) / 'main.py'
        if not game_path.is_file():
            return {'status': 'error', 'message': f'游戏入口不存在: {game_path}'}

        # 启动进程
        try:
            self._current_process = subprocess.Popen(
                [sys.executable, str(game_path)],
                cwd=str(Path(game_meta['path'])),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._current_game_id = game_id
            self._start_time = time.monotonic()

            logger.info(
                "Pygame 游戏已启动: %s (PID=%d)",
                game_id, self._current_process.pid
            )

            self._record_game_event(game_id, 'started')

            return {
                'status': 'launched',
                'message': f'游戏 {game_meta["name"]} 已启动',
                'game_id': game_id,
                'game_name': game_meta['name'],
                'pid': self._current_process.pid,
            }
        except OSError as exc:
            logger.error("启动游戏失败: %s — %s", game_id, exc)
            self._current_process = None
            self._current_game_id = None
            self._start_time = None
            return {'status': 'error', 'message': f'启动失败: {exc}'}

    def get_status(self) -> Dict:
        """获取当前运行中的游戏状态

        Returns:
            包含 running (bool)、game_id、elapsed 等字段的状态字典
        """
        self._cleanup_finished()

        if self._current_process is None:
            return {'running': False}

        elapsed = time.monotonic() - self._start_time if self._start_time else 0
        game_meta = self._scanner.get_game_by_id(self._current_game_id) or {}

        return {
            'running': True,
            'game_id': self._current_game_id,
            'game_name': game_meta.get('name', self._current_game_id),
            'pid': self._current_process.pid,
            'elapsed_seconds': round(elapsed, 1),
        }

    def stop_game(self) -> Dict:
        """停止当前正在运行的游戏进程

        Returns:
            操作结果字典
        """
        self._cleanup_finished()

        if self._current_process is None:
            return {'status': 'ok', 'message': '没有正在运行的游戏'}

        game_id = self._current_game_id
        pid = self._current_process.pid

        try:
            self._current_process.terminate()
            try:
                self._current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._current_process.kill()
                self._current_process.wait(timeout=3)
            logger.info("Pygame 游戏已停止: %s (PID=%d)", game_id, pid)
        except OSError as exc:
            logger.error("停止游戏进程失败: %s — %s", game_id, exc)

        self._record_game_event(game_id, 'stopped')
        self._current_process = None
        self._current_game_id = None
        self._start_time = None

        return {
            'status': 'stopped',
            'message': f'游戏 {game_id} 已停止',
            'game_id': game_id,
        }

    def _cleanup_finished(self) -> None:
        """检查当前进程是否已自行结束，若已结束则清理状态"""
        if self._current_process is None:
            return
        returncode = self._current_process.poll()
        if returncode is not None:
            logger.info(
                "Pygame 游戏已自行结束: %s (exit=%s)",
                self._current_game_id, returncode,
            )
            self._record_game_event(self._current_game_id, 'finished')
            self._current_process = None
            self._current_game_id = None
            self._start_time = None

    def _record_game_event(self, game_id: str, event: str) -> None:
        """记录游戏启动/停止事件到数据库（如果可用）

        Args:
            game_id: 游戏标识符
            event: 事件类型 ('started', 'stopped', 'finished')
        """
        try:
            from backend.database.db import db, Game
            game = Game.query.filter_by(game_id=game_id).first()
            if game and event == 'started':
                game.total_plays += 1
                db.session.commit()
                logger.debug("已更新游戏 %s 的游玩次数", game_id)
        except Exception as exc:
            logger.debug("记录游戏事件失败 (非致命): %s", exc)
