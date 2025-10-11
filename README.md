# Game Center 开发文档

> 最后更新：2025-10-11（北京时间）

Game Center 是一个汇集多款 Python 游戏与工具的项目集合，覆盖 3D/2.5D 格斗、平台跳跃、棋类 AI 以及资源处理脚本。本指南聚焦于统一的项目结构、运行方式和当前可用功能，便于后续维护与扩展。

## 目录

1. [项目概览](#项目概览)
2. [仓库结构](#仓库结构)
3. [环境准备与通用依赖](#环境准备与通用依赖)
4. [快速开始](#快速开始)
5. [StreetBattle——3D/2.5D 格斗平台](#streetbattle3d25d-格斗平台)
6. [Eco Grassland——生态平衡模拟](#eco-grassland生态平衡模拟)
7. [其他子项目概览](#其他子项目概览)
8. [开发工具脚本](#开发工具脚本)
9. [贡献流程](#贡献流程)
10. [许可证与资源来源](#许可证与资源来源)

---

## 项目概览

- **仓库定位**：整合多个子项目的游戏中心，提供共享的资源管理和测试流程。
- **核心语言**：Python 3.12（默认），Windows 11 + PowerShell 为主要运行环境。
- **主要框架**：Panda3D、Pygame、LangChain、Pillow、Requests、NumPy/SciPy 等。
- **资源策略**：所有可分发素材均采用开源或 CC0 授权；避免使用临时或程序化占位资产。

---

## 仓库结构

```
gamecenter/
├─ streetBattle/        # 3D/2.5D 格斗主项目
├─ superMario/          # Super Mario Brothers 平台跳跃
# Game Center 开发手册

> 最后更新：2025-10-11（北京时间）

Game Center 集成了五款 Python 游戏（Chess、StreetBattle、Stickman Game、Super Mario、Tank Battle），统一了资源治理、测试流程和运维策略。本手册作为唯一权威文档，对整体环境、各子模块特性、常用脚本与质量保证手段进行系统说明，便于团队协同维护与版本迭代。

## 目录

1. [项目概览](#项目概览)
2. [目录结构](#目录结构)
3. [环境准备](#环境准备)
4. [运行方式概览](#运行方式概览)
5. [游戏模块总览](#游戏模块总览)
   1. [Chess](#chess)
   2. [Military Chess（中国军棋）](#military-chess中国军棋)
   3. [StreetBattle](#streetbattle)
   4. [Eco Grassland](#eco-grassland生态平衡模拟)
   5. [Stickman Game](#stickman-game)
   6. [Super Mario Bros](#super-mario-bros)
   7. [Tank Battle](#tank-battle)
6. [工具与自动化脚本](#工具与自动化脚本)
7. [质量保障与测试](#质量保障与测试)
8. [贡献流程](#贡献流程)
9. [许可证与资源来源](#许可证与资源来源)

---

## 项目概览

- **定位**：单一仓库存放五款可独立运行的游戏项目，与资源、工具脚本共享。
- **目标平台**：Windows 11，PowerShell 为默认终端；Python 3.12 是推荐运行时。
- **核心依赖**：Pygame、Panda3D、LangChain、Pillow、Requests、NumPy/SciPy、PyTorch 等。
- **资源策略**：全部素材保持合法来源（CC0/CC-BY 等），通过脚本自动校验与同步，避免占位资产。

---

## 目录结构

```
gamecenter/
├─ README.md                 # 本文档（唯一项目文档）
├─ chess/                    # 国际象棋 + AI 陪伴系统
├─ militaryChess/            # 中国军棋（陆战棋）+ 智能 AI
├─ streetBattle/             # 3D/2.5D 格斗平台
├─ stickman_game/            # 火柴人动作冒险
├─ superMario/               # 超级玛丽平台跳跃
├─ tankBattle/               # 坦克大战 + 强化学习 AI
└─ tools/                    # 通用工具脚本与资源流水线
```

顶层还包含其他安全研究项目（如 `llmAttack/`、`NetPenetration/`），与游戏中心无直接耦合，此处不展开。

---

## 环境准备

所有模块均可在同一虚拟环境中运行，建议按照如下步骤初始化：

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel
```

- **通用依赖**：大部分 Pygame/Panda3D 项目需要 `pygame`, `pillow`, `requests`, `numpy`, `scipy`。
- **模块专属依赖**：
  - Chess：`langchain`, `chromadb`, `torch`, `openai`, `pygame`, `speechrecognition`, `pyaudio`（可选），`python-chess` 等。
  - StreetBattle（3D）：`panda3d`, `numpy`; 2.5D 模式仅需 `pygame`。
  - Tank Battle：`torch`, `tqdm`, `numpy`。

各子项目提供独立的 `requirements*.txt` 时，请优先参考对应文件。

### macOS（Homebrew + zsh）快速开始

> 建议始终在项目本地虚拟环境中安装依赖，避免触发 Homebrew 的 PEP 668 保护（externally-managed-environment）。以下步骤在 zsh 下验证通过。

1) 准备 Python 3.13（通过 Homebrew 安装或已存在于 `/usr/local/bin/python3`）

2) 在仓库根目录创建并激活虚拟环境

- 使用绝对路径调用 Python 创建 `.venv`，激活后用 `python -V` 确认为 3.13。

3) 安装通用依赖（示例：pygame）

- 在已激活的虚拟环境中，先升级 pip，再安装 pygame；不要在系统环境直接使用 pip。

4) 运行冒烟测试（以军棋模块为例）

- 在虚拟环境中安装 pytest 后运行 `gamecenter/militaryChess/test_smoke.py`，应全部通过。

常见问题与排查：
- 出现 “error: externally-managed-environment / PEP 668” 提示：说明你在系统环境中使用 pip，需先激活 `.venv` 再安装；不建议使用 `--break-system-packages` 强行写入系统环境。
- `pip` 指向已卸载的旧解释器（例如 3.11）导致 “bad interpreter” 错误：
   - 检查 shebang（pip 文件前两行）确认目标解释器。
   - 如指向 3.11，可重建链接：将系统级 `/usr/local/bin/pip` 链接到 3.13 的 `pip3`；更推荐直接在 `.venv` 中使用 `python -m pip ...`，彻底避免系统级冲突。

VS Code 提示：
- 通过命令面板选择解释器为仓库根目录的 `.venv/bin/python`，终端与测试任务将继承该解释器，体验更稳定。

---

## 运行方式概览

1. 在 `gamecenter/` 根目录激活虚拟环境。
2. 根据目标游戏进入其子目录并执行主入口：
   - Chess：`python chess/main.py`（或 `python -m chess.game`）
   - Military Chess（军棋）：`cd militaryChess; python main.py` 或 `python -c "from gamecenter.militaryChess import run_game; run_game()"`
   - StreetBattle：`cd streetBattle; python main.py`
   - Stickman Game：`cd stickman_game; python main.py`
   - Super Mario：`cd superMario; python main.py`
   - Tank Battle：`cd tankBattle; python main.py`
3. 如需运行工具或测试，参见相应章节。

---

## 游戏模块总览

### Chess

**概览**：现代化国际象棋平台，集成多层级 AI、语音助手、记忆检索与自对弈训练。项目结构围绕 GUI（Pygame）、AI Agent（LangChain/OpenAI）与数据存储（SQLite/向量数据库）展开。

**核心特性**
- 四种对战模式：双人、传统 AI（Minimax）、机器学习 AI（AlphaZero 架构）、GPT 专家 AI。
- **Chess AI Agent**：具备记忆库（ChromaDB/LanceDB）、任务规划、工具链调用（MCP 服务）以及跨平台语音交互（OpenAI Whisper/TTS，系统 TTS 回退）。
- **训练体系**：并行自对弈、经验回放、双头神经网络，支持 GPU 加速与混合精度。
- **数据持久化**：自动记录棋局（PGN、FEN、特征向量）并保存至 SQLite。

**依赖 & 配置**
- 标准依赖见 `chess/requirements.txt`。
- 启用语音或 GPT 模式需要配置 `OPENAI_API_KEY` 环境变量。
- 语音测试脚本：`python chess/test_voice.py --mode <tts|stt|full>`。

**运行与测试**
```powershell
cd gamecenter/chess
python main.py                   # GUI 入口
python -m pytest tests           # 运行单元/集成测试
python tools/training.py --episodes 100  # 示例训练脚本
```

**关键目录**
- `ai/`: 记忆、规划、工具、语音、ML AI 模块。
- `assets/`: 棋子图像、音效、语音缓存。
- `config/`: UI/颜色/字体/路径等集中配置。

---

### Military Chess（中国军棋）

**概览**：完整的中国军棋（陆战棋）实现，具备智能 AI 对手与现代化 Pygame 界面。采用模块化架构，分离游戏逻辑、AI 引擎和评估函数，支持多种运行方式。

**核心特性**
- **完整规则实现**：标准中国军棋规则，包括棋子等级、行营铁路、司令部等要素。
- **智能 AI 引擎**：基于 negamax 搜索算法，支持迭代加深、时间限制和多种难度设置。
- **现代化 UI**：响应式 Pygame 界面，支持菜单、规则说明、游戏进行和结束画面。
- **暗棋模式**：开局全盘随机、全部棋子朝下，玩家与 AI 需先翻子再行动，AI 会自动翻找可行动的棋子。
- **中文字体引擎升级**：FontManager 直接解析系统字体文件（PingFang、Microsoft YaHei、Noto Sans CJK 等），彻底解决窗口内中文乱码问题。
- **跨平台中文字体**：智能字体管理器，自动检测并使用系统最佳中文字体（macOS: PingFang SC, Windows: Microsoft YaHei）。
- **音效系统**：内置移动、攻击、胜利音效，支持音量调节和静音模式。
- **多线程 AI**：AI 思考过程在后台线程运行，保持界面响应性。
- **绝对导入架构**：统一的模块导入系统，支持直接运行和包导入两种方式。

**运行方式**
```zsh
# 方式 1：直接运行（推荐用于开发调试）
cd gamecenter/militaryChess
python main.py

# 方式 2：包导入运行
python -c "from gamecenter.militaryChess import run_game; run_game()"

# 方式 3：模块内测试
python test_smoke.py
```

**控制说明**
- 鼠标点击选择和移动棋子
- 暗棋模式下首次点击己方棋子会翻面，再次点击合法目的地即可完成行动
- ESC 键返回主菜单
- F11 切换全屏模式
- F4 切换字体调试信息（显示当前使用的字体）
- 音量调节：设置菜单中调整
- AI 难度：可在设置中切换简单/标准/困难

**字体和显示**
- 自动检测并使用系统最佳中文字体
- macOS：直接加载 `/System/Library/Fonts/PingFang.ttc` 等中文字体，确保 glyph 完整
- Windows：优先匹配 `Microsoft YaHei`、`SimHei` 等字体文件
- Linux：支持 Noto Sans CJK SC、WenQuanYi 系列字体，优先使用对应 `.ttc/.otf`
- 如遇到中文显示问题，请确保系统已安装中文字体

**技术架构**
- `main.py`：游戏 UI、渲染、事件处理和主循环
- `game_logic.py`：棋盘表示、移动生成、战斗解算和游戏状态管理
- `ai_engine.py`：AI 控制器、搜索算法和设置管理
- `settings.json`：保存音量、难度、暗棋模式（`dark_mode`）等持久化配置
- `evaluation.py`：位置评估、启发式函数和策略分析
- `__init__.py`：包接口和公开 API

**测试与质量保证**
```zsh
# 冒烟测试（验证核心功能）
python test_smoke.py

# 包导入测试
python -c "from gamecenter.militaryChess import create_logic_state; print('导入成功')"
```

---

### StreetBattle

**概览**：KOF 97/98 风格的格斗平台，提供 Panda3D 3D 模式与 Pygame 2.5D 模式。最新版本支持 43 名角色的自动化资源生成、颜色调制与技能配置。当前已完成29个核心角色的高质量3D资源下载转换（67.4%完成度）。

**核心特性**
- **双引擎**：`main.py` 提供 GUI 启动器，`twod5/game.py` 负责 2.5D 快速对战。
- **Roster 管理**：`config/roster.json`、`config/skills.json` 描述角色属性、输入映射和技能；`tools/build_kof_roster_assets.py` 可一键再生成 manifest 与配置。
- **资源管线**：精灵 manifest 统一引用 Martial Hero CC0 包，可通过 `tools/sync_sprites.py` 与 `tools/sync_portraits.py` 维护。3D 模式资源由 `resource_manager.py` 负责拉取与审计。
- **全自动测试**：`tests/test_smoke.py` 校验精灵、技能、设置；额外的 `test_combat.py`、`test_rollback_sim.py` 验证战斗逻辑。

**最新更新（2025-09-30）**
- 修复了 2.5D 启动时因 `config/roster.json` 使用字符串列表导致的角色表空集问题，现支持自动融合统一角色清单，避免 “list index out of range” 崩溃。
- `SpriteBattleGame` 会确保默认玩家/CPU 角色始终可用，并在缺失配置时回退到统一精灵清单。
- 新增 `tests/test_twod5_roster.py` 冒烟测试，覆盖花名册解析与默认角色检查。

**运行指令**
```powershell
cd gamecenter/streetBattle
python main.py              # GUI 启动器
python twod5/game.py        # 直接进入 2.5D 模式
```

**配置要点**
- `config/settings.json`：存储图形/音频/键位以及 `gameplay.player_character`、`gameplay.cpu_character`。
- `assets/sprites/<fighter>/manifest.json`：逐角色动画配置（自动生成，可手动微调）。
- 胜利提示、HUD 等根据角色 display name 动态渲染。

**测试**
```powershell
cd gamecenter
python -m pytest streetBattle/tests/test_smoke.py
pytest streetBattle/tests/test_twod5_roster.py
```

**常用脚本**
- `tools/build_kof_roster_assets.py`：批量生成 43 名角色的 manifest/skills/roster。
- `tools/resource_manager.py`：3D 模式资源下载、审计、清理。
- `tools/assets_audit.py`：资产完整性扫描。

---

### Eco Grassland——生态平衡模拟

**概览**：生态平衡教学模拟器，玩家可在大地图中观察羊、兔、牛、草地与水源之间的动态循环，配合实时生态统计与预警提示，适用于课堂演示与玩法扩展。

**最新更新（2025-10-11）**
- 修复生态压力累乘导致动物能量消耗指数级膨胀的问题，现按基础能量线性调节。
- 动物新增寻水/饮水行为链，饮水过程会随时间线性降低口渴值并重置移动目标。
- 进食过程仅在草地仍有营养时才降低饥饿值，避免出现“空气充饥”。
- 新增 `gamecenter/tests/test_ecosystem_logic.py`，覆盖进食、饮水与生态压力回归场景。

**运行与测试**
```powershell
cd gamecenter/Eco_grassland
python main.py
python -m pytest gamecenter/tests/test_ecosystem_logic.py
```

**关键模块**
- `main.py`：游戏入口、摄像机与 UI 管理。
- `ecosystem.py`：生态压力评估、草地网格、动物生成与统计出口。
- `game_entities.py`：动物 AI 状态机、草地生长逻辑与渲染细节。

---

### Stickman Game

**概览**：单人火柴人动作冒险，包含 30 关卡、武器切换、全屏增益与多彩 UI。

**核心特性**
- 侧向平台关卡，支持手枪、炸弹、近战（可通过 `switch_weapon` 切换）。
- 全屏模式提供移动、跳跃、射程等增益，增强战斗节奏。
- 敌人 AI 拥有基础追踪/攻击范围设定；每关时间限制与得分系统。
- 跨平台中文字体自动探测与回退，确保界面文本稳定显示。

**运行与控制**
```powershell
cd gamecenter/stickman_game
python main.py
```

| 操作 | 键位 |
| --- | --- |
| 左/右移动 | ← / → |
| 跳跃 | 空格 |
| 射击 | Z |
| 投掷炸弹 | X |
| 切换武器 | C |
| 全屏切换 | F11 |

**关键模块**
- `src/config.py`：分值、敌人、平台、UI、字体等统一配置。
- `src/game.py`：状态机、关卡逻辑、事件处理。
- `assets/`：精灵、音效、关卡数据。

---

### Super Mario Bros

**概览**：完整的 2D 平台跳跃游戏，包含 30 个关卡、积分系统、自动资源下载与中英双语 UI。

**核心特性**
- 游戏启动自动校验/下载素材（图片、音频、字体），支持离线回退。
- 完整音频系统，使用 NumPy/SciPy 生成音效，支持静音回退。
- 关卡组件模块化：`src/player.py`, `src/level.py`, `src/scoring.py` 等。
- 跨平台字体检测，确保中文文本显示。

**运行与控制**
```powershell
cd gamecenter/superMario
python main.py
```

| 操作 | 键位 |
| --- | --- |
| 开始/下一关 | Enter |
| 左/右移动 | A / D 或 ← / → |
| 跳跃 | 空格 / W / ↑ |
| 暂停 | P |
| 退出 | Q |

**依赖**
- `pygame`, `pillow`, `requests`, `numpy`, `scipy`。
- 资源下载逻辑位于 `src/downloader.py`，支持断点续传。

---

### Tank Battle

**概览**：坦克对战游戏，强化学习 AI（Double DQN + Huber Loss + LayerNorm）与地图要素（围墙、基地、防御）。

**核心特性**
- 三种 AI 难度：规则 AI（简单/中等）与强化学习策略（困难）。
- GPU 加速训练，支持 `torch.compile`、AMP、并行环境采样。
- 30 关预设地图、子弹/掩体系统、基地胜负条件。
- UI 支持中文字体、透明度调节、HUD 控件。

**运行与训练**
```powershell
cd gamecenter/tankBattle
python main.py                          # 游戏入口
python train_ai.py --episodes 1000      # GPU 强化学习
python main.py --smoke-test --frames 300
```

**配置**
- `config.py`：地图、武器、HUD、AI 参数。
- `ai/reinforcement_learning.py`：核心 DQN 模型与训练循环。
- `training_config.json`：可调超参（批量、学习率、并行环境数）。

---

## 工具与自动化脚本

| 脚本 | 说明 |
| --- | --- |
| `tools/build_kof_roster_assets.py` | 生成 StreetBattle 43 名角色的 manifest / roster / skills 配置 |
| `tools/resource_manager.py` | StreetBattle 3D 资源下载、授权校验、临时文件清理 |
| `tools/sync_sprites.py` | 2.5D 精灵批量同步与 manifest 验证 |
| `tools/sync_portraits.py` | 角色肖像自动化拉取 / 渲染 |
| `tools/assets_audit.py` | CC0 资产校验与占位资源清理 |
| `superMario/src/downloader.py` | 超级玛丽资源自检与下载 |
| `tankBattle/system_check.py` | 坦克大战依赖、显卡、声音环境快速诊断 |

执行脚本前请激活虚拟环境、备份重要资产，并在 PowerShell 中运行（部分脚本依赖 Windows API）。

---

## 质量保障与测试

- **Military Chess（军棋）**：`python test_smoke.py` 验证游戏逻辑、AI 引擎和包导入；支持直接运行和包导入两种方式的测试。
- **StreetBattle**：`python -m pytest streetBattle/tests/test_smoke.py`（验证 manifest、技能、设置）；建议定期运行 `test_combat.py` 和 `test_rollback_sim.py`。
- **Eco Grassland**：`python -m pytest gamecenter/tests/test_ecosystem_logic.py` 覆盖生态压力、进食与饮水逻辑，确保教学模式稳定运行。
- **Chess**：`python -m pytest` 覆盖 GUI、规则、AI 接口；训练脚本支持离线验证。
- **Tank Battle**：提供 `--smoke-test` 模式快速回归，训练脚本内置日志。
- **Super Mario / Stickman**：暂未提供自动化测试，需要通过快速通关、资源加载、输入回放进行人工冒烟；建议在后续迭代补充 pytest 框架。

测试通过是合并修改前的硬性要求；如因环境差异产生告警（例如 `pkg_resources` 弃用），请记录并评估是否需要抑制或升级依赖。

---

## 贡献流程

1. 新建分支，遵循 PEP 8 与项目现有代码风格；单文件长度保持在 1000 行以内。
2. 修改前阅读本 README，确保文档同步更新；禁止新增其他说明文档。
3. 执行针对性测试（至少包含 StreetBattle 冒烟测试，或模块专属测试）。
4. 在提交信息中记录变更动机、测试结果和外部资源来源。
5. 提交 PR 前检查依赖、脚本、资源是否随改动同步更新。

---

## 许可证与资源来源

- **代码**：遵循仓库根目录许可。
- **StreetBattle 精灵**：Martial Hero（LuizMelo，CC0 1.0），许可证存放于 `streetBattle/assets/sprites/LICENSE_martial_hero.txt`。
- **UI/音效**：Kenney UI Pack、NumPy/SciPy 生成音效（CC0 或 MIT），详情见各资产目录。
- **3D 模型 & 肖像**：resource manager / portrait pipeline 生成，保留来源与授权信息于 `assets/ATTRIBUTION.md`。

引入新素材前需确认授权可再分发，并在资源目录附上来源、许可证及更新时间。
