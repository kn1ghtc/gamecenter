# Game Center 开发手册

> 最后更新：2026-01-24（北京时间）

Game Center 集成了十一款 Python 游戏（Chess、Gomoku、Military Chess、StreetBattle、Eco Grassland、Stickman Game、Super Mario、Tank Battle、Tetris、Alien Invasion、Delta Operation），并提供 Web 游戏中心平台和 **Pygame 统一启动器**，统一了资源治理、测试流程和运维策略。本手册作为唯一权威文档，对整体环境、各子模块特性、常用脚本与质量保证手段进行系统说明，便于团队协同维护与版本迭代。

## 目录

- [Game Center 开发手册](#game-center-开发手册)
  - [目录](#目录)
  - [项目概览](#项目概览)
  - [目录结构](#目录结构)
  - [环境准备](#环境准备)
    - [macOS（Homebrew + zsh）快速开始](#macoshomebrew--zsh快速开始)
  - [运行方式概览](#运行方式概览)
  - [Pygame 游戏启动器](#pygame-游戏启动器)
  - [Web 游戏中心 (webGameCenter)](#web-游戏中心-webgamecenter)
  - [游戏模块总览](#游戏模块总览)
    - [Chess（国际象棋）](#chess国际象棋)
    - [Gomoku（五子棋）](#gomoku五子棋)
    - [Military Chess（中国军棋）](#military-chess中国军棋)
    - [StreetBattle（街头格斗）](#streetbattle街头格斗)
    - [Eco Grassland（生态平衡模拟）](#eco-grassland生态平衡模拟)
    - [Stickman Game（火柴人冒险）](#stickman-game火柴人冒险)
    - [Super Mario Bros（超级玛丽）](#super-mario-bros超级玛丽)
    - [Tank Battle（坦克大战）](#tank-battle坦克大战)
    - [Tetris（俄罗斯方块）](#tetris俄罗斯方块)
    - [Alien Invasion（外星人入侵）](#alien-invasion外星人入侵)
    - [Delta Operation（三角洲行动）](#delta-operation三角洲行动)
  - [工具与自动化脚本](#工具与自动化脚本)
  - [质量保障与测试](#质量保障与测试)
  - [贡献流程](#贡献流程)
  - [许可证与资源来源](#许可证与资源来源)

---

## 项目概览

- **定位**：单一仓库存放多款可独立运行的游戏项目，与资源、工具脚本共享。
- **目标平台**：Windows 11，PowerShell 为默认终端；Python 3.12+ 是推荐运行时。macOS、Linux 同样支持。
- **核心依赖**：Pygame、Panda3D、LangChain、Pillow、Requests、NumPy/SciPy、PyTorch、Flask 等。
- **资源策略**：全部素材保持合法来源（CC0/CC-BY 等），通过脚本自动校验与同步，避免占位资产。

---

## 目录结构

```
gamecenter/
├─ README.md                 # 本文档（唯一项目文档）
├─ pygame_launcher.py        # 🆕 Pygame 游戏统一启动器
├─ game_progress.json        # 游戏进度记录文件（自动生成）
├─ webGameCenter/            # Web网页游戏中心（Flask + HTML5）
├─ chess/                    # 国际象棋 + AI 陪伴系统
├─ gomoku/                   # 五子棋 + 三级智能 AI
├─ militaryChess/            # 中国军棋（陆战棋）+ 智能 AI
├─ streetBattle/             # 3D/2.5D 格斗平台
├─ Eco_grassland/            # 生态平衡教学模拟器
├─ stickman_game/            # 火柴人动作冒险
├─ superMario/               # 超级玛丽平台跳跃
├─ tankBattle/               # 坦克大战 + 强化学习 AI
├─ tetris/                   # 俄罗斯方块增强版（100关卡）
├─ alien_invasion/           # 外星人入侵射击游戏（双人模式）
├─ deltaOperation/           # 三角洲行动横版射击（支持双人）
└─ __init__.py               # 包初始化文件
```

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
2. **推荐方式**：使用 Pygame 统一启动器
   ```powershell
   python pygame_launcher.py
   ```
3. 或根据目标游戏进入其子目录并执行主入口：
   - Chess：`python chess/main.py`（或 `python -m chess.game`）
   - Gomoku（五子棋）：`cd gomoku; python main.py` 或 `python -c "from gamecenter.gomoku import run_game; run_game()"`
   - Military Chess（军棋）：`cd militaryChess; python main.py` 或 `python -c "from gamecenter.militaryChess import run_game; run_game()"`
   - StreetBattle：`cd streetBattle; python main.py`
   - Eco Grassland：`cd Eco_grassland; python main.py`
   - Stickman Game：`cd stickman_game; python main.py`
   - Super Mario：`cd superMario; python main.py`
   - Tank Battle：`cd tankBattle; python main.py`
   - Tetris：`cd tetris; python main.py`
   - Alien Invasion：`cd alien_invasion; python alien_invasion.py`
   - Delta Operation：`cd deltaOperation; python main.py`
4. 如需运行工具或测试，参见相应章节。

---

## Pygame 游戏启动器

**概览**：统一的 Pygame 游戏中心界面，整合所有 11 款 Pygame 游戏。提供游戏分类浏览、进度记录和快捷启动功能。

**功能特性**
- ✅ **统一界面**：现代化的游戏选择界面
- ✅ **分类过滤**：按类型（策略/动作/射击/益智/模拟）筛选游戏
- ✅ **进度记录**：自动记录游玩次数和最高分
- ✅ **键盘导航**：方向键选择，Enter 启动，Esc 退出
- ✅ **11 款游戏**：
  - 🧠 策略游戏：中国象棋、五子棋、军旗
  - ⚡ 动作游戏：超级玛丽、街头霸王、火柴人格斗
  - 🎯 射击游戏：坦克大战、三角洲行动、外星人入侵
  - 🧩 益智游戏：俄罗斯方块
  - 🌍 模拟游戏：生态草原

**快速开始**
```powershell
cd gamecenter
python pygame_launcher.py
```

**快捷键**
| 按键 | 功能 |
|------|------|
| ↑/↓ | 选择游戏 |
| Enter | 启动游戏 |
| 1-5 | 过滤类别（1:策略 2:动作 3:射击 4:益智 5:模拟） |
| 0 | 显示全部游戏 |
| Esc | 退出启动器 |

---

## Web 游戏中心 (webGameCenter)

**概览**：现代化的网页游戏平台，基于 Flask 后端 + HTML5 前端，集成多款经典网页小游戏。提供完整的用户管理、游戏分类、积分排行系统。

> **注意**：KOF、俄罗斯方块、坦克大战已移至 Pygame 版本，Web 版本不再维护这三款游戏。

**核心功能**
- ✅ **用户系统**：注册、登录、资料编辑（JWT 认证）
- ✅ **游戏中心**：分类浏览、在线游戏、进度保存
- ✅ **排行系统**：全球排行榜、游戏排行、个人排名
- ✅ **游戏列表**：
  - 🎮 动作游戏：魂斗罗 (Contra)
  - 🎯 射击游戏：太空射击
  - 🎰 益智游戏：2048、推箱子、扫雷、打砖块
  - 🐍 街机游戏：贪吃蛇
  - 🦅 休闲游戏：飞鸟、恐龙跑酷、吃豆人

**快速开始**
```powershell
cd gamecenter/webGameCenter
pip install -r requirements.txt
python run.py
# 访问 http://localhost:5000
```

**项目结构**
```
webGameCenter/
├─ app.py                   # Flask 主应用
├─ config.py                # 配置与游戏定义
├─ run.py                   # 启动脚本
├─ requirements.txt         # Python 依赖
├─ backend/
│  ├─ database/db.py       # SQLAlchemy 数据模型
│  └─ routes/
│     ├─ auth.py           # 认证 API
│     ├─ games.py          # 游戏 API
│     └─ scores.py         # 积分 API
└─ frontend/
   ├─ index.html           # 首页
   ├─ login.html           # 登录页
   ├─ game.html            # 游戏容器
   ├─ leaderboard.html     # 排行榜
   ├─ dashboard.html       # 个人中心
   ├─ css/style.css        # 样式表
   ├─ js/api.js            # API 客户端
   ├─ js/ui.js             # UI 工具函数
   ├─ js/main.js           # 主应用逻辑
   └─ games/               # 5+ 款游戏
      ├─ action/
      ├─ shooting/
      ├─ arcade/
      ├─ puzzle/
      └─ casual/
```

**API 文档**
- 认证：`POST /api/auth/register`, `POST /api/auth/login`
- 游戏：`GET /api/games/categories`, `GET /api/games/list`
- 记录：`POST /api/games/record`, `GET /api/games/records`
- 排名：`GET /api/scores/leaderboard`, `GET /api/scores/game/<id>`

**前端框架**
- Bootstrap 5：响应式设计
- Vanilla JavaScript：轻量级交互
- Canvas 2D：游戏渲染
- JWT：客户端认证

**后端栈**
- Flask 3.0：Web 框架
- SQLAlchemy 2.0：ORM
- Flask-JWT-Extended：认证
- SQLite/PostgreSQL：数据库

**文档**
- `README.md`：完整项目文档
- `QUICKSTART.md`：5分钟快速开始
- `TECHNICAL.md`：技术实现细节
- `COMPLETION_REPORT.md`：项目交付清单
- `verify_setup.py`：环境验证脚本

**部署**
```powershell
# 验证环境
python verify_setup.py

# 数据库初始化
python manage.py init_db

# 生产启动
set FLASK_ENV=production
python run.py --host 0.0.0.0 --port 8000
```

详见 `webGameCenter/QUICKSTART.md` 和 `webGameCenter/README.md`。

---

## 游戏模块总览

### Chess（国际象棋）

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

### Gomoku（五子棋）

**概览**：专业级五子棋游戏，搭载三级难度AI（Minimax + Alpha-Beta剪枝）、棋型识别系统（12种棋型）和现代化自适应UI。支持悔棋、存档、全屏模式，提供流畅的人机对战体验。

**核心特性**
- **三级智能AI**：简单（3层搜索）、中等（5层+Alpha-Beta剪枝）、困难（7层+迭代加深+历史启发）。
- **棋型识别**：五连、活四、冲四、活三、眠三等12种基础棋型，精准评估局面优劣。
- **自适应布局**：默认窗口 900×800，调整尺寸或全屏时自动重排棋盘与侧边栏。
- **3D棋子渲染**：渐变阴影与高光效果，模拟真实棋子质感。
- **悔棋系统**：默认3次悔棋机会，每次悔2步（玩家+AI）。
- **存档/读档**：JSON格式保存完整棋局状态（棋盘、历史、当前玩家）。
- **算法优化**：评估缓存、历史启发、邻域搜索、着法排序，大幅提升AI响应速度。
- **会话保存**：保存棋局时同步保存配置与积分，下次启动自动恢复上次进度。

**最新更新（2025-10-11）**
- UI 背景升级为渐变纹理，棋盘面板自动按窗口宽度分配空白空间，居中展示效果更佳。
- 全屏/窗口尺寸调整时保留按钮状态与布局配色，避免重新创建导致的样式闪烁。
- 棋盘背景新增预生成高光与阴影图层，提升棋子层次感并减少实时混合开销。

**运行方式**
```powershell
# 方式 1：直接运行
cd gamecenter/gomoku
python main.py

# 方式 2：包导入运行
python -c "from gamecenter.gomoku import run_game; run_game()"
```

**控制说明**
- **鼠标左键**：在空位落子
- **U键**：悔棋（撤销玩家和AI最后各一步）
- **R键**：重新开始游戏
- **F11**：切换全屏模式
- **ESC**：退出游戏
- **UI按钮**：新游戏、悔棋、切换AI难度

**技术架构**
- `main.py`：游戏主循环、事件处理、AI集成（320行）
- `game_logic.py`：棋盘表示、胜负检测、悔棋系统（485行）
- `ai_engine.py`：Minimax搜索、难度控制、着法生成（386行）
- `evaluation.py`：棋型识别、局面评估、缓存优化（398行）
- `ui_manager.py`：自适应布局、棋盘渲染、动画系统（450行）
- `font_manager.py`：跨平台中文字体管理（130行）
- `config/`：游戏常量、UI配置、音效生成脚本
- `assets/`：音效文件（自动生成）、图标资源

**测试与质量保证**
```powershell
# 完整冒烟测试（22个测试用例）
cd gamecenter/gomoku
$env:SDL_VIDEODRIVER='dummy'; $env:SDL_AUDIODRIVER='dummy'; pytest test_smoke.py -v

# 测试覆盖类别：
# - 棋盘逻辑（8个）：初始化、落子、胜负检测（横竖斜）、和棋、悔棋
# - 游戏管理（2个）：悔棋限制、游戏重置
# - AI引擎（3个）：着法合法性、必胜着法识别、性能测试
# - 评估系统（3个）：评估器初始化、初始局面、获胜局面
# - 字体管理（5个）：初始化、字体获取、回退机制、渲染、尺寸
# - 存档系统（1个）：保存与加载完整性
```

**AI性能指标**
| 难度 | 搜索深度 | 平均耗时 | 算法特性 |
|-----|---------|---------|---------|
| 简单 | 3层 | <0.5秒 | 基础Minimax |
| 中等 | 5层 | 1-3秒 | Alpha-Beta剪枝 |
| 困难 | 7层 | 3-10秒 | 迭代加深+历史启发 |

**版本说明**
- **v1.0.0 (2025-01)**：首个稳定版本，完整五子棋规则、三级AI、自适应UI、音效系统、完整测试覆盖。
- **后续计划**：联机对战、复盘系统、开局库、神经网络AI（MCTS/深度学习）、禁手规则。

---

### Military Chess（中国军棋）

**概览**：完整的中国军棋（陆战棋）实现，具备智能 AI 对手与现代化 Pygame 界面。采用模块化架构，分离游戏逻辑、AI 引擎和评估函数,支持多种运行方式。

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

### StreetBattle（街头格斗）

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

### Eco Grassland（生态平衡模拟）

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

### Stickman Game（火柴人冒险）

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

### Super Mario Bros（超级玛丽）

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

### Tank Battle（坦克大战）

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

### Tetris（俄罗斯方块）

**概览**：增强版俄罗斯方块游戏，具有精美的3D效果、粒子特效和100关卡系统。使用Pygame开发，支持音效和背景音乐。

**核心特性**
- **100关卡系统**：从简单到极致挑战，关卡越高速度越快
- **智能分数系统**：单行、双行、三行、四行消除不同得分，支持连击加分
- **自适应屏幕**：根据屏幕分辨率自动调整窗口大小和方块尺寸
- **幽灵方块**：实时显示方块将要落在哪里，便于精确操作
- **3D方块渲染**：渐变色、高光、阴影效果，视觉更立体
- **粒子特效**：消除方块时的爆炸粒子效果
- **动画效果**：消行动画、升级通知、连击提示
- **SRS旋转系统**：支持Wall Kick墙踢操作
- **音效系统**：背景音乐、移动、旋转、消除、升级、游戏结束等音效

**运行方式**
```powershell
cd gamecenter/tetris
python main.py
```

**控制说明**
| 按键 | 功能 |
|------|------|
| ← / → | 左右移动方块 |
| ↓ | 软下落（缓慢下落，每格得1分） |
| Space | 硬下落（瞬间落到底部，每格得2分） |
| ↑ / Z | 顺时针旋转方块 |
| P | 暂停/继续游戏 |
| R | 重新开始游戏 |
| Esc | 退出游戏 |

**评分规则**
- 单行消除：100分 × 关卡数
- 双行消除：300分 × 关卡数
- 三行消除：500分 × 关卡数
- 四行消除（Tetris）：800分 × 关卡数
- 连击加成：连续消除时得分 × (1 + (连击数-1) × 0.5)

**项目结构**
- `main.py`：游戏入口文件
- `src/game_enhanced.py`：主游戏逻辑（100关卡系统）
- `src/tetromino.py`：方块类（SRS旋转系统、3D渲染）
- `src/board.py`：游戏板类（碰撞检测、消行动画、粒子效果）
- `src/ui_renderer.py`：UI渲染模块（面板、背景、动画）
- `src/sound_manager.py`：音效管理器
- `assets/`：音效和图片资源（CC0授权）

**测试**
```powershell
cd gamecenter/tetris
pytest tests/ -v
```

---

### Alien Invasion（外星人入侵）

**概览**：经典太空射击游戏，支持双人模式。玩家控制飞船射击入侵的外星人舰队，具备完整的音效系统和分数系统。

**核心特性**
- **双人对战模式**：支持两名玩家同时游戏
- **外星人舰队AI**：舰队移动、边缘检测、下降攻击
- **音效系统**：射击、爆炸、背景音乐等音效
- **分数系统**：击杀计分、关卡升级、速度递增
- **生命系统**：多条生命、碰撞检测
- **Play按钮**：鼠标点击开始游戏

**运行方式**
```powershell
cd gamecenter/alien_invasion
python alien_invasion.py
```

**控制说明**
| 玩家 | 操作 | 键位 |
|------|------|------|
| 玩家1 | 左/右移动 | A / D |
| 玩家1 | 上/下移动 | W / S |
| 玩家1 | 射击 | 空格 |
| 玩家2 | 左/右移动 | ← / → |
| 玩家2 | 上/下移动 | ↑ / ↓ |
| 玩家2 | 射击 | Enter |
| 通用 | 退出 | Q |

**项目结构**
- `alien_invasion.py`：游戏主入口和游戏循环
- `settings.py`：游戏配置（屏幕、飞船、子弹、外星人参数）
- `ship.py`：飞船类（移动、绘制）
- `bullet.py`：子弹类（移动、碰撞）
- `alien.py`：外星人类（移动、边缘检测）
- `game_stats.py`：游戏统计（分数、生命、关卡）
- `scoreboard.py`：分数显示
- `sound_manager.py`：音效管理
- `button.py`：UI按钮
- `images/`：游戏图像资源
- `sounds/`：音效文件

---

### Delta Operation（三角洲行动）

**概览**：横版射击动作游戏，支持单人和双人模式。包含多种武器、敌人类型、关卡系统、完整动画系统和存档功能。

**核心特性**
- **完整动画系统**：12种动画状态（待机、行走、奔跑、跳跃、下落、蹲伏、射击、换弹、受击、死亡、近战、攀爬），平滑过渡
- **增强视觉效果**：枪口火焰、血液溅射、弹壳抛出、爆炸粒子
- **双人协作模式**：支持本地双人游戏，各自独立控制
- **武器系统**：M9手枪、M4A1步枪、M24狙击枪、M870霰弹枪
- **敌人系统**：普通敌人、精英敌人、Boss，智能AI状态机
- **物理系统**：重力、跳跃、空中控制
- **存档系统**：快速保存（F5）和快速读取（F9）
- **小地图**：实时显示玩家和敌人位置
- **屏幕震动**：战斗反馈效果

**运行方式**
```powershell
cd gamecenter/deltaOperation
python main.py                    # 正常窗口模式
python main.py --multiplayer      # 启用双人模式
python main.py --headless         # 无头测试模式
python main.py --smoke-test --frames 300  # 冒烟测试
```

**控制说明**
| 玩家1 | 操作 | 玩家2 |
|-------|------|-------|
| A / D | 左右移动 | ← / → |
| W | 跳跃 | ↑ |
| S | 下蹲 | ↓ |
| 空格 | 射击 | RCtrl |
| R | 换弹 | . |
| Q | 切换武器 | / |
| ESC | 暂停 | ESC |

**调试快捷键**
| 按键 | 功能 |
|------|------|
| F1 | 小地图开关 |
| F2 | 放大(2x) |
| F3 | 正常(1x) |
| F4 | 屏幕震动 |
| F5 | 快速保存 |
| F9 | 快速读取 |

**项目结构**
- `main.py`：游戏入口、参数解析
- `config.py`：游戏配置（窗口、玩家、武器、敌人、控制）
- `core/game_state.py`：游戏状态管理
- `core/player.py`：玩家角色（集成AnimationController）
- `core/enemy.py`：敌人AI（智能状态机 + 动画系统）
- `core/animation_system.py`：完整动画状态机（12状态、平滑过渡、动态精灵生成）
- `core/weapon.py`：武器系统
- `core/physics.py`：物理引擎
- `core/level_manager.py`：关卡管理
- `core/gameplay_scene.py`：场景协调（粒子效果集成）
- `utils/enhanced_visuals.py`：增强粒子系统（枪口火焰、血液、弹壳、爆炸）
- `ui/`：用户界面组件
- `assets/`：游戏资源
- `saves/`：存档目录

**测试**
```powershell
cd gamecenter/deltaOperation
python main.py --smoke-test --frames 300
```

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

- **Chess（国际象棋）**：`python -m pytest chess/tests` 覆盖 GUI、规则、AI 接口；训练脚本支持离线验证。
- **Gomoku（五子棋）**：`cd gomoku; pytest test_smoke.py -v` 验证棋盘逻辑、AI引擎、评估系统、字体管理、存档系统（22个测试用例，100%通过率）。
- **Military Chess（军棋）**：`python test_smoke.py` 验证游戏逻辑、AI 引擎和包导入；支持直接运行和包导入两种方式的测试。
- **StreetBattle（街头格斗）**：`python -m pytest streetBattle/tests/test_smoke.py`（验证 manifest、技能、设置）；建议定期运行 `test_combat.py` 和 `test_rollback_sim.py`。
- **Eco Grassland（生态模拟）**：人工冒烟测试，通过运行 `cd Eco_grassland; python main.py` 验证生态压力、进食与饮水逻辑。
- **Tank Battle（坦克大战）**：提供 `--smoke-test` 模式快速回归，训练脚本内置日志。
- **Tetris（俄罗斯方块）**：`cd tetris; pytest tests/ -v` 验证游戏逻辑、方块旋转、碰撞检测、消行动画。
- **Alien Invasion（外星人入侵）**：人工冒烟测试，通过快速通关验证游戏流程。
- **Delta Operation（三角洲行动）**：`python main.py --smoke-test --frames 300` 快速回归测试。
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
- **Tetris 音效**：OpenGameArt "512 Sound Effects (8-bit style)" by Juhani Junkala (CC0)，背景音乐 FreePD "Bit Bit Loop" by Kevin MacLeod (CC0)。
- **UI/音效**：Kenney UI Pack、NumPy/SciPy 生成音效（CC0 或 MIT），详情见各资产目录。
- **3D 模型 & 肖像**：resource manager / portrait pipeline 生成，保留来源与授权信息于 `assets/ATTRIBUTION.md`。

引入新素材前需确认授权可再分发，并在资源目录附上来源、许可证及更新时间。
