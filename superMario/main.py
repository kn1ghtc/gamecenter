#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Main Entry Point
A complete Super Mario game with 30 levels, scoring system, and automatic resource downloading.
"""

import sys
import os
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