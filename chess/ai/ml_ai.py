"""
机器学习AI实现
使用神经网络和强化学习的中等难度AI
"""
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
import sys
import os
from collections import deque
from typing import List, Tuple, Optional, Dict
import pickle

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.board import ChessBoard
from game.pieces import PieceColor, PieceType
from ai.evaluation import ChessEvaluator

class ChessNeuralNetwork(nn.Module):
    """国际象棋神经网络模型"""
    
    def __init__(self, input_size=773, hidden_size=512, output_size=1):
        super(ChessNeuralNetwork, self).__init__()
        
        # 位置评估网络
        self.position_net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, output_size),
            nn.Tanh()  # 输出范围 [-1, 1]
        )
        
        # 移动价值网络（用于移动排序）
        self.move_value_net = nn.Sequential(
            nn.Linear(input_size + 64, hidden_size // 2),  # +64 for target square one-hot
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()  # 输出范围 [0, 1]
        )
    
    def forward(self, position_features, move_features=None):
        """前向传播"""
        position_value = self.position_net(position_features)
        
        if move_features is not None:
            # 连接位置特征和移动特征
            combined_features = torch.cat([position_features, move_features], dim=-1)
            move_value = self.move_value_net(combined_features)
            return position_value, move_value
        
        return position_value

class PositionEncoder:
    """棋盘位置编码器"""
    
    def __init__(self):
        # 特征维度计算：
        # 8x8x12 = 768 (每个格子的棋子类型，12种棋子类型)
        # + 5 (游戏状态：当前玩家、王车易位权利等)
        self.feature_size = 773
    
    def encode_position(self, board: ChessBoard) -> np.ndarray:
        """编码棋盘位置为特征向量"""
        features = np.zeros(self.feature_size, dtype=np.float32)
        
        # 编码棋盘状态 (768维)
        piece_map = {
            (PieceColor.WHITE, PieceType.PAWN): 0,
            (PieceColor.WHITE, PieceType.KNIGHT): 1,
            (PieceColor.WHITE, PieceType.BISHOP): 2,
            (PieceColor.WHITE, PieceType.ROOK): 3,
            (PieceColor.WHITE, PieceType.QUEEN): 4,
            (PieceColor.WHITE, PieceType.KING): 5,
            (PieceColor.BLACK, PieceType.PAWN): 6,
            (PieceColor.BLACK, PieceType.KNIGHT): 7,
            (PieceColor.BLACK, PieceType.BISHOP): 8,
            (PieceColor.BLACK, PieceType.ROOK): 9,
            (PieceColor.BLACK, PieceType.QUEEN): 10,
            (PieceColor.BLACK, PieceType.KING): 11,
        }
        
        for position, piece in board.pieces.items():
            x, y = position
            piece_index = piece_map[(piece.color, piece.piece_type)]
            feature_index = y * 8 * 12 + x * 12 + piece_index
            features[feature_index] = 1.0
        
        # 游戏状态特征 (5维)
        feature_offset = 768
        
        # 当前玩家
        features[feature_offset] = 1.0 if board.current_player == PieceColor.WHITE else -1.0
        
        # 王车易位权利 (简化版本)
        features[feature_offset + 1] = 1.0 if board.board.has_kingside_castling_rights(True) else 0.0
        features[feature_offset + 2] = 1.0 if board.board.has_queenside_castling_rights(True) else 0.0
        features[feature_offset + 3] = 1.0 if board.board.has_kingside_castling_rights(False) else 0.0
        features[feature_offset + 4] = 1.0 if board.board.has_queenside_castling_rights(False) else 0.0
        
        return features
    
    def encode_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> np.ndarray:
        """编码移动为特征向量"""
        # 目标格子的one-hot编码
        move_features = np.zeros(64, dtype=np.float32)
        x, y = to_pos
        square_index = y * 8 + x
        move_features[square_index] = 1.0
        
        return move_features

class ChessMLAI:
    """机器学习国际象棋AI"""
    
    def __init__(self, model_path: str = None, device: str = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")
        
        self.encoder = PositionEncoder()
        self.model = ChessNeuralNetwork().to(self.device)
        self.traditional_evaluator = ChessEvaluator()
        
        # 优化训练参数以提升胜率
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0001, weight_decay=1e-5)  # 降低学习率，增加正则化
        self.criterion = nn.MSELoss()
        
        # 扩大经验回放缓冲区
        self.replay_buffer = deque(maxlen=50000)
        
        # 修正模型路径加载逻辑
        if model_path:
            self.load_model(model_path)
        else:
            # 尝试加载默认模型
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            default_model_path = os.path.join(parent_dir, "training", "models", "ml_ai_model.pth")
            
            if os.path.exists(default_model_path):
                self.load_model(default_model_path)
            else:
                print("未找到预训练模型，使用随机初始化的模型")
        
        # 优化探索参数 - 更激进的学习策略
        self.epsilon = 0.3  # 提高初始探索率
        self.exploration_decay = 0.998  # 更慢的衰减
        self.min_epsilon = 0.05  # 保持一定的探索
    
    def get_best_move(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """获取最佳移动"""
        legal_moves = self._get_all_legal_moves(board, color)
        if not legal_moves:
            return None
        
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # 使用神经网络评估移动
        best_move = None
        best_score = float('-inf') if color == PieceColor.WHITE else float('inf')
        
        position_features = self.encoder.encode_position(board)
        position_tensor = torch.FloatTensor(position_features).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            for move in legal_moves:
                from_pos, to_pos = move
                
                # 评估移动后的位置
                board_copy = self._make_move_copy(board, from_pos, to_pos)
                move_features = self.encoder.encode_move(from_pos, to_pos)
                move_tensor = torch.FloatTensor(move_features).unsqueeze(0).to(self.device)
                
                # 获取位置评估和移动价值
                position_value, move_value = self.model(position_tensor, move_tensor)
                
                # 结合传统评估
                traditional_eval = self.traditional_evaluator.evaluate_position(board_copy)
                
                # 混合评估（70% 神经网络，30% 传统评估）
                combined_score = 0.7 * position_value.item() * 1000 + 0.3 * traditional_eval
                combined_score += move_value.item() * 100  # 移动价值加成
                
                # 添加随机探索
                if random.random() < self.epsilon:
                    combined_score += random.uniform(-50, 50)
                
                if color == PieceColor.WHITE:
                    if combined_score > best_score:
                        best_score = combined_score
                        best_move = move
                else:
                    if combined_score < best_score:
                        best_score = combined_score
                        best_move = move
        
        # 更新探索参数
        self.epsilon = max(self.min_epsilon, self.epsilon * self.exploration_decay)
        
        return best_move or random.choice(legal_moves)
    
    def _get_all_legal_moves(self, board: ChessBoard, color: PieceColor) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """获取所有合法移动"""
        legal_moves = []
        
        for position, piece in board.pieces.items():
            if piece.color == color:
                moves = board.get_legal_moves(position)
                for to_pos in moves:
                    legal_moves.append((position, to_pos))
        
        return legal_moves
    
    def _make_move_copy(self, board: ChessBoard, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> ChessBoard:
        """创建移动后的棋盘副本"""
        import copy
        board_copy = copy.deepcopy(board)
        board_copy.make_move(from_pos, to_pos)
        return board_copy
    
    def train_on_game(self, game_moves: List[Dict], game_result: str):
        """基于游戏记录进行训练"""
        if len(game_moves) < 5:  # 游戏太短，跳过
            return
        
        training_data = []
        
        for i, move_data in enumerate(game_moves):
            if 'board_state' not in move_data:
                continue
            
            board_state = move_data['board_state']
            board = self._reconstruct_board_from_state(board_state)
            
            if board is None:
                continue
            
            # 计算目标值（基于游戏结果和位置）
            target_value = self._calculate_target_value(game_result, i, len(game_moves), board)
            
            # 编码位置
            position_features = self.encoder.encode_position(board)
            
            training_data.append((position_features, target_value))
        
        if training_data:
            self._train_batch(training_data)
    
    def _calculate_target_value(self, game_result: str, move_index: int, total_moves: int, board: ChessBoard) -> float:
        """计算训练目标值"""
        # 基于游戏结果
        if game_result == 'white':
            result_value = 1.0
        elif game_result == 'black':
            result_value = -1.0
        else:  # draw
            result_value = 0.0
        
        # 考虑移动的时间衰减
        time_factor = (total_moves - move_index) / total_moves
        
        # 结合传统评估
        traditional_eval = self.traditional_evaluator.evaluate_position(board)
        normalized_eval = np.tanh(traditional_eval / 1000.0)  # 归一化到 [-1, 1]
        
        # 混合目标值
        target = 0.6 * result_value * time_factor + 0.4 * normalized_eval
        
        return float(target)
    
    def _reconstruct_board_from_state(self, board_state: Dict) -> Optional[ChessBoard]:
        """从状态字典重建棋盘"""
        try:
            # 这里需要根据实际的board_state格式来实现
            # 简化版本：返回None，需要完整实现
            return None
        except Exception as e:
            print(f"重建棋盘失败: {e}")
            return None
    
    def _train_batch(self, training_data: List[Tuple[np.ndarray, float]]):
        """批量训练"""
        if len(training_data) < 4:  # 批次太小
            return
        
        # 添加到经验回放缓冲区
        for data in training_data:
            self.replay_buffer.append(data)
        
        # 从缓冲区采样训练
        if len(self.replay_buffer) >= 32:
            batch_size = min(32, len(self.replay_buffer))
            batch = random.sample(list(self.replay_buffer), batch_size)
            
            positions = torch.FloatTensor([item[0] for item in batch]).to(self.device)
            targets = torch.FloatTensor([item[1] for item in batch]).to(self.device)
            
            # 前向传播
            predictions = self.model(positions)
            loss = self.criterion(predictions.squeeze(), targets)
            
            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            if random.random() < 0.1:  # 10%的概率打印损失
                print(f"训练损失: {loss.item():.4f}")
    
    def save_model(self, path: str):
        """保存模型"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'replay_buffer': list(self.replay_buffer)
        }
        
        torch.save(checkpoint, path)
        print(f"模型已保存到: {path}")
    
    def load_model(self, path: str):
        """加载模型"""
        try:
            checkpoint = torch.load(path, map_location=self.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            
            if 'epsilon' in checkpoint:
                self.epsilon = checkpoint['epsilon']
            
            if 'replay_buffer' in checkpoint:
                self.replay_buffer = deque(checkpoint['replay_buffer'], maxlen=10000)
            
            print(f"模型已从 {path} 加载")
            
        except Exception as e:
            print(f"加载模型失败: {e}")
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'device': self.device,
            'model_parameters': sum(p.numel() for p in self.model.parameters()),
            'trainable_parameters': sum(p.numel() for p in self.model.parameters() if p.requires_grad),
            'epsilon': self.epsilon,
            'replay_buffer_size': len(self.replay_buffer)
        }
