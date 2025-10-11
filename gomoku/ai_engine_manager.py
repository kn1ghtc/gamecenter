"""AI引擎管理器 - 支持C++/Python引擎切换和自动回退
AI Engine Manager with C++/Python switching and automatic fallback.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple
from enum import Enum

from gamecenter.gomoku.game_logic import Board, Player

# 尝试导入C++引擎
try:
    from gamecenter.gomoku.cpp_engine.cpp_ai_wrapper import CppAIEngine
    CPP_AVAILABLE = True
except (ImportError, FileNotFoundError, OSError) as e:
    CPP_AVAILABLE = False
    logging.warning(f"C++ engine not available: {e}")

# 导入Python引擎
try:
    from gamecenter.gomoku.ai_engine_phase2 import Phase2AIController, DifficultyLevel
    PYTHON_PHASE2_AVAILABLE = True
except ImportError:
    PYTHON_PHASE2_AVAILABLE = False
    from gamecenter.gomoku.ai_engine import OptimizedAIController, DifficultyLevel
    PYTHON_PHASE2_AVAILABLE = False


class EngineType(Enum):
    """AI引擎类型"""
    CPP = "cpp"           # C++引擎 (最快)
    PYTHON_PHASE2 = "python_phase2"  # Python Phase 2优化
    PYTHON_PHASE1 = "python_phase1"  # Python Phase 1优化
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
                 time_limit: float = 5.0):
        """初始化AI引擎管理器
        
        Args:
            engine_type: 引擎类型
            difficulty: 难度等级 ('easy', 'medium', 'hard')
            time_limit: 时间限制(秒)
        """
        self.requested_engine_type = engine_type
        self.difficulty_name = difficulty
        self.time_limit = time_limit
        self.current_engine_type: Optional[EngineType] = None
        self.engine: Optional[any] = None
        
        # 统计信息
        self.cpp_failures = 0
        self.fallback_count = 0
        
        # 初始化引擎
        self._initialize_engine()
    
    def _initialize_engine(self) -> None:
        """初始化AI引擎"""
        # 确定使用的引擎类型
        if self.requested_engine_type == EngineType.AUTO:
            # 自动选择: C++ > Python Phase2 > Python Phase1
            if CPP_AVAILABLE:
                target_type = EngineType.CPP
            elif PYTHON_PHASE2_AVAILABLE:
                target_type = EngineType.PYTHON_PHASE2
            else:
                target_type = EngineType.PYTHON_PHASE1
        else:
            target_type = self.requested_engine_type
        
        # 尝试创建引擎
        success = self._create_engine(target_type)
        
        # 如果失败，尝试回退
        if not success:
            logging.warning(f"Failed to create {target_type}, trying fallback...")
            self.fallback_count += 1
            
            if target_type == EngineType.CPP:
                # C++失败，尝试Python Phase2
                if PYTHON_PHASE2_AVAILABLE:
                    self._create_engine(EngineType.PYTHON_PHASE2)
                else:
                    self._create_engine(EngineType.PYTHON_PHASE1)
            elif target_type == EngineType.PYTHON_PHASE2:
                # Phase2失败，使用Phase1
                self._create_engine(EngineType.PYTHON_PHASE1)
    
    def _create_engine(self, engine_type: EngineType) -> bool:
        """创建指定类型的引擎
        
        Returns:
            bool: 是否成功
        """
        try:
            if engine_type == EngineType.CPP:
                if not CPP_AVAILABLE:
                    return False
                
                # 映射难度到深度
                depth_map = {'easy': 3, 'medium': 5, 'hard': 7}
                depth = depth_map.get(self.difficulty_name, 5)
                
                self.engine = CppAIEngine()
                self.current_engine_type = EngineType.CPP
                # 存储参数供find_best_move使用
                self._cpp_depth = depth
                logging.info("C++ engine initialized successfully")
                return True
            
            elif engine_type == EngineType.PYTHON_PHASE2:
                if not PYTHON_PHASE2_AVAILABLE:
                    return False
                
                from gamecenter.gomoku.ai_engine_phase2 import Phase2AIController
                difficulty_map = {
                    'easy': DifficultyLevel.EASY,
                    'medium': DifficultyLevel.MEDIUM,
                    'hard': DifficultyLevel.HARD,
                }
                difficulty = difficulty_map.get(self.difficulty_name, DifficultyLevel.MEDIUM)
                self.engine = Phase2AIController(difficulty, self.time_limit)
                self.current_engine_type = EngineType.PYTHON_PHASE2
                logging.info("Python Phase 2 engine initialized successfully")
                return True
            
            else:  # PYTHON_PHASE1
                from gamecenter.gomoku.ai_engine import OptimizedAIController
                difficulty_map = {
                    'easy': DifficultyLevel.EASY,
                    'medium': DifficultyLevel.MEDIUM,
                    'hard': DifficultyLevel.HARD,
                }
                difficulty = difficulty_map.get(self.difficulty_name, DifficultyLevel.MEDIUM)
                self.engine = OptimizedAIController(difficulty, self.time_limit)
                self.current_engine_type = EngineType.PYTHON_PHASE1
                logging.info("Python Phase 1 engine initialized successfully")
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
                if PYTHON_PHASE2_AVAILABLE:
                    self._create_engine(EngineType.PYTHON_PHASE2)
                else:
                    self._create_engine(EngineType.PYTHON_PHASE1)
                
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
        
        if self.current_engine_type == EngineType.CPP:
            # C++引擎：更新深度参数
            depth_map = {'easy': 3, 'medium': 5, 'hard': 7}
            self._cpp_depth = depth_map.get(difficulty, 5)
        else:
            # Python引擎：调用set_difficulty
            difficulty_map = {
                'easy': DifficultyLevel.EASY,
                'medium': DifficultyLevel.MEDIUM,
                'hard': DifficultyLevel.HARD,
            }
            diff_level = difficulty_map.get(difficulty, DifficultyLevel.MEDIUM)
            if hasattr(self.engine, 'set_difficulty'):
                self.engine.set_difficulty(diff_level)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            'engine_type': self.current_engine_type.value if self.current_engine_type else 'none',
            'cpp_available': CPP_AVAILABLE,
            'python_phase2_available': PYTHON_PHASE2_AVAILABLE,
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
        elif self.current_engine_type == EngineType.PYTHON_PHASE2:
            return "Python Phase 2"
        elif self.current_engine_type == EngineType.PYTHON_PHASE1:
            return "Python Phase 1"
        else:
            return "Unknown"
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.engine and hasattr(self.engine, 'tt'):
            self.engine.tt.clear()
        if self.engine and hasattr(self.engine, 'killer_table'):
            self.engine.killer_table.clear()


def create_ai_engine(engine_type: str = "auto", 
                     difficulty: str = "medium",
                     time_limit: float = 5.0) -> AIEngineManager:
    """创建AI引擎管理器（工厂函数）
    
    Args:
        engine_type: 引擎类型 ('auto', 'cpp', 'python_phase2', 'python_phase1')
        difficulty: 难度 ('easy', 'medium', 'hard')
        time_limit: 时间限制(秒)
    
    Returns:
        AIEngineManager实例
    """
    engine_type_map = {
        'auto': EngineType.AUTO,
        'cpp': EngineType.CPP,
        'python_phase2': EngineType.PYTHON_PHASE2,
        'python_phase1': EngineType.PYTHON_PHASE1,
    }
    
    engine_enum = engine_type_map.get(engine_type.lower(), EngineType.AUTO)
    return AIEngineManager(engine_enum, difficulty, time_limit)
