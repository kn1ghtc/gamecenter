# -*- coding: utf-8 -*-
"""
Pygame 路由 API 测试 — 验证 Pygame 游戏 API 端点的功能和安全性

使用 Flask test client 测试端点响应、白名单校验和状态管理。
"""
import pytest
import sys
import os

# 确保 webGameCenter 目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


@pytest.fixture
def app(tmp_path):
    """创建测试 Flask 应用

    构建模拟游戏目录并配置测试专用 app 实例。

    Returns:
        Flask app 实例
    """
    # 创建模拟 gamecenter 目录
    gc_root = tmp_path / 'gamecenter'
    gc_root.mkdir()
    for name in ['chess', 'tetris']:
        game_dir = gc_root / name
        game_dir.mkdir()
        (game_dir / 'main.py').write_text('# entry', encoding='utf-8')

    app = create_app('testing')

    # 覆盖 scanner 配置使用模拟目录
    from backend.services.game_scanner import GameScanner
    from backend.services.pygame_launcher import PygameLauncherService

    scanner = GameScanner(
        gc_root,
        exclude_dirs=['webGameCenter', '__pycache__'],
        pygame_games_config=app.config.get('PYGAME_GAMES', []),
    )
    launcher = PygameLauncherService(scanner)
    app.config['GAME_SCANNER'] = scanner
    app.config['PYGAME_LAUNCHER'] = launcher

    return app


@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


class TestPygameGamesEndpoint:
    """GET /api/pygame/games 测试"""

    def test_list_games_returns_200(self, client):
        """验证游戏列表返回 200"""
        resp = client.get('/api/pygame/games')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'games' in data
        assert data['total'] >= 2

    def test_list_games_contains_expected(self, client):
        """验证返回结果包含预期游戏"""
        resp = client.get('/api/pygame/games')
        data = resp.get_json()
        ids = {g['id'] for g in data['games']}
        assert 'chess' in ids
        assert 'tetris' in ids


class TestPygameGameDetail:
    """GET /api/pygame/games/<game_id> 测试"""

    def test_existing_game(self, client):
        """验证获取已有游戏详情"""
        resp = client.get('/api/pygame/games/chess')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == 'chess'

    def test_nonexistent_game(self, client):
        """验证获取不存在的游戏返回 404"""
        resp = client.get('/api/pygame/games/nonexistent')
        assert resp.status_code == 404


class TestPygameLaunch:
    """POST /api/pygame/launch/<game_id> 测试"""

    def test_launch_invalid_game_returns_403(self, client):
        """安全测试: 非白名单 game_id 返回 403 或 404"""
        resp = client.post('/api/pygame/launch/../../etc/passwd')
        assert resp.status_code in (403, 404)

    def test_launch_nonexistent_returns_403(self, client):
        """安全测试: 不存在的 game_id 返回 403"""
        resp = client.post('/api/pygame/launch/fake_game')
        assert resp.status_code == 403


class TestPygameStatus:
    """GET /api/pygame/status 测试"""

    def test_status_no_game_running(self, client):
        """验证无游戏运行时状态"""
        resp = client.get('/api/pygame/status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['running'] is False


class TestPygameStop:
    """POST /api/pygame/stop 测试"""

    def test_stop_no_game_running(self, client):
        """验证无游戏运行时停止操作"""
        resp = client.post('/api/pygame/stop')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'


class TestPygameRefresh:
    """POST /api/pygame/refresh 测试"""

    def test_refresh_returns_games(self, client):
        """验证刷新缓存返回游戏列表"""
        resp = client.post('/api/pygame/refresh')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['refreshed'] is True
        assert data['total'] >= 2


class TestWhitelistSecurity:
    """白名单安全校验测试"""

    def test_path_traversal_blocked(self, client):
        """验证路径穿越攻击被阻止"""
        malicious_ids = [
            '../etc/passwd',
            '..\\windows\\system32',
            'chess/../../../etc/shadow',
            '; rm -rf /',
            'chess; echo hacked',
        ]
        for mid in malicious_ids:
            resp = client.post(f'/api/pygame/launch/{mid}')
            assert resp.status_code in (403, 404), \
                f"Expected 403/404 for '{mid}', got {resp.status_code}"
