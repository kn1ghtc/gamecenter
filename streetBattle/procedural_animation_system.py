"""
程序化动画系统 (Procedural Animation System)
为不包含骨骼动画的3D模型创建Transform动画

解决方案: 通过Interval系统控制模型的位置、旋转、缩放来模拟动作
适用于: 所有从Sketchfab下载的静态BAM模型
"""

from direct.interval.IntervalGlobal import *
from panda3d.core import Vec3, Point3
from typing import Dict, Optional
import random


class ProceduralAnimationSystem:
    """程序化动画系统 - 为静态模型创建动画效果"""
    
    def __init__(self):
        self.active_animations = {}  # character_id -> Interval
        self.animation_configs = self._setup_animation_configs()
    
    def _setup_animation_configs(self) -> Dict:
        """配置各种动画参数"""
        return {
            'idle': {
                'float_amplitude': 0.03,  # 浮动幅度
                'float_speed': 1.5,       # 浮动速度
                'sway_angle': 1.5,        # 摇摆角度
                'sway_speed': 2.0         # 摇摆速度
            },
            'walk': {
                'bob_amplitude': 0.08,    # 跳动幅度
                'bob_speed': 0.4,         # 跳动速度
                'rock_angle': 4,          # 前后摇摆角度
                'rock_speed': 0.4         # 摇摆速度
            },
            'run': {
                'bob_amplitude': 0.12,
                'bob_speed': 0.25,
                'rock_angle': 6,
                'rock_speed': 0.25
            },
            'jump': {
                'height': 1.5,
                'duration': 0.8,
                'rotation': 360
            },
            'attack_light': {
                'lunge_distance': 0.3,
                'lunge_speed': 0.15,
                'spin_angle': 15,
                'recovery_speed': 0.2
            },
            'attack_heavy': {
                'lunge_distance': 0.5,
                'lunge_speed': 0.2,
                'spin_angle': 30,
                'recovery_speed': 0.3
            },
            'hurt': {
                'knockback': 0.3,
                'shake_amplitude': 0.1,
                'duration': 0.5
            },
            'victory': {
                'jump_height': 0.5,
                'spin_angle': 720,
                'duration': 2.0
            },
            'defeat': {
                'fall_duration': 1.0,
                'rotation_angle': 90
            }
        }
    
    def create_idle_animation(self, model, character_id: str) -> Interval:
        """创建idle动画 - 轻微浮动和呼吸效果"""
        config = self.animation_configs['idle']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 轻微上下浮动（呼吸效果）
        float_up = model.posInterval(
            config['float_speed'],
            Point3(base_pos.x, base_pos.y, base_pos.z + config['float_amplitude']),
            blendType='easeInOut'
        )
        float_down = model.posInterval(
            config['float_speed'],
            base_pos,
            blendType='easeInOut'
        )
        float_sequence = Sequence(float_up, float_down)
        
        # 轻微左右摇摆
        sway_left = model.hprInterval(
            config['sway_speed'],
            Vec3(base_hpr.x + config['sway_angle'], base_hpr.y, base_hpr.z),
            blendType='easeInOut'
        )
        sway_right = model.hprInterval(
            config['sway_speed'],
            Vec3(base_hpr.x - config['sway_angle'], base_hpr.y, base_hpr.z),
            blendType='easeInOut'
        )
        sway_sequence = Sequence(sway_left, sway_right)
        
        # 组合动画并循环
        animation = Parallel(float_sequence, sway_sequence)
        animation.loop()
        
        self.active_animations[f"{character_id}_idle"] = animation
        return animation
    
    def create_walk_animation(self, model, character_id: str) -> Interval:
        """创建walk动画 - 前后摇摆和跳动"""
        config = self.animation_configs['walk']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 上下跳动（模拟步伐）
        bob_up = model.posInterval(
            config['bob_speed'] / 2,
            Point3(base_pos.x, base_pos.y, base_pos.z + config['bob_amplitude']),
            blendType='easeInOut'
        )
        bob_down = model.posInterval(
            config['bob_speed'] / 2,
            base_pos,
            blendType='easeInOut'
        )
        bob_sequence = Sequence(bob_up, bob_down)
        
        # 前后摇摆（模拟躯干运动）
        rock_forward = model.hprInterval(
            config['rock_speed'] / 2,
            Vec3(base_hpr.x, base_hpr.y + config['rock_angle'], base_hpr.z),
            blendType='easeInOut'
        )
        rock_backward = model.hprInterval(
            config['rock_speed'] / 2,
            Vec3(base_hpr.x, base_hpr.y - config['rock_angle'], base_hpr.z),
            blendType='easeInOut'
        )
        rock_sequence = Sequence(rock_forward, rock_backward)
        
        # 组合并循环
        animation = Parallel(bob_sequence, rock_sequence)
        animation.loop()
        
        self.active_animations[f"{character_id}_walk"] = animation
        return animation
    
    def create_run_animation(self, model, character_id: str) -> Interval:
        """创建run动画 - 更快更剧烈的移动"""
        config = self.animation_configs['run']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 更大幅度的跳动
        bob_up = model.posInterval(
            config['bob_speed'] / 2,
            Point3(base_pos.x, base_pos.y, base_pos.z + config['bob_amplitude'])
        )
        bob_down = model.posInterval(
            config['bob_speed'] / 2,
            base_pos
        )
        bob_sequence = Sequence(bob_up, bob_down)
        
        # 更大角度的前后倾斜
        rock_forward = model.hprInterval(
            config['rock_speed'] / 2,
            Vec3(base_hpr.x, base_hpr.y + config['rock_angle'], base_hpr.z)
        )
        rock_backward = model.hprInterval(
            config['rock_speed'] / 2,
            Vec3(base_hpr.x, base_hpr.y - config['rock_angle'], base_hpr.z)
        )
        rock_sequence = Sequence(rock_forward, rock_backward)
        
        animation = Parallel(bob_sequence, rock_sequence)
        animation.loop()
        
        self.active_animations[f"{character_id}_run"] = animation
        return animation
    
    def create_jump_animation(self, model, character_id: str) -> Interval:
        """创建jump动画 - 跳跃和旋转"""
        config = self.animation_configs['jump']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 跳起
        jump_up = model.posInterval(
            config['duration'] / 3,
            Point3(base_pos.x, base_pos.y, base_pos.z + config['height']),
            blendType='easeOut'
        )
        
        # 悬空
        hang_time = Wait(config['duration'] / 6)
        
        # 落下
        jump_down = model.posInterval(
            config['duration'] / 2,
            base_pos,
            blendType='easeIn'
        )
        
        # 旋转效果（可选）
        spin = model.hprInterval(
            config['duration'],
            Vec3(base_hpr.x + config['rotation'], base_hpr.y, base_hpr.z)
        )
        reset_spin = model.hprInterval(0.1, base_hpr)
        
        animation = Sequence(
            Parallel(jump_up, spin),
            hang_time,
            jump_down,
            reset_spin
        )
        
        self.active_animations[f"{character_id}_jump"] = animation
        return animation
    
    def create_attack_light_animation(self, model, character_id: str) -> Interval:
        """创建light attack动画 - 快速冲击"""
        config = self.animation_configs['attack_light']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 前冲
        lunge = model.posInterval(
            config['lunge_speed'],
            Point3(base_pos.x, base_pos.y + config['lunge_distance'], base_pos.z),
            blendType='easeOut'
        )
        
        # 旋转冲击
        spin = model.hprInterval(
            config['lunge_speed'],
            Vec3(base_hpr.x + config['spin_angle'], base_hpr.y, base_hpr.z)
        )
        
        # 恢复位置
        recover_pos = model.posInterval(
            config['recovery_speed'],
            base_pos,
            blendType='easeIn'
        )
        recover_hpr = model.hprInterval(0.1, base_hpr)
        
        animation = Sequence(
            Parallel(lunge, spin),
            Wait(0.1),
            Parallel(recover_pos, recover_hpr)
        )
        
        self.active_animations[f"{character_id}_attack_light"] = animation
        return animation
    
    def create_attack_heavy_animation(self, model, character_id: str) -> Interval:
        """创建heavy attack动画 - 强力冲击"""
        config = self.animation_configs['attack_heavy']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 蓄力（后退）
        charge = model.posInterval(
            0.2,
            Point3(base_pos.x, base_pos.y - 0.2, base_pos.z),
            blendType='easeOut'
        )
        
        # 强力前冲
        lunge = model.posInterval(
            config['lunge_speed'],
            Point3(base_pos.x, base_pos.y + config['lunge_distance'], base_pos.z),
            blendType='easeOut'
        )
        
        # 大角度旋转
        spin = model.hprInterval(
            config['lunge_speed'],
            Vec3(base_hpr.x + config['spin_angle'], base_hpr.y, base_hpr.z)
        )
        
        # 恢复
        recover_pos = model.posInterval(
            config['recovery_speed'],
            base_pos,
            blendType='easeIn'
        )
        recover_hpr = model.hprInterval(0.15, base_hpr)
        
        animation = Sequence(
            charge,
            Parallel(lunge, spin),
            Wait(0.15),
            Parallel(recover_pos, recover_hpr)
        )
        
        self.active_animations[f"{character_id}_attack_heavy"] = animation
        return animation
    
    def create_hurt_animation(self, model, character_id: str) -> Interval:
        """创建hurt动画 - 受击后退"""
        config = self.animation_configs['hurt']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 后退
        knockback = model.posInterval(
            config['duration'] / 2,
            Point3(base_pos.x, base_pos.y - config['knockback'], base_pos.z),
            blendType='easeOut'
        )
        
        # 震动效果
        shake_left = model.hprInterval(
            config['duration'] / 6,
            Vec3(base_hpr.x - 5, base_hpr.y, base_hpr.z)
        )
        shake_right = model.hprInterval(
            config['duration'] / 6,
            Vec3(base_hpr.x + 5, base_hpr.y, base_hpr.z)
        )
        shake_sequence = Sequence(shake_left, shake_right, shake_left)
        
        # 恢复
        recover = model.posInterval(
            config['duration'] / 2,
            base_pos,
            blendType='easeIn'
        )
        reset_hpr = model.hprInterval(0.1, base_hpr)
        
        animation = Sequence(
            Parallel(knockback, shake_sequence),
            Parallel(recover, reset_hpr)
        )
        
        self.active_animations[f"{character_id}_hurt"] = animation
        return animation
    
    def create_victory_animation(self, model, character_id: str) -> Interval:
        """创建victory动画 - 胜利庆祝"""
        config = self.animation_configs['victory']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 跳跃
        jump_up = model.posInterval(
            0.3,
            Point3(base_pos.x, base_pos.y, base_pos.z + config['jump_height']),
            blendType='easeOut'
        )
        jump_down = model.posInterval(
            0.3,
            base_pos,
            blendType='easeIn'
        )
        
        # 旋转庆祝
        spin = model.hprInterval(
            1.0,
            Vec3(base_hpr.x + config['spin_angle'], base_hpr.y, base_hpr.z)
        )
        
        # pose保持
        hold = Wait(0.5)
        
        animation = Sequence(
            Parallel(jump_up, spin),
            jump_down,
            hold
        )
        
        self.active_animations[f"{character_id}_victory"] = animation
        return animation
    
    def create_defeat_animation(self, model, character_id: str) -> Interval:
        """创建defeat动画 - 倒地"""
        config = self.animation_configs['defeat']
        base_pos = model.getPos()
        base_hpr = model.getHpr()
        
        # 倒下
        fall = model.posInterval(
            config['fall_duration'],
            Point3(base_pos.x, base_pos.y, base_pos.z - 1.0),
            blendType='easeIn'
        )
        
        # 旋转倒地
        rotate = model.hprInterval(
            config['fall_duration'],
            Vec3(base_hpr.x, base_hpr.y + config['rotation_angle'], base_hpr.z),
            blendType='easeIn'
        )
        
        animation = Parallel(fall, rotate)
        
        self.active_animations[f"{character_id}_defeat"] = animation
        return animation
    
    def play_animation(self, model, animation_name: str, character_id: str, loop: bool = False) -> Optional[Interval]:
        """播放指定动画"""
        # 停止当前动画
        self.stop_animation(character_id, animation_name)
        
        # 创建新动画
        animation = None
        if animation_name == 'idle':
            animation = self.create_idle_animation(model, character_id)
        elif animation_name == 'walk':
            animation = self.create_walk_animation(model, character_id)
        elif animation_name == 'run':
            animation = self.create_run_animation(model, character_id)
        elif animation_name == 'jump':
            animation = self.create_jump_animation(model, character_id)
        elif animation_name in ['attack_light', 'light_attack']:
            animation = self.create_attack_light_animation(model, character_id)
        elif animation_name in ['attack_heavy', 'heavy_attack']:
            animation = self.create_attack_heavy_animation(model, character_id)
        elif animation_name == 'hurt':
            animation = self.create_hurt_animation(model, character_id)
        elif animation_name == 'victory':
            animation = self.create_victory_animation(model, character_id)
        elif animation_name == 'defeat':
            animation = self.create_defeat_animation(model, character_id)
        
        if animation:
            animation.start()
            return animation
        
        return None
    
    def stop_animation(self, character_id: str, animation_name: str = None):
        """停止动画"""
        if animation_name:
            key = f"{character_id}_{animation_name}"
            if key in self.active_animations:
                self.active_animations[key].pause()
                del self.active_animations[key]
        else:
            # 停止所有该角色的动画
            keys_to_remove = [k for k in self.active_animations.keys() if k.startswith(character_id)]
            for key in keys_to_remove:
                self.active_animations[key].pause()
                del self.active_animations[key]
    
    def cleanup(self):
        """清理所有动画"""
        for animation in self.active_animations.values():
            animation.pause()
        self.active_animations.clear()
        print("✅ 程序化动画系统清理完成")


# 使用示例
if __name__ == "__main__":
    print("程序化动画系统测试")
    print("=" * 50)
    print("支持的动画类型:")
    print("  - idle: 轻微浮动和呼吸效果")
    print("  - walk: 前后摇摆和跳动")
    print("  - run: 更快更剧烈的移动")
    print("  - jump: 跳跃和旋转")
    print("  - attack_light: 快速冲击")
    print("  - attack_heavy: 强力冲击")
    print("  - hurt: 受击后退")
    print("  - victory: 胜利庆祝")
    print("  - defeat: 倒地")
    print("=" * 50)
    print("✅ 程序化动画系统就绪！")
