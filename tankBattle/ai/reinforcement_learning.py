"""
强化学习框架
===========
基于PyTorch的深度Q网络(DQN)实现，用于坦克AI决策学习

功能：
- DQN神经网络
- 经验回放机制
- 目标网络软更新
- 状态特征提取
- 动作执行接口
"""

import math
import os
import random
import numpy as np
from collections import deque, namedtuple
from typing import Tuple, List, Dict, Optional, Any

# 条件导入 - 支持无PyTorch环境
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from torch.cuda.amp import autocast
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False

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
        
        def __iter__(self):
            return iter(self.iterable)
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
        
        def update(self, n=1):
            self.n += n
            if self.n % 100 == 0:
                print(f"\r{self.desc}: {self.n}/{self.total if self.total else '?'}", end="", flush=True)
        
        def set_postfix(self, **kwargs):
            if self.n % 50 == 0:
                status = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
                print(f" ({status})", end="", flush=True)
    print("PyTorch未安装，强化学习功能将不可用")

# 经验元组
Experience = namedtuple('Experience', 
                       ['state', 'action', 'reward', 'next_state', 'done'])

class TankDQN(nn.Module):
    """深度Q网络用于坦克AI决策 - 增强版本"""
    
    def __init__(self, state_size: int = 128, action_size: int = 8, 
                 hidden_sizes: List[int] = None):
        super(TankDQN, self).__init__()
        
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch未安装，无法创建DQN网络")
        
        if hidden_sizes is None:
            hidden_sizes = [512, 256, 128]  # 更大的默认网络

        layers = []
        prev_size = state_size

        # 构建隐藏层 - 使用LayerNorm避免小批量不稳定
        for i, hidden_size in enumerate(hidden_sizes):
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.LayerNorm(hidden_size),
                nn.ReLU(inplace=True),
                nn.Dropout(0.1 if i < len(hidden_sizes) - 1 else 0.2)  # 渐进式dropout
            ])
            prev_size = hidden_size

        # 输出层 - 添加最终的线性层
        layers.extend([
            nn.Linear(prev_size, action_size)
        ])

        self.network = nn.Sequential(*layers)
        
        # 权重初始化 - 使用Xavier初始化
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """初始化网络权重"""
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            module.bias.data.fill_(0.01)
    
    def forward(self, x):
        return self.network(x)

