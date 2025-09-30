#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2.5D Animation Enhancement System Test
Test animation interpolation, motion blur, hit stop and other features
"""

import sys
from pathlib import Path

# Add project path
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
    """Test animation enhancement system"""
    print("=" * 80)
    print("Testing Animation Enhancement System")
    print("=" * 80)
    
    pygame.init()
    
    # Create test screen
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Animation Enhancer Test")
    clock = pygame.time.Clock()
    
    # Initialize systems
    enhancer = AnimationEnhancer(screen_size=(800, 600))
    vfx = EnhancedVFXSystem(800, 600)
    
    # Create test sprite
    test_surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.circle(test_surface, (255, 100, 100, 255), (32, 32), 30)
    
    # Test variables
    position = [100.0, 300.0]
    velocity = [300.0, 0.0]
    hit_test_timer = 0.0
    
    running = True
    frame_count = 0
    
    print("\nFeature List:")
    print("1. Motion Blur - Automatic display")
    print("2. Hit Stop - Press SPACE to trigger")
    print("3. Impact Flash - Triggers with hit stop")
    print("4. Punch Trail - Press P to trigger")
    print("5. Kick Trail - Press K to trigger")
    print("6. Impact Ring - Press R to trigger")
    print("7. ESC to exit")
    print()
    
    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Trigger hit effect
                    print(f"[Frame {frame_count}] Triggered Heavy Hit")
                    enhancer.on_hit("heavy", (position[0], position[1]))
                    vfx.create_hit_effect(position[0], position[1], "heavy")
                    vfx.create_impact_ring(position[0], position[1])
                elif event.key == pygame.K_p:
                    # Trigger punch trail
                    print(f"[Frame {frame_count}] Triggered Punch Trail")
                    end_x = position[0] + 100
                    end_y = position[1]
                    vfx.create_punch_trail(position[0], position[1], end_x, end_y)
                elif event.key == pygame.K_k:
                    # Trigger kick trail
                    print(f"[Frame {frame_count}] Triggered Kick Trail")
                    import math
                    direction = 0  # Right
                    vfx.create_kick_trail(position[0], position[1], direction, radius=80)
                elif event.key == pygame.K_r:
                    # Trigger impact ring
                    print(f"[Frame {frame_count}] Triggered Impact Ring")
                    vfx.create_impact_ring(position[0], position[1])
        
        # Update systems
        modified_dt = enhancer.update(dt)
        vfx.update(dt)
        
        # Update position (using modified dt)
        position[0] += velocity[0] * modified_dt
        
        # Boundary bounce
        if position[0] > 700 or position[0] < 100:
            velocity[0] = -velocity[0]
        
        # Add motion blur frame (every 3 frames)
        if frame_count % 3 == 0:
            enhancer.add_motion_blur_frame(
                test_surface,
                (position[0], position[1]),
                velocity=(velocity[0], velocity[1]),
                force=False
            )
        
        # Auto trigger hit test (every 2 seconds)
        hit_test_timer += dt
        if hit_test_timer > 2.0:
            hit_test_timer = 0.0
            # Random trigger different intensity hits
            import random
            hit_types = ["light", "medium", "heavy"]
            hit_type = random.choice(hit_types)
            print(f"[Frame {frame_count}] Auto triggered {hit_type.upper()} Hit")
            enhancer.on_hit(hit_type, (position[0], position[1]))
            vfx.create_hit_effect(position[0], position[1], hit_type)
        
        # Render
        screen.fill((20, 20, 30))
        
        # Render motion blur
        enhancer.render_motion_blur(screen)
        
        # Render VFX particles and trails
        vfx.render(screen)
        
        # Render main sprite
        sprite_rect = test_surface.get_rect(center=(int(position[0]), int(position[1])))
        screen.blit(test_surface, sprite_rect)
        
        # Render impact flash
        enhancer.render_impact_flash(screen)
        
        # Display info
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
    print("\nTest completed!")


def test_easing_functions():
    """Test easing functions"""
    print("\n" + "=" * 80)
    print("Testing Easing Functions")
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
    print("2.5D Animation Enhancement System Test Suite")
    print("=" * 80)
    
    # Test easing functions
    test_easing_functions()
    
    # Test animation enhancement system
    try:
        test_animation_enhancer()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
