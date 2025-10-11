"""Tests for the optimized Python AI controller."""

from gamecenter.gomoku.ai_engine import OptimizedAIController
from gamecenter.gomoku.game_logic import Board, Player


def test_python_ai_returns_valid_move() -> None:
    """AI should return a legal move for a non-terminal position."""
    ai = OptimizedAIController(difficulty="easy", time_limit=1.0)
    board = Board()
    board.place_stone(7, 7, Player.BLACK)

    move = ai.find_best_move(board, Player.WHITE)
    assert move is not None
    row, col = move
    assert board.is_valid_pos(row, col)
    assert board.is_empty(row, col)


def test_set_difficulty_updates_configuration() -> None:
    """Switching difficulty should update controller configuration."""
    ai = OptimizedAIController(difficulty="easy", time_limit=1.0)
    ai.set_difficulty("hard")

    assert ai.difficulty_name == "hard"
    assert ai.difficulty_config.search_depth >= 7
    assert ai.tt.max_size == ai.difficulty_config.transposition_table_size
