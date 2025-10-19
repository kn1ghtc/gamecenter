# Tank Battle Game

一个基于 PyGame 开发的坦克大战游戏，集成了先进的深度强化学习 AI 系统。

## 🎮 核心特性

### 游戏机制
- **完整坦克系统**: 玩家坦克、AI敌方坦克、多样化武器系统
- **智能关卡设计**: 30个预设关卡，支持自定义地图生成
- **战术元素**: 隔离围墙系统、基地防御、特殊围墙效果
- **存档系统**: 游戏进度保存与加载功能
- **中文UI**: 完整的中文界面和透明UI系统

### 🧠 AI 系统 ⭐ **核心优势**
- **深度强化学习**: PyTorch实现的优化DQN神经网络架构
- **GPU训练加速**: 自动检测并利用GPU，显著提升训练效率
- **实时进度监控**: tqdm可视化训练过程，显示奖励/胜率/探索率等关键指标
- **最优网络结构**: 512-256-128层大型网络，配合批标准化和AdamW优化器
- **智能决策**: A*路径规划、威胁分析、动态战术选择
- **🎉 优化突破**: 胜率从2%提升至16.67%，平均奖励+164.39，首次实现游戏胜利！

## 🚀 快速开始

### 系统要求
- **Python**: 3.6+ (推荐 3.8+)
- **操作系统**: Windows (推荐)，支持 macOS/Linux
- **内存**: 最少 512MB RAM
- **显卡**: 支持NVIDIA GPU加速训练 (可选)

### 安装依赖
```bash
# 基础运行依赖
pip install pygame

# AI训练依赖 (推荐)
pip install torch scikit-learn numpy tqdm
```

### 运行游戏
```bash
# 开始游戏
python main.py

# AI训练 (使用GPU加速)
python train_ai.py --episodes 1000

# 快速测试
python main.py --smoke-test --frames 300
```

## 🎯 游戏操作

### 基础控制
- **↑/↓**: 前进/后退
- **←/→**: 左转/右转
- **空格**: 发射子弹
- **Q/E**: 切换子弹类型
- **1/2/3**: 切换 AI 难度（简单/中等/困难）
- **P**: 暂停游戏
- **H**: 显示帮助
- **U**: 切换UI显示
- **+/-**: 调整UI透明度
- **R**: 重置关卡
- **ESC**: 退出/返回菜单

### 胜负条件
**胜利条件** (需同时满足):
1. 摧毁敌方基地 (紫色)
2. 消灭所有敌方坦克

**失败条件** (任一发生):
1. 玩家坦克被摧毁
2. 玩家基地被摧毁 (蓝色)

## 🧠 AI 训练系统
### 🧠 AI 系统 ⭐ **核心优势**
- **深度强化学习**: PyTorch 优化版 DQN（Double DQN + Huber Loss）
- **更稳健的网络**: 使用 LayerNorm（替代小批次下不稳定的 BatchNorm）
- **GPU训练加速**: 自动检测 GPU，支持可选混合精度与编译加速
- **实时进度监控**: tqdm 显示奖励/胜率/探索率等关键指标
- **统一模型格式**: 训练产物统一保存在 `ai/models/`，并提供 `best_model.pth` 别名
- **智能决策**: A* 路径规划、威胁分析、动态战术选择

# 快速验证训练
python train_ai.py --episodes 100

# 继续训练现有模型
python train_ai.py --episodes 500 --load-model
python train_ai.py --episodes 1000

# 快速测试
python main.py --smoke-test --frames 300

### 难度与射击特性
- **AI难度**: 支持简单/中等/困难三档。
    - `简单/中等`: 规则AI（上帝视角，A*绕障，直线可打即开火；中等会优先争取特殊墙效果）。
    - `困难`: 启用强化学习策略（若模型可用，否则回退战术AI）。
- **连续射击**: 玩家与AI均取消射击冷却，按住空格即可持续发射；AI根据策略与角度对齐自动高频开火。子弹寿命由 `config.py` 的 `BULLET_TYPES` 控制，保障性能。

### 并行训练与奖励塑形
- **向量化环境**: 训练时一次运行多实例环境以加速采样，配置项 `training.num_envs`（默认4，上限16）。
- **奖励维度**: 除存活、命中、击杀、移动、角度对齐等外，新增：
    - `base_damage`: 压制/接近敌方基地
    - `pickup_special`/`use_special`: 争取并使用特殊墙效果
    - `zone_control`: 占领优势区域（向上推进）
    - `cover_bonus`: 利用掩体
    - `avoid_friendly`: 避免友伤（近似）
    - `path_efficiency`: 路径效率（更快接近目标）

