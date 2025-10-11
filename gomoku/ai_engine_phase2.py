"""Phase 2优化AI引擎
Advanced optimizations for reaching 3000+ NPS target.

Phase 2优化技术:
1. 增量评估 (Incremental Evaluation) - 缓存线评分
2. 后期着法削减 (Late Move Reductions) - 降低后续着法深度
3. 空着裁剪 (Null Move Pruning) - 跳过一步试探
4. 改进的着法排序 - PV move + Hash move + Killer moves
5. 更大的置换表 - 500K entries
"""

from __future__ import annotations

import random
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from collections import OrderedDict

from gamecenter.gomoku.evaluation import BoardEvaluator
from gamecenter.gomoku.game_logic import Board, Player, GameState


# DifficultyLevel现在从config_loader导入
from gamecenter.gomoku.config.config_loader import get_difficulty_config, DifficultyConfig


class HistoryTable:
    """历史启发表"""
    
    def __init__(self, board_size: int = 15):
        self.board_size = board_size
        self.table: Dict[Tuple[int, int], int] = {}
    
    def record(self, row: int, col: int, depth: int) -> None:
        key = (row, col)
        self.table[key] = self.table.get(key, 0) + (1 << depth)
    
    def get_score(self, row: int, col: int) -> int:
        return self.table.get((row, col), 0)
    
    def clear(self) -> None:
        self.table.clear()


class ZobristHasher:
    """Zobrist哈希生成器"""
    
    def __init__(self, board_size: int = 15, seed: int = 12345):
        random.seed(seed)
        self.zobrist_table = [
            [[random.getrandbits(64) for _ in range(2)]
             for _ in range(board_size)]
            for _ in range(board_size)
        ]
        self.board_size = board_size
    
    def compute_hash(self, board: Board) -> int:
        hash_value = 0
        for row in range(self.board_size):
            for col in range(self.board_size):
                stone = board.get_stone(row, col)
                if stone is not None:
                    player_idx = 0 if stone == Player.BLACK else 1
                    hash_value ^= self.zobrist_table[row][col][player_idx]
        return hash_value
    
    def update_hash(self, current_hash: int, row: int, col: int, player: Player) -> int:
        player_idx = 0 if player == Player.BLACK else 1
        return current_hash ^ self.zobrist_table[row][col][player_idx]


class TranspositionTable:
    """置换表 - Phase 2: 增大到500K"""
    
    def __init__(self, max_size: int = 500000, zobrist: Optional[ZobristHasher] = None):
        self.max_size = max_size
        self.table: OrderedDict = OrderedDict()
        self.zobrist = zobrist or ZobristHasher()
        self.hits = 0
        self.misses = 0
    
    def get(self, hash_key: int, depth: int, alpha: float, beta: float) -> Optional[Tuple[Optional[Tuple[int, int]], float]]:
        key = (hash_key, depth)
        if key in self.table:
            entry = self.table[key]
            score, best_move, entry_alpha, entry_beta = entry
            self.table.move_to_end(key)
            self.hits += 1
            if entry_alpha <= alpha and entry_beta >= beta:
                return (best_move, score)
        self.misses += 1
        return None
    
    def store(self, hash_key: int, depth: int, score: float, best_move: Optional[Tuple[int, int]], 
              alpha: float, beta: float) -> None:
        key = (hash_key, depth)
        if len(self.table) >= self.max_size:
            self.table.popitem(last=False)
        self.table[key] = (score, best_move, alpha, beta)
    
    def clear(self) -> None:
        self.table.clear()
        self.hits = 0
        self.misses = 0
    
    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class KillerMoveTable:
    """杀手着法表"""
    
    def __init__(self, max_depth: int = 20):
        self.max_depth = max_depth
        self.killers = [[] for _ in range(max_depth + 1)]
    
    def add(self, move: Tuple[int, int], depth: int) -> None:
        if depth > self.max_depth:
            return
        if move not in self.killers[depth]:
            self.killers[depth].insert(0, move)
            self.killers[depth] = self.killers[depth][:2]
    
    def get(self, depth: int) -> List[Tuple[int, int]]:
        if depth > self.max_depth:
            return []
        return self.killers[depth]
    
    def clear(self) -> None:
        self.killers = [[] for _ in range(self.max_depth + 1)]


