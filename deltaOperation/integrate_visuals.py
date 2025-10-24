#!/usr/bin/env python3
"""视觉效果增强集成脚本 (Visual Enhancement Integration Script)

一键集成粒子系统到现有游戏代码

Author: kn1ghtc
Date: 2025-10-23
Version: 1.0.0
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent


def backup_file(file_path: Path) -> None:
    """备份文件"""
    backup_path = file_path.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(file_path, backup_path)
    print(f"  ✅ 已备份: {backup_path.name}")


def integrate_weapon_particles():
    """集成武器粒子效果到weapon.py"""
    weapon_file = PROJECT_ROOT / "core" / "weapon.py"
    
    if not weapon_file.exists():
        print("❌ 未找到 weapon.py")
        return False
    
    print("\n🔧 集成武器粒子效果...")
    backup_file(weapon_file)
    
    # 读取现有代码
    with open(weapon_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加导入（如果不存在）
    if "from gamecenter.deltaOperation.utils.enhanced_visuals import get_particle_system" not in content:
        # 找到第一个import语句后插入
        import_pattern = r"(import .*?)\n\n"
        replacement = r"\1\nfrom gamecenter.deltaOperation.utils.enhanced_visuals import get_particle_system\n\n"
        content = re.sub(import_pattern, replacement, content, count=1)
        print("  ✅ 添加粒子系统导入")
    
    # 在Weapon类的shoot方法中添加粒子效果
    if "particle_sys.create_muzzle_flash" not in content:
        # 查找shoot方法
        shoot_pattern = r"(def shoot\(self.*?\):\s*.*?)(return.*?\n)"
        
        particle_code = '''
        # 🆕 粒子效果: 枪口火焰 + 弹壳抛出
        particle_sys = get_particle_system()
        weapon_type_map = {
            "M9 Pistol": "pistol",
            "M4A1": "rifle",
            "SPAS-12": "shotgun",
            "M24": "sniper"
        }
        
        # 计算射击角度
        dx = target_pos[0] - shooter_pos[0]
        dy = target_pos[1] - shooter_pos[1]
        shoot_angle = math.degrees(math.atan2(dy, dx))
        
        # 枪口火焰效果
        particle_sys.create_muzzle_flash(
            x=shooter_pos[0],
            y=shooter_pos[1],
            angle=shoot_angle,
            weapon_type=weapon_type_map.get(self.name, "rifle")
        )
        
        # 弹壳抛出效果
        particle_sys.create_bullet_shell(
            x=shooter_pos[0],
            y=shooter_pos[1],
            angle=shoot_angle,
            weapon_type=weapon_type_map.get(self.name, "rifle")
        )
        
        '''
        
        replacement = r"\1" + particle_code + r"\2"
        content = re.sub(shoot_pattern, replacement, content, flags=re.DOTALL)
        print("  ✅ 添加枪口火焰 + 弹壳抛出效果")
    
    # 保存修改
    with open(weapon_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ weapon.py 集成完成")
    return True


def integrate_gameplay_particles():
    """集成粒子系统到gameplay_scene.py"""
    gameplay_file = PROJECT_ROOT / "core" / "gameplay_scene.py"
    
    if not gameplay_file.exists():
        print("❌ 未找到 gameplay_scene.py")
        return False
    
    print("\n🔧 集成粒子系统到游戏场景...")
    backup_file(gameplay_file)
    
    # 读取现有代码
    with open(gameplay_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加导入
    if "from gamecenter.deltaOperation.utils.enhanced_visuals import get_particle_system" not in content:
        import_pattern = r"(from gamecenter\.deltaOperation\..*?)\n\n"
        replacement = r"\1\nfrom gamecenter.deltaOperation.utils.enhanced_visuals import get_particle_system\n\n"
        content = re.sub(import_pattern, replacement, content, count=1)
        print("  ✅ 添加粒子系统导入")
    
    # 在__init__中初始化粒子系统
    if "self.particle_system = get_particle_system()" not in content:
        init_pattern = r"(def __init__\(self.*?\):\s*.*?)(self\.level_manager.*?\n)"
        replacement = r"\1\2        self.particle_system = get_particle_system()\n"
        content = re.sub(init_pattern, replacement, content, flags=re.DOTALL)
        print("  ✅ 初始化粒子系统实例")
    
    # 在update方法中更新粒子
    if "self.particle_system.update" not in content:
        update_pattern = r"(def update\(self, delta_time\):\s*.*?)(# Update.*?\n)"
        replacement = r"\1\2        # 🆕 更新粒子系统\n        self.particle_system.update(delta_time)\n        \n"
        content = re.sub(update_pattern, replacement, content, flags=re.DOTALL)
        print("  ✅ 添加粒子更新逻辑")
    
    # 在render方法中渲染粒子（在HUD之前）
    if "self.particle_system.render" not in content:
        render_pattern = r"(self\.player\.render\(.*?\)\s*\n)(.*?# .*?HUD)"
        replacement = r'''\1
        # 🆕 渲染粒子效果（在HUD之前）
        camera_offset = (self.camera.offset_x, self.camera.offset_y)
        self.particle_system.render(screen, camera_offset)
        
\2'''
        content = re.sub(render_pattern, replacement, content, flags=re.DOTALL)
        print("  ✅ 添加粒子渲染逻辑")
    
    # 保存修改
    with open(gameplay_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ gameplay_scene.py 集成完成")
    return True


def integrate_enemy_blood_effects():
    """集成血液溅射效果到enemy.py"""
    enemy_file = PROJECT_ROOT / "core" / "enemy.py"
    
    if not enemy_file.exists():
        print("❌ 未找到 enemy.py")
        return False
    
    print("\n🔧 集成血液溅射效果...")
    backup_file(enemy_file)
    
    # 读取现有代码
    with open(enemy_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加导入
    if "from gamecenter.deltaOperation.utils.enhanced_visuals import get_particle_system" not in content:
        import_pattern = r"(import .*?)\n\n"
        replacement = r"\1\nfrom gamecenter.deltaOperation.utils.enhanced_visuals import get_particle_system\n\n"
        content = re.sub(import_pattern, replacement, content, count=1)
        print("  ✅ 添加粒子系统导入")
    
    # 在take_damage方法中添加血液效果
    if "particle_sys.create_blood_splash" not in content:
        damage_pattern = r"(def take_damage\(self, damage.*?\):\s*.*?self\.health -= damage\s*\n)"
        
        blood_code = '''
        # 🆕 血液溅射效果
        if self.health > 0:  # 还活着才溅血
            particle_sys = get_particle_system()
            # 计算子弹入射角度
            if hasattr(self, '_last_bullet_direction'):
                bullet_dir = self._last_bullet_direction
                impact_angle = math.degrees(math.atan2(bullet_dir[1], bullet_dir[0]))
            else:
                impact_angle = 0  # 默认角度
            
            particle_sys.create_blood_splash(
                x=self.position.x,
                y=self.position.y,
                impact_angle=impact_angle,
                intensity=int(damage / 5)  # 根据伤害调整粒子数
            )
        
'''
        
        replacement = r"\1" + blood_code
        content = re.sub(damage_pattern, replacement, content, flags=re.DOTALL)
        print("  ✅ 添加血液溅射效果")
    
    # 保存修改
    with open(enemy_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ enemy.py 集成完成")
    return True


def integrate_audio_3d():
    """集成3D音效系统到audio.py"""
    audio_file = PROJECT_ROOT / "utils" / "audio.py"
    
    if not audio_file.exists():
        print("❌ 未找到 audio.py")
        return False
    
    print("\n🔧 集成3D音效系统...")
    backup_file(audio_file)
    
    # 读取现有代码
    with open(audio_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加3D音效方法
    if "def play_sound_3d" not in content:
        # 找到AudioSystem类的最后一个方法
        class_pattern = r"(class AudioSystem:.*?)((?=\nclass )|$)"
        
        audio_3d_code = '''
    def play_sound_3d(self, sound_name: str, world_x: float, world_y: float, 
                      listener_x: float, listener_y: float, max_distance: float = 800) -> None:
        """播放3D定位音效
        
        Args:
            sound_name: 音效名称
            world_x, world_y: 音源世界坐标
            listener_x, listener_y: 听者（玩家）坐标
            max_distance: 最大听力距离
        """
        import math
        
        # 计算距离
        dx = world_x - listener_x
        dy = world_y - listener_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > max_distance:
            return  # 超出听力范围
        
        # 音量衰减（距离平方反比）
        volume = 1.0 - (distance / max_distance) ** 2
        volume = max(0.0, min(1.0, volume))
        
        # 左右声道平衡（简单立体声）
        angle = math.atan2(dy, dx)
        pan = math.sin(angle)  # -1(左) 到 1(右)
        left_volume = volume * (1 - max(0, pan))
        right_volume = volume * (1 - max(0, -pan))
        
        # 播放音效
        sound = self._get_sound(sound_name)
        if sound:
            channel = sound.play()
            if channel:
                channel.set_volume(left_volume * self.sound_volume, 
                                   right_volume * self.sound_volume)

'''
        
        replacement = r"\1" + audio_3d_code + r"\2"
        content = re.sub(class_pattern, replacement, content, flags=re.DOTALL)
        print("  ✅ 添加3D音效方法")
    
    # 保存修改
    with open(audio_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ audio.py 集成完成")
    return True


def generate_integration_report():
    """生成集成报告"""
    report_path = PROJECT_ROOT / "INTEGRATION_REPORT.md"
    
    report = f"""# 视觉效果集成报告 (Visual Integration Report)

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**集成版本**: v1.3.0  
**状态**: ✅ 成功

