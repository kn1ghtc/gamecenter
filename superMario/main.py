#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Main Entry Point
A complete Super Mario game with 30 levels, scoring system, and automatic resource downloading.
"""

import sys
import os
from pathlib import Path

# Set up path to ensure proper module resolution
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Change to project directory to ensure assets can be found
os.chdir(PROJECT_ROOT)

import pygame
from src.game import Game

def main():
    """Main game entry point"""
    try:
        # Initialize Pygame
        pygame.init()
        pygame.mixer.init()

        # Create game instance
        game = Game()

        # Run the game
        game.run()

    except KeyboardInterrupt:
        print("Game interrupted by user")
    except Exception as e:
        print(f"Game error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()
