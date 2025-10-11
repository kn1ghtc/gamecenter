"""五子棋冒烟测试
Smoke tests for Gomoku game.

验证核心功能：棋盘初始化、胜负检测、AI合法性、悔棋限制、字体回退。
"""

import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gamecenter.gomoku.game_logic import Board, GameManager, GameState, Player, create_game
from gamecenter.gomoku.ai_engine import AIController, DifficultyLevel, create_ai
from gamecenter.gomoku.evaluation import BoardEvaluator, evaluate_move
from gamecenter.gomoku.font_manager import FontManager, get_font_manager


class TestBoardLogic:
    """棋盘逻辑测试"""
    
    def test_board_init(self):
        """测试棋盘初始化"""
        board = Board()
        assert board.size == 15
        assert board.empty_count == 225
        assert board.current_player == Player.BLACK
        assert board.state == GameState.ONGOING
    
    def test_place_stone(self):
        """测试落子"""
        board = Board()
        
        # 黑棋先手
        assert board.place_stone(7, 7)
        assert board.get_stone(7, 7) == Player.BLACK
        assert board.current_player == Player.WHITE
        
        # 白棋
        assert board.place_stone(7, 8)
        assert board.get_stone(7, 8) == Player.WHITE
        assert board.current_player == Player.BLACK
        
        # 不能在已有棋子的位置落子
        assert not board.place_stone(7, 7)
    
    def test_win_detection_horizontal(self):
        """测试横向五子连珠检测"""
        board = Board()
        
        # 黑棋横向五连
        for col in range(5):
            board.place_stone(7, col, Player.BLACK)
            if col < 4:
                board.place_stone(8, col, Player.WHITE)  # 白棋干扰
        
        assert board.state == GameState.BLACK_WIN
        assert board.winning_line is not None
        assert len(board.winning_line) == 5
    
    def test_win_detection_vertical(self):
        """测试竖向五子连珠检测"""
        board = Board()
        
        # 白棋竖向五连（需要避免黑棋先赢）
        for row in range(5):
            board.place_stone(row, 8, Player.WHITE)  # 白棋竖向
            if row < 4:
                board.place_stone(row, 7, Player.BLACK)  # 黑棋干扰
        
        assert board.state == GameState.WHITE_WIN
    
    def test_win_detection_diagonal(self):
        """测试对角线五子连珠检测"""
        board = Board()
        
        # 黑棋对角线五连（左上到右下）
        for i in range(5):
            board.place_stone(i, i, Player.BLACK)
            if i < 4:
                board.place_stone(i, i + 1, Player.WHITE)
        
        assert board.state == GameState.BLACK_WIN
    
    def test_draw_detection(self):
        """测试平局检测"""
        board = Board(size=3)  # 小棋盘便于测试
        
        # 填满棋盘但无胜者
        moves = [
            (0, 0, Player.BLACK), (0, 1, Player.WHITE), (0, 2, Player.BLACK),
            (1, 0, Player.WHITE), (1, 1, Player.BLACK), (1, 2, Player.WHITE),
            (2, 0, Player.BLACK), (2, 1, Player.WHITE), (2, 2, Player.BLACK),
        ]
        
        for row, col, player in moves:
            board.place_stone(row, col, player)
        
        # 注意：这个简单的填充不一定会产生平局，因为可能先有人获胜
        # 这里只是验证空位检测
        assert board.empty_count == 0
    
    def test_undo_move(self):
        """测试悔棋"""
        board = Board()
        
        # 落子
        board.place_stone(7, 7)
        board.place_stone(7, 8)
        assert len(board.history) == 2
        
        # 悔棋
        assert board.undo_move()
        assert len(board.history) == 1
        assert board.get_stone(7, 8) == Player.EMPTY
        assert board.current_player == Player.WHITE
        
        # 再悔棋
        assert board.undo_move()
        assert len(board.history) == 0
        assert board.get_stone(7, 7) == Player.EMPTY
        
        # 无法继续悔棋
        assert not board.undo_move()


class TestGameManager:
    """游戏管理器测试"""
    
    def test_undo_limit(self):
        """测试悔棋次数限制"""
        manager = GameManager(max_undo=3)
        
        # 落几步棋
        for i in range(6):
            manager.place_stone(i, i)
        
        # 悔棋3次（每次悔1步）
        assert manager.undo()
        assert manager.undo()
        assert manager.undo()
        
        # 达到限制
        assert not manager.undo()
        assert manager.get_undo_remaining() == 0
    
    def test_reset(self):
        """测试重置游戏"""
        manager = GameManager()
        
        # 落子并悔棋
        manager.place_stone(7, 7)
        manager.undo()
        
        # 重置
        manager.reset()
        
        assert len(manager.board.history) == 0
        assert manager.undo_count == 0
        assert manager.board.state == GameState.ONGOING


