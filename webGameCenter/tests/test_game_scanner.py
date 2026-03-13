# -*- coding: utf-8 -*-
"""
GameScanner 单元测试 — 验证 Pygame 游戏自动扫描功能

测试扫描发现、元数据提取、缓存刷新和目录排除逻辑。
"""
import pytest
from pathlib import Path
from backend.services.game_scanner import GameScanner


@pytest.fixture
def fake_gamecenter(tmp_path):
    """创建模拟 gamecenter 目录结构

    Returns:
        tmp_path: 包含模拟游戏目录的临时路径
    """
    # 合法游戏目录（有 main.py）
    for name in ['chess', 'tetris', 'gomoku']:
        game_dir = tmp_path / name
        game_dir.mkdir()
        (game_dir / 'main.py').write_text('# game entry', encoding='utf-8')
        (game_dir / '__init__.py').write_text('', encoding='utf-8')

    # 不含 main.py 的目录（不应被扫描到）
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs' / 'readme.md').write_text('doc', encoding='utf-8')

    # 排除目录（webGameCenter）
    wgc = tmp_path / 'webGameCenter'
    wgc.mkdir()
    (wgc / 'main.py').write_text('# ignored', encoding='utf-8')

    # 隐藏目录
    hidden = tmp_path / '.git'
    hidden.mkdir()
    (hidden / 'main.py').write_text('# ignored', encoding='utf-8')

    # __pycache__
    pycache = tmp_path / '__pycache__'
    pycache.mkdir()

    return tmp_path


@pytest.fixture
def sample_config():
    """提供 PYGAME_GAMES 配置样本"""
    return [
        {
            'id': 'chess',
            'name': '中国象棋',
            'description': 'AI对弈',
            'category': 'strategy',
            'icon': 'fas fa-chess',
            'difficulty': 'medium',
            'module': 'gamecenter.chess',
        },
        {
            'id': 'tetris',
            'name': '俄罗斯方块',
            'description': '经典益智',
            'category': 'puzzle',
            'icon': 'fas fa-th-large',
            'difficulty': 'easy',
            'module': 'gamecenter.tetris',
        },
    ]


class TestGameScanner:
    """GameScanner 测试套件"""

    def test_scan_finds_valid_games(self, fake_gamecenter):
        """验证扫描到包含 main.py 的目录"""
        scanner = GameScanner(
            fake_gamecenter,
            exclude_dirs=['webGameCenter', '__pycache__', '.git'],
        )
        games = scanner.scan_pygame_games()
        ids = {g['id'] for g in games}
        assert 'chess' in ids
        assert 'tetris' in ids
        assert 'gomoku' in ids
        assert len(games) == 3

    def test_excludes_webgamecenter(self, fake_gamecenter):
        """验证 webGameCenter 被排除"""
        scanner = GameScanner(
            fake_gamecenter,
            exclude_dirs=['webGameCenter'],
        )
        games = scanner.scan_pygame_games()
        ids = {g['id'] for g in games}
        assert 'webGameCenter' not in ids

    def test_excludes_hidden_dirs(self, fake_gamecenter):
        """验证隐藏目录（.开头）被排除"""
        scanner = GameScanner(fake_gamecenter)
        games = scanner.scan_pygame_games()
        ids = {g['id'] for g in games}
        assert '.git' not in ids

    def test_excludes_dirs_without_main_py(self, fake_gamecenter):
        """验证无 main.py 的目录不会被扫描到"""
        scanner = GameScanner(fake_gamecenter)
        games = scanner.scan_pygame_games()
        ids = {g['id'] for g in games}
        assert 'docs' not in ids

    def test_metadata_enrichment(self, fake_gamecenter, sample_config):
        """验证使用 PYGAME_GAMES 配置丰富元数据"""
        scanner = GameScanner(
            fake_gamecenter,
            exclude_dirs=['webGameCenter'],
            pygame_games_config=sample_config,
        )
        games = scanner.scan_pygame_games()
        chess = next(g for g in games if g['id'] == 'chess')
        assert chess['name'] == '中国象棋'
        assert chess['category'] == 'strategy'
        assert chess['game_type'] == 'pygame'

    def test_default_metadata_for_unconfigured(self, fake_gamecenter):
        """验证未配置的游戏使用默认元数据"""
        scanner = GameScanner(
            fake_gamecenter, exclude_dirs=['webGameCenter']
        )
        games = scanner.scan_pygame_games()
        gomoku = next(g for g in games if g['id'] == 'gomoku')
        assert gomoku['name'] == 'gomoku'
        assert gomoku['game_type'] == 'pygame'

    def test_cache_returns_same_result(self, fake_gamecenter):
        """验证缓存生效：两次扫描返回相同结果"""
        scanner = GameScanner(
            fake_gamecenter, exclude_dirs=['webGameCenter']
        )
        first = scanner.scan_pygame_games()
        second = scanner.scan_pygame_games()
        assert first == second

    def test_refresh_cache(self, fake_gamecenter):
        """验证缓存刷新后发现新增游戏"""
        scanner = GameScanner(
            fake_gamecenter, exclude_dirs=['webGameCenter']
        )
        first = scanner.scan_pygame_games()
        assert len(first) == 3

        # 新增一个游戏目录
        new_game = fake_gamecenter / 'newgame'
        new_game.mkdir()
        (new_game / 'main.py').write_text('# new', encoding='utf-8')

        refreshed = scanner.refresh_cache()
        assert len(refreshed) == 4
        assert 'newgame' in {g['id'] for g in refreshed}

    def test_get_game_by_id(self, fake_gamecenter, sample_config):
        """验证按 ID 查询单个游戏"""
        scanner = GameScanner(
            fake_gamecenter,
            exclude_dirs=['webGameCenter'],
            pygame_games_config=sample_config,
        )
        chess = scanner.get_game_by_id('chess')
        assert chess is not None
        assert chess['name'] == '中国象棋'

        missing = scanner.get_game_by_id('nonexistent')
        assert missing is None

    def test_get_valid_game_ids(self, fake_gamecenter):
        """验证白名单 ID 集合"""
        scanner = GameScanner(
            fake_gamecenter, exclude_dirs=['webGameCenter']
        )
        valid = scanner.get_valid_game_ids()
        assert isinstance(valid, set)
        assert 'chess' in valid
        assert 'webGameCenter' not in valid

    def test_nonexistent_root(self, tmp_path):
        """验证根目录不存在时返回空列表"""
        scanner = GameScanner(tmp_path / 'nonexistent')
        games = scanner.scan_pygame_games()
        assert games == []
