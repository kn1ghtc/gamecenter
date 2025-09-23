# -*- coding: utf-8 -*-
"""
国际象棋游戏主程序
Professional Chess Game - 主入口
"""
import sys
import os

# 确保控制台输出支持UTF-8
if sys.platform == "win32":
    import locale
    try:
        # 设置控制台编码为UTF-8
        import os
        os.system("chcp 65001 >nul 2>&1")
    except:
        pass

# 添加项目路径到系统路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    def main():
        """主函数 - 延迟加载优化启动"""
        print("🏆 Starting Professional Chess Game...")
        
        # 基础配置加载（快速）
        from config.settings import PATHS, DATABASE_PATH
        print("✅ 基础配置加载完成")
        
        # 延迟加载重量级模块
        print("🎮 Starting game interface...")
        try:
            # 按需导入UI模块
            from ui.gui import ChessUI
            
            print(f"📁 Models: {PATHS['models']}")
            print(f"🗄️ Database: {DATABASE_PATH}")
            
            chess_game = ChessUI()
            print("✅ Game initialized successfully!")
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
