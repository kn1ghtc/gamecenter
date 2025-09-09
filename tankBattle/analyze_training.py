#!/usr/bin/env python3
"""分析训练优化前后的表现对比"""
import json
import numpy as np

def analyze_training_logs():
    # 读取训练日志
    logs = []
    with open('ai/models/training_log.jsonl', 'r') as f:
        for line in f:
            logs.append(json.loads(line))

    # 分析新旧数据（最后6条是优化后的）
    old_data = logs[:-6]  # 前100条是优化前的
    new_data = logs[-6:]  # 最后6条是优化后的

    print('🔍 优化前后对比分析')
    print('=' * 60)

    if old_data:
        old_rewards = [log['reward'] for log in old_data]
        old_win_rates = [log['win_rate'] for log in old_data]
        old_epsilons = [log['epsilon'] for log in old_data]
        
        print(f'📊 优化前 (前{len(old_data)}回合):')
        print(f'  平均奖励: {np.mean(old_rewards):.2f}')
        print(f'  最大奖励: {max(old_rewards):.2f}')
        print(f'  最小奖励: {min(old_rewards):.2f}')
        print(f'  最终胜率: {old_win_rates[-1]:.2%}')
        print(f'  最终ε值: {old_epsilons[-1]:.4f}')

    print()
    new_rewards = [log['reward'] for log in new_data]
    new_win_rates = [log['win_rate'] for log in new_data]
    new_epsilons = [log['epsilon'] for log in new_data]

    print(f'📊 优化后 (最新{len(new_data)}回合):')
    print(f'  平均奖励: {np.mean(new_rewards):.2f}')
    print(f'  最大奖励: {max(new_rewards):.2f}')
    print(f'  最小奖励: {min(new_rewards):.2f}')
    print(f'  最终胜率: {new_win_rates[-1]:.2%}')
    print(f'  最终ε值: {new_epsilons[-1]:.4f}')

    print()
    print('🚀 改进效果:')
    if old_data:
        reward_improvement = np.mean(new_rewards) - np.mean(old_rewards)
        win_rate_improvement = new_win_rates[-1] - old_win_rates[-1]
        print(f'  奖励改进: {reward_improvement:+.2f}')
        print(f'  胜率改进: {win_rate_improvement:+.2%}')

    print()
    print('📈 优化后详细表现:')
    for i, log in enumerate(new_data, 1):
        won_str = '✅' if log['won'] else '❌'
        print(f'  回合{i}: 奖励={log["reward"]:.1f} {won_str}, 胜率={log["win_rate"]:.1%}, ε={log["epsilon"]:.3f}')
    
    # 分析关键指标
    print()
    print('🎯 关键改进指标:')
    print(f'  探索率(ε)健康度: {"✅正常" if new_epsilons[-1] > 0.03 else "⚠️过低"}')
    print(f'  奖励稳定性: {"✅改善" if np.std(new_rewards) < 100 else "⚠️波动大"}')
    print(f'  胜利突破: {"🏆首胜！" if any(log["won"] for log in new_data) else "❌尚未胜利"}')
    
    if old_data and any(log['won'] for log in new_data):
        print('  🎉 优化成功！AI已能获胜')
    
if __name__ == '__main__':
    analyze_training_logs()
