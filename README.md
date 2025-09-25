# 🥊 StreetBattle 3D格斗游戏

> 受KOF97启发，基于Panda3D引擎的3D/2.5D街头格斗游戏，支持本地与局域网对战，具备回滚同步、真实3D资源、现代化UI与粒子特效。

- **位置**: `streetBattle/`
- **状态**: ✅ 完整可玩，支持角色选择、游戏模式选择、本地/局域网对战、combo连击、现代化UI设计
- **最新更新 2025-12-30**: �️ **完成全面系统修复与资源重组**
  - ✅ **占位符修复**: 发现并修复84+个GLTF占位符文件（仅2KB JSON元数据）
  - ✅ **纹理修复**: 修复333个损坏纹理文件（0x5c 0x78错误头→标准JPEG格式）
  - ✅ **资源重组**: 移动误放资产到正确目录（win.ogg/lose.ogg→audio/music/，particle.png→images/effects/）
  - ✅ **模型生成系统**: 创建SimpleModelGenerator生成几何模型作为占位符角色
  - ✅ **角色管理器重构**: FixedEnhancedCharacterManager智能回退：BAM→简单模型→Arena FPS→空节点
  - ✅ **音频清理增强**: 完善OpenAL清理机制，防止AL lib关闭警告
  - ✅ **功能验证**: 5/5测试通过，游戏可正常启动和角色加载
  - ✅ **系统稳定性**: 修复所有警告，实现优雅的资源清理和错误处理
- **特色**:
  - **现代化UI设计**: 基于Street Fighter/KOF标准的专业格斗游戏界面
    - 顶部水平血条布局（左右对称）
    - 中央倒计时器与回合信息
    - 现代渐变色彩方案与动画效果
    - 符合行业标准的HUD元素定位
    - 已移除任何半透明/不透明遮挡层（确认日志：[HUD] ... alpha=0）
  - **完整的玩家控制系统**: 
    - WASD移动、空格/鼠标攻击、J跳跃
    - 组合技能系统（如：右+轻攻击 = 突进技）
    - 实时输入调试与反馈系统
  - **真实3D角色与场景资源**（`assets/`目录，支持自定义替换）  
  - **🆕 智能角色系统**：FixedEnhancedCharacterManager支持多层级回退（占位GLTF检测→几何模型生成→BAM fallback→Arena FPS备用）
  - **🆕 简单模型生成器**：SimpleModelGenerator可生成基础几何体（盒子/圆柱）作为角色占位符，支持材质着色
  - **🆕 纹理修复工具**：TextureRepairTool自动检测并修复损坏JPEG文件（0x5c 0x78→标准JPEG头）
  - **🆕 资源重组器**：AssetReorganizer自动整理误放资产到正确目录结构
  - **完整的游戏模式选择**（冒险、对战、网络模式）
  - **20个KOF97风格角色**可选，支持键盘和鼠标双重选择方式
  - **Panda3D高性能渲染**，动态光影、摄像机抖动、粒子/光晕/击中特效
  - **回滚同步系统**：主机端保存状态历史，客户端预测+重放，支持高延迟下的流畅对战
  - **音效/音乐系统**：真实BGM与SFX，支持自定义
  - **支持本地AI对战、局域网主机/客户端对战**

## 🎨 优化的单层级资源系统
### **角色模型** (88个KOF角色，单层级Sketchfab)
- **📁 位置**: `assets/characters/[角色名]/sketchfab/` 
- **主模型格式**: GLTF/GLB高质量社区资源（7.88GB总容量）
  - `kyo_kusanagi.gltf` + `kyo_kusanagi.bin` (完整模型+动画数据)
  - 包含纹理、材质、动画序列的完整3D资源包
- **优化特性**: 
  - 单层级查找（无需多tier fallback），加载速度更快
  - 统一的Sketchfab质量标准，视觉效果一致
  - Enhanced Character Manager自动检测最佳资源格式
- **支持角色**: 完整KOF系列88个经典角色

### **🎵 整合音效系统**
- **📁 统一位置**: `assets/audio/` (所有音频文件集中管理)
- **高质量音效**: 44.1kHz WAV/OGG文件，总容量500KB
  - `bgm_loop.ogg` (104KB) - 循环背景音乐
  - `hit.wav` (35KB) - 基础打击音效
  - `combo_enhanced.wav` (43KB) - 连击增强音效  
  - `victory_enhanced.wav` (86KB) - 胜利音效
  - `lose.ogg` (7.5KB) - 失败音效（下降颤音）
