"""
快速启动脚本 - 3D格斗游戏
Quick Launch Script - 3D Fighting Game

一键启动修复后的3D格斗游戏
One-click launch for the fixed 3D fighting game
"""

import subprocess
import sys
import os
from pathlib import Path

def launch_game():
    """启动3D格斗游戏"""
    print("🎮 启动修复后的3D格斗游戏...")
    print("🎮 Launching fixed 3D Fighting Game...")
    print("")
    print("✅ 所有修复已应用:")
    print("   ✅ 角色模型智能缩放 - 解决巨大模型问题")
    print("   ✅ Iori角色可见性修复 - 不再是白色透明")
    print("   ✅ 键盘输入安全强化 - 防止崩溃")
    print("   ✅ 3D动画状态机实现 - 完整动画系统")
    print("   ✅ 性能优化系统 - 智能加载")
    print("   ✅ 控制台输出优化 - 减少冗余信息")
    print("")
    print("🎮 操作说明:")
    print("   - WASD/方向键: 移动和导航")
    print("   - 回车/空格键: 选择确认")
    print("   - ESC: 取消/返回")
    print("   - 游戏中: WASD移动，JK攻击，空格跳跃")
    print("")
    
    # 确保在正确目录
    game_dir = Path(__file__).parent
    os.chdir(game_dir)
    
    try:
        # 启动游戏
        result = subprocess.run([sys.executable, "main.py"], 
                              cwd=game_dir, 
                              check=False)
        
        if result.returncode == 0:
            print("🎉 游戏正常退出")
        elif result.returncode == 1:
            print("✅ 游戏被用户中断(正常)")
        else:
            print(f"⚠️  游戏退出代码: {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n✅ 游戏被用户中断")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔧 故障排除:")
        print("   1. 确保已安装 Panda3D")
        print("   2. 检查 Python 环境")
        print("   3. 运行综合测试: python test_comprehensive_fixes.py")


if __name__ == "__main__":
    launch_game()