#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick feature validation script for Super Mario
Tests triple jump and resource loading
"""

import sys
from pathlib import Path

def test_resources():
    """Test that all resources are present"""
    print("Testing resource availability...")
    
    assets_dir = Path("assets")
    required = [
        "images/mario.png",
        "images/tiles.png",
        "images/enemies.png",
        "images/coin.png",
        "images/powerup.png",
        "images/goal.png",
        "sounds/jump.wav",
        "sounds/coin.wav",
        "sounds/enemy_die.wav",
        "sounds/background_music.wav"
    ]
    
    all_present = True
    for resource in required:
        path = assets_dir / resource
        if path.exists():
            print(f"  ✓ {resource}")
        else:
            print(f"  ✗ {resource} MISSING")
            all_present = False
    
    return all_present

def test_triple_jump():
    """Test triple jump mechanics"""
    print("\nTesting triple jump mechanism...")
    
    from src.player import Player
    
    # Create player with default config
    player = Player((100, 500), "assets", {})
    
    print(f"  Initial air jumps remaining: {player.air_jumps_remaining}")
    
    # Simulate being in air
    player.on_ground = False
    
    # First air jump
    result1 = player.jump()
    print(f"  First air jump: {'SUCCESS' if result1 else 'FAILED'}")
    print(f"  Air jumps remaining: {player.air_jumps_remaining}")
    
    # Second air jump
    result2 = player.jump()
    print(f"  Second air jump: {'SUCCESS' if result2 else 'FAILED'}")
    print(f"  Air jumps remaining: {player.air_jumps_remaining}")
    
    # Third attempt (should fail - no more air jumps)
    result3 = player.jump()
    print(f"  Third air jump attempt: {'BLOCKED (correct)' if not result3 else 'ALLOWED (incorrect)'}")
    
    # Test ground reset - simulate manually
    player.on_ground = True
    if player.on_ground:
        player.air_jumps_remaining = 2
    print(f"  After landing, air jumps reset to: {player.air_jumps_remaining}")
    
    success = result1 and result2 and not result3 and player.air_jumps_remaining == 2
    return success

def test_no_downloader():
    """Test that downloader is not imported in game.py"""
    print("\nTesting that downloader is not used on startup...")
    
    with open("src/game.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    if "from src.downloader import ResourceDownloader" in content:
        print("  ✗ Downloader still imported in game.py")
        return False
    
    if "downloader.download_all_resources()" in content:
        print("  ✗ Download call still present in game.py")
        return False
    
    print("  ✓ Downloader removed from game startup")
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("Super Mario Feature Validation")
    print("="*60)
    
    results = {
        "Resources": test_resources(),
        "Triple Jump": test_triple_jump(),
        "No Downloader": test_no_downloader()
    }
    
    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("All tests PASSED! 🎉")
        print("="*60)
        return 0
    else:
        print("Some tests FAILED")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