- **背景音乐**: `bgm_loop.ogg` - 循环播放的格斗主题音乐

### **💥 视觉特效资源**
- **场景模型**: `arena_1.bam` - 高质量格斗竞技场
- **粒子特效**: `hit_spark.png` (32x32) - 程序生成的橙白色击中火花
- **能量粒子**: `particle.png` - 技能释放特效纹理

### **🔧 开发工具集**
- **`premium_model_downloader.py`** - 从互联网搜索和下载高质量3D模型
- **`real_model_creator.py`** - 创建真实的角色模型变体和配置系统
- **`enhanced_audio_creator.py`** - 生成专业级游戏音效文件
- **`model_converter.py`** - 通用3D格式转换为Panda3D兼容格式
- **`assets_audit.py`** - 资源完整性和质量检查工具

## 运行方式
```powershell
cd gamecenter/streetBattle
# 直接运行（推荐）- 包含完整的游戏模式选择和角色选择界面
python main.py

# 或使用模块方式运行
cd ../..
python -m gamecenter.streetBattle.main

# 命令行参数（可选）
python main.py --mode local    # 本地AI对战
python main.py --mode host --port 12000    # 启动主机
python main.py --mode client --host 192.168.1.100 --port 12000    # 启动客户端
```

## 游戏控制
- **游戏模式选择**: 鼠标点击或键盘导航选择冒险/对战/网络模式
- **角色选择**: 鼠标点击角色头像或使用WASD/方向键导航，Enter确认
- **战斗控制**: 
  - WASD - 角色移动
  - 空格/鼠标左键 - 轻攻击  
  - 鼠标右键 - 重攻击
  - J - 跳跃
  - H - 显示/隐藏帮助
  - ESC - 返回上级菜单
  - 提示：只有在“FIGHT!”阶段输入才会驱动角色（日志打印 Player input: [...] 代表输入已生效）

## 回滚同步与网络对战说明
- 主机端每帧保存状态快照，收到延迟输入时自动回滚并重放，保证对战公平与流畅。
- 客户端本地预测并保存输入历史，收到主机快照后自动重放修正。
- 支持高延迟/丢包环境下的流畅体验。

## UI与特效美化
- 渐变血条、combo连击槽、受击闪烁、3D HUD
- 动态光影、摄像机抖动、粒子/光晕/击中特效
- 所有UI与特效均可自定义美化，详见 `ui.py`、`vfx.py`。
 - HUD 透明性确认：启动时控制台会打印 `[HUD] ... alpha=0 (transparent)`，确保不遮挡3D场景。

## 自动化测试
```powershell
# 单元测试
python -m unittest gamecenter/streetBattle/test_combat.py
# 集成smoke测试
python gamecenter/streetBattle/smoke_integration_test.py
# 回滚仿真测试
python gamecenter/streetBattle/test_rollback_sim.py
```

## 资源自定义与扩展
- 替换 `assets/` 下的模型、贴图、音效即可自定义角色、场景与特效。
- 支持BAM/PNG/WAV/OGG等主流格式。
- 代码结构清晰，便于扩展新角色、技能、UI与网络协议。

---
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

#### 新增功能与优化（v2025.09.22-后续）
- 🤖 Assistant 一体化入口：原“Voice Chat/Ask Question”合并为单一按钮“Assistant”。点击后：
  - 播报提示→短时监听（约2-3秒）；
  - 本地意图识别（无需外部工具）判断是“局面分析/建议”还是“闲聊”；
  - 直接进入最短响应路径，减少无关调用与卡顿。
- 🧠 RAG 严格模式：记忆检索默认启用 strict_vector，仅使用向量检索；网络/证书异常时不再静默关键词降级，返回空结果并记录日志。
 - 🧠 RAG 严格模式：记忆检索默认启用 strict_vector，仅使用向量检索；网络/证书异常时不再静默关键词降级，返回空结果并记录日志。
 - 🔑 API 配置简化：棋类陪伴组件仅需设置环境变量 `OPENAI_API_KEY`；不再读取 `base_url` 或任何 wildcard 变量。
- 🪟 拖动/缩放更流畅：窗口尺寸变化引发的布局重算增加节流，显著降低拖动卡顿。
- 🔊 语音播放更顺滑：OpenAI TTS 播放采用短轮询的非严格阻塞，界面更跟手。

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
  - RAG在严格模式下不会降级为关键词检索；若向量库暂不可用，将返回空结果并记录日志。

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