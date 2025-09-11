"""
国际象棋棋盘渲染器
负责绘制棋盘、棋子和特效
"""
import pygame
import os
import sys
from typing import Dict, List, Tuple, Optional

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config.settings import COLORS, SQUARE_SIZE, BOARD_SIZE
from game.pieces import ChessPiece, PieceColor, PieceType

class ChessBoardRenderer:
    """棋盘渲染器"""
    
    def __init__(self, square_size: int = SQUARE_SIZE):
        self.square_size = square_size
        self.board_size = BOARD_SIZE * square_size
        self.piece_images = {}
        self.load_piece_images()
        
        # 渲染缓存
        self.board_surface = None
        self.piece_surfaces = {}
        
        # 动画系统
        self.animations = []
        
    def load_piece_images(self):
        """加载棋子图片"""
        # 修复路径问题
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        chess_root = os.path.dirname(current_file_dir)  # 上一级目录是chess根目录
        assets_path = os.path.join(chess_root, "assets", "pieces")
        
        pieces = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
        colors = ['white', 'black']
        
        for color in colors:
            for piece in pieces:
                filename = f"{color}_{piece}.png"
                filepath = os.path.join(assets_path, filename)
                
                try:
                    if os.path.exists(filepath):
                        image = pygame.image.load(filepath)
                        # 缩放到正确大小
                        scaled_image = pygame.transform.scale(image, (self.square_size - 8, self.square_size - 8))
                        self.piece_images[f"{color}_{piece}"] = scaled_image
                    else:
                        print(f"Warning: Could not find {filepath}")
                        # 创建占位符
                        placeholder = pygame.Surface((self.square_size - 8, self.square_size - 8))
                        placeholder.fill(COLORS['WHITE'] if color == 'white' else COLORS['BLACK'])
                        self.piece_images[f"{color}_{piece}"] = placeholder
                except pygame.error as e:
                    print(f"Warning: Could not load {filename}: {e}")
                    # 创建占位符
                    placeholder = pygame.Surface((self.square_size - 8, self.square_size - 8))
                    placeholder.fill(COLORS['WHITE'] if color == 'white' else COLORS['BLACK'])
                    self.piece_images[f"{color}_{piece}"] = placeholder
    
    def create_board_surface(self) -> pygame.Surface:
        """创建棋盘表面"""
        if self.board_surface is None:
            self.board_surface = pygame.Surface((self.board_size, self.board_size))
            
            for row in range(8):
                for col in range(8):
                    color = COLORS['LIGHT_SQUARE'] if (row + col) % 2 == 0 else COLORS['DARK_SQUARE']
                    rect = pygame.Rect(col * self.square_size, row * self.square_size, 
                                     self.square_size, self.square_size)
                    pygame.draw.rect(self.board_surface, color, rect)
                    
                    # 添加边框
                    pygame.draw.rect(self.board_surface, COLORS['BLACK'], rect, 1)
        
        return self.board_surface
    
    def render_board(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)):
        """渲染棋盘"""
        board_surface = self.create_board_surface()
        surface.blit(board_surface, offset)
        
        # 绘制坐标标签
        self.draw_coordinate_labels(surface, offset)
    
    def draw_coordinate_labels(self, surface: pygame.Surface, offset: Tuple[int, int]):
        """绘制坐标标签"""
        font = pygame.font.Font(None, 24)
        
        # 列标签 (a-h)
        for col in range(8):
            letter = chr(ord('a') + col)
            text = font.render(letter, True, COLORS['TEXT'])
            x = offset[0] + col * self.square_size + self.square_size // 2 - text.get_width() // 2
            y = offset[1] + self.board_size + 5
            surface.blit(text, (x, y))
        
        # 行标签 (1-8)
        for row in range(8):
            number = str(8 - row)
            text = font.render(number, True, COLORS['TEXT'])
            x = offset[0] - 25
            y = offset[1] + row * self.square_size + self.square_size // 2 - text.get_height() // 2
            surface.blit(text, (x, y))
    
    def render_pieces(self, surface: pygame.Surface, pieces: Dict[Tuple[int, int], ChessPiece], 
                     offset: Tuple[int, int] = (0, 0)):
        """渲染棋子"""
        for position, piece in pieces.items():
            self.render_piece(surface, piece, position, offset)
    
    def render_piece(self, surface: pygame.Surface, piece: ChessPiece, 
                    position: Tuple[int, int], offset: Tuple[int, int] = (0, 0)):
        """渲染单个棋子"""
        col, row = position
        piece_key = f"{piece.color.value}_{piece.piece_type.value}"
        
        if piece_key in self.piece_images:
            image = self.piece_images[piece_key]
            x = offset[0] + col * self.square_size + 4
            y = offset[1] + row * self.square_size + 4
            surface.blit(image, (x, y))
        else:
            # 文本回退
            self.render_piece_text(surface, piece, position, offset)
    
    def render_piece_text(self, surface: pygame.Surface, piece: ChessPiece, 
                         position: Tuple[int, int], offset: Tuple[int, int] = (0, 0)):
        """使用文本渲染棋子（回退方案）"""
        font = pygame.font.Font(None, 48)
        symbol = piece.get_symbol()
        text = font.render(symbol, True, COLORS['BLACK'])
        
        col, row = position
        x = offset[0] + col * self.square_size + self.square_size // 2 - text.get_width() // 2
        y = offset[1] + row * self.square_size + self.square_size // 2 - text.get_height() // 2
        surface.blit(text, (x, y))
    
    def render_highlights(self, surface: pygame.Surface, highlighted_squares: List[Tuple[int, int]], 
                         offset: Tuple[int, int] = (0, 0)):
        """渲染高亮方格"""
        for position in highlighted_squares:
            self.render_highlight(surface, position, COLORS['HIGHLIGHT'], offset)
    
    def render_move_hints(self, surface: pygame.Surface, move_hints: List[Tuple[int, int]], 
                         offset: Tuple[int, int] = (0, 0)):
        """渲染移动提示"""
        for position in move_hints:
            self.render_move_hint(surface, position, offset)
    
    def render_highlight(self, surface: pygame.Surface, position: Tuple[int, int], 
                        color: Tuple[int, int, int, int], offset: Tuple[int, int] = (0, 0)):
        """渲染高亮效果"""
        col, row = position
        # 创建带透明度的表面
        highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
        highlight_surface.fill(color)
        
        x = offset[0] + col * self.square_size
        y = offset[1] + row * self.square_size
        surface.blit(highlight_surface, (x, y))
    
    def render_move_hint(self, surface: pygame.Surface, position: Tuple[int, int], 
                        offset: Tuple[int, int] = (0, 0)):
        """渲染移动提示点"""
        col, row = position
        center_x = offset[0] + col * self.square_size + self.square_size // 2
        center_y = offset[1] + row * self.square_size + self.square_size // 2
        
        # 绘制半透明圆圈
        hint_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
        pygame.draw.circle(hint_surface, COLORS['MOVE_HINT'], 
                         (self.square_size // 2, self.square_size // 2), 8)
        
        x = offset[0] + col * self.square_size
        y = offset[1] + row * self.square_size
        surface.blit(hint_surface, (x, y))
    
    def render_last_move(self, surface: pygame.Surface, last_move: Dict, 
                        offset: Tuple[int, int] = (0, 0)):
        """渲染上一步移动"""
        if last_move:
            from_pos = last_move.get('from')
            to_pos = last_move.get('to')
            
            if from_pos:
                self.render_highlight(surface, from_pos, (255, 255, 0, 80), offset)
            if to_pos:
                self.render_highlight(surface, to_pos, (255, 255, 0, 120), offset)
    
    def render_check_warning(self, surface: pygame.Surface, king_position: Tuple[int, int], 
                           offset: Tuple[int, int] = (0, 0)):
        """渲染将军警告"""
        self.render_highlight(surface, king_position, COLORS['DANGER'], offset)
    
    def pixel_to_board_position(self, pixel_pos: Tuple[int, int], 
                               offset: Tuple[int, int] = (0, 0)) -> Optional[Tuple[int, int]]:
        """将像素坐标转换为棋盘位置"""
        x, y = pixel_pos
        x -= offset[0]
        y -= offset[1]
        
        if 0 <= x < self.board_size and 0 <= y < self.board_size:
            col = x // self.square_size
            row = y // self.square_size
            return (col, row)
        
        return None
    
    def board_position_to_pixel(self, board_pos: Tuple[int, int], 
                               offset: Tuple[int, int] = (0, 0)) -> Tuple[int, int]:
        """将棋盘位置转换为像素坐标"""
        col, row = board_pos
        x = offset[0] + col * self.square_size + self.square_size // 2
        y = offset[1] + row * self.square_size + self.square_size // 2
        return (x, y)

class AnimationManager:
    """动画管理器"""
    
    def __init__(self):
        self.animations = []
    
    def add_move_animation(self, piece: ChessPiece, from_pos: Tuple[int, int], 
                          to_pos: Tuple[int, int], duration: float = 0.3):
        """添加移动动画"""
        animation = {
            'type': 'move',
            'piece': piece,
            'from_pos': from_pos,
            'to_pos': to_pos,
            'start_time': pygame.time.get_ticks(),
            'duration': duration * 1000,  # 转换为毫秒
            'completed': False
        }
        self.animations.append(animation)
    
    def update(self, dt: float):
        """更新动画"""
        current_time = pygame.time.get_ticks()
        
        for animation in self.animations[:]:
            elapsed = current_time - animation['start_time']
            progress = min(elapsed / animation['duration'], 1.0)
            
            if progress >= 1.0:
                animation['completed'] = True
                self.animations.remove(animation)
    
    def render_animations(self, surface: pygame.Surface, renderer: ChessBoardRenderer, 
                         offset: Tuple[int, int] = (0, 0)):
        """渲染动画"""
        current_time = pygame.time.get_ticks()
        
        for animation in self.animations:
            if animation['type'] == 'move':
                elapsed = current_time - animation['start_time']
                progress = min(elapsed / animation['duration'], 1.0)
                
                # 计算插值位置
                from_pixel = renderer.board_position_to_pixel(animation['from_pos'], offset)
                to_pixel = renderer.board_position_to_pixel(animation['to_pos'], offset)
                
                current_x = from_pixel[0] + (to_pixel[0] - from_pixel[0]) * progress
                current_y = from_pixel[1] + (to_pixel[1] - from_pixel[1]) * progress
                
                # 渲染移动中的棋子
                piece = animation['piece']
                piece_key = f"{piece.color.value}_{piece.piece_type.value}"
                
                if piece_key in renderer.piece_images:
                    image = renderer.piece_images[piece_key]
                    x = current_x - image.get_width() // 2
                    y = current_y - image.get_height() // 2
                    surface.blit(image, (x, y))
    
    def is_animating(self) -> bool:
        """检查是否有动画正在播放"""
        return len(self.animations) > 0
