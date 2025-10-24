# 程序化生成的游戏资源清单

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
    frame = pygame.image.load(f"assets/images/effects/explosion_{i:02d}.png")
    explosion_frames.append(frame)
```

## 📝 注意事项

1. 这些资源是程序化生成的，风格为简约像素艺术
2. 音效使用NumPy生成的合成音频，质量有限
3. 建议替换为专业美术资源以获得更好的视觉效果
4. 所有资源已优化用于deltaOperation游戏项目

---

**重新生成**: `python generate_game_assets.py`
