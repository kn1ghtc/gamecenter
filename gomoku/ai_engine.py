"""高性能AI引擎模块（优化版）
Optimized AI engine with Transposition Table, better move ordering, and faster evaluation.

性能优化策略：
1. Transposition Table（置换表）：缓存已搜索局面
2. 更激进的着法剪枝：只搜索最有价值的Top-N着法
3. 快速评估函数：增量评估，减少重复计算
4. 更好的着法排序：提升Alpha-Beta剪枝效率
5. 时间管理：动态调整搜索深度
"""

from __future__ import annotations

import random
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict

from gamecenter.gomoku.evaluation import BoardEvaluator, evaluate_move
from gamecenter.gomoku.game_logic import Board, Player, GameState
from gamecenter.gomoku.config.config_manager import (
    get_config_manager,
    get_difficulty_config,
    DifficultyConfig,
)


_CONFIG = get_config_manager()
_GAMEPLAY_CONFIG = _CONFIG.get_gameplay_config()
_ENGINE_CONFIG = _CONFIG.get_engine_metadata()
BOARD_SIZE_DEFAULT = _GAMEPLAY_CONFIG.get('board_size', 15)
DEFAULT_TIME_LIMIT = _CONFIG.get_engine_defaults().get('time_limit', 5.0)
DEFAULT_TT_SIZE = _ENGINE_CONFIG.get('python', {}).get('transposition_table_size', 500_000)


class HistoryTable:
    """历史启发表
    
    记录历史最佳着法，用于移动排序优化。
    """
    
    def __init__(self, board_size: int = BOARD_SIZE_DEFAULT):
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


class ZobristHasher:
    """Zobrist哈希生成器
    
    使用随机数表为每个(row, col, player)组合生成唯一64位哈希值。
    支持O(1)增量更新。
    """
    
    def __init__(self, board_size: int = BOARD_SIZE_DEFAULT, seed: int = 12345):
        """初始化Zobrist哈希表
        
        Args:
            board_size: 棋盘大小
            seed: 随机数种子（确保可重现）
        """
        random.seed(seed)
        
        # 为每个位置和玩家生成随机64位数
        self.zobrist_table = [
            [[random.getrandbits(64) for _ in range(2)]  # [BLACK, WHITE]
             for _ in range(board_size)]
            for _ in range(board_size)
        ]
        
        self.board_size = board_size
    
    def compute_hash(self, board: Board) -> int:
        """计算棋盘的完整哈希值
        
        Args:
            board: 棋盘实例
            
        Returns:
            64位哈希值
        """
        hash_value = 0
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                stone = board.get_stone(row, col)
                if stone is not None:
                    player_idx = 0 if stone == Player.BLACK else 1
                    hash_value ^= self.zobrist_table[row][col][player_idx]
        
        return hash_value
    
    def update_hash(self, current_hash: int, row: int, col: int, player: Player) -> int:
        """增量更新哈希值（落子或悔棋）
        
        Args:
            current_hash: 当前哈希值
            row: 行坐标
            col: 列坐标
            player: 玩家
            
        Returns:
            更新后的哈希值
        """
        player_idx = 0 if player == Player.BLACK else 1
        return current_hash ^ self.zobrist_table[row][col][player_idx]


class KillerMoveTable:
    """杀手着法表
    
    记录在同一深度引起beta剪枝的着法，优先搜索这些着法。
    """
    
    def __init__(self, max_depth: int = 20):
        """初始化杀手着法表
        
        Args:
            max_depth: 最大搜索深度
        """
        self.max_depth = max_depth
        # 每层保存2个杀手着法
        self.killers = [[] for _ in range(max_depth + 1)]
    
    def add(self, move: Tuple[int, int], depth: int) -> None:
        """添加杀手着法
        
        Args:
            move: 着法坐标
            depth: 搜索深度
        """
        if depth > self.max_depth:
            return
        
        if move not in self.killers[depth]:
            # 插入到列表开头，只保留最近的2个
            self.killers[depth].insert(0, move)
            self.killers[depth] = self.killers[depth][:2]
    
    def get(self, depth: int) -> List[Tuple[int, int]]:
        """获取该深度的杀手着法
        
        Args:
            depth: 搜索深度
            
        Returns:
            杀手着法列表
        """
        if depth > self.max_depth:
            return []
        return self.killers[depth]
    
    def clear(self) -> None:
        """清空所有杀手着法"""
        self.killers = [[] for _ in range(self.max_depth + 1)]


