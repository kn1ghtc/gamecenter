#!/usr/bin/env python3
"""
StreetBattle 测试运行器

这个脚本运行所有测试套件，包括单元测试和集成测试。
"""

import sys
import os
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("StreetBattle 测试套件")
    print("=" * 60)
    
    # 运行所有测试
    test_dir = Path(__file__).parent
    
    # 收集所有测试文件
    test_files = [
        "test_config_manager.py",
        "test_character_system.py", 
        "test_audio_system.py",
        "test_game_settings.py",
        "test_skill_system.py",
        "test_portrait_system.py",
        "test_player_system.py",
        "test_integration.py"
    ]
    
    # 运行每个测试文件
    exit_code = 0
    for test_file in test_files:
        test_path = test_dir / test_file
        if test_path.exists():
            print(f"\n运行测试: {test_file}")
            print("-" * 40)
            
            # 运行单个测试文件
            result = pytest.main([
                str(test_path),
                "-v",  # 详细输出
                "--tb=short",  # 简短的错误回溯
                "--disable-warnings"  # 禁用警告
            ])
            
            if result != 0:
                exit_code = result
                print(f"❌ {test_file} 测试失败")
            else:
                print(f"✅ {test_file} 测试通过")
    
    # 运行所有测试的汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    if exit_code == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    
    return exit_code

def run_specific_test(test_name: str):
    """运行特定测试"""
    print(f"运行特定测试: {test_name}")
    
    # 构建测试路径
    test_path = Path(__file__).parent / f"test_{test_name}.py"
    
    if not test_path.exists():
        print(f"❌ 测试文件不存在: {test_path}")
        return 1
    
    # 运行特定测试
    result = pytest.main([
        str(test_path),
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
    
    return result

if __name__ == "__main__":
    # 解析命令行参数
    if len(sys.argv) > 1:
        # 运行特定测试
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # 运行所有测试
        exit_code = run_all_tests()
    
    sys.exit(exit_code)