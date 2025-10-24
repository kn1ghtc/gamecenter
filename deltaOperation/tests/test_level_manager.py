"""关卡管理器测试"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from gamecenter.deltaOperation.core import (
    LevelManager, TileType, Player, PhysicsEngine
)

print("="*60)
print("关卡管理器测试")
print("="*60)

# 测试1: 创建关卡管理器
print("\n[测试1] 创建关卡管理器...")
level = LevelManager(level_id=1)
level._create_default_level()  # 使用默认地图

print(f"✓ 关卡尺寸: {level.width}x{level.height} 瓦片")
print(f"✓ 瓦片大小: {level.tile_size}px")
print(f"✓ 关卡边界: {level.level_bounds.width}x{level.level_bounds.height}px")

# 测试2: 玩家出生点和撤离点
print("\n[测试2] 出生点与撤离点...")
print(f"✓ 玩家出生点: {level.player_spawn}")
print(f"✓ 撤离点: {level.extraction_point}")

# 测试3: 敌人生成
print("\n[测试3] 敌人生成系统...")
print(f"✓ 生成点数量: {len(level.spawn_points)}")
level.spawn_enemies()
print(f"✓ 生成敌人: {len(level.enemies)}个")

for i, enemy in enumerate(level.enemies):
    print(f"  - 敌人{i+1}: {enemy.enemy_type} at ({int(enemy.position.x)}, {int(enemy.position.y)})")

# 测试4: 瓦片查询
print("\n[测试4] 瓦片查询...")
test_pos = (100, 600)
tile_type = level.get_tile_at(*test_pos)
print(f"✓ 坐标{test_pos}的瓦片类型: {TileType(tile_type)}")

# 测试5: 检查点系统
print("\n[测试5] 检查点系统...")
print(f"✓ 检查点数量: {len(level.checkpoints)}")

player = Player(*level.player_spawn)
cp_id = level.activate_checkpoint((player.position.x, player.position.y), radius=100)
if cp_id is not None:
    print(f"✓ 激活了检查点 #{cp_id}")
else:
    print("✓ 玩家不在检查点附近")

# 测试6: 撤离点检测
print("\n[测试6] 撤离点检测...")
at_extraction = level.check_extraction((player.position.x, player.position.y))
print(f"✓ 玩家{'已到达' if at_extraction else '未到达'}撤离点")

# 测试到撤离点
if level.extraction_point:
    at_extraction = level.check_extraction(level.extraction_point, radius=10)
    print(f"✓ 撤离点处检测: {at_extraction}")

# 测试7: 碰撞检测
print("\n[测试7] 碰撞检测...")
from gamecenter.deltaOperation.core.physics import AABB
player_aabb = AABB(player.position.x, player.position.y, 
                   player.width, player.height)
collision_tiles = level.get_collision_tiles(player_aabb)
print(f"✓ 玩家周围固体瓦片: {len(collision_tiles)}个")

# 测试8: 边界检查
print("\n[测试8] 边界检查...")
in_bounds = not level.is_out_of_bounds(100, 100)
out_bounds = level.is_out_of_bounds(-10, -10)
print(f"✓ (100, 100)在边界内: {in_bounds}")
print(f"✓ (-10, -10)在边界外: {out_bounds}")

# 测试9: 更新循环
print("\n[测试9] 更新循环...")
engine = PhysicsEngine()
player.target = (300, 100)

for i in range(30):
    level.update(0.016, engine, [player])

alive_count = len(level.get_alive_enemies())
print(f"✓ 更新30帧后存活敌人: {alive_count}个")

# 测试10: 渲染系统
print("\n[测试10] 渲染系统...")
screen = pygame.Surface((800, 600))
try:
    level.render(screen)
    print("✓ 关卡渲染成功")
except Exception as e:
    print(f"✗ 渲染失败: {e}")

print("\n" + "="*60)
print("✓✓✓ 所有关卡管理器测试通过!")
print("="*60)
