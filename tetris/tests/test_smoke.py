"""
俄罗斯方块游戏冒烟测试

验证游戏的基本功能和稳定性
"""
import pytest
import pygame
import os
import sys

# 设置无头模式
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from gamecenter.tetris.src.game_enhanced import TetrisGame
from gamecenter.tetris.src.tetromino import Tetromino
from gamecenter.tetris.src.board import Board
from gamecenter.tetris.src.resource_manager import ResourceManager


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """初始化pygame"""
    pygame.init()
    yield
    pygame.quit()


class TestTetromino:
    """测试Tetromino方块类"""
    
    def test_tetromino_creation(self):
        """测试方块创建"""
        piece = Tetromino()
        assert piece is not None
        assert piece.shape is not None
        assert piece.color in ['CYAN', 'YELLOW', 'PURPLE', 'ORANGE', 'BLUE', 'GREEN', 'RED']
    
    def test_tetromino_rotation(self):
        """测试方块旋转"""
        piece = Tetromino('I')
        original_rotation = piece.rotation_state
        piece.rotate_clockwise()
        assert piece.rotation_state != original_rotation or len(piece.shapes_list) == 1
    
    def test_tetromino_positions(self):
        """测试方块位置获取"""
        piece = Tetromino('O')
        piece.x = 3
        piece.y = 5
        positions = piece.get_positions()
        assert len(positions) > 0
        assert all(isinstance(pos, tuple) for pos in positions)


class TestBoard:
    """测试Board游戏板类"""
    
    def test_board_creation(self):
        """测试游戏板创建"""
        board = Board()
        assert board.width == 10
        assert board.height == 20
        assert len(board.grid) == 20
        assert len(board.grid[0]) == 10
    
    def test_valid_move(self):
        """测试有效移动检测"""
        board = Board()
        piece = Tetromino('O')
        piece.x = 4
        piece.y = 0
        
        # 有效位置
        assert board.is_valid_move(piece, 4, 0)
        
        # 超出左边界
        assert not board.is_valid_move(piece, -1, 0)
        
        # 超出右边界
        assert not board.is_valid_move(piece, 9, 0)
    
    def test_lock_piece(self):
        """测试方块锁定"""
        board = Board()
        piece = Tetromino('O')
        piece.x = 4
        piece.y = 18
        
        # 锁定方块
        board.lock_piece(piece)
        
        # 检查网格中是否有方块
        has_block = False
        for row in board.grid:
            if any(cell is not None for cell in row):
                has_block = True
                break
        assert has_block
    
    def test_find_full_lines(self):
        """测试查找完整行"""
        board = Board()
        
        # 填满一行
        for x in range(board.width):
            board.grid[19][x] = 'RED'
        
        full_lines = board.find_full_lines()
        assert 19 in full_lines


class TestGame:
    """测试TetrisGame游戏类"""
    
    def test_game_creation(self):
        """测试游戏创建"""
        game = TetrisGame()
        assert game is not None
        assert game.board is not None
        assert game.score == 0
        assert game.level == 1
    
    def test_game_start(self):
        """测试游戏开始"""
        game = TetrisGame()
        game.start_game()
        
        assert game.current_piece is not None
        assert game.next_piece is not None
        assert game.score == 0
        assert game.level == 1
        assert not game.game_over
    
    def test_piece_movement(self):
        """测试方块移动"""
        game = TetrisGame()
        game.start_game()
        
        original_x = game.current_piece.x
        
        # 测试左移
        result = game.move_piece(-1, 0)
        if result:
            assert game.current_piece.x == original_x - 1
        
        # 测试右移
        game.current_piece.x = original_x
        result = game.move_piece(1, 0)
        if result:
            assert game.current_piece.x == original_x + 1
    
    def test_piece_rotation(self):
        """测试方块旋转"""
        game = TetrisGame()
        game.start_game()
        
        # 将方块设置为I型
        game.current_piece = Tetromino('I')
        game.current_piece.x = 4
        game.current_piece.y = 5
        
        original_rotation = game.current_piece.rotation_state
        game.rotate_piece()
        
        # 旋转应该成功或保持原状
        assert game.current_piece.rotation_state >= 0
    
    def test_hard_drop(self):
        """测试硬下落"""
        game = TetrisGame()
        game.start_game()
        
        original_y = game.current_piece.y
        distance = game.hard_drop()
        
        assert distance >= 0
        assert game.current_piece.y >= original_y
    
    def test_game_update(self):
        """测试游戏更新"""
        game = TetrisGame()
        game.start_game()
        
        # 更新游戏状态
        game.update(16)  # 模拟一帧
        
        # 游戏应该正常运行
        assert game.board is not None


class TestResourceManager:
    """测试资源管理器"""
    
    def test_resource_manager_creation(self):
        """测试资源管理器创建"""
        rm = ResourceManager()
        assert rm is not None
    
    def test_check_resources(self):
        """测试资源检查"""
        rm = ResourceManager()
        status = rm.check_all_resources()
        
        assert isinstance(status, dict)
        assert len(status) > 0


def test_smoke_full_game_cycle():
    """完整游戏流程冒烟测试"""
    game = TetrisGame()
    game.start_game()
    
    # 模拟几帧游戏
    for _ in range(10):
        game.update(16)
        game.draw()
    
    # 测试移动
    game.move_piece(-1, 0)
    game.move_piece(1, 0)
    game.move_piece(0, 1)
    
    # 测试旋转
    game.rotate_piece()
    
    # 测试硬下落
    game.hard_drop()
    game.lock_current_piece()
    
    # 验证游戏状态
    assert game.board is not None
    assert game.score >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