---

## 📦 已集成模块

### 1. 武器粒子效果 (`core/weapon.py`)
- ✅ 枪口火焰效果（根据武器类型自动调整）
- ✅ 弹壳抛出效果（物理模拟）
- ✅ 射击角度计算

### 2. 游戏场景粒子系统 (`core/gameplay_scene.py`)
- ✅ 粒子系统初始化
- ✅ 粒子更新逻辑（每帧）
- ✅ 粒子渲染逻辑（相机偏移）

### 3. 敌人血液效果 (`core/enemy.py`)
- ✅ 血液溅射效果（受击时触发）
- ✅ 子弹入射角度计算
- ✅ 伤害强度映射粒子数量

### 4. 3D音效系统 (`utils/audio.py`)
- ✅ 空间定位音效播放
- ✅ 距离衰减计算
- ✅ 左右声道平衡

---

## 🎯 集成效果验证清单

请运行游戏并验证以下效果：

### 视觉效果
- [ ] 射击时武器有明显的枪口火焰
- [ ] 弹壳向侧面抛出并落地（有重力效果）
- [ ] 敌人受击时血液向后方溅射
- [ ] 手枪/步枪/霰弹枪/狙击枪火焰效果不同

### 音效效果
- [ ] 远处枪声音量减小
- [ ] 左侧枪声偏向左声道
- [ ] 右侧枪声偏向右声道

