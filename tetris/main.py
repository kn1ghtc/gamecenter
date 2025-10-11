"""
俄罗斯方块游戏主入口

增强版俄罗斯方块，支持100关卡、精美UI、动态效果
"""
import os
import sys

# Windows控制台UTF-8编码
os.system("chcp 65001 >nul 2>&1")

from gamecenter.tetris.src.game_enhanced import TetrisGame


def main():
    """游戏入口函数"""
    print("=" * 60)
    print("     俄罗斯方块 - Tetris Enhanced")
    print("=" * 60)
    print("\n游戏特性:")
    print("  • 100 关卡系统")
    print("  • 精美3D方块效果")
    print("  • 粒子特效和动画")
    print("  • 连击系统")
    print("  • 自适应屏幕")
    print("  • 音效和背景音乐")
    print("\n正在启动游戏...\n")
    
    try:
        game = TetrisGame()
        game.run()
    except KeyboardInterrupt:
        print("\n\n游戏已退出。")
    except Exception as e:
        print(f"\n游戏运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
