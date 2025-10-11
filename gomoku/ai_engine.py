"""五子棋AI引擎模块
AI engine for Gomoku using Minimax with Alpha-Beta pruning.

包含三个难度级别、着法生成优化、历史启发等功能。
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Dict, List, Optional, Tuple

from gamecenter.gomoku.evaluation import BoardEvaluator, evaluate_move
from gamecenter.gomoku.game_logic import Board, Player


class DifficultyLevel(Enum):
    """AI难度等级"""
    EASY = "easy"        # 3层深度，基础Minimax
    MEDIUM = "medium"    # 5层深度，Alpha-Beta剪枝
    HARD = "hard"        # 7层深度，迭代加深 + 历史启发
    
    def get_depth(self) -> int:
        """获取搜索深度"""
        depths = {
            DifficultyLevel.EASY: 3,
            DifficultyLevel.MEDIUM: 5,
            DifficultyLevel.HARD: 7,
        }
        return depths[self]
    
    def __str__(self) -> str:
        return self.value


class MoveGenerator:
    """着法生成器
    
    优化搜索空间，只生成有价值的候选着法。
    """
    
    def __init__(self, board: Board, search_distance: int = 2):
        """初始化着法生成器
        
        Args:
            board: 棋盘实例
            search_distance: 搜索距离（默认2格）
        """
        self.board = board
        self.search_distance = search_distance
    
    def generate_moves(self, player: Player) -> List[Tuple[int, int]]:
        """生成候选着法列表
        
        Args:
            player: 当前玩家
        
        Returns:
            候选着法坐标列表
        """
        # 获取已落子周围的空位
        candidates = self.board.get_empty_neighbors(self.search_distance)
        
        if not candidates:
            # 第一步，返回中心
            center = self.board.size // 2
            return [(center, center)]
        
        return candidates
    
    def generate_sorted_moves(self, player: Player, top_n: int = 20) -> List[Tuple[int, int]]:
        """生成并排序候选着法
        
        Args:
            player: 当前玩家
            top_n: 返回前N个最佳着法
        
        Returns:
            排序后的着法列表
        """
        candidates = self.generate_moves(player)
        
        # 快速评估每个着法
        scored_moves = []
        for row, col in candidates:
            score = evaluate_move(self.board, row, col, player)
            scored_moves.append(((row, col), score))
        
        # 按分数降序排序
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前N个
        return [move for move, score in scored_moves[:top_n]]


class HistoryTable:
    """历史启发表
    
    记录历史最佳着法，用于移动排序优化。
    """
    
    def __init__(self, board_size: int = 15):
        """初始化历史表
        
        Args:
            board_size: 棋盘大小
        """
        self.board_size = board_size
        self.table: Dict[Tuple[int, int], int] = {}
    
    def record(self, row: int, col: int, depth: int) -> None:
        """记录一个好的着法
        
        Args:
            row, col: 着法位置
            depth: 搜索深度（深度越大权重越高）
        """
        key = (row, col)
        self.table[key] = self.table.get(key, 0) + (1 << depth)
    
    def get_score(self, row: int, col: int) -> int:
        """获取着法的历史分数"""
        return self.table.get((row, col), 0)
    
    def clear(self) -> None:
        """清空历史表"""
        self.table.clear()


class AIController:
    """AI控制器
    
    统一的AI接口，支持不同难度级别。
    """
    
    def __init__(self, difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
                 time_limit: float = 10.0):
        """初始化AI控制器
        
        Args:
            difficulty: 难度级别
            time_limit: 时间限制（秒）
        """
        self.difficulty = difficulty
        self.time_limit = time_limit
        self.evaluator = BoardEvaluator()
        self.history_table = HistoryTable()
        
        # 统计信息
        self.nodes_searched = 0
        self.search_time = 0.0
    
    def set_difficulty(self, difficulty: DifficultyLevel) -> None:
        """设置难度"""
        self.difficulty = difficulty
        self.history_table.clear()
    
    def find_best_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """寻找最佳着法
        
        Args:
            board: 棋盘实例
            player: AI玩家
        
        Returns:
            最佳着法坐标，如果无着法则返回None
        """
        self.nodes_searched = 0
        start_time = time.time()
        
        # 检查是否有必胜着法
        killer_move = self._find_killer_move(board, player)
        if killer_move:
            self.search_time = time.time() - start_time
            return killer_move
        
        # 根据难度选择搜索策略
        if self.difficulty == DifficultyLevel.HARD:
            best_move = self._iterative_deepening_search(board, player)
        else:
            depth = self.difficulty.get_depth()
            best_move, _ = self._minimax_search(
                board, player, depth, -float('inf'), float('inf'), True
            )
        
        self.search_time = time.time() - start_time
        return best_move
    
    def _find_killer_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """寻找杀棋着法（立即获胜或防御必输）
        
        Args:
            board: 棋盘
            player: 玩家
        
        Returns:
            杀棋着法，无则返回None
        """
        move_gen = MoveGenerator(board)
        candidates = move_gen.generate_moves(player)
        
        # 检查我方是否有必胜着法
        for row, col in candidates:
            temp_board = board.copy()
            temp_board.place_stone(row, col, player)
            if temp_board.state.value in ['black_win', 'white_win']:
                return (row, col)
        
        # 检查对方是否有必胜威胁
        opponent = player.opponent()
        for row, col in candidates:
            temp_board = board.copy()
            temp_board.place_stone(row, col, opponent)
            if temp_board.state.value in ['black_win', 'white_win']:
                return (row, col)  # 必须防守
        
        return None
    
    def _iterative_deepening_search(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """迭代加深搜索
        
        Args:
            board: 棋盘
            player: 玩家
        
        Returns:
            最佳着法
        """
        best_move = None
        max_depth = self.difficulty.get_depth()
        
        # 从深度1开始逐步加深
        for depth in range(1, max_depth + 1):
            if time.time() - time.time() > self.time_limit:
                break
            
            move, score = self._minimax_search(
                board, player, depth, -float('inf'), float('inf'), True
            )
            
            if move:
                best_move = move
                
                # 如果找到必胜着法，提前返回
                if abs(score) > 50000:
                    break
        
        return best_move
    
    def _minimax_search(self, board: Board, player: Player, depth: int,
                       alpha: float, beta: float, is_maximizing: bool
                       ) -> Tuple[Optional[Tuple[int, int]], float]:
        """Minimax搜索（带Alpha-Beta剪枝）
        
        Args:
            board: 棋盘
            player: AI玩家（固定）
            depth: 剩余搜索深度
            alpha: Alpha值
            beta: Beta值
            is_maximizing: 是否为最大化节点
        
        Returns:
            (最佳着法, 评估分数)
        """
        self.nodes_searched += 1
        
        # 终止条件
        if depth == 0 or board.state.value != 'ongoing':
            score = self.evaluator.evaluate(board, player)
            return (None, score)
        
        # 生成候选着法
        current_player = board.current_player
        move_gen = MoveGenerator(board)
        
        # 根据难度选择候选数量
        if self.difficulty == DifficultyLevel.EASY:
            candidates = move_gen.generate_sorted_moves(current_player, top_n=10)
        else:
            candidates = move_gen.generate_sorted_moves(current_player, top_n=15)
        
        if not candidates:
            return (None, 0.0)
        
        # 使用历史启发排序
        if self.difficulty == DifficultyLevel.HARD:
            candidates = self._sort_by_history(candidates)
        
        best_move = None
        
        if is_maximizing:
            max_eval = -float('inf')
            
            for row, col in candidates:
                # 尝试着法
                temp_board = board.copy()
                temp_board.place_stone(row, col)
                
                # 递归搜索
                _, eval_score = self._minimax_search(
                    temp_board, player, depth - 1, alpha, beta, False
                )
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (row, col)
                
                # Alpha-Beta剪枝
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    # 记录历史启发
                    if self.difficulty == DifficultyLevel.HARD:
                        self.history_table.record(row, col, depth)
                    break
            
            return (best_move, max_eval)
        
        else:
            min_eval = float('inf')
            
            for row, col in candidates:
                # 尝试着法
                temp_board = board.copy()
                temp_board.place_stone(row, col)
                
                # 递归搜索
                _, eval_score = self._minimax_search(
                    temp_board, player, depth - 1, alpha, beta, True
                )
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (row, col)
                
                # Alpha-Beta剪枝
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return (best_move, min_eval)
    
    def _sort_by_history(self, moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """使用历史启发排序着法
        
        Args:
            moves: 着法列表
        
        Returns:
            排序后的着法列表
        """
        scored_moves = [
            (move, self.history_table.get_score(move[0], move[1]))
            for move in moves
        ]
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in scored_moves]
    
    def get_stats(self) -> Dict[str, any]:
        """获取搜索统计信息"""
        return {
            'nodes_searched': self.nodes_searched,
            'search_time': self.search_time,
            'nodes_per_second': (self.nodes_searched / self.search_time 
                                if self.search_time > 0 else 0),
        }


def create_ai(difficulty: str = "medium") -> AIController:
    """创建AI实例（工厂函数）
    
    Args:
        difficulty: 难度字符串（"easy", "medium", "hard"）
    
    Returns:
        AI控制器实例
    """
    difficulty_map = {
        'easy': DifficultyLevel.EASY,
        'medium': DifficultyLevel.MEDIUM,
        'hard': DifficultyLevel.HARD,
    }
    
    level = difficulty_map.get(difficulty.lower(), DifficultyLevel.MEDIUM)
    return AIController(level)
