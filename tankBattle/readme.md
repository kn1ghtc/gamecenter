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

### 训练命令
```bash
# 标准训练 (推荐)
python train_ai.py --episodes 1000

# 快速验证训练
python train_ai.py --episodes 100

# 继续训练现有模型
python train_ai.py --episodes 500 --load-model
```

### 网络架构 ⭐ **最优配置**
```python
网络结构: 输入层 → 512 → BatchNorm → 256 → BatchNorm → 128 → 输出层
优化器: AdamW (lr=0.0003, weight_decay=0.01)
调度器: CosineAnnealingLR (T_max=1000)
批大小: 128 | 经验池: 50,000 | 目标更新: 每500步
```

### 训练特性
- **GPU自动检测**: 支持NVIDIA GPU显著加速训练过程
- **实时监控**: tqdm进度条显示训练指标和实时效果
- **智能保存**: 每100集自动保存，保留历史最佳模型
- **稳定收敛**: 大型网络配合优化超参数确保训练质量

## ⚙️ 配置系统

### 核心配置 (`config.py`)
```python
# 显示设置
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 120

# AI训练参数 ⭐ **优化重点**
AI_CONFIG = {
    'learning_rate': 0.0003,        # 学习率
    'batch_size': 128,              # 批大小
    'hidden_size': [512, 256, 128], # 网络层大小
    'target_win_rate': 0.8,         # 目标胜率 (80%)
    'save_frequency': 100,          # 保存频率 (每100集)
    'use_gpu': True,                # GPU加速开关
}

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

## 📈 更新日志

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