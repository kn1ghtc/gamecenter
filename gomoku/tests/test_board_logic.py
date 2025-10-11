"""Smoke tests for the core board and game manager logic."""

from gamecenter.gomoku.game_logic import Board, GameManager, GameState, Player


def test_board_initial_state() -> None:
    board = Board()
    assert board.size == 15
    assert board.current_player == Player.BLACK
    assert board.state == GameState.ONGOING


def test_place_stone_switches_player() -> None:
    board = Board()
    assert board.place_stone(7, 7, Player.BLACK)
    assert board.current_player == Player.WHITE
    assert not board.place_stone(7, 7, Player.WHITE)


def test_detects_horizontal_win() -> None:
    board = Board()
    for col in range(5):
        board.place_stone(7, col, Player.BLACK)
        if col < 4:
            board.place_stone(8, col, Player.WHITE)
    assert board.state == GameState.BLACK_WIN


def test_game_manager_undo_limit() -> None:
    manager = GameManager(max_undo=2)
    for i in range(4):
        manager.place_stone(i, i)
    assert manager.undo()
    assert manager.undo()
    assert not manager.undo()
