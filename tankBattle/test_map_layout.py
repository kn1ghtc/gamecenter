#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试地图布局优化功能
验证：
1. 玩家起始位置是否在基地附近
2. 敌人是否在上半部分生成
3. 中间分割线是否正确生成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from level_manager import LevelManager
from config import MAP_CONFIG, GAME_CONFIG

def test_map_layout():
    """测试地图布局优化"""
    print("测试地图布局优化功能...")

    level_manager = LevelManager()

    # 测试前几关
    for level in range(1, 4):
        print(f"\n--- 测试第{level}关 ---")

        # 生成关卡数据
        level_data = level_manager.generate_level_data(level)

        # 获取基地位置
        player_base = level_data['player_base_pos']
        enemy_base = level_data['enemy_base_pos']

        print(f"玩家基地位置: ({player_base['x']}, {player_base['y']})")
        print(f"敌方基地位置: ({enemy_base['x']}, {enemy_base['y']})")

        # 获取玩家位置
        player_pos = level_data['player_pos']
        player_grid_x = int(player_pos['x'] // MAP_CONFIG['CELL_SIZE'])
        player_grid_y = int(player_pos['y'] // MAP_CONFIG['CELL_SIZE'])

        print(f"玩家起始位置: 网格({player_grid_x}, {player_grid_y}), 像素({player_pos['x']}, {player_pos['y']})")

        # 检查玩家是否在下半部分
        map_center_y = MAP_CONFIG['GRID_HEIGHT'] // 2
        if player_grid_y >= map_center_y:
            print("✅ 玩家在下半部分（己方势力范围）")
        else:
            print("❌ 玩家不在下半部分")

        # 计算玩家与基地的距离
        base_grid_x = int(player_base['x'] // MAP_CONFIG['CELL_SIZE'])
        base_grid_y = int(player_base['y'] // MAP_CONFIG['CELL_SIZE'])
        distance_to_base = max(abs(player_grid_x - base_grid_x), abs(player_grid_y - base_grid_y))
        print(f"玩家距离己方基地: {distance_to_base}格")

        # 检查敌人位置
        enemies = level_data['enemies']
        print(f"敌人数量: {len(enemies)}")

        enemies_in_upper_half = 0
        enemies_in_lower_half = 0

        for i, enemy in enumerate(enemies):
            enemy_grid_x = int(enemy['x'] // MAP_CONFIG['CELL_SIZE'])
            enemy_grid_y = int(enemy['y'] // MAP_CONFIG['CELL_SIZE'])

            if enemy_grid_y < map_center_y:
                enemies_in_upper_half += 1
            else:
                enemies_in_lower_half += 1

            print(f"  敌人{i+1}: 网格({enemy_grid_x}, {enemy_grid_y})")

        print(f"上半部分敌人: {enemies_in_upper_half}/{len(enemies)}")
        print(f"下半部分敌人: {enemies_in_lower_half}/{len(enemies)}")

        if enemies_in_upper_half == len(enemies):
            print("✅ 所有敌人都在上半部分（敌方势力范围）")
        elif enemies_in_upper_half > enemies_in_lower_half:
            print("⚠️  大部分敌人在上半部分")
        else:
            print("❌ 敌人分布不符合要求")

        # 检查中间分割线
        walls = level_data['walls']
        center_walls = []

        for wall in walls:
            wall_grid_y = int(wall['y'] // MAP_CONFIG['CELL_SIZE'])
            if wall_grid_y in [map_center_y - 1, map_center_y]:
                center_walls.append(wall)

        print(f"中间分割线围墙数量: {len(center_walls)}")

        if len(center_walls) > 0:
            print("✅ 中间分割线已生成")
        else:
            print("❌ 中间分割线未正确生成")

def test_territory_division():
    """测试势力范围划分"""
    print("\n\n=== 势力范围划分测试 ===")

    grid_height = MAP_CONFIG['GRID_HEIGHT']
    map_center = grid_height // 2

    print(f"地图总高度: {grid_height}格")
    print(f"地图中心线: 第{map_center}行")
    print(f"敌方势力范围: 第0行 到 第{map_center-1}行")
    print(f"己方势力范围: 第{map_center}行 到 第{grid_height-1}行")
    print(f"中间分割线: 第{map_center-1}行 和 第{map_center}行")

if __name__ == "__main__":
    test_map_layout()
    test_territory_division()
