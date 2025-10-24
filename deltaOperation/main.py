"""
三角洲行动 - 游戏主入口
Delta Force: Shadow Operations

使用方法:
    python main.py             # 正常窗口模式
    python main.py --test      # 无头测试模式
    python main.py --headless  # 无头模式(用于测试)
"""

import os
import sys
import argparse
import warnings

# 过滤 pygame 的 pkg_resources 弃用警告
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import pygame

# 设置Windows控制台为UTF-8编码
os.system("chcp 65001 >nul 2>&1")

# 设置项目根路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 绝对导入
from gamecenter.deltaOperation import config
from gamecenter.deltaOperation.core.game_state import GameState


def print_welcome():
    """打印欢迎信息"""
    print("="*70)
    print("三角洲行动 - Delta Force: Shadow Operations")
    print("="*70)
    print("\n游戏控制:")
    print("  WASD - 移动")
    print("  空格 - 射击")
    print("  R    - 换弹")
    print("  Q    - 切换武器")
    print("  H    - 帮助/提示")
    print("  ESC  - 暂停/退出")
    print("\n调试快捷键:")
    print("  F1 - 小地图开关")
    print("  F2 - 放大(2x)")
    print("  F3 - 正常(1x)")
    print("  F4 - 屏幕震动")
    print("  F5 - 快速保存")
    print("  F9 - 快速读取")
    print("\n正在启动游戏...\n")


def main(headless=False, test_frames=0, enable_multiplayer=False):
    """
    游戏主函数
    
    Args:
        headless: 是否以无头模式运行(用于测试)
        test_frames: 测试模式运行帧数(0=无限制)
        enable_multiplayer: 是否启用双人模式
    """
    # 初始化Pygame
    pygame.init()
    pygame.mixer.init()
    
    # 设置无头模式
    if headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    
    # 创建游戏窗口
    if headless:
        screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT),
            pygame.HIDDEN
        )
    else:
        screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(config.WINDOW_TITLE)
    
    # 创建时钟对象
    clock = pygame.time.Clock()
    
    # 创建游戏状态管理器 (传递multiplayer标志)
    game_state = GameState(screen, headless=headless, enable_multiplayer=enable_multiplayer)
    
    # 游戏主循环
    running = True
    frame_count = 0
    
    try:
        while running:
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    game_state.handle_event(event)
            
            # 更新游戏状态
            delta_time = clock.get_time() / 1000.0  # 转换为秒
            game_state.update(delta_time)
            
            # 渲染
            if not headless:
                game_state.render()
                pygame.display.flip()
            
            # 控制帧率
            clock.tick(config.FPS)
            
            # 测试模式帧数限制
            if test_frames > 0:
                frame_count += 1
                if frame_count >= test_frames:
                    print(f"\n[测试完成] 运行{frame_count}帧成功!")
                    running = False
            
            # 检查是否退出
            if game_state.should_quit():
                running = False
    
    except KeyboardInterrupt:
        print("\n\n游戏被用户中断")
    except Exception as e:
        print(f"\n游戏运行错误: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # 清理
        pygame.quit()
    
    sys.exit(0)


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="三角洲行动 - Delta Force: Shadow Operations"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行(不显示窗口,用于测试)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="测试模式(等同于--headless)"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="烟雾测试模式(等同于--headless)"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=300,
        help="测试模式运行帧数(默认300帧=5秒@60FPS)"
    )
    parser.add_argument(
        "--multiplayer",
        action="store_true",
        help="启用双人模式 (Player 2 uses Arrow Keys + RShift/RCtrl)"
    )
    
    args = parser.parse_args()
    
    # 确定是否无头模式
    headless_mode = args.headless or args.test or args.smoke_test
    test_frames = args.frames if headless_mode else 0
    
    # 打印欢迎信息
    if headless_mode:
        print("="*70)
        print(f"无头测试模式 - 运行{test_frames}帧")
        print("="*70)
    else:
        print_welcome()
        if args.multiplayer:
            print("[双人模式] Player 2 Controls:")
            print("  Arrow Keys - 移动")
            print("  RShift     - 射击")
            print("  RCtrl      - 换弹")
            print("  Enter      - 切换武器")
            print("")
    
    # 启动游戏
    main(headless=headless_mode, test_frames=test_frames, enable_multiplayer=args.multiplayer)