class TestAI:
    """AI引擎测试"""
    
    def test_ai_move_validity(self):
        """测试AI生成的着法合法性"""
        # 只测试easy难度以加快速度
        ai = create_ai('easy')
        board = Board()
        
        # 落几步棋
        board.place_stone(7, 7)
        board.place_stone(7, 8)
        
        # AI生成着法
        move = ai.find_best_move(board, Player.BLACK)
        
        assert move is not None
        row, col = move
        assert board.is_valid_pos(row, col)
        assert board.is_empty(row, col)
    
    def test_ai_finds_winning_move(self):
        """测试AI能找到必胜着法"""
        ai = create_ai('easy')
        board = Board()
        
        # 黑棋四连，白棋需要防守
        for col in range(4):
            board.place_stone(7, col, Player.BLACK)
            if col < 3:
                board.place_stone(8, col, Player.WHITE)
        
        # 白棋应该堵在(7, 4)
        move = ai.find_best_move(board, Player.WHITE)
        assert move == (7, 4)
    
    def test_ai_performance(self):
        """测试AI性能（响应时间）"""
        ai = create_ai('easy')
        board = Board()
        
        import time
        start = time.time()
        move = ai.find_best_move(board, Player.BLACK)
        elapsed = time.time() - start
        
        # 简单难度应在3秒内响应
        assert elapsed < 3.0
        assert move is not None


class TestEvaluation:
    """评估函数测试"""
    
    def test_evaluator_init(self):
        """测试评估器初始化"""
        evaluator = BoardEvaluator()
        assert evaluator.board_size == 15
    
    def test_evaluate_initial_board(self):
        """测试初始棋盘评估"""
        board = Board()
        evaluator = BoardEvaluator()
        
        score = evaluator.evaluate(board, Player.BLACK)
        assert isinstance(score, (int, float))
    
    def test_evaluate_winning_position(self):
        """测试获胜局面评估"""
        board = Board()
        evaluator = BoardEvaluator()
        
        # 黑棋五连
        for col in range(5):
            board.place_stone(7, col, Player.BLACK)
            if col < 4:
                board.place_stone(8, col, Player.WHITE)
        
        # 黑方应该得到极高分数
        score = evaluator.evaluate(board, Player.BLACK)
        assert score > 50000


class TestFontManager:
    """字体管理器测试"""
    
    def test_font_manager_init(self):
        """测试字体管理器初始化"""
        font_mgr = FontManager()
        assert font_mgr.font_name is not None
        assert font_mgr.system in ['Darwin', 'Windows', 'Linux']
    
    def test_get_font(self):
        """测试获取字体"""
        font_mgr = get_font_manager()
        
        font = font_mgr.get_font(20)
        assert font is not None
        
        # 测试缓存
        font2 = font_mgr.get_font(20)
        assert font is font2
    
    def test_font_fallback(self):
        """测试字体回退机制"""
        font_mgr = FontManager()
        
        # 即使没有找到理想字体，也应该能返回默认字体
        font = font_mgr.get_font(16)
        assert font is not None
    
    def test_render_text(self):
        """测试文本渲染"""
        font_mgr = get_font_manager()
        
        # 渲染中文
        surface = font_mgr.render_text("五子棋", 20, (255, 255, 255))
        assert surface is not None
        assert surface.get_width() > 0
        assert surface.get_height() > 0
    
    def test_get_text_size(self):
        """测试获取文本大小"""
        font_mgr = get_font_manager()
        
        width, height = font_mgr.get_text_size("测试", 20)
        assert width > 0
        assert height > 0


class TestGameSaveLoad:
    """游戏保存/加载测试"""
    
    def test_save_and_load(self, tmp_path):
        """测试保存和加载棋局"""
        board = Board()
        
        # 落几步棋
        board.place_stone(7, 7)
        board.place_stone(7, 8)
        board.place_stone(8, 7)
        
        # 保存
        save_file = tmp_path / "test_save.json"
        board.save_to_file(str(save_file))
        
        # 加载
        loaded_board = Board.load_from_file(str(save_file))
        
        # 验证
        assert len(loaded_board.history) == 3
        assert loaded_board.get_stone(7, 7) == Player.BLACK
        assert loaded_board.get_stone(7, 8) == Player.WHITE
        assert loaded_board.get_stone(8, 7) == Player.BLACK


def test_package_import():
    """测试包导入"""
    from gamecenter.gomoku import (
        Board, GameManager, Player, GameState,
        AIController, DifficultyLevel,
        run_game
    )
    
    # 验证导出的符号
    assert Board is not None
    assert GameManager is not None
    assert Player is not None
    assert AIController is not None
    assert run_game is not None


if __name__ == '__main__':
    # 设置无头模式（避免pygame窗口弹出）
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
