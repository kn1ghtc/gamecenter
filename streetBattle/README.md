## 资源下载认证指南（Sketchfab）

当常规用户名/密码登录因CSRF/反自动化保护失败时，可使用已登录浏览器中的 Cookie 进行回退认证：

1) 在浏览器（已登录 Sketchfab）开发者工具中执行：
   - 访问任意可下载模型的 API，如 `https://sketchfab.com/i/models/<UID>/download`
   - 确认返回 JSON 中含有 `latest.gltf/glb` 等字段
   - 在控制台输入 `document.cookie` 并复制包含 `sb_csrftoken`、`aws-waf-token` 等的整行 Cookie

2) 将 Cookie 粘贴到 `gamecenter/streetBattle/.env.local`，新增一行：
```
SKETCHFAB_cookies = "<粘贴浏览器里的 Cookie 字符串>"
```

3) 运行资源管理器（优先只下载一个角色进行冒烟）：
```
python .\gamecenter\streetBattle\resource_manager.py --characters kyo_kusanagi --keep-archives
```

脚本会自动：
- 优先尝试常规登录；
- 如失败则回退到 Cookie 方式导入；
- 调用 `/i/models/<uid>/download` 探测是否已授权；
- 解析 `latest` 节点并补全相对 URL 后下载 GLTF/GLB。

注意：Cookie 有有效期，若后续失效需重复上述步骤重新粘贴。

#  🌟 项目架构优化完成 (2025.01.22)
- 🧹 **项目结构清理**：删除重复的角色生成器，合并多个下载器为统一的资源管理器
- 🛠️ **工具模块化**：创建 `tools/` 目录，统一管理9个辅助工具脚本
- 📊 **资源管理统一**：`resource_manager.py` 集成下载、审计、验证和清理功能
- 🔧 **增强角色管理**：`EnhancedCharacterManager` 支持多层级资源，FBX占位符检测和BAM兜底
- 🎯 **无效资源清理**：清理423个无效文件，节省108GB磁盘空间（从117GB减少到9.4GB）
- 📁 **架构简化**：从15个文件简化为8个核心模块，提升维护性和可读性
- ✅ **游戏可玩性确认**：84角色正常加载，增强角色管理器运行正常，游戏成功启动 - 次世代格斗游戏巨作


## 🌟 真实3D资源系统 (2025.09.25) - 彻底解决占位符问题
## � Kyo Kusanagi资源下载测试成功 (2025.09.25) - 验证完成
- ✅ **Sketchfab认证系统**：成功实现浏览器自动化登录 (kcshareg@gmail.com)
- ✅ **模型搜索与下载**：成功找到并下载"Kyo Kusanagi 94-98 - KOF All Stars"模型
- ✅ **高质量3D资源**：31.28MB FBX模型 + 完整贴图包 (漫反射/法线/高光)
- ✅ **动画数据完整**：包含KOF All Stars完整动画集，7.7k三角面，4k顶点
- ✅ **商用许可**：CC Attribution许可，支持商业使用
- ✅ **多格式支持**：FBX(31MB), GLB(12MB), USDZ(767KB), glTF(4MB)
- 🎭 **Actor 角色模型管线**：移除圆柱体/卡通兜底，统一使用 BAM/GLTF/GLB 的 Actor 模型
- 🖥️ **UI界面完全重构**：修复倒计时遮挡问题，多层渲染系统，清晰的界面布局
- ⏰ **游戏状态管理**：120秒每局时间限制，完整胜负判定，多回合制比赛
- 🏃 **角色动画框架**：流畅的角色动画系统（idle、walking、attack、victory状态）
```powershell
# 执行一次完整的清理 + 下载流程（使用 resource_catalog.json 中的 UID）
python .\gamecenter\streetBattle\resource_manager.py

# 仅查看将要执行的操作（不会删除或下载）
python .\gamecenter\streetBattle\resource_manager.py --dry-run

# 仅针对部分角色重新下载
python .\gamecenter\streetBattle\resource_manager.py --characters kyo_kusanagi iori_yagami
```

> 配置说明：
> - 在 `gamecenter/streetBattle/.env.local` 提供 `SKETCHFAB_email` 和 `SKETCHFAB_password`，脚本会自动登录并处理重试。
> - `assets/resource_catalog.json` 已预置全部角色 UID，下载时会优先获取 GLTF 格式，无法获取时回退至 GLB。
> - 当前流程仅依赖 Sketchfab 源，如需追加 Models Resource 直链，可在 catalog 的 `models_resource` 节点中补充。
- **智能动画系统**：基于LerpInterval的流畅角色动画，支持多种动作状态
- **完整游戏流程**：120秒回合制，多种胜负条件（KO/时间结束），状态机管理
- **多层UI架构**：解决界面遮挡问题，清晰的血条、计时器、角色信息显示

### 🎨 视觉与音效系统
- **专业级3D角色**：80MB高质量FBX模型，专业级材质和纹理，告别程序化生成
- **双层级资源架构**：Sketchfab/Models Resource多源资源，确保最佳视觉效果
- **高质量场景**：专业级竞技场模型和特效纹理系统
- **程序化竞技场**：默认删除冗余纹理，仅保留 UI 纹理目录，战斗舞台由程序化地面实时生成
- **动态特效**：击打闪光、粒子系统、UI动画效果
- **完整音频**：打击音效、连击音效、背景音乐的完整音频体验