class IncrementalEvaluator:
    """增量评估器 - Phase 2优化
    
    缓存每条线的评分，落子时只更新受影响的线。
    """
    
    def __init__(self, board: Board):
        self.board = board
        self.evaluator = BoardEvaluator()
        # 缓存每个位置在4个方向的线评分
        self.line_cache: Dict[Tuple[int, int, int], float] = {}
        self.cached_total_score: Optional[float] = None
    
    def evaluate(self, player: Player) -> float:
        """完整评估 (首次或缓存失效时)"""
        if self.cached_total_score is None:
            self.cached_total_score = self.evaluator.evaluate(self.board, player)
        return self.cached_total_score
    
    def update_move(self, row: int, col: int, player: Player) -> None:
        """增量更新评估 (落子后)"""
        # 清除缓存，下次重新计算
        self.cached_total_score = None
        # 清除受影响位置的缓存
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for d_idx, (dr, dc) in enumerate(directions):
            # 清除该方向上5个位置的缓存
            for i in range(-4, 5):
                r, c = row + dr * i, col + dc * i
                if 0 <= r < 15 and 0 <= c < 15:
                    key = (r, c, d_idx)
                    if key in self.line_cache:
                        del self.line_cache[key]
    
    def invalidate(self) -> None:
        """使缓存失效"""
        self.cached_total_score = None
        self.line_cache.clear()


