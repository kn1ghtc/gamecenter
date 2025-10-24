#!/usr/bin/env python3
"""程序化生成游戏资源 (Programmatic Game Asset Generator)

生成高质量的像素艺术风格游戏资源，包括：
- 士兵角色精灵图 (像素艺术风格)
- 武器精灵图 (手枪/步枪/霰弹枪/狙击枪)
- UI元素 (按钮/面板/图标)
- 特效 (枪口火焰/爆炸序列帧)
- WAV音效文件 (使用NumPy生成)

Author: kn1ghtc
Date: 2025-10-23
Version: 1.0.0
"""

import os
import sys
import pygame
import numpy as np
from pathlib import Path
import wave
import struct

# 初始化Pygame
pygame.init()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
ASSETS_ROOT = PROJECT_ROOT / "assets"


def ensure_dir(path: Path):
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def draw_soldier_sprite(surface, x, y, color, size=64):
    """绘制士兵精灵 (像素艺术风格)"""
    # 头部
    head_color = (222, 184, 135)  # 肤色
    pygame.draw.circle(surface, head_color, (x + size//2, y + size//4), size//6)
    
    # 头盔
    helmet_color = color
    pygame.draw.ellipse(surface, helmet_color, 
                        (x + size//2 - size//6, y + size//6, size//3, size//5))
    
    # 身体 (防弹衣)
    body_color = color
    pygame.draw.rect(surface, body_color,
                     (x + size//2 - size//4, y + size//3, size//2, size//2.5))
    
    # 装备背带
    strap_color = (80, 80, 80)
    pygame.draw.line(surface, strap_color,
                     (x + size//2 - size//4, y + size//2.5),
                     (x + size//2 + size//4, y + size//2.5), 2)
    
    # 手臂 (持枪姿势)
    arm_color = color
    pygame.draw.rect(surface, arm_color,
                     (x + size//2 - size//3, y + size//2.5, size//8, size//3))
    pygame.draw.rect(surface, arm_color,
                     (x + size//2 + size//4, y + size//2.5, size//8, size//3))
    
    # 枪械 (简化表示)
    gun_color = (40, 40, 40)
    pygame.draw.rect(surface, gun_color,
                     (x + size//2 + size//4, y + size//2.2, size//2, size//15))
    
    # 腿部
    leg_color = (90, 90, 90)
    pygame.draw.rect(surface, leg_color,
                     (x + size//2 - size//5, y + size//1.3, size//10, size//2.5))
    pygame.draw.rect(surface, leg_color,
                     (x + size//2 + size//10, y + size//1.3, size//10, size//2.5))
    
    # 靴子
    boot_color = (50, 50, 50)
    pygame.draw.rect(surface, boot_color,
                     (x + size//2 - size//5, y + size//1.15, size//8, size//8))
    pygame.draw.rect(surface, boot_color,
                     (x + size//2 + size//10, y + size//1.15, size//8, size//8))


def draw_weapon(surface, weapon_type, size=128):
    """绘制武器精灵"""
    surface.fill((0, 0, 0, 0))  # 透明背景
    
    gun_color = (40, 40, 40)
    barrel_color = (60, 60, 60)
    grip_color = (80, 60, 40)
    
    if weapon_type == "pistol":
        # 手枪 - 紧凑型
        pygame.draw.rect(surface, gun_color, (size//4, size//2.2, size//2, size//10))  # 滑套
        pygame.draw.rect(surface, barrel_color, (size//1.4, size//2.2, size//5, size//15))  # 枪管
        pygame.draw.polygon(surface, grip_color, [  # 握把
            (size//4, size//2), 
            (size//3, size//1.6),
            (size//2.5, size//1.6),
            (size//3.5, size//2)
        ])
    
    elif weapon_type == "rifle":
        # 步枪 - 现代突击步枪
        pygame.draw.rect(surface, gun_color, (size//6, size//2.3, size//1.5, size//8))  # 枪身
        pygame.draw.rect(surface, barrel_color, (size//1.3, size//2.3, size//4, size//12))  # 枪管
        pygame.draw.rect(surface, gun_color, (size//5, size//2.8, size//10, size//6))  # 弹匣
        pygame.draw.polygon(surface, grip_color, [  # 握把
            (size//3, size//2.1), 
            (size//2.5, size//1.8),
            (size//2.2, size//1.8),
            (size//2.6, size//2.1)
        ])
        pygame.draw.rect(surface, gun_color, (size//8, size//3.2, size//5, size//20))  # 枪托
    
    elif weapon_type == "shotgun":
        # 霰弹枪 - 粗壮枪管
        pygame.draw.rect(surface, gun_color, (size//5, size//2.5, size//1.5, size//6))  # 枪身
        pygame.draw.rect(surface, barrel_color, (size//1.4, size//2.5, size//3.5, size//7))  # 粗枪管
        pygame.draw.rect(surface, gun_color, (size//4, size//2.2, size//8, size//12))  # 装填口
        pygame.draw.rect(surface, grip_color, (size//3.5, size//2, size//12, size//5))  # 泵动握把
        pygame.draw.rect(surface, gun_color, (size//7, size//2.8, size//6, size//15))  # 枪托
    
    elif weapon_type == "sniper":
        # 狙击枪 - 长枪管 + 瞄准镜
        pygame.draw.rect(surface, gun_color, (size//8, size//2.4, size//1.2, size//10))  # 枪身
        pygame.draw.rect(surface, barrel_color, (size//1.2, size//2.4, size//3, size//15))  # 长枪管
        pygame.draw.ellipse(surface, (100, 100, 120), (size//3, size//3.5, size//4, size//8))  # 瞄准镜
        pygame.draw.rect(surface, gun_color, (size//4, size//2.6, size//12, size//8))  # 弹匣
        pygame.draw.polygon(surface, gun_color, [  # 两脚架
            (size//1.6, size//2.1),
            (size//1.5, size//1.7),
            (size//1.4, size//1.7),
            (size//1.5, size//2.1)
        ])


def draw_muzzle_flash(surface, frame, size=64):
    """绘制枪口火焰序列帧"""
    surface.fill((0, 0, 0, 0))
    
    # 根据帧数变化颜色和形状
    colors = [
        (255, 255, 200, 255),  # 黄白色
        (255, 220, 100, 230),  # 黄橙色
        (255, 150, 50, 200),   # 橙红色
        (200, 100, 0, 150),    # 深橙色
    ]
    
    color = colors[frame % len(colors)]
    
    # 中心核心
    core_size = size // (2 + frame)
    pygame.draw.circle(surface, color[:3], (size//2, size//2), core_size)
    
    # 放射状火焰
    num_rays = 8
    for i in range(num_rays):
        angle = (360 / num_rays) * i + frame * 15
        import math
        end_x = size//2 + int(math.cos(math.radians(angle)) * (size//2 - frame * 5))
        end_y = size//2 + int(math.sin(math.radians(angle)) * (size//2 - frame * 5))
        pygame.draw.line(surface, color[:3], (size//2, size//2), (end_x, end_y), 3)


def draw_explosion(surface, frame, size=128):
    """绘制爆炸序列帧"""
    surface.fill((0, 0, 0, 0))
    
    import math
    
    # 爆炸阶段
    if frame < 3:  # 初期 - 明亮火球
        colors = [(255, 255, 150), (255, 200, 100), (255, 150, 50)]
        for i, color in enumerate(colors):
            radius = (size//2) * (frame + 1) // 3 - i * 5
            if radius > 0:
                pygame.draw.circle(surface, color, (size//2, size//2), radius)
    elif frame < 6:  # 中期 - 火焰扩散
        colors = [(255, 150, 0), (200, 100, 0), (150, 50, 0)]
        for i, color in enumerate(colors):
            radius = (size//2) + (frame - 3) * 10 - i * 8
            if radius > 0:
                pygame.draw.circle(surface, color, (size//2, size//2), radius)
    else:  # 后期 - 黑烟
        smoke_color = (80, 80, 80)
        for i in range(5):
            offset_x = int(math.cos(i * 1.2) * (frame - 5) * 3)
            offset_y = int(math.sin(i * 1.2) * (frame - 5) * 3)
            pygame.draw.circle(surface, smoke_color, 
                               (size//2 + offset_x, size//2 + offset_y), 
                               size//3)


def draw_ui_button(surface, width, height, style="normal"):
    """绘制UI按钮"""
    surface.fill((0, 0, 0, 0))
    
    if style == "normal":
        # 主按钮 - 蓝灰色
        bg_color = (70, 90, 120)
        border_color = (100, 120, 150)
    elif style == "hover":
        # 悬停 - 亮蓝色
        bg_color = (90, 120, 160)
        border_color = (120, 150, 190)
    elif style == "pressed":
        # 按下 - 深色
        bg_color = (50, 70, 100)
        border_color = (70, 90, 120)
    
    # 背景
    pygame.draw.rect(surface, bg_color, (2, 2, width-4, height-4), border_radius=5)
    # 边框
    pygame.draw.rect(surface, border_color, (0, 0, width, height), 2, border_radius=5)
    # 高光
    highlight_color = (255, 255, 255, 80)
    pygame.draw.line(surface, highlight_color, (4, 4), (width-4, 4), 2)


def generate_sine_wave(frequency, duration, sample_rate=44100, amplitude=0.3):
    """生成正弦波音频"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    return wave


def generate_gunshot_sound(weapon_type, duration=0.3, sample_rate=44100):
    """生成枪声音效"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    if weapon_type == "pistol":
        # 手枪 - 高频脆响
        wave = 0.5 * np.sin(2 * np.pi * 800 * t) + 0.3 * np.sin(2 * np.pi * 1500 * t)
        wave *= np.exp(-8 * t)  # 快速衰减
    elif weapon_type == "rifle":
        # 步枪 - 中频爆裂声
        wave = 0.6 * np.sin(2 * np.pi * 400 * t) + 0.4 * np.sin(2 * np.pi * 800 * t)
        wave *= np.exp(-6 * t)
    elif weapon_type == "shotgun":
        # 霰弹枪 - 低频轰鸣
        wave = 0.7 * np.sin(2 * np.pi * 200 * t) + 0.3 * np.sin(2 * np.pi * 400 * t)
        wave *= np.exp(-4 * t)
    elif weapon_type == "sniper":
        # 狙击枪 - 低频重击
        wave = 0.8 * np.sin(2 * np.pi * 150 * t) + 0.2 * np.sin(2 * np.pi * 300 * t)
        wave *= np.exp(-5 * t)
    else:
        wave = np.zeros_like(t)
    
    # 添加白噪声模拟火药爆炸
    noise = np.random.normal(0, 0.1, len(t))
    wave += noise * np.exp(-10 * t)
    
    # 归一化
    wave = np.clip(wave, -1.0, 1.0)
    
    return wave


def generate_explosion_sound(duration=0.8, sample_rate=44100):
    """生成爆炸音效"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 低频轰鸣
    wave = 0.8 * np.sin(2 * np.pi * 100 * t)
    wave += 0.4 * np.sin(2 * np.pi * 50 * t)
    
    # 初期冲击波 (高能量)
    impact = np.exp(-3 * t)
    wave *= impact
    
    # 添加强烈白噪声
    noise = np.random.normal(0, 0.3, len(t))
    wave += noise * np.exp(-2 * t)
    
    # 归一化
    wave = np.clip(wave, -1.0, 1.0)
    
    return wave


def save_wav(filename, audio_data, sample_rate=44100):
    """保存WAV文件"""
    # 转换为16-bit整数
    audio_int16 = np.int16(audio_data * 32767)
    
    with wave.open(str(filename), 'w') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())


def main():
    """主生成函数"""
    print("=" * 60)
    print("🎨 程序化生成游戏资源 v1.0.0")
    print("=" * 60)
    
    # ===== 生成角色精灵图 =====
    print("\n📦 生成角色精灵图...")
    characters_dir = ASSETS_ROOT / "images" / "characters"
    ensure_dir(characters_dir)
    
    soldier_colors = [
        ("soldier_green", (60, 100, 60)),   # 绿色制服
        ("soldier_desert", (140, 120, 80)),  # 沙漠迷彩
        ("soldier_urban", (80, 80, 90)),     # 城市灰
    ]
    
    for name, color in soldier_colors:
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        draw_soldier_sprite(surface, 0, 0, color, 64)
        pygame.image.save(surface, str(characters_dir / f"{name}.png"))
        print(f"  ✅ {name}.png")
    
    # ===== 生成敌人精灵图 =====
    print("\n📦 生成敌人精灵图...")
    enemies_dir = ASSETS_ROOT / "images" / "enemies"
    ensure_dir(enemies_dir)
    
    enemy_colors = [
        ("terrorist_red", (120, 40, 40)),    # 红色
        ("terrorist_black", (40, 40, 40)),   # 黑色
        ("terrorist_camo", (70, 90, 60)),    # 迷彩
    ]
    
    for name, color in enemy_colors:
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        draw_soldier_sprite(surface, 0, 0, color, 64)
        pygame.image.save(surface, str(enemies_dir / f"{name}.png"))
        print(f"  ✅ {name}.png")
    
    # ===== 生成武器精灵图 =====
    print("\n📦 生成武器精灵图...")
    weapons_dir = ASSETS_ROOT / "images" / "weapons"
    ensure_dir(weapons_dir)
    
    weapon_types = ["pistol", "rifle", "shotgun", "sniper"]
    for weapon in weapon_types:
        surface = pygame.Surface((128, 64), pygame.SRCALPHA)
        draw_weapon(surface, weapon, 128)
        pygame.image.save(surface, str(weapons_dir / f"{weapon}.png"))
        print(f"  ✅ {weapon}.png")
    
    # ===== 生成特效精灵图 =====
    print("\n📦 生成特效精灵图...")
    effects_dir = ASSETS_ROOT / "images" / "effects"
    ensure_dir(effects_dir)
    
    # 枪口火焰 (4帧动画)
    for frame in range(4):
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        draw_muzzle_flash(surface, frame, 64)
        pygame.image.save(surface, str(effects_dir / f"muzzle_flash_{frame}.png"))
        print(f"  ✅ muzzle_flash_{frame}.png")
    
    # 爆炸效果 (10帧动画)
    for frame in range(10):
        surface = pygame.Surface((128, 128), pygame.SRCALPHA)
        draw_explosion(surface, frame, 128)
        pygame.image.save(surface, str(effects_dir / f"explosion_{frame:02d}.png"))
        print(f"  ✅ explosion_{frame:02d}.png")
    
    # ===== 生成UI元素 =====
    print("\n📦 生成UI元素...")
    ui_dir = ASSETS_ROOT / "images" / "ui"
    ensure_dir(ui_dir)
    
    button_styles = ["normal", "hover", "pressed"]
    for style in button_styles:
        surface = pygame.Surface((200, 60), pygame.SRCALPHA)
        draw_ui_button(surface, 200, 60, style)
        pygame.image.save(surface, str(ui_dir / f"button_{style}.png"))
        print(f"  ✅ button_{style}.png")
    
    # ===== 生成音效文件 =====
    print("\n📦 生成音效文件...")
    sounds_dir = ASSETS_ROOT / "sounds" / "weapons"
    ensure_dir(sounds_dir)
    
    # 武器音效
    weapon_sounds = {
        "pistol_shoot": ("pistol", 0.2),
        "rifle_shoot": ("rifle", 0.25),
        "shotgun_shoot": ("shotgun", 0.35),
        "sniper_shoot": ("sniper", 0.4),
    }
    
    for sound_name, (weapon_type, duration) in weapon_sounds.items():
        audio = generate_gunshot_sound(weapon_type, duration)
        save_wav(sounds_dir / f"{sound_name}.wav", audio)
        print(f"  ✅ {sound_name}.wav")
    
    # 爆炸音效
    effects_sounds_dir = ASSETS_ROOT / "sounds" / "effects"
    ensure_dir(effects_sounds_dir)
    
    explosion_audio = generate_explosion_sound(0.8)
    save_wav(effects_sounds_dir / "explosion.wav", explosion_audio)
    print(f"  ✅ explosion.wav")
    
    # ===== 生成资源清单 =====
    print("\n📦 生成资源清单...")
    manifest_content = f"""# 程序化生成的游戏资源清单

**生成时间**: 2025-10-23 17:30
**生成器**: generate_game_assets.py v1.0.0

## 📊 资源统计

- **角色精灵图**: 3个士兵 (绿色/沙漠/城市迷彩)
- **敌人精灵图**: 3个恐怖分子 (红色/黑色/迷彩)
- **武器精灵图**: 4种武器 (手枪/步枪/霰弹枪/狙击枪)
- **特效精灵图**: 枪口火焰 (4帧) + 爆炸 (10帧)
- **UI元素**: 按钮 (普通/悬停/按下)
- **音效文件**: 4种枪声 + 1个爆炸音

## 📁 目录结构

```
assets/
├── images/
│   ├── characters/
│   │   ├── soldier_green.png
│   │   ├── soldier_desert.png
│   │   └── soldier_urban.png
│   ├── enemies/
│   │   ├── terrorist_red.png
│   │   ├── terrorist_black.png
│   │   └── terrorist_camo.png
│   ├── weapons/
│   │   ├── pistol.png
│   │   ├── rifle.png
│   │   ├── shotgun.png
│   │   └── sniper.png
│   ├── effects/
│   │   ├── muzzle_flash_0.png (初始帧)
│   │   ├── muzzle_flash_1.png
│   │   ├── muzzle_flash_2.png
│   │   ├── muzzle_flash_3.png (最后帧)
│   │   ├── explosion_00.png (初始帧)
│   │   ├── explosion_01.png
│   │   ├── ...
│   │   └── explosion_09.png (最后帧)
│   └── ui/
│       ├── button_normal.png
│       ├── button_hover.png
│       └── button_pressed.png
└── sounds/
    ├── weapons/
    │   ├── pistol_shoot.wav (200ms)
    │   ├── rifle_shoot.wav (250ms)
    │   ├── shotgun_shoot.wav (350ms)
    │   └── sniper_shoot.wav (400ms)
    └── effects/
        └── explosion.wav (800ms)
```

## 🎨 资源质量

- **图片格式**: PNG with Alpha透明通道
- **图片尺寸**: 角色64x64, 武器128x64, 特效64x64/128x128, UI200x60
- **音频格式**: WAV (16-bit, 44.1kHz, 单声道)
- **许可证**: 程序化生成资源，可自由使用

## 🔧 使用方法

```python
# 加载角色精灵
soldier = pygame.image.load("assets/images/characters/soldier_green.png")

# 加载武器精灵
rifle = pygame.image.load("assets/images/weapons/rifle.png")

# 播放枪声
gunshot_sound = pygame.mixer.Sound("assets/sounds/weapons/rifle_shoot.wav")
gunshot_sound.play()

# 加载爆炸动画帧
explosion_frames = []
for i in range(10):
    frame = pygame.image.load(f"assets/images/effects/explosion_{{i:02d}}.png")
    explosion_frames.append(frame)
```

## 📝 注意事项

1. 这些资源是程序化生成的，风格为简约像素艺术
2. 音效使用NumPy生成的合成音频，质量有限
3. 建议替换为专业美术资源以获得更好的视觉效果
4. 所有资源已优化用于deltaOperation游戏项目

---

**重新生成**: `python generate_game_assets.py`
"""
    
    with open(ASSETS_ROOT / "ASSET_MANIFEST.md", 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    print(f"  ✅ ASSET_MANIFEST.md")
    
    # ===== 完成 =====
    print("\n" + "=" * 60)
    print("✅ 所有资源生成完成!")
    print("=" * 60)
    print(f"\n资源目录: {ASSETS_ROOT}")
    print("\n资源统计:")
    print(f"  - 角色精灵图: 6个 (3士兵 + 3敌人)")
    print(f"  - 武器精灵图: 4个")
    print(f"  - 特效精灵图: 14个 (4火焰帧 + 10爆炸帧)")
    print(f"  - UI元素: 3个")
    print(f"  - 音效文件: 5个")
    print(f"\n下一步: 运行游戏测试粒子效果")
    print(f"  python main.py")
    print()


if __name__ == "__main__":
    main()
