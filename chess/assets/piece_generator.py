"""
创建简单的棋子图形
用于生成基础的棋子图像
"""
import pygame
import math
import os
from typing import Tuple

def create_piece_surface(piece_type: str, color: str, size: int = 64) -> pygame.Surface:
    """创建棋子表面"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # 颜色定义
    if color == 'white':
        piece_color = (240, 240, 240)
        outline_color = (0, 0, 0)
    else:
        piece_color = (40, 40, 40)
        outline_color = (255, 255, 255)
    
    center = (size // 2, size // 2)
    
    if piece_type == 'pawn':
        # 兵
        pygame.draw.circle(surface, piece_color, (center[0], center[1] - 8), size // 6)
        pygame.draw.rect(surface, piece_color, (center[0] - size//8, center[1] - 4, size//4, size//3))
        pygame.draw.circle(surface, outline_color, (center[0], center[1] - 8), size // 6, 2)
        pygame.draw.rect(surface, outline_color, (center[0] - size//8, center[1] - 4, size//4, size//3), 2)
        
    elif piece_type == 'rook':
        # 车
        rect_width = size // 2
        rect_height = size // 2
        rect = pygame.Rect(center[0] - rect_width//2, center[1] - rect_height//2, rect_width, rect_height)
        pygame.draw.rect(surface, piece_color, rect)
        pygame.draw.rect(surface, outline_color, rect, 2)
        
        # 城垛
        for i in range(3):
            x = center[0] - rect_width//2 + i * rect_width//3
            pygame.draw.rect(surface, piece_color, (x, center[1] - rect_height//2 - 8, rect_width//4, 8))
            pygame.draw.rect(surface, outline_color, (x, center[1] - rect_height//2 - 8, rect_width//4, 8), 1)
    
    elif piece_type == 'knight':
        # 马
        points = [
            (center[0] - 12, center[1] + 16),
            (center[0] - 8, center[1] - 12),
            (center[0] + 4, center[1] - 16),
            (center[0] + 12, center[1] - 8),
            (center[0] + 16, center[1] + 8),
            (center[0] + 8, center[1] + 16)
        ]
        pygame.draw.polygon(surface, piece_color, points)
        pygame.draw.polygon(surface, outline_color, points, 2)
    
    elif piece_type == 'bishop':
        # 象
        pygame.draw.circle(surface, piece_color, center, size // 4)
        pygame.draw.circle(surface, outline_color, center, size // 4, 2)
        
        # 十字
        pygame.draw.line(surface, outline_color, 
                        (center[0], center[1] - size//6), 
                        (center[0], center[1] + size//6), 3)
        pygame.draw.line(surface, outline_color, 
                        (center[0] - size//6, center[1]), 
                        (center[0] + size//6, center[1]), 3)
    
    elif piece_type == 'queen':
        # 后
        pygame.draw.circle(surface, piece_color, center, size // 3)
        pygame.draw.circle(surface, outline_color, center, size // 3, 2)
        
        # 皇冠
        for i in range(5):
            angle = i * math.pi * 2 / 5 - math.pi / 2
            x = center[0] + math.cos(angle) * size // 4
            y = center[1] + math.sin(angle) * size // 4
            pygame.draw.circle(surface, piece_color, (int(x), int(y)), 4)
            pygame.draw.circle(surface, outline_color, (int(x), int(y)), 4, 1)
    
    elif piece_type == 'king':
        # 王
        pygame.draw.circle(surface, piece_color, center, size // 3)
        pygame.draw.circle(surface, outline_color, center, size // 3, 2)
        
        # 十字
        cross_size = size // 8
        pygame.draw.line(surface, outline_color,
                        (center[0], center[1] - cross_size),
                        (center[0], center[1] + cross_size), 4)
        pygame.draw.line(surface, outline_color,
                        (center[0] - cross_size, center[1]),
                        (center[0] + cross_size, center[1]), 4)
    
    return surface

def generate_all_pieces(output_dir: str, size: int = 80):
    """生成所有棋子图片"""
    pygame.init()
    
    pieces = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
    colors = ['white', 'black']
    
    os.makedirs(output_dir, exist_ok=True)
    
    for color in colors:
        for piece in pieces:
            surface = create_piece_surface(piece, color, size)
            filename = f"{color}_{piece}.png"
            filepath = os.path.join(output_dir, filename)
            pygame.image.save(surface, filepath)
            print(f"Generated: {filename}")
    
    pygame.quit()

if __name__ == "__main__":
    # 生成棋子图片
    generate_all_pieces("pieces")
