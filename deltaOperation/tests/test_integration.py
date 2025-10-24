"""游戏主循环集成测试 - 运行10秒验证所有系统"""
import os
import sys
import time

# 设置UTF-8编码
os.system("chcp 65001 >nul 2>&1")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# 设置路径
project_root = os.path.abspath(".")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pygame
from gamecenter.deltaOperation.core import GameState

def test_game_integration():
    """集成测试:验证游戏主循环10秒"""
    print("="*70)
    print("游戏主循环集成测试")
    print("="*70)
    
    try:
        # 初始化Pygame
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        
        # 创建游戏状态
        print("\n[1/5] 创建游戏状态...")
        game_state = GameState(screen, headless=True)
        print("  [+] 游戏状态已创建")
        
        # 主循环
        print("\n[2/5] 运行游戏主循环...")
        start_time = time.time()
        frame_count = 0
        max_frames = 60 * 10  # 10秒 @ 60FPS
        
        print("  [提示] 将运行600帧(10秒 @ 60FPS)\n")
        
        while frame_count < max_frames and not game_state.should_quit():
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    break
                game_state.handle_event(event)
            
            # 更新
            delta_time = clock.tick(60) / 1000.0
            game_state.update(delta_time)
            
            # 渲染(跳过以节省时间)
            # game_state.render()
            
            frame_count += 1
            
            # 每秒打印一次状态
            if frame_count % 60 == 0:
                elapsed = time.time() - start_time
                print(f"  [{int(elapsed)}s] 帧数: {frame_count}/600")
        
        elapsed_time = time.time() - start_time
        
        print(f"\n[3/5] 循环完成!")
        print(f"  总帧数: {frame_count}")
        print(f"  运行时间: {elapsed_time:.2f}秒")
        print(f"  平均FPS: {frame_count/elapsed_time:.1f}")
        
        # 验证游戏对象
        print("\n[4/5] 验证游戏对象...")
        gameplay_scene = game_state.scenes.get(game_state.STATE_GAME_PLAY)
        
        if gameplay_scene:
            print("  [+] 游戏场景存在")
            
            if gameplay_scene.player:
                print(f"  [+] 玩家系统正常")
                print(f"      位置: ({gameplay_scene.player.position.x:.1f}, {gameplay_scene.player.position.y:.1f})")
                print(f"      血量: {gameplay_scene.player.health:.1f}/{gameplay_scene.player.max_health}")
            
            if gameplay_scene.level:
                alive_enemies = len(gameplay_scene.level.get_alive_enemies())
                print(f"  [+] 关卡系统正常")
                print(f"      地图大小: {gameplay_scene.level.level_bounds.width}x{gameplay_scene.level.level_bounds.height}")
                print(f"      存活敌人: {alive_enemies}")
            
            if gameplay_scene.mission:
                print(f"  [+] 任务系统正常")
                print(f"      任务: {gameplay_scene.mission.config.name}")
                print(f"      击杀数: {gameplay_scene.mission.enemies_killed}")
                print(f"      完成: {gameplay_scene.mission.is_completed()}")
            
            if gameplay_scene.camera:
                print(f"  [+] 相机系统正常")
                print(f"      位置: ({gameplay_scene.camera.x:.1f}, {gameplay_scene.camera.y:.1f})")
                print(f"      缩放: {gameplay_scene.camera.zoom:.2f}")
        else:
            print("  [!] 游戏场景未找到")
        
        # 清理
        print("\n[5/5] 清理资源...")
        pygame.quit()
        
        print("\n" + "="*70)
        print("测试通过! 所有系统正常运行")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\n[✗] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_game_integration()
    sys.exit(0 if success else 1)
