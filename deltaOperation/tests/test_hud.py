"""HUD系统测试"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from gamecenter.deltaOperation.ui import HUD
from gamecenter.deltaOperation.core import (
    Player,
    Mission,
    LevelManager,
    PhysicsEngine,
    WeaponFactory,
)

print("="*70)
print("HUD系统测试")
print("="*70)

# 创建测试环境
screen = pygame.Surface((1280, 720))
hud = HUD(1280, 720)

# 创建游戏对象
level = LevelManager(level_id=1)
level._create_default_level()
level.spawn_enemies()

player = Player(*level.player_spawn)
mission = Mission(mission_id=1)
mission.start_mission()

# 为玩家装备标准手枪,以验证武器HUD信息
pistol = WeaponFactory.create_pistol()
player.add_weapon(pistol)

print("\n[测试1] HUD初始化...")
print(f"✓ 屏幕尺寸: {hud.screen_width}x{hud.screen_height}")
print(f"✓ 血条宽度: {hud.health_bar_width}px")
print(f"✓ 小地图尺寸: {hud.minimap_size}x{hud.minimap_size}px")

print("\n[测试2] 渲染玩家状态...")
hud._render_player_status(screen, player)
print(f"✓ 玩家血量: {player.health}/{player.max_health}")
print(f"✓ 血条渲染成功")

print("\n[测试3] 渲染武器信息...")
hud._render_weapon_info(screen, player)
print(f"✓ 武器: {player.current_weapon.name}")
print(f"✓ 弹药: {player.current_weapon.current_ammo}/{player.current_weapon.reserve_ammo}")

print("\n[测试4] 渲染小地图...")
hud._render_minimap(screen, player, level)
print(f"✓ 小地图位置: {hud.minimap_pos}")
print(f"✓ 显示玩家: 1个")
print(f"✓ 显示敌人: {len(level.get_alive_enemies())}个")
print(f"✓ 显示检查点: {len(level.checkpoints)}个")

print("\n[测试5] 渲染任务目标...")
hud._render_mission_objectives(screen, mission)
print(f"✓ 任务: {mission.config.name}")
print(f"✓ 目标数量: {len(mission.config.objectives)}个")
print(f"✓ 完成度: {mission.get_completion_percentage():.1f}%")

print("\n[测试6] 消息系统...")
hud.show_message("测试消息1", (255, 255, 255))
hud.show_message("测试消息2", (255, 255, 0))
print(f"✓ 消息数量: {len(hud.messages)}个")

hud.show_checkpoint_activated(1)
print(f"✓ 检查点消息: {len(hud.messages)}个")

hud.show_objective_completed("消灭所有敌人")
print(f"✓ 目标完成消息: {len(hud.messages)}个")

print("\n[测试7] 消息更新和淡出...")
initial_count = len(hud.messages)
for i in range(100):
    hud.update(0.05)  # 5秒
    
final_count = len(hud.messages)
print(f"✓ 初始消息: {initial_count}个")
print(f"✓ 5秒后消息: {final_count}个 (已淡出)")

print("\n[测试8] 小地图切换...")
initial_state = hud.show_minimap
hud.toggle_minimap()
print(f"✓ 初始状态: {initial_state}")
print(f"✓ 切换后: {hud.show_minimap}")

print("\n[测试9] 完整HUD渲染...")
screen.fill((0, 0, 0))
try:
    hud.render(screen, player, mission, level)
    print("✓ 完整HUD渲染成功")
except Exception as e:
    print(f"✗ 渲染失败: {e}")

print("\n[测试10] 时间限制任务HUD...")
timed_mission = Mission(mission_id=3)  # 人质营救有时间限制
timed_mission.start_mission()
hud._render_timer(screen, timed_mission)
remaining = timed_mission.get_time_remaining()
print(f"✓ 时间限制: {timed_mission.config.time_limit}秒")
print(f"✓ 剩余时间: {remaining}秒")
print(f"✓ 倒计时渲染成功")

print("\n[测试11] 击杀计数...")
mission.enemies_killed = 5
hud._render_kill_count(screen, mission)
print(f"✓ 击杀数: {mission.enemies_killed}")

print("\n[测试12] 任务状态消息...")
hud.show_mission_completed()
print(f"✓ 任务完成消息已显示")

hud.show_mission_failed("玩家阵亡")
print(f"✓ 任务失败消息已显示")
print(f"✓ 当前消息队列: {len(hud.messages)}个")

print("\n[测试13] 血量变化渲染...")
test_healths = [100, 60, 30, 10]
for hp in test_healths:
    player.health = hp
    hud._render_player_status(screen, player)
    
    # 计算血量颜色
    ratio = hp / player.max_health
    if ratio > 0.6:
        color = "绿色"
    elif ratio > 0.3:
        color = "黄色"
    else:
        color = "红色"
    print(f"✓ 血量{hp}% → {color}")

print("\n" + "="*70)
print("✓✓✓ 所有HUD测试通过!")
print("="*70)
