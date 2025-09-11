"""
国际象棋棋盘类实现
管理棋盘状态、棋子移动和游戏规则
"""
import chess
import copy
import sys
import os
from typing import List, Tuple, Optional, Dict, Set

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.pieces import ChessPiece, PieceFactory, PieceColor, PieceType

class ChessBoard:
    """国际象棋棋盘类"""
    
    def __init__(self):
        self.board = chess.Board()  # 使用python-chess库进行规则验证
        self.pieces = PieceFactory.create_initial_board()
        self.move_history = []
        self.captured_pieces = {'white': [], 'black': []}
        self.current_player = PieceColor.WHITE
        self.game_over = False
        self.winner = None
        
    def get_piece_at(self, position: Tuple[int, int]) -> Optional[ChessPiece]:
        """获取指定位置的棋子"""
        return self.pieces.get(position)
    
    def is_valid_position(self, position: Tuple[int, int]) -> bool:
        """检查位置是否在棋盘范围内"""
        x, y = position
        return 0 <= x < 8 and 0 <= y < 8
    
    def position_to_chess_notation(self, position: Tuple[int, int]) -> str:
        """将坐标转换为国际象棋记谱法
        我们的坐标系统：(0,0)在左上角，(7,7)在右下角
        象棋坐标系统：a1在左下角，h8在右上角
        """
        x, y = position
        return chr(ord('a') + x) + str(y + 1)
    
    def chess_notation_to_position(self, notation: str) -> Tuple[int, int]:
        """将国际象棋记谱法转换为坐标"""
        x = ord(notation[0]) - ord('a')
        y = int(notation[1]) - 1
        return (x, y)
    
    def is_square_attacked(self, position: Tuple[int, int], by_color: PieceColor) -> bool:
        """检查指定位置是否被指定颜色的棋子攻击"""
        chess_pos = self.position_to_chess_notation(position)
        square = getattr(chess, chess_pos.upper())
        
        # 切换到攻击方的视角
        temp_board = copy.deepcopy(self.board)
        temp_board.turn = (by_color == PieceColor.WHITE)
        
        return temp_board.is_attacked_by(chess.WHITE if by_color == PieceColor.WHITE else chess.BLACK, square)
    
    def get_legal_moves(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """获取指定位置棋子的所有合法移动"""
        piece = self.get_piece_at(position)
        if not piece or piece.color != self.current_player:
            return []
        
        legal_moves = []
        from_square = self.position_to_chess_notation(position)
        
        try:
            from_chess_square = getattr(chess, from_square.upper())
            
            for move in self.board.legal_moves:
                if move.from_square == from_chess_square:
                    to_pos = self.chess_notation_to_position(chess.square_name(move.to_square))
                    legal_moves.append(to_pos)
        except AttributeError:
            pass
        
        return legal_moves
    
    def make_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], promotion_piece: str = None) -> bool:
        """执行棋子移动
        
        Args:
            from_pos: 起始位置
            to_pos: 目标位置  
            promotion_piece: 升变棋子类型 ('queen', 'rook', 'bishop', 'knight')
        """
        piece = self.get_piece_at(from_pos)
        
        if not piece or piece.color != self.current_player:
            return False
        
        # 使用python-chess验证移动的合法性
        from_square = self.position_to_chess_notation(from_pos)
        to_square = self.position_to_chess_notation(to_pos)
        
        try:
            from_chess_square = getattr(chess, from_square.upper())
            to_chess_square = getattr(chess, to_square.upper())
            
            # 检查是否是兵升变
            promotion = None
            if (piece.piece_type.name.lower() == 'pawn' and 
                ((piece.color.name.lower() == 'white' and to_pos[1] == 7) or
                 (piece.color.name.lower() == 'black' and to_pos[1] == 0))):
                # 兵升变 - 默认升变为皇后
                if promotion_piece is None:
                    promotion_piece = 'queen'
                
                promotion_map = {
                    'queen': chess.QUEEN,
                    'rook': chess.ROOK,
                    'bishop': chess.BISHOP,
                    'knight': chess.KNIGHT
                }
                promotion = promotion_map.get(promotion_piece, chess.QUEEN)
            
            move = chess.Move(from_chess_square, to_chess_square, promotion=promotion)
            
            if move in self.board.legal_moves:
                # 记录被吃的棋子
                captured_piece = self.get_piece_at(to_pos)
                if captured_piece:
                    self.captured_pieces[captured_piece.color.value].append(captured_piece)
                
                # 在推入移动前获取记谱法
                move_notation = self.board.san(move)
                
                # 执行移动
                self.board.push(move)
                
                # 更新我们的棋子状态
                if promotion:
                    # 升变：创建新的棋子
                    from game.pieces import PieceFactory
                    new_piece = PieceFactory.create_piece(promotion_piece, piece.color.value, to_pos)
                    self.pieces[to_pos] = new_piece
                else:
                    # 普通移动
                    self.pieces[to_pos] = piece
                    piece.position = to_pos
                    piece.has_moved = True
                
                del self.pieces[from_pos]
                
                # 记录移动历史
                move_record = {
                    'from': from_pos,
                    'to': to_pos,
                    'piece': piece,
                    'captured': captured_piece,
                    'notation': move_notation
                }
                self.move_history.append(move_record)
                
                # 切换当前玩家
                self.current_player = PieceColor.BLACK if self.current_player == PieceColor.WHITE else PieceColor.WHITE
                
                # 检查游戏结束状态
                self._check_game_over()
                
                return True
        except (AttributeError, ValueError):
            pass
        
        return False
    
    def undo_move(self) -> bool:
        """撤销上一步移动"""
        if not self.move_history:
            return False
        
        last_move = self.move_history.pop()
        self.board.pop()
        
        # 恢复棋子位置
        piece = last_move['piece']
        self.pieces[last_move['from']] = piece
        piece.position = last_move['from']
        
        if last_move['to'] in self.pieces:
            del self.pieces[last_move['to']]
        
        # 恢复被吃的棋子
        if last_move['captured']:
            captured = last_move['captured']
            self.pieces[last_move['to']] = captured
            self.captured_pieces[captured.color.value].remove(captured)
        
        # 切换当前玩家
        self.current_player = PieceColor.BLACK if self.current_player == PieceColor.WHITE else PieceColor.WHITE
        
        # 重置游戏状态
        self.game_over = False
        self.winner = None
        
        return True
    
    def _check_game_over(self):
        """检查游戏是否结束"""
        if self.board.is_checkmate():
            self.game_over = True
            self.winner = PieceColor.BLACK if self.current_player == PieceColor.WHITE else PieceColor.WHITE
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition():
            self.game_over = True
            self.winner = None  # 平局
    
    def is_in_check(self, color: PieceColor) -> bool:
        """检查指定颜色的王是否被将军"""
        return self.board.is_check()
    
    def get_king_position(self, color: PieceColor) -> Optional[Tuple[int, int]]:
        """获取指定颜色王的位置"""
        for position, piece in self.pieces.items():
            if piece.piece_type == PieceType.KING and piece.color == color:
                return position
        return None
    
    def get_board_state(self) -> Dict:
        """获取当前棋盘状态用于AI分析"""
        return {
            'pieces': copy.deepcopy(self.pieces),
            'current_player': self.current_player,
            'move_history': copy.deepcopy(self.move_history),
            'captured_pieces': copy.deepcopy(self.captured_pieces),
            'in_check': self.is_in_check(self.current_player),
            'game_over': self.game_over,
            'winner': self.winner,
            'fen': self.board.fen()
        }
    
    def get_all_pieces_of_color(self, color: PieceColor) -> List[Tuple[Tuple[int, int], ChessPiece]]:
        """获取指定颜色的所有棋子"""
        return [(pos, piece) for pos, piece in self.pieces.items() if piece.color == color]
    
    def evaluate_position(self) -> float:
        """评估当前位置（简单的材料评估）"""
        white_value = sum(piece.get_piece_value() for piece in self.pieces.values() if piece.color == PieceColor.WHITE)
        black_value = sum(piece.get_piece_value() for piece in self.pieces.values() if piece.color == PieceColor.BLACK)
        return white_value - black_value
    
    def is_game_over(self) -> bool:
        """检查游戏是否结束"""
        return self.game_over or self.board.is_game_over()
    
    def is_checkmate(self) -> bool:
        """检查是否将死"""
        return self.board.is_checkmate()
    
    def is_stalemate(self) -> bool:
        """检查是否和棋（逼和）"""
        return self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition()
