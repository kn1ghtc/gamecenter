#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线强化学习训练系统
==================
用于快速训练智能AI坦克模型 - 优化版本
"""

import os
import sys
import time
import random
import numpy as np
import json
import pygame
from collections import deque
from typing import Dict, List, Tuple, Optional
import threading
import multiprocessing

# 进度条支持
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # 简单的进度条替代
    class tqdm:
        def __init__(self, iterable=None, total=None, desc="", **kwargs):
            self.iterable = iterable
            self.total = total
            self.desc = desc
            self.n = 0
            self.start_time = time.time()
        
        def __iter__(self):
            for item in self.iterable:
                yield item
                self.update(1)
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
        
        def update(self, n=1):
            self.n += n
            if self.n % 10 == 0:
                elapsed = time.time() - self.start_time
                rate = self.n / elapsed if elapsed > 0 else 0
                print(f"\r{self.desc}: {self.n}/{self.total if self.total else '?'} [{rate:.1f}it/s]", end="", flush=True)
        
        def set_postfix(self, **kwargs):
            if self.n % 5 == 0:
                status = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
                print(f" ({status})", end="", flush=True)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from .reinforcement_learning import TankRLAgent
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("PyTorch不可用，训练将使用基础算法")

class TankBattleTrainingEnvironment:
    """坦克大战训练环境模拟器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.map_width = config.get('map_width', 1500)
        self.map_height = config.get('map_height', 900)
        self.max_episode_steps = config.get('max_episode_steps', 3000)
        
        # 训练状态
        self.current_step = 0
        self.episode_count = 0
        self.total_reward = 0
        
        # 环境状态
        self.tank_position = (self.map_width // 2, self.map_height // 2)
        self.tank_angle = 0
        self.tank_health = 100
        
        # 模拟玩家位置
        self.player_position = (200, 200)
        self.player_health = 100
        self.player_velocity = (0, 0)
        
        # 模拟墙体和障碍物
        self.walls = self._generate_walls()
        self.special_walls = self._generate_special_walls()
        
        # 游戏对象状态
        self.bullets = []
        self.last_shot_time = 0
        self.shot_cooldown = 20  # 帧数
        
        # 奖励参数 - 重新平衡，避免过高胜率
        self.reward_config = {
            'survival': 0.01,          # 降低存活奖励
            'hit_player': 10.0,        # 命中玩家奖励
            'kill_player': 100.0,      # 击杀玩家奖励
            'damage_taken': -5.0,      # 增加受伤惩罚
            'death': -50.0,            # 增加死亡惩罚
            'movement': 0.005,         # 降低移动奖励
            'stuck_penalty': -0.5,     # 增加卡住惩罚
            'wall_hit': 2.0,           # 击中特殊墙体
            'distance_to_player': 0.001, # 降低接近奖励
            'miss_shot': -1.0,         # 新增：射击未命中惩罚
            'efficient_movement': 0.1,  # 新增：高效移动奖励
            'defensive_bonus': 0.5     # 新增：防守奖励
        }
    
    def _generate_walls(self) -> List[Dict]:
        """生成训练用墙体"""
        walls = []
        
        # 边界墙
        walls.extend([
            {'x': 0, 'y': 0, 'width': self.map_width, 'height': 25},  # 上
            {'x': 0, 'y': self.map_height-25, 'width': self.map_width, 'height': 25},  # 下
            {'x': 0, 'y': 0, 'width': 25, 'height': self.map_height},  # 左
            {'x': self.map_width-25, 'y': 0, 'width': 25, 'height': self.map_height},  # 右
        ])
        
        # 随机内部墙体
        for _ in range(10):
            x = random.randint(100, self.map_width - 200)
            y = random.randint(100, self.map_height - 200)
            width = random.randint(50, 150)
            height = random.randint(25, 50)
            walls.append({'x': x, 'y': y, 'width': width, 'height': height, 'health': 100})
        
        return walls
    
    def _generate_special_walls(self) -> List[Dict]:
        """生成特殊墙体"""
        special_walls = []
        effects = ['piercing_ammo', 'explosive_ammo', 'speed_boost', 'shield', 'multi_shot']
        
        for i in range(5):
            x = random.randint(200, self.map_width - 200)
            y = random.randint(200, self.map_height - 200)
            special_walls.append({
                'x': x, 'y': y, 'width': 50, 'height': 50,
                'effect': random.choice(effects),
                'health': 50
            })
        
        return special_walls
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        self.current_step = 0
        self.total_reward = 0
        
        # 重置坦克状态
        self.tank_position = (
            random.randint(100, self.map_width - 100),
            random.randint(100, self.map_height - 100)
        )
        self.tank_angle = random.uniform(0, 2 * np.pi)
        self.tank_health = 100
        
        # 重置玩家状态
        self.player_position = (
            random.randint(100, self.map_width - 100),
            random.randint(100, self.map_height - 100)
        )
        self.player_health = 100
        self.player_velocity = (
            random.uniform(-2, 2),
            random.uniform(-2, 2)
        )
        
        # 清空子弹
        self.bullets = []
        self.last_shot_time = 0
        
        return self._get_state()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        self.current_step += 1
        
        # 执行动作
        reward = self._execute_action(action)
        
        # 更新环境
        self._update_environment()
        
        # 检查终止条件
        done = self._check_done()
        
        # 获取新状态
        next_state = self._get_state()
        
        info = {
            'episode_step': self.current_step,
            'tank_health': self.tank_health,
            'player_health': self.player_health,
            'distance_to_player': self._get_distance_to_player()
        }
        
        self.total_reward += reward
        
        return next_state, reward, done, info
    
    def _execute_action(self, action: int) -> float:
        """执行动作并返回奖励"""
        reward = self.reward_config['survival']  # 基础存活奖励
        
        old_position = self.tank_position
        
        # 动作映射
        if action == 0:  # 前进
            new_x = self.tank_position[0] + 2 * np.cos(self.tank_angle)
            new_y = self.tank_position[1] + 2 * np.sin(self.tank_angle)
            new_pos = (new_x, new_y)
            
            if self._is_valid_position(new_pos):
                self.tank_position = new_pos
                reward += self.reward_config['movement']
        
        elif action == 1:  # 后退
            new_x = self.tank_position[0] - 1 * np.cos(self.tank_angle)
            new_y = self.tank_position[1] - 1 * np.sin(self.tank_angle)
            new_pos = (new_x, new_y)
            
            if self._is_valid_position(new_pos):
                self.tank_position = new_pos
                reward += self.reward_config['movement'] * 0.5
        
        elif action == 2:  # 左转
            self.tank_angle -= 0.1
            if self.tank_angle < 0:
                self.tank_angle += 2 * np.pi
        
        elif action == 3:  # 右转
            self.tank_angle += 0.1
            if self.tank_angle >= 2 * np.pi:
                self.tank_angle -= 2 * np.pi
        
        elif action in [4, 5, 6]:  # 射击 (普通/穿甲/爆炸)
            if self.current_step - self.last_shot_time >= self.shot_cooldown:
                bullet_type = ['normal', 'piercing', 'explosive'][action - 4]
                hit_reward = self._simulate_shot(bullet_type)
                reward += hit_reward
                self.last_shot_time = self.current_step
        
        # 检查是否卡住
        distance_moved = np.sqrt(
            (self.tank_position[0] - old_position[0])**2 + 
            (self.tank_position[1] - old_position[1])**2
        )
        if distance_moved < 0.5:
            reward += self.reward_config['stuck_penalty']
        
        # 距离奖励
        distance_to_player = self._get_distance_to_player()
        if distance_to_player < 300:
            reward += self.reward_config['distance_to_player'] * (300 - distance_to_player)
        
        return reward
    
    def _simulate_shot(self, bullet_type: str) -> float:
        """模拟射击并返回奖励 - 重新平衡命中率"""
        # 简化的射击命中检测
        distance_to_player = self._get_distance_to_player()
        
        # 超出射程
        if distance_to_player > 400:
            return self.reward_config['miss_shot'] * 0.5  # 轻微惩罚
        
        # 角度差计算
        dx = self.player_position[0] - self.tank_position[0]
        dy = self.player_position[1] - self.tank_position[1]
        target_angle = np.arctan2(dy, dx)
        angle_diff = abs(self.tank_angle - target_angle)
        if angle_diff > np.pi:
            angle_diff = 2 * np.pi - angle_diff
        
        # 重新平衡命中概率 - 降低过高的命中率
        distance_factor = max(0, 1 - distance_to_player / 400)
        angle_factor = max(0, 1 - angle_diff / 0.3)  # 更严格的角度要求
        
        # 基础命中率降低
        base_hit_rate = 0.4  # 从0.8降低到0.4
        hit_probability = distance_factor * angle_factor * base_hit_rate
        
        # 子弹类型修正
        type_multipliers = {'normal': 1.0, 'piercing': 1.15, 'explosive': 1.25}
        hit_probability *= type_multipliers.get(bullet_type, 1.0)
        
        # 添加随机性以增加挑战
        hit_probability *= random.uniform(0.7, 1.3)
        
        if random.random() < hit_probability:
            # 命中！
            damage_map = {'normal': 20, 'piercing': 25, 'explosive': 30}  # 略微降低伤害
            damage = damage_map[bullet_type]
            self.player_health -= damage
            
            reward = self.reward_config['hit_player']
            if self.player_health <= 0:
                reward += self.reward_config['kill_player']
            
            return reward
        else:
            # 未命中惩罚
            return self.reward_config['miss_shot']
    
    def _update_environment(self):
        """更新环境状态"""
        # 模拟玩家移动
        new_player_x = self.player_position[0] + self.player_velocity[0]
        new_player_y = self.player_position[1] + self.player_velocity[1]
        
        # 边界检查
        new_player_x = max(50, min(self.map_width - 50, new_player_x))
        new_player_y = max(50, min(self.map_height - 50, new_player_y))
        
        self.player_position = (new_player_x, new_player_y)
        
        # 随机改变玩家速度
        if random.random() < 0.05:  # 5%概率改变方向
            self.player_velocity = (
                random.uniform(-2, 2),
                random.uniform(-2, 2)
            )
        
        # 模拟玩家攻击 - 增加挑战性
        if random.random() < 0.04:  # 增加到4%概率攻击
            distance_to_tank = self._get_distance_to_player()
            if distance_to_tank < 350:  # 增加攻击范围
                hit_prob = 0.6 * (1 - distance_to_tank / 350)  # 提高命中率
                if random.random() < hit_prob:
                    damage = random.randint(20, 35)  # 随机伤害
                    self.tank_health -= damage
                    return self.reward_config['damage_taken'] * (damage / 25)
    
    def _is_valid_position(self, position: Tuple[float, float]) -> bool:
        """检查位置是否有效（不与墙体碰撞）"""
        x, y = position
        
        # 边界检查
        if x < 50 or x > self.map_width - 50 or y < 50 or y > self.map_height - 50:
            return False
        
        # 墙体碰撞检查
        tank_rect = {'x': x - 20, 'y': y - 20, 'width': 40, 'height': 40}
        
        for wall in self.walls:
            if self._rect_collision(tank_rect, wall):
                return False
        
        return True
    
    def _rect_collision(self, rect1: Dict, rect2: Dict) -> bool:
        """矩形碰撞检测"""
        return (rect1['x'] < rect2['x'] + rect2['width'] and
                rect1['x'] + rect1['width'] > rect2['x'] and
                rect1['y'] < rect2['y'] + rect2['height'] and
                rect1['y'] + rect1['height'] > rect2['y'])
    
    def _get_distance_to_player(self) -> float:
        """获取到玩家的距离"""
        dx = self.player_position[0] - self.tank_position[0]
        dy = self.player_position[1] - self.tank_position[1]
        return np.sqrt(dx**2 + dy**2)
    
    def _get_state(self) -> np.ndarray:
        """获取当前状态向量"""
        # 128维状态向量
        state = np.zeros(128)
        
        # 坦克状态 (8维)
        state[0] = self.tank_position[0] / self.map_width  # 归一化位置
        state[1] = self.tank_position[1] / self.map_height
        state[2] = np.cos(self.tank_angle)  # 角度的cos和sin
        state[3] = np.sin(self.tank_angle)
        state[4] = self.tank_health / 100  # 归一化生命值
        state[5] = (self.current_step - self.last_shot_time) / self.shot_cooldown  # 射击冷却
        state[6] = self.current_step / self.max_episode_steps  # 时间进度
        state[7] = len(self.bullets) / 10  # 当前子弹数量
        
        # 玩家状态 (8维)
        state[8] = self.player_position[0] / self.map_width
        state[9] = self.player_position[1] / self.map_height
        state[10] = self.player_velocity[0] / 5  # 归一化速度
        state[11] = self.player_velocity[1] / 5
        state[12] = self.player_health / 100
        
        # 相对位置和距离 (8维)
        dx = self.player_position[0] - self.tank_position[0]
        dy = self.player_position[1] - self.tank_position[1]
        distance = np.sqrt(dx**2 + dy**2)
        
        state[13] = dx / self.map_width  # 相对位置
        state[14] = dy / self.map_height
        state[15] = distance / (self.map_width + self.map_height)  # 归一化距离
        
        # 到玩家的角度
        if distance > 0:
            target_angle = np.arctan2(dy, dx)
            angle_diff = target_angle - self.tank_angle
            if angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            elif angle_diff < -np.pi:
                angle_diff += 2 * np.pi
            state[16] = angle_diff / np.pi  # 归一化角度差
        
        # 周围障碍物检测 (32维) - 8个方向，每个方向4个距离层次
        directions = np.linspace(0, 2*np.pi, 8, endpoint=False)
        for i, direction in enumerate(directions):
            for j, check_distance in enumerate([50, 100, 200, 300]):
                check_x = self.tank_position[0] + check_distance * np.cos(direction)
                check_y = self.tank_position[1] + check_distance * np.sin(direction)
                
                obstacle_detected = not self._is_valid_position((check_x, check_y))
                state[17 + i*4 + j] = 1.0 if obstacle_detected else 0.0
        
        # 特殊墙体位置 (30维) - 最多记录6个特殊墙体，每个5维
        for i, wall in enumerate(self.special_walls[:6]):
            base_idx = 49 + i * 5
            wall_dx = wall['x'] - self.tank_position[0]
            wall_dy = wall['y'] - self.tank_position[1]
            wall_distance = np.sqrt(wall_dx**2 + wall_dy**2)
            
            state[base_idx] = wall_dx / self.map_width
            state[base_idx + 1] = wall_dy / self.map_height
            state[base_idx + 2] = wall_distance / (self.map_width + self.map_height)
            state[base_idx + 3] = wall['health'] / 50
            # 效果类型编码
            effect_map = {'piercing_ammo': 0.2, 'explosive_ammo': 0.4, 'speed_boost': 0.6, 'shield': 0.8, 'multi_shot': 1.0}
            state[base_idx + 4] = effect_map.get(wall['effect'], 0.0)
        
        # 预留空间用于扩展 (49维)
        # state[79:128] 保留用于未来功能
        
        return state
    
    def _check_done(self) -> bool:
        """检查是否结束"""
        return (self.tank_health <= 0 or 
                self.player_health <= 0 or 
                self.current_step >= self.max_episode_steps)

class OfflineTrainer:
    """离线训练器"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.environment = TankBattleTrainingEnvironment(self.config['environment'])
        
        if PYTORCH_AVAILABLE:
            self.agent = TankRLAgent()
        else:
            print("PyTorch不可用，无法进行深度强化学习训练")
            return
        
        # 训练统计
        self.training_stats = {
            'episodes': 0,
            'total_steps': 0,
            'best_reward': float('-inf'),
            'recent_rewards': deque(maxlen=100),
            'win_rate': 0.0,
            'average_episode_length': 0.0
        }
        
        # 模型保存路径
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置"""
        default_config = {
            'environment': {
                'map_width': 1500,
                'map_height': 900,
                'max_episode_steps': 3000
            },
            'training': {
                'total_episodes': 10000,
                'save_frequency': 500,
                'eval_frequency': 100,
                'target_win_rate': 0.8,
                'early_stopping_patience': 2000
            },
            'agent': {
                'learning_rate': 0.001,
                'epsilon_start': 1.0,
                'epsilon_end': 0.01,
                'epsilon_decay': 0.995,
                'batch_size': 64,
                'memory_size': 50000,
                'target_update_frequency': 100
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 深度合并配置
                self._deep_update(default_config, user_config)
        
        return default_config
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def train(self, resume_from: str = None):
        """开始训练"""
        if not PYTORCH_AVAILABLE:
            print("❌ PyTorch不可用，无法训练")
            return
        
        print("🚀 开始离线强化学习训练...")
        print(f"训练目标: {self.config['training']['total_episodes']} episodes")
        print(f"目标胜率: {self.config['training']['target_win_rate']:.1%}")
        if hasattr(self.agent, 'device'):
            print(f"设备: {self.agent.device}")
        
        # 加载之前的模型（如果存在）
        if resume_from:
            self._load_model(resume_from)
        
        start_time = time.time()
        episodes_without_improvement = 0
        
        # 创建进度条
        pbar = tqdm(
            range(self.config['training']['total_episodes']),
            desc="🎯训练中",
            unit="episode",
            ncols=120
        )
        
        try:
            for episode in pbar:
                episode_reward, episode_length, won = self._run_episode()
                
                # 更新统计
                self.training_stats['episodes'] += 1
                self.training_stats['total_steps'] += episode_length
                self.training_stats['recent_rewards'].append(episode_reward)
                
                # 计算胜率
                recent_wins = sum(1 for r in list(self.training_stats['recent_rewards']) if r > 30)
                self.training_stats['win_rate'] = recent_wins / len(self.training_stats['recent_rewards'])
                
                # 更新最佳奖励
                if episode_reward > self.training_stats['best_reward']:
                    self.training_stats['best_reward'] = episode_reward
                    episodes_without_improvement = 0
                    # 保存最佳模型
                    self._save_model(f'best_model_ep{episode}.pth')
                else:
                    episodes_without_improvement += 1
                
                # 更新进度条信息
                avg_reward = np.mean(self.training_stats['recent_rewards'])
                pbar.set_postfix({
                    '奖励': f'{episode_reward:.1f}',
                    '平均': f'{avg_reward:.1f}',
                    '胜率': f'{self.training_stats["win_rate"]:.1%}',
                    'ε': f'{self.agent.epsilon:.3f}',
                    '最佳': f'{self.training_stats["best_reward"]:.1f}'
                })
                
                # 定期输出详细信息
                if (episode + 1) % 200 == 0:
                    elapsed = time.time() - start_time
                    steps_per_sec = self.training_stats['total_steps'] / elapsed
                    pbar.write(f"📊 Episode {episode + 1:5d} | "
                              f"奖励: {episode_reward:7.2f} | "
                              f"平均: {avg_reward:7.2f} | "
                              f"胜率: {self.training_stats['win_rate']:5.1%} | "
                              f"步/秒: {steps_per_sec:.1f}")
                
                # 定期保存
                if (episode + 1) % self.config['training']['save_frequency'] == 0:
                    self._save_model(f'checkpoint_ep{episode + 1}.pth')
                    self._save_training_stats()
                
                # 早停检查
                if (episodes_without_improvement >= self.config['training']['early_stopping_patience'] and
                    self.training_stats['win_rate'] >= self.config['training']['target_win_rate']):
                    pbar.write(f"🎯 达到目标胜率 {self.training_stats['win_rate']:.1%}，训练完成！")
                    break
        
        except KeyboardInterrupt:
            pbar.close()
            print(f"\n⚠️ 训练被用户中断 (Ctrl+C)")
            print(f"📊 已完成 {self.training_stats['episodes']} 个回合")
            print(f"💾 正在保存当前进度...")
            
            # 保存中断时的模型
            self._save_model(f'interrupted_ep{self.training_stats["episodes"]}.pth')
            self._save_training_stats()
            
            # 即使中断也显示报告
            total_time = time.time() - start_time
            self._print_training_report(total_time)
            return
        
        except Exception as e:
            pbar.close()
            print(f"\n❌ 训练过程中发生错误: {e}")
            print(f"💾 正在保存当前进度...")
            
            # 保存错误时的模型
            self._save_model(f'error_ep{self.training_stats["episodes"]}.pth')
            self._save_training_stats()
            raise
        
        pbar.close()
        
        # 保存最终模型
        self._save_model('final_model.pth')
        self._save_training_stats()
        
        total_time = time.time() - start_time
        self._print_training_report(total_time)
    
    def _print_training_report(self, training_time: float):
        """打印详细的训练分析报告"""
        print(f"\n" + "="*60)
        print(f"🎯 坦克大战AI训练完成报告")
        print(f"="*60)
        
        # 基础统计
        print(f"📊 训练统计:")
        print(f"  总训练时间: {training_time:.1f}秒 ({training_time/3600:.2f}小时)")
        print(f"  总回合数: {self.training_stats['episodes']}")
        print(f"  总步数: {self.training_stats['total_steps']:,}")
        print(f"  平均每回合时间: {training_time/max(self.training_stats['episodes'], 1):.2f}秒")
        print(f"  平均每回合步数: {self.training_stats['total_steps']/max(self.training_stats['episodes'], 1):.1f}")
        print(f"  训练效率: {self.training_stats['total_steps']/training_time:.1f} 步/秒")
        
        # 性能指标
        print(f"\n🏆 性能指标:")
        print(f"  最终胜率: {self.training_stats['win_rate']:.1%}")
        print(f"  最佳单局奖励: {self.training_stats['best_reward']:.2f}")
        print(f"  最近100局平均奖励: {np.mean(self.training_stats['recent_rewards']):.2f}")
        print(f"  奖励标准差: {np.std(self.training_stats['recent_rewards']):.2f}")
        
        # AI学习进度
        if hasattr(self.agent, 'epsilon'):
            print(f"\n🧠 AI学习状态:")
            print(f"  最终探索率(ε): {self.agent.epsilon:.4f}")
            print(f"  学习步数: {self.agent.training_step:,}")
            print(f"  经验池大小: {len(self.agent.memory):,}")
            if hasattr(self.agent, 'losses') and self.agent.losses:
                recent_loss = np.mean(self.agent.losses[-100:]) if len(self.agent.losses) >= 100 else np.mean(self.agent.losses)
                print(f"  最近平均损失: {recent_loss:.6f}")
        
        # 硬件使用情况
        if hasattr(self.agent, 'device'):
            print(f"\n⚙️ 硬件信息:")
            print(f"  训练设备: {self.agent.device}")
            if str(self.agent.device) == 'cuda':
                try:
                    import torch
                    print(f"  GPU显存使用: {torch.cuda.max_memory_allocated()/1024**3:.2f}GB")
                    print(f"  GPU利用率: 优化的GPU加速训练")
                except:
                    pass
        
        # 模型评估
        print(f"\n📈 训练质量评估:")
        if self.training_stats['win_rate'] >= 0.8:
            print(f"  ✅ 优秀: 胜率达到{self.training_stats['win_rate']:.1%}，AI性能优异")
        elif self.training_stats['win_rate'] >= 0.6:
            print(f"  ✅ 良好: 胜率{self.training_stats['win_rate']:.1%}，AI具备基本战斗能力")
        elif self.training_stats['win_rate'] >= 0.4:
            print(f"  ⚠️ 一般: 胜率{self.training_stats['win_rate']:.1%}，建议增加训练轮数")
        else:
            print(f"  ❌ 需改进: 胜率仅{self.training_stats['win_rate']:.1%}，建议调整超参数")
        
        # 奖励分析
        recent_rewards = list(self.training_stats['recent_rewards'])
        if recent_rewards:
            reward_quartiles = np.percentile(recent_rewards, [25, 50, 75])
            print(f"  奖励分布 (25%/50%/75%): {reward_quartiles[0]:.1f}/{reward_quartiles[1]:.1f}/{reward_quartiles[2]:.1f}")
            
            # 计算训练稳定性
            if len(recent_rewards) >= 50:
                first_half = recent_rewards[:len(recent_rewards)//2]
                second_half = recent_rewards[len(recent_rewards)//2:]
                improvement = np.mean(second_half) - np.mean(first_half)
                print(f"  训练后期改进: {improvement:+.2f} (最近50局对比)")
        
        # 保存位置
        print(f"\n📁 模型文件:")
        print(f"  保存目录: {self.models_dir}")
        print(f"  最佳模型: best_model_ep*.pth")
        print(f"  最终模型: final_model.pth")
        print(f"  训练统计: training_stats.json")
        
        # 使用建议
        print(f"\n💡 使用建议:")
        if self.training_stats['win_rate'] >= 0.7:
            print(f"  🎮 模型已具备强战斗力，可直接用于游戏")
            print(f"  🔧 可尝试更高难度的训练环境")
        else:
            print(f"  📚 建议继续训练或调整超参数")
            print(f"  🔍 可分析训练日志优化奖励函数")
        
        print(f"  🚀 使用命令测试模型: python train_ai.py --eval --model ai/models/best_model_ep*.pth")
        print(f"="*60)
    
    def _run_episode(self) -> Tuple[float, int, bool]:
        """运行一个训练episode"""
        state = self.environment.reset()
        total_reward = 0
        steps = 0
        won = False
        replay_frequency = 4  # 每4步训练一次，提高效率
        
        while True:
            # 选择动作
            action = self.agent.act(state, training=True)
            
            # 执行动作
            next_state, reward, done, info = self.environment.step(action)
            
            # 存储经验
            self.agent.remember(state, action, reward, next_state, done)
            
            # 训练 - 优化频率控制
            if (len(self.agent.memory) > self.agent.batch_size and 
                steps % replay_frequency == 0):
                self.agent.replay()
            
            state = next_state
            total_reward += reward
            steps += 1
            
            if done:
                won = info.get('player_health', 100) <= 0  # 击败玩家算胜利
                break
        
        return total_reward, steps, won
    
    def _save_model(self, filename: str):
        """保存模型和训练状态"""
        filepath = os.path.join(self.models_dir, filename)
        
        # 创建完整的检查点
        checkpoint = {
            'q_network_state_dict': self.agent.q_network.state_dict(),
            'target_network_state_dict': self.agent.target_network.state_dict(),
            'optimizer_state_dict': self.agent.optimizer.state_dict(),
            'training_stats': {
                'episodes': self.training_stats['episodes'],
                'best_reward': self.training_stats['best_reward'],
                'win_rate': self.training_stats['win_rate'],
                'epsilon': self.agent.epsilon,
                'training_step': self.agent.training_step
            },
            'config': self.config,
            'timestamp': time.time()
        }
        
        try:
            torch.save(checkpoint, filepath)
            # 只在重要保存时输出日志
            if 'best_model' in filename or 'final_model' in filename:
                print(f"💾 模型已保存: {filename}")
        except Exception as e:
            print(f"❌ 保存模型失败: {e}")
    
    def _load_model(self, model_path: str):
        """加载模型和训练状态"""
        if not os.path.exists(model_path):
            print(f"❌ 模型文件不存在: {model_path}")
            return False
        
        try:
            checkpoint = torch.load(model_path, map_location=self.agent.device)
            
            # 加载网络状态
            self.agent.q_network.load_state_dict(checkpoint['q_network_state_dict'])
            self.agent.target_network.load_state_dict(checkpoint['target_network_state_dict'])
            
            # 如果有优化器状态，也加载
            if 'optimizer_state_dict' in checkpoint and hasattr(self.agent, 'optimizer'):
                self.agent.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            
            # 加载训练统计（如果有）
            if 'training_stats' in checkpoint:
                self.training_stats.update(checkpoint['training_stats'])
                self.agent.epsilon = checkpoint['training_stats'].get('epsilon', 0.1)
                self.agent.training_step = checkpoint['training_stats'].get('training_step', 0)
            
            print(f"✅ 模型加载成功: {model_path}")
            return True
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            return False
    
    def _save_training_stats(self):
        """保存详细训练统计"""
        stats_file = os.path.join(self.models_dir, 'training_stats.json')
        
        # 转换不可序列化的对象
        stats_to_save = self.training_stats.copy()
        stats_to_save['recent_rewards'] = list(stats_to_save['recent_rewards'])
        stats_to_save['config'] = self.config
        stats_to_save['timestamp'] = time.time()
        stats_to_save['device_info'] = {
            'device': str(self.agent.device),
            'cuda_available': torch.cuda.is_available(),
            'gpu_name': torch.cuda.get_device_name() if torch.cuda.is_available() else None
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_to_save, f, indent=2, ensure_ascii=False)
        
        print(f"📈 训练统计已保存: {stats_file}")
    
    def evaluate(self, model_path: str, num_episodes: int = 100) -> Dict:
        """全面评估模型性能"""
        print(f"🔍 评估模型: {model_path}")
        
        # 加载模型
        if not self._load_model(model_path):
            return {}
        
        # 评估统计
        eval_stats = {
            'wins': 0,
            'total_episodes': num_episodes,
            'total_reward': 0,
            'episode_rewards': [],
            'episode_lengths': [],
            'damage_dealt': [],
            'survival_times': [],
            'shot_accuracy': []
        }
        
        # 创建评估进度条
        pbar = tqdm(range(num_episodes), desc="🎯评估中", unit="episode")
        
        # 保存原始epsilon
        original_epsilon = self.agent.epsilon
        self.agent.epsilon = 0.0  # 使用贪婪策略
        
        try:
            for episode in pbar:
                episode_reward, episode_length, won = self._run_episode()
                
                # 记录统计
                if won:
                    eval_stats['wins'] += 1
                eval_stats['total_reward'] += episode_reward
                eval_stats['episode_rewards'].append(episode_reward)
                eval_stats['episode_lengths'].append(episode_length)
                
                # 更新进度条
                current_win_rate = eval_stats['wins'] / (episode + 1)
                avg_reward = eval_stats['total_reward'] / (episode + 1)
                pbar.set_postfix({
                    '胜率': f'{current_win_rate:.1%}',
                    '平均奖励': f'{avg_reward:.1f}'
                })
        
        finally:
            # 恢复原始epsilon
            self.agent.epsilon = original_epsilon
            pbar.close()
        
        # 计算最终统计
        eval_stats['win_rate'] = eval_stats['wins'] / num_episodes
        eval_stats['average_reward'] = eval_stats['total_reward'] / num_episodes
        eval_stats['average_episode_length'] = np.mean(eval_stats['episode_lengths'])
        eval_stats['reward_std'] = np.std(eval_stats['episode_rewards'])
        eval_stats['max_reward'] = max(eval_stats['episode_rewards'])
        eval_stats['min_reward'] = min(eval_stats['episode_rewards'])
        
        # 生成评估报告
        self._print_evaluation_report(eval_stats)
        
        # 保存评估结果
        eval_file = os.path.join(self.models_dir, f'evaluation_{int(time.time())}.json')
        with open(eval_file, 'w', encoding='utf-8') as f:
            json.dump(eval_stats, f, indent=2, ensure_ascii=False)
        
        return eval_stats
    
    def _print_evaluation_report(self, eval_stats: Dict):
        """打印详细评估报告"""
        print(f"\n📊 模型评估报告")
        print("=" * 50)
        print(f"🎯 总体表现:")
        print(f"  胜率: {eval_stats['win_rate']:.1%} ({eval_stats['wins']}/{eval_stats['total_episodes']})")
        print(f"  平均奖励: {eval_stats['average_reward']:.2f} ± {eval_stats['reward_std']:.2f}")
        print(f"  平均回合长度: {eval_stats['average_episode_length']:.1f}步")
        
        print(f"\n📈 奖励分析:")
        print(f"  最高奖励: {eval_stats['max_reward']:.2f}")
        print(f"  最低奖励: {eval_stats['min_reward']:.2f}")
        print(f"  标准差: {eval_stats['reward_std']:.2f}")
        
        print(f"\n💡 模型质量评估:")
        if eval_stats['win_rate'] >= 0.8:
            print("  🌟 优秀 - 模型表现卓越，可用于高难度对战")
        elif eval_stats['win_rate'] >= 0.6:
            print("  ✅ 良好 - 模型表现不错，适合一般对战")
        elif eval_stats['win_rate'] >= 0.4:
            print("  ⚠️ 中等 - 模型需要进一步训练")
        else:
            print("  ❌ 较差 - 建议重新训练或调整参数")
        
        print(f"\n🎮 使用建议:")
        if eval_stats['win_rate'] > 0.9:
            print("  - 可能过度训练，考虑增加游戏难度")
        elif eval_stats['win_rate'] < 0.3:
            print("  - 训练不足，建议增加训练episode数量")
            print("  - 检查奖励函数设计是否合理")
        else:
            print("  - 表现平衡，可直接使用")
        
        print("=" * 50)

def main():
    """主函数"""
    print("🤖 坦克大战离线AI训练系统")
    print("=" * 50)
    
    # 检查PyTorch
    if not PYTORCH_AVAILABLE:
        print("❌ 需要安装PyTorch才能进行训练")
        print("安装命令: pip install torch torchvision")
        return
    
    # 创建训练器
    trainer = OfflineTrainer()
    
    # 开始训练
    try:
        trainer.train()
    except KeyboardInterrupt:
        print("\n⚠️ 训练被用户中断")
    except Exception as e:
        print(f"❌ 训练出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
