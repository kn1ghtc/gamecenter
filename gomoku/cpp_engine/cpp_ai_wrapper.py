"""Python wrapper for C++ Gomoku Engine
Uses ctypes to call the compiled C++ library.
"""

import ctypes
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

from gamecenter.gomoku.game_logic import Board, Player


class CppAIEngine:
    """Python wrapper for C++ AI engine"""

    def __init__(self, lib_path: Optional[str] = None):
        """Initialize C++ engine

        Args:
            lib_path: Path to the compiled library (.dll, .so, or .dylib)
        """
        if lib_path is None:
            # Auto-detect library path
            current_dir = Path(__file__).parent
            if sys.platform == "win32":
                lib_path = current_dir / "gomoku_engine.dll"
            elif sys.platform == "darwin":
                lib_path = current_dir / "libgomoku_engine.dylib"
            else:
                lib_path = current_dir / "libgomoku_engine.so"

        if not Path(lib_path).exists():
            raise FileNotFoundError(
                f"C++ library not found: {lib_path}\n"
                "Please compile first using: cd cpp_engine && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && cmake --build ."
            )

        # Load library
        self.lib = ctypes.CDLL(str(lib_path))

        # Define function signatures
        self.lib.gomoku_create_engine.restype = ctypes.c_void_p

        self.lib.gomoku_destroy_engine.argtypes = [ctypes.c_void_p]

        self.lib.gomoku_set_board.argtypes = [
            ctypes.c_void_p,           # engine
            ctypes.POINTER(ctypes.c_int8),  # grid
            ctypes.c_int               # size
        ]

        self.lib.gomoku_find_best_move.argtypes = [
            ctypes.c_void_p,           # engine
            ctypes.c_int,              # player
            ctypes.c_int,              # max_depth
            ctypes.c_double,           # time_limit
            ctypes.POINTER(ctypes.c_int),  # out_row
            ctypes.POINTER(ctypes.c_int),  # out_col
            ctypes.POINTER(ctypes.c_int)   # out_score
        ]

        self.lib.gomoku_get_nodes_searched.argtypes = [ctypes.c_void_p]
        self.lib.gomoku_get_nodes_searched.restype = ctypes.c_uint64

        self.lib.gomoku_get_search_time.argtypes = [ctypes.c_void_p]
        self.lib.gomoku_get_search_time.restype = ctypes.c_double

        # Create engine instance
        self.engine = self.lib.gomoku_create_engine()

        # Statistics
        self.nodes_searched = 0
        self.search_time = 0.0

    def __del__(self):
        """Destroy engine"""
        if hasattr(self, 'engine') and self.engine:
            self.lib.gomoku_destroy_engine(self.engine)

    def find_best_move(self, board: Board, player: Player, max_depth: int = 7,
                       time_limit: float = 5.0) -> Optional[Tuple[int, int]]:
        """Find best move using C++ engine

        Args:
            board: Current board state
            player: Player to move
            max_depth: Maximum search depth
            time_limit: Time limit in seconds

        Returns:
            (row, col) of best move, or None if no valid move
        """
        # Convert board to flat array
        grid = np.zeros(225, dtype=np.int8)
        for row in range(15):
            for col in range(15):
                stone = board.get_stone(row, col)
                if stone == Player.BLACK:
                    grid[row * 15 + col] = 1
                elif stone == Player.WHITE:
                    grid[row * 15 + col] = 2
                else:
                    grid[row * 15 + col] = 0

        # Set board state
        grid_ptr = grid.ctypes.data_as(ctypes.POINTER(ctypes.c_int8))
        self.lib.gomoku_set_board(self.engine, grid_ptr, 225)

        # Call find_best_move
        player_val = 1 if player == Player.BLACK else 2
        out_row = ctypes.c_int()
        out_col = ctypes.c_int()
        out_score = ctypes.c_int()

        self.lib.gomoku_find_best_move(
            self.engine,
            player_val,
            max_depth,
            time_limit,
            ctypes.byref(out_row),
            ctypes.byref(out_col),
            ctypes.byref(out_score)
        )

        # Get statistics
        self.nodes_searched = self.lib.gomoku_get_nodes_searched(self.engine)
        self.search_time = self.lib.gomoku_get_search_time(self.engine)

        # Return result
        if out_row.value >= 0 and out_col.value >= 0:
            return (out_row.value, out_col.value)
        return None

    def get_stats(self) -> dict:
        """Get search statistics"""
        nps = self.nodes_searched / self.search_time if self.search_time > 0 else 0
        return {
            'nodes_searched': self.nodes_searched,
            'search_time': self.search_time,
            'nodes_per_second': nps,
            'engine': 'C++'
        }


# Factory function for easy integration
def create_cpp_ai(max_depth: int = 7, time_limit: float = 5.0):
    """Create C++ AI controller with standard interface

    Args:
        max_depth: Maximum search depth
        time_limit: Time limit per move

    Returns:
        CppAIEngine instance
    """
    engine = CppAIEngine()
    # Store parameters for later use
    engine.max_depth = max_depth
    engine.time_limit = time_limit

    # Add wrapper method for consistency with Python AI
    original_find_best_move = engine.find_best_move

    def find_best_move_wrapper(board, player):
        return original_find_best_move(board, player, engine.max_depth, engine.time_limit)

    engine.find_best_move = find_best_move_wrapper

    return engine
