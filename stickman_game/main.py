#!/usr/bin/env python3
"""
主程序入口
简化版单人火柴人动作冒险游戏
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """主函数"""
    try:
        import pygame
        from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
        from src.game import Game
        
        print("🎮 火柴人冒险游戏")
        print("正在加载...")
        
        # 初始化pygame
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("火柴人动作冒险游戏 - 单人模式")
        
        # 创建并运行游戏（传递screen引用以支持全屏切换）
        game = Game()
        game.screen = screen  # 添加screen引用
        print("游戏启动成功！按F11切换全屏模式")
        game.run()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖已正确安装: pip install pygame")
        
    except Exception as e:
        print(f"启动失败: {e}")
        
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()