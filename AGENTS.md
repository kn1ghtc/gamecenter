# gamecenter - AI Development Guidelines (AGENTS.md)

> **项目**: 多游戏平台（11 款游戏 + Web 游戏中心）  
> **更新时间**: 2026-02-07 (Beijing Time, UTC+8)

---

## 📌 项目定位

gamecenter 是一个多游戏集成平台，包含 11 款独立游戏和 1 个 Web 游戏中心，使用 Pygame 统一启动器管理。

---

## 📁 目录结构

```
gamecenter/
├── pygame_launcher.py       # Pygame 统一启动器入口
├── game_progress.json       # 游戏进度存储
├── README.md                # 项目文档（唯一权威）
├── alien_invasion/          # 外星人入侵
├── chess/                   # 中国象棋（AI Agent + 语音）
├── deltaOperation/          # 三角洲行动
├── Eco_grassland/           # 生态草原模拟
├── gomoku/                  # 五子棋（AI对弈）
├── militaryChess/           # 军棋（暗棋模式）
├── stickman_game/           # 火柴人格斗
├── streetBattle/            # 街霸（2.5D/3D 双模式）
├── superMario/              # 超级马里奥（30关）
├── tankBattle/              # 坦克大战（强化学习）
├── tetris/                  # 俄罗斯方块
└── webGameCenter/           # Web 游戏中心
```

---

## 🔧 核心开发规范

### 1. 导入与包管理

- **绝对导入**：所有游戏使用 `from gamecenter.<game> import ...`，禁止相对导入
- **每个游戏目录**必须有 `__init__.py`，导出 `run_game()` 等核心函数
- **根 `__init__.py`** 维护完整的 `__all__` 列表

### 2. 入口点模式

```python
# gamecenter/<game>/main.py
def main():
    """游戏主入口"""
    ...

if __name__ == "__main__":
    main()
```

- 每个游戏的 `main.py` 同时支持直接执行和包导入
- 启动器通过 `pygame_launcher.py` 统一管理所有游戏

### 3. 渲染与字体

- **UTF-8 强制**：入口文件设置 `os.system("chcp 65001 >nul 2>&1")`
- **字体回退链**：PingFang SC → Microsoft YaHei → Noto Sans CJK → System default
- **资源策略**：首次运行自动下载；所有资源必须 CC0/CC-BY 授权

### 4. 测试规范

- **全自动化**：所有 smoke test 禁止手动交互
- **Headless 渲染**：使用 `SDL_VIDEODRIVER=dummy` + `SDL_AUDIODRIVER=dummy`
- **Fixture 模式**：`@pytest.fixture(scope="module", autouse=True)` 初始化 pygame
- **测试目录**：各游戏 `<game>/tests/` 存放游戏专属测试
- **模拟输入**：使用 `monkeypatch` 或 `pyautogui`，禁止等待用户点击

```powershell
# Headless smoke test
$env:SDL_VIDEODRIVER="dummy"; $env:SDL_AUDIODRIVER="dummy"
python .\gamecenter\tankBattle\main.py --smoke-test --frames 300
```

### 5. 游戏专属模式

| 游戏 | 技术特点 | 关键依赖 |
|------|---------|---------|
| **chess** | LangChain AI Agent + ChromaDB 记忆 + 语音 I/O | whisper, TTS |
| **militaryChess** | Negamax + 暗棋模式 + 多线程 AI | pygame |
| **tankBattle** | DQN 强化学习 + 存档系统 | PyTorch |
| **superMario** | 30 关卡 + 自动资源下载 + 程序化关卡生成 | pygame |
| **streetBattle** | Panda3D 3D / Pygame 2.5D 双模式 | panda3d |
| **gomoku** | Minimax AI + α-β 剪枝 | pygame |
| **webGameCenter** | Web 版游戏中心 | Flask/JS |

---

## 🚨 禁止事项

1. ❌ 禁止使用 `print()` 调试——使用 `logging`
2. ❌ 禁止在测试中要求手动交互
3. ❌ 禁止硬编码文件路径——使用 `Path(__file__).parent` 相对路径
4. ❌ 禁止提交二进制资源文件（音频/图片）到 Git——用 `.gitignore` 排除
5. ❌ 禁止使用 `import pygame` 在模块顶层无保护——须在函数内或 try/except 中导入
