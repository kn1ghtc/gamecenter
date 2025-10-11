"""Tests for the AIEngineManager abstraction."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

import gamecenter.gomoku.ai_engine_manager as mgr_module
from gamecenter.gomoku import get_difficulty_config
from gamecenter.gomoku.ai_engine_manager import AIEngineManager, EngineType, create_ai_engine
from gamecenter.gomoku.game_logic import Board, Player


@dataclass
class DummyCppEngine:
    """Minimal stub emulating the C++ engine interface used in tests."""

    nodes_searched: int = 0
    search_time: float = 0.0

    def find_best_move(self, board: Board, player: Player, depth: int, time_limit: float):
        self.nodes_searched += 1
        self.search_time = 0.001
        return (0, 0)


@pytest.fixture(autouse=True)
def _configure_headless_env(monkeypatch):
    """Ensure pygame can initialise in headless environments if needed."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")


def test_auto_mode_falls_back_to_python(monkeypatch):
    """When C++ is unavailable the manager should fall back to Python engine."""
    monkeypatch.setattr(mgr_module, "CPP_AVAILABLE", False, raising=False)

    manager = AIEngineManager(engine_type=EngineType.AUTO, difficulty="easy")
    assert manager.current_engine_type == EngineType.PYTHON

    board = Board()
    board.place_stone(7, 7, Player.BLACK)
    move = manager.find_best_move(board, Player.WHITE)
    assert move is not None
    assert board.is_empty(*move)


def test_cpp_engine_is_selected_when_available(monkeypatch):
    """Explicit CPP selection should use the native engine when available."""
    monkeypatch.setattr(mgr_module, "CPP_AVAILABLE", True, raising=False)
    monkeypatch.setattr(mgr_module, "CppAIEngine", DummyCppEngine, raising=False)

    manager = AIEngineManager(engine_type=EngineType.CPP, difficulty="hard")
    assert manager.current_engine_type == EngineType.CPP
    assert manager._cpp_depth == get_difficulty_config("hard").search_depth

    board = Board()
    board.place_stone(7, 7, Player.BLACK)
    move = manager.find_best_move(board, Player.WHITE)
    assert move == (0, 0)


def test_create_ai_engine_supports_deprecated_alias(monkeypatch):
    """Factory should redirect deprecated python phase names to the Python engine."""
    monkeypatch.setattr(mgr_module, "CPP_AVAILABLE", False, raising=False)

    manager = create_ai_engine("python_phase2", "medium")
    assert manager.current_engine_type == EngineType.PYTHON


def test_custom_time_limit_is_preserved(monkeypatch):
    """Providing a custom time limit keeps the override after difficulty changes."""
    monkeypatch.setattr(mgr_module, "CPP_AVAILABLE", False, raising=False)

    manager = AIEngineManager(engine_type=EngineType.PYTHON, difficulty="medium", time_limit=2.0)
    assert manager.time_limit == 2.0

    manager.set_difficulty("hard")
    assert manager.time_limit == 2.0
    assert getattr(manager.engine, "time_limit") == 2.0