### 网络架构 ⭐ **最优配置**
```python
网络结构: 输入(128) → 512 → LayerNorm → 256 → LayerNorm → 128 → 输出(8)
损失函数: Huber Loss（Smooth L1）
算法: Double DQN（避免过估计）
优化器: AdamW (默认 lr=1e-4)
调度器: CosineAnnealingLR（可选）
批大小: 64（可在配置中调优）
经验池: 100,000（可在配置中调优）
replay_frequency: 1（训练步频，可在配置中调优）
```
调度器: CosineAnnealingLR (T_max=1000)
### 训练特性
- **GPU自动检测**: 支持 NVIDIA GPU；可开启混合精度（AMP）与 PyTorch 2 编译加速
- **实时监控**: tqdm 进度条显示训练指标和实时效果（奖励/胜率/ε/最佳）
- **智能保存**: 周期性保存 checkpoint；最佳模型另存为 `best_model_ep*.pth`，并同步 `best_model.pth`
- **稳定收敛**: Double DQN + Huber Loss + LayerNorm；梯度裁剪与余弦退火（可选）
- **GPU自动检测**: 支持NVIDIA GPU显著加速训练过程
- **实时监控**: tqdm进度条显示训练指标和实时效果
- **智能保存**: 每100集自动保存，保留历史最佳模型
    'learning_rate': 0.0001,        # 建议较低学习率提升稳定性
    'batch_size': 64,               # 默认批大小（可按显存调优）
    'hidden_size': [512, 256, 128], # 网络层大小
    'target_win_rate': 0.8,         # 目标胜率 (80%)
    'save_frequency': 100,          # 保存频率 (每100集)
    'use_gpu': True,                # GPU加速开关
# 显示设置
SCREEN_WIDTH = 1600
├── reinforcement_learning.py  # 强化学习核心（Double DQN + Huber + LayerNorm）
SCREEN_HEIGHT = 900
FPS = 120
### v3.1.0 - RL算法与模型格式统一 (2025-09-09)
🧠 核心更新
- 采用 Double DQN + Huber Loss，替换小批次不稳定的 BatchNorm 为 LayerNorm
- 引入 `best_model.pth` 统一别名，集成加载逻辑自动优先使用最佳/最终模型
- 训练循环增加 `replay_frequency` 配置项，便于在不同硬件上调优训练步频
- 可选启用 AMP 与 torch.compile 提升训练速度

### v3.0.0 - AI训练系统优化 (2025-01-09)

# AI训练参数 ⭐ **优化配置**
AI_CONFIG = {
    'learning_rate': 0.0002,        # 优化后学习率（从0.0001提升）
    'batch_size': 64,               # 默认批大小（可按显存调优）
    'epsilon_end': 0.05,            # 优化后最小探索率（从0.01提升）
    'epsilon_decay': 0.9998,        # 优化后衰减率（从0.9995调整）
    'hidden_size': [512, 256, 128], # 网络层大小
    'target_win_rate': 0.8,         # 目标胜率 (80%)
    'save_frequency': 100,          # 保存频率 (每100集)
    'use_gpu': True,                # GPU加速开关
}

# 🎯 优化成果 (2025-01-16)
训练表现对比:
- 优化前: 平均奖励 -3.73，胜率 2.00%，探索率过快衰减至0.01
- 优化后: 平均奖励 +164.39，胜率 16.67%，首次实现游戏胜利 ✅
- 奖励稳定性: 波动范围从±253降至±125，训练更加稳定
- 探索平衡: 探索率保持在健康的0.05，避免过早收敛

# 关键配置说明
- `training.num_envs`: 并行环境数量（默认4；1-16）。
- `training.replay_frequency`: 经验回放频率（步频）。
- `BULLET_TYPES.*.LIFETIME`: 子弹生命周期（帧），可用于控制屏幕子弹数量与性能。

# 武器系统
BULLET_TYPES = {
    'normal': {'damage': 10, 'speed': 8, 'color': (255, 255, 0)},
    'armor_piercing': {'damage': 30, 'speed': 12, 'color': (255, 100, 100)},
}
```

## 🔧 项目结构

### 核心文件
```
tankBattle/
├── main.py                 # 游戏主入口
├── train_ai.py            # AI训练启动脚本
├── config.py              # 游戏配置文件
├── ui_manager.py          # UI界面管理器
├── tank_system.py         # 坦克系统核心
├── bullet_system.py       # 子弹系统
├── environment.py         # 环境管理
├── level_manager.py       # 关卡管理器
├── save_system.py         # 存档系统
├── special_walls.py       # 特殊围墙系统
├── system_check.py        # 系统检查工具
└── training_config.json   # 训练配置文件
```

### AI系统模块
```
ai/
├── __init__.py            # AI模块初始化
├── integration.py         # AI系统集成
├── reinforcement_learning.py  # 强化学习核心
├── offline_training.py    # 离线训练环境
├── tactical_ai.py         # 战术AI决策
├── pathfinding.py         # A*路径规划
└── models/                # 保存的AI模型
```

### 游戏资源
```
assets/
├── level1.map ~ level30.map  # 30个预设关卡
├── tank_red.png              # 敌方坦克贴图
├── tank_green.png            # 玩家坦克贴图
├── explosion.wav             # 爆炸音效
├── shoot.wav                 # 射击音效
├── preview.png               # 游戏预览图
├── PNG/                      # PNG格式贴图
├── Vector/                   # 矢量格式资源
├── Spritesheet/             # 精灵图集
└── license.txt              # 资源许可证
```

### 存档目录
```
saves/
└── game_progress.json    # 游戏进度存档
```

## 🎨 游戏特色

### 特殊围墙系统
- **隔离围墙**: 中央分割战场，穿甲弹可穿透
- **效果围墙**: 破坏后给予特殊能力
- **动态生成**: 每次游戏随机生成通道位置

### 多样化武器
- **普通子弹**: 基础伤害，快速射击
- **穿甲弹**: 高伤害，可穿透隔离围墙
- **掩体弹**: 可创建临时防御工事

### 透明UI系统
- **可调透明度**: +/- 键调节UI透明度
- **智能隐藏**: U键快速切换UI显示
- **中文字体**: 自动检测系统中文字体

## 🔧 扩展开发

### 自定义坦克类型
```python
# 在 tank_system.py 中继承 BaseTank
class CustomTank(BaseTank):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 4  # 自定义速度

