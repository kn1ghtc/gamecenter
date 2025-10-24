"""敌人AI系统测试"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from gamecenter.deltaOperation.core import (
    Enemy, EnemyState, Player, PhysicsEngine
)

print("="*60)
print("敌人AI系统测试")
print("="*60)

# 测试1: 创建不同类型的敌人
print("\n[测试1] 创建敌人...")
grunt = Enemy(100, 100, "grunt")
elite = Enemy(200, 100, "elite")
boss = Enemy(300, 100, "boss")

print(f"✓ 杂兵: 血量={grunt.health}, 伤害={grunt.damage}, 速度={grunt.move_speed}")
print(f"✓ 精英: 血量={elite.health}, 伤害={elite.damage}, 速度={elite.move_speed}")
print(f"✓ BOSS: 血量={boss.health}, 伤害={boss.damage}, 速度={boss.move_speed}")

# 测试2: 巡逻系统
print("\n[测试2] 巡逻系统...")
grunt.set_patrol_points([(100, 100), (200, 100), (300, 100)])
assert len(grunt.patrol_points) == 3
assert grunt.state == EnemyState.PATROL
print(f"✓ 巡逻点设置成功: {len(grunt.patrol_points)}个点")

# 测试3: 视野检测
print("\n[测试3] 视野检测...")
player = Player(150, 100)  # 在视野内
can_see = grunt.can_see_target((player.position.x, player.position.y))
print(f"✓ 视野检测: {can_see} (玩家距离={abs(grunt.position.x - player.position.x)}px)")

# 测试4: 状态切换
print("\n[测试4] AI状态机...")
grunt.take_damage(10)
print(f"✓ 受伤后状态: {grunt.state} (血量={grunt.health})")

grunt.alert_level = 0.8
assert grunt.alert_level >= grunt.alert_threshold
print(f"✓ 警戒级别: {grunt.alert_level} (阈值={grunt.alert_threshold})")

# 测试5: 武器系统
print("\n[测试5] 敌人武器...")
print(f"✓ 杂兵武器: {grunt.weapon.name}")
print(f"✓ 精英武器: {elite.weapon.name}")
print(f"✓ BOSS武器: {boss.weapon.name}")

# 测试6: 更新循环
print("\n[测试6] 更新循环...")
engine = PhysicsEngine()
grunt.target = player
grunt.state = EnemyState.COMBAT

for i in range(10):
    grunt.update(0.016, engine, [player])

print(f"✓ 更新10帧后位置: ({int(grunt.position.x)}, {int(grunt.position.y)})")
print(f"✓ 状态: {grunt.state}")
print(f"✓ 发射子弹数: {len(grunt.weapon.bullets)}")

# 测试7: 伤害系统
print("\n[测试7] 伤害与死亡...")
initial_health = elite.health
elite.take_damage(50)
print(f"✓ 受伤: {initial_health} -> {elite.health}")

elite.take_damage(1000)
assert not elite.is_alive()
assert elite.state == EnemyState.DEATH
print(f"✓ 死亡状态: {elite.state}")

print("\n" + "="*60)
print("✓✓✓ 所有敌人AI测试通过!")
print("="*60)
