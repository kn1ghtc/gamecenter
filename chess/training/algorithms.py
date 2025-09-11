"""
国际象棋AI训练算法集合
集成了AlphaZero架构、MCTS、残差网络等现代化算法
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import random
from typing import List, Dict, Tuple, Optional
from collections import deque
import copy
import sys
import os

# 添加路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入游戏相关类
from game.pieces import PieceColor

# ============================================================================
# 神经网络架构
# ============================================================================

class ResidualBlock(nn.Module):
    """残差块 - AlphaZero风格 - 稳定版本"""
    
    def __init__(self, hidden_size: int):
        super(ResidualBlock, self).__init__()
        self.linear1 = nn.Linear(hidden_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        # 使用LayerNorm替代BatchNorm以处理小批次
        self.norm1 = nn.LayerNorm(hidden_size)
        self.norm2 = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, x):
        residual = x
        x = F.relu(self.norm1(self.linear1(x)))
        x = self.dropout(x)
        x = self.norm2(self.linear2(x))
        x = x + residual  # 残差连接
        return F.relu(x)

class AttentionModule(nn.Module):
    """注意力机制模块"""
    
    def __init__(self, hidden_size: int, num_heads: int = 8):
        super(AttentionModule, self).__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        
        self.query = nn.Linear(hidden_size, hidden_size)
        self.key = nn.Linear(hidden_size, hidden_size)
        self.value = nn.Linear(hidden_size, hidden_size)
        self.output = nn.Linear(hidden_size, hidden_size)
        
    def forward(self, x):
        batch_size = x.size(0)
        
        # 多头注意力
        q = self.query(x).view(batch_size, self.num_heads, self.head_dim)
        k = self.key(x).view(batch_size, self.num_heads, self.head_dim)
        v = self.value(x).view(batch_size, self.num_heads, self.head_dim)
        
        # 计算注意力权重
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attention_weights = F.softmax(scores, dim=-1)
        
        # 应用注意力
        attended = torch.matmul(attention_weights, v)
        attended = attended.view(batch_size, self.hidden_size)
        
        return self.output(attended)

class ModernChessNetwork(nn.Module):
    """现代象棋神经网络 - 基于AlphaZero架构 - 稳定版本"""
    
    def __init__(self, 
                 input_channels: int = 20, 
                 board_size: int = 8,
                 filters: int = 256,
                 residual_blocks: int = 12,
                 value_head_hidden: int = 256):
        super(ModernChessNetwork, self).__init__()
        
        self.board_size = board_size
        self.input_size = input_channels * board_size * board_size
        
        # 输入处理 - 使用LayerNorm
        self.input_layer = nn.Linear(self.input_size, filters)
        self.input_norm = nn.LayerNorm(filters)
        
        # 残差塔
        self.residual_tower = nn.ModuleList([
            ResidualBlock(filters) for _ in range(residual_blocks)
        ])
        
        # 注意力机制
        self.attention = AttentionModule(filters, num_heads=8)
        
        # 策略头（移动概率） - 使用LayerNorm
        self.policy_head = nn.Sequential(
            nn.Linear(filters, filters),
            nn.ReLU(),
            nn.LayerNorm(filters),
            nn.Linear(filters, 4096),  # 64x64 可能移动
            nn.Dropout(0.3)
        )
        
        # 价值头（位置评估） - 使用LayerNorm
        self.value_head = nn.Sequential(
            nn.Linear(filters, value_head_hidden),
            nn.ReLU(),
            nn.LayerNorm(value_head_hidden),
            nn.Dropout(0.3),
            nn.Linear(value_head_hidden, 1),
            nn.Tanh()
        )
        
        # 辅助头（游戏阶段预测）
        self.auxiliary_head = nn.Sequential(
            nn.Linear(filters, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
        # 初始化权重
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Xavier初始化"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
    
    def forward(self, x):
        batch_size = x.size(0)
        
        # 重塑输入
        if len(x.shape) == 4:  # (batch, channels, height, width)
            x = x.view(batch_size, -1)
        
        # 输入处理
        x = F.relu(self.input_norm(self.input_layer(x)))
        
        # 残差塔
        for residual_block in self.residual_tower:
            x = residual_block(x)
        
        # 注意力增强
        x = x + self.attention(x)
        
        # 三个输出头
        policy = self.policy_head(x)
        value = self.value_head(x)
        auxiliary = self.auxiliary_head(x)
        
        return policy, value, auxiliary

# ============================================================================
# 蒙特卡洛树搜索 (MCTS)
# ============================================================================

class MCTSNode:
    """MCTS节点"""
    
    def __init__(self, move=None, parent=None, prior_probability=0.0):
        self.move = move
        self.parent = parent
        self.children = {}
        
        # 统计信息
        self.visits = 0
        self.total_value = 0.0
        self.prior_probability = prior_probability
        
        # 虚拟损失（用于并行搜索）
        self.virtual_loss = 0
    
    def is_leaf(self):
        return len(self.children) == 0
    
    def is_root(self):
        return self.parent is None
    
    def get_value(self):
        if self.visits == 0:
            return 0
        return self.total_value / self.visits
    
    def get_ucb_score(self, c_puct=1.0):
        """计算UCB1分数"""
        if self.visits == 0:
            return float('inf')
        
        # UCB1公式：Q(s,a) + c_puct * P(s,a) * sqrt(N(s)) / (1 + N(s,a))
        exploration_factor = c_puct * self.prior_probability * math.sqrt(max(1, self.parent.visits))
        exploration_bonus = exploration_factor * math.sqrt(max(1, math.log(max(1, self.parent.visits))) / max(1, self.visits))
        
        return self.get_value() + exploration_bonus
    
    def select_child(self, c_puct=1.0):
        """选择最佳子节点"""
        return max(self.children.values(), key=lambda child: child.get_ucb_score(c_puct))
    
    def expand(self, move_priors):
        """扩展节点"""
        for move, prior in move_priors:
            self.children[move] = MCTSNode(move=move, parent=self, prior_probability=prior)
    
    def backup(self, value):
        """回传价值"""
        self.visits += 1
        self.total_value += value
        if self.parent:
            self.parent.backup(-value)  # 对手视角，取负值

class AdvancedMCTS:
    """高级蒙特卡洛树搜索"""
    
    def __init__(self, 
                 neural_network,
                 c_puct: float = 1.0,
                 num_simulations: int = 800,
                 temperature: float = 1.0,
                 device: str = 'cpu'):
        self.neural_network = neural_network
        self.c_puct = c_puct
        self.num_simulations = num_simulations
        self.temperature = temperature
        self.device = device
        
    def search(self, board, root_node=None):
        """执行MCTS搜索"""
        if root_node is None:
            root_node = MCTSNode()
        
        for _ in range(self.num_simulations):
            self._simulate(board, root_node)
        
        return root_node
    
    def _simulate(self, board, node):
        """单次模拟"""
        path = []
        current_node = node
        current_board = copy.deepcopy(board)
        
        # 选择阶段
        while not current_node.is_leaf():
            action = current_node.select_child(self.c_puct)
            path.append((current_node, action))
            current_node = action
            
            # 在棋盘上执行移动
            from_pos, to_pos = action.move
            current_board.make_move(from_pos, to_pos)
        
        # 扩展和评估阶段
        if not current_board.is_game_over():
            legal_moves = self._get_legal_moves(current_board)
            if legal_moves:
                # 使用神经网络获取策略和价值
                policy, value = self._evaluate_position(current_board)
                
                # 扩展节点
                move_priors = [(move, policy.get(move, 0.01)) for move in legal_moves]
                current_node.expand(move_priors)
                
                # 使用神经网络的价值评估
                leaf_value = float(value)
            else:
                leaf_value = 0.0
        else:
            # 终端节点评估
            if current_board.is_checkmate():
                leaf_value = -1.0  # 对当前玩家不利
            else:
                leaf_value = 0.0   # 和棋
        
        # 回传阶段
        for node, action in reversed(path):
            leaf_value = -leaf_value  # 交替视角
        current_node.backup(leaf_value)
    
    def _get_legal_moves(self, board):
        """获取合法移动"""
        legal_moves = []
        current_player = board.current_player
        
        for position, piece in board.pieces.items():
            if piece.color == current_player:
                moves = board.get_legal_moves(position)
                for to_pos in moves:
                    legal_moves.append((position, to_pos))
        
        return legal_moves
    
    def _evaluate_position(self, board):
        """使用神经网络评估位置"""
        # 编码棋盘状态
        board_tensor = self._encode_board(board)
        
        with torch.no_grad():
            self.neural_network.eval()
            policy_logits, value, _ = self.neural_network(board_tensor)
            
            # 转换为概率分布
            policy_probs = F.softmax(policy_logits, dim=-1)
            
            # 构建移动到概率的映射
            policy_dict = {}
            legal_moves = self._get_legal_moves(board)
            
            for i, move in enumerate(legal_moves):
                if i < len(policy_probs[0]):
                    policy_dict[move] = float(policy_probs[0][i])
        
        return policy_dict, float(value[0])
    
    def _encode_board(self, board):
        """编码棋盘状态为神经网络输入"""
        # 简化版本，实际应该使用更完整的编码
        encoding = ChessBoardEncoder().encode(board)
        return torch.FloatTensor(encoding).unsqueeze(0).to(self.device)
    
    def get_action_probabilities(self, root_node, temperature=1.0):
        """获取动作概率分布"""
        if not root_node.children:
            return {}
        
        visits = np.array([child.visits for child in root_node.children.values()])
        
        if temperature == 0:
            # 贪婪选择
            action_probs = np.zeros_like(visits)
            action_probs[np.argmax(visits)] = 1.0
        else:
            # 温度采样
            visits_temp = visits ** (1.0 / temperature)
            action_probs = visits_temp / visits_temp.sum()
        
        return {move: prob for move, prob in zip(root_node.children.keys(), action_probs)}

# ============================================================================
# 棋盘编码器
# ============================================================================

class ChessBoardEncoder:
    """象棋棋盘编码器 - 20通道编码"""
    
    def __init__(self):
        self.channels = 20
        self.board_size = 8
    
    def encode(self, board):
        """编码棋盘状态"""
        encoding = np.zeros((self.channels, self.board_size, self.board_size), dtype=np.float32)
        
        # 获取当前玩家
        current_player = board.current_player
        
        # 基础编码（12个通道：6种棋子 x 2种颜色）
        piece_channels = {
            'Pawn': 0, 'Rook': 1, 'Knight': 2, 
            'Bishop': 3, 'Queen': 4, 'King': 5
        }
        
        for position, piece in board.pieces.items():
            row, col = position
            piece_type = piece.__class__.__name__
            
            if piece_type in piece_channels:
                channel_base = piece_channels[piece_type]
                
                # 当前玩家的棋子
                if piece.color == current_player:
                    encoding[channel_base, row, col] = 1.0
                # 对手的棋子
                else:
                    encoding[channel_base + 6, row, col] = 1.0
        
        # 攻击和防守信息（2个通道）
        encoding[12] = self._encode_attacks(board, current_player)
        opponent_color = PieceColor.BLACK if current_player == PieceColor.WHITE else PieceColor.WHITE
        encoding[13] = self._encode_attacks(board, opponent_color)
        
        # 移动历史和特殊状态（6个通道）
        encoding[14] = self._encode_castling_rights(board)
        encoding[15] = self._encode_en_passant(board)
        encoding[16] = self._encode_move_count(board)
        encoding[17] = self._encode_check_status(board)
        encoding[18] = self._encode_game_phase(board)
        encoding[19] = np.ones((8, 8)) if current_player.name == 'WHITE' else np.zeros((8, 8))
        
        return encoding
    
    def _encode_attacks(self, board, color):
        """编码攻击信息"""
        attack_map = np.zeros((8, 8), dtype=np.float32)
        
        for position, piece in board.pieces.items():
            if piece.color == color:
                legal_moves = board.get_legal_moves(position)
                for to_pos in legal_moves:
                    row, col = to_pos
                    attack_map[row, col] = 1.0
        
        return attack_map
    
    def _encode_castling_rights(self, board):
        """编码王车易位权利"""
        # 简化实现
        return np.zeros((8, 8), dtype=np.float32)
    
    def _encode_en_passant(self, board):
        """编码过路兵"""
        # 简化实现
        return np.zeros((8, 8), dtype=np.float32)
    
    def _encode_move_count(self, board):
        """编码移动计数"""
        # 简化实现
        return np.zeros((8, 8), dtype=np.float32)
    
    def _encode_check_status(self, board):
        """编码将军状态"""
        check_map = np.zeros((8, 8), dtype=np.float32)
        current_player = board.current_player
        
        try:
            if hasattr(board, 'is_in_check') and board.is_in_check(current_player):
                # 标记国王位置
                for position, piece in board.pieces.items():
                    if piece.__class__.__name__ == 'King' and piece.color == current_player:
                        row, col = position
                        check_map[row, col] = 1.0
        except:
            # 如果检查失败，返回零矩阵
            pass
        
        return check_map
    
    def _encode_game_phase(self, board):
        """编码游戏阶段"""
        # 根据剩余棋子数量判断游戏阶段
        piece_count = len(board.pieces)
        if piece_count > 24:
            phase_value = 1.0  # 开局
        elif piece_count > 12:
            phase_value = 0.5  # 中局
        else:
            phase_value = 0.0  # 残局
        
        return np.full((8, 8), phase_value, dtype=np.float32)

# ============================================================================
# 高级训练策略
# ============================================================================

class AdvancedTrainingStrategy:
    """高级训练策略集合"""
    
    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.experience_buffer = deque(maxlen=100000)
        self.priorities = deque(maxlen=100000)
        
    def priority_experience_replay(self, batch_size: int):
        """优先经验回放"""
        if len(self.experience_buffer) < batch_size:
            return None
        
        # 计算采样概率（基于TD误差优先级）
        priorities = np.array(self.priorities) + 1e-6  # 避免零概率
        priorities = priorities.flatten()  # 确保是一维数组
        probabilities = priorities / priorities.sum()
        
        # 采样索引
        indices = np.random.choice(len(self.experience_buffer), batch_size, p=probabilities)
        
        # 返回采样的经验
        batch = [self.experience_buffer[i] for i in indices]
        return batch
    
    def curriculum_learning_update(self, current_win_rate: float):
        """课程学习更新"""
        # 根据当前胜率调整训练参数
        if current_win_rate < 30:
            # 胜率低，增加探索
            return {'epsilon': 0.3, 'temperature': 1.5}
        elif current_win_rate > 70:
            # 胜率高，减少探索
            return {'epsilon': 0.1, 'temperature': 0.8}
        else:
            # 平衡状态
            return {'epsilon': 0.2, 'temperature': 1.0}
    
    def adaptive_opponent_selection(self, training_history):
        """自适应对手选择"""
        # 根据训练历史选择合适的对手
        recent_performance = training_history[-20:] if len(training_history) >= 20 else training_history
        
        if not recent_performance:
            return 'basic'
        
        avg_performance = np.mean([game['ml_ai_result'] == 'win' for game in recent_performance])
        
        if avg_performance < 0.3:
            return 'easy'
        elif avg_performance > 0.7:
            return 'hard' 
        else:
            return 'medium'

# ============================================================================
# 自适应学习率调度器
# ============================================================================

class AdaptiveLearningRate:
    """自适应学习率调度器"""
    
    def __init__(self, initial_lr=0.001, patience=10, factor=0.5, min_lr=1e-6):
        self.initial_lr = initial_lr
        self.patience = patience
        self.factor = factor
        self.min_lr = min_lr
        
        self.best_loss = float('inf')
        self.wait = 0
        self.current_lr = initial_lr
    
    def update(self, current_loss, current_win_rate, optimizer):
        """更新学习率"""
        # 综合考虑损失和胜率
        performance_metric = current_loss - (current_win_rate / 100.0) * 0.1
        
        if performance_metric < self.best_loss:
            self.best_loss = performance_metric
            self.wait = 0
        else:
            self.wait += 1
            
            if self.wait >= self.patience:
                # 降低学习率
                self.current_lr = max(self.current_lr * self.factor, self.min_lr)
                
                # 更新优化器学习率
                for param_group in optimizer.param_groups:
                    param_group['lr'] = self.current_lr
                
                self.wait = 0
                print(f"📉 学习率调整为: {self.current_lr:.6f}")
        
        return self.current_lr

# ============================================================================
# 经验回放缓冲区
# ============================================================================

class ExperienceReplayBuffer:
    """经验回放缓冲区"""
    
    def __init__(self, capacity=100000):
        self.buffer = deque(maxlen=capacity)
        self.priorities = deque(maxlen=capacity)
        
    def add(self, experience, priority=1.0):
        """添加经验"""
        self.buffer.append(experience)
        self.priorities.append(priority)
    
    def sample(self, batch_size, alpha=0.6):
        """优先采样"""
        if len(self.buffer) < batch_size:
            return random.sample(list(self.buffer), len(self.buffer))
        
        # 计算采样概率
        priorities = np.array(self.priorities) ** alpha
        priorities = priorities.flatten()  # 确保是一维数组
        probabilities = priorities / priorities.sum()
        
        # 采样
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        
        return [self.buffer[i] for i in indices]
    
    def clear_old_data(self, keep_ratio=0.8):
        """清理旧数据"""
        keep_size = int(len(self.buffer) * keep_ratio)
        if keep_size < len(self.buffer):
            # 保留最新的数据
            self.buffer = deque(list(self.buffer)[-keep_size:], maxlen=self.buffer.maxlen)
            self.priorities = deque(list(self.priorities)[-keep_size:], maxlen=self.priorities.maxlen)
    
    def __len__(self):
        return len(self.buffer)

# ============================================================================
# 导出主要类
# ============================================================================

__all__ = [
    'ModernChessNetwork',
    'AdvancedMCTS', 
    'ChessBoardEncoder',
    'AdvancedTrainingStrategy',
    'AdaptiveLearningRate',
    'ExperienceReplayBuffer',
    'MCTSNode'
]
