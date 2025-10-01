"""Military Chess package initialization.

This module sets up the package paths and provides absolute imports for all
military chess modules. It ensures consistent import behavior across different
execution contexts.
"""

import sys
from pathlib import Path

# Setup package path for absolute imports
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

# Ensure project root is in Python path for absolute imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Now use absolute imports consistently
from gamecenter.militaryChess.game_logic import (
    GameState, JunqiBoard, Player, Move, MoveKind, Piece,
    GameTermination, GameStatus, IllegalMove, create_logic_state
)
from gamecenter.militaryChess.ai_engine import AIController, AIConfig, SettingsManager
from gamecenter.militaryChess.evaluation import evaluate_state
from gamecenter.militaryChess.main import run_game

__all__ = [
    "GameState", "JunqiBoard", "Player", "Move", "MoveKind", "Piece",
    "GameTermination", "GameStatus", "IllegalMove", "create_logic_state",
    "AIController", "AIConfig", "SettingsManager", "evaluate_state",
    "run_game"
]
