"""AI引擎管理器 - 支持C++/Python引擎切换和自动回退
AI Engine Manager with C++/Python switching and automatic fallback.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Tuple
from enum import Enum

from gamecenter.gomoku.config.config_manager import get_difficulty_config
from gamecenter.gomoku.game_logic import Board, Player, GameState

# 尝试导入C++引擎
try:
    from gamecenter.gomoku.cpp_engine.cpp_ai_wrapper import CppAIEngine
    CPP_AVAILABLE = True
except (ImportError, FileNotFoundError, OSError) as e:
    CPP_AVAILABLE = False
    logging.warning(f"C++ engine not available: {e}")

from gamecenter.gomoku.ai_engine import OptimizedAIController


class EngineType(Enum):
    """AI引擎类型"""
    CPP = "cpp"           # C++引擎 (最快)
    PYTHON = "python"     # Python引擎
    AUTO = "auto"         # 自动选择 (优先C++)


class AIEngineManager:
    """AI引擎管理器
    
    功能:
    1. 支持C++和Python引擎切换
    2. C++引擎出错自动回退到Python
    3. 统一的API接口
    4. 性能统计
    """
    
    def __init__(self, 
                 engine_type: EngineType = EngineType.AUTO,
                 difficulty: str = "medium",
                 time_limit: Optional[float] = None):
        """初始化AI引擎管理器
        
        Args:
            engine_type: 引擎类型
            difficulty: 难度等级 ('easy', 'medium', 'hard')
            time_limit: 时间限制(秒)
        """
        self.requested_engine_type = engine_type
        self.difficulty_name = difficulty
        try:
            self._difficulty_config = get_difficulty_config(self.difficulty_name)
        except KeyError:  # pragma: no cover - config fallback safeguard
            logging.warning("Difficulty '%s' not found. Falling back to 'medium'.", self.difficulty_name)
            self.difficulty_name = "medium"
            self._difficulty_config = get_difficulty_config(self.difficulty_name)
        self._custom_time_limit = time_limit is not None
        self.time_limit = time_limit if self._custom_time_limit else self._difficulty_config.time_limit
        self._cpp_depth = self._difficulty_config.search_depth
        self.current_engine_type: Optional[EngineType] = None
        self.engine: Optional[Any] = None
        
        # 统计信息
        self.cpp_failures = 0
        self.fallback_count = 0
        
        # 初始化引擎
        self._initialize_engine()
    
    def _initialize_engine(self) -> None:
        """初始化AI引擎"""
        # 确定使用的引擎类型
        if self.requested_engine_type == EngineType.AUTO:
            # 自动选择: C++ 优先，其次 Python
            target_type = EngineType.CPP if CPP_AVAILABLE else EngineType.PYTHON
        else:
            target_type = self.requested_engine_type
        
        # 尝试创建引擎
        success = self._create_engine(target_type)
        
        # 如果失败，尝试回退
        if not success:
            logging.warning(f"Failed to create {target_type}, trying fallback...")
            self.fallback_count += 1
            
            if target_type == EngineType.CPP:
                # C++失败，尝试Python引擎
                self._create_engine(EngineType.PYTHON)
            # Python失败无进一步回退
    
    def _create_engine(self, engine_type: EngineType) -> bool:
        """创建指定类型的引擎
        
        Returns:
            bool: 是否成功
        """
        try:
            if engine_type == EngineType.CPP:
                if not CPP_AVAILABLE:
                    return False
                
                # 使用配置中的搜索深度
                depth = self._difficulty_config.search_depth
                
                self.engine = CppAIEngine()
                self.current_engine_type = EngineType.CPP
                # 存储参数供find_best_move使用
                self._cpp_depth = depth
                logging.info("C++ engine initialized successfully")
                return True
            
            else:  # PYTHON
                self.engine = OptimizedAIController(self.difficulty_name, self.time_limit)
                self.current_engine_type = EngineType.PYTHON
                logging.info("Python engine initialized successfully")
                return True
        
        except Exception as e:
            logging.error(f"Failed to create {engine_type} engine: {e}")
            return False
    
    def find_best_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """寻找最佳着法
        
        Args:
            board: 棋盘
            player: 玩家
        
        Returns:
            最佳着法坐标，失败返回None
        """
        if self.engine is None:
            logging.error("No engine available!")
            return None
        
        immediate_move = self._find_immediate_move(board, player)
        if immediate_move is not None:
            return immediate_move

        try:
            if self.current_engine_type == EngineType.CPP:
                # C++引擎调用
                move = self.engine.find_best_move(board, player, self._cpp_depth, self.time_limit)
                return move
            else:
                # Python引擎调用
                move = self.engine.find_best_move(board, player)
                return move
        
        except Exception as e:
            logging.error(f"Engine error: {e}")
            
            # 如果是C++引擎出错，尝试回退到Python
            if self.current_engine_type == EngineType.CPP:
                self.cpp_failures += 1
                logging.warning(f"C++ engine failed (count: {self.cpp_failures}), falling back to Python...")
                
                # 回退到Python
                self._create_engine(EngineType.PYTHON)
                
                # 重试
                try:
                    return self.engine.find_best_move(board, player)
                except Exception as e2:
                    logging.error(f"Fallback engine also failed: {e2}")
                    return None
            
            return None
    
    def set_difficulty(self, difficulty: str) -> None:
        """设置难度
        
        Args:
            difficulty: 难度名称 ('easy', 'medium', 'hard')
        """
        self.difficulty_name = difficulty
        self._difficulty_config = get_difficulty_config(self.difficulty_name)
        if not self._custom_time_limit:
            self.time_limit = self._difficulty_config.time_limit
        
        if self.current_engine_type == EngineType.CPP:
            # C++引擎：更新深度参数
            self._cpp_depth = self._difficulty_config.search_depth
        else:
            # Python引擎：调用set_difficulty (now accepts string)
            if hasattr(self.engine, 'set_difficulty'):
                self.engine.set_difficulty(difficulty)
                if self._custom_time_limit:
                    # 重新应用自定义时间限制
                    setattr(self.engine, 'time_limit', self.time_limit)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            'engine_type': self.current_engine_type.value if self.current_engine_type else 'none',
            'cpp_available': CPP_AVAILABLE,
            'cpp_failures': self.cpp_failures,
            'fallback_count': self.fallback_count,
        }
        
        # 添加引擎特定统计
        if self.engine and hasattr(self.engine, 'get_stats'):
            engine_stats = self.engine.get_stats()
            stats.update(engine_stats)
        elif self.current_engine_type == EngineType.CPP and self.engine:
            # C++引擎统计
            if hasattr(self.engine, 'nodes_searched'):
                stats['nodes_searched'] = self.engine.nodes_searched
            if hasattr(self.engine, 'search_time'):
                stats['search_time'] = self.engine.search_time
        
        return stats
    
    def get_engine_name(self) -> str:
        """获取当前引擎名称"""
        if self.current_engine_type == EngineType.CPP:
            return "C++ Engine"
        elif self.current_engine_type == EngineType.PYTHON:
            return "Python Engine"
        else:
            return "Unknown"
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.engine and hasattr(self.engine, 'tt'):
            self.engine.tt.clear()
        if self.engine and hasattr(self.engine, 'killer_table'):
            self.engine.killer_table.clear()

    def _find_immediate_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """检测立即获胜或必须防守的落点"""
        if board.state != GameState.ONGOING:
            return None

        candidates = board.get_empty_neighbors(distance=1)
        if not candidates:
            candidates = board.get_empty_neighbors(distance=2)

        winning_move = self._find_for_player(board, player, candidates)
        if winning_move:
            return winning_move

        blocking_move = self._find_for_player(board, player.opponent(), candidates)
        if blocking_move:
            return blocking_move

        return None

    def _find_for_player(self, board: Board, target_player: Player,
                         candidates: list[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """判断候选点是否对指定玩家形成五连"""
        for row, col in candidates:
            test_board = board.copy()
            if not test_board.place_stone(row, col, target_player):
                continue
            if target_player == Player.BLACK and test_board.state == GameState.BLACK_WIN:
                return (row, col)
            if target_player == Player.WHITE and test_board.state == GameState.WHITE_WIN:
                return (row, col)
        return None


def create_ai_engine(engine_type: str = "auto", 
                     difficulty: str = "medium",
                     time_limit: Optional[float] = None) -> AIEngineManager:
    """创建AI引擎管理器（工厂函数）
    
    Args:
        engine_type: 引擎类型 ('auto', 'cpp', 'python')
        difficulty: 难度 ('easy', 'medium', 'hard')
        time_limit: 时间限制(秒)
    
    Returns:
        AIEngineManager实例
    """
    engine_type_lower = engine_type.lower()
    if engine_type_lower in {"python_phase1", "python_phase2"}:
        logging.warning("Engine type '%s' is deprecated. Using 'python' engine instead.", engine_type)
        engine_type_lower = "python"

    engine_type_map = {
        'auto': EngineType.AUTO,
        'cpp': EngineType.CPP,
        'python': EngineType.PYTHON,
    }
    
    engine_enum = engine_type_map.get(engine_type_lower, EngineType.AUTO)
    return AIEngineManager(engine_enum, difficulty, time_limit)
