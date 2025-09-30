#!/usr/bin/env python3
"""
2.5D动画增强系统测试
测试动画插值、残影、打击停顿等功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pygame
from gamecenter.streetBattle.twod5.animation_enhancer import (
    AnimationEnhancer,
    EasingFunctions,
    get_animation_enhancer
)
from gamecenter.streetBattle.twod5.enhanced_vfx import EnhancedVFXSystem


def test_animation_enhancer():
    """测试动画增强系统"""
    print("=" * 80)
    print("测试动画增强系统")
    print("=" * 80)
    
    pygame.init()
    
    # 创建测试屏幕
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Animation Enhancer Test")
    clock = pygame.time.Clock()
    
    # 初始化系统
    enhancer = AnimationEnhancer(screen_size=(800, 600))
    vfx = EnhancedVFXSystem(800, 600)
    
    # 创建测试精灵
    test_surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.circle(test_surface, (255, 100, 100, 255), (32, 32), 30)
    
    # 测试变量
    position = [100.0, 300.0]
    velocity = [300.0, 0.0]
    hit_test_timer = 0.0
    
    running = True
    frame_count = 0
    
    print("\n测试功能列表:")
    print("1. 残影效果 (Motion Blur) - 自动显示")
    print("2. 打击停顿 (Hit Stop) - 按 SPACE 触发")
    print("3. 冲击闪光 (Impact Flash) - 随打击停顿触发")
    print("4. 出拳轨迹 (Punch Trail) - 按 P 触发")
    print("5. 出腿轨迹 (Kick Trail) - 按 K 触发")
    print("6. 冲击波环 (Impact Ring) - 按 R 触发")
    print("7. ESC 退出")
    print()
    
    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # 触发打击效果
                    print(f"[Frame {frame_count}] 触发 Heavy Hit")
                    enhancer.on_hit("heavy", (position[0], position[1]))
                    vfx.create_hit_effect(position[0], position[1], "heavy")
                    vfx.create_impact_ring(position[0], position[1])
                elif event.key == pygame.K_p:
                    # 触发出拳轨迹
                    print(f"[Frame {frame_count}] 触发 Punch Trail")
                    end_x = position[0] + 100
                    end_y = position[1]
                    vfx.create_punch_trail(position[0], position[1], end_x, end_y)
                elif event.key == pygame.K_k:
                    # 触发出腿轨迹
                    print(f"[Frame {frame_count}] 触发 Kick Trail")
                    import math
                    direction = 0  # 向右
                    vfx.create_kick_trail(position[0], position[1], direction, radius=80)
                elif event.key == pygame.K_r:
                    # 触发冲击波
                    print(f"[Frame {frame_count}] 触发 Impact Ring")
                    vfx.create_impact_ring(position[0], position[1])
        
        # 更新系统
        modified_dt = enhancer.update(dt)
        vfx.update(dt)
        
        # 更新位置 (使用修正后的dt)
        position[0] += velocity[0] * modified_dt
        
        # 边界反弹
        if position[0] > 700 or position[0] < 100:
            velocity[0] = -velocity[0]
        
        # 添加残影帧 (每3帧添加一次)
        if frame_count % 3 == 0:
            enhancer.add_motion_blur_frame(
                test_surface,
                (position[0], position[1]),
                velocity=(velocity[0], velocity[1]),
                force=False
            )
        
        # 自动触发打击测试 (每2秒)
        hit_test_timer += dt
        if hit_test_timer > 2.0:
            hit_test_timer = 0.0
            # 随机触发不同强度的打击
            import random
            hit_types = ["light", "medium", "heavy"]
            hit_type = random.choice(hit_types)
            print(f"[Frame {frame_count}] 自动触发 {hit_type.upper()} Hit")
            enhancer.on_hit(hit_type, (position[0], position[1]))
            vfx.create_hit_effect(position[0], position[1], hit_type)
        
        # 渲染
        screen.fill((20, 20, 30))
        
        # 渲染残影
        enhancer.render_motion_blur(screen)
        
        # 渲染VFX粒子和轨迹
        vfx.render(screen)
        
        # 渲染主精灵
        sprite_rect = test_surface.get_rect(center=(int(position[0]), int(position[1])))
        screen.blit(test_surface, sprite_rect)
        
        # 渲染冲击闪光
        enhancer.render_impact_flash(screen)
        
        # 显示信息
        font = pygame.font.Font(None, 24)
        info_texts = [
            f"FPS: {clock.get_fps():.1f}",
            f"Frame: {frame_count}",
            f"Hit Stop: {'Active' if enhancer.hitstop_manager.is_active() else 'Inactive'}",
            f"Motion Blur: {len(enhancer.motion_blur.after_images)} frames",
            f"Particles: {len(vfx.particles)}",
            f"Attack Trails: {len(vfx.attack_trails)}",
            "",
            "Controls:",
            "SPACE - Heavy Hit",
            "P - Punch Trail",
            "K - Kick Trail",
            "R - Impact Ring"
        ]
        
        y_offset = 10
        for text in info_texts:
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
    
    pygame.quit()
    print("\n测试完成!")


def test_easing_functions():
    """测试缓动函数"""
    print("\n" + "=" * 80)
    print("测试缓动函数")
    print("=" * 80)
    
    test_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    
    easing_funcs = {
        "Linear": EasingFunctions.linear,
        "Ease In Quad": EasingFunctions.ease_in_quad,
        "Ease Out Quad": EasingFunctions.ease_out_quad,
        "Ease In Out Quad": EasingFunctions.ease_in_out_quad,
        "Ease In Cubic": EasingFunctions.ease_in_cubic,
        "Ease Out Cubic": EasingFunctions.ease_out_cubic,
        "Ease Out Elastic": EasingFunctions.ease_out_elastic,
        "Ease Out Back": EasingFunctions.ease_out_back
    }
    
    for func_name, func in easing_funcs.items():
        print(f"\n{func_name}:")
        results = [f"  t={t:.2f} -> {func(t):.4f}" for t in test_values]
        print("\n".join(results))


if __name__ == "__main__":
    print("2.5D动画增强系统测试套件")
    print("=" * 80)
    
    # 测试缓动函数
    test_easing_functions()
    
    # 测试动画增强系统
    try:
        test_animation_enhancer()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
