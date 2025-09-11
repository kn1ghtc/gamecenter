"""
基础AI实现 - Minimax算法与Alpha-Beta剪枝
"""
import time
import random
import copy
import sys
import os
from typing import Tuple, Optional, List

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.board import ChessBoard
from game.pieces import PieceColor
from ai.evaluation import ChessEvaluator

class BasicChessAI:
    """基础国际象棋AI - 使用Minimax算法"""
    
    def __init__(self, depth: int = 3, time_limit: float = 5.0):
        self.depth = depth
        self.time_limit = time_limit
        self.evaluator = ChessEvaluator()
        self.nodes_searched = 0
        self.start_time = 0
        self.best_move = None
        
        # 移动排序权重
        self.move_ordering_weights = {
            'capture': 1000,
            'check': 500,
            'castle': 300,
            'promotion': 800,
            'center_control': 100
        }
    
    def get_best_move(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """获取最佳移动"""
        self.start_time = time.time()
        self.nodes_searched = 0
        self.best_move = None
        
        legal_moves = self._get_all_legal_moves(board, color)
        if not legal_moves:
            return None
        
        # 如果只有一个合法移动，直接返回
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # 使用迭代深化搜索
        best_move = None
        for current_depth in range(1, self.depth + 1):
            if time.time() - self.start_time > self.time_limit * 0.8:
                break
            
            try:
                move = self._iterative_deepening(board, color, current_depth)
                if move:
                    best_move = move
            except TimeoutError:
                break
        
        return best_move or random.choice(legal_moves)
    
    def _iterative_deepening(self, board: ChessBoard, color: PieceColor, depth: int) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """迭代深化搜索"""
        alpha = float('-inf')
        beta = float('inf')
        best_move = None
        best_score = float('-inf') if color == PieceColor.WHITE else float('inf')
        
        legal_moves = self._get_all_legal_moves(board, color)
        ordered_moves = self._order_moves(board, legal_moves, color)
        
        for move in ordered_moves:
            if time.time() - self.start_time > self.time_limit:
                raise TimeoutError()
            
            from_pos, to_pos = move
            board_copy = self._make_move_copy(board, from_pos, to_pos)
            
            if color == PieceColor.WHITE:
                score = self._minimax(board_copy, depth - 1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                score = self._minimax(board_copy, depth - 1, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)
        
        return best_move
    
    def _minimax(self, board: ChessBoard, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """Minimax算法与Alpha-Beta剪枝"""
        self.nodes_searched += 1
        
        # 检查时间限制
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError()
        
        # 终止条件
        if depth == 0 or board.game_over:
            return self.evaluator.evaluate_position(board)
        
        current_color = PieceColor.WHITE if maximizing else PieceColor.BLACK
        legal_moves = self._get_all_legal_moves(board, current_color)
        
        if not legal_moves:
            return self.evaluator.evaluate_position(board)
        
        ordered_moves = self._order_moves(board, legal_moves, current_color)
        
        if maximizing:
            max_eval = float('-inf')
            for move in ordered_moves:
                from_pos, to_pos = move
                board_copy = self._make_move_copy(board, from_pos, to_pos)
                eval_score = self._minimax(board_copy, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-Beta剪枝
            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                from_pos, to_pos = move
                board_copy = self._make_move_copy(board, from_pos, to_pos)
                eval_score = self._minimax(board_copy, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-Beta剪枝
            return min_eval
    
    def _get_all_legal_moves(self, board: ChessBoard, color: PieceColor) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """获取所有合法移动"""
        legal_moves = []
        
        for position, piece in board.pieces.items():
            if piece.color == color:
                moves = board.get_legal_moves(position)
                for to_pos in moves:
                    legal_moves.append((position, to_pos))
        
        return legal_moves
    
    def _order_moves(self, board: ChessBoard, moves: List[Tuple[Tuple[int, int], Tuple[int, int]]], color: PieceColor) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """移动排序以提高Alpha-Beta剪枝效率"""
        def move_score(move):
            from_pos, to_pos = move
            score = 0
            
            # 吃子移动优先
            target_piece = board.get_piece_at(to_pos)
            if target_piece:
                attacker = board.get_piece_at(from_pos)
                # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
                victim_value = target_piece.get_piece_value()
                attacker_value = attacker.get_piece_value()
                score += self.move_ordering_weights['capture'] + victim_value - attacker_value
            
            # 中心控制
            x, y = to_pos
            if 2 <= x <= 5 and 2 <= y <= 5:
                score += self.move_ordering_weights['center_control']
            
            # 将军移动
            board_copy = self._make_move_copy(board, from_pos, to_pos)
            opponent_color = PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
            if board_copy.is_in_check(opponent_color):
                score += self.move_ordering_weights['check']
            
            return score
        
        return sorted(moves, key=move_score, reverse=True)
    
    def _make_move_copy(self, board: ChessBoard, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> ChessBoard:
        """创建移动后的棋盘副本"""
        board_copy = copy.deepcopy(board)
        board_copy.make_move(from_pos, to_pos)
        return board_copy
    
    def get_search_info(self) -> dict:
        """获取搜索信息"""
        search_time = time.time() - self.start_time if self.start_time else 0
        return {
            'nodes_searched': self.nodes_searched,
            'search_time': search_time,
            'nodes_per_second': self.nodes_searched / search_time if search_time > 0 else 0,
            'depth': self.depth
        }

class ImprovedBasicAI(BasicChessAI):
    """改进的基础AI，增加了一些优化"""
    
    def __init__(self, depth: int = 4, time_limit: float = 3.0):
        super().__init__(depth, time_limit)
        self.transposition_table = {}
        self.killer_moves = [[] for _ in range(depth)]
        
    def _minimax(self, board: ChessBoard, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """带转置表的Minimax"""
        # 转置表查找
        board_hash = hash(board.board.fen())
        if board_hash in self.transposition_table:
            entry = self.transposition_table[board_hash]
            if entry['depth'] >= depth:
                return entry['score']
        
        score = super()._minimax(board, depth, alpha, beta, maximizing)
        
        # 存储到转置表
        self.transposition_table[board_hash] = {
            'score': score,
            'depth': depth
        }
        
        return score
    
    def _order_moves(self, board: ChessBoard, moves: List[Tuple[Tuple[int, int], Tuple[int, int]]], color: PieceColor) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """改进的移动排序，包含killer moves"""
        scored_moves = []
        
        for move in moves:
            score = self._score_move(board, move, color)
            scored_moves.append((move, score))
        
        # 按分数排序
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in scored_moves]
    
    def _score_move(self, board: ChessBoard, move: Tuple[Tuple[int, int], Tuple[int, int]], color: PieceColor) -> float:
        """为移动打分"""
        from_pos, to_pos = move
        score = 0
        
        # 基础移动评分
        score += super()._order_moves(board, [move], color)[0] == move and 1000 or 0
        
        # Killer moves
        if move in self.killer_moves[min(self.depth - 1, len(self.killer_moves) - 1)]:
            score += 900
        
        # 历史表（可以后续添加）
        
        return score

# 为了兼容性，创建别名
BasicAI = BasicChessAI

class ImprovedBasicAI(BasicChessAI):
    """改进版基础AI - 更深的搜索和更好的评估"""
    
    def __init__(self, depth: int = 4, time_limit: float = 3.0):
        super().__init__(depth, time_limit)
        
        # 更激进的时间管理
        self.time_per_move_factor = 0.8
        
        # 开局库支持
        self.opening_book = {
            # 一些基本开局移动
            'e2e4': ['e7e5', 'c7c5', 'e7e6'],  # 王兵开局的回应
            'e2e3': ['d7d5', 'e7e6'],           # 其他开局
            'd2d4': ['d7d5', 'g8f6', 'e7e6'],   # 后兵开局
        }
    
    def get_best_move(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """获取最佳移动 - 改进版"""
        
        # 尝试使用开局库（前几步）
        if len(board.move_history) < 6:
            opening_move = self._try_opening_book(board, color)
            if opening_move:
                return opening_move
        
        # 调用基础AI的方法
        return super().get_best_move(board, color)
    
    def _try_opening_book(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """尝试使用开局库"""
        if not board.move_history:
            # 第一步，使用常见开局
            if color == PieceColor.WHITE:
                common_openings = [
                    ((4, 1), (4, 3)),  # e2-e4
                    ((3, 1), (3, 3)),  # d2-d4
                ]
                return random.choice(common_openings)
        
        # 简化的开局逻辑
        return None

# 为了兼容性，提供别名
BasicAI = BasicChessAI
