"""
资源下载工具

可选的资源下载脚本，用于预先下载游戏资源
游戏可以在没有这些资源的情况下正常运行
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gamecenter.tetris.src.resource_manager import ResourceManager


def main():
    """主函数"""
    print("=" * 60)
    print("    俄罗斯方块 - 资源下载工具")
    print("=" * 60)
    print("\n注意: 资源下载是可选的，游戏可以在没有这些资源的情况下运行")
    print("      系统将使用内置字体和静音模式\n")
    
    # 创建资源管理器（启用自动下载）
    rm = ResourceManager(auto_download=True)
    
    # 检查缺失资源
    missing = rm.get_missing_resources()
    
    if not missing:
        print("✓ 所有资源已就绪！\n")
        
        # 显示资源状态
        print("资源清单:")
        status = rm.check_all_resources()
        for key, exists in status.items():
            symbol = "✓" if exists else "✗"
            print(f"  {symbol} {key}")
        return
    
    print(f"发现 {len(missing)} 个缺失资源:")
    for key in missing:
        print(f"  • {key}")
    
    print("\n是否开始下载? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice != 'y':
        print("\n已取消下载。游戏仍然可以正常运行。")
        return
    
    # 开始下载
    print()
    rm.download_all_resources()
    
    # 显示最终状态
    print("\n最终资源状态:")
    status = rm.check_all_resources()
    for key, exists in status.items():
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {key}")
    
    print("\n完成！现在可以启动游戏了。")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消。")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