# 在 config.py 中添加配置
CUSTOM_TANK_CONFIG = {...}
```

### 新增子弹类型
```python
# 在 config.py 中定义
BULLET_TYPES['explosive'] = {
    'damage': 25,
    'speed': 6,
    'color': (255, 165, 0)
}

# 在 bullet_system.py 中实现特殊效果
def handle_explosive_impact(self):
    # 爆炸效果逻辑
    pass
```

### 自定义关卡
```python
# 在 level_manager.py 中添加关卡生成逻辑
def create_custom_level(level_number):
    # 自定义关卡生成算法
    return level_data
```

## ⚡ 性能优化 (v3.1.0)

### � 智能AI性能飞跃
**优化成果** (2025-10-15):
- **FPS提升**: 从 2.4 FPS → **58.2 FPS** (提升 **24倍**)
- **帧时间**: 从 422ms → **17ms** (降低 **96%**)
- **CPU使用率**: 从 80-100% → **30-50%**

### 核心优化技术
1. **网格地图预处理**:
   - 将墙体数据转换为二维网格数组
   - 碰撞检测从 O(n) 降至 O(1)
   - 消除 40,000+ 次重复墙体遍历

2. **路径规划缓存**:
   - 智能路径失效检测(目标位移>50px才重新规划)
   - 掩体评分缓存机制
   - 路径重用率提升 60%

3. **AI决策频率优化**:
   - 策略层: 60→120帧冷却
   - 战术层: 8→12帧间隔
   - 路径规划: 15→20帧超时
   - 决策频率: 每3帧→每5帧

4. **算法简化**:
   - 掩体检查距离: 3格→2格
   - 移除昂贵的墙体距离计算
   - 使用网格地图替代实时碰撞检测

### 性能对比表

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **游戏FPS** | 2.4 | 58.2 | 24.2x ⚡ |
| **AI路径规划** | ~1000ms | <20ms | 50x 🚀 |
| **碰撞检测调用** | 29M/30帧 | <1K/30帧 | 29000x 💫 |
| **CPU占用** | 80-100% | 30-50% | -50% 🔋 |

### 配置优化建议
```python
# config.py 性能优化配置
AI_CONFIG = {
    'AI_PATH_PLANNING_COOLDOWN': 120,  # 路径规划冷却(帧)
    'AI_DECISION_FREQUENCY': 5,        # 决策间隔(帧)
    'DECISION_CONFIG': {
        'strategy_timeout': 30,        # 策略层超时
        'tactical_timeout': 12,        # 战术层超时
        'pathfinding_timeout': 20,     # 路径查找超时
    }
}
```

## �📈 更新日志

### v3.1.0 - 智能AI性能优化 (2025-10-15)
⚡ **性能突破**
- **24倍FPS提升**: 智能AI从2.4 FPS提升至58.2 FPS
- **网格地图系统**: O(1)碰撞检测替代O(n)遍历
- **路径规划缓存**: 智能失效检测+掩体评分缓存
- **AI频率优化**: 多层次决策超时调整
- **算法简化**: 移除冗余计算,专注核心功能

### v3.0.0 - AI训练系统优化 (2025-01-09)
🧠 **重大升级**
- **GPU训练加速**: 自动检测并使用GPU，大幅提升训练速度
- **最优网络架构**: 512-256-128层神经网络，提供最佳AI能力
- **进度可视化**: 集成tqdm显示详细训练进度和实时效果
- **训练稳定性**: AdamW优化器 + 余弦退火学习率调度
- **项目优化**: 精简文件结构，统一文档体系

### v2.1.0 - 中文字体优化 (2025-01-08)
🔧 **技术改进**
- 智能中文字体检测和多级回退机制
- 完整UI中文支持，解决显示乱码问题

### v2.0.0 - AI系统集成 (2025-01-07)
🧠 **AI核心特性**
- PyTorch深度强化学习系统集成
- A*路径规划和智能威胁分析
- 多层次战术AI决策架构

## 📄 许可证
MIT License - 开源教育项目，欢迎学习和改进。

---
**项目特色**: 这是一个专注于AI技术教学的游戏项目，展示了现代深度强化学习在游戏AI中的实际应用。项目包含完整的游戏系统、先进的AI训练架构和丰富的扩展功能。