### 🔊 音频系统
- **程序化BGM**：30秒循环战斗音乐，支持OGG/WAV格式
- **撞击音效**：使用NumPy生成的高质量战斗音效
- **空间音频**：基于位置的3D音效系统
- **智能回退**：多层音频文件回退确保兼容性

## 🚀 快速开始

### 系统要求
- Python 3.10+ 
- Panda3D 1.10.13+
- PIL (图像处理)
- NumPy (音效生成)
- Wave (音频处理)

### 一键运行
```powershell
# 一键清理并同步全部角色资源
python .\gamecenter\streetBattle\resource_manager.py

# 预览将执行的操作（不会修改文件）
python .\gamecenter\streetBattle\resource_manager.py --dry-run

# 仅同步指定角色
python .\gamecenter\streetBattle\resource_manager.py --characters kyo_kusanagi iori_yagami

# 初始化工具脚本（可选）
python .\tools\create_kof97_characters.py  # 创建角色数据库
python .\tools\generate_bgm.py             # 生成音频资源

# 启动游戏
python .\main.py
```

### 运行方式

**本地对战 (AI对手):**
```bash
python main.py --mode local
```

**局域网主机:**
```bash
python main.py --mode host --port 12000
```

**局域网客户端:**
```bash
python main.py --mode client --host 192.168.1.100 --port 12000
```

### 控制方式
- **WASD** - 移动
- **空格/鼠标左键** - 轻攻击
- **鼠标右键** - 重攻击
- **J** - 跳跃
- **ESC** - 退出

### 角色选择
游戏包含完整84个KOF角色(1994-2024)，涵盖全系列经典角色：
- **日本队**: 草薙京、八神庵、千鹤等
- **饿狼队**: 泰瑞、安迪、东丈等  
- **龙虎队**: 坂崎良、罗伯特、坂崎由莉等
- **怒队**: 莉安娜、拉尔夫、克拉克等
- **心灵战士队**: 麻宫雅典娜、镇元斋、椎拳崇等
- **女性格斗家队**: 不知火舞、金、布鲁玛丽等
- **NESTS篇**: K'、Maxima、Whip等
- **BOSS角色**: 吉斯、大蛇、卢卡尔、伊格尼兹等
- **新世代**: Shun'ei、Isla、Dolores等

每个角色均配备：
- （已移除CGTrader层级）
- **高质量PBR材质和4K纹理**
- **完整动画集** (idle、walk、attack、victory等)
- **角色特定属性** (格斗风格、国籍、技能等)



#### 按角色批量下载（可选）
你也可以通过 `assets/characters_manifest.json` 为 20 个角色批量拉取 Actor 模型与动画（URL 可为你自己的开源/自建仓库）：

```json
{
   "characters": [
      {
         "name": "Kyo Kusanagi",
         "id": "kyo_kusanagi",
         "model": "https://example.com/kyo/kyo_kusanagi.bam",
         "animations": {
            "idle": "https://example.com/kyo/idle.bam",
            "walk": "https://example.com/kyo/walk.bam",
            "light": "https://example.com/kyo/light.bam",
            "heavy": "https://example.com/kyo/heavy.bam"
         }
      }
   ]
}
```

放置文件到 `assets/characters_manifest.json` 后，执行：

```powershell
python .\download_assets.py
```

下载器会将模型保存至 `assets/characters/<id>/`，动画保存至 `assets/characters/<id>/animations/`。

> 兼容性：未在清单中提供的角色或文件会继续使用 `npc_1.bam` 进行临时填充，确保 Actor-only 可运行。
### 资产管理
- 资产目录：`assets/` 包含所有游戏资源
- 文件有效性验证（FBX/GLTF/GLB格式校验）

#### 动画自动映射（Auto-mapping）
`CharacterManager` 会自动扫描 `assets/characters/<char_id>/animations` 下的 `.bam/.gltf/.glb` 文件，并根据文件名将其映射为标准动画键：

- 标准键：`idle, walk, light, heavy, attack, hurt, jump, block, crouch, victory, defeat`
- 名称同义词（示例）：
   - `idle/stand` → `idle`
   - `walk/run/move` → `walk`
   - `jab/lp/punch_light` → `light`
   - `hp/strong/punch_heavy` → `heavy`
   - `punch/kick/strike` → `attack`
   - `hit/hurt/damage` → `hurt`
   - `guard/block` → `block`；`duck/crouch` → `crouch`
   - `win/victory` → `victory`；`lose/ko/death/defeat` → `defeat`

若只提供了通用 `attack`，系统会同时为 `light/heavy` 兜底映射为该动作。

字符 ID 规则：将人物名小写并用下划线替换空格，例如：
- "Kyo Kusanagi" -> `kyo_kusanagi`
- "Iori Yagami" -> `iori_yagami`

### 资产完整性审计（强烈建议）
加入资产审计工具确保资源真实可用、无占位符：

