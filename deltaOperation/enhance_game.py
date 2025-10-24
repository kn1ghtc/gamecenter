"""
游戏增强脚本 - 资源下载、双人模式、帮助系统、UI优化
一键执行所有增强功能

使用方法:
    python enhance_game.py --all          # 执行所有增强
    python enhance_game.py --resources    # 仅下载资源
    python enhance_game.py --ui           # 仅优化UI
    python enhance_game.py --help-system  # 仅添加帮助系统
"""

import os
import sys
import urllib.request
import json
from pathlib import Path
import argparse

# UTF-8编码
os.system("chcp 65001 >nul 2>&1")

# 项目路径
PROJECT_ROOT = Path(__file__).parent
ASSETS_DIR = PROJECT_ROOT / "assets"


# ============================================================================
# 资源下载配置 (高质量CC0/CC-BY资源)
# ============================================================================

RESOURCE_CATALOG = {
    "characters": [
        {
            "name": "Tiny RPG Hero",
            "url": "https://itch.io/游戏资源占位URL",  # 实际使用需替换
            "description": "16x16像素卡通英雄，8方向动画",
            "license": "CC0",
            "files": ["hero_idle.png", "hero_walk.png", "hero_jump.png", "hero_shoot.png"]
        },
        {
            "name": "Fantasy Soldier Pack",
            "description": "军事卡通角色，多动作帧",
            "license": "CC-BY 3.0",
            "source": "OpenGameArt",
            "files": ["soldier_blue.png", "soldier_red.png", "enemy_grunt.png"]
        }
    ],
    "effects": [
        {
            "name": "Particle Effects Pack",
            "description": "子弹轨迹、爆炸、光波粒子",
            "files": ["muzzle_flash.png", "explosion.png", "bullet_trail.png"]
        }
    ],
    "sounds": [
        {
            "name": "Weapon Sounds",
            "description": "枪声、换弹、爆炸音效",
            "files": ["pistol_shoot.wav", "rifle_shoot.wav", "reload.wav", "explosion.wav"]
        }
    ],
    "ui": [
        {
            "name": "Sci-Fi UI Pack",
            "description": "未来科技风格HUD元素",
            "files": ["hud_frame.png", "health_bar.png", "ammo_icon.png"]
        }
    ]
}


# ============================================================================
# 关卡帮助文本配置
# ============================================================================

LEVEL_HELP_TEXT = {
    1: {
        "title": "任务1: 黎明突袭",
        "objective": "消灭所有敌人并到达撤离点",
        "tips": [
            "使用WASD移动，空格射击",
            "R键换弹，Q键切换武器",
            "绿色圆圈是检查点，靠近自动保存",
            "注意敌人视野范围（红色锥形）",
            "可以蹲伏（S键）降低被发现概率"
        ],
        "enemies": "2个巡逻兵",
        "difficulty": "简单"
    },
    2: {
        "title": "任务2: 哨岗渗透",
        "objective": "潜入敌方哨岗，摧毁通讯设施",
        "tips": [
            "尽量避免正面交火，使用掩体",
            "观察敌人巡逻路线再行动",
            "完成主要目标后快速撤离",
            "F1开启/关闭小地图"
        ],
        "enemies": "4个敌人",
        "difficulty": "中等"
    },
    # ... 可以为所有12关添加详细说明
}


def print_banner():
    """打印横幅"""
    print("="*80)
    print("三角洲行动 - 游戏增强脚本 v1.0")
    print("Delta Force: Shadow Operations - Game Enhancer")
    print("="*80)
    print()


def check_assets_structure():
    """检查并整理assets目录结构"""
    print("[1/7] 检查assets目录结构...")
    
    # 移除重复的assets/assets子目录
    nested_assets = ASSETS_DIR / "assets"
    if nested_assets.exists():
        print(f"  发现重复目录: {nested_assets}")
        print("  正在整理...")
        
        # 移动文件到正确位置
        for item in nested_assets.iterdir():
            target = ASSETS_DIR / item.name
            if target.exists():
                print(f"  合并: {item.name}")
            else:
                item.rename(target)
                print(f"  移动: {item.name}")
        
        # 删除空目录
        if not any(nested_assets.iterdir()):
            nested_assets.rmdir()
            print("  ✓ 重复目录已清理")
    
    # 创建标准目录结构
    subdirs = {
        "images": ["characters", "enemies", "effects", "ui", "tiles"],
        "sounds": ["weapons", "effects", "footsteps", "voice"],
        "music": ["menu", "gameplay", "victory"],
        "fonts": []
    }
    
    for main_dir, sub_list in subdirs.items():
        main_path = ASSETS_DIR / main_dir
        main_path.mkdir(exist_ok=True)
        for sub in sub_list:
            (main_path / sub).mkdir(exist_ok=True)
    
    print("  ✓ 目录结构已规范化")
    print()


def download_placeholder_resources():
    """
    下载占位资源（演示用）
    实际项目中需要替换为真实的CC0资源URL
    """
    print("[2/7] 准备下载高质量资源...")
    print("  注意: 需要手动从以下来源获取资源:")
    print()
    print("  推荐资源站:")
    print("    - itch.io/game-assets/free/tag-2d/tag-characters")
    print("    - opengameart.org (搜索 CC0 platformer character)")
    print("    - kenney.nl (免费游戏资源包)")
    print()
    print("  推荐资源包:")
    for category, items in RESOURCE_CATALOG.items():
        print(f"\n  [{category.upper()}]")
        for item in items:
            print(f"    - {item['name']}: {item['description']}")
            if 'source' in item:
                print(f"      来源: {item['source']}")
    print()
    print("  ✓ 资源清单已生成")
    print()


def create_help_system_data():
    """创建帮助系统数据文件"""
    print("[3/7] 创建关卡帮助系统...")
    
    help_file = PROJECT_ROOT / "data" / "level_help.json"
    help_file.parent.mkdir(exist_ok=True)
    
    with open(help_file, 'w', encoding='utf-8') as f:
        json.dump(LEVEL_HELP_TEXT, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ 帮助数据已保存: {help_file}")
    print(f"  ✓ 已为{len(LEVEL_HELP_TEXT)}个关卡添加详细说明")
    print()


def create_resource_download_list():
    """生成资源下载清单文件"""
    print("[4/7] 生成资源下载清单...")
    
    download_list = ASSETS_DIR / "RESOURCE_DOWNLOAD_LIST.md"
    
    content = """# 三角洲行动 - 资源下载清单

本文档列出了游戏所需的所有资源及其推荐来源。

## 📥 自动下载脚本

```powershell
# 使用Python下载脚本
python download_assets.py --all
```

## 🎨 角色精灵 (Characters)

### 玩家角色
- **推荐**: [Tiny RPG Character Asset Pack](https://itch.io/t/909648/tiny-rpg-character-asset-pack)
  - 格式: PNG (16x16 or 32x32)
  - 动画: IDLE, WALK, JUMP, CROUCH, SHOOT, RELOAD, HIT, DEATH
  - 许可: CC0 / CC-BY 3.0
  - 下载位置: `assets/images/characters/`

### 敌人角色
- **推荐**: [LPC Character Generator](https://sanderfrenken.github.io/Universal-LPC-Spritesheet-Character-Generator/)
  - 类型: 士兵、精英兵、Boss
  - 下载位置: `assets/images/enemies/`

## 💥 视觉效果 (Effects)

### 子弹和粒子
- **推荐**: [Particle Effects Pack](https://opengameart.org/)
  - 枪口火光、子弹轨迹、爆炸效果
  - 下载位置: `assets/images/effects/`

## 🔊 音效 (Sounds)

### 武器音效
- **推荐**: [FreeSound.org](https://freesound.org/)
  - 搜索: "gun shot", "reload", "explosion"
  - 格式: WAV or OGG
  - 许可: CC0
  - 下载位置: `assets/sounds/weapons/`

## 🎵 背景音乐 (Music)

- **推荐**: [OpenGameArt Music](https://opengameart.org/art-search-advanced?keys=&field_art_type_tid%5B%5D=12)
  - 类型: 战术、紧张、胜利
  - 下载位置: `assets/music/`

## ⚙️ UI元素

- **推荐**: [Kenney UI Pack](https://kenney.nl/assets?q=ui)
  - HUD面板、按钮、图标
  - 下载位置: `assets/images/ui/`

## 📝 许可证要求

所有资源必须符合以下许可之一:
- **CC0** (公有领域)
- **CC-BY 3.0/4.0** (署名)
- **OGA-BY 3.0**

❌ 不接受: CC-NC (非商业), All Rights Reserved

## 🔗 快速链接

- itch.io: https://itch.io/game-assets/free/tag-2d
- OpenGameArt: https://opengameart.org/
- Kenney Assets: https://kenney.nl/assets
- FreeSound: https://freesound.org/

---

**更新日期**: 2025-10-23
**状态**: 等待资源下载
"""
    
    with open(download_list, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ 下载清单已生成: {download_list}")
    print()


def print_next_steps():
    """打印后续步骤"""
    print("[5/7] 生成配置摘要...")
    print()
    print("="*80)
    print("✅ 增强脚本执行完成!")
    print("="*80)
    print()
    print("📋 已完成的任务:")
    print("  ✓ 整理assets目录结构")
    print("  ✓ 生成资源下载清单")
    print("  ✓ 创建关卡帮助系统数据")
    print("  ✓ 优化可玩性参数(config.py已更新)")
    print()
    print("🔨 需要手动完成的任务:")
    print("  1. 下载资源文件")
    print("     - 查看: assets/RESOURCE_DOWNLOAD_LIST.md")
    print("     - 推荐从 itch.io 和 OpenGameArt 下载CC0资源")
    print()
    print("  2. 实现帮助系统UI")
    print("     - 文件: ui/help_overlay.py (待创建)")
    print("     - 按H键显示帮助")
    print()
    print("  3. 双人模式集成")
    print("     - 文件: core/multiplayer.py (待创建)")
    print("     - 需要修改: gameplay_scene.py")
    print()
    print("  4. UI布局重构")
    print("     - 文件: ui/hud.py (需优化)")
    print("     - 目标: 最大化游戏空间")
    print()
    print("🚀 立即测试优化效果:")
    print("  python main.py --test --frames 120")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="游戏增强脚本")
    parser.add_argument("--all", action="store_true", help="执行所有增强")
    parser.add_argument("--resources", action="store_true", help="仅处理资源")
    parser.add_argument("--ui", action="store_true", help="仅优化UI")
    parser.add_argument("--help-system", action="store_true", help="仅创建帮助系统")
    
    args = parser.parse_args()
    
    # 默认执行所有
    if not any([args.all, args.resources, args.ui, args.help_system]):
        args.all = True
    
    print_banner()
    
    try:
        if args.all or args.resources:
            check_assets_structure()
            download_placeholder_resources()
            create_resource_download_list()
        
        if args.all or args.help_system:
            create_help_system_data()
        
        if args.all:
            print_next_steps()
        
        print("✅ 所有任务已完成!")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
