"""Smoke tests for Military Chess game modules."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from gamecenter.militaryChess import (
    create_logic_state, GameState, Player, GameTermination,
    AIController, SettingsManager
)


def test_basic_game_creation():
    """Test basic game state creation and initial setup."""
    state = create_logic_state(seed=42, randomize=False)
    assert state.current_player == Player.RED
    assert state.status.outcome == GameTermination.ONGOING
    assert len(state.board.pieces(Player.RED)) == 25
    assert len(state.board.pieces(Player.BLUE)) == 25


def test_ai_controller_creation():
    """Test AI controller initialization."""
    controller = AIController()
    assert controller.config.difficulty == "standard"
    assert controller.config.base_depth >= 1


def test_settings_manager():
    """Test settings manager functionality."""
    settings = SettingsManager()
    assert "volume" in settings.data
    assert "difficulty" in settings.data

    config = settings.as_config()
    assert config.difficulty == settings.data["difficulty"]


def test_move_generation():
    """Test basic move generation."""
    state = create_logic_state(seed=42, randomize=False)

    # Find a red piece and test move generation
    for coord, tile in state.board.tiles.items():
        if tile.occupant and tile.occupant.owner == Player.RED:
            moves = state.legal_moves(coord)
            # Should be able to generate moves (even if empty list)
            assert isinstance(moves, list)
            break


def test_game_cloning():
    """Test game state cloning."""
    state = create_logic_state(seed=42, randomize=False)
    cloned = state.clone()

    assert cloned.current_player == state.current_player
    assert cloned.turn_index == state.turn_index
    assert len(cloned.board.pieces(Player.RED)) == len(state.board.pieces(Player.RED))


if __name__ == "__main__":
    # Run basic smoke tests
    test_basic_game_creation()
    test_ai_controller_creation()
    test_settings_manager()
    test_move_generation()
    test_game_cloning()
    print("✓ All smoke tests passed!")