class TankRLAgent:
    """强化学习坦克AI智能体"""
    
    def __init__(self, state_size: int = 128, action_size: int = 8, 
                 lr: float = 1e-4, device: str = None, auto_load_model: bool = True,
                 mixed_precision: bool = False, double_dqn: bool = True, huber_delta: float = 1.0,
                 batch_size: int = 64, memory_size: int = 100000,
                 epsilon_start: float = None, epsilon_end: float = None, epsilon_decay: float = None,
                 target_update_frequency: int = 200, compile_models: bool = True):
        
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch未安装，无法创建强化学习智能体")
        
        # 设备配置 - 优先使用GPU
        if device is None:
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                print(f"✅ 使用GPU训练: {torch.cuda.get_device_name(0)}")
                print(f"📊 GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
            else:
                self.device = torch.device("cpu")
                print("⚠️ 使用CPU训练 (建议安装CUDA以获得更好性能)")
        else:
            self.device = torch.device(device)
        
        self.state_size = state_size
        self.action_size = action_size

        # 神经网络 - 使用更大的网络结构（先不编译，加载权重后再编译）
        self.q_network = TankDQN(state_size, action_size, hidden_sizes=[512, 256, 128]).to(self.device)
        self.target_network = TankDQN(state_size, action_size, hidden_sizes=[512, 256, 128]).to(self.device)
        self._compiled = False
        self._compile_enabled = compile_models

        # 优化器 - 使用AdamW提高稳定性
        self.optimizer = optim.AdamW(
            self.q_network.parameters(),
            lr=lr,
            weight_decay=1e-4,
            amsgrad=True
        )

        # 学习率调度器 - 更长的周期
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=10000, eta_min=1e-6
        )

        # AMP与训练选项
        self.use_amp = mixed_precision and (str(self.device) == 'cuda')
        try:
            # New API: torch.amp.GradScaler('cuda', ...)
            self.scaler = torch.amp.GradScaler('cuda', enabled=self.use_amp) if hasattr(torch, 'amp') else None
        except Exception:
            # Fallback for older versions
            from torch.cuda.amp import GradScaler as CudaGradScaler
            self.scaler = CudaGradScaler(enabled=self.use_amp)

        # 算法选项
        self.double_dqn = double_dqn
        self.huber_delta = huber_delta

        # 将目标网络初始化为与主网络相同的权重
        self.update_target_network()

        # 经验回放 - 更大的经验池
        self.memory = deque(maxlen=memory_size)
        self.batch_size = batch_size  # 可配置批次大小

        # 超参数 - 优化为最佳训练效果
        self.epsilon = 1.0 if epsilon_start is None else float(epsilon_start)
        self.epsilon_min = 0.01 if epsilon_end is None else float(epsilon_end)
        self.epsilon_decay = 0.9995 if epsilon_decay is None else float(epsilon_decay)
        self.gamma = 0.99       # 更高的折扣因子
        self.tau = 5e-3         # 软更新参数略大，加速收敛
        self.target_update_frequency = int(target_update_frequency or 200)

        # 动作映射
        self.actions = [
            'move_forward', 'move_backward', 'rotate_left', 'rotate_right',
            'fire_normal', 'fire_piercing', 'fire_explosive', 'stay_still'
        ]

        # 自动加载预训练模型
        if auto_load_model:
            self._auto_load_best_model()
        # 加载后再选择性编译
        self._maybe_compile()

        # 训练统计
        self.training_step = 0
        self.losses = []
    
    def _auto_load_best_model(self):
        """自动加载最佳可用模型"""
        try:
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            if not os.path.exists(models_dir):
                print("ℹ️ 模型目录不存在，将使用随机初始化的模型")
                return

            model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth')]
            if not model_files:
                print("ℹ️ 未找到训练好的模型，将使用随机初始化的模型")
                return

            # 优先级：best_model.pth / best_model_* > final_model* > checkpoint_*
            candidates = sorted(model_files, key=lambda x: (
                3 if x == 'best_model.pth' or x.startswith('best_model_') else 2 if x.startswith('final_model') else 1 if x.startswith('checkpoint_') else 0
            ), reverse=True)

            best_model = candidates[0] if candidates else None
            if best_model:
                model_path = os.path.join(models_dir, best_model)
                try:
                    checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                    self._load_model_state_dict(self.q_network, checkpoint['q_network_state_dict'], strict=False)
                    if 'target_network_state_dict' in checkpoint:
                        self._load_model_state_dict(self.target_network, checkpoint['target_network_state_dict'], strict=False)
                    print(f"✅ 自动加载模型: {best_model} (部分兼容)")
                except Exception as load_error:
                    print(f"⚠️ 模型 {best_model} 结构不兼容或损坏，使用随机初始化: {str(load_error)[:100]}...")
            else:
                print("ℹ️ 未找到合适的模型文件，将使用随机初始化的模型")

        except Exception as e:
            print(f"⚠️ 自动加载模型失败: {str(e)[:100]}...")
            print("ℹ️ 使用随机初始化的模型")

    def _maybe_compile(self):
        """在CUDA上按需编译模型（PyTorch 2）"""
        if self._compiled:
            return
        try:
            if self._compile_enabled and hasattr(torch, 'compile') and str(self.device) == 'cuda':
                # 仅在triton可用时启用编译，避免运行期后端失败
                try:
                    import importlib.util
                    triton_ok = importlib.util.find_spec('triton') is not None
                except Exception:
                    triton_ok = False
                if not triton_ok:
                    # 无triton则跳过编译，保持eager
                    return
                self.q_network = torch.compile(self.q_network)
                self.target_network = torch.compile(self.target_network)
                self._compiled = True
        except Exception:
            pass

    @staticmethod
    def _get_model_state_dict(model):
        try:
            return model._orig_mod.state_dict()
        except AttributeError:
            return model.state_dict()

    @staticmethod
    def _load_model_state_dict(model, state_dict, strict: bool = False):
        try:
            model._orig_mod.load_state_dict(state_dict, strict=strict)
        except AttributeError:
            model.load_state_dict(state_dict, strict=strict)
        
    def get_state(self, tank, player, walls, bullets, environment) -> np.ndarray:
        """提取环境状态特征"""
        state_features = []
        
        # 获取坦克中心位置
        tank_center = self._get_tank_center(tank)
        
        # 1. 坦克自身状态 (8维)
        tank_features = self._extract_tank_features(tank, tank_center)
        state_features.extend(tank_features)
        
        # 2. 玩家状态 (6维)
        player_features = self._extract_player_features(player, tank_center)
        state_features.extend(player_features)
        
        # 3. 周围障碍物信息 (64维)
        obstacle_features = self._extract_obstacle_features(tank_center, walls)
        state_features.extend(obstacle_features)
        
        # 4. 子弹威胁评估 (16维)
        bullet_features = self._extract_bullet_features(tank_center, bullets)
        state_features.extend(bullet_features)
        
        # 5. 基地状态 (8维)
        base_features = self._extract_base_features(tank_center, environment)
        state_features.extend(base_features)
        
        # 6. 战术评估 (20维)
        tactical_features = self._extract_tactical_features(tank, player, walls, environment)
        state_features.extend(tactical_features)
        
        # 确保状态维度正确
        while len(state_features) < self.state_size:
            state_features.append(0.0)
        
        return np.array(state_features[:self.state_size], dtype=np.float32)
    
    def _get_tank_center(self, tank) -> np.ndarray:
        """获取坦克中心位置"""
        if hasattr(tank, 'rect'):
            return np.array([tank.rect.centerx, tank.rect.centery])
        else:
            return np.array([tank.x + tank.size[0]//2, tank.y + tank.size[1]//2])
    
    def _extract_tank_features(self, tank, tank_center: np.ndarray) -> List[float]:
        """提取坦克自身特征"""
        features = []
        
        # 位置信息（归一化）
        features.append(tank_center[0] / 800.0)
        features.append(tank_center[1] / 600.0)
        
        # 角度信息
        features.append(tank.angle / (2 * math.pi))
        
        # 生命值状态
        features.append(tank.health / 100.0)
        
        # 射击冷却状态
        cooldown = getattr(tank, 'fire_cooldown', 0)
        features.append(cooldown / 30.0)
        
        # AI模式
        ai_mode = getattr(tank, 'ai_mode', 'attack')
        features.append(1.0 if ai_mode == 'attack' else 0.0)
        
        # 被困状态
        stuck_timer = getattr(tank, 'stuck_timer', 0)
        features.append(stuck_timer / 60.0)
        
        # 决策计时器
        decision_timer = getattr(tank, 'decision_timer', 0)
        features.append(decision_timer / 60.0)
        
        return features
    
    def _extract_player_features(self, player, tank_center: np.ndarray) -> List[float]:
        """提取玩家特征"""
        features = []
        
        if player and player.health > 0:
            player_center = self._get_tank_center(player)
            distance = np.linalg.norm(tank_center - player_center)
            angle_to_player = math.atan2(player_center[1] - tank_center[1], 
                                       player_center[0] - tank_center[0])
            
            features.extend([
                player_center[0] / 800.0,
                player_center[1] / 600.0,
                distance / 1000.0,
                angle_to_player / (2 * math.pi),
                player.health / 100.0,
                player.angle / (2 * math.pi)
            ])
        else:
            features.extend([0.0] * 6)
        
        return features
    
    def _extract_obstacle_features(self, center: np.ndarray, walls) -> List[float]:
        """提取障碍物特征 - 8方向 × 8距离层"""
        directions = 8
        layers = 8
        features = []
        
        for d in range(directions):
            angle = d * 2 * math.pi / directions
            direction = np.array([math.cos(angle), math.sin(angle)])
            
            for layer in range(1, layers + 1):
                check_pos = center + direction * (layer * 30)
                
                # 检查边界
                if (check_pos[0] < 0 or check_pos[0] >= 800 or 
                    check_pos[1] < 0 or check_pos[1] >= 600):
                    features.append(1.0)
                    break
                
                # 检查墙体
                obstacle_found = False
                for wall in walls:
                    if hasattr(wall, 'rect') and wall.rect.collidepoint(check_pos):
                        # 根据墙体类型设置不同的值
                        if hasattr(wall, 'wall_type'):
                            if wall.wall_type == 'barrier':
                                features.append(0.8)  # 隔离墙
                            elif wall.wall_type == 'special':
                                features.append(0.6)  # 特殊墙
                            else:
                                features.append(1.0)  # 普通墙
                        else:
                            features.append(1.0)
                        obstacle_found = True
                        break
                
                if obstacle_found:
                    break
                elif layer == layers:  # 最后一层仍未发现障碍
                    features.append(0.0)
        
        # 确保特征数量正确
        while len(features) < directions * layers:
            features.append(0.0)
        
        return features[:directions * layers]
    
    def _extract_bullet_features(self, center: np.ndarray, bullets) -> List[float]:
        """提取子弹威胁特征"""
        max_bullets = 4
        features = []
        
        # 收集相关子弹
        relevant_bullets = []
        for bullet in bullets:
            if hasattr(bullet, 'owner') and bullet.owner != 'enemy':
                continue  # 只关心敌对子弹
            
            bullet_pos = self._get_bullet_center(bullet)
            distance = np.linalg.norm(center - bullet_pos)
            
            if distance < 200:  # 200像素内的子弹
                relevant_bullets.append((bullet, distance, bullet_pos))
        
        # 按距离排序
        relevant_bullets.sort(key=lambda x: x[1])
        
        # 提取特征
        for i in range(max_bullets):
            if i < len(relevant_bullets):
                bullet, distance, bullet_pos = relevant_bullets[i]
                relative_pos = bullet_pos - center
                threat_level = max(0, 1.0 - distance / 200.0)
                
                features.extend([
                    relative_pos[0] / 200.0,  # 相对X位置
                    relative_pos[1] / 200.0,  # 相对Y位置
                    threat_level,             # 威胁等级
                    getattr(bullet, 'damage', 25) / 50.0  # 伤害等级
                ])
            else:
                features.extend([0.0, 0.0, 0.0, 0.0])
        
        return features
    
    def _get_bullet_center(self, bullet) -> np.ndarray:
        """获取子弹中心位置"""
        if hasattr(bullet, 'rect'):
            return np.array([bullet.rect.centerx, bullet.rect.centery])
        else:
            return np.array([bullet.x, bullet.y])
    
    def _extract_base_features(self, center: np.ndarray, environment) -> List[float]:
        """提取基地特征"""
        features = [0.0] * 8
        
        if environment:
            # 敌方基地（AI的目标）
            if hasattr(environment, 'enemy_base') and environment.enemy_base:
                base = environment.enemy_base
                base_pos = np.array([base.rect.centerx, base.rect.centery])
                distance = np.linalg.norm(center - base_pos)
                
                features[0] = base_pos[0] / 800.0
                features[1] = base_pos[1] / 600.0
                features[2] = distance / 1000.0
                features[3] = base.health / 100.0
            
            # 玩家基地（AI需要考虑的威胁源）
            if hasattr(environment, 'player_base') and environment.player_base:
                base = environment.player_base
                base_pos = np.array([base.rect.centerx, base.rect.centery])
                distance = np.linalg.norm(center - base_pos)
                
                features[4] = base_pos[0] / 800.0
                features[5] = base_pos[1] / 600.0
                features[6] = distance / 1000.0
                features[7] = base.health / 100.0
        
        return features
    
    def _extract_tactical_features(self, tank, player, walls, environment) -> List[float]:
        """提取战术特征"""
        features = []
        tank_center = self._get_tank_center(tank)
        
        # 地形优势评估 (4维)
        cover_score = self._evaluate_cover(tank_center, walls)
        escape_routes = self._count_escape_routes(tank_center, walls)
        
        features.extend([
            cover_score,
            escape_routes / 8.0,
            self._get_height_advantage(tank_center),
            self._get_corner_penalty(tank_center)
        ])
        
        # 战术态势 (8维)
        if player and player.health > 0:
            player_center = self._get_tank_center(player)
            
            features.extend([
                self._evaluate_flanking_position(tank_center, player_center, player.angle),
                self._evaluate_crossfire_potential(tank_center, player_center, walls),
                self._evaluate_ambush_potential(tank_center, player_center, walls),
                self._evaluate_retreat_safety(tank_center, player_center, walls),
                self._evaluate_fire_line_clarity(tank_center, player_center, walls),
                float(self._is_behind_cover(tank_center, player_center, walls)),
                self._evaluate_movement_freedom(tank_center, walls),
                self._evaluate_territorial_control(tank_center, environment)
            ])
        else:
            features.extend([0.0] * 8)
        
        # 资源和时机 (8维)
        features.extend([
            getattr(tank, 'fire_cooldown', 0) / 30.0,
            float(getattr(tank, 'can_fire', lambda: True)()),
            self._evaluate_ammo_efficiency(),
            self._evaluate_health_ratio(tank, player),
            self._evaluate_time_pressure(),
            self._evaluate_map_control(tank_center, environment),
            self._evaluate_objective_priority(tank, environment),
            self._evaluate_risk_assessment(tank_center, player, walls)
        ])
        
        return features
    
    def _evaluate_cover(self, position: np.ndarray, walls) -> float:
        """评估掩体价值"""
        cover_score = 0.0
        directions = 8
        
        for i in range(directions):
            angle = i * 2 * math.pi / directions
            direction = np.array([math.cos(angle), math.sin(angle)])
            
            for distance in range(20, 100, 20):
                check_pos = position + direction * distance
                for wall in walls:
                    if hasattr(wall, 'rect') and wall.rect.collidepoint(check_pos):
                        cover_score += 1.0 / (distance / 20)
                        break
        
        return min(cover_score / directions, 1.0)
    
    def _count_escape_routes(self, position: np.ndarray, walls) -> int:
        """计算逃生路线数量"""
        escape_routes = 0
        directions = 8
        
        for i in range(directions):
            angle = i * 2 * math.pi / directions
            direction = np.array([math.cos(angle), math.sin(angle)])
            
            clear_path = True
            for distance in range(30, 120, 30):
                check_pos = position + direction * distance
                
                # 检查边界
                if (check_pos[0] < 30 or check_pos[0] >= 770 or 
                    check_pos[1] < 30 or check_pos[1] >= 570):
                    clear_path = False
                    break
                
                # 检查障碍物
                for wall in walls:
                    if hasattr(wall, 'rect') and wall.rect.collidepoint(check_pos):
                        clear_path = False
                        break
                
                if not clear_path:
                    break
            
            if clear_path:
                escape_routes += 1
        
        return escape_routes
    
    # 简化的战术评估方法（返回基础值）
    def _get_height_advantage(self, position: np.ndarray) -> float:
        return 0.5  # 中性值
    
    def _get_corner_penalty(self, position: np.ndarray) -> float:
        # 角落惩罚
        margin = 50
        penalty = 0.0
        if position[0] < margin or position[0] > 750:
            penalty += 0.3
        if position[1] < margin or position[1] > 550:
            penalty += 0.3
        return min(penalty, 1.0)
    
    def _evaluate_flanking_position(self, tank_pos: np.ndarray, player_pos: np.ndarray, player_angle: float) -> float:
        to_tank = tank_pos - player_pos
        angle_diff = abs(math.atan2(to_tank[1], to_tank[0]) - player_angle)
        return min(angle_diff / math.pi, 1.0)
    
    def _evaluate_crossfire_potential(self, tank_pos: np.ndarray, player_pos: np.ndarray, walls) -> float:
        return 0.5  # 简化实现
    
    def _evaluate_ambush_potential(self, tank_pos: np.ndarray, player_pos: np.ndarray, walls) -> float:
        return 0.5
    
    def _evaluate_retreat_safety(self, tank_pos: np.ndarray, player_pos: np.ndarray, walls) -> float:
        distance = np.linalg.norm(tank_pos - player_pos)
        return min(distance / 300.0, 1.0)
    
    def _evaluate_fire_line_clarity(self, tank_pos: np.ndarray, player_pos: np.ndarray, walls) -> float:
        return 0.7  # 简化实现
    
    def _is_behind_cover(self, tank_pos: np.ndarray, player_pos: np.ndarray, walls) -> bool:
        return False  # 简化实现
    
    def _evaluate_movement_freedom(self, position: np.ndarray, walls) -> float:
        return 0.6
    
    def _evaluate_territorial_control(self, position: np.ndarray, environment) -> float:
        return 0.5
    
    def _evaluate_ammo_efficiency(self) -> float:
        return 0.8
    
    def _evaluate_health_ratio(self, tank, player) -> float:
        if not player:
            return 1.0
        return tank.health / max(player.health, 1)
    
    def _evaluate_time_pressure(self) -> float:
        return 0.5
    
    def _evaluate_map_control(self, position: np.ndarray, environment) -> float:
        return 0.5
    
    def _evaluate_objective_priority(self, tank, environment) -> float:
        return 0.7
    
    def _evaluate_risk_assessment(self, tank_pos: np.ndarray, player, walls) -> float:
        if not player:
            return 0.0
        player_pos = self._get_tank_center(player)
        distance = np.linalg.norm(tank_pos - player_pos)
        return max(0, 1.0 - distance / 200.0)
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        """选择动作"""
        if training and random.random() <= self.epsilon:
            return random.choice(range(self.action_size))
        
        # 优化tensor创建 - 直接从numpy转换
        state_array = np.array(state, dtype=np.float32)
        state_tensor = torch.from_numpy(state_array).unsqueeze(0).to(self.device)
        
        self.q_network.eval()
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        self.q_network.train()
        
        return q_values.cpu().data.numpy().argmax()
    
    def remember(self, state, action, reward, next_state, done):
        """存储经验"""
        self.memory.append(Experience(state, action, reward, next_state, done))
    
    def replay(self):
        """经验回放训练"""
        if len(self.memory) < self.batch_size:
            return
        
        batch = random.sample(self.memory, self.batch_size)
        
        # 优化tensor创建 - 使用numpy批量转换避免性能警告
        states_array = np.array([e.state for e in batch], dtype=np.float32)
        actions_array = np.array([e.action for e in batch], dtype=np.int64)
        rewards_array = np.array([e.reward for e in batch], dtype=np.float32)
        next_states_array = np.array([e.next_state for e in batch], dtype=np.float32)
        dones_array = np.array([e.done for e in batch], dtype=bool)
        
        states = torch.from_numpy(states_array).to(self.device)
        actions = torch.from_numpy(actions_array).to(self.device)
        rewards = torch.from_numpy(rewards_array).to(self.device)
        next_states = torch.from_numpy(next_states_array).to(self.device)
        dones = torch.from_numpy(dones_array).to(self.device)
        
        with torch.amp.autocast('cuda', enabled=self.use_amp):
            current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
            if self.double_dqn:
                # Double DQN: 使用在线网络选择动作，目标网络评估
                next_actions = self.q_network(next_states).argmax(1).detach()
                next_q_values = self.target_network(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1).detach()
            else:
                next_q_values = self.target_network(next_states).max(1)[0].detach()
            target_q_values = rewards + (self.gamma * next_q_values * (~dones))

            # Huber损失更稳定
            loss = F.smooth_l1_loss(current_q_values, target_q_values, beta=self.huber_delta)
        
        self.optimizer.zero_grad(set_to_none=True)
        if self.use_amp:
            self.scaler.scale(loss).backward()
            torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
            self.optimizer.step()
        
        # 更新学习率
        self.scheduler.step()
        
        # 更新探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # 记录损失
        self.losses.append(loss.item())
        self.training_step += 1
        
        # 定期软更新目标网络
        if self.training_step % 4 == 0:
            self.soft_update_target_network()
        # 周期性硬更新（可配置）
        if self.training_step % max(1, self.target_update_frequency) == 0:
            self.update_target_network()
    
    def soft_update_target_network(self):
        """软更新目标网络"""
        for target_param, local_param in zip(self.target_network.parameters(), 
                                           self.q_network.parameters()):
            target_param.data.copy_(self.tau * local_param.data + 
                                  (1.0 - self.tau) * target_param.data)
    
    def update_target_network(self):
        """硬更新目标网络"""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def save_model(self, filepath: str):
        """保存模型"""
        checkpoint = {
            'q_network_state_dict': self._get_model_state_dict(self.q_network),
            'target_network_state_dict': self._get_model_state_dict(self.target_network),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step
        }
        torch.save(checkpoint, filepath)
    
    def load_model(self, filepath: str):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device, weights_only=False)

        self._load_model_state_dict(self.q_network, checkpoint['q_network_state_dict'], strict=False)
        self._load_model_state_dict(self.target_network, checkpoint['target_network_state_dict'], strict=False)
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        # 加载调度器状态（如果存在）
        if 'scheduler_state_dict' in checkpoint:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        self.epsilon = checkpoint.get('epsilon', self.epsilon)
        self.training_step = checkpoint.get('training_step', 0)
        # 加载后按需编译
        self._maybe_compile()
    
    def get_training_stats(self) -> Dict:
        """获取训练统计信息"""
        return {
            'training_steps': self.training_step,
            'epsilon': self.epsilon,
            'memory_size': len(self.memory),
            'average_loss': np.mean(self.losses[-100:]) if self.losses else 0.0,
            'device': str(self.device)
        }

# 创建简化的奖励计算器
class RewardCalculator:
    """奖励计算器"""
    
    def __init__(self):
        self.prev_state = {}
        
    def calculate_reward(self, tank, action: str, game_state: Dict) -> float:
        """
        计算奖励值 - 考虑子弹限制和目标识别
        """
        reward = 0.0
        
        # 基础生存奖励
        reward += 0.1
        
        # 健康状态奖励
        health_ratio = tank.health / 100.0
        if health_ratio > 0.8:
            reward += 0.3
        elif health_ratio < 0.2:
            reward -= 0.5
        
        # 获取可用子弹类型和当前子弹
        available_bullets = getattr(tank, 'available_bullet_types', ['NORMAL'])
        current_bullet = getattr(tank, 'bullet_type', 'NORMAL')
        
        # 动作奖励 - 考虑子弹合理性
        if 'fire' in action:
            bullet_type = action.split('_')[1] if '_' in action else 'normal'
            bullet_type = bullet_type.upper()
            
            # 检查是否使用了可用的子弹
            if bullet_type not in available_bullets:
                reward -= 2.0  # 惩罚使用不可用的子弹
            
            # 命中奖励
            if game_state.get('hit_target', False):
                target_type = game_state.get('target_type', 'unknown')
                
                # 根据目标类型和子弹类型给予不同奖励
                if target_type == 'player':
                    if bullet_type == 'EXPLOSIVE' and game_state.get('target_distance', 300) < 100:
                        reward += 10.0  # 近距离爆炸弹击中玩家
                    elif bullet_type == 'PIERCING' and game_state.get('target_distance', 300) > 200:
                        reward += 8.0   # 远距离穿甲弹击中玩家
                    elif bullet_type == 'RAPID':
                        reward += 7.0   # 快速弹击中玩家
                    else:
                        reward += 5.0   # 普通弹击中玩家
                        
                elif target_type == 'player_base':
                    if bullet_type in ['HEAVY', 'EXPLOSIVE']:
                        reward += 15.0  # 用重弹或爆炸弹攻击基地
                    else:
                        reward += 8.0   # 其他子弹攻击基地
                        
                elif target_type == 'special_wall':
                    if bullet_type == 'HEAVY':
                        reward += 12.0  # 用重弹攻击特殊墙体
                    else:
                        reward += 6.0   # 其他子弹攻击特殊墙体
                        
                else:
                    reward += 3.0   # 击中其他目标
            
            # 误击友方惩罚
            if game_state.get('hit_friendly', False):
                reward -= 15.0  # 严重惩罚误击友方
            
            # 射击频率控制
            if game_state.get('fire_rate_too_high', False):
                reward -= 1.0   # 惩罚过度射击
        
        # 子弹管理奖励
        special_bullet_count = sum(1 for bullet in available_bullets if bullet != 'NORMAL')
        if special_bullet_count > 0:
            reward += 0.5 * special_bullet_count  # 拥有特殊子弹的奖励
        
        # 目标选择奖励
        target_selection_score = game_state.get('target_selection_score', 0)
        reward += target_selection_score * 0.5
        
        # 瞄准精度奖励
        aiming_accuracy = game_state.get('aiming_accuracy', 0)
        reward += aiming_accuracy * 2.0
        
        # 战术位置奖励
        tank_pos = np.array([tank.x + tank.size[0]//2, tank.y + tank.size[1]//2])
        position_score = self._evaluate_tactical_position(tank_pos, game_state)
        reward += position_score
        
        # 避免友方目标奖励
        if game_state.get('avoided_friendly_fire', False):
            reward += 1.0
        
        # 距离管理奖励
        if game_state.get('optimal_distance', False):
            reward += 0.5
        
        return reward
    
    def _evaluate_tactical_position(self, position: np.ndarray, game_state: Dict) -> float:
        """评估战术位置价值"""
        score = 0.0
        
        # 避免太靠近边缘
        margin = 50
        if (position[0] < margin or position[0] > 750 or
            position[1] < margin or position[1] > 550):
            score -= 2.0
        
        # 距离玩家的合理性
        player = game_state.get('player')
        if player:
            player_pos = np.array([player.x + player.size[0]//2, player.y + player.size[1]//2])
            distance = np.linalg.norm(position - player_pos)
            
            # 理想距离是100-250像素
            if 100 <= distance <= 250:
                score += 1.0
            elif distance < 50:
                score -= 1.5  # 太近了
            elif distance > 350:
                score -= 0.5  # 太远了
        
        # 掩体价值
        walls = game_state.get('walls', [])
        if self._has_nearby_cover(position, walls):
            score += 0.5
        
        return score
    
    def _has_nearby_cover(self, position: np.ndarray, walls) -> bool:
        """检查附近是否有掩体"""
        for wall in walls:
            wall_pos = np.array([wall.rect.centerx, wall.rect.centery])
            distance = np.linalg.norm(position - wall_pos)
            if distance < 80:  # 80像素内有掩体
                return True
        return False
    
    def _is_good_position(self, position: np.ndarray) -> bool:
        """判断是否是好位置（保持向后兼容）"""
        # 避免太靠近边缘
        margin = 50
        if (position[0] < margin or position[0] > 750 or
            position[1] < margin or position[1] > 550):
            return False
        return True
    
    
