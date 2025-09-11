"""
国际象棋棋子类实现
包含所有棋子的移动逻辑和规则
"""
import chess
from typing import List, Tuple, Optional
from enum import Enum

class PieceType(Enum):
    PAWN = 'pawn'
    ROOK = 'rook'
    KNIGHT = 'knight'
    BISHOP = 'bishop'
    QUEEN = 'queen'
    KING = 'king'

class PieceColor(Enum):
    WHITE = 'white'
    BLACK = 'black'

class ChessPiece:
    """棋子基类"""
    
    def __init__(self, piece_type: PieceType, color: PieceColor, position: Tuple[int, int]):
        self.piece_type = piece_type
        self.color = color
        self.position = position
        self.has_moved = False
        
    def __str__(self):
        return f"{self.color.value}_{self.piece_type.value}"
    
    def get_symbol(self) -> str:
        """获取棋子的Unicode符号"""
        symbols = {
            (PieceColor.WHITE, PieceType.KING): '♔',
            (PieceColor.WHITE, PieceType.QUEEN): '♕',
            (PieceColor.WHITE, PieceType.ROOK): '♖',
            (PieceColor.WHITE, PieceType.BISHOP): '♗',
            (PieceColor.WHITE, PieceType.KNIGHT): '♘',
            (PieceColor.WHITE, PieceType.PAWN): '♙',
            (PieceColor.BLACK, PieceType.KING): '♚',
            (PieceColor.BLACK, PieceType.QUEEN): '♛',
            (PieceColor.BLACK, PieceType.ROOK): '♜',
            (PieceColor.BLACK, PieceType.BISHOP): '♝',
            (PieceColor.BLACK, PieceType.KNIGHT): '♞',
            (PieceColor.BLACK, PieceType.PAWN): '♟',
        }
        return symbols.get((self.color, self.piece_type), '?')
    
    def get_piece_value(self) -> int:
        """获取棋子价值用于AI评估"""
        values = {
            PieceType.PAWN: 100,
            PieceType.KNIGHT: 320,
            PieceType.BISHOP: 330,
            PieceType.ROOK: 500,
            PieceType.QUEEN: 900,
            PieceType.KING: 20000
        }
        return values.get(self.piece_type, 0)

class PieceFactory:
    """棋子工厂类"""
    
    @staticmethod
    def create_piece(piece_type: str, color: str, position: Tuple[int, int]) -> ChessPiece:
        """根据类型和颜色创建棋子"""
        piece_type_enum = PieceType(piece_type.lower())
        color_enum = PieceColor(color.lower())
        return ChessPiece(piece_type_enum, color_enum, position)
    
    @staticmethod
    def create_initial_board() -> dict:
        """创建初始棋盘布局 - 修复坐标系统"""
        pieces = {}
        
        # 白方棋子 - 在棋盘底部 (y=0,1)
        # 第1排：主要棋子
        white_pieces = [
            ('rook', (0, 0)), ('knight', (1, 0)), ('bishop', (2, 0)), ('queen', (3, 0)),
            ('king', (4, 0)), ('bishop', (5, 0)), ('knight', (6, 0)), ('rook', (7, 0))
        ]
        
        for piece_type, position in white_pieces:
            pieces[position] = PieceFactory.create_piece(piece_type, 'white', position)
        
        # 第2排：白兵
        for col in range(8):
            pieces[(col, 1)] = PieceFactory.create_piece('pawn', 'white', (col, 1))
        
        # 黑方棋子 - 在棋盘顶部 (y=6,7)
        # 第7排：黑兵  
        for col in range(8):
            pieces[(col, 6)] = PieceFactory.create_piece('pawn', 'black', (col, 6))
            
        # 第8排：主要棋子
        black_pieces = [
            ('rook', (0, 7)), ('knight', (1, 7)), ('bishop', (2, 7)), ('queen', (3, 7)),
            ('king', (4, 7)), ('bishop', (5, 7)), ('knight', (6, 7)), ('rook', (7, 7))
        ]
        
        for piece_type, position in black_pieces:
            pieces[position] = PieceFactory.create_piece(piece_type, 'black', position)
        
        return pieces
