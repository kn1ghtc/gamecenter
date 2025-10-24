# 🎮 网页游戏中心 - Web Game Center

一个完整的现代化在线游戏平台，提供 13 个精心打造的 HTML5 游戏。用户可以注册、登录、游玩游戏、查看排行榜并跟踪个人成就。

## ✨ 核心功能

### 游戏库 (13 个游戏)
- **动作游戏**: 魂斗罗、拳皇
- **街机游戏**: 贪吃蛇  
- **休闲游戏**: 小恐龙、飞翔的鸟、吃豆人
- **益智游戏**: 2048、打砖块、扫雷、推箱子、俄罗斯方块
- **射击游戏**: 太空射击、坦克大战

### 用户系统
- ✅ JWT 认证与授权
- ✅ 用户注册、登录、资料管理
- ✅ 30 天 token 过期机制
- ✅ 安全的密码存储

### 游戏功能
- ✅ 游戏分类管理 (5 个类别)
- ✅ 实时游戏数据库记录
- ✅ 动态游戏列表加载
- ✅ HTML5 Canvas + DOM 混合支持

### 排行榜系统
- ✅ 全球排行榜
- ✅ 按游戏分类排行
- ✅ 实时排名更新
- ✅ 用户排名查询

### 成就系统
- ✅ 成就追踪与解锁
- ✅ 徽章系统
- ✅ 个人成就仪表板

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Flask 3.0.0 + SQLAlchemy 2.0 |
| **数据库** | SQLite (production 可用 PostgreSQL) |
| **认证** | Flask-JWT-Extended |
| **前端框架** | Bootstrap 5.3 + Vanilla JS |
| **游戏引擎** | HTML5 Canvas + requestAnimationFrame |
| **测试框架** | pytest + Selenium WebDriver |

## 📁 项目结构

```
webGameCenter/
├── app.py                      # Flask 主应用入口
├── config.py                   # 配置文件（游戏列表、数据库设置）
├── requirements.txt            # Python 依赖
├── README.md                   # 项目文档
├── HELP.md                     # 用户帮助指南
│
├── backend/                    # 后端代码
│   ├── database/
│   │   └── db.py              # SQLAlchemy 数据模型
│   └── routes/
│       ├── auth.py            # 用户认证接口
│       ├── games.py           # 游戏信息接口
│       └── scores.py          # 排行榜接口
│
├── frontend/                   # 前端代码
│   ├── index.html             # 主页面
│   ├── css/
│   │   └── style.css          # 全局样式
│   ├── js/
│   │   ├── main.js            # 应用主逻辑
│   │   ├── api.js             # API 调用封装
│   │   └── ui.js              # UI 辅助函数
│   └── games/                 # 游戏目录
│       ├── action/            # 动作游戏
│       │   ├── contra/
│       │   └── kof/
│       ├── arcade/            # 街机游戏
│       │   └── snake/
│       ├── casual/            # 休闲游戏
│       │   ├── dinosaur/
│       │   ├── flappybird/
│       │   └── pacman/
│       ├── puzzle/            # 益智游戏
│       │   ├── 2048/
│       │   ├── breakout/
│       │   ├── minesweeper/
│       │   ├── sokoban/
│       │   └── tetris/
│       └── shooting/          # 射击游戏
│           ├── spaceshooter/
│           └── tankbattle/
│
├── scripts/                    # 辅助脚本
│   ├── download_resources.py  # 游戏资源下载
│   └── validate_games.py      # 游戏验证
│
├── tests/                      # 测试套件
│   ├── conftest.py            # pytest 配置
│   ├── test_api.py            # API 端点测试
│   └── test_games.py          # Selenium 游戏测试
│
└── instance/                   # 实例文件夹
    └── game_center.db         # SQLite 数据库
```

## 🚀 快速开始

### 1. 环境设置

```bash
# 进入项目目录
cd d:\pyproject\gamecenter\webGameCenter

# 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
# 运行 Flask 应用
python app.py

# 应用启动在 http://127.0.0.1:5000
```

### 3. 访问游戏中心

打开浏览器访问 `http://127.0.0.1:5000`，您会看到：
- 游戏中心主页面
- 游戏分类浏览
- 用户登录/注册选项
- 排行榜查看

## 📊 API 文档

### 认证接口

**POST** `/api/auth/register` - 用户注册
```json
{
  "username": "player1",
  "email": "player@example.com",
  "password": "securepass"
}
```

