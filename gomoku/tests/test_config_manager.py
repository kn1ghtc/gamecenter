"""Configuration manager tests for Gomoku.

These tests validate that the unified JSON configuration is loaded correctly
and that helper accessors expose the expected structure.
"""

import pytest

from gamecenter.gomoku.config.config_manager import (
    ConfigManager,
    DifficultyConfig,
    get_config_manager,
    get_difficulty_config,
)


def test_get_config_manager_singleton() -> None:
    """ConfigManager should behave as a singleton."""
    manager_a = get_config_manager()
    manager_b = get_config_manager()
    assert manager_a is manager_b


def test_difficulty_config_fields() -> None:
    """Difficulty configuration exposes typed attributes."""
    medium = get_difficulty_config("medium")
    assert isinstance(medium, DifficultyConfig)
    assert medium.search_depth == 5
    assert medium.time_limit == 5.0
    assert medium.transposition_table_size == 500_000

def test_invalid_difficulty_falls_back_to_default() -> None:
    """Unknown difficulty names should fall back to the configured default difficulty."""
    manager = ConfigManager()
    manager.reload()

    fallback_name = manager.get_engine_defaults().get("difficulty", "medium")
    fallback_config = manager.get_difficulty_config(fallback_name)
    resolved_config = manager.get_difficulty_config("non-existent")

    assert resolved_config.search_depth == fallback_config.search_depth
    assert resolved_config.transposition_table_size == fallback_config.transposition_table_size


def test_ui_layout_contains_expected_keys() -> None:
    """UI layout section should expose important sizing values."""
    manager = get_config_manager()
    layout = manager.get_ui_config("layout")
    assert layout["ui_panel_width"] == 300
    assert layout["button_height"] == 48


def test_engine_defaults_match_difficulty_names() -> None:
    """Default engine difficulty must exist in difficulty registry."""
    manager = get_config_manager()
    defaults = manager.get_engine_defaults()
    difficulty_name = defaults.get("difficulty")
    assert difficulty_name in manager.get_difficulty_names()