class TranspositionTable:
    """置换表（缓存已搜索局面）
    
    使用Zobrist哈希 + LRU策略管理内存，存储局面评估结果。
    """
    
    def __init__(self, max_size: int = DEFAULT_TT_SIZE, zobrist: Optional[ZobristHasher] = None):
        """初始化置换表
        
        Args:
            max_size: 最大条目数
            zobrist: Zobrist哈希器（如果为None则创建新实例）
        """
        self.max_size = max_size
        self.table: OrderedDict = OrderedDict()
        self.zobrist = zobrist or ZobristHasher()
        self.hits = 0
        self.misses = 0
    
    def get(self, hash_key: int, depth: int, alpha: float, beta: float) -> Optional[Tuple[Optional[Tuple[int, int]], float]]:
        """查询置换表
        
        Args:
            hash_key: Zobrist哈希值
            depth: 搜索深度
            alpha: alpha值
            beta: beta值
        
        Returns:
            (best_move, score) 如果命中，否则返回None
        """
        key = (hash_key, depth)
        
        if key in self.table:
            entry = self.table[key]
            score, best_move, entry_alpha, entry_beta = entry
            
            # 移到最后（LRU更新）
            self.table.move_to_end(key)
            self.hits += 1
            
            # 检查是否可用（alpha-beta窗口是否匹配）
            if entry_alpha <= alpha and entry_beta >= beta:
                return (best_move, score)
        
        self.misses += 1
        return None
    
    def store(self, hash_key: int, depth: int, score: float, best_move: Optional[Tuple[int, int]], 
              alpha: float, beta: float) -> None:
        """存储到置换表
        
        Args:
            hash_key: Zobrist哈希值
            depth: 搜索深度
            score: 评估分数
            best_move: 最佳着法
            alpha: alpha值
            beta: beta值
        """
        key = (hash_key, depth)
        
        # LRU淘汰
        if len(self.table) >= self.max_size:
            self.table.popitem(last=False)
        
        self.table[key] = (score, best_move, alpha, beta)
    
    def clear(self) -> None:
        """清空置换表"""
        self.table.clear()
        self.hits = 0
        self.misses = 0
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class FastMoveGenerator:
    """快速着法生成器（优化版）
    
    减少候选着法数量，提升搜索效率。
    """
    
    def __init__(self, board: Board, top_n: int = 15):
        """初始化着法生成器
        
        Args:
            board: 棋盘实例
            top_n: 返回前N个最佳着法
        """
        self.board = board
        self.top_n = top_n
    
    def generate_best_moves(self, player: Player) -> List[Tuple[int, int]]:
        """生成最佳候选着法列表
        
        只返回评估分数最高的top_n个着法。
        """
        # 获取候选着法（已落子周围2格）
        candidates = self.board.get_empty_neighbors(distance=2)
        
        if not candidates:
            # 第一步，返回中心附近
            center = self.board.size // 2
            return [(center, center)]
        
        if len(candidates) <= self.top_n:
            return candidates
        
        # 快速评估并排序
        scored_moves = []
        for row, col in candidates:
            # 使用快速评估（不使用完整评估函数）
            score = self._quick_evaluate(row, col, player)
            scored_moves.append(((row, col), score))
        
        # 按分数降序排序，返回前N个
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in scored_moves[:self.top_n]]
    
    def _quick_evaluate(self, row: int, col: int, player: Player) -> float:
        """快速评估着法价值
        
        使用简化的评估函数，不调用完整的BoardEvaluator。
        """
        score = 0.0
        
        # 位置权重（中心区域更高）
        center = self.board.size // 2
        distance_to_center = abs(row - center) + abs(col - center)
        score += (15 - distance_to_center) * 10
        
        # 检查四个方向的连续性
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            # 我方连续
            my_count = self._count_consecutive(row, col, dr, dc, player)
            score += my_count * my_count * 100
            
            # 对手连续（需要防守）
            opp_count = self._count_consecutive(row, col, dr, dc, player.opponent())
            score += opp_count * opp_count * 80
        
        return score
    
    def _count_consecutive(self, row: int, col: int, dr: int, dc: int, player: Player) -> int:
        """统计某方向上的连续棋子数"""
        count = 0
        
        # 正向
        r, c = row + dr, col + dc
        while 0 <= r < self.board.size and 0 <= c < self.board.size:
            if self.board.get_stone(r, c) == player:
                count += 1
                r += dr
                c += dc
            else:
                break
        
        # 反向
        r, c = row - dr, col - dc
        while 0 <= r < self.board.size and 0 <= c < self.board.size:
            if self.board.get_stone(r, c) == player:
                count += 1
                r -= dr
                c -= dc
            else:
                break
        
        return count


