#!/usr/bin/env python3
"""捕获数组歧义错误的精确位置"""

import sys
import traceback
import numpy as np

def custom_excepthook(exc_type, exc_value, exc_traceback):
    """自定义异常钩子来捕获数组错误"""
    if "ambiguous" in str(exc_value):
        print("🔥 捕获到数组歧义错误!")
        print("📍 错误位置:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("\n📊 堆栈分析:")
        for frame_info in traceback.extract_tb(exc_traceback):
            print(f"  文件: {frame_info.filename}")
            print(f"  行号: {frame_info.lineno}")
            print(f"  函数: {frame_info.name}")
            print(f"  代码: {frame_info.line}")
            print("  ---")
    else:
        # 默认处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

# 安装自定义异常钩子
sys.excepthook = custom_excepthook

if __name__ == "__main__":
    print("🔍 数组错误调试工具已启动")
    print("现在运行训练器...")
    
    # 导入并运行训练器
    try:
        from trainer import ModernChessTrainer
        
        trainer = ModernChessTrainer()
        
        # 运行几局来触发错误
        trainer.run_training(num_games=4, opponent_type='basic', training_mode='quick')
        
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        traceback.print_exc()
