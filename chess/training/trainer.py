"""
国际象棋AI训练器 - 最终版本
集成现代化算法，支持AlphaZero架构、MCTS、残差网络等
"""
import signal
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import sys
import os
import json
import time
import warnings
import traceback
import math
import threading
import queue
import psutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from tqdm import tqdm
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入本地算法模块
from training.algorithms import (
    ModernChessNetwork, 
    AdvancedMCTS, 
    ChessBoardEncoder,
    AdvancedTrainingStrategy,
    AdaptiveLearningRate,
    ExperienceReplayBuffer
)

# 导入游戏相关模块
from ai.ml_ai import ChessMLAI, ChessNeuralNetwork, PositionEncoder
from ai.basic_ai import BasicAI
from game.board import ChessBoard
from game.pieces import PieceColor, PieceType
from data.database import ChessDatabase

class ModernChessTrainer:
    """现代化象棋AI训练器"""
    
    def __init__(self, 
                 model_path: str = None,
                 training_data_dir: str = None,  # 改为None，使用绝对路径
                 database_path: str = None,  # 默认None，将使用统一数据库路径
                 use_modern_architecture: bool = True,
                 load_best_model: bool = True):
        # 设备和性能配置
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.num_workers = min(8, os.cpu_count())
        self.use_modern_architecture = use_modern_architecture
        self.load_best_model = load_best_model

        print("🚀 现代化象棋AI训练器初始化")
        print(f"   设备: {self.device}")
        print(f"   现代架构: {'启用' if use_modern_architecture else '禁用'}")
        print(f"   CPU核心: {os.cpu_count()}")
        print(f"   工作进程: {self.num_workers}")
        print(f"   加载最佳模型: {'是' if load_best_model else '否'}")

        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name()}")
            print(f"   GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

        # 🆕 目录设置 - 使用绝对路径避免多层training目录
        if training_data_dir is None:
            # 获取当前trainer.py所在的目录，即gamecenter/chess/training
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            self.training_data_dir = current_script_dir
        else:
            self.training_data_dir = os.path.abspath(training_data_dir)
        
        # 模型目录：gamecenter/chess/training/models
        self.models_dir = os.path.join(self.training_data_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        print(f"📂 训练数据目录: {self.training_data_dir}")
        print(f"📂 模型存储目录: {self.models_dir}")

        # 模型版本管理
        self.model_tracker = {
            'best_model_path': None,
            'best_win_rate': 0.0,
            'best_model_games': 0,
            'current_model_performance': 0.0,
            'training_history': []
        }

        # 数据库路径处理 - 使用统一数据库路径（提前初始化）
        if database_path is None:
            # 使用config/settings.py中定义的统一数据库路径
            from config.settings import DATABASE_PATH
            database_path = DATABASE_PATH
        
        self.database = ChessDatabase(database_path)

        # 查找并加载最佳模型（现在可以使用数据库）
        if load_best_model:
            best_model_info = self._find_best_model()
            if best_model_info:
                model_path = best_model_info['path']
                # 统一显示历史游戏信息
                print(f"📊 已发现模型: ml_ai_model.pth，历史AI游戏: {best_model_info['games']} 局")
                self.model_tracker.update({
                    'best_model_path': best_model_info['path'],
                    'best_win_rate': best_model_info['win_rate'],
                    'best_model_games': best_model_info['games']
                })

        # 并发安全锁（需在模型初始化前创建，供包装器使用）
        self.model_lock = threading.Lock()
        
        # 优雅退出标志
        self._stop_training = threading.Event()
        self._setup_signal_handlers()

        # 初始化AI模型
        self._initialize_models(model_path)

        # 训练配置 - 🆕 优化并行性能
        self.config = {
            'batch_size': 64,  # 提升批处理大小
            'min_training_samples': 4,  # 降低最小训练样本数
            'max_moves_per_game': 80,  # 🆕 降低最大步数
            'save_frequency': 25,
            'evaluation_frequency': 20,
            'learning_rate': 0.003,  # 🆕 提升学习率
            'weight_decay': 1e-4,
            'gradient_clip_norm': 1.0,
            'temperature': 0.8,
            'c_puct': 1.0,
            'num_simulations': 200,  # 🆕 降低MCTS模拟次数
            'train_every_n_games': 1,  # 🆕 每局都训练
            # MCTS使用率配置
            'mcts_usage_rate_serial': 0.3,  # 串行训练中30%使用MCTS
            'mcts_usage_rate_parallel': 0.2,  # 并行训练中20%使用MCTS
            # 并行消费者优化参数
            'consumer_queue_maxsize': 1024,  # 🆕 降低队列大小
            'consumer_batch_target': 128,  # 🆕 降低目标批次
            'consumer_min_batch': 32,  # 🆕 降低最小批次
            'consumer_flush_timeout_ms': 20,  # 🆕 降低超时时间
        }

        # 经验回放缓冲区
        self.experience_buffer = ExperienceReplayBuffer(capacity=100000)

        # 高级训练组件
        if self.use_modern_architecture:
            self.training_strategy = AdvancedTrainingStrategy(self.neural_network, self.device)
            self.adaptive_lr = AdaptiveLearningRate(initial_lr=self.config['learning_rate'])
            self.mcts = AdvancedMCTS(
                neural_network=self.neural_network,
                c_puct=self.config['c_puct'],
                num_simulations=self.config['num_simulations'],
                device=self.device
            )

        # 性能统计
        self.performance_stats = {
            'games_per_second': 0.0,
            'training_loss': 0.0,
            'gpu_utilization': 0.0,
            'total_parameters': 0,
            'model_size_mb': 0.0,
            'batch_processing_time': 0.0
        }

        # 训练统计
        self.training_stats = {
            'games_played': 0,
            'white_wins': 0,
            'black_wins': 0,
            'draws': 0,
            'total_moves': 0,
            'ml_ai_wins': 0,
            'ml_ai_losses': 0,
            'ml_ai_draws': 0,
            'average_game_length': 0.0,
            'win_rate_progression': [],
            'loss_progression': [],
            'epsilon_progression': [],
            'training_epochs': 0,
            'total_training_time': 0.0,
            'start_time': datetime.now().isoformat(),
            'model_updates': 0,
            'historical_games_loaded': 0,
            'total_training_samples': 0,
            'convergence_metrics': {
                'loss_variance': 0.0,
                'win_rate_stability': 0.0,
                'learning_curve_slope': 0.0
            }
        }

        # 设置优化器
        self._setup_optimizer()

        # 计算模型统计
        self._calculate_model_stats()

        # 加载历史训练数据
        self._load_historical_training_data()

    def _setup_signal_handlers(self):
        """设置信号处理器以支持优雅退出"""
        def signal_handler(signum, frame):
            print(f"\n🛑 收到中断信号 ({signum})，正在优雅退出...")
            self._stop_training.set()
            
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)  # 终止信号

    def _find_best_model(self):
        """查找最佳模型信息 - 简化版本，优先使用ml_ai_model.pth作为标准模型"""
        try:
            # 🆕 简化逻辑：ml_ai_model.pth就是当前最佳模型
            default_model = os.path.join(self.models_dir, "ml_ai_model.pth")
            
            if os.path.exists(default_model):
                # 🆕 从数据库统计历史AI训练局数
                historical_ai_games = self._count_historical_ai_games()
                return {
                    'path': default_model,
                    'filename': "ml_ai_model.pth",
                    'win_rate': 0.0,  # 后续从统计中计算
                    'games': historical_ai_games,
                    'stats_file': None,
                    'model_updates': 0
                }
            
            print("❌ 没有找到标准模型文件 ml_ai_model.pth")
            return None
            
        except Exception as e:
            print(f"❌ 查找模型失败: {e}")
            return None
    
    def _count_historical_ai_games(self) -> int:
        """统计数据库中的历史AI游戏局数"""
        try:
            # 使用数据库连接统计AI参与的游戏
            import sqlite3
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM games 
                    WHERE white_type = 'ai' OR black_type = 'ai'
                ''')
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            print(f"⚠️ 统计历史AI游戏失败: {e}")
            return 0
    
    def _initialize_models(self, model_path: str):
        """初始化AI模型"""
        try:
            if self.use_modern_architecture:
                # 使用现代架构
                print("🧠 加载现代化神经网络架构...")
                self.neural_network = ModernChessNetwork().to(self.device)
                self.board_encoder = ChessBoardEncoder()
                
                # 如果有预训练模型，尝试加载
                if model_path and os.path.exists(model_path):
                    try:
                        checkpoint = torch.load(model_path, map_location=self.device)
                        state_dict = None
                        if isinstance(checkpoint, dict):
                            if 'state_dict' in checkpoint and isinstance(checkpoint['state_dict'], dict):
                                state_dict = checkpoint['state_dict']
                            elif 'model_state_dict' in checkpoint and isinstance(checkpoint['model_state_dict'], dict):
                                state_dict = checkpoint['model_state_dict']
                            elif 'model' in checkpoint and isinstance(checkpoint['model'], dict):
                                state_dict = checkpoint['model']
                            else:
                                # 可能直接是权重字典
                                # 简单启发式：键里含有层名
                                example_keys = list(checkpoint.keys())
                                if example_keys and isinstance(example_keys[0], str):
                                    state_dict = checkpoint
                        
                        if state_dict is not None:
                            missing, unexpected = self.neural_network.load_state_dict(state_dict, strict=False)
                            if missing:
                                print(f"⚠️ 预训练模型缺失参数: {len(missing)} 项")
                            if unexpected:
                                print(f"⚠️ 预训练模型多余参数: {len(unexpected)} 项")
                            print(f"✅ 已加载预训练模型: {model_path}")
                        else:
                            raise ValueError("不包含可用的 state_dict")
                    except Exception as e:
                        print(f"⚠️ 预训练模型加载失败，使用随机初始化: {e}")
                
                # 创建兼容的ML AI包装器
                self.ml_ai = self._create_modern_ml_ai_wrapper()
                
            else:
                # 使用传统架构
                print("🔄 加载传统ML AI架构...")
                self.ml_ai = ChessMLAI(model_path)
                self.neural_network = self.ml_ai.model
                self.board_encoder = self.ml_ai.encoder
            
            # 基础AI作为对手
            self.basic_ai = BasicAI(depth=3)
            
        except Exception as e:
            print(f"❌ 模型初始化失败: {e}")
            print("🔄 回退到传统架构...")
            self.use_modern_architecture = False
            self.ml_ai = ChessMLAI()
            self.neural_network = self.ml_ai.model
            self.board_encoder = self.ml_ai.encoder
            self.basic_ai = BasicAI(depth=3)
    
    def _create_modern_ml_ai_wrapper(self):
        """创建现代ML AI包装器以保持兼容性"""
        model_lock = self.model_lock
        class ModernMLAIWrapper:
            def __init__(self, neural_network, board_encoder, device, model_lock):
                self.model = neural_network
                self.encoder = board_encoder
                self.device = device
                self.model_lock = model_lock
                self.epsilon = 0.3  # 初始探索率
                self.move_history = []  # 移动历史
            
            def get_best_move(self, board, color):
                """获取最佳移动 - 智能决策算法"""
                return self.get_move(board)
            
            def get_move(self, board):
                """获取AI移动 - 优化的决策策略，增加激进性"""
                legal_moves = self._get_legal_moves(board)
                if not legal_moves:
                    return None
                
                # 如果只有一个合法移动，直接返回
                if len(legal_moves) == 1:
                    return legal_moves[0]
                
                try:
                    # 使用神经网络评估所有合法移动
                    move_scores = self._evaluate_moves(board, legal_moves)
                    
                    # 动态调整探索率 - 更激进的策略
                    dynamic_epsilon = self.epsilon + 0.2  # 增加基础探索
                    
                    # 更复杂的决策策略
                    if random.random() < dynamic_epsilon:
                        # 探索模式：使用多样化选择
                        if random.random() < 0.3:
                            # 30%概率完全随机
                            return random.choice(legal_moves)
                        else:
                            # 70%概率从前60%的移动中选择
                            sorted_moves = sorted(move_scores.items(), key=lambda x: x[1], reverse=True)
                            top_moves = sorted_moves[:max(2, int(len(sorted_moves) * 0.6))]
                            
                            # 使用加权随机选择
                            weights = [score for _, score in top_moves]
                            # 添加温度参数使选择更多样化
                            temp_weights = [math.exp(w / 0.5) for w in weights]
                            total_weight = sum(temp_weights)
                            rand_val = random.random() * total_weight
                            
                            cumulative = 0
                            for i, weight in enumerate(temp_weights):
                                cumulative += weight
                                if rand_val <= cumulative:
                                    return top_moves[i][0]
                            return top_moves[0][0]
                    else:
                        # 利用模式：选择最佳移动，但添加小幅随机化
                        sorted_moves = sorted(move_scores.items(), key=lambda x: x[1], reverse=True)
                        
                        # 10%概率选择次优移动来避免过度确定性
                        if len(sorted_moves) > 1 and random.random() < 0.1:
                            return sorted_moves[1][0]
                        else:
                            return sorted_moves[0][0]
                
                except Exception as e:
                    print(f"⚠️ AI决策失败，使用启发式: {e}")
                    # 回退到启发式移动选择
                    return self._get_heuristic_move(board, legal_moves)
            
            # 旧版 _evaluate_moves 已移除，保留加锁的修复版本
            
            def _evaluate_position_value(self, board, move):
                """评估移动的位置价值 - 增强激进性"""
                from_pos, to_pos = move
                score = 0.0
                
                try:
                    # 检查是否吃子 - 增加激励
                    if to_pos in board.pieces:
                        target_piece = board.pieces[to_pos]
                        # 吃子大幅加分
                        piece_values = {
                            'PAWN': 1, 'KNIGHT': 3, 'BISHOP': 3,
                            'ROOK': 5, 'QUEEN': 9, 'KING': 100
                        }
                        piece_name = target_piece.piece_type.name
                        score += piece_values.get(piece_name, 1) * 3.0  # 增加吃子奖励
                    
                    # 检查是否将军 - 大幅奖励攻击性移动
                    if hasattr(board, '_would_cause_check'):
                        if board._would_cause_check(move):
                            score += 2.5  # 增加将军奖励
                    
                    # 中心控制奖励 - 增强
                    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
                    extended_center = [(2, 2), (2, 3), (2, 4), (2, 5), 
                                     (3, 2), (3, 5), (4, 2), (4, 5),
                                     (5, 2), (5, 3), (5, 4), (5, 5)]
                    
                    if to_pos in center_squares:
                        score += 1.0  # 增加中心奖励
                    elif to_pos in extended_center:
                        score += 0.5
                    
                    # 攻击性移动奖励
                    row_diff = abs(to_pos[0] - from_pos[0])
                    col_diff = abs(to_pos[1] - from_pos[1])
                    move_distance = row_diff + col_diff
                    
                    # 奖励大幅移动（更激进）
                    if move_distance >= 3:
                        score += 0.8
                    elif move_distance >= 2:
                        score += 0.4
                    
                    # 前进奖励（特别是兵类）
                    if from_pos in board.pieces:
                        piece = board.pieces[from_pos]
                        if piece.piece_type.name == 'PAWN':
                            if piece.color.name == 'WHITE' and to_pos[0] < from_pos[0]:
                                # 白兵前进奖励
                                advance_reward = (from_pos[0] - to_pos[0]) * 0.6
                                score += advance_reward
                            elif piece.color.name == 'BLACK' and to_pos[0] > from_pos[0]:
                                # 黑兵前进奖励
                                advance_reward = (to_pos[0] - from_pos[0]) * 0.6
                                score += advance_reward
                    
                    # 避免过度保守的角落移动
                    corner_squares = [(0, 0), (0, 7), (7, 0), (7, 7)]
                    if to_pos in corner_squares:
                        score -= 1.0  # 惩罚角落移动
                    
                    # 边缘惩罚减少
                    if to_pos[0] in [0, 7] or to_pos[1] in [0, 7]:
                        score -= 0.1  # 减少边缘惩罚
                    
                    # 添加随机因子增加多样性
                    score += random.uniform(-0.3, 0.3)
                    
                except Exception as e:
                    print(f"⚠️ 位置评估失败: {e}")
                    score = random.uniform(-0.5, 0.5)
                
                return score
            
            def _get_heuristic_move(self, board, legal_moves):
                """启发式选择移动（用于回退）"""
                scored_moves = []
                for move in legal_moves:
                    from_pos, to_pos = move
                    score = 0.0
                    try:
                        # 吃子奖励
                        if to_pos in board.pieces:
                            target_piece = board.pieces[to_pos]
                            piece_values = {
                                'PAWN': 1, 'KNIGHT': 3, 'BISHOP': 3,
                                'ROOK': 5, 'QUEEN': 9, 'KING': 100
                            }
                            score += piece_values.get(target_piece.piece_type.name, 1) * 3.0
                        
                        # 中心控制
                        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
                        if to_pos in center_squares:
                            score += 1.0
                        
                        # 兵前进奖励 / 其他子力走远奖励
                        if from_pos in board.pieces:
                            piece = board.pieces[from_pos]
                            if piece.piece_type.name == 'PAWN':
                                if piece.color.name == 'WHITE' and to_pos[0] < from_pos[0]:
                                    score += (from_pos[0] - to_pos[0]) * 0.6
                                elif piece.color.name == 'BLACK' and to_pos[0] > from_pos[0]:
                                    score += (to_pos[0] - from_pos[0]) * 0.6
                            else:
                                move_distance = abs(to_pos[0] - from_pos[0]) + abs(to_pos[1] - from_pos[1])
                                score += move_distance * 0.3
                        
                        # 角落轻微惩罚
                        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
                        if to_pos in corners:
                            score -= 0.5
                        
                        # 少量噪声
                        score += random.uniform(-0.2, 0.2)
                    except Exception:
                        pass
                    scored_moves.append((move, score))
                
                if not scored_moves:
                    return random.choice(legal_moves)
                
                scored_moves.sort(key=lambda x: x[1], reverse=True)
                top_count = max(1, len(scored_moves) // 3)
                top_moves = scored_moves[:top_count]
                return random.choice(top_moves)[0]
            
            def _get_legal_moves(self, board):
                """获取所有合法移动"""
                legal_moves = []
                current_player = board.current_player
                
                for position, piece in board.pieces.items():
                    if piece.color == current_player:
                        moves = board.get_legal_moves(position)
                        for to_pos in moves:
                            legal_moves.append((position, to_pos))
                
                return legal_moves
            
            def _encode_board(self, board):
                """编码棋盘状态 - 修复版本"""
                try:
                    encoding = self.encoder.encode(board)
                    tensor = torch.FloatTensor(encoding).unsqueeze(0).to(self.device)
                    
                    # 确保张量维度正确
                    if len(tensor.shape) == 2 and tensor.shape[1] == 1280:  # 20*8*8
                        # 重塑为 (batch, channels, height, width) 格式
                        tensor = tensor.view(1, 20, 8, 8)
                    
                    return tensor
                    
                except Exception as e:
                    print(f"⚠️ 棋盘编码失败: {e}")
                    # 创建兼容的输入张量
                    return torch.randn(1, 20, 8, 8).to(self.device)
            
            def _evaluate_moves(self, board, legal_moves):
                """使用神经网络评估所有移动 - 修复版本"""
                move_scores = {}
                
                try:
                    with self.model_lock:
                        # 保存并设置推理模式
                        prev_mode = self.model.training
                        self.model.eval()
                        
                        with torch.no_grad():
                            board_tensor = self._encode_board(board)
                            
                            # 获取神经网络输出
                            outputs = self.model(board_tensor)
                            if isinstance(outputs, tuple) and len(outputs) >= 2:
                                policy, value = outputs[0], outputs[1]
                            else:
                                policy = outputs if not isinstance(outputs, tuple) else outputs[0]
                                value = torch.zeros(1).to(self.device)
                            
                            # 为每个移动计算分数
                            for i, move in enumerate(legal_moves):
                                try:
                                    # 神经网络分数
                                    if len(policy.shape) > 1 and i < policy.shape[1]:
                                        neural_score = float(policy[0][i])
                                    elif len(policy.shape) == 1 and i < len(policy):
                                        neural_score = float(policy[i])
                                    else:
                                        neural_score = random.uniform(-1, 1)
                                    
                                    # 位置价值评估
                                    position_score = self._evaluate_position_value(board, move)
                                    
                                    # 组合分数
                                    total_score = neural_score * 0.6 + position_score * 0.4
                                    move_scores[move] = total_score
                                    
                                except Exception:
                                    # 如果单个移动评估失败，使用位置分数
                                    move_scores[move] = self._evaluate_position_value(board, move)
                        
                        # 恢复原始模式
                        self.model.train(prev_mode)
                    
                except Exception as e:
                    print(f"⚠️ 神经网络评估失败: {e}")
                    # 完全回退到启发式评估
                    for move in legal_moves:
                        move_scores[move] = self._evaluate_position_value(board, move)
                
                return move_scores
            
            def save_model(self, path):
                """保存模型"""
                torch.save(self.model.state_dict(), path)
                
            def update_epsilon(self, new_epsilon):
                """更新探索率"""
                self.epsilon = max(0.05, min(0.95, new_epsilon))
        return ModernMLAIWrapper(self.neural_network, self.board_encoder, self.device, model_lock)
    
    def _setup_optimizer(self):
        """设置优化器和调度器"""
        if hasattr(self, 'neural_network'):
            # AdamW优化器
            self.optimizer = optim.AdamW(
                self.neural_network.parameters(),
                lr=self.config['learning_rate'],
                weight_decay=self.config['weight_decay'],
                betas=(0.9, 0.999),
                eps=1e-8
            )
            
            # 余弦退火调度器
            self.scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
                self.optimizer,
                T_0=50,
                T_mult=2,
                eta_min=1e-6
            )
            
            # 混合精度训练
            self.scaler = torch.cuda.amp.GradScaler() if self.device.type == 'cuda' else None
    
    def _calculate_model_stats(self):
        """计算模型统计信息"""
        if hasattr(self, 'neural_network'):
            self.performance_stats['total_parameters'] = sum(
                p.numel() for p in self.neural_network.parameters()
            )
            
            # 估算模型大小
            param_size = sum(p.numel() * p.element_size() for p in self.neural_network.parameters())
            buffer_size = sum(b.numel() * b.element_size() for b in self.neural_network.buffers())
            self.performance_stats['model_size_mb'] = (param_size + buffer_size) / 1024 / 1024

    def _load_historical_training_data(self):
        """从数据库加载历史训练数据"""
        print("📚 加载历史训练数据...")
        try:
            # 获取所有历史游戏
            historical_games = self.database.get_games(limit=10000)  # 获取最多10000局游戏
            historical_samples = []
            
            for game in historical_games:
                try:
                    # 获取游戏的所有移动
                    moves = self.database.get_game_moves(game['id'])
                    
                    # 确定ML AI的颜色和结果
                    ml_ai_result = self._determine_ml_ai_result_from_db(game)
                    if ml_ai_result is None:
                        continue  # 跳过没有AI参与的游戏
                    
                    # 转换为训练样本
                    game_samples = self._convert_db_game_to_training_samples(game, moves, ml_ai_result)
                    historical_samples.extend(game_samples)
                    
                except Exception as e:
                    print(f"⚠️ 处理历史游戏失败 (ID: {game['id']}): {e}")
                    continue
            
            # 添加到经验缓冲区
            for sample in historical_samples:
                self.experience_buffer.add(sample)
            
            # 更新统计
            self.training_stats['historical_games_loaded'] = len(historical_games)
            self.training_stats['total_training_samples'] = len(historical_samples)
            
            print(f"✅ 已加载 {len(historical_games)} 局历史游戏，生成 {len(historical_samples)} 个训练样本")
            
        except Exception as e:
            import traceback
            print(f"⚠️ 加载历史训练数据失败: {e}")
            print("详细错误信息:")
            traceback.print_exc()
    
    def _determine_ml_ai_result_from_db(self, game: Dict) -> Optional[str]:
        """从数据库游戏记录中确定ML AI的结果"""
        # 检查是否有AI参与
        has_ai = (game.get('white_type') == 'ai' or game.get('black_type') == 'ai')
        if not has_ai:
            return None
        
        # 确定AI颜色
        if game.get('white_type') == 'ai':
            ai_color = 'white'
        else:
            ai_color = 'black'
        
        # 根据游戏结果确定AI结果
        game_result = game.get('result', 'draw')
        if game_result == f"{ai_color}_wins":
            return 'win'
        elif game_result == 'draw':
            return 'draw'
        else:
            return 'loss'
    
    def _convert_db_game_to_training_samples(self, game: Dict, moves: List[Dict], ml_ai_result: str) -> List[Dict]:
        """将数据库中的游戏转换为训练样本"""
        training_samples = []
        
        # 计算结果值
        result_value = self._get_result_value_from_string(ml_ai_result)
        
        # 只处理有 position_after 的移动
        valid_moves = [move for move in moves if move.get('position_after')]
        
        if not valid_moves:
            return training_samples
        
        total_moves = len(valid_moves)
        
        for i, move in enumerate(valid_moves):
            try:
                # 使用 position_after 作为棋盘状态
                board_state = move['position_after']
                
                # 计算训练目标值（考虑时间衰减）
                target_value = self._calculate_training_target(
                    result_value, i, total_moves
                )
                
                # 编码特征 - 使用专门的数据库格式解析器
                features = self._db_position_to_features(board_state)
                if features is not None:
                    training_sample = {
                        'features': features,
                        'target': target_value,
                        'game_id': game['id'],
                        'move_number': move.get('move_number', i + 1),
                        'source': 'database'
                    }
                    training_samples.append(training_sample)
                    
            except Exception as e:
                print(f"⚠️ 转换移动失败 (游戏 {game['id']}, 移动 {i}): {e}")
                continue
        
        return training_samples
    
    def _get_result_value_from_string(self, result: str) -> float:
        """从字符串结果获取数值"""
        if result == 'win':
            return 1.0
        elif result == 'draw':
            return 0.0
        elif result == 'loss':
            return -1.0
        else:
            return 0.0
    
    def _db_position_to_features(self, position_str: str):
        """将数据库的位置字符串转换为特征向量
        数据库格式: '00WR;01WP;06BP;07BR;10WK;...' 
        其中每个部分是：行列+颜色+棋子类型
        """
        try:
            if not position_str or position_str == 'error':
                return None
            
            # 解析数据库格式: "位置+颜色+棋子类型;"
            pieces_data = position_str.split(';')
            
            # 创建特征张量
            if self.use_modern_architecture:
                # 20通道：12个棋子通道 + 8个预留/状态通道
                features = np.zeros((20, 8, 8), dtype=np.float32)
                
                piece_mapping = {
                    'WK': 0, 'WQ': 1, 'WR': 2, 'WB': 3, 'WN': 4, 'WP': 5,
                    'BK': 6, 'BQ': 7, 'BR': 8, 'BB': 9, 'BN': 10, 'BP': 11
                }
                
                for piece_str in pieces_data:
                    if len(piece_str) >= 4:
                        try:
                            # 数据库格式：RRCCPT（行行列列棋子类型）
                            row = int(piece_str[0])
                            col = int(piece_str[1])
                            color = piece_str[2]  # W或B
                            piece_type = piece_str[3]  # K,Q,R,B,N,P
                            
                            piece_key = f"{color}{piece_type}"
                            if piece_key in piece_mapping and 0 <= row < 8 and 0 <= col < 8:
                                channel = piece_mapping[piece_key]
                                features[channel, row, col] = 1.0
                        except (ValueError, IndexError):
                            continue
                
                return features
            else:
                # 传统架构使用平坦特征（简化实现）
                features = np.zeros(773, dtype=np.float32)
                return features
            
        except Exception as e:
            print(f"⚠️ 解析数据库位置失败: {e}")
            return None
    
    def run_training(self, 
                    num_games: int = 100, 
                    opponent_type: str = 'basic',
                    training_mode: str = 'standard',
                    use_parallel: bool = True):
        """运行训练"""
        print(f"\n🎯 开始训练 - {num_games} 局游戏")
        print(f"   对手类型: {opponent_type}")
        print(f"   训练模式: {training_mode}")
        print(f"   架构: {'现代' if self.use_modern_architecture else '传统'}")
        print(f"   并行模式: {'启用' if use_parallel else '禁用'}")
        print(f"   模型参数: {self.performance_stats['total_parameters']:,}")
        print(f"   模型大小: {self.performance_stats['model_size_mb']:.1f} MB")
        
        # GPU预热
        if self.device.type == 'cuda':
            self._warmup_gpu()
        
        # 历史样本预热训练
        self._warmup_with_historical_data()
        
        start_time = time.time()
        
        if use_parallel and num_games >= 3:  # 🆕 降低并行阈值到3局
            # 启用真正的并行训练流水线（生产者-消费者）
            self._run_parallel_training(num_games, opponent_type, training_mode)
        else:
            # 使用串行训练
            self._run_serial_training(num_games, opponent_type, training_mode)
        
        # 训练完成统计
        total_time = time.time() - start_time
        self.training_stats['total_training_time'] = total_time
        self.performance_stats['games_per_second'] = num_games / total_time
        
        # 保存和统计
        self._save_final_model()
        self._save_training_stats()
        self._print_comprehensive_stats()
    
    def _run_parallel_training(self, num_games: int, opponent_type: str, training_mode: str):
        """并行训练"""
        print("🚀 启动并行训练模式")

        # 🆕 优化并行参数 - 确保小规模游戏也能获得合理的并行度
        if num_games >= 100:
            num_workers = min(8, os.cpu_count())
            batch_size = min(32, max(4, num_games // 4))
        elif num_games >= 50:
            num_workers = min(6, os.cpu_count())
            batch_size = min(16, max(4, num_games // 4))
        elif num_games >= 10:
            num_workers = min(4, os.cpu_count())
            batch_size = min(8, max(2, num_games // 3))
        else:
            # 小规模游戏（3-9局）也保证至少2个并发
            num_workers = min(3, os.cpu_count(), num_games)
            batch_size = max(1, num_games // 2)

        print(f"   游戏总数: {num_games}")
        print(f"   并行工作数: {num_workers}")
        print(f"   批处理大小: {batch_size}")
        print(f"   预计并行效率: {num_workers}x 理论加速")

        # 游戏结果队列（容量可配置，避免阻塞生产者）
        queue_maxsize = int(self.config.get('consumer_queue_maxsize', 2048))
        if queue_maxsize <= 0:
            queue_maxsize = 0  # 0 表示无限
        game_queue = queue.Queue(maxsize=queue_maxsize)

        # 启动训练消费者线程
        training_thread = threading.Thread(
            target=self._training_consumer,
            args=(game_queue, num_games)
        )
        training_thread.start()

        # 并行执行游戏
        completed_games = 0

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            with tqdm(total=num_games, desc="并行训练进度", unit="局") as pbar:
                # 提交游戏任务
                future_to_game = {
                    executor.submit(self._play_parallel_game, opponent_type, i): i
                    for i in range(num_games)
                }

                for future in as_completed(future_to_game):
                    # 检查停止标志
                    if self._stop_training.is_set():
                        print("🛑 检测到退出信号，正在停止并行训练...")
                        executor.shutdown(wait=False)
                        break
                    
                    game_id = future_to_game[future]
                    try:
                        game_result = future.result()
                        game_queue.put(game_result)
                        completed_games += 1

                        # 🆕 保存游戏到数据库 - 修复并行训练缺失的数据库保存
                        if game_result.get('result') != 'error':
                            try:
                                self._save_game_to_database(game_result)
                            except Exception as db_error:
                                print(f"⚠️ 保存游戏到数据库失败: {db_error}")

                        # 更新统计
                        self._update_stats(game_result)

                        # 更新进度条 - 🆕 增强显示信息
                        pbar.update(1)

                        # 🆕 定期更新进度条显示信息
                        if completed_games % 5 == 0 or completed_games <= 10:  # 前10局和每5局更新
                            win_rate = self._get_current_win_rate()
                            current_loss = self.training_stats['loss_progression'][-1] if self.training_stats['loss_progression'] else 0.0
                            pbar.set_postfix({
                                'WinRate': f"{win_rate:.1f}%",
                                'ε': f"{getattr(self.ml_ai, 'epsilon', 0):.3f}",
                                'Loss': f"{current_loss:.4f}",
                                'Updates': self.training_stats['model_updates'],
                                'Buffer': len(self.experience_buffer),
                                'Samples': self.training_stats.get('total_training_samples', 0),
                                'GPU': f"{self._get_gpu_usage():.1f}%"
                            })

                        # 定期保存
                        if completed_games % 50 == 0:
                            win_rate = self._get_current_win_rate()
                            self._evaluate_and_save(completed_games)

                    except Exception as e:
                        if not self._stop_training.is_set():  # 只在非停止状态下记录错误
                            print(f"⚠️ 游戏 {game_id} 执行失败: {e}")
                        completed_games += 1
                        pbar.update(1)

        # 停止训练消费者
        game_queue.put(None)  # 停止信号
        training_thread.join()

        print("🎉 并行训练完成!")
    
    def _run_serial_training(self, num_games: int, opponent_type: str, training_mode: str):
        """串行训练（原有方法）"""
        # 训练循环
        with tqdm(total=num_games, desc="训练进度", unit="局") as pbar:
            batch_games = []
            
            for game_num in range(num_games):
                try:
                    # 单局游戏
                    game_result = self._play_single_game(opponent_type)
                    batch_games.append(game_result)
                    
                    # 更新统计
                    self._update_stats(game_result)
                    
                    # 详细日志记录
                    if (game_num + 1) % 5 == 0:  # 每5局记录一次详细信息
                        self._log_training_progress(game_num + 1, game_result)
                    
                    # 批处理训练 - 降低阈值增加训练频率
                    if len(batch_games) >= self.config['train_every_n_games']:
                        print(f"🧠 进行批量训练 ({len(batch_games)} 局游戏)")
                        try:
                            self._process_game_batch(batch_games)
                        except Exception as train_error:
                            print(f"⚠️ 批量训练失败: {train_error}")
                            # 继续训练，不中断
                        batch_games = []
                    
                    # 定期评估和保存 - 降低频率阈值
                    if (game_num + 1) % self.config['evaluation_frequency'] == 0:
                        print(f"📊 定期评估和保存 (第 {game_num + 1} 局)")
                        try:
                            self._evaluate_and_save(game_num + 1)
                        except Exception as eval_error:
                            print(f"⚠️ 评估保存失败: {eval_error}")
                            # 继续训练，不中断
                    
                    # 🆕 增强进度条显示
                    current_loss = self.training_stats['loss_progression'][-1] if self.training_stats['loss_progression'] else self.performance_stats.get('training_loss', 0.0)
                    pbar.set_postfix({
                        'WinRate': f"{self._get_current_win_rate():.1f}%",
                        'ε': f"{getattr(self.ml_ai, 'epsilon', 0):.3f}",
                        'Loss': f"{current_loss:.4f}",
                        'Updates': self.training_stats['model_updates'],
                        'Buffer': len(self.experience_buffer),
                        'Samples': self.training_stats.get('total_training_samples', 0) + len(self.experience_buffer),
                        'GPU': f"{self._get_gpu_usage():.1f}%"
                    })
                    pbar.update(1)
                    
                except Exception as game_error:
                    print(f"⚠️ 第 {game_num + 1} 局游戏出错: {game_error}")
                    # 创建错误游戏结果避免中断训练
                    error_result = {
                        'result': 'error',
                        'ml_ai_result': 'error',
                        'move_count': 0,
                        'moves': [],
                        'error': str(game_error)
                    }
                    batch_games.append(error_result)
                    pbar.update(1)
                    continue
            
            # 处理剩余游戏
            if batch_games:
                self._process_game_batch(batch_games)
    
    def _warmup_gpu(self):
        """GPU预热"""
        print("🔥 GPU预热中...")
        if self.use_modern_architecture:
            dummy_input = torch.randn(32, 20, 8, 8).to(self.device)
        else:
            dummy_input = torch.randn(32, 773).to(self.device)
        
        with torch.no_grad():
            for _ in range(10):
                if self.use_modern_architecture:
                    self.neural_network(dummy_input)
                else:
                    self.ml_ai.model(dummy_input)
        
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
        print("✅ GPU预热完成")
    
    def _warmup_with_historical_data(self):
        """使用历史数据进行充分预热训练 - 最大化历史样本利用"""
        if len(self.experience_buffer) == 0:
            print("📚 没有历史样本可用于预热训练")
            return
        
        print(f"🔥 历史样本全量预热训练 (缓冲区: {len(self.experience_buffer)} 样本)...")
        
        try:
            # 🆕 更激进的预热策略 - 使用更多历史样本
            total_samples = len(self.experience_buffer)
            
            # 根据样本数量决定预热规模
            if total_samples >= 10000:
                warmup_batches = 78
                samples_per_batch = 128
            
            print(f"🧠 预热策略: {warmup_batches} 批次，每批 {samples_per_batch} 样本")
            print(f"📊 预热覆盖率: {(warmup_batches * samples_per_batch / total_samples * 100):.1f}%")
            
            total_warmup_samples = 0
            warmup_losses = []
            
            for batch_idx in range(warmup_batches):
                print(f"📊 预热批次 {batch_idx + 1}/{warmup_batches}")
                
                # 从经验缓冲区采样更多历史样本
                replay_samples = self.experience_buffer.sample(samples_per_batch)
                
                if replay_samples:
                    # 转换为训练格式
                    replay_training_samples = []
                    for experience in replay_samples:
                        try:
                            replay_training_samples.append({
                                'features': experience['features'],
                                'target': experience['target']
                            })
                        except Exception as e:
                            # 兼容不同的经验格式
                            continue
                    
                    # 执行预热训练
                    if len(replay_training_samples) >= 8:
                        initial_loss = self.performance_stats.get('training_loss', 0.0)
                        self._train_neural_network_batch_immediate(replay_training_samples)
                        final_loss = self.performance_stats.get('training_loss', 0.0)
                        
                        total_warmup_samples += len(replay_training_samples)
                        warmup_losses.append(final_loss)
                        
                        # 显示预热进度
                        print(f"   ✅ 完成 {len(replay_training_samples)} 样本预热，损失: {final_loss:.4f}")
                    else:
                        print(f"   ⚠️ 跳过批次 {batch_idx + 1}：有效样本不足 ({len(replay_training_samples)} < 8)")
            
            # 预热总结
            if warmup_losses:
                avg_warmup_loss = np.mean(warmup_losses)
                loss_improvement = warmup_losses[0] - warmup_losses[-1] if len(warmup_losses) > 1 else 0.0
                
                print(f"✅ 历史样本全量预热完成！")
                print(f"   📊 预热样本总数: {total_warmup_samples}")
                print(f"   📊 实际覆盖率: {(total_warmup_samples / total_samples * 100):.1f}%")
                print(f"   📊 平均预热损失: {avg_warmup_loss:.4f}")
                print(f"   📊 损失改善: {loss_improvement:.4f}")
                print(f"   📊 模型总更新: {self.training_stats['model_updates']} 次")
                print(f"🧠 模型已通过充分的历史数据获得初始经验")
            else:
                print(f"⚠️ 预热过程中没有成功的训练批次")
                print(f"🧠 模型保持原始状态")
            
        except Exception as e:
            print(f"⚠️ 历史样本预热失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _play_single_game(self, opponent_type: str) -> Dict:
        """单局游戏"""
        board = ChessBoard()
        game_moves = []
        move_count = 0
        
        # 随机选择AI颜色
        ml_ai_color = random.choice([PieceColor.WHITE, PieceColor.BLACK])
        game_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        while not board.is_game_over() and move_count < self.config['max_moves_per_game']:
            current_player = board.current_player
            
            # 选择AI并获取移动
            if current_player == ml_ai_color:
                # ML AI的回合 - 根据配置使用MCTS
                if (self.use_modern_architecture and hasattr(self, 'mcts') and 
                    random.random() < self.config['mcts_usage_rate_serial']):
                    # 使用MCTS进行高质量搜索
                    move = self._get_mcts_move(board)
                else:
                    # 使用普通神经网络
                    move = self.ml_ai.get_best_move(board, current_player)
                ai_type = "ml_ai"
            else:
                # 对手的回合
                if opponent_type == 'basic':
                    move = self.basic_ai.get_best_move(board, current_player)
                elif opponent_type == 'random':
                    move = self._get_random_move(board, current_player)
                else:
                    move = self.ml_ai.get_best_move(board, current_player)
                ai_type = opponent_type
            
            if move is None:
                break
            
            from_pos, to_pos = move
            
            # 记录移动数据（仅ML AI）
            if ai_type == "ml_ai":
                # 简化的棋盘状态编码，使用FEN格式字符串
                try:
                    board_state = self._encode_board_to_fen(board)
                except:
                    board_state = f"error_{move_count}"
                
                game_moves.append({
                    'board_state': board_state,
                    'move': move,
                    'move_index': move_count
                })
            
            # 执行移动
            success = board.make_move(from_pos, to_pos)
            if not success:
                break
            
            move_count += 1
        
        # 确定游戏结果
        game_result = self._determine_game_result(board, ml_ai_color, move_count)
        game_result['moves'] = game_moves
        game_result['game_id'] = game_id
        
        return game_result
    
    def _get_mcts_move(self, board):
        """使用MCTS获取移动 - 增强错误处理和数值稳定性"""
        try:
            if hasattr(self, 'mcts'):
                root_node = self.mcts.search(board)
                action_probs = self.mcts.get_action_probabilities(root_node, temperature=self.config['temperature'])
                
                if action_probs and len(action_probs) > 0:
                    # 转换为列表并验证数据有效性
                    moves = list(action_probs.keys())
                    probs = list(action_probs.values())
                    
                    # 确保概率为numpy数组并进行数值检查
                    probs = np.array(probs, dtype=np.float64)
                    
                    # 验证概率有效性
                    if not np.all(np.isfinite(probs)) or not np.all(probs >= 0):
                        raise ValueError("检测到无效概率值")
                    
                    # 验证概率和
                    prob_sum = np.sum(probs)
                    if abs(prob_sum - 1.0) > 1e-5:
                        # 尝试重新归一化
                        if prob_sum > 1e-8:
                            probs = probs / prob_sum
                        else:
                            raise ValueError(f"概率和异常: {prob_sum}")
                    
                    # 温度采样选择移动
                    if self.config['temperature'] > 0 and len(probs) > 1:
                        try:
                            # 使用更安全的随机选择
                            chosen_index = np.random.choice(len(moves), p=probs)
                            chosen_move = moves[chosen_index]
                        except ValueError as e:
                            # 如果随机选择失败，选择最高概率的移动
                            print(f"⚠️ 随机选择失败，使用贪婪选择: {e}")
                            best_index = np.argmax(probs)
                            chosen_move = moves[best_index]
                    else:
                        # 选择最佳移动（贪婪策略）
                        best_index = np.argmax(probs)
                        chosen_move = moves[best_index]
                    
                    return chosen_move
                else:
                    raise ValueError("MCTS返回空的概率分布")
                    
        except Exception as e:
            print(f"⚠️ MCTS失败，回退到神经网络: {e}")
        
        # 回退到普通神经网络
        return self.ml_ai.get_best_move(board, board.current_player)
    
    def _get_random_move(self, board: ChessBoard, color: PieceColor):
        """获取随机合法移动"""
        legal_moves = []
        
        for position, piece in board.pieces.items():
            if piece.color == color:
                moves = board.get_legal_moves(position)
                for to_pos in moves:
                    legal_moves.append((position, to_pos))
        
        return random.choice(legal_moves) if legal_moves else None
    
    def _get_thread_safe_ml_move(self, board, color):
        """线程安全的ML AI移动获取 - 使用线程局部存储避免深拷贝"""
        try:
            # 使用线程局部存储获取当前线程的AI实例
            import threading
            if not hasattr(self, '_thread_local'):
                self._thread_local = threading.local()
            
            # 如果当前线程还没有AI实例，创建一个
            if not hasattr(self._thread_local, 'local_ai'):
                if self.use_modern_architecture:
                    # 为当前线程创建独立的现代架构AI
                    local_neural_network = ModernChessNetwork().to(self.device)
                    local_neural_network.load_state_dict(self.neural_network.state_dict())
                    local_neural_network.eval()
                    
                    # 创建线程局部的包装器
                    self._thread_local.local_ai = self._create_thread_local_ai_wrapper(
                        local_neural_network, self.board_encoder
                    )
                else:
                    # 传统架构的线程安全处理
                    self._thread_local.local_ai = self.ml_ai
            
            # 使用线程局部AI获取移动
            if hasattr(self._thread_local.local_ai, 'get_best_move'):
                return self._thread_local.local_ai.get_best_move(board, color)
            else:
                return self._get_random_move(board, color)
                
        except Exception as e:
            # 如果线程局部AI创建失败，回退到随机移动
            print(f"⚠️ 线程安全AI调用失败: {e}")
            return self._get_random_move(board, color)
    
    def _create_thread_local_ai_wrapper(self, neural_network, board_encoder):
        """为当前线程创建AI包装器"""
        class ThreadLocalAIWrapper:
            def __init__(self, network, encoder, device):
                self.neural_network = network
                self.board_encoder = encoder
                self.device = device
                self.epsilon = 0.1  # 线程局部探索率
            
            def get_best_move(self, board, color):
                try:
                    # 简化的最佳移动选择
                    legal_moves = self._get_legal_moves(board, color)
                    if not legal_moves:
                        return None
                    
                    # ε-贪心策略
                    if random.random() < self.epsilon:
                        return random.choice(legal_moves)
                    
                    # 使用神经网络评估
                    best_move = None
                    best_score = float('-inf')
                    
                    # 简化评估 - 只评估前几个移动以提高速度
                    moves_to_evaluate = random.sample(legal_moves, min(5, len(legal_moves)))
                    
                    for move in moves_to_evaluate:
                        try:
                            # 简化的位置评估
                            score = random.random() + self._evaluate_move_simple(board, move, color)
                            if score > best_score:
                                best_score = score
                                best_move = move
                        except:
                            continue
                    
                    return best_move if best_move else random.choice(legal_moves)
                except:
                    # 失败时返回随机移动
                    legal_moves = self._get_legal_moves(board, color)
                    return random.choice(legal_moves) if legal_moves else None
            
            def _get_legal_moves(self, board, color):
                """获取合法移动"""
                legal_moves = []
                for position, piece in board.pieces.items():
                    if piece.color == color:
                        moves = board.get_legal_moves(position)
                        for to_pos in moves:
                            legal_moves.append((position, to_pos))
                return legal_moves
            
            def _evaluate_move_simple(self, board, move, color):
                """简化的移动评估"""
                from_pos, to_pos = move
                score = 0.0
                
                # 中心控制奖励
                center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
                if to_pos in center_squares:
                    score += 0.5
                
                # 吃子奖励
                if to_pos in board.pieces:
                    score += 1.0
                
                return score
        
        return ThreadLocalAIWrapper(neural_network, board_encoder, self.device)
    
    
    
    def _training_consumer(self, game_queue: queue.Queue, total_games: int):
        """训练数据消费者线程（短超时+动态批次+节流日志）"""
        print("🧠 训练消费者线程启动")

        processed_games = 0
        batch_buffer: list = []
        batch_target = int(self.config.get('consumer_batch_target', 256))  # 目标批大小
        min_batch = int(self.config.get('consumer_min_batch', 64))         # 最小触发训练的批大小
        flush_timeout_ms = float(self.config.get('consumer_flush_timeout_ms', 40))  # 动态刷新定时（毫秒）
        last_flush_ts = time.perf_counter()
        last_warn_ts = 0.0
        warn_interval = 30.0  # 延长告警间隔至30秒，减少日志刷屏

        while processed_games < total_games and not self._stop_training.is_set():
            try:
                # 短超时以避免长时间卡住
                game_result = game_queue.get(timeout=0.25)

                if game_result is None:  # 停止信号
                    break

                # 处理游戏结果 - 确保保存到数据库
                if isinstance(game_result, dict):
                    # 先保存游戏到数据库
                    if game_result.get('result') != 'error':
                        try:
                            self._save_game_to_database(game_result)
                        except Exception as e:
                            print(f"⚠️ 保存游戏到数据库失败: {e}")
                    
                    # 提取训练样本
                    if game_result.get('result') != 'error':
                        training_samples = self._extract_training_samples_parallel(game_result)
                        if training_samples:
                            batch_buffer.extend(training_samples)
                            # 添加到经验回放缓冲区
                            for sample in training_samples:
                                self.experience_buffer.add(sample)

                processed_games += 1

                # 动态批次刷新：达到目标批或到达最小批且超时
                now = time.perf_counter()
                if len(batch_buffer) >= batch_target or (
                    len(batch_buffer) >= min_batch and (now - last_flush_ts) * 1000.0 >= flush_timeout_ms
                ):
                    # 使用经验回放+优化训练
                    try:
                        self._train_batch_parallel(batch_buffer[:batch_target])
                    finally:
                        # 滑动窗口保留尾部未训练样本
                        batch_buffer = batch_buffer[batch_target:]
                        last_flush_ts = now

            except queue.Empty:
                # 检查停止标志
                if self._stop_training.is_set():
                    print("🛑 消费者线程检测到停止信号")
                    break
                    
                # 定时检查是否需要基于时间刷新
                now = time.perf_counter()
                if len(batch_buffer) >= min_batch and (now - last_flush_ts) * 1000.0 >= flush_timeout_ms:
                    try:
                        self._train_batch_parallel(batch_buffer[:batch_target])
                    finally:
                        batch_buffer = batch_buffer[batch_target:]
                        last_flush_ts = now
                # 节流超时日志 - 提供更多有用信息
                if now - last_warn_ts >= warn_interval:
                    queue_size = game_queue.qsize()
                    buffer_size = len(batch_buffer)
                    print(f"⌛ 训练消费者等待数据... [队列:{queue_size}, 缓存:{buffer_size}/{batch_target}, 已处理:{processed_games}/{total_games}]")
                    last_warn_ts = now
                continue
            except Exception as e:
                # 节流错误日志
                now = time.perf_counter()
                if now - last_warn_ts >= warn_interval and not self._stop_training.is_set():
                    print(f"⚠️ 训练消费者错误: {e}")
                    last_warn_ts = now
                continue

        # 处理剩余批次
        if batch_buffer:
            self._train_batch_parallel(batch_buffer)

        print("🧠 训练消费者线程完成")
    
    def _extract_training_samples_parallel(self, game_result):
        """从并行游戏结果提取训练样本 - 修复版本"""
        training_samples = []
        
        try:
            moves = game_result.get('moves', [])
            ml_ai_result = game_result.get('ml_ai_result')
            
            # 转换游戏结果为数值
            if ml_ai_result == 'win':
                game_value = 1.0
            elif ml_ai_result == 'loss':
                game_value = -1.0
            else:
                game_value = 0.0  # 和棋或其他情况
            
            # 处理每个ML AI的移动
            if len(moves) > 0:
                for i, move_data in enumerate(moves):
                    # 获取棋盘状态 - 支持多种键名
                    board_state = (move_data.get('board_state') or 
                                 move_data.get('board_fen') or 
                                 move_data.get('position') or
                                 'default_position')
                    
                    # 计算目标值 - 考虑移动的时间位置
                    move_factor = 1.0 - (i * 0.1 / max(1, len(moves)))
                    target_value = game_value * move_factor
                    
                    # 创建训练样本
                    training_sample = {
                        'board_fen': board_state,
                        'target_value': target_value,
                        'move': move_data.get('move'),
                        'player': move_data.get('player'),
                        'move_number': move_data.get('move_number', i + 1),
                        'game_phase': 'opening' if i < len(moves) * 0.3 else 
                                    'middlegame' if i < len(moves) * 0.7 else 'endgame'
                    }
                    training_samples.append(training_sample)
            
        except Exception as e:
            print(f"⚠️ 提取训练样本失败: {e}")
            import traceback
            traceback.print_exc()
        
        return training_samples
    
    def _play_parallel_game(self, opponent_type: str, game_id: int) -> Dict:
        """并行游戏执行 - 优化版本，生成更好的训练数据"""
        try:
            board = ChessBoard()
            game_moves = []
            move_count = 0
            
            # 创建独立的Basic AI实例 - 降低深度提升速度
            local_basic_ai = BasicAI(depth=2)
            
            # 随机选择AI颜色
            ml_ai_color = random.choice([PieceColor.WHITE, PieceColor.BLACK])
            
            # 游戏主循环 - 移除超时限制，让游戏自然结束
            while (not board.is_game_over() and 
                   move_count < self.config['max_moves_per_game'] and 
                   not self._stop_training.is_set()):
                
                current_player = board.current_player
                move = None
                ai_type = "unknown"
                
                if current_player == ml_ai_color:
                    # ML AI的回合 - 根据配置选择搜索策略
                    try:
                        if (self.use_modern_architecture and hasattr(self, 'mcts') and 
                            random.random() < self.config['mcts_usage_rate_parallel']):
                            # 使用MCTS进行高质量搜索（保守使用率）
                            move = self._get_mcts_move(board)
                            ai_type = "ml_ai_mcts"
                        else:
                            # 使用快速神经网络模式
                            move = self._get_fast_ml_move(board, current_player)
                            ai_type = "ml_ai"
                    except Exception as e:
                        # 如果ML AI失败，使用随机移动
                        move = self._get_random_move(board, current_player)
                        ai_type = "ml_ai_fallback"
                else:
                    # 对手的回合
                    if opponent_type == 'basic':
                        try:
                            move = local_basic_ai.get_best_move(board, current_player)
                            ai_type = "basic_ai"
                        except Exception:
                            move = self._get_random_move(board, current_player)
                            ai_type = "basic_ai_fallback"
                    else:
                        move = self._get_random_move(board, current_player)
                        ai_type = "random"
                
                if move is None:
                    # 无合法移动，游戏结束
                    break
                
                # 记录ML AI的移动数据用于训练
                if current_player == ml_ai_color:
                    # 创建训练样本
                    board_encoding = self._encode_board_to_fen(board)
                    
                    game_moves.append({
                        'move': move,
                        'player': current_player.name.lower(),
                        'board_state': board_encoding,
                        'move_number': move_count + 1,
                        'ai_type': ai_type,
                        'piece_type': board.pieces.get(move[0]).piece_type.name if move[0] in board.pieces else 'unknown',
                        'notation': f"{move[0]}-{move[1]}"
                    })
                
                # 执行移动
                from_pos, to_pos = move
                success = board.make_move(from_pos, to_pos)
                
                if success:
                    move_count += 1
                else:
                    # 移动失败，游戏异常结束
                    break
            
            # 确定游戏结果
            game_result = self._determine_game_result(board, ml_ai_color, move_count)
            game_result['game_id'] = game_id
            game_result['moves'] = game_moves
            game_result['final_position'] = self._comprehensive_board_encode(board)
            game_result['total_moves'] = move_count
            
            return game_result
            
        except Exception as e:
            return {
                'game_id': game_id,
                'result': 'error',
                'ml_ai_result': 'error',
                'moves': [],
                'move_count': 0,
                'error': str(e),
                'total_moves': 0
            }
    
    def _get_fast_ml_move(self, board, color):
        """快速ML AI移动获取 - 优化性能"""
        try:
            # 🆕 使用更简单的评估策略
            legal_moves = self._get_legal_moves_for_player(board, color)
            if not legal_moves:
                return None
            
            # 如果移动数量少，使用神经网络
            if len(legal_moves) <= 3:
                return self.ml_ai.get_best_move(board, color)
            
            # 否则使用启发式快速选择
            return self._get_heuristic_fast_move(board, legal_moves, color)
            
        except Exception:
            return self._get_random_move(board, color)
    
    def _get_heuristic_fast_move(self, board, legal_moves, color):
        """启发式快速移动选择"""
        try:
            # 简单启发式：优先选择吃子移动
            capture_moves = []
            for move in legal_moves:
                from_pos, to_pos = move
                if to_pos in board.pieces and board.pieces[to_pos].color != color:
                    capture_moves.append(move)
            
            if capture_moves:
                return random.choice(capture_moves)
            
            # 否则随机选择
            return random.choice(legal_moves)
            
        except Exception:
            return random.choice(legal_moves) if legal_moves else None
    
    def _comprehensive_board_encode(self, board):
        """更全面的棋盘编码"""
        try:
            pieces_str = ""
            piece_count = 0
            
            for pos, piece in board.pieces.items():
                if piece_count < 32:  # 限制编码长度
                    pieces_str += f"{pos[0]}{pos[1]}{piece.color.name[0]}{piece.piece_type.name[0]};"
                    piece_count += 1
            
            # 添加游戏状态信息
            game_state = f"player:{board.current_player.name[0]};count:{piece_count};"
            
            return pieces_str + game_state
            
        except Exception as e:
            return f"error:{str(e)[:20]}"
    
    def _get_legal_moves_for_player(self, board, player):
        """获取指定玩家的所有合法移动"""
        legal_moves = []
        for position, piece in board.pieces.items():
            if piece.color == player:
                moves = board.get_legal_moves(position)
                for to_pos in moves:
                    legal_moves.append((position, to_pos))
        return legal_moves
    
    def _train_batch_parallel(self, training_samples):
        """并行训练批处理 - 使用正确的神经网络训练"""
        try:
            if len(training_samples) < 16:
                return
            
            # 转换为神经网络训练格式
            features = []
            targets = []
            
            for sample in training_samples:
                # 使用真实的棋盘编码而不是随机特征
                board_fen = sample.get('board_fen', '')
                if board_fen and board_fen != 'error':
                    # 简化的FEN编码转换为特征向量
                    board_features = self._fen_to_features(board_fen)
                    if board_features is not None and board_features.size > 0:
                        features.append(board_features)
                        targets.append(float(sample.get('target_value', 0.0)))
            
            # 确保有足够的有效样本
            if len(features) >= 8:
                # 添加到经验回放缓冲区
                for i in range(len(features)):
                    sample_data = {
                        'features': features[i],
                        'target': targets[i]
                    }
                    priority = abs(targets[i]) + 0.1
                    self.experience_buffer.add(sample_data, priority)
                
                # 如果缓冲区足够大，进行批量训练
                if len(self.experience_buffer) >= self.config['batch_size']:
                    replay_samples = self.experience_buffer.sample(min(32, len(features)))
                    self._train_neural_network_batch_optimized(replay_samples)
                    
                    print(f"✅ 并行训练批次: {len(features)}样本 -> 缓冲区: {len(self.experience_buffer)}")
        
        except Exception as e:
            print(f"⚠️ 批量训练失败: {e}")
            import traceback
            print("📍 详细错误信息:")
            traceback.print_exc()
    
    def _fen_to_features(self, board_fen):
        """将简化的FEN编码转换为特征向量"""
        try:
            if not board_fen or board_fen == 'error':
                return None
            
            # 解析简化的FEN格式: "位置颜色棋子类型;"
            pieces_data = board_fen.split(';')
            
            # 创建8x8x20的特征张量 (20通道：12个棋子通道 + 8个预留/状态通道)
            if self.use_modern_architecture:
                features = np.zeros((20, 8, 8), dtype=np.float32)
                
                piece_mapping = {
                    'WK': 0, 'WQ': 1, 'WR': 2, 'WB': 3, 'WN': 4, 'WP': 5,
                    'BK': 6, 'BQ': 7, 'BR': 8, 'BB': 9, 'BN': 10, 'BP': 11
                }
                
                for piece_str in pieces_data:
                    if len(piece_str) >= 4:
                        try:
                            row = int(piece_str[0])
                            col = int(piece_str[1])
                            color = piece_str[2]  # W或B
                            piece_type = piece_str[3]  # K,Q,R,B,N,P
                            
                            piece_key = f"{color}{piece_type}"
                            if piece_key in piece_mapping and 0 <= row < 8 and 0 <= col < 8:
                                # 映射到前12个通道
                                channel = piece_mapping[piece_key]
                                if 0 <= channel < 12:
                                    features[channel, row, col] = 1.0
                        except:
                            continue
                
                return features
            else:
                # 传统架构使用平坦特征
                features = np.zeros(773, dtype=np.float32)
                
                # 简化的特征提取
                for i, piece_str in enumerate(pieces_data[:100]):  # 限制长度
                    if piece_str and len(piece_str) >= 4:
                        try:
                            row = int(piece_str[0])
                            col = int(piece_str[1])
                            pos_idx = row * 8 + col
                            if pos_idx < 64:
                                features[pos_idx] = 1.0  # 有棋子
                                
                                # 颜色特征
                                if piece_str[2] == 'W':
                                    features[64 + pos_idx] = 1.0
                                else:
                                    features[128 + pos_idx] = 1.0
                        except:
                            continue
                
                return features
                
        except Exception as e:
            print(f"⚠️ FEN编码转换失败: {e}")
            return None
    
    def _train_neural_network_batch_optimized(self, training_samples):
        """优化的神经网络批量训练"""
        if len(training_samples) < 8:
            return
        
        # 准备训练数据
        features = []
        targets = []
        
        for sample in training_samples:
            # 处理不同的样本格式
            if 'features' in sample:
                feature = sample['features']
                target = sample['target']
            elif 'board_fen' in sample:
                # 从FEN转换为特征向量
                try:
                    board_fen = sample['board_fen']
                    # 检查是否是标准FEN格式还是自定义格式
                    if '/' in board_fen and ' ' in board_fen:
                        # 标准FEN格式
                        board = ChessBoard()
                        if board.set_fen(board_fen):
                            feature = self._board_to_feature_vector(board, sample.get('player', PieceColor.WHITE))
                            target = sample.get('target_value', 0.0)
                        else:
                            print(f"⚠️ 无效标准FEN字符串: {board_fen}")
                            continue
                    else:
                        # 自定义格式，直接转换为特征
                        feature = self._custom_fen_to_features(board_fen)
                        target = sample.get('target_value', 0.0)
                        
                    if feature is None:
                        continue
                        
                except Exception as e:
                    print(f"⚠️ FEN转换特征失败: {e}")
                    continue
            else:
                print(f"⚠️ 未知样本格式: {list(sample.keys())}")
                continue
            
            # 验证特征形状
            if isinstance(feature, np.ndarray) and feature.size > 0:
                if self.use_modern_architecture:
                    # 现代架构期望 (20, 8, 8)；若为12通道则补齐
                    if feature.shape == (20, 8, 8):
                        features.append(feature)
                        targets.append(target)
                    elif feature.shape == (12, 8, 8):
                        padded = np.zeros((20, 8, 8), dtype=np.float32)
                        padded[:12] = feature
                        features.append(padded)
                        targets.append(target)
                else:
                    # 传统架构期望 (773,)
                    if len(feature.shape) == 1 and feature.shape[0] == 773:
                        features.append(feature)
                        targets.append(target)
        
        # 确保有足够的有效样本
        if len(features) < 8:
            return
        
        # 转换为张量
        try:
            if self.use_modern_architecture:
                features_tensor = torch.FloatTensor(np.array(features)).to(self.device)
            else:
                features_tensor = torch.FloatTensor(np.array(features)).to(self.device)
            
            targets_tensor = torch.FloatTensor(targets).to(self.device)
        except Exception as e:
            print(f"⚠️ 张量转换失败: {e}, features shapes: {[f.shape for f in features[:3]]}")
            return
        
        # 执行训练
        self.neural_network.train()
        self.optimizer.zero_grad()
        
        try:
            # 混合精度训练
            if self.scaler and self.device.type == 'cuda':
                with torch.cuda.amp.autocast():
                    loss = self._compute_loss_optimized(features_tensor, targets_tensor)
                
                self.scaler.scale(loss).backward()
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.neural_network.parameters(), self.config['gradient_clip_norm'])
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                loss = self._compute_loss_optimized(features_tensor, targets_tensor)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.neural_network.parameters(), self.config['gradient_clip_norm'])
                self.optimizer.step()
            
            # 更新统计
            self.performance_stats['training_loss'] = loss.item()
            self.training_stats['loss_progression'].append(loss.item())
            self.training_stats['model_updates'] += 1
            
            # 学习率调度
            self.scheduler.step()
            
        except Exception as e:
            print(f"⚠️ 神经网络训练失败: {e}")
    
    def _compute_loss_optimized(self, features_tensor, targets_tensor):
        """优化的损失计算"""
        if self.use_modern_architecture:
            policy, value, auxiliary = self.neural_network(features_tensor)
            
            # 多任务损失
            value_loss = nn.MSELoss()(value.squeeze(), targets_tensor)
            
            # 策略损失（使用目标值作为权重）
            policy_targets = torch.softmax(torch.randn_like(policy) * targets_tensor.unsqueeze(1), dim=1)
            policy_loss = nn.KLDivLoss(reduction='batchmean')(
                torch.log_softmax(policy, dim=1), 
                policy_targets
            )
            
            # 辅助损失
            aux_loss = nn.MSELoss()(auxiliary.squeeze(), torch.abs(targets_tensor))
            
            total_loss = value_loss + 0.1 * policy_loss + 0.05 * aux_loss
        else:
            predictions = self.neural_network(features_tensor).squeeze()
            total_loss = nn.MSELoss()(predictions, targets_tensor)
        
        return total_loss
    
    def _encode_board_to_fen(self, board):
        """将棋盘编码为简化的FEN字符串格式"""
        pieces_list = []
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece_at((row, col))
                if piece:
                    color = 'W' if piece.color.name == 'WHITE' else 'B'
                    piece_type = piece.piece_type.name[0]  # K, Q, R, B, N, P
                    pieces_list.append(f"{row}{col}{color}{piece_type}")
        
        return ';'.join(pieces_list)
    
    def _determine_game_result(self, board: ChessBoard, ml_ai_color: PieceColor, move_count: int) -> Dict:
        """确定游戏结果"""
        result = {
            'move_count': move_count,
            'ml_ai_color': 'white' if ml_ai_color == PieceColor.WHITE else 'black'
        }
        
        if board.is_checkmate():
            loser = board.current_player
            winner = PieceColor.BLACK if loser == PieceColor.WHITE else PieceColor.WHITE
            
            result['result'] = 'white' if winner == PieceColor.WHITE else 'black'
            result['ml_ai_result'] = 'win' if winner == ml_ai_color else 'loss'
            result['termination'] = 'checkmate'
            
        elif board.is_stalemate() or move_count >= self.config['max_moves_per_game']:
            result['result'] = 'draw'
            result['ml_ai_result'] = 'draw'
            result['termination'] = 'stalemate' if board.is_stalemate() else 'max_moves'
        else:
            result['result'] = 'draw'
            result['ml_ai_result'] = 'draw'
            result['termination'] = 'incomplete'
        
        return result
    
    def _process_game_batch(self, game_batch: List[Dict]):
        """批处理游戏数据进行训练 - 优化版本确保训练执行"""
        if not game_batch:
            return
        
        start_time = time.time()
        print(f"🧠 开始处理 {len(game_batch)} 局游戏的训练数据...")
        
        # 收集训练样本
        training_samples = []
        
        # 🆕 同时保存游戏到数据库
        saved_games = 0
        
        for game in game_batch:
            # 🆕 保存游戏到数据库
            try:
                self._save_game_to_database(game)
                saved_games += 1
            except Exception as e:
                print(f"⚠️ 保存游戏到数据库失败: {e}")
            
            if 'moves' not in game or not game['moves']:
                print(f"⚠️ 游戏 {game.get('game_id', 'unknown')} 没有移动数据")
                continue
            
            game_result_value = self._get_result_value(game['result'], game['ml_ai_color'])
            
            for i, move_data in enumerate(game['moves']):
                board_state = move_data.get('board_state')
                
                # 修复数组布尔值判断错误
                if board_state is not None and (
                    (isinstance(board_state, str) and board_state.strip()) or
                    (isinstance(board_state, np.ndarray) and board_state.size > 0)
                ):
                    # 编码棋盘状态
                    if self.use_modern_architecture:
                        features = self._encode_board_modern(board_state)
                    else:
                        features = self._encode_board_traditional(board_state)
                    
                    if features is not None and features.size > 0:
                        target = self._calculate_training_target(game_result_value, i, len(game['moves']))
                        
                        training_samples.append({
                            'features': features,
                            'target': target,
                            'move': move_data.get('move'),
                            'game_id': game.get('game_id', 'unknown')
                        })
                        
                        # 添加到经验回放缓冲区
                        experience = {
                            'features': features,
                            'target': target,
                            'board_fen': board_state,
                            'move_index': i
                        }
                        priority = abs(target) + 0.1
                        self.experience_buffer.add(experience, priority)
        
        print(f"📊 收集到 {len(training_samples)} 个训练样本")
        print(f"💾 已保存 {saved_games} 局游戏到数据库")
        
        # 🆕 更新总训练样本统计
        self.training_stats['total_training_samples'] = len(self.experience_buffer)
        print(f"📈 缓冲区总样本数: {self.training_stats['total_training_samples']}")
        
        # 立即训练样本（降低阈值）
        if len(training_samples) >= self.config['min_training_samples']:
            print(f"🚀 立即执行神经网络训练 ({len(training_samples)} 样本)")
            self._train_neural_network_batch_immediate(training_samples)
        
        # 如果缓冲区足够大，也进行额外的回放训练
        if len(self.experience_buffer) >= self.config['batch_size']:
            # 增加历史样本使用比例 - 使用更多历史样本
            replay_batch_size = min(self.config['batch_size'], len(self.experience_buffer) // 4)  # 使用1/4缓冲区
            replay_batch_size = max(replay_batch_size, 32)  # 至少32个样本
            
            print(f"🔄 进行经验回放训练 (缓冲区大小: {len(self.experience_buffer)}, 使用: {replay_batch_size})")
            replay_samples = self.experience_buffer.sample(replay_batch_size)
            replay_training_samples = []
            for experience in replay_samples:
                replay_training_samples.append({
                    'features': experience['features'],
                    'target': experience['target']
                })
            if replay_training_samples:
                self._train_neural_network_batch_immediate(replay_training_samples)
        
        self.performance_stats['batch_processing_time'] = time.time() - start_time
        print(f"⏱️ 批处理完成，用时 {self.performance_stats['batch_processing_time']:.2f} 秒")
    
    def _encode_board_modern(self, board_state):
        """现代架构的棋盘编码"""
        try:
            # 创建8x8x20的特征张量 (20通道：每种棋子类型2个颜色 + 游戏状态)
            features = np.zeros((20, 8, 8), dtype=np.float32)
            
            if isinstance(board_state, str) and board_state != 'error' and board_state.strip():
                # 解析简化的编码格式
                parts = board_state.split(';')
                valid_pieces = 0
                
                for part in parts:
                    if len(part) >= 4:
                        try:
                            row = int(part[0])
                            col = int(part[1])
                            color_char = part[2]
                            piece_char = part[3]
                            
                            if 0 <= row < 8 and 0 <= col < 8:
                                # 计算特征通道
                                piece_channel = self._get_piece_channel(piece_char, color_char)
                                if piece_channel < 20:
                                    features[piece_channel, row, col] = 1.0
                                    valid_pieces += 1
                        except (ValueError, IndexError):
                            continue
                
                # 如果没有有效棋子，返回None
                if valid_pieces == 0:
                    return None
            else:
                # 无效输入，返回None
                return None
            
            return features
            
        except Exception as e:
            print(f"⚠️ 现代架构编码失败: {e}")
            return None
    
    def _custom_fen_to_features(self, custom_fen: str):
        """将自定义FEN格式转换为特征向量
        自定义格式: '00WR;01WP;06BP;...' (位置+颜色+棋子类型)
        """
        try:
            if not custom_fen or custom_fen == 'error':
                return None
            
            if self.use_modern_architecture:
                # 现代架构：创建20通道的8x8特征张量
                features = np.zeros((20, 8, 8), dtype=np.float32)
                
                # 棋子类型到通道的映射
                piece_channels = {
                    ('P', 'W'): 0,  ('P', 'B'): 1,  # 兵
                    ('R', 'W'): 2,  ('R', 'B'): 3,  # 车
                    ('N', 'W'): 4,  ('N', 'B'): 5,  # 马
                    ('B', 'W'): 6,  ('B', 'B'): 7,  # 象
                    ('Q', 'W'): 8,  ('Q', 'B'): 9,  # 后
                    ('K', 'W'): 10, ('K', 'B'): 11, # 王
                }
                
                # 解析自定义FEN
                pieces = custom_fen.split(';')
                piece_count = 0
                white_pieces = 0
                black_pieces = 0
                
                for piece_info in pieces:
                    if len(piece_info) >= 3:
                        try:
                            # 解析位置：前2位是行列
                            row = int(piece_info[0])
                            col = int(piece_info[1])
                            
                            # 解析颜色和棋子类型
                            color = piece_info[2]  # W or B
                            piece_type = piece_info[3] if len(piece_info) > 3 else 'P'
                            
                            # 确保坐标在有效范围内
                            if 0 <= row < 8 and 0 <= col < 8:
                                channel = piece_channels.get((piece_type, color))
                                if channel is not None:
                                    features[channel, row, col] = 1.0
                                    piece_count += 1
                                    if color == 'W':
                                        white_pieces += 1
                                    else:
                                        black_pieces += 1
                        except (ValueError, IndexError):
                            continue
                
                # 添加游戏状态信息
                # 假设白方先行（可以根据实际情况调整）
                features[12, :, :] = 1.0  # 白方回合（默认）
                
                # 游戏阶段估计
                total_pieces = piece_count
                if total_pieces > 24:
                    features[16, :, :] = 1.0  # 开局
                elif total_pieces > 12:
                    features[17, :, :] = 1.0  # 中局
                else:
                    features[18, :, :] = 1.0  # 残局
                
                return features
            else:
                # 传统架构：创建773维特征向量
                features = np.zeros(773, dtype=np.float32)
                
                pieces = custom_fen.split(';')
                piece_count = 0
                
                for piece_info in pieces:
                    if len(piece_info) >= 3:
                        try:
                            row = int(piece_info[0])
                            col = int(piece_info[1])
                            color = piece_info[2]
                            piece_type = piece_info[3] if len(piece_info) > 3 else 'P'
                            
                            if 0 <= row < 8 and 0 <= col < 8:
                                square_idx = row * 8 + col
                                if square_idx < 64:
                                    features[square_idx] = 1.0  # 有棋子
                                    
                                    # 棋子类型编码
                                    type_values = {'P': 1, 'R': 5, 'N': 3, 'B': 3, 'Q': 9, 'K': 100}
                                    piece_value = type_values.get(piece_type, 1)
                                    if color == 'B':
                                        piece_value = -piece_value
                                    features[64 + square_idx] = piece_value
                                    
                                    piece_count += 1
                        except (ValueError, IndexError):
                            continue
                
                # 添加全局状态
                features[128] = piece_count / 32.0  # 归一化棋子数量
                return features
                
        except Exception as e:
            print(f"⚠️ 自定义FEN解析失败: {e}")
            return None
    
    def _board_to_feature_vector(self, board: ChessBoard, player: PieceColor):
        """将棋盘对象转换为特征向量"""
        try:
            if self.use_modern_architecture:
                # 现代架构：创建20通道的8x8特征张量
                features = np.zeros((20, 8, 8), dtype=np.float32)
                
                # 基础棋子通道 (0-11)：每种棋子类型2个通道（白/黑）
                piece_channels = {
                    (PieceType.PAWN, PieceColor.WHITE): 0,
                    (PieceType.PAWN, PieceColor.BLACK): 1,
                    (PieceType.ROOK, PieceColor.WHITE): 2,
                    (PieceType.ROOK, PieceColor.BLACK): 3,
                    (PieceType.KNIGHT, PieceColor.WHITE): 4,
                    (PieceType.KNIGHT, PieceColor.BLACK): 5,
                    (PieceType.BISHOP, PieceColor.WHITE): 6,
                    (PieceType.BISHOP, PieceColor.BLACK): 7,
                    (PieceType.QUEEN, PieceColor.WHITE): 8,
                    (PieceType.QUEEN, PieceColor.BLACK): 9,
                    (PieceType.KING, PieceColor.WHITE): 10,
                    (PieceType.KING, PieceColor.BLACK): 11,
                }
                
                # 填充棋子位置
                for position, piece in board.pieces.items():
                    x, y = position
                    if 0 <= x < 8 and 0 <= y < 8:
                        channel = piece_channels.get((piece.piece_type, piece.color))
                        if channel is not None:
                            features[channel, y, x] = 1.0
                
                # 状态通道 (12-19)
                # 当前玩家通道
                if player == PieceColor.WHITE:
                    features[12, :, :] = 1.0  # 白方回合
                else:
                    features[13, :, :] = 1.0  # 黑方回合
                
                # 将军状态
                if board.is_in_check(PieceColor.WHITE):
                    features[14, :, :] = 1.0
                if board.is_in_check(PieceColor.BLACK):
                    features[15, :, :] = 1.0
                
                # 游戏阶段（根据棋子数量估算）
                total_pieces = len(board.pieces)
                if total_pieces > 24:
                    features[16, :, :] = 1.0  # 开局
                elif total_pieces > 12:
                    features[17, :, :] = 1.0  # 中局
                else:
                    features[18, :, :] = 1.0  # 残局
                
                # 预留通道
                features[19, :, :] = 0.0  # 预留
                
                return features
            else:
                # 传统架构：创建773维特征向量
                features = np.zeros(773, dtype=np.float32)
                
                # 基础位置编码 (0-63)
                for position, piece in board.pieces.items():
                    x, y = position
                    if 0 <= x < 8 and 0 <= y < 8:
                        square_idx = y * 8 + x
                        if square_idx < 64:
                            features[square_idx] = 1.0
                
                # 棋子类型编码 (64-127)
                piece_type_offset = 64
                for position, piece in board.pieces.items():
                    x, y = position
                    if 0 <= x < 8 and 0 <= y < 8:
                        square_idx = y * 8 + x
                        if square_idx < 64:
                            piece_value = piece.piece_type.value * (1 if piece.color == PieceColor.WHITE else -1)
                            features[piece_type_offset + square_idx] = piece_value
                
                # 游戏状态编码 (128-...)
                state_offset = 128
                features[state_offset] = 1.0 if player == PieceColor.WHITE else -1.0
                features[state_offset + 1] = 1.0 if board.is_in_check(PieceColor.WHITE) else 0.0
                features[state_offset + 2] = 1.0 if board.is_in_check(PieceColor.BLACK) else 0.0
                features[state_offset + 3] = len(board.pieces) / 32.0  # 归一化棋子数量
                
                return features
                
        except Exception as e:
            print(f"⚠️ 棋盘特征向量转换失败: {e}")
            return None
    
    def _encode_board_traditional(self, board_state):
        """传统架构的棋盘编码"""
        try:
            # 创建773维特征向量
            features = np.zeros(773, dtype=np.float32)
            
            if isinstance(board_state, str) and board_state != 'error' and board_state.strip():
                # 简化编码：前64位代表棋盘位置，后面代表棋子类型等
                parts = board_state.split(';')
                piece_count = 0
                
                for part in parts:
                    if len(part) >= 4 and piece_count < 64:
                        try:
                            row = int(part[0])
                            col = int(part[1])
                            if 0 <= row < 8 and 0 <= col < 8:
                                pos_index = row * 8 + col
                                if pos_index < 64:
                                    features[pos_index] = 1.0
                                piece_count += 1
                        except (ValueError, IndexError):
                            continue
                
                # 如果没有棋子数据，返回None
                if piece_count == 0:
                    return None
                
                # 添加一些随机特征以增加多样性
                features[64:128] = np.random.random(64) * 0.2
                features[128:256] = np.random.random(128) * 0.1
            else:
                # 无效输入，返回None
                return None
            
            return features
            
        except Exception as e:
            print(f"⚠️ 传统架构编码失败: {e}")
            return None
    
    def _get_piece_channel(self, piece_char, color_char):
        """获取棋子对应的特征通道"""
        piece_types = {'K': 0, 'Q': 2, 'R': 4, 'B': 6, 'N': 8, 'P': 10}
        color_offset = 0 if color_char == 'W' else 1
        return piece_types.get(piece_char, 12) + color_offset
    
    def _train_neural_network_batch_immediate(self, training_samples):
        """立即执行神经网络训练 - 确保训练发生"""
        if len(training_samples) < 4:  # 进一步降低最小阈值
            print(f"⚠️ 样本数不足 ({len(training_samples)} < 4)，跳过训练")
            return
        
        print(f"🧠 开始神经网络训练 ({len(training_samples)} 样本)...")
        
        # 准备训练数据
        features = []
        targets = []
        
        for sample in training_samples:
            feature = sample['features']
            # 验证特征形状
            if isinstance(feature, np.ndarray) and feature.size > 0:
                if self.use_modern_architecture:
                    # 现代架构期望 (20, 8, 8)，若为12通道则补齐
                    if feature.shape == (20, 8, 8):
                        features.append(feature)
                        targets.append(sample['target'])
                    elif feature.shape == (12, 8, 8):
                        padded = np.zeros((20, 8, 8), dtype=np.float32)
                        padded[:12] = feature
                        features.append(padded)
                        targets.append(sample['target'])
                else:
                    # 传统架构期望 (773,)
                    if len(feature.shape) == 1 and feature.shape[0] == 773:
                        features.append(feature)
                        targets.append(sample['target'])
        
        # 确保有足够的有效样本
        if len(features) < 4:
            print(f"⚠️ 验证后样本数不足 ({len(features)} < 4)，跳过训练")
            return
        
        # 转换为张量
        try:
            if self.use_modern_architecture:
                features_tensor = torch.FloatTensor(np.array(features)).to(self.device)
            else:
                features_tensor = torch.FloatTensor(np.array(features)).to(self.device)
            
            targets_tensor = torch.FloatTensor(targets).to(self.device)
            
            print(f"📊 特征张量形状: {features_tensor.shape}")
            print(f"📊 目标张量形状: {targets_tensor.shape}")
            
            # 执行训练
            self.neural_network.train()
            self.optimizer.zero_grad()
            
            # 前向传播和损失计算
            if self.use_modern_architecture:
                policy, value, auxiliary = self.neural_network(features_tensor)
                
                # 多任务损失
                value_loss = nn.MSELoss()(value.squeeze(), targets_tensor)
                
                # 策略损失
                dummy_policy_targets = torch.softmax(torch.randn_like(policy), dim=1)
                policy_loss = nn.KLDivLoss(reduction='batchmean')(
                    torch.log_softmax(policy, dim=1), 
                    dummy_policy_targets
                )
                
                # 辅助损失
                aux_loss = nn.MSELoss()(auxiliary.squeeze(), torch.abs(targets_tensor))
                
                total_loss = value_loss + 0.1 * policy_loss + 0.05 * aux_loss
                print(f"📊 损失组成 - 价值: {value_loss.item():.4f}, 策略: {policy_loss.item():.4f}, 辅助: {aux_loss.item():.4f}")
            else:
                predictions = self.neural_network(features_tensor).squeeze()
                total_loss = nn.MSELoss()(predictions, targets_tensor)
                print(f"📊 预测损失: {total_loss.item():.4f}")
            
            # 反向传播
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.neural_network.parameters(), self.config['gradient_clip_norm'])
            self.optimizer.step()
            
            # 记录统计
            self.performance_stats['training_loss'] = total_loss.item()
            self.training_stats['loss_progression'].append(total_loss.item())
            self.training_stats['model_updates'] += 1
            
            print(f"✅ 模型更新完成！总更新次数: {self.training_stats['model_updates']}")
            print(f"📊 当前损失: {total_loss.item():.4f}")
            
            # 学习率调度
            if hasattr(self, 'scheduler'):
                self.scheduler.step()
                print(f"📊 当前学习率: {self.optimizer.param_groups[0]['lr']:.6f}")
            
        except Exception as e:
            print(f"❌ 神经网络训练失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_result_value(self, result: str, ml_ai_color: str) -> float:
        """获取游戏结果数值"""
        if result == 'draw':
            return 0.0
        elif (result == 'white' and ml_ai_color == 'white') or (result == 'black' and ml_ai_color == 'black'):
            return 1.0
        else:
            return -1.0
    
    def _calculate_training_target(self, game_result: float, move_index: int, total_moves: int) -> float:
        """计算训练目标值"""
        # 时间衰减
        time_decay = (total_moves - move_index) / total_moves
        
        # 目标值
        target = game_result * time_decay * 0.8
        
        # 添加少量噪声
        noise = np.random.normal(0, 0.05)
        target += noise
        
        return float(np.clip(target, -1.0, 1.0))
    
    def _train_neural_network_batch(self, training_samples: List[Dict]):
        """批量训练神经网络"""
        if len(training_samples) < 32:  # 最小批次大小
            return
        
        # 采样批次
        batch_samples = random.sample(training_samples, min(self.config['batch_size'], len(training_samples)))
        
        # 准备数据
        features = []
        targets = []
        
        for sample in batch_samples:
            features.append(sample['features'])
            targets.append(sample['target'])
        
        # 转换为张量
        if self.use_modern_architecture:
            # 现代架构：(batch, channels, height, width)
            features_tensor = torch.FloatTensor(np.array(features)).to(self.device)
        else:
            # 传统架构：(batch, features)
            features_tensor = torch.FloatTensor(np.array(features)).to(self.device)
        
        targets_tensor = torch.FloatTensor(targets).to(self.device)
        
        # 训练
        self.neural_network.train()
        self.optimizer.zero_grad()
        
        # 混合精度训练
        if self.scaler and self.device.type == 'cuda':
            with torch.cuda.amp.autocast():
                if self.use_modern_architecture:
                    policy, value, auxiliary = self.neural_network(features_tensor)
                    # 多任务损失
                    value_loss = nn.MSELoss()(value.squeeze(), targets_tensor)
                    policy_loss = nn.CrossEntropyLoss()(policy, torch.zeros(policy.size(0), dtype=torch.long).to(self.device))
                    aux_loss = nn.MSELoss()(auxiliary.squeeze(), torch.abs(targets_tensor))
                    total_loss = value_loss + 0.1 * policy_loss + 0.05 * aux_loss
                else:
                    predictions = self.neural_network(features_tensor).squeeze()
                    total_loss = nn.MSELoss()(predictions, targets_tensor)
            
            self.scaler.scale(total_loss).backward()
            self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.neural_network.parameters(), self.config['gradient_clip_norm'])
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            # 标准精度训练
            if self.use_modern_architecture:
                policy, value, auxiliary = self.neural_network(features_tensor)
                value_loss = nn.MSELoss()(value.squeeze(), targets_tensor)
                policy_loss = nn.CrossEntropyLoss()(policy, torch.zeros(policy.size(0), dtype=torch.long).to(self.device))
                aux_loss = nn.MSELoss()(auxiliary.squeeze(), torch.abs(targets_tensor))
                total_loss = value_loss + 0.1 * policy_loss + 0.05 * aux_loss
            else:
                predictions = self.neural_network(features_tensor).squeeze()
                total_loss = nn.MSELoss()(predictions, targets_tensor)
            
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.neural_network.parameters(), self.config['gradient_clip_norm'])
            self.optimizer.step()
        
        # 更新学习率
        if hasattr(self, 'adaptive_lr'):
            current_win_rate = self._get_current_win_rate()
            self.adaptive_lr.update(total_loss.item(), current_win_rate, self.optimizer)
        
        self.scheduler.step()
        
        # 记录统计
        self.performance_stats['training_loss'] = total_loss.item()
        self.training_stats['loss_progression'].append(total_loss.item())
        self.training_stats['model_updates'] += 1
        
        # 动态调整探索率
        if hasattr(self.ml_ai, 'epsilon'):
            if self.use_modern_architecture and hasattr(self, 'training_strategy'):
                # 使用课程学习调整
                curriculum_params = self.training_strategy.curriculum_learning_update(self._get_current_win_rate())
                if curriculum_params:
                    self.ml_ai.epsilon = curriculum_params.get('epsilon', self.ml_ai.epsilon)
            else:
                # 传统epsilon衰减
                self.ml_ai.epsilon = max(0.05, self.ml_ai.epsilon * 0.9995)
            
            self.training_stats['epsilon_progression'].append(self.ml_ai.epsilon)
    
    def _update_stats(self, game_result: Dict):
        """更新训练统计"""
        self.training_stats['games_played'] += 1
        self.training_stats['total_moves'] += game_result['move_count']
        
        # 基本统计
        if game_result['result'] == 'white':
            self.training_stats['white_wins'] += 1
        elif game_result['result'] == 'black':
            self.training_stats['black_wins'] += 1
        else:
            self.training_stats['draws'] += 1
        
        # ML AI统计
        ml_result = game_result.get('ml_ai_result', 'draw')
        if ml_result == 'win':
            self.training_stats['ml_ai_wins'] += 1
        elif ml_result == 'loss':
            self.training_stats['ml_ai_losses'] += 1
        else:
            self.training_stats['ml_ai_draws'] += 1
        
        # 记录胜率进展
        if self.training_stats['games_played'] % 10 == 0:
            win_rate = self._get_current_win_rate()
            self.training_stats['win_rate_progression'].append(win_rate)
    
    def _log_training_progress(self, game_num: int, last_game_result: Dict):
        """记录详细的训练进度"""
        print(f"\n📈 训练进度报告 (第 {game_num} 局)")
        print(f"   最新游戏结果: {last_game_result.get('ml_ai_result', 'unknown')}")
        print(f"   最新游戏长度: {last_game_result.get('move_count', 0)} 回合")
        print(f"   当前胜率: {self._get_current_win_rate():.1f}%")
        print(f"   模型更新次数: {self.training_stats['model_updates']}")
        print(f"   经验缓冲区: {len(self.experience_buffer)} 样本")
        print(f"   当前探索率: {self.ml_ai.epsilon:.3f}")
        
        if self.training_stats['loss_progression']:
            recent_loss = self.training_stats['loss_progression'][-1]
            avg_loss = np.mean(self.training_stats['loss_progression'][-10:])
            print(f"   最新损失: {recent_loss:.4f}")
            print(f"   平均损失: {avg_loss:.4f}")
        
        print(f"   GPU使用率: {self._get_gpu_usage():.1f}%")
        print(f"   处理速度: {self.performance_stats.get('games_per_second', 0):.2f} 局/秒")
    
    def _get_current_win_rate(self) -> float:
        """获取当前ML AI胜率"""
        total = self.training_stats['ml_ai_wins'] + self.training_stats['ml_ai_losses'] + self.training_stats['ml_ai_draws']
        if total == 0:
            return 0.0
        return (self.training_stats['ml_ai_wins'] / total) * 100
    
    def _get_gpu_usage(self) -> float:
        """获取GPU使用率"""
        if torch.cuda.is_available():
            return torch.cuda.utilization() or 0.0
        return 0.0
    
    def _evaluate_and_save(self, game_num: int):
        """定期评估和保存 - 增强版本"""
        current_win_rate = self._get_current_win_rate()
        
        # 保存检查点
        checkpoint_path = os.path.join(self.models_dir, f"checkpoint_{game_num}.pth")
        self.ml_ai.save_model(checkpoint_path)
        
        # 检查是否需要保存为新的最佳模型
        is_new_best = self._check_and_save_best_model(current_win_rate, game_num)
        
        # 计算收敛指标
        self._calculate_convergence_metrics()
        
        # 更新模型追踪器
        self.model_tracker['current_model_performance'] = current_win_rate
        self.model_tracker['training_history'].append({
            'game_num': game_num,
            'win_rate': current_win_rate,
            'model_updates': self.training_stats['model_updates'],
            'timestamp': datetime.now().isoformat()
        })
        
        # 进度报告
        avg_loss = np.mean(self.training_stats['loss_progression'][-50:]) if self.training_stats['loss_progression'] else 0.0
        
        print(f"\n📊 进度报告 ({game_num} 局):")
        print(f"   ML AI胜率: {current_win_rate:.1f}% {'🏆 新纪录!' if is_new_best else ''}")
        print(f"   历史最佳: {self.model_tracker['best_win_rate']:.1f}%")
        print(f"   平均损失: {avg_loss:.4f}")
        print(f"   探索率: {self.ml_ai.epsilon:.3f}")
        print(f"   模型更新: {self.training_stats['model_updates']:,} 次")
        print(f"   GPU使用: {self._get_gpu_usage():.1f}%")
        print(f"   缓冲区大小: {len(self.experience_buffer)}")
        
        # 动态调整探索率
        self._adjust_exploration_rate(current_win_rate, game_num)
    
    def _calculate_convergence_metrics(self):
        """计算收敛指标"""
        try:
            # 损失方差计算
            if len(self.training_stats['loss_progression']) >= 10:
                recent_losses = self.training_stats['loss_progression'][-20:]
                loss_variance = np.var(recent_losses)
                self.training_stats['convergence_metrics']['loss_variance'] = float(loss_variance)
            
            # 胜率稳定性计算
            if len(self.training_stats['win_rate_progression']) >= 5:
                recent_win_rates = self.training_stats['win_rate_progression'][-10:]
                win_rate_stability = 1.0 / (1.0 + np.std(recent_win_rates))
                self.training_stats['convergence_metrics']['win_rate_stability'] = float(win_rate_stability)
            
            # 学习曲线斜率计算
            if len(self.training_stats['win_rate_progression']) >= 3:
                x = np.arange(len(self.training_stats['win_rate_progression']))
                y = np.array(self.training_stats['win_rate_progression'])
                if len(x) > 1:
                    slope, _ = np.polyfit(x, y, 1)
                    self.training_stats['convergence_metrics']['learning_curve_slope'] = float(slope)
                    
        except Exception as e:
            print(f"⚠️ 收敛指标计算失败: {e}")
            # 设置默认值
            self.training_stats['convergence_metrics'].update({
                'loss_variance': 0.0,
                'win_rate_stability': 0.0,
                'learning_curve_slope': 0.0
            })
    
    def _check_and_save_best_model(self, current_win_rate: float, game_num: int) -> bool:
        """检查并保存最佳模型"""
        is_new_best = False
        
        # 如果当前表现超过历史最佳，保存为新的最佳模型
        if (current_win_rate > self.model_tracker['best_win_rate'] and 
            self.training_stats['games_played'] >= 20):  # 至少20局游戏
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            best_model_path = os.path.join(self.models_dir, f"best_model_{timestamp}.pth")
            
            # 保存新的最佳模型
            self.ml_ai.save_model(best_model_path)
            
            # 更新追踪器
            self.model_tracker.update({
                'best_model_path': best_model_path,
                'best_win_rate': current_win_rate,
                'best_model_games': self.training_stats['games_played']
            })
            
            # 保存追踪信息
            tracker_path = os.path.join(self.models_dir, "model_tracker.json")
            with open(tracker_path, 'w', encoding='utf-8') as f:
                json.dump(self.model_tracker, f, indent=2, ensure_ascii=False)
            
            print(f"🏆 新的最佳模型已保存: {best_model_path}")
            is_new_best = True
        
        return is_new_best
    
    def _adjust_exploration_rate(self, current_win_rate: float, game_num: int):
        """动态调整探索率"""
        if hasattr(self.ml_ai, 'epsilon'):
            # 基于性能动态调整探索率
            if current_win_rate > 60:
                # 表现很好，减少探索
                target_epsilon = 0.05
            elif current_win_rate > 40:
                # 表现中等，适度探索
                target_epsilon = 0.15
            else:
                # 表现较差，增加探索
                target_epsilon = 0.35
            
            # 渐进调整
            adjustment_rate = 0.1
            new_epsilon = self.ml_ai.epsilon * (1 - adjustment_rate) + target_epsilon * adjustment_rate
            
            # 更新探索率
            if hasattr(self.ml_ai, 'update_epsilon'):
                self.ml_ai.update_epsilon(new_epsilon)
            else:
                self.ml_ai.epsilon = max(0.05, min(0.5, new_epsilon))
    
    def _save_final_model(self):
        """保存最终模型 - 增强版本"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存最终模型
        final_path = os.path.join(self.models_dir, f"final_model_{timestamp}.pth")
        self.ml_ai.save_model(final_path)
        
        # 保存为默认模型
        default_path = os.path.join(self.models_dir, "ml_ai_model.pth")
        self.ml_ai.save_model(default_path)
        
        # 如果这次训练的表现是最佳的，同时保存为最佳模型
        current_win_rate = self._get_current_win_rate()
        if current_win_rate > self.model_tracker['best_win_rate']:
            best_final_path = os.path.join(self.models_dir, f"best_model_{timestamp}.pth")
            self.ml_ai.save_model(best_final_path)
            
            self.model_tracker.update({
                'best_model_path': best_final_path,
                'best_win_rate': current_win_rate,
                'best_model_games': self.training_stats['games_played']
            })
            print(f"🏆 训练完成！新的历史最佳模型: {best_final_path}")
        
        print(f"\n💾 模型已保存:")
        print(f"   最终模型: {final_path}")
        print(f"   默认模型: {default_path}")
        
        # 保存最终的模型追踪信息
        tracker_path = os.path.join(self.models_dir, "model_tracker.json")
        with open(tracker_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_tracker, f, indent=2, ensure_ascii=False)
    
    def _save_training_stats(self):
        """保存训练统计"""
        self.training_stats['end_time'] = datetime.now().isoformat()
        
        # 计算最终指标
        total_games = self.training_stats['games_played']
        if total_games > 0:
            self.training_stats['average_game_length'] = self.training_stats['total_moves'] / total_games
        
        # 确保models目录存在
        os.makedirs(self.models_dir, exist_ok=True)
        
        # 保存统计到models目录下
        stats_path = os.path.join(self.models_dir, f"training_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.training_stats, f, indent=2, ensure_ascii=False)
        
        # 保存性能统计到models目录下
        perf_path = os.path.join(self.models_dir, "performance_stats.json")
        with open(perf_path, 'w', encoding='utf-8') as f:
            json.dump(self.performance_stats, f, indent=2, ensure_ascii=False)
        
        print(f"📊 统计数据已保存:")
        print(f"   训练统计: {stats_path}")
        print(f"   性能统计: {perf_path}")
    
    def _print_comprehensive_stats(self):
        """打印综合统计报告"""
        stats = self.training_stats
        total_games = stats['games_played']
        historical_games = stats.get('historical_games_loaded', 0)
        total_training_samples = stats.get('total_training_samples', 0)
        
        print("\n" + "="*80)
        print("🎯 训练完成 - 综合统计报告")
        print("="*80)
        
        # 基础统计
        print(f"\n📈 基础指标:")
        print(f"   本次游戏数: {total_games:,}")
        if historical_games > 0:
            print(f"   历史游戏数: {historical_games:,}")
            print(f"   总游戏数: {total_games + historical_games:,}")
        if total_training_samples > 0:
            print(f"   总训练样本: {total_training_samples:,}")
        print(f"   训练时长: {self._format_duration(stats['total_training_time'])}")
        print(f"   游戏速度: {self.performance_stats['games_per_second']:.2f} 局/秒")
        print(f"   平均游戏长度: {stats.get('average_game_length', 0):.1f} 回合")
        
        # 架构信息
        print(f"\n🏗️ 模型架构:")
        print(f"   类型: {'现代AlphaZero架构' if self.use_modern_architecture else '传统架构'}")
        print(f"   参数数量: {self.performance_stats['total_parameters']:,}")
        print(f"   模型大小: {self.performance_stats['model_size_mb']:.1f} MB")
        
        # ML AI表现
        ml_total = stats['ml_ai_wins'] + stats['ml_ai_losses'] + stats['ml_ai_draws']
        if ml_total > 0:
            ml_win_rate = stats['ml_ai_wins'] / ml_total * 100
            print(f"\n🤖 ML AI表现:")
            print(f"   总对局: {ml_total:,}")
            print(f"   胜率: {ml_win_rate:.2f}%")
            print(f"   胜利: {stats['ml_ai_wins']:,}")
            print(f"   失败: {stats['ml_ai_losses']:,}")
            print(f"   和棋: {stats['ml_ai_draws']:,}")
        
        # 训练指标
        print(f"\n🧠 训练指标:")
        print(f"   模型更新: {stats['model_updates']:,} 次")
        print(f"   最终探索率: {self.ml_ai.epsilon:.4f}")
        print(f"   经验回放缓冲区: {len(self.experience_buffer)}")
        
        if stats['loss_progression']:
            final_loss = stats['loss_progression'][-1]
            avg_loss = np.mean(stats['loss_progression'])
            print(f"   最终损失: {final_loss:.4f}")
            print(f"   平均损失: {avg_loss:.4f}")
        
        # 性能统计
        print(f"\n⚡ 性能统计:")
        print(f"   批处理时间: {self.performance_stats['batch_processing_time']*1000:.1f} ms")
        print(f"   GPU使用率: {self._get_gpu_usage():.1f}%")
        print(f"   内存使用: {psutil.virtual_memory().percent:.1f}%")
        
        print("\n" + "="*80)
        print("🎉 训练报告完成!")
        print("="*80)
    
    def _save_game_to_database(self, game_result: Dict):
        """将游戏结果保存到数据库"""
        try:
            # 准备游戏数据
            start_time = datetime.now()
            end_time = datetime.now()
            
            # 确定玩家信息
            ml_ai_color = game_result.get('ml_ai_color', 'white')
            if ml_ai_color == 'white':
                white_player = "ML_AI"
                black_player = "BasicAI"
                white_type = "ai"
                black_type = "ai"
            else:
                white_player = "BasicAI"
                black_player = "ML_AI"
                white_type = "ai"
                black_type = "ai"
            
            # 准备游戏数据字典
            game_data = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'white_player': white_player,
                'black_player': black_player,
                'white_type': white_type,
                'black_type': black_type,
                'ai_level': "training",
                'result': game_result.get('result', 'draw'),
                'total_moves': game_result.get('move_count', 0),
                'game_duration': 0.0,  # 训练游戏不计时
                'pgn': self._generate_simple_pgn(game_result),
                'final_position': game_result.get('final_position', '')
            }
            
            # 保存游戏
            game_id = self.database.save_game(game_data)
            
            # 保存移动数据
            moves = game_result.get('moves', [])
            for i, move_data in enumerate(moves):
                # 🆕 修复move元组类型转换问题
                move_tuple = move_data.get('move', ('', ''))
                from_square = str(move_tuple[0]) if len(move_tuple) > 0 else ''
                to_square = str(move_tuple[1]) if len(move_tuple) > 1 else ''
                
                move_record = {
                    'move_number': i + 1,
                    'player_color': move_data.get('player', 'white'),
                    'from_square': from_square,
                    'to_square': to_square,
                    'piece_type': move_data.get('piece_type', ''),
                    'captured_piece': move_data.get('captured_piece'),
                    'special_move': move_data.get('special_move'),
                    'notation': move_data.get('notation', ''),
                    'evaluation': move_data.get('evaluation', 0.0),
                    'think_time': move_data.get('think_time', 0.0),
                    'position_after': move_data.get('board_state', '')
                }
                self.database.save_move(game_id, move_record)
            
            return game_id
            
        except Exception as e:
            print(f"⚠️ 保存游戏到数据库失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_simple_pgn(self, game_result: Dict) -> str:
        """生成简单的PGN格式字符串"""
        try:
            moves = game_result.get('moves', [])
            if not moves:
                return "[Training Game - No moves recorded]"
            
            pgn_moves = []
            for i, move_data in enumerate(moves):
                if i % 2 == 0:  # 白棋移动
                    move_num = (i // 2) + 1
                    pgn_moves.append(f"{move_num}.")
                
                move_notation = move_data.get('notation', f"{move_data.get('move', ['?', '?'])[0]}-{move_data.get('move', ['?', '?'])[1]}")
                pgn_moves.append(move_notation)
            
            # 添加结果
            result = game_result.get('result', 'draw')
            if result == 'white':
                pgn_moves.append("1-0")
            elif result == 'black':
                pgn_moves.append("0-1")
            else:
                pgn_moves.append("1/2-1/2")
            
            return " ".join(pgn_moves)
        except Exception as e:
            return f"[Training Game - PGN generation error: {str(e)}]"

    def _format_duration(self, seconds: float) -> str:
        """格式化时间长度"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{td.days}天 {hours:02d}:{minutes:02d}:{seconds:02d}"

def main():
    """主函数"""
    print("🚀 现代化国际象棋AI训练系统")
    print("=" * 60)
    
    # 路径设置
    current_dir = os.path.dirname(os.path.abspath(__file__))
    chess_dir = os.path.dirname(current_dir)
    
    training_dir = current_dir  # 使用当前training目录
    
    # 确保目录存在
    os.makedirs(os.path.join(training_dir, "models"), exist_ok=True)
    
    print(f"📁 训练目录: {training_dir}")
    print(f"📁 模型目录: {os.path.join(training_dir, 'models')}")
    print("🗄️ 数据库: 将使用统一数据库路径")
    
    # 创建训练器
    try:
        trainer = ModernChessTrainer(
            training_data_dir=training_dir,
            use_modern_architecture=True  # 默认使用现代架构
        )
        
        # 训练菜单
        print("\n🎯 选择训练模式:")
        print("1. 快速验证 (20局) - 现代架构")
        print("2. 标准训练 (100局) - 现代架构")
        print("3. 深度训练 (500局) - 现代架构")
        print("4. 传统训练 (100局) - 传统架构")
        print("5. 自定义训练")
        
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == '1':
            trainer.run_training(num_games=20, training_mode='quick')
        elif choice == '2':
            trainer.run_training(num_games=100, training_mode='standard')
        elif choice == '3':
            trainer.run_training(num_games=500, training_mode='deep')
        elif choice == '4':
            # 重新创建使用传统架构的训练器
            trainer = ModernChessTrainer(
                training_data_dir=training_dir,
                use_modern_architecture=False
            )
            trainer.run_training(num_games=100, training_mode='traditional')
        elif choice == '5':
            num_games = int(input("请输入游戏局数: "))
            use_modern = input("使用现代架构? (y/n): ").strip().lower() == 'y'
            
            if not use_modern:
                trainer = ModernChessTrainer(
                    training_data_dir=training_dir,
                    use_modern_architecture=False
                )
            
            trainer.run_training(num_games=num_games, training_mode='custom')
        else:
            print("❌ 无效选择")
    
    except KeyboardInterrupt:
        print("\n\n🛑 训练被用户中断")
        if 'trainer' in locals():
            print("💾 正在保存训练进度...")
            try:
                trainer._save_final_model()
                trainer._save_training_stats()
                print("✅ 训练进度已保存")
            except Exception as e:
                print(f"⚠️ 保存失败: {e}")
    except Exception as e:
        print(f"\n❌ 训练出错: {e}")
        traceback.print_exc()
        if 'trainer' in locals():
            print("💾 尝试保存当前进度...")
            try:
                trainer._save_final_model()
                trainer._save_training_stats()
                print("✅ 当前进度已保存")
            except Exception as save_e:
                print(f"⚠️ 保存失败: {save_e}")

if __name__ == "__main__":
    main()