class OptimizedAIController:
    """优化的AI控制器 (Phase 1)
    
    性能提升：
    - Zobrist Hashing (完美哈希)
    - Transposition Table (高效缓存)
    - Killer Move Heuristic (着法排序)
    - Aspiration Window (窄窗口搜索)
    - 更少的候选着法（Top-15）
    - 时间管理
    """
    
    def __init__(self, difficulty: str = "medium", time_limit: Optional[float] = None):
        """初始化AI控制器
        
        Args:
            difficulty: 难度名称 (easy/medium/hard/expert)
            time_limit: 时间限制（秒），None则使用配置文件中的值
        """
        # 加载难度配置
        self.difficulty_config = get_difficulty_config(difficulty)
        self.difficulty_name = difficulty
        self.time_limit = time_limit if time_limit is not None else self.difficulty_config.time_limit
        
        self.evaluator = BoardEvaluator()
        
        # Zobrist哈希器（所有模块共享）
        self.zobrist = ZobristHasher()
        
        # 置换表（使用配置中的大小）
        tt_size = self.difficulty_config.transposition_table_size
        self.tt = TranspositionTable(max_size=tt_size, zobrist=self.zobrist)
        
        # 历史启发表
        self.history_table = HistoryTable()
        
        # 杀手着法表
        self.killer_table = KillerMoveTable(max_depth=20)
        
        # 统计信息
        self.nodes_searched = 0
        self.search_time = 0.0
        self.search_start_time = 0.0
        self.current_hash = 0  # 当前局面哈希
    
    def set_difficulty(self, difficulty: str) -> None:
        """设置难度
        
        Args:
            difficulty: 难度名称 (easy/medium/hard/expert)
        """
        self.difficulty_config = get_difficulty_config(difficulty)
        self.difficulty_name = difficulty
        self.time_limit = self.difficulty_config.time_limit
        
        # 根据新配置调整TT大小
        tt_size = self.difficulty_config.transposition_table_size
        if len(self.tt.table) != tt_size:
            self.tt = TranspositionTable(max_size=tt_size, zobrist=self.zobrist)
        else:
            self.tt.clear()
        
        self.history_table.clear()
        self.killer_table.clear()
    
    def find_best_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """寻找最佳着法（优化版）"""
        self.nodes_searched = 0
        self.search_start_time = time.time()
        
        # 计算当前局面的Zobrist哈希
        self.current_hash = self.zobrist.compute_hash(board)
        
        # 检查必胜/必防着法
        killer_move = self._find_killer_move(board, player)
        if killer_move:
            self.search_time = time.time() - self.search_start_time
            return killer_move
        
        # 使用迭代加深搜索（所有难度）
        best_move = self._iterative_deepening_search(board, player)
        
        self.search_time = time.time() - self.search_start_time
        return best_move
    
    def _find_killer_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """寻找杀棋着法（立即获胜或防御必输）"""
        move_gen = FastMoveGenerator(board, top_n=board.size * board.size)
        candidates = move_gen.generate_best_moves(player)
        
        for row, col in candidates:
            # 尝试我方落子
            board.place_stone(row, col, player)
            # 检查是否获胜（使用枚举比较）
            if player == Player.BLACK and board.state == GameState.BLACK_WIN:
                board.undo_move()
                return (row, col)
            elif player == Player.WHITE and board.state == GameState.WHITE_WIN:
                board.undo_move()
                return (row, col)
            board.undo_move()
            
            # 尝试对手落子（防守）
            opponent = player.opponent()
            board.place_stone(row, col, opponent)
            if opponent == Player.BLACK and board.state == GameState.BLACK_WIN:
                board.undo_move()
                return (row, col)
            elif opponent == Player.WHITE and board.state == GameState.WHITE_WIN:
                board.undo_move()
                return (row, col)
            board.undo_move()
        
        return None
    
    def _iterative_deepening_search(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        """迭代加深搜索（时间管理版 + Aspiration Window）"""
        best_move = None
        prev_score = 0.0
        max_depth = self.difficulty_config.search_depth
        
        # 从深度1开始逐步加深
        for depth in range(1, max_depth + 1):
            # 检查剩余时间
            elapsed = time.time() - self.search_start_time
            if elapsed > self.time_limit * 0.8:
                break
            
            try:
                if depth == 1:
                    # 第一层使用完整窗口
                    move, score = self._minimax_search(
                        board, player, depth, -float('inf'), float('inf'), True, self.current_hash
                    )
                else:
                    # 使用Aspiration Window（窄窗口搜索）
                    window = 50  # 窗口大小
                    alpha, beta = prev_score - window, prev_score + window
                    
                    move, score = self._minimax_search(
                        board, player, depth, alpha, beta, True, self.current_hash
                    )
                    
                    # 如果超出窗口，使用完整窗口重新搜索
                    if score <= alpha or score >= beta:
                        move, score = self._minimax_search(
                            board, player, depth, -float('inf'), float('inf'), True, self.current_hash
                        )
                
                if move:
                    best_move = move
                    prev_score = score
                    
                    # 如果找到必胜着法，立即返回
                    if score > 90000:
                        break
            except TimeoutError:
                break
        
        return best_move
    
    def _minimax_search(self, board: Board, player: Player, depth: int,
                       alpha: float, beta: float, is_maximizing: bool, 
                       current_hash: Optional[int] = None) -> Tuple[Optional[Tuple[int, int]], float]:
        """Minimax搜索（Alpha-Beta剪枝 + Zobrist哈希 + 置换表 + 杀手着法）"""
        # 超时检查
        if time.time() - self.search_start_time > self.time_limit:
            raise TimeoutError()
        
        self.nodes_searched += 1
        
        # 使用传入的哈希值或计算新的
        if current_hash is None:
            current_hash = self.zobrist.compute_hash(board)
        
        # 查询置换表（使用Zobrist哈希）
        tt_result = self.tt.get(current_hash, depth, alpha, beta)
        if tt_result:
            return tt_result
        
        # 终止条件：达到深度或游戏结束
        if depth == 0 or board.state != GameState.ONGOING:
            score = self.evaluator.evaluate(board, player)
            return (None, score)
        
        # 生成候选着法（减少数量）
        move_gen = FastMoveGenerator(board, top_n=12 if depth > 3 else 15)
        candidates = move_gen.generate_best_moves(player if is_maximizing else player.opponent())
        
        if not candidates:
            return (None, 0.0)
        
        # 着法排序：杀手着法优先
        killer_moves = self.killer_table.get(depth)
        ordered_candidates = []
        
        # 先添加杀手着法
        for move in killer_moves:
            if move in candidates:
                ordered_candidates.append(move)
        
        # 再添加其他着法
        for move in candidates:
            if move not in ordered_candidates:
                ordered_candidates.append(move)
        
        best_move = None
        
        if is_maximizing:
            max_eval = -float('inf')
            for row, col in ordered_candidates:
                # 落子并更新哈希
                board.place_stone(row, col, player)
                new_hash = self.zobrist.update_hash(current_hash, row, col, player)
                
                _, eval_score = self._minimax_search(
                    board, player, depth - 1, alpha, beta, False, new_hash
                )
                
                board.undo_move()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (row, col)
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    # 记录杀手着法和历史表
                    self.killer_table.add((row, col), depth)
                    self.history_table.record(row, col, depth)
                    break
            
            # 存入置换表
            self.tt.store(current_hash, depth, max_eval, best_move, alpha, beta)
            return (best_move, max_eval)
        else:
            min_eval = float('inf')
            current_player = player.opponent()
            for row, col in ordered_candidates:
                # 落子并更新哈希
                board.place_stone(row, col, current_player)
                new_hash = self.zobrist.update_hash(current_hash, row, col, current_player)
                
                _, eval_score = self._minimax_search(
                    board, player, depth - 1, alpha, beta, True, new_hash
                )
                
                board.undo_move()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (row, col)
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    # 记录杀手着法和历史表
                    self.killer_table.add((row, col), depth)
                    self.history_table.record(row, col, depth)
                    break
            
            self.tt.store(current_hash, depth, min_eval, best_move, alpha, beta)
            return (best_move, min_eval)
    
    def get_stats(self) -> dict:
        """获取搜索统计信息"""
        nps = self.nodes_searched / self.search_time if self.search_time > 0 else 0
        return {
            'nodes_searched': self.nodes_searched,
            'search_time': self.search_time,
            'nodes_per_second': nps,
            'tt_hit_rate': self.tt.get_hit_rate(),
            'tt_size': len(self.tt.table)
        }


# 工厂函数（兼容旧接口）
def create_optimized_ai(difficulty_name: str = 'medium', time_limit: Optional[float] = None) -> OptimizedAIController:
    """创建优化AI实例
    
    Args:
        difficulty_name: 难度名称 ('easy', 'medium', 'hard', 'expert')
        time_limit: 时间限制（秒），None则使用配置文件中的值
    
    Returns:
        OptimizedAIController实例
    """
    return OptimizedAIController(difficulty_name, time_limit)