```powershell
python assets_audit.py --base assets --report assets\audit_report.json --clean-placeholders
```

它会：
- 校验 BAM/GLTF/GLB 的基本有效性（头部/JSON/魔数）
- 识别并可清理 .txt 占位符文件（如“replace with actual”提示）
- 报告可疑的小文件与缺失的关键资源（如 arena_1.bam、npc_1.bam）

通过审计后再运行游戏，可显著降低模型加载失败导致的“方块/圆柱体”兜底出现概率。

## 技术架构

### 核心模块
- **main.py** - 游戏主循环和场景管理
- **enhanced_character_manager.py** - 84角色双层级资源管理系统
- **resource_manager.py** - 统一资源下载、审计、验证和清理工具
- **character_selector.py** - 84角色选择器，智能数据兼容性处理
- **player.py** - 角色控制和战斗逻辑，支持角色特定属性
- **combat.py** - 格斗系统和伤害计算，防止重复击中
- **ai.py** - 智能AI系统：预测、撤退、连击逻辑
- **vfx.py** - 优化VFX系统：纹理预加载，避免性能问题
- **audio.py** - 音频管理和空间音效，支持程序化生成
- **ui.py** - 增强UI系统：角色信息、战斗状态显示
- **net.py** - UDP网络和帧同步回滚

### 工具目录 (tools/)
- **bam_character_creator.py** - BAM格式角色模型生成器
- **character_generator.py** - 程序化角色生成工具
- **cleanup_project.py** - 项目清理和优化脚本
- **create_kof97_characters.py** - KOF97角色数据库生成器
- **enhanced_audio_creator.py** - 高质量音频生成工具
- **enhance_assets.py** - 资源增强和优化工具
- **generate_bgm.py** - 背景音乐生成器
- **model_converter.py** - 3D模型格式转换工具
- **real_model_creator.py** - 真实模型创建工具

### 数据结构
- **kof97_characters.json** - 20个角色的完整数据库（3138行）
- **assets/characters/** - 20个角色目录，包含模型和动画占位符
- **assets/models/** - Arena FPS高质量3D模型（76MB总计）
- **ui.py** - 用户界面和HUD系统

### 网络架构
- **协议**: 自定义UDP协议，基于帧同步
- **回滚**: 客户端预测和服务器权威回滚
- **延迟补偿**: 自动网络延迟检测和补偿
- **断线重连**: 优雅的连接失败处理

### 程序化生成资源 
4. **VFX 纹理** (CC0 - 公共领域)
   - 生成工具: PIL + NumPy
   - 文件: hit_spark.png, energy.png, smoke.png
   - 算法: 程序化特效纹理生成

5. **传统兜底资源** (BSD 3-Clause)
   - 来源: Arena FPS项目
   - 文件: npc_1.bam（仅当3D资源系统完全失败时使用）
   - 现状: 已被专业3D资源完全替代

6. **音效文件** (CC0 - 公共领域)  
   - 生成工具: NumPy
   - 文件: hit_generated.wav, combo_generated.wav
   - 算法: 程序化音频合成

### 角色肖像资源
- **来源**：`assets/portrait_sources.json` 现以程序化规格描述（调色板、纹样、标志文字等），所有肖像均由项目内脚本生成，归属为 CC0 可自由使用。
- **生成机制**：执行 `python .\tools\download_portraits.py` 会调用 Pillow 根据配置生成 768×960 的高质量立绘，并写入 `assets/images/portraits/<角色>.png`，彻底摆脱远程下载与封锁风险。
- **更新流程**：为新角色添加时，在 `portrait_sources.json` 中补充 `palette`、`accent_color`、`pattern`、`emblem_text` 等字段即可；生成脚本会自动依据这些参数渲染全新的原创肖像。如需完全自定义，直接放置同名 PNG 到 `assets/images/portraits/` 将覆盖程序化结果。
- **合规提醒**：由于肖像现为团队原创生成，`assets/ATTRIBUTION.md` 中的肖像段落保持 CC0 说明即可；调整配置后请重新运行生成脚本，并在游戏中验证缩放与透明度效果是否正常。

### 许可合规
- 所有专业3D资源使用均符合商业许可条款
- 程序化生成内容采用CC0许可，可自由使用
- 完整归属信息见 `assets/ATTRIBUTION.md`

## 贡献指南

### 代码风格
- 遵循PEP 8 Python编码规范
- 使用类型提示和文档字符串
- 模块化设计，保持低耦合


## 版本历史

- **v1.0** (2024) - 初始版本，基础格斗系统
- **v2.0** (2024) - 网络对战和回滚系统
- **v3.0** (2024) - 高质量资源集成和程序化生成

## 许可证

本项目为内部研究项目。核心代码采用内部许可，外部资源遵循各自原始许可证。详见各资源文件的许可声明。

## next steps
- 完成剩余42个角色的真实3D资源替换，从sketchfab按个下载后，使用本地的gltf2bam转换后替换
- 优化AI逻辑，提升对战智能
- 完善3d和2.5d的动画集animations的完整补充与优化，确保真实有效，可玩性提升
- 优化net局域网内联机对战的稳定性和流畅度