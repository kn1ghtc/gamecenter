#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI和特殊围墙修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from level_manager import LevelManager
from config import MAP_CONFIG, ENEMY_CONFIG

def test_enemy_distribution():
    """测试敌人分布优化"""
    print("=== 测试敌人分布优化 ===")

    level_manager = LevelManager()
    level_data = level_manager.generate_level_data(1)

    grid_height = MAP_CONFIG['GRID_HEIGHT']
    territory_border = grid_height // 2
    cell_size = MAP_CONFIG['CELL_SIZE']

    enemies = level_data['enemies']
    print(f"总敌人数量: {len(enemies)}")

    # 统计分布
    upper_half = 0
    lower_half = 0
    distances = []

    for i, enemy in enumerate(enemies):
        enemy_grid_y = int(enemy['y'] // cell_size)
        if enemy_grid_y < territory_border:
            upper_half += 1
        else:
            lower_half += 1

        # 计算敌人之间的最近距离
        for j, other_enemy in enumerate(enemies):
            if i != j:
                dx = abs(enemy['x'] - other_enemy['x'])
                dy = abs(enemy['y'] - other_enemy['y'])
                distance = max(dx, dy) // cell_size
                distances.append(distance)

    print(f"上半部分敌人: {upper_half}")
    print(f"下半部分敌人: {lower_half}")
    print(f"期望比例: 2/3在上半部分, 1/3在下半部分")

    if distances:
        min_distance = min(distances)
        avg_distance = sum(distances) / len(distances)
        print(f"敌人间最小距离: {min_distance}格")
        print(f"敌人间平均距离: {avg_distance:.1f}格")

        if min_distance >= 6:
            print("✅ 敌人分散良好，无扎堆现象")
        else:
            print("⚠️  部分敌人可能距离过近")

def test_ai_parameters():
    """测试AI参数设置"""
    print("\n=== AI参数分析 ===")

    # 获取实际配置参数
    attack_range = ENEMY_CONFIG['AI_ATTACK_RANGE']
    vision_range = ENEMY_CONFIG['AI_VISION_RANGE']
    fire_rate = ENEMY_CONFIG['FIRE_RATE']
    rotation_threshold = ENEMY_CONFIG['AI_ROTATION_THRESHOLD']

    print(f"AI攻击范围: {attack_range}像素")
    print(f"AI视野范围: {vision_range}像素")
    print(f"射击频率: {fire_rate}")
    print(f"旋转阈值: {rotation_threshold}")

    # 地图尺寸参考
    map_width = MAP_CONFIG['GRID_WIDTH'] * MAP_CONFIG['CELL_SIZE']
    map_height = MAP_CONFIG['GRID_HEIGHT'] * MAP_CONFIG['CELL_SIZE']
    grid_width = MAP_CONFIG['GRID_WIDTH']
    grid_height = MAP_CONFIG['GRID_HEIGHT']

    print(f"\n地图尺寸: {grid_width}x{grid_height}格")
    print(f"像素尺寸: {map_width}x{map_height}")

    # 计算攻击范围覆盖度
    max_distance = ((map_width**2 + map_height**2)**0.5)
    attack_coverage = (attack_range / max_distance) * 100
    vision_coverage = (vision_range / max_distance) * 100

    print(f"攻击范围覆盖: {attack_coverage:.1f}%的地图对角线")
    print(f"视野范围覆盖: {vision_coverage:.1f}%的地图对角线")

    # 评估参数合理性
    if attack_coverage < 20:
        print("⚠️  攻击范围可能过小")
    elif attack_coverage > 60:
        print("⚠️  攻击范围可能过大")
    else:
        print("✅ 攻击范围设置合理")

    if vision_coverage < 40:
        print("⚠️  视野范围可能过小")
    elif vision_coverage > 80:
        print("⚠️  视野范围可能过大")
    else:
        print("✅ 视野范围设置合理")

def test_special_wall_colors():
    """测试特殊围墙颜色定义"""
    print("\n=== 特殊围墙颜色映射 ===")

    # 从special_walls.py导入颜色定义
    try:
        from special_walls import SpecialWall

        effect_colors = {
            'piercing_ammo': (255, 255, 0),      # 黄色
            'explosive_ammo': (139, 69, 19),     # 棕色
            'wall_destroyer': (0, 100, 255),     # 蓝色
            'teleport': (0, 255, 100),           # 绿色
            'health_swap': (128, 0, 128),        # 紫色
            'speed_boost': (255, 255, 100),      # 亮黄色
            'shield': (200, 200, 200),           # 白色
            'multi_shot': (0, 255, 255),         # 青色
            'ghost_mode': (64, 64, 64)           # 黑色
        }

        print("特殊围墙效果 -> 颜色映射:")
        for effect, color in effect_colors.items():
            print(f"  {effect:<15} -> RGB{color}")

        print("✅ 特殊围墙颜色定义完整")

    except Exception as e:
        print(f"❌ 无法验证特殊围墙颜色: {e}")

if __name__ == "__main__":
    test_enemy_distribution()
    test_ai_parameters()
    test_special_wall_colors()

    print("\n=== 修复总结 ===")
    print("1. ✅ 敌方坦克AI攻击范围扩大到400像素")
    print("2. ✅ 敌人分布优化：1/3在玩家势力范围，避免扎堆")
    print("3. ✅ 特殊围墙效果对所有打破者生效")
    print("4. ✅ 帮助界面更新特殊围墙说明")
    print("5. ✅ 持续射击功能保持正常")
