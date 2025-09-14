#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速训练启动脚本
===============
一键启动离线强化学习训练
"""

import os
import sys
import argparse
import json
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

def create_training_config():
    """创建最优训练配置文件"""
    config = {
        "environment": {
            "map_width": 1500,
            "map_height": 900,
            "max_episode_steps": 3000,  # 更长的episode获得更好的学习效果
            "training_mode": True,
            "render": False  # 训练时不渲染提高速度
        },
        "training": {
            "use_gpu": True,          # 启用GPU（如果可用）
            "total_episodes": 10000,  # 更多的训练回合
            "save_frequency": 100,
            "eval_frequency": 200,   
            "target_win_rate": 0.8,  # 更高的目标胜率
            "early_stopping_patience": 1000,  # 更大的耐心值
            "warmup_episodes": 200,  # 更长的预热期
            "replay_frequency": 1,   # 每步都学习
            "num_envs": 4            # 向量化环境数量（1-16）
        },
        "agent": {
            "use_gpu": True,          # 启用GPU（如果可用）
            "learning_rate": 0.0002,  # 提高学习率，加速初期学习
            "epsilon_start": 1.0,
            "epsilon_end": 0.05,      # 提高最小探索率
            "epsilon_decay": 0.9998,  # 减慢衰减速度
            "batch_size": 256,         # 更大的批次
            "memory_size": 100000,    # 更大的经验池
            "target_update_frequency": 300,  # 减慢目标网络更新
            "double_dqn": True,       # 启用Double DQN
            "dueling_dqn": False,     # 暂时禁用以保持稳定
            "gradient_clipping": 1.0,
            "weight_decay": 1e-4
        },
        "optimization": {
            "use_gpu": True,          # 启用GPU（如果可用）
            "mixed_precision": False, # 暂时禁用混合精度训练
            "lr_scheduler": "cosine", # 余弦退火学习率
            "min_lr": 1e-6
        }
    }
    
    config_path = current_dir / "training_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 最优训练配置已创建: {config_path}")
    return config_path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='坦克大战AI离线训练')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--resume', type=str, help='从指定模型继续训练')
    parser.add_argument('--episodes', type=int, default=5000, help='训练回合数')
    parser.add_argument('--eval', action='store_true', help='评估模式')
    parser.add_argument('--eval-episodes', type=int, default=100, help='评估回合数，默认100')
    parser.add_argument('--model', type=str, help='评估的模型路径')
    
    args = parser.parse_args()
    
    print("🤖 坦克大战AI快速训练启动器")
    print("=" * 50)
    
    # 检查依赖
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ PyTorch可用 (GPU: {torch.cuda.get_device_name(0)})")
        else:
            print("✅ PyTorch可用 (CPU)")
    except ImportError:
        print("❌ PyTorch不可用，请安装: pip install torch")
        return
    
    try:
        import numpy as np
        print("✅ NumPy可用")
    except ImportError:
        print("❌ NumPy不可用，请安装: pip install numpy")
        return
    
    try:
        from tqdm import tqdm
        print("✅ 进度条支持可用")
    except ImportError:
        print("⚠️ tqdm不可用，将使用简单进度显示")
        print("建议安装: pip install tqdm")
    
    # 创建配置
    if not args.config:
        config_path = create_training_config()
    else:
        config_path = args.config
    
    # 导入训练器
    try:
        from ai.offline_training import OfflineTrainer
        
        if args.eval:
            # 评估模式
            if not args.model:
                print("❌ 评估模式需要指定模型路径: --model <path>")
                return
            
            trainer = OfflineTrainer(config_path)
            print(f"🔍 评估模型: {args.model}")
            results = trainer.evaluate(args.model, num_episodes=max(1, int(args.eval_episodes)))
            
            print(f"\n📊 评估结果:")
            print(f"胜率: {results['win_rate']:.1%}")
            print(f"平均奖励: {results['average_reward']:.2f}")
            
        else:
            # 训练模式
            print(f"🚀 开始训练，目标回合数: {args.episodes}")
            
            # 更新配置中的回合数
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['training']['total_episodes'] = args.episodes
            
            # 调整保存频率：每100轮保存一次
            config['training']['save_frequency'] = 100
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 使用更新后的配置创建训练器
            trainer = OfflineTrainer(config_path)
            trainer.train(resume_from=args.resume)
            
    except ImportError as e:
        print(f"❌ 导入训练器失败: {e}")
        print("请确保在tankBattle目录下运行")
    except Exception as e:
        print(f"❌ 训练出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