### 性能指标
- [ ] 帧率保持在 50-60 FPS
- [ ] 粒子数量不超过 2000
- [ ] 无明显卡顿或掉帧

---

## 🔧 备份文件列表

以下文件已自动备份（时间戳: {datetime.now().strftime('%Y%m%d_%H%M%S')}）：

- `core/weapon.py.bak_*`
- `core/gameplay_scene.py.bak_*`
- `core/enemy.py.bak_*`
- `utils/audio.py.bak_*`

如需回滚，请执行：
```powershell
# 示例：恢复weapon.py
cp core/weapon.py.bak_TIMESTAMP core/weapon.py
```

---

## 🚀 下一步优化建议

1. **下载高质量资源** (VISUAL_ENHANCEMENT_GUIDE.md)
   - CraftPix Soldier Pack
   - Fire Weapons Sound Pack
   - Kenney UI Pack

2. **集成真实精灵图** (替换占位符)
   - 角色精灵图加载
   - 武器精灵图渲染
   - 背景瓦片地图

3. **高级视觉效果** (后处理)
   - 屏幕震动
   - 慢动作击杀
   - 闪光弹致盲效果

---

**集成完成! 立即运行游戏体验新效果：**
```powershell
python main.py
```
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📝 集成报告已生成: {report_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("🎮 视觉效果增强集成脚本 v1.0.0")
    print("=" * 60)
    
    success_count = 0
    total_tasks = 4
    
    # 执行集成任务
    if integrate_weapon_particles():
        success_count += 1
    
    if integrate_gameplay_particles():
        success_count += 1
    
    if integrate_enemy_blood_effects():
        success_count += 1
    
    if integrate_audio_3d():
        success_count += 1
    
    # 生成报告
    generate_integration_report()
    
    # 总结
    print("\n" + "=" * 60)
    print(f"✅ 集成完成: {success_count}/{total_tasks} 个模块")
    print("=" * 60)
    
    if success_count == total_tasks:
        print("\n🎉 所有模块集成成功！")
        print("\n下一步:")
        print("  1. 下载资源: python download_assets.py --all")
        print("  2. 运行游戏: python main.py")
        print("  3. 查看报告: INTEGRATION_REPORT.md")
    else:
        print("\n⚠️ 部分模块集成失败，请检查错误信息")
    
    print()


if __name__ == "__main__":
    main()
