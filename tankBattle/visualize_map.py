#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图布局可视化工具
显示地图的势力划分、基地位置、分割线等
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from level_manager import LevelManager
from config import MAP_CONFIG, GAME_CONFIG

def visualize_map_layout():
    """可视化地图布局"""
    print("=== 坦克大战地图布局可视化 ===\n")

    level_manager = LevelManager()
    level_data = level_manager.generate_level_data(1)

    # 地图基本信息
    grid_width = MAP_CONFIG['GRID_WIDTH']
    grid_height = MAP_CONFIG['GRID_HEIGHT']
    cell_size = MAP_CONFIG['CELL_SIZE']

    print(f"地图尺寸: {grid_width} × {grid_height} 格")
    print(f"像素尺寸: {GAME_CONFIG['WIDTH']} × {GAME_CONFIG['HEIGHT']} 像素")
    print(f"网格大小: {cell_size} × {cell_size} 像素/格")

    # 势力范围划分
    territory_border = grid_height // 2
    print(f"\n=== 势力范围划分 ===")
    print(f"地图中心线: 第 {territory_border} 行")
    print(f"敌方势力范围: 第 0-{territory_border-1} 行 (上半部分)")
    print(f"己方势力范围: 第 {territory_border}-{grid_height-1} 行 (下半部分)")

    # 基地位置
    player_base = level_data['player_base_pos']
    enemy_base = level_data['enemy_base_pos']

    player_base_grid = (int(player_base['x'] // cell_size), int(player_base['y'] // cell_size))
    enemy_base_grid = (int(enemy_base['x'] // cell_size), int(enemy_base['y'] // cell_size))

    print(f"\n=== 基地位置 ===")
    print(f"玩家基地: 网格 {player_base_grid}, 像素 ({player_base['x']}, {player_base['y']})")
    print(f"敌方基地: 网格 {enemy_base_grid}, 像素 ({enemy_base['x']}, {enemy_base['y']})")

    # 玩家起始位置
    player_pos = level_data['player_pos']
    player_grid = (int(player_pos['x'] // cell_size), int(player_pos['y'] // cell_size))

    print(f"\n=== 起始位置 ===")
    print(f"玩家起始: 网格 {player_grid}, 像素 ({player_pos['x']}, {player_pos['y']})")

    distance_to_base = max(abs(player_grid[0] - player_base_grid[0]),
                          abs(player_grid[1] - player_base_grid[1]))
    print(f"距离己方基地: {distance_to_base} 格")

    # 敌人位置统计
    enemies = level_data['enemies']
    enemies_upper = 0
    enemies_lower = 0

    print(f"\n=== 敌人分布 ===")
    print(f"敌人总数: {len(enemies)}")

    for enemy in enemies:
        enemy_grid_y = int(enemy['y'] // cell_size)
        if enemy_grid_y < territory_border:
            enemies_upper += 1
        else:
            enemies_lower += 1

    print(f"上半部分敌人: {enemies_upper}")
    print(f"下半部分敌人: {enemies_lower}")

    # 分割线统计
    walls = level_data['walls']
    barrier_walls = 0

    for wall in walls:
        wall_grid_y = int(wall['y'] // cell_size)
        if wall_grid_y in [territory_border - 1, territory_border]:
            barrier_walls += 1

    print(f"\n=== 中间分割线 ===")
    print(f"分割线位置: 第 {territory_border-1} 和 {territory_border} 行")
    print(f"分割线围墙数量: {barrier_walls}")
    print(f"预计通道数量: 3个 (左、中、右)")

    # 创建简化的地图可视化
    print(f"\n=== 地图布局简图 ===")
    print("图例: E=敌方基地, P=玩家基地, S=玩家起始, #=分割线, ·=空白区域")
    print()

    # 创建简化地图 (每4格合并为1个字符)
    map_scale = 4
    visual_width = grid_width // map_scale
    visual_height = grid_height // map_scale

    for y in range(visual_height):
        line = ""
        for x in range(visual_width):
            # 计算实际网格坐标
            actual_y = y * map_scale
            actual_x = x * map_scale

            # 检查这个区域包含什么
            char = '·'

            # 敌方基地
            if (actual_y <= enemy_base_grid[1] < actual_y + map_scale and
                actual_x <= enemy_base_grid[0] < actual_x + map_scale):
                char = 'E'
            # 玩家基地
            elif (actual_y <= player_base_grid[1] < actual_y + map_scale and
                  actual_x <= player_base_grid[0] < actual_x + map_scale):
                char = 'P'
            # 玩家起始位置
            elif (actual_y <= player_grid[1] < actual_y + map_scale and
                  actual_x <= player_grid[0] < actual_x + map_scale):
                char = 'S'
            # 分割线区域
            elif actual_y <= territory_border < actual_y + map_scale:
                char = '#'
            # 势力范围标记
            elif actual_y < territory_border:
                char = '░'  # 敌方势力范围
            else:
                char = '▓'  # 己方势力范围

            line += char + ' '

        # 添加行号标记
        if y == 0:
            line += "  ← 敌方势力范围"
        elif y == visual_height // 2:
            line += "  ← 分割线"
        elif y == visual_height - 1:
            line += "  ← 己方势力范围"

        print(line)

    print(f"\n地图说明:")
    print(f"- 上半部分 (░): 敌方势力范围，敌人和敌方基地在此区域")
    print(f"- 下半部分 (▓): 己方势力范围，玩家和玩家基地在此区域")
    print(f"- 中间 (#): 分割线，有3个通道口连接两个势力范围")
    print(f"- E: 敌方基地位置")
    print(f"- P: 玩家基地位置")
    print(f"- S: 玩家起始位置")

if __name__ == "__main__":
    visualize_map_layout()
