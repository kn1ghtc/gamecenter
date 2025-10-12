import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from gamecenter.gomoku.main import GomokuGame, GameState
from gamecenter.gomoku.game_logic import Player


@pytest.fixture
def game_instance(tmp_path):
    save_dir = tmp_path / "saves"
    session_path = tmp_path / "last_session.json"
    settings_path = tmp_path / "runtime_settings.json"
    game = GomokuGame(
        save_dir_override=save_dir,
        session_path_override=session_path,
        settings_path_override=settings_path,
    )
    yield game
    pygame.quit()


def test_sidebar_state_builds(game_instance):
    sidebar = game_instance._build_sidebar_state()
    assert sidebar.move_count == 0
    assert sidebar.game_mode_label.startswith("模式")
    assert sidebar.current_turn_text.startswith("当前回合")


def test_update_and_draw_cycle(game_instance, monkeypatch):
    monkeypatch.setattr(pygame.display, "flip", lambda: None)
    game_instance.update()
    game_instance.draw()
    assert game_instance.player_states[Player.BLACK].last_move is None


def test_format_move_output():
    assert GomokuGame._format_move((0, 0)) == "A1"
    assert GomokuGame._format_move((7, 7)) == "H8"
    assert GomokuGame._format_move(None) is None


def test_save_and_restore_session(tmp_path):
    save_dir = tmp_path / "saves"
    session_path = tmp_path / "last_session.json"
    settings_path = tmp_path / "runtime_settings.json"

    game = GomokuGame(
        save_dir_override=save_dir,
        session_path_override=session_path,
        settings_path_override=settings_path,
    )

    game.player_states[Player.BLACK].score = 2
    game.player_states[Player.WHITE].score = 1
    game.game_mode = 'pvp'
    game._sync_player_profiles()

    game.game_manager.place_stone(7, 7)
    game.game_manager.place_stone(7, 8)

    game._save_game()

    restored = GomokuGame(
        save_dir_override=save_dir,
        session_path_override=session_path,
        settings_path_override=settings_path,
    )

    try:
        assert restored.game_manager.board.history
        assert restored.player_states[Player.BLACK].score == 2
        assert restored.player_states[Player.WHITE].score == 1
        assert restored.game_mode == 'pvp'
    finally:
        pygame.quit()
