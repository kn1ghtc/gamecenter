# -*- coding: utf-8 -*-
"""
游戏扫描服务 — 自动发现 gamecenter/ 目录下的 Pygame 游戏

扫描 gamecenter 根目录，检测包含 main.py 的子目录作为可启动的 Pygame 游戏。
通过配置元数据（PYGAME_GAMES）丰富游戏信息，支持缓存和刷新。
"""
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 扫描结果中每个游戏的默认图标
_DEFAULT_ICON = 'fas fa-gamepad'
_DEFAULT_CATEGORY = 'other'
_DEFAULT_DIFFICULTY = 'medium'


class GameScanner:
    """Pygame 游戏自动扫描器

    扫描 gamecenter/ 目录下的子目录，识别包含 main.py 的目录为可启动游戏。
    使用 PYGAME_GAMES 配置列表丰富元数据。结果被缓存以避免重复 I/O。

    Args:
        gamecenter_root: gamecenter 根目录路径
        exclude_dirs: 需要排除的目录名列表
        pygame_games_config: PYGAME_GAMES 配置列表（用于元数据丰富）
    """

    def __init__(
        self,
        gamecenter_root: Path,
        exclude_dirs: Optional[List[str]] = None,
        pygame_games_config: Optional[List[Dict]] = None,
    ) -> None:
        self._root = Path(gamecenter_root)
        self._exclude = set(exclude_dirs or [])
        self._metadata_map: Dict[str, Dict] = {}
        if pygame_games_config:
            for item in pygame_games_config:
                self._metadata_map[item['id']] = item
        self._cache: Optional[List[Dict]] = None
        self._cache_time: float = 0.0
        logger.info("GameScanner 初始化: root=%s, exclude=%s", self._root, self._exclude)

    def scan_pygame_games(self) -> List[Dict]:
        """扫描并返回所有 Pygame 游戏元数据列表（使用缓存）

        Returns:
            游戏元数据字典列表，每项包含 id, name, description, category,
            difficulty, module, icon, path 字段。
        """
        if self._cache is not None:
            return list(self._cache)
        return self._do_scan()

    def refresh_cache(self) -> List[Dict]:
        """强制刷新扫描缓存并返回最新游戏列表

        Returns:
            刷新后的游戏元数据列表
        """
        self._cache = None
        return self._do_scan()

    def get_game_by_id(self, game_id: str) -> Optional[Dict]:
        """根据 game_id 获取单个游戏元数据

        Args:
            game_id: 游戏标识符（即目录名）

        Returns:
            游戏元数据字典，若未找到返回 None
        """
        games = self.scan_pygame_games()
        for game in games:
            if game['id'] == game_id:
                return game
        return None

    def get_valid_game_ids(self) -> set:
        """获取所有合法 game_id 集合（用于白名单校验）

        Returns:
            合法 game_id 字符串集合
        """
        return {g['id'] for g in self.scan_pygame_games()}

    def _do_scan(self) -> List[Dict]:
        """执行实际的目录扫描

        Returns:
            扫描到的游戏元数据列表
        """
        start = time.monotonic()
        games: List[Dict] = []

        if not self._root.is_dir():
            logger.warning("gamecenter 根目录不存在: %s", self._root)
            self._cache = games
            return games

        for entry in sorted(self._root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name in self._exclude:
                continue
            if entry.name.startswith('.') or entry.name.startswith('_'):
                continue
            main_py = entry / 'main.py'
            if not main_py.is_file():
                continue
            metadata = self._build_metadata(entry)
            games.append(metadata)

        elapsed = (time.monotonic() - start) * 1000
        logger.info("扫描完成: 发现 %d 个 Pygame 游戏 (%.1fms)", len(games), elapsed)

        self._cache = games
        self._cache_time = time.monotonic()
        return list(games)

    def _build_metadata(self, game_dir: Path) -> Dict:
        """为单个游戏目录构建元数据字典

        优先使用 PYGAME_GAMES 配置中的元数据，未配置的使用目录名生成默认值。

        Args:
            game_dir: 游戏目录 Path 对象

        Returns:
            游戏元数据字典
        """
        game_id = game_dir.name
        config_meta = self._metadata_map.get(game_id, {})

        return {
            'id': game_id,
            'name': config_meta.get('name', game_id),
            'description': config_meta.get('description', f'{game_id} Pygame 游戏'),
            'category': config_meta.get('category', _DEFAULT_CATEGORY),
            'difficulty': config_meta.get('difficulty', _DEFAULT_DIFFICULTY),
            'module': config_meta.get('module', f'gamecenter.{game_id}'),
            'icon': config_meta.get('icon', _DEFAULT_ICON),
            'game_type': 'pygame',
            'path': str(game_dir),
        }
