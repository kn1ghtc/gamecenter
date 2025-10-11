# 五子棋 (Gomoku) 游戏工程

专业级五子棋游戏实现，具备智能AI、现代化UI和完整的游戏功能。

## 📋 目录

- [核心功能](#核心功能)
- [技术特点](#技术特点)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [游戏操作](#游戏操作)
- [AI难度说明](#ai难度说明)
- [开发指南](#开发指南)
- [测试覆盖](#测试覆盖)
- [版本历史](#版本历史)
- [后续计划](#后续计划)

## 🎯 核心功能

### 1. **智能AI对战系统**
- **三级难度**：简单（3层搜索）、中等（5层搜索）、困难（7层+迭代加深）
- **Minimax算法**：基于Alpha-Beta剪枝的高效搜索
- **棋型识别**：五连、活四、冲四、活三等12种基础棋型
- **位置评估**：中心区域权重加成，边缘棋力衰减
- **杀棋检测**：自动识别必胜/必防着法
- **历史启发**：记录历史最佳着法优化搜索

### 2. **完善的游戏功能**
- **悔棋系统**：默认3次悔棋机会，可配置
- **存档/读档**：JSON格式保存完整棋局状态
- **实时提示**：显示当前玩家、AI思考状态
- **胜负判定**：自动检测五连、和棋状态
- **游戏统计**：记录AI搜索节点数、耗时等信息

### 3. **现代化UI设计**
- **自适应布局**：窗口大小改变时自动调整棋盘比例
- **全屏支持**：F11切换全屏模式（1920×1080优化）
- **3D棋子效果**：渐变阴影、高光模拟真实质感
- **动画反馈**：落子动画、获胜连线闪烁
- **木纹棋盘**：随机生成逼真木质纹理
- **跨平台字体**：自动检测最佳中文字体

## 🛠️ 技术特点

### 算法优化
- **评估缓存**：使用棋盘版本号缓存线路提取结果
- **着法排序**：按评估分数排序，优先搜索高价值着法
- **邻域搜索**：只搜索已落子周围2格范围，减少空间
- **迭代加深**（困难模式）：从浅到深逐层搜索，更快找到最优解

### 跨平台适配
- **字体回退链**：
  - macOS: PingFang SC → Microsoft YaHei → Noto Sans CJK SC
  - Windows: Microsoft YaHei → Noto Sans CJK SC
  - Linux: Noto Sans CJK SC → WenQuanYi Micro Hei
- **音效系统**：NumPy合成WAV音频，无外部依赖

### 代码质量
- **模块化设计**：游戏逻辑、AI引擎、评估系统、UI分离
- **类型注解**：完整的Python类型提示
- **文档字符串**：所有类和方法均有详细说明
- **测试覆盖**：22个冒烟测试，覆盖核心功能

## 📂 项目结构

```
gomoku/
├── __init__.py                         # 包导出接口
├── main.py                             # 主程序入口
├── game_logic.py                       # 棋盘逻辑、胜负判定
├── ai_engine.py                        # Python AI引擎 (Phase 1)
├── ai_engine_phase2.py                 # Python AI引擎 (Phase 2高级优化)
├── ai_engine_manager.py                # 统一引擎管理器（多引擎支持）
├── evaluation.py                       # 棋型识别、局面评估
├── ui_manager.py                       # 界面渲染、事件处理
├── font_manager.py                     # 跨平台字体管理
├── test_smoke.py                       # 冒烟测试套件
├── test_ai_integration.py              # AI引擎集成测试
├── test_pure_search_performance.py     # 纯搜索性能测试
├── TASK_COMPLETION_SUMMARY.md          # 任务完成总结
│
├── config/
│   ├── constants.py                    # 游戏常量、引擎配置
│   ├── ui_config.py                    # UI布局配置
│   ├── settings.json                   # 用户配置文件
│   └── generate_sounds.py              # 音效生成脚本
│
├── cpp_engine/                         # C++引擎目录
│   ├── gomoku_engine.cpp               # C++引擎源码
│   ├── gomoku_engine.def               # DLL导出定义
│   ├── CMakeLists.txt                  # CMake构建配置
│   ├── gomoku_engine.dll               # 编译后的DLL（Windows）
│   └── build/                          # 构建目录（已忽略）
│
└── assets/
    ├── sounds/                         # 游戏音效（自动生成）
    │   ├── stone_black.wav             # 黑棋落子
    │   ├── stone_white.wav             # 白棋落子
    │   ├── win.wav                     # 胜利音效
    │   └── undo.wav                    # 悔棋音效
    └── icons/                          # 图标资源（预留）
```

### 核心模块说明

#### `game_logic.py` (485行)
- **Board类**：15×15棋盘，落子、悔棋、胜负检测
- **GameManager类**：游戏状态管理、悔棋次数控制
- **Player枚举**：黑/白/空位标识
- **GameState枚举**：进行中/黑胜/白胜/和棋

#### `ai_engine.py` (641行)
- **OptimizedAIController类**：Python Phase 1 AI引擎
- **TranspositionTable类**：置换表（500K条目）
- **KillerMoveTable类**：Killer Moves启发
- **HistoryTable类**：历史启发表
- **MoveGenerator类**：候选着法生成与排序
- **DifficultyLevel枚举**：难度级别定义

#### `ai_engine_phase2.py` (541行)
- **Phase2AIController类**：Python Phase 2高级优化引擎
- **IncrementalEvaluator类**：增量评估器（缓存线路评分）
- **FastMoveGenerator类**：改进的着法生成（优先级排序）
- **Late Move Reductions (LMR)**：后期着法深度削减
- **Null Move Pruning (NMP)**：空着剪枝

#### `ai_engine_manager.py` (350行)
- **AIEngineManager类**：统一引擎管理器
- **EngineType枚举**：CPP, PYTHON_PHASE2, PYTHON_PHASE1, AUTO
- **自动回退机制**：C++ → Phase2 → Phase1
- **create_ai_engine()工厂函数**：统一创建接口

#### `evaluation.py` (398行)
- **PatternRecognizer类**：棋型识别（滑动窗口算法）
- **BoardEvaluator类**：整盘局面评估（缓存优化）
- **PositionEvaluator类**：位置权重计算
- **PATTERN_SCORES字典**：12种棋型分数表

#### `ui_manager.py` (450行)
- **UIManager类**：主UI控制器
- **AdaptiveLayout类**：自适应布局计算
- **BoardRenderer类**：棋盘渲染、棋子绘制
- **Button类**：UI按钮组件

#### `font_manager.py` (130行)
- **FontManager类**：跨平台字体检测与缓存
- **Singleton模式**：全局字体管理器单例

## 🚀 快速开始

### 环境要求
```bash
Python 3.12+
pygame >= 2.5.0
numpy >= 1.24.0
```

### 安装依赖
```powershell
cd d:\pyproject\gamecenter\gomoku
pip install pygame numpy
```

### 生成音效（首次运行）
```powershell
python config/generate_sounds.py
```

### 启动游戏

#### 方式1：直接执行
```powershell
python main.py
```

#### 方式2：包导入
```python
from gamecenter.gomoku import run_game
run_game()
```

#### 方式3：指定AI引擎
```python
from gamecenter.gomoku.ai_engine_manager import create_ai_engine

# 使用C++引擎（推荐）
ai = create_ai_engine("cpp", "hard", time_limit=3.0)

# 使用Python Phase1（稳定）
ai = create_ai_engine("python_phase1", "medium", time_limit=5.0)

# 使用自动模式（智能选择）
ai = create_ai_engine("auto", "medium", time_limit=5.0)

# AI下棋
best_move = ai.find_best_move(board, player)
stats = ai.get_stats()  # 获取性能统计
```

## 🎮 游戏操作

### 鼠标操作
- **左键点击**：在空位落子
- **点击按钮**：
  - `新游戏`：重置棋盘
  - `悔棋`：撤销最后一步（限3次）
  - `切换AI`：循环切换简单/中等/困难

### 键盘快捷键
- `U`：悔棋（Undo）
- `R`：重新开始（Reset）
- `F11`：全屏/窗口切换
- `ESC`：退出游戏

### 游戏流程
1. 黑棋先手，人机对战模式
2. 点击棋盘空位落子
3. AI自动计算并落子（显示"AI思考中..."）
4. 先达成五连者获胜
5. 可使用悔棋功能（每次悔2步，最多3次）

## 🤖 AI引擎系统

### 引擎类型

本项目支持**多引擎架构**，提供3种AI引擎供选择：

| 引擎 | 性能 | 特点 | 推荐场景 |
|------|------|------|---------|
| **C++ Engine** | 70,000+ NPS | 原生编译，超高性能 | 困难模式，实时对战 ⭐ |
| **Python Phase 1** | ~860 NPS | 基础优化，稳定可靠 | 中等难度，开发调试 |
| **Python Phase 2** | ~600 NPS | 高级特性（LMR/NMP），实验性 | 算法研究 |

*NPS = Nodes Per Second (每秒搜索节点数)*

### 引擎配置

在`config/constants.py`中配置：

```python
AI_ENGINE_TYPE = "auto"  # 引擎类型
# 可选值: "auto" | "cpp" | "python_phase1" | "python_phase2"

AI_DEFAULT_DIFFICULTY = "medium"  # 默认难度
# 可选值: "easy" | "medium" | "hard"
```

### 自动回退机制

系统采用**多层回退**策略，确保稳定性：

```
AUTO模式
  ↓
尝试加载C++ Engine (gomoku_engine.dll)
  ↓ 失败？
尝试Python Phase 2 (高级优化)
  ↓ 失败？
使用Python Phase 1 (基础优化，保底)
```

### 引擎技术对比

#### C++ Engine (推荐✅)
- **性能**: 70,000+ NPS（超目标23倍）
- **技术**: Visual Studio 2022编译，AVX2指令集优化
- **优点**: 极速响应，困难模式无延迟
- **缺点**: 需要DLL文件（已包含）

#### Python Phase 1（稳定✅）
- **性能**: ~860 NPS（基线）
- **技术**: Alpha-Beta剪枝 + 置换表 + Killer Moves + 历史启发
- **优点**: 纯Python实现，跨平台兼容
- **缺点**: 中等性能，深度搜索慢

#### Python Phase 2（实验⚠️）
- **性能**: ~600 NPS（待优化）
- **技术**: Late Move Reductions + Null Move Pruning + 增量评估
- **优点**: 实现了高级搜索技术
- **缺点**: 当前参数未调优，性能反而低于Phase 1

### AI难度说明

| 难度 | 搜索深度 | 算法特性 | C++耗时 | Python耗时 | 适用场景 |
|-----|---------|---------|---------|-----------|---------|
| **简单** | 3层 | 基础Minimax | <0.1秒 | <0.5秒 | 初学者 |
| **中等** | 5层 | Alpha-Beta剪枝 | <0.5秒 | 1-3秒 | 中级玩家 |
| **困难** | 7层+ | 迭代加深 + 历史启发 | 1-2秒 | 5-15秒 | 高手对战 |

### AI思考过程可视化
- **引擎类型显示**：实时显示当前使用的引擎
- **搜索节点数**：实时显示搜索规模
- **耗时统计**：精确到毫秒
- **回退记录**：显示C++失败次数（如有）

## 👨‍💻 开发指南

### 运行测试
```powershell
# 完整冒烟测试
$env:SDL_VIDEODRIVER='dummy'; $env:SDL_AUDIODRIVER='dummy'; pytest test_smoke.py -v

# 测试覆盖率
pytest test_smoke.py --cov=. --cov-report=html

# 单独测试类
pytest test_smoke.py::TestAI -v
```

### 调整AI参数
编辑 `ai_engine.py` 中的 `DifficultyLevel.get_depth()`：
```python
depths = {
    DifficultyLevel.EASY: 3,    # 改为 2 加快速度
    DifficultyLevel.MEDIUM: 5,  # 改为 4
    DifficultyLevel.HARD: 7,    # 改为 6
}
```

### 修改棋型分数
编辑 `config/constants.py` 中的 `PATTERN_SCORES`：
```python
PATTERN_SCORES = {
    "FIVE": 100000,        # 五连（获胜）
    "LIVE_FOUR": 10000,    # 活四（必胜）
    "RUSH_FOUR": 1000,     # 冲四（需防守）
    # ... 其他棋型
}
```

### 自定义UI配色
编辑 `config/ui_config.py`：
```python
THEME = {
    "bg_color": (34, 139, 34),       # 背景色
    "board_color": (218, 165, 32),   # 棋盘色
    "line_color": (0, 0, 0),         # 线条色
    # ...
}
```

## 🧪 测试覆盖

### 测试统计
- **测试文件**：`test_smoke.py`（347行）
- **测试用例**：22个
- **测试类**：6个（棋盘逻辑、游戏管理、AI、评估、字体、存档）
- **通过率**：100%
- **执行时间**：3.88秒

### 测试分类
1. **棋盘逻辑测试**（7个）
   - 初始化、落子、胜负检测（横竖斜）、和棋、悔棋

2. **游戏管理测试**（2个）
   - 悔棋次数限制、游戏重置

3. **AI引擎测试**（3个）
   - 着法合法性、必胜着法识别、性能测试

4. **评估系统测试**（3个）
   - 评估器初始化、初始局面评估、获胜局面评估

5. **字体管理测试**（5个）
   - 初始化、字体获取、回退机制、渲染、尺寸计算

6. **存档系统测试**（1个）
   - 保存与加载完整性

7. **包导入测试**（1个）
   - 验证包结构正确性

## 📜 版本历史

### v1.0.0 (2025-01-XX)
**首个稳定版本发布**

#### 核心功能
- ✅ 实现完整的五子棋游戏规则
- ✅ 三级难度AI（简单/中等/困难）
- ✅ Minimax + Alpha-Beta剪枝算法
- ✅ 12种棋型识别系统
- ✅ 悔棋功能（3次限制）
- ✅ 存档/读档系统

#### UI/UX
- ✅ 自适应窗口布局
- ✅ 全屏模式支持（F11）
- ✅ 3D棋子渲染效果
- ✅ 木纹棋盘纹理
- ✅ 落子动画与音效
- ✅ 获胜连线闪烁动画

#### 技术优化
- ✅ 评估函数缓存机制
- ✅ 历史启发着法排序
- ✅ 邻域搜索空间优化
- ✅ 跨平台字体回退系统
- ✅ NumPy音效生成

#### 测试与质量
- ✅ 22个冒烟测试用例
- ✅ 100%测试通过率
- ✅ 完整类型注解
- ✅ 详细文档字符串

## 🗺️ 后续计划

### v1.1.0 - 功能增强（计划中）
- [ ] **联机对战**：局域网/互联网对战
- [ ] **复盘系统**：保存对局记录，支持逐步回放
- [ ] **开局库**：预置经典开局，减少开局思考时间
- [ ] **定式识别**：识别常见定式并提供建议
- [ ] **统计系统**：胜率、平均耗时、棋型频率分析

### v1.2.0 - AI升级（计划中）
- [ ] **神经网络AI**：基于PyTorch的深度学习模型
- [ ] **MCTS算法**：蒙特卡洛树搜索替代Minimax
- [ ] **禁手规则**：支持标准五子棋禁手（三三、四四、长连）
- [ ] **自我对弈训练**：AI自我提升系统

### v1.3.0 - 用户体验（计划中）
- [ ] **多主题支持**：经典、现代、暗黑主题切换
- [ ] **背景音乐**：可配置的背景音乐系统
- [ ] **新手教程**：交互式教学模式
- [ ] **成就系统**：解锁成就和称号
- [ ] **排行榜**：本地/在线排行榜

### v2.0.0 - 多模式扩展（远期规划）
- [ ] **六子棋模式**：支持六子棋规则
- [ ] **连珠模式**：日本连珠规则
- [ ] **自定义规则**：棋盘大小、获胜条件可配置
- [ ] **AI编辑器**：可视化编辑AI评估函数

## 📝 开发者信息

- **开发者**：kn1ghtc
- **项目类型**：独立游戏
- **开发周期**：2025-01
- **代码质量**：生产级，无占位符代码
- **文档语言**：中文
- **编程语言**：Python 3.12
- **开发环境**：Windows 11 + PowerShell

## 📄 许可证

本项目为个人研究项目，仅供学习交流使用。

---

**享受智能五子棋的乐趣！Have fun! 🎮**
