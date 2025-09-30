"""
测试程序化动画系统
Test Procedural Animation System
"""

import sys
from pathlib import Path

# Bootstrap
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT_STR = str(_PROJECT_ROOT)
if _PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT_STR)

from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4, Point3
from gamecenter.streetBattle.enhanced_character_manager import EnhancedCharacterManager
from gamecenter.streetBattle.enhanced_3d_animation_system import Animation3DManager, AnimationState


class ProceduralAnimationTest(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        
        # Camera
        self.camera.setPos(0, -15, 3)
        self.camera.lookAt(0, 0, 1)
        
        # Lights
        ambient = AmbientLight('ambient')
        ambient.setColor(Vec4(0.4, 0.4, 0.4, 1))
        ambientNP = self.render.attachNewNode(ambient)
        self.render.setLight(ambientNP)
        
        directional = DirectionalLight('directional')
        directional.setColor(Vec4(0.8, 0.8, 0.8, 1))
        directionalNP = self.render.attachNewNode(directional)
        directionalNP.setHpr(-30, -60, 0)
        self.render.setLight(directionalNP)
        
        print("\n" + "="*60)
        print("🎬 程序化动画系统测试")
        print("="*60)
        
        # Character manager
        self.char_manager = EnhancedCharacterManager(self)
        
        # Animation manager
        self.animation_manager = Animation3DManager()
        
        # 加载测试角色
        self.test_characters = ['Kyo Kusanagi', 'Iori Yagami']
        self.models = []
        self.state_machines = []
        
        for i, char_name in enumerate(self.test_characters):
            print(f"\n🎯 加载测试角色 {i+1}: {char_name}")
            pos = Point3(-3 + i * 6, 0, 0)
            model = self.char_manager.create_character_model(char_name, pos)
            
            if model:
                self.models.append(model)
                
                # 注册到动画管理器
                state_machine = self.animation_manager.register_character(
                    f"test_char_{i}",
                    model,
                    char_name
                )
                
                if state_machine:
                    self.state_machines.append(state_machine)
                    print(f"✅ {char_name} 动画状态机已注册")
                    print(f"   使用程序化动画: {state_machine.use_procedural_animation}")
                else:
                    print(f"❌ {char_name} 动画状态机注册失败")
            else:
                print(f"❌ {char_name} 模型加载失败")
        
        # 动画测试序列
        self.animation_sequence = [
            (AnimationState.IDLE, 3.0, "空闲站立"),
            (AnimationState.WALK, 2.0, "行走"),
            (AnimationState.RUN, 2.0, "奔跑"),
            (AnimationState.ATTACK_LIGHT, 1.5, "轻攻击"),
            (AnimationState.ATTACK_HEAVY, 2.0, "重攻击"),
            (AnimationState.JUMP, 1.5, "跳跃"),
            (AnimationState.HURT, 1.5, "受伤"),
            (AnimationState.VICTORY, 3.0, "胜利"),
        ]
        
        self.current_animation_index = 0
        self.animation_timer = 0
        self.test_completed = False  # 添加完成标志
        
        # 开始测试
        if self.state_machines:
            self._start_next_animation()
            self.taskMgr.add(self.update_test, 'update-test')
            print("\n✅ 测试开始！\n")
        else:
            print("\n❌ 没有可用的动画状态机，测试失败\n")
            sys.exit(1)
        
        # ESC退出
        self.accept('escape', sys.exit)
    
    def _start_next_animation(self):
        """开始下一个动画"""
        if self.current_animation_index >= len(self.animation_sequence):
            print("\n" + "="*60)
            print("✅ 所有动画测试完成！")
            print("="*60)
            print("\n按ESC退出（或等待3秒自动退出）")
            # 标记测试完成，停止更新任务
            self.test_completed = True
            # 3秒后自动退出
            self.taskMgr.doMethodLater(3.0, lambda task: sys.exit(0), 'auto_exit')
            return
        
        state, duration, description = self.animation_sequence[self.current_animation_index]
        self.animation_timer = duration
        
        print(f"\n🎬 测试动画 {self.current_animation_index + 1}/{len(self.animation_sequence)}: {description}")
        print(f"   状态: {state.value}, 持续: {duration}秒")
        
        # 为所有测试角色播放动画
        for state_machine in self.state_machines:
            state_machine.request_state_change(state, force=True)
    
    def update_test(self, task):
        """更新测试"""
        # 如果测试已完成，停止更新
        if self.test_completed:
            return task.done
        
        dt = self.clock.get_dt()
        
        # 更新动画管理器
        self.animation_manager.update_all(dt)
        
        # 更新动画计时器
        self.animation_timer -= dt
        if self.animation_timer <= 0:
            self.current_animation_index += 1
            self._start_next_animation()
        
        return task.cont


if __name__ == "__main__":
    app = ProceduralAnimationTest()
    app.run()
