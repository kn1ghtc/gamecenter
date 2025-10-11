# 五子棋 (Gomoku) 游戏工程

现代化五子棋项目，结合高性能AI、可配置化管控和跨平台UI，覆盖从安全研究到游戏体验的完整需求。

## 📋 目录

- [核心功能](#核心功能)
- [技术亮点](#技术亮点)
- [项目结构](#项目结构)
- [统一配置系统](#统一配置系统)
- [AI 引擎体系](#ai-引擎体系)
- [快速开始](#快速开始)
- [测试](#测试)
- [开发说明](#开发说明)
- [版本历史](#版本历史)
- [后续计划](#后续计划)

## 🎯 核心功能

### 智能对弈
- 三档难度：简单（D3）、中等（D5）、困难（D7+迭代加深）
- Alpha-Beta 剪枝、历史启发、Killer Moves、置换表等优化
- 棋型识别覆盖五连、活四、冲四、活三等关键模式
- 自动检测必胜/必防着法，实时输出搜索统计

### 完整游戏体验
- 人机 / 双人模式切换，默认最多 3 次悔棋
- JSON 存档机制，可在 `saves/` 下自动生成快照
- UI 按钮与快捷键并存（U 悔棋，R 重开，F11 全屏）
- 自适应布局、落子动画、胜利闪烁线、木纹棋盘
- 右侧信息面板展示双方积分、最近落子、思考状态与用时

### 资源与字体
- 脚本生成音效（无需外部素材），跨平台字体回退链
- 统一的字体管理器缓存与调试模式（F4 切换）

## 🛠️ 技术亮点

### 算法与性能
- 迭代加深 + 期望窗口 + 候选着法 Top-N 过滤
- 统一 Zobrist 哈希与可调置换表容量
- 通过配置控制时间管理、候选着法数量、迭代策略

### 架构与可维护性
- 单一配置入口 (`config_manager.py` + `game_config.json`)
- `AIEngineManager` 统一封装 C++ / Python 引擎并提供回退
- 绝对导入、类型注解、模块化拆分（逻辑 / AI / UI / 工具）

### 质量保障
- 新的 pytest 套件覆盖配置、AI 管理、AI 核心与棋盘逻辑
- 关键模块均包含文档字符串与必要的解释性注释

## 📂 项目结构

```
gomoku/
├── __init__.py
├── ai_engine.py
├── ai_engine_manager.py
├── evaluation.py
├── font_manager.py
├── game_logic.py
├── main.py
├── scripts/
│   └── generate_sounds.py
├── config/
│   ├── config_manager.py
│   └── game_config.json
├── tests/
│   ├── test_ai_engine_core.py
│   ├── test_ai_engine_manager.py
│   ├── test_board_logic.py
│   └── test_config_manager.py
├── ui_manager.py
├── cpp_engine/        # C++ 引擎与构建资源
├── assets/            # 自动生成的声音与图形资产
├── TASK_COMPLETION_SUMMARY.md
├── OPTIMIZATION_ANALYSIS.md
├── PERFORMANCE_ANALYSIS.md
└── UPDATE_SUMMARY_20250122.md
```

> 说明：后续会逐步将历史文档内容迁入本 README，保留时间线信息但避免重复维护。

## ⚙️ 统一配置系统

- 所有游戏、AI、UI、音频配置统一存放在 `config/game_config.json`
- 通过 `config/config_manager.py` 提供类型化访问与缓存
- `DifficultyConfig` 为难度层级提供对象封装，并暴露 `search_depth`、`time_limit`、`transposition_table_size` 等核心指标
- 运行时设置自动同步至 `saves/runtime_settings.json`，避免仓库内出现重复的 `user_settings.json`

常用接口示例：
```python
from gamecenter.gomoku.config.config_manager import get_config_manager, get_difficulty_config

manager = get_config_manager()
defaults = manager.get_engine_defaults()
medium = get_difficulty_config("medium")
print(defaults["type"], medium.search_depth)
```

> 配置热加载：调用 `ConfigManager.reload()` 可重新读取 JSON，无需重启进程。

## 🤖 AI 引擎体系

| 引擎 | 性能指标 (NPS*) | 特点 | 场景 |
|------|-----------------|------|------|
| C++ Engine | 70,000+ | 原生 DLL，最佳性能 | 高难度 / 竞技对局 |
| Python Engine | ~860 | 纯 Python，配置化可调 | 开发调试 / 普通对局 |

*NPS = 每秒搜索节点数。

### 引擎管理
- `EngineType` 支持 `cpp` / `python` / `auto`
- `auto` 模式优先尝试 C++，若加载失败自动回退到 Python
- `create_ai_engine(engine_type, difficulty, time_limit=None)` 为统一工厂
- 兼容旧参数：`python_phase1`、`python_phase2` 会自动映射到 `python`

```python
from gamecenter.gomoku.ai_engine_manager import create_ai_engine
from gamecenter.gomoku.game_logic import Board, Player

ai = create_ai_engine("auto", "medium", time_limit=3.0)
board = Board()
board.place_stone(7, 7, Player.BLACK)
print(ai.find_best_move(board, Player.WHITE))
print(ai.get_stats())
```

## 🚀 快速开始

### 环境要求
- Windows 11 + PowerShell
- Python 3.12+

### 安装依赖
```powershell
cd d:\pyproject\gamecenter\gomoku
python -m pip install --upgrade pip
pip install pygame numpy pytest
```

### 生成音效（首次运行）
```powershell
python scripts/generate_sounds.py
```

### 启动游戏
```powershell
python main.py
```
或通过包导入：
```python
from gamecenter.gomoku import run_game
run_game()
```

## 🧪 测试

新的 pytest 套件集中在 `tests/` 目录：

- `test_config_manager.py`：验证配置单例与字段完整性
- `test_ai_engine_manager.py`：覆盖引擎回退、兼容别名、时间限制保持等逻辑
- `test_ai_engine_core.py`：确保 Python AI 能返回合法着法并正确处理难度切换
- `test_board_logic.py`：棋盘初始化、落子、胜负与悔棋约束
- `test_game_ui.py`：验证游戏主类初始化、侧边栏构建以及一次更新/绘制循环

运行方式：
```powershell
$env:SDL_VIDEODRIVER='dummy'
$env:SDL_AUDIODRIVER='dummy'
pytest tests -v
```

> 建议在 CI 中开启 `--maxfail=1 --disable-warnings` 以及覆盖率采集 (`pytest --cov=gamecenter.gomoku tests`).

## 🧭 开发说明

- **配置扩展**：新增难度或 UI 参数时，先在 `game_config.json` 中定义，再通过 `ConfigManager` 访问
- **AI 调优**：`game_config.json` 的 `engine.difficulties` 节点控制搜索深度、迭代开关、候选着法数量
- **资产管理**：资源放入 `assets/`，必要时更新 `scripts/generate_sounds.py`
- **C++ 引擎**：源码位于 `cpp_engine/`，需借助 VS2022/vcpkg 构建
- **编码规范**：绝对导入，单文件不超过 1000 行，复杂代码段辅以简明注释

## 📜 版本历史

### 2025-10-11
- ♻️ 重构右侧信息面板，新增积分、最近落子、思考状态与用时展示，并优化棋盘填充布局
- ✅ 修复调试阶段禁用的 killer move 逻辑，确保 AI 在有必胜手时立即落子
- 🚚 运行时设置迁移至 `saves/runtime_settings.json`，仓库中删除冗余 `user_settings.json`
- ✅ C++ / Python 引擎统一启用即时胜负判断，遇到必胜手优先执行并自动补强防守
- ✅ 修复 Transposition Table 命中场景下的连续落子问题，保证人机对战节奏稳定
- 🎨 自适应棋盘布局升级，窗口缩放或小屏场景下棋盘与侧边栏均完整展示
- 📐 优化横向剩余空间分配，棋盘自动贴合左右安全边界，在宽屏下填满可用区域且不遮挡信息面板

### 2025-02-XX
- ✅ 引入统一 JSON 配置与 `ConfigManager`
- ✅ `AIEngineManager` 精简，移除实验性的 Phase 2 引擎
- ✅ 删除遗留配置脚本与旧测试，构建新的 pytest 套件
- ✅ 更新 README，明确当前结构与工作流

## 🗺️ 后续计划

| 版本 | 方向 | 目标 |
|------|------|------|
| v1.1 | 功能增强 | 复盘、开局库、统计面板 |
| v1.2 | AI 升级 | 引入 MCTS / NN 评估、完善禁手规则 |
| v1.3 | 用户体验 | 多主题、成就系统、在线排行 |
| v2.0 | 模式扩展 | 六子棋、连珠、可定制规则 |

## 🧑‍💻 开发者
- 作者：kn1ghtc
- 平台：Windows 11 + PowerShell
- 编码：UTF-8（控制台自动切换 `chcp 65001`）

---

畅享智能五子棋对弈！🎮
