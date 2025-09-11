"""
国际象棋评估函数
用于AI算法的位置评估
"""
import numpy as np
import sys
import os
from typing import Dict, Tuple

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.board import ChessBoard
from game.pieces import PieceType, PieceColor

class ChessEvaluator:
    """国际象棋位置评估器"""
    
    def __init__(self):
        # 棋子基础价值
        self.piece_values = {
            PieceType.PAWN: 100,
            PieceType.KNIGHT: 320,
            PieceType.BISHOP: 330,
            PieceType.ROOK: 500,
            PieceType.QUEEN: 900,
            PieceType.KING: 20000
        }
        
        # 位置评估表 (从白方视角)
        self.position_tables = self._init_position_tables()
    
    def _init_position_tables(self) -> Dict:
        """初始化位置评估表"""
        
        # 兵的位置价值表
        pawn_table = np.array([
            [0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5,  5, 10, 25, 25, 10,  5,  5],
            [0,  0,  0, 20, 20,  0,  0,  0],
            [5, -5,-10,  0,  0,-10, -5,  5],
            [5, 10, 10,-20,-20, 10, 10,  5],
            [0,  0,  0,  0,  0,  0,  0,  0]
        ])
        
        # 马的位置价值表
        knight_table = np.array([
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ])
        
        # 象的位置价值表
        bishop_table = np.array([
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ])
        
        # 车的位置价值表
        rook_table = np.array([
            [0,  0,  0,  0,  0,  0,  0,  0],
            [5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [0,  0,  0,  5,  5,  0,  0,  0]
        ])
        
        # 后的位置价值表
        queen_table = np.array([
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [-5,  0,  5,  5,  5,  5,  0, -5],
            [0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ])
        
        # 王的位置价值表 (开局/中局)
        king_middle_table = np.array([
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [20, 20,  0,  0,  0,  0, 20, 20],
            [20, 30, 10,  0,  0, 10, 30, 20]
        ])
        
        # 王的位置价值表 (残局)
        king_end_table = np.array([
            [-50,-40,-30,-20,-20,-30,-40,-50],
            [-30,-20,-10,  0,  0,-10,-20,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-30,  0,  0,  0,  0,-30,-30],
            [-50,-30,-30,-30,-30,-30,-30,-50]
        ])
        
        return {
            PieceType.PAWN: pawn_table,
            PieceType.KNIGHT: knight_table,
            PieceType.BISHOP: bishop_table,
            PieceType.ROOK: rook_table,
            PieceType.QUEEN: queen_table,
            PieceType.KING: king_middle_table,
            'KING_END': king_end_table
        }
    
    def evaluate_position(self, board: ChessBoard) -> float:
        """评估当前位置"""
        if board.game_over:
            if board.winner == PieceColor.WHITE:
                return 9999
            elif board.winner == PieceColor.BLACK:
                return -9999
            else:
                return 0  # 平局
        
        score = 0
        
        # 材料评估
        score += self._evaluate_material(board)
        
        # 位置评估
        score += self._evaluate_position(board)
        
        # 机动性评估
        score += self._evaluate_mobility(board)
        
        # 王的安全性评估
        score += self._evaluate_king_safety(board)
        
        # 兵结构评估
        score += self._evaluate_pawn_structure(board)
        
        return score
    
    def _evaluate_material(self, board: ChessBoard) -> float:
        """材料评估"""
        white_material = 0
        black_material = 0
        
        for piece in board.pieces.values():
            value = self.piece_values[piece.piece_type]
            if piece.color == PieceColor.WHITE:
                white_material += value
            else:
                black_material += value
        
        return white_material - black_material
    
    def _evaluate_position(self, board: ChessBoard) -> float:
        """位置评估"""
        score = 0
        is_endgame = self._is_endgame(board)
        
        for position, piece in board.pieces.items():
            x, y = position
            piece_table = self.position_tables[piece.piece_type]
            
            # 对于王，根据游戏阶段选择不同的表
            if piece.piece_type == PieceType.KING and is_endgame:
                piece_table = self.position_tables['KING_END']
            
            if piece.color == PieceColor.WHITE:
                score += piece_table[y][x]
            else:
                # 对黑方，翻转棋盘
                score -= piece_table[7-y][x]
        
        return score
    
    def _evaluate_mobility(self, board: ChessBoard) -> float:
        """机动性评估"""
        white_mobility = 0
        black_mobility = 0
        
        # 计算白方的合法移动数
        if board.current_player == PieceColor.WHITE:
            white_mobility = len(list(board.board.legal_moves))
        
        # 切换到黑方计算合法移动数
        temp_board = board.board.copy()
        temp_board.turn = not temp_board.turn
        black_mobility = len(list(temp_board.legal_moves))
        
        return (white_mobility - black_mobility) * 10
    
    def _evaluate_king_safety(self, board: ChessBoard) -> float:
        """王的安全性评估"""
        score = 0
        
        # 简单的王安全评估
        white_king_pos = board.get_king_position(PieceColor.WHITE)
        black_king_pos = board.get_king_position(PieceColor.BLACK)
        
        if white_king_pos and black_king_pos:
            # 检查王是否被将军
            if board.is_in_check(PieceColor.WHITE):
                score -= 50
            if board.is_in_check(PieceColor.BLACK):
                score += 50
        
        return score
    
    def _evaluate_pawn_structure(self, board: ChessBoard) -> float:
        """兵结构评估"""
        score = 0
        white_pawns = []
        black_pawns = []
        
        # 收集兵的位置
        for position, piece in board.pieces.items():
            if piece.piece_type == PieceType.PAWN:
                if piece.color == PieceColor.WHITE:
                    white_pawns.append(position)
                else:
                    black_pawns.append(position)
        
        # 评估重叠兵（同一列有多个兵）
        white_files = [pos[0] for pos in white_pawns]
        black_files = [pos[0] for pos in black_pawns]
        
        for file in range(8):
            white_count = white_files.count(file)
            black_count = black_files.count(file)
            
            if white_count > 1:
                score -= (white_count - 1) * 20  # 重叠兵扣分
            if black_count > 1:
                score += (black_count - 1) * 20
        
        # 评估孤立兵
        for pos in white_pawns:
            if self._is_isolated_pawn(pos, white_pawns):
                score -= 25
        
        for pos in black_pawns:
            if self._is_isolated_pawn(pos, black_pawns):
                score += 25
        
        return score
    
    def _is_isolated_pawn(self, pawn_pos: Tuple[int, int], same_color_pawns: list) -> bool:
        """检查是否是孤立兵"""
        x, y = pawn_pos
        adjacent_files = [x-1, x+1]
        
        for pos in same_color_pawns:
            if pos[0] in adjacent_files:
                return False
        
        return True
    
    def _is_endgame(self, board: ChessBoard) -> bool:
        """判断是否进入残局"""
        # 简单的残局判断：后不在棋盘上或棋子总数较少
        queens = sum(1 for piece in board.pieces.values() if piece.piece_type == PieceType.QUEEN)
        total_pieces = len(board.pieces)
        
        return queens == 0 or total_pieces <= 12