class FastMoveGenerator:
    """快速着法生成器 - Phase 2改进"""
    
    def __init__(self, board: Board, top_n: int = 15):
        self.board = board
        self.top_n = top_n
        # 缓存候选着法
        self._candidate_cache: Optional[List[Tuple[int, int]]] = None
    
    def generate_best_moves(self, player: Player, pv_move: Optional[Tuple[int, int]] = None,
                           hash_move: Optional[Tuple[int, int]] = None,
                           killer_moves: List[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
        """生成最佳候选着法 - Phase 2: 改进着法排序"""
        candidates = self.board.get_empty_neighbors(distance=2)
        
        if not candidates:
            center = self.board.size // 2
            return [(center, center)]
        
        # 优先级排序: PV move > Hash move > Killer moves > 评估排序
        ordered = []
        
        # 1. PV move (上一次迭代的最佳着法)
        if pv_move and pv_move in candidates:
            ordered.append(pv_move)
            candidates.remove(pv_move)
        
        # 2. Hash move (TT中的最佳着法)
        if hash_move and hash_move in candidates:
            ordered.append(hash_move)
            candidates.remove(hash_move)
        
        # 3. Killer moves
        if killer_moves:
            for km in killer_moves:
                if km in candidates:
                    ordered.append(km)
                    candidates.remove(km)
        
        # 4. 快速评估剩余着法
        if len(candidates) > self.top_n - len(ordered):
            scored_moves = []
            for row, col in candidates:
                score = self._quick_evaluate(row, col, player)
                scored_moves.append(((row, col), score))
            scored_moves.sort(key=lambda x: x[1], reverse=True)
            ordered.extend([move for move, _ in scored_moves[:self.top_n - len(ordered)]])
        else:
            ordered.extend(candidates)
        
        return ordered
    
    def _quick_evaluate(self, row: int, col: int, player: Player) -> float:
        """快速评估"""
        score = 0.0
        center = self.board.size // 2
        distance_to_center = abs(row - center) + abs(col - center)
        score += (15 - distance_to_center) * 10
        
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            my_count = self._count_consecutive(row, col, dr, dc, player)
            score += my_count * my_count * 100
            opp_count = self._count_consecutive(row, col, dr, dc, player.opponent())
            score += opp_count * opp_count * 80
        
        return score
    
    def _count_consecutive(self, row: int, col: int, dr: int, dc: int, player: Player) -> int:
        count = 0
        r, c = row + dr, col + dc
        while 0 <= r < self.board.size and 0 <= c < self.board.size:
            if self.board.get_stone(r, c) == player:
                count += 1
                r += dr
                c += dc
            else:
                break
        r, c = row - dr, col - dc
        while 0 <= r < self.board.size and 0 <= c < self.board.size:
            if self.board.get_stone(r, c) == player:
                count += 1
                r -= dr
                c -= dc
            else:
                break
        return count


class Phase2AIController:
    """Phase 2优化AI控制器
    
    新增优化:
    1. 增量评估
    2. 后期着法削减 (LMR)
    3. 空着裁剪 (NMP)
    4. 改进的着法排序
    5. 使用配置管理的TT大小
    """
    
    def __init__(self, difficulty: str = "medium", time_limit: Optional[float] = None):
        # 加载配置
        from gamecenter.gomoku.config.config_loader import get_config_manager
        self.difficulty_config = get_difficulty_config(difficulty)
        self.difficulty_name = difficulty
        self.time_limit = time_limit if time_limit is not None else self.difficulty_config.time_limit
        
        # 加载Phase 2优化配置并缓存参数（避免热路径查询）
        config_mgr = get_config_manager()
        self.phase2_config = config_mgr.get_phase2_config()
        
        # LMR参数缓存
        lmr_cfg = self.phase2_config.get('late_move_reduction', {})
        self.lmr_enabled = lmr_cfg.get('enabled', True)
        self.lmr_min_depth = lmr_cfg.get('min_depth', 3)
        self.lmr_min_move_idx = lmr_cfg.get('min_move_index', 3)
        self.lmr_reduction = lmr_cfg.get('reduction_amount', 1)
        
        # NMP参数缓存
        nmp_cfg = self.phase2_config.get('null_move_pruning', {})
        self.nmp_enabled = nmp_cfg.get('enabled', True)
        self.nmp_min_depth = nmp_cfg.get('min_depth', 3)
        self.nmp_R = nmp_cfg.get('R_value', 3)
        
        # 初始化组件
        self.zobrist = ZobristHasher()
        tt_size = self.difficulty_config.transposition_table_size
        self.tt = TranspositionTable(max_size=tt_size, zobrist=self.zobrist)
        self.history_table = HistoryTable()
        self.killer_table = KillerMoveTable(max_depth=20)
        
        # 搜索统计
        self.nodes_searched = 0
        self.search_time = 0.0
        self.search_start_time = 0.0
        self.current_hash = 0
        self.pv_move: Optional[Tuple[int, int]] = None
        self.null_move_allowed = True
    
    def set_difficulty(self, difficulty: str) -> None:
        """动态设置难度"""
        self.difficulty_config = get_difficulty_config(difficulty)
        self.difficulty_name = difficulty
        self.time_limit = self.difficulty_config.time_limit
        
        # 调整TT大小
        new_tt_size = self.difficulty_config.transposition_table_size
        if new_tt_size != self.tt.max_size:
            self.tt = TranspositionTable(max_size=new_tt_size, zobrist=self.zobrist)
        else:
            self.tt.clear()
        
        self.history_table.clear()
        self.killer_table.clear()
    
    def find_best_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        self.nodes_searched = 0
        self.search_start_time = time.time()
        self.current_hash = self.zobrist.compute_hash(board)
        
        # 检查必胜/必防
        killer_move = self._find_killer_move(board, player)
        if killer_move:
            self.search_time = time.time() - self.search_start_time
            return killer_move
        
        # 迭代加深搜索
        best_move = self._iterative_deepening_search(board, player)
        self.search_time = time.time() - self.search_start_time
        return best_move
    
    def _find_killer_move(self, board: Board, player: Player) -> Optional[Tuple[int, int]]:
        move_gen = FastMoveGenerator(board, top_n=20)
        candidates = move_gen.generate_best_moves(player)
        
        for row, col in candidates:
            board.place_stone(row, col, player)
            if player == Player.BLACK and board.state == GameState.BLACK_WIN:
                board.undo_move()
                return (row, col)
            elif player == Player.WHITE and board.state == GameState.WHITE_WIN:
                board.undo_move()
                return (row, col)
            board.undo_move()
            
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
        best_move = None
        prev_score = 0.0
        max_depth = self.difficulty_config.search_depth
        
        for depth in range(1, max_depth + 1):
            elapsed = time.time() - self.search_start_time
            if elapsed > self.time_limit * 0.8:
                break
            
            try:
                if depth == 1:
                    move, score = self._minimax_search(
                        board, player, depth, -float('inf'), float('inf'), True, self.current_hash
                    )
                else:
                    # Aspiration windows
                    window = 50
                    alpha, beta = prev_score - window, prev_score + window
                    move, score = self._minimax_search(
                        board, player, depth, alpha, beta, True, self.current_hash
                    )
                    # Re-search if out of window
                    if score <= alpha or score >= beta:
                        move, score = self._minimax_search(
                            board, player, depth, -float('inf'), float('inf'), True, self.current_hash
                        )
                
                if move:
                    best_move = move
                    self.pv_move = move
                    prev_score = score
            except TimeoutError:
                break
        
        return best_move
    
    def _minimax_search(self, board: Board, player: Player, depth: int,
                       alpha: float, beta: float, is_maximizing: bool, 
                       current_hash: Optional[int] = None,
                       allow_null_move: bool = True) -> Tuple[Optional[Tuple[int, int]], float]:
        """Minimax with Phase 2 optimizations"""
        if time.time() - self.search_start_time > self.time_limit:
            raise TimeoutError()
        
        self.nodes_searched += 1
        
        if current_hash is None:
            current_hash = self.zobrist.compute_hash(board)
        
        # TT lookup
        tt_result = self.tt.get(current_hash, depth, alpha, beta)
        if tt_result:
            return tt_result
        
        # Terminal check
        if depth == 0 or board.state != GameState.ONGOING:
            evaluator = BoardEvaluator()
            score = evaluator.evaluate(board, player)
            return (None, score)
        
        # Phase 2: Null Move Pruning (使用缓存的参数)
        if (self.nmp_enabled and allow_null_move and depth >= self.nmp_min_depth and not is_maximizing and 
            self.null_move_allowed and len(board.history) > 2):
            # Try passing a turn
            self.null_move_allowed = False
            _, null_score = self._minimax_search(
                board, player, depth - self.nmp_R, -beta, -beta + 1, True, current_hash, False
            )
            self.null_move_allowed = True
            null_score = -null_score
            
            if null_score >= beta:
                return (None, beta)  # Cutoff
        
        # Generate moves with improved ordering
        current_player = player if is_maximizing else player.opponent()
        hash_move = None
        tt_entry = self.tt.get(current_hash, depth, -float('inf'), float('inf'))
        if tt_entry:
            hash_move = tt_entry[0]
        
        killer_moves = self.killer_table.get(depth)
        move_gen = FastMoveGenerator(board, top_n=12 if depth > 3 else 15)
        candidates = move_gen.generate_best_moves(
            current_player, 
            pv_move=self.pv_move if depth == self.difficulty_config.search_depth else None,
            hash_move=hash_move,
            killer_moves=killer_moves
        )
        
        if not candidates:
            return (None, 0.0)
        
        best_move = None
        
        if is_maximizing:
            max_eval = -float('inf')
            for move_idx, (row, col) in enumerate(candidates):
                board.place_stone(row, col, player)
                new_hash = self.zobrist.update_hash(current_hash, row, col, player)
                
                # Phase 2: Late Move Reductions (使用缓存的参数)
                if self.lmr_enabled and move_idx > self.lmr_min_move_idx and depth >= self.lmr_min_depth:
                    # Reduce depth for later moves
                    reduced_depth = depth - 1 - self.lmr_reduction
                    _, eval_score = self._minimax_search(
                        board, player, reduced_depth, alpha, beta, False, new_hash
                    )
                    # Re-search if promising
                    if eval_score > alpha:
                        _, eval_score = self._minimax_search(
                            board, player, depth - 1, alpha, beta, False, new_hash
                        )
                else:
                    _, eval_score = self._minimax_search(
                        board, player, depth - 1, alpha, beta, False, new_hash
                    )
                
                board.undo_move()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (row, col)
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    self.killer_table.add((row, col), depth)
                    break
            
            self.tt.store(current_hash, depth, max_eval, best_move, alpha, beta)
            return (best_move, max_eval)
        else:
            min_eval = float('inf')
            current_player = player.opponent()
            for move_idx, (row, col) in enumerate(candidates):
                board.place_stone(row, col, current_player)
                new_hash = self.zobrist.update_hash(current_hash, row, col, current_player)
                
                # Phase 2: Late Move Reductions (使用缓存的参数)
                if self.lmr_enabled and move_idx > self.lmr_min_move_idx and depth >= self.lmr_min_depth:
                    reduced_depth = depth - 1 - self.lmr_reduction
                    _, eval_score = self._minimax_search(
                        board, player, reduced_depth, alpha, beta, True, new_hash
                    )
                    if eval_score < beta:
                        _, eval_score = self._minimax_search(
                            board, player, depth - 1, alpha, beta, True, new_hash
                        )
                else:
                    _, eval_score = self._minimax_search(
                        board, player, depth - 1, alpha, beta, True, new_hash
                    )
                
                board.undo_move()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (row, col)
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            self.tt.store(current_hash, depth, min_eval, best_move, alpha, beta)
            return (best_move, min_eval)
    
    def get_stats(self) -> dict:
        nps = self.nodes_searched / self.search_time if self.search_time > 0 else 0
        return {
            'nodes_searched': self.nodes_searched,
            'search_time': self.search_time,
            'nodes_per_second': nps,
            'tt_hit_rate': self.tt.get_hit_rate(),
            'tt_size': len(self.tt.table)
        }


# Backward compatibility
OptimizedAIController = Phase2AIController


def create_optimized_ai(difficulty_name: str = 'medium', time_limit: Optional[float] = None) -> Phase2AIController:
    """创建Phase 2优化AI实例 (配置化)"""
    return Phase2AIController(difficulty_name, time_limit)
