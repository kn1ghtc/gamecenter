import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from gamecenter.gomoku.main import GomokuGame, GameState
from gamecenter.gomoku.game_logic import Player


@pytest.fixture
def game_instance():
    game = GomokuGame()
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
