# Game Center 项目集合

这是一个游戏开发项目集合，包含多个经典游戏的 Python 实现。

## 项目列表

### 🎮 超级玛丽兄弟 (Super Mario Bros)
- **位置**: `superMario/`
- **状态**: ✅ 完成
- **特色**: 30关卡、积分系统、声音效果、背景音乐（支持切换）、自动资源下载、继续/关卡选择、中英双语支持、中文字体跨平台回退（Windows/macOS/Linux）、UI文字阴影+描边美化、3D卡通风格精灵（自动生成）、统一配置系统
- **运行**: `cd superMario; python main.py`

#### 常用按键
- `Enter`: 开始游戏
- `↑/↓`: 菜单选择
- `Q`: 退出游戏
- `M`: 切换背景音乐 开/关
- `P`: 暂停/继续
- `←/→`: 关卡选择页切换关卡

### ♟️ 国际象棋 (Chess)
- **位置**: `chess/`
- **状态**: 开发中

### 🏃 跑酷游戏 (Stickman Game)
- **位置**: `stickman_game/`
- **状态**: 开发中

### 🚀 超级玛丽 (Super Mario)
- **位置**: `superMario/`
- **状态**: ✅ 完成

### ⚔️ 坦克大战 (Tank Battle)
- **位置**: `tankBattle/`
- **状态**: 开发中

## 技术栈

- **Python 3.8+**
- **Pygame** - 游戏开发框架
- **Pillow** - 图像处理
- **Requests** - 网络请求
- **NumPy + SciPy** - 程序化音效合成（WAV）

## 开发环境

```powershell
# 安装基础依赖（Windows PowerShell）
python -m pip install -U pip; pip install pygame pillow requests numpy scipy

# 运行超级玛丽
cd superMario; python main.py
```

### 字体与资源说明
- 中文字体优先使用 `assets/fonts/chinese_font.otf`，若加载异常，则自动回退到系统字体（Windows: `msyh.ttc`/`simhei.ttf` 等；macOS: `PingFang.ttc` 等；Linux: `WenQuanYi`/`Noto CJK` 等）。
- 文本渲染默认带阴影与描边，确保中文在浅/深背景下都清晰可读。
- 资源下载失败时，下载器会自动生成 3D 卡通风格的本地资源：
	- `assets/images/mario.png`、`tiles.png`（包含地面+管道）、`enemy.png`、`coin.png`、`powerup.png`、`goal.png`
	- `assets/sounds/*.wav` 音效与 `background_music.wav` 由 NumPy/SciPy 合成，不为空，兼容 `pygame.mixer`；若在线音乐下载失败会使用该本地合成BGM。

### 存档与关卡
- 首次运行会在 `levels/` 下自动生成 30 个关卡（程序化生成，固定种子保证稳定性）。
- 主菜单包含 “继续游戏 / 新游戏 / 关卡选择 / 退出”。存在 `assets/savegame.json` 时显示“继续游戏”。
- 游戏进行中会在过关或失去生命时自动保存进度（关卡、分数、生命、剩余时间）。

### 统一配置
- 配置文件：`assets/config.json`（可选）。
- 默认值位于 `src/config.py`。可覆盖项：
	- `game.max_levels`、`game.initial_lives`、`game.time_per_level`、`game.music_enabled`
	- `player.speed`、`player.jump_force`、`player.gravity`、`player.max_fall_speed`
	- `player.skills.double_jump`、`player.skills.dash`

## 贡献

欢迎为任何游戏项目贡献代码！请确保：
- 代码符合 PEP 8 规范
- 添加适当的注释和文档
- 测试游戏功能正常

## 许可证

各项目采用相应开源许可证。