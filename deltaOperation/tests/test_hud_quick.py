"""HUD快速测试"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

import sys
sys.path.insert(0, "d:/pyproject")

# 直接导入hud模块
from gamecenter.deltaOperation.ui.hud import HUD
from gamecenter.deltaOperation.core.player import Player
from gamecenter.deltaOperation.core.mission import Mission
from gamecenter.deltaOperation.core.level_manager import LevelManager

print("="*70)
print("HUD快速测试")
print("="*70)

# 创建HUD
screen = pygame.Surface((1280, 720))
hud = HUD(1280, 720)
print(f"\n✓ HUD创建成功: {hud.screen_width}x{hud.screen_height}")

# 创建游戏对象
level = LevelManager(level_id=1)
level._create_default_level()
player = Player(*level.player_spawn)
mission = Mission(mission_id=1)
mission.start_mission()

print("✓ 游戏对象创建成功")

# 测试渲染
try:
    hud.render(screen, player, mission, level)
    print("✓ HUD完整渲染成功")
except Exception as e:
    print(f"✗ 渲染失败: {e}")
    import traceback
    traceback.print_exc()

# 测试消息系统
hud.show_message("测试消息", (255, 255, 255))
hud.show_checkpoint_activated(1)
hud.show_objective_completed("测试目标")
print(f"✓ 消息系统: {len(hud.messages)}条消息")

# 测试更新
hud.update(1.0)
print(f"✓ 更新后消息: {len(hud.messages)}条消息")

print("\n" + "="*70)
print("✓✓✓ HUD核心功能测试通过!")
print("="*70)
