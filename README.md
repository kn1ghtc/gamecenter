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
- **状态**: ✅ 基础完成，AI陪伴功能已实现
- **特色**: 
  - 完整国际象棋游戏规则
  - 多级AI难度：Easy/Medium/Hard/GPT AI
  - **🆕 Chess AI Agent v2.0 - 超级智能陪伴助理**
    - ChromaDB/LanceDB向量记忆系统（RAG）
    - OpenAI语音陪伴聊天功能
    - MCP工具集成（网络搜索、学术研究）
    - 自主任务规划和执行
    - 个性化AI助理（友好导师、竞技专家、耐心教师、休闲朋友）
    - 持久化游戏记忆和学习经验
- **运行**: `cd chess; python game.py`

#### Chess AI Agent v2.0 功能亮点
- **🧠 智能记忆**: 使用ChromaDB存储游戏历史、对话记录、策略学习
- **🗣️ 语音陪伴**: OpenAI TTS/STT或本地语音引擎，实时语音交流
- **🔧 工具集成**: MCP服务（深度研究、网络搜索、代码分析等）
- **📋 自主规划**: 根据游戏情况自动规划和执行任务
- **🎭 个性定制**: 4种AI个性，适应不同用户需求
- **💾 持久化**: 所有交互和学习都会保存，持续改进

#### 测试状态
- **总测试通过率**: 100% (7/7通过) ✅
- ✅ Agent适配器创建和接口：完全正常
- ✅ Agent聊天同步功能：智能对话正常
- ✅ Agent创建和基础功能：核心功能稳定
- ✅ 错误处理：异常恢复机制正常
- ✅ 记忆持久化：ChromaDB向量存储正常
- ✅ 记忆系统基础：向量搜索功能正常
- ✅ 移动生成：智能决策和解释正常

#### 最新修复 (v2025.09.22)
- 🔧 **OpenAI嵌入**: 修复SSL证书问题，正确配置API调用
- 🔧 **资源清理**: 完善ChessPlanningEngine清理机制
- 🔧 **临时文件**: 改进Windows平台文件删除逻辑
- 🔧 **API现代化**: 更新LangChain导入，消除弃用警告
- 🔧 **向量存储**: 恢复完整ChromaDB向量功能
 - 🖥️ **UI 自适应**: 棋盘界面默认 1024×768，窗口可调整大小；右侧信息/历史/吃子面板与按钮区域自适应布局。语音与问答按钮固定在界面可视范围内，不会被遮挡。
 - ⚡ **性能优化**: 记忆系统支持快速启动（延迟初始化向量库），减少首次加载卡顿；移除启动阶段数据一致性校验。
 - 🗣️ **语音增强**: 走子语音包含“棋子名称+起止位置+简要理由”；新增“语音聊天”引导提示、一次性听写并播报AI回复。
 - 🔔 **提示气泡**: 语音与问答操作时在右上角显示Toast（开始说话、AI思考、AI播报中）。

#### 语音与问答使用说明（陪伴模式）
- 进入方式: 主菜单点“与 AI（Companion）对战”。
- `Voice Chat` 按钮:
  - 点击后会播报提示“请在提示音后说话，三秒内结束”。
  - 系统监听一次你的简短语音（2-3秒），自动结束并识别。
  - AI 会用语音播报和文字同时响应。
- `Ask` 按钮:
  - 点击会发送一条预设或自定义问题给AI并显示回答（文本，同时尝试语音播报）。
- 提示信号:
  - 开始说话: 有语音提示文案；
  - 结束说话: 录音自动停止并转入识别；
  - AI播报: 语音输出播放期间不可重复触发；播放结束后可继续操作。
- 常见问题:
  - 若无麦克风或系统语音库不可用，将回退为文本问答；
  - 若OpenAI TTS不可用，会自动使用系统TTS或静默回退；
  - 网络/证书问题导致向量库不可用时，RAG自动降级为本地关键词检索。

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