#!/usr/bin/env python3
"""调试数组错误的简化测试"""

import numpy as np
import torch

# 测试所有可能导致数组歧义错误的情况
def test_array_conditions():
    print("🔍 测试数组条件判断...")
    
    # 测试1: 空数组
    empty_array = np.array([])
    print(f"空数组: {empty_array}, size: {empty_array.size}")
    try:
        if empty_array and empty_array.size > 0:
            print("✅ 空数组条件OK")
    except Exception as e:
        print(f"❌ 空数组条件错误: {e}")
    
    # 测试2: 多维数组
    features = np.zeros((12, 8, 8))
    print(f"多维数组: shape {features.shape}, size: {features.size}")
    try:
        if features is not None and features.size > 0:
            print("✅ 多维数组条件OK")
    except Exception as e:
        print(f"❌ 多维数组条件错误: {e}")
    
    # 测试3: 列表中的数组
    feature_list = [np.zeros((12, 8, 8)), np.zeros((12, 8, 8))]
    print(f"数组列表: 长度 {len(feature_list)}")
    try:
        if feature_list:
            print("✅ 数组列表条件OK")
    except Exception as e:
        print(f"❌ 数组列表条件错误: {e}")
    
    # 测试4: np.array()转换
    try:
        features_array = np.array(feature_list)
        print(f"✅ np.array转换OK: {features_array.shape}")
    except Exception as e:
        print(f"❌ np.array转换错误: {e}")
    
    # 测试5: 可能的问题条件
    try:
        # 这可能是问题所在
        if np.array([1, 2, 3]):
            print("❌ 这里会有问题!")
    except ValueError as e:
        print(f"✅ 找到问题: {e}")
    
    # 测试6: 正确的方式
    test_array = np.array([1, 2, 3])
    if test_array.size > 0:
        print("✅ 正确的数组条件判断")

if __name__ == "__main__":
    test_array_conditions()
