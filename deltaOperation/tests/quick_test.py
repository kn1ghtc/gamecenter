# -*- coding: utf-8 -*-
"""快速测试脚本"""
import os
os.system("chcp 65001 >nul 2>&1")

import sys
sys.stdout.reconfigure(encoding='utf-8')

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.font.init()

print("="*70)
print("快速测试")
print("="*70)

# 测试1: Vector2D
try:
    from gamecenter.deltaOperation.core.physics import Vector2D
    v = Vector2D(3, 4)
    assert v.length() == 5.0
    print("[OK] Vector2D")
except Exception as e:
    print(f"[FAIL] Vector2D: {e}")
    sys.exit(1)

# 测试2: Player
try:
    from gamecenter.deltaOperation.core.player import Player
    p = Player(100, 100)
    assert hasattr(p, 'current_weapon')
    assert hasattr(p, 'weapons')
    print("[OK] Player属性")
except Exception as e:
    print(f"[FAIL] Player: {e}")
    sys.exit(1)

# 测试3: 移动速度
try:
    from gamecenter.deltaOperation import config
    speed = config.PLAYER_CONFIG["move_speed"]
    assert speed >= 200, f"速度太慢: {speed}"
    print(f"[OK] 移动速度: {speed} 像素/秒")
except Exception as e:
    print(f"[FAIL] 速度: {e}")
    sys.exit(1)

# 测试4: 精灵图
try:
    sprite_dir = config.ASSETS_DIR / "assets" / "images" / "characters"
    sprites = list(sprite_dir.glob("*.png"))
    if sprites:
        print(f"[OK] 精灵图: {len(sprites)}个文件")
        for s in sprites:
            print(f"     - {s.name}")
    else:
        print("[WARN] 无精灵图,使用占位符")
except Exception as e:
    print(f"[FAIL] 精灵图: {e}")

# 测试5: 游戏初始化
try:
    screen = pygame.display.set_mode((800, 600), pygame.HIDDEN)
    from gamecenter.deltaOperation.core.game_state import GameState
    gs = GameState(screen, headless=True)
    gs.update(0.016)
    print("[OK] 游戏初始化和更新")
    pygame.quit()
except Exception as e:
    print(f"[FAIL] 游戏: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("所有测试通过!")
print("="*70)
print("\n运行游戏: python main.py")