**POST** `/api/auth/login` - 用户登录
```json
{
  "username": "player1",
  "password": "securepass"
}
```

### 游戏接口

**GET** `/api/games/categories` - 获取所有游戏分类
```json
{
  "casual": {
    "name": "休闲游戏",
    "games": [...]
  }
}
```

**GET** `/api/games/category/{category_id}` - 获取分类内游戏
```json
{
  "games": [
    {
      "id": "flappybird",
      "name": "飞翔的鸟",
      "difficulty": "easy",
      "icon": "🐦"
    }
  ]
}
```

### 排行榜接口

**GET** `/api/scores/leaderboard` - 全球排行榜（前 10）

**GET** `/api/scores/game/{game_id}` - 游戏排行榜

**GET** `/api/scores/user/{user_id}` - 用户排行信息

## 🧪 测试

### 运行测试套件

```bash
# API 端点测试
pytest tests/test_api.py -v

# 游戏验证
python scripts/validate_games.py

# 所有测试 + 覆盖率
pytest tests/ --cov=backend --cov-report=html
```

### 验证脚本输出示例

```
🎮 游戏可玩性验证

📁 动作游戏:
  ✓ contra
  ✓ kof

📁 街机游戏:
  ✓ snake

...

📊 验证结果: 13/13 完整 (0 个警告)
```

## 🎮 游戏文件结构

每个游戏都包含两个文件：

```
games/[category]/[game_id]/
├── index.html    # 游戏 HTML 容器（包含 Canvas 或 DOM 结构）
└── game.js       # 游戏逻辑（支持两种实现方式）
```

### 支持的实现方式

**方式 1: Canvas-based**
```javascript
class Game {
  constructor() { }
  draw() { }
  update() { }
  gameLoop() { }
}
```

**方式 2: DOM-based**
```javascript
class Game {
  constructor() { }
  init() { }
  bindEvents() { }
  move() { }
}
```

## 📝 配置文件

编辑 `config.py` 可修改：

```python
GAMES_CONFIG = {
    'casual': {
        'name': '休闲游戏',
        'games': [
            {
                'id': 'flappybird',
                'name': '飞翔的鸟',
                'description': '点击屏幕让小鸟飞翔',
                'difficulty': 'easy',
                'icon': '🐦'
            },
            # 添加更多游戏...
        ]
    }
}
```

## 🔧 开发工作流

### 添加新游戏

1. **在 config.py 中注册**
   ```python
   'new_game': {
       'id': 'my_game',
       'name': 'My Game',
       'description': '...',
       'difficulty': 'medium',
       'icon': '🎮'
   }
   ```

2. **创建游戏文件**
   ```bash
   mkdir frontend/games/[category]/[game_id]
   touch frontend/games/[category]/[game_id]/index.html
   touch frontend/games/[category]/[game_id]/game.js
   ```

3. **验证游戏**
   ```bash
   python scripts/validate_games.py
   ```

### 数据库迁移

项目使用 SQLAlchemy，数据库会自动初始化。表结构：

- **users** - 用户账户
- **games** - 游戏元数据
- **game_records** - 游戏记录
- **scores** - 玩家分数
- **achievements** - 成就系统

## 🐛 常见问题

**Q: 游戏加载失败？**
A: 检查 `frontend/games/` 目录结构是否正确，确保每个游戏都有 `index.html` 和 `game.js`。

**Q: 分数没有保存？**
A: 需要用户登录。检查后端日志和浏览器控制台是否有错误。

**Q: 如何部署到生产环境？**
A: 使用生产级 WSGI 服务器（如 Gunicorn），配置 PostgreSQL 数据库，启用 HTTPS。

**Q: 支持移动设备吗？**
A: 是的。前端使用 Bootstrap 5 响应式设计，支持手机和平板。

## 📈 项目状态

- ✅ 13/13 游戏完整实现
- ✅ 所有游戏通过验证 (0 个警告)
- ✅ 4/4 API 端点测试通过
- ✅ 响应式 UI 设计完成
- ✅ 用户认证系统完整
- ✅ 排行榜功能正常
- ✅ 成就系统已集成

## 📄 许可证

本项目为教育用途开发，提供开源代码供学习参考。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

---

**最后更新**: 2025-10-24  
**维护者**: kn1ghtc  
**版本**: 1.0.0
