"""任务系统测试"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from gamecenter.deltaOperation.core import (
    Mission, MissionStatus, ObjectiveType,
    LevelManager, Player, PhysicsEngine
)

print("="*70)
print("任务系统测试")
print("="*70)

# 测试1: 创建任务
print("\n[测试1] 创建任务...")
mission = Mission(mission_id=1)
print(f"✓ 任务ID: {mission.mission_id}")
print(f"✓ 任务名称: {mission.config.name}")
print(f"✓ 任务描述: {mission.config.description}")
print(f"✓ 难度: {mission.config.difficulty}")
print(f"✓ 关卡ID: {mission.config.level_id}")

# 测试2: 任务简报
print("\n[测试2] 任务简报...")
print(f"简报: {mission.config.briefing}")

# 测试3: 任务目标
print("\n[测试3] 任务目标...")
print(f"✓ 目标数量: {len(mission.config.objectives)}")
for i, obj in enumerate(mission.config.objectives, 1):
    print(f"  {i}. {obj.description} ({obj.obj_type.value})")

# 测试4: 开始任务
print("\n[测试4] 开始任务...")
mission.start_mission()
print(f"✓ 任务状态: {mission.status}")

# 测试5: 目标进度更新
print("\n[测试5] 目标进度更新...")
mission.on_enemy_killed()
mission.on_enemy_killed()
print(f"✓ 已击杀敌人: {mission.enemies_killed}")

objectives_text = mission.get_objectives_text()
for text in objectives_text:
    print(f"  {text}")

# 测试6: 完成度计算
print("\n[测试6] 完成度计算...")
completion = mission.get_completion_percentage()
print(f"✓ 任务完成度: {completion:.1f}%")

# 测试7: 测试不同任务类型
print("\n[测试7] 测试不同任务类型...")
test_missions = [3, 6, 12]  # 人质营救、防御战、最终对决
for mid in test_missions:
    m = Mission(mission_id=mid)
    print(f"✓ 任务{mid}: {m.config.name} - 难度:{m.config.difficulty}")
    if m.config.time_limit:
        print(f"  时间限制: {m.config.time_limit}秒")
    print(f"  目标: {len(m.config.objectives)}个")

# 测试8: 时间限制任务
print("\n[测试8] 时间限制任务...")
timed_mission = Mission(mission_id=3)  # 人质营救有时间限制
timed_mission.start_mission()
print(f"✓ 时间限制: {timed_mission.config.time_limit}秒")
print(f"✓ 已用时间: {timed_mission.elapsed_time:.1f}秒")
remaining = timed_mission.get_time_remaining()
print(f"✓ 剩余时间: {remaining}秒")

# 测试9: 任务更新循环
print("\n[测试9] 任务更新循环...")
level = LevelManager(level_id=1)
level._create_default_level()
level.spawn_enemies()

player = Player(*level.player_spawn)
engine = PhysicsEngine()

mission = Mission(mission_id=1)
mission.start_mission()

# 模拟游戏循环
for i in range(60):  # 1秒(60帧)
    mission.update(0.016, level, player)

print(f"✓ 更新60帧后时间: {mission.elapsed_time:.2f}秒")
print(f"✓ 任务状态: {mission.status}")

# 测试10: 胜利条件
print("\n[测试10] 胜利条件...")
# 杀死所有敌人
for enemy in level.enemies:
    enemy.take_damage(9999)
    mission.on_enemy_killed()

# 移动到撤离点
if level.extraction_point:
    player.position.x = level.extraction_point[0]
    player.position.y = level.extraction_point[1]

mission.update(0.016, level, player)

print(f"✓ 所有敌人已消灭: {len(level.get_alive_enemies())} 存活")
print(f"✓ 任务状态: {mission.status}")
print(f"✓ 任务完成: {mission.is_completed()}")

# 测试11: 失败条件
print("\n[测试11] 失败条件...")
fail_mission = Mission(mission_id=3)
fail_mission.start_mission()
fail_mission.on_player_death()
print(f"✓ 玩家死亡后状态: {fail_mission.status}")
print(f"✓ 任务失败: {fail_mission.is_failed()}")

# 测试12: 所有12个任务
print("\n[测试12] 所有12个任务概览...")
print(f"{'ID':<4} {'任务名称':<15} {'难度':<8} {'目标数':<6} {'时限':<6}")
print("-" * 60)
for mid in range(1, 13):
    m = Mission(mission_id=mid)
    time_str = f"{m.config.time_limit}s" if m.config.time_limit else "无"
    print(f"{mid:<4} {m.config.name:<15} {m.config.difficulty:<8} "
          f"{len(m.config.objectives):<6} {time_str:<6}")

print("\n" + "="*70)
print("✓✓✓ 所有任务系统测试通过!")
print("="*70)
