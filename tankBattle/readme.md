# Tank Battle Game - 面向对象重构版

## 概述

这是一个完全重构的坦克大战游戏，采用面向对象设计，具有更好的扩展性和可维护性。

## 新特性

### 🎯 胜利条件改进
- **双重胜利条件**: 需要同时摧毁敌方基地并消灭所有敌人才能通关
- **配置化**: 可通过 `config.py` 中的 `WIN_CONDITION` 轻松修改胜利条件
- **敌方基地**: 每关都有一个需要摧毁的敌方基地

### 🔫 多种子弹类型
1. **普通弹** (NORMAL)
   - 标准伤害和速度
   - 无特殊效果

2. **穿甲弹** (PIERCING)
   - 可以穿透墙壁
   - 更高的伤害和速度
   - 黄色标识

3. **爆炸弹** (EXPLOSIVE)
   - 爆炸范围伤害
   - 较慢但伤害更高
   - 橙色标识，带闪烁效果

### ⚙️ 配置化系统
- **独立配置文件**: `config.py` 包含所有游戏参数
- **玩家设置**: 可单独配置玩家坦克属性（生命值、速度、子弹类型等）
- **敌方设置**: 可单独配置敌方坦克属性
- **子弹配置**: 每种子弹类型都可独立配置

### 🏗️ 面向对象设计
- **模块化**: 代码拆分为多个专门的模块
- **可扩展**: 新功能易于添加
- **可维护**: 清晰的类结构和职责分离

## 文件结构

```
tankBattle/
├── main_oop.py          # 新的主游戏文件
├── config.py            # 游戏配置文件
├── tank_system.py       # 坦克系统（玩家和敌方坦克）
├── bullet_system.py     # 子弹系统（多种子弹类型）
├── environment.py       # 环境系统（墙壁、基地）
├── level_manager.py     # 关卡管理器
├── main.py             # 原版游戏文件（保留）
└── assets/             # 游戏资源
    ├── level*.map      # 关卡地图文件
    └── ...
```

## 游戏操作

- **↑/↓**: 前进/后退
- **←/→**: 左转/右转
- **空格**: 射击
- **P**: 暂停/继续
- **回车**:
  - 关卡完成时：进入下一关
  - 游戏结束时：重新开始## 配置说明

### 修改玩家配置
在 `config.py` 中修改 `PLAYER_CONFIG`:
```python
PLAYER_CONFIG = {
    'HEALTH': 100,        # 生命值
    'SPEED': 3,           # 移动速度
    'RELOAD_TIME': 30,    # 射击冷却时间
    # ... 其他配置
}
```

### 修改敌方配置
在 `config.py` 中修改 `ENEMY_CONFIG`:
```python
ENEMY_CONFIG = {
    'HEALTH': 3,          # 敌方生命值
    'SPEED': 1,           # 敌方移动速度
    'FIRE_RATE': 0.02,    # 射击频率
    # ... 其他配置
}
```

### 修改子弹类型
在 `config.py` 中修改子弹配置:
```python
PLAYER_BULLET_CONFIG = {
    'TYPE': 'PIERCING',   # 改为穿甲弹
}

ENEMY_BULLET_CONFIG = {
    'TYPE': 'EXPLOSIVE',  # 敌方使用爆炸弹
}
```

### 修改胜利条件
```python
WIN_CONDITION = {
    'DESTROY_ENEMY_BASE': True,     # 需要摧毁敌方基地
    'ELIMINATE_ALL_ENEMIES': True,  # 需要消灭所有敌人
    'BOTH_REQUIRED': True,          # 是否需要同时满足
    'TIME_LIMIT': None,             # 时间限制（毫秒）
}
```

## 游戏机制

### 关卡结构
- **玩家基地**: 蓝色基地，位于屏幕底部，需要保护
- **敌方基地**: 紫色基地，位于屏幕顶部，需要摧毁
- **迷宫墙壁**: 可以被射击摧毁的障碍物
- **敌方坦克**: 会主动攻击玩家和玩家基地

### 胜利条件
默认情况下，需要同时：
1. 摧毁敌方基地
2. 消灭所有敌方坦克

### 失败条件
以下任一情况会导致游戏失败：
1. 玩家坦克被摧毁
2. 玩家基地被摧毁

## 扩展指南

### 添加新的子弹类型
1. 在 `config.py` 的 `BULLET_TYPES` 中添加新类型
2. 在 `bullet_system.py` 的 `Bullet.draw()` 方法中添加绘制逻辑
3. 如需特殊效果，在 `Bullet` 类中添加相应方法

### 添加新的坦克类型
1. 在 `tank_system.py` 中继承 `BaseTank` 类
2. 在 `config.py` 中添加相应配置
3. 在关卡生成时使用新的坦克类型

### 修改AI行为
在 `tank_system.py` 的 `EnemyTank.update_ai()` 方法中修改敌方AI逻辑。

## 运行要求

- Python 3.6+
- pygame

安装依赖：
```bash
pip install pygame
```

运行游戏：
```bash
python main.py
```

## 开发说明

这个重构版本完全向后兼容，原版的 `main.py` 仍然可以运行。新版本提供了更好的代码组织、更丰富的功能和更强的可扩展性。
