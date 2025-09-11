"""
国际象棋游戏主程序
Professional Chess Game - 主入口
"""
import sys
import os

# 添加项目路径到系统路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    # 先加载配置
    from config.settings import PATHS, DATABASE_PATH
    
    # 仅按需导入
    from ui.gui import ChessUI
    import pygame
    
    def main():
        """主函数"""
        print("🏆 Starting Professional Chess Game...")
        print("Loading game components...")
        print(f"📁 Models: {PATHS['models']}")
        print(f"🗄️ Database: {DATABASE_PATH}")
        
        try:
            chess_game = ChessUI()
            print("✅ Game initialized successfully!")
            print("🎮 Starting game interface...")
            chess_game.run()
        except Exception as e:
            print(f"❌ Error starting game: {e}")
            import traceback
            traceback.print_exc()
            input("Press Enter to exit...")
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    input("Press Enter to exit...")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
