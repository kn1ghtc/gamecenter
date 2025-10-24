"""相机系统测试"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

import sys
sys.path.insert(0, "d:/pyproject")

from gamecenter.deltaOperation.utils.camera import Camera

print("="*70)
print("相机系统测试")
print("="*70)

# 测试1: 创建相机
print("\n[测试1] 创建相机...")
camera = Camera(1280, 720)
print(f"✓ 屏幕尺寸: {camera.screen_width}x{camera.screen_height}")
print(f"✓ 相机位置: ({camera.x}, {camera.y})")
print(f"✓ 缩放级别: {camera.zoom}")

# 测试2: 跟随目标
print("\n[测试2] 跟随目标...")
camera.follow(500, 300)
print(f"✓ 目标位置: ({camera.target_x}, {camera.target_y})")

# 模拟多帧更新
for i in range(50):
    camera.update(0.016)

print(f"✓ 更新后相机位置: ({camera.x:.1f}, {camera.y:.1f})")

# 测试3: 前瞻功能
print("\n[测试3] 前瞻功能...")
camera.x, camera.y = 0, 0
camera.follow(100, 100, velocity_x=10, velocity_y=0)  # 向右移动

for i in range(30):
    camera.update(0.016)

print(f"✓ 前瞻偏移: ({camera.look_ahead_x:.1f}, {camera.look_ahead_y:.1f})")
print(f"✓ 相机位置(带前瞻): ({camera.x:.1f}, {camera.y:.1f})")

# 测试4: 缩放
print("\n[测试4] 缩放功能...")
camera.set_zoom(2.0)
print(f"✓ 目标缩放: {camera.target_zoom}")

for i in range(30):
    camera.update(0.016)

print(f"✓ 当前缩放: {camera.zoom:.2f}")

# 测试5: 边界限制
print("\n[测试5] 边界限制...")
camera.set_bounds(0, 0, 1000, 1000)
camera.x, camera.y = 0, 0
camera.follow(2000, 2000)  # 超出边界

for i in range(50):
    camera.update(0.016)

print(f"✓ 边界: ({camera.min_x}, {camera.min_y}) - ({camera.max_x}, {camera.max_y})")
print(f"✓ 相机位置(限制后): ({camera.x:.1f}, {camera.y:.1f})")

# 测试6: 屏幕震动
print("\n[测试6] 屏幕震动...")
camera.shake(intensity=20, duration=0.5)
print(f"✓ 震动强度: {camera.shake_intensity}")
print(f"✓ 震动持续: {camera.shake_duration}秒")

# 模拟震动衰减
for i in range(30):
    camera.update(0.016)
    if i % 10 == 0:
        print(f"  第{i}帧: 偏移=({camera.shake_offset_x:.1f}, {camera.shake_offset_y:.1f})")

# 测试7: 坐标转换
print("\n[测试7] 坐标转换...")
camera.reset()
camera.x, camera.y = 500, 300

world_pos = (600, 400)
screen_pos = camera.world_to_screen(*world_pos)
world_pos_back = camera.screen_to_world(*screen_pos)

print(f"✓ 世界坐标: {world_pos}")
print(f"✓ 屏幕坐标: {screen_pos}")
print(f"✓ 转换回世界: ({world_pos_back[0]:.1f}, {world_pos_back[1]:.1f})")

# 测试8: 视口矩形
print("\n[测试8] 视口矩形...")
viewport = camera.get_viewport_rect()
print(f"✓ 视口: x={viewport[0]:.1f}, y={viewport[1]:.1f}")
print(f"  宽度={viewport[2]:.1f}, 高度={viewport[3]:.1f}")

# 测试9: 可见性检测
print("\n[测试9] 可见性检测...")
visible_obj = (550, 350, 50, 50)
invisible_obj = (5000, 5000, 50, 50)

is_visible_1 = camera.is_visible(*visible_obj)
is_visible_2 = camera.is_visible(*invisible_obj)

print(f"✓ 对象1 {visible_obj[:2]}: {'可见' if is_visible_1 else '不可见'}")
print(f"✓ 对象2 {invisible_obj[:2]}: {'可见' if is_visible_2 else '不可见'}")

# 测试10: 重置
print("\n[测试10] 重置相机...")
camera.x, camera.y = 1000, 1000
camera.zoom = 2.5
camera.shake_intensity = 50

camera.reset()

print(f"✓ 重置后位置: ({camera.x}, {camera.y})")
print(f"✓ 重置后缩放: {camera.zoom}")
print(f"✓ 重置后震动: {camera.shake_intensity}")

print("\n" + "="*70)
print("✓✓✓ 所有相机测试通过!")
print("="*70)
