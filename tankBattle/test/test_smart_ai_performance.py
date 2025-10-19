#!/usr/bin/env python3
"""
智能AI性能测试脚本
测试启用智能AI后的实际游戏性能
"""
import sys
from pathlib import Path
import time

# 添加项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pygame
from main import GameManager
from config import GAME_CONFIG

def test_smart_ai_performance(duration_seconds=10):
    """测试智能AI性能"""
    print(f"=== 智能AI性能测试 (运行{duration_seconds}秒) ===\n")

    # 创建游戏管理器(非smoke test,会启用智能AI)
    game = GameManager(smoke_test=False, smoke_test_frames=0)

    # 手动进入游戏
    game.current_level = 1
    game.load_level(game.current_level)
    game.game_state = 'playing'

    # 性能统计
    start_time = time.time()
    frame_count = 0
    frame_times = []

    running = True
    test_start = pygame.time.get_ticks()

    print("开始测试...")

    while running:
        frame_start = time.time()

        # 处理事件(允许ESC退出)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 更新游戏
        if game.game_state == 'playing' and not game.paused:
            game.update()
            frame_count += 1

        # 绘制(但不flip,减少开销)
        # game.draw()  # 跳过绘制以专注测试AI性能

        # 时间控制
        game.clock.tick(GAME_CONFIG['FPS'])

        frame_time = time.time() - frame_start
        frame_times.append(frame_time)

        # 测试时长检查
        elapsed = (pygame.time.get_ticks() - test_start) / 1000.0
        if elapsed >= duration_seconds:
            running = False

    # 统计结果
    total_time = time.time() - start_time
    avg_frame_time = sum(frame_times) / len(frame_times) if frame_times else 0
    max_frame_time = max(frame_times) if frame_times else 0
    min_frame_time = min(frame_times) if frame_times else 0

    # 计算AI统计
    enemy_count = len(game.enemies)
    ai_enabled_count = sum(1 for e in game.enemies if hasattr(e, 'ai_enabled') and e.ai_enabled)

    pygame.quit()

    print("\n=== 性能测试结果 ===")
    print(f"总运行时间: {total_time:.2f}秒")
    print(f"总帧数: {frame_count}")
    print(f"平均FPS: {frame_count/total_time:.1f}")
    print(f"平均帧时间: {avg_frame_time*1000:.2f}ms")
    print(f"最大帧时间: {max_frame_time*1000:.2f}ms")
    print(f"最小帧时间: {min_frame_time*1000:.2f}ms")
    print(f"\n敌人数量: {enemy_count}")
    print(f"启用智能AI: {ai_enabled_count}")
    print(f"玩家射击: {game.stats['shots_fired']}")
    print(f"击毁敌人: {game.stats['enemies_destroyed']}")
    print("=" * 30)

    # 判断性能
    avg_fps = frame_count / total_time
    if avg_fps >= 50:
        print("✅ 性能优秀 (FPS ≥ 50)")
    elif avg_fps >= 30:
        print("⚠️ 性能可接受 (30 ≤ FPS < 50)")
    else:
        print("❌ 性能较差 (FPS < 30)")

    return avg_fps

if __name__ == '__main__':
    test_smart_ai_performance(duration_seconds=10)
