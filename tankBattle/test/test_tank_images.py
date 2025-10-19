#!/usr/bin/env python3
"""简单测试坦克图片加载"""

import sys
from pathlib import Path

# 添加项目根目录到路径
TANK_BATTLE_DIR = Path(__file__).parent
sys.path.insert(0, str(TANK_BATTLE_DIR))

from config import PLAYER_CONFIG, ENEMY_CONFIG
import os

print("🔍 检查坦克图片配置...")
print(f"玩家坦克图片路径: {PLAYER_CONFIG['IMAGE']}")
print(f"文件是否存在: {os.path.exists(PLAYER_CONFIG['IMAGE'])}")

print(f"\n敌方坦克图片路径: {ENEMY_CONFIG['IMAGE']}")
print(f"文件是否存在: {os.path.exists(ENEMY_CONFIG['IMAGE'])}")

if os.path.exists(PLAYER_CONFIG['IMAGE']) and os.path.exists(ENEMY_CONFIG['IMAGE']):
    print("\n✅ 所有坦克图片文件存在！")

    # 尝试加载图片
    import pygame
    pygame.init()

    try:
        player_img = pygame.image.load(PLAYER_CONFIG['IMAGE'])
        print(f"✅ 玩家坦克图片加载成功 - 尺寸: {player_img.get_size()}")
    except Exception as e:
        print(f"❌ 玩家坦克图片加载失败: {e}")

    try:
        enemy_img = pygame.image.load(ENEMY_CONFIG['IMAGE'])
        print(f"✅ 敌方坦克图片加载成功 - 尺寸: {enemy_img.get_size()}")
    except Exception as e:
        print(f"❌ 敌方坦克图片加载失败: {e}")

    pygame.quit()
else:
    print("\n❌ 图片文件不存在！")
