# 摄像机系统
# 处理视角移动、缩放和世界坐标转换

import pygame
import math
from typing import Tuple

class Camera:
    """摄像机类，处理视角控制和坐标转换"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 摄像机位置（世界坐标）
        self.x = 0.0
        self.y = 0.0

        # 缩放级别
        self.zoom = 1.0
        self.min_zoom = 0.3
        self.max_zoom = 3.0

        # 移动速度
        self.move_speed = 300.0  # 像素每秒
        self.zoom_speed = 0.1

        # 平滑移动
        self.target_x = 0.0
        self.target_y = 0.0
        self.smooth_factor = 0.1

        # 边界限制
        self.world_width = 2000
        self.world_height = 1500
        self.enable_bounds = True

    def update(self, dt: float, keys_pressed):
        """更新摄像机状态"""
        # 处理键盘输入
        move_x = 0
        move_y = 0

        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            move_x -= 1
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            move_x += 1
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            move_y -= 1
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            move_y += 1

        # 应用移动
        if move_x != 0 or move_y != 0:
            # 归一化对角线移动
            length = math.sqrt(move_x * move_x + move_y * move_y)
            move_x /= length
            move_y /= length

            # 考虑缩放影响移动速度
            effective_speed = self.move_speed / self.zoom

            self.target_x += move_x * effective_speed * dt
            self.target_y += move_y * effective_speed * dt

        # 平滑移动到目标位置
        self.x += (self.target_x - self.x) * self.smooth_factor
        self.y += (self.target_y - self.y) * self.smooth_factor

        # 应用边界限制
        if self.enable_bounds:
            self._apply_bounds()

    def _apply_bounds(self):
        """应用摄像机边界限制"""
        # 计算可视区域大小
        visible_width = self.screen_width / self.zoom
        visible_height = self.screen_height / self.zoom

        # 限制摄像机不超出世界边界
        min_x = visible_width / 2
        max_x = self.world_width - visible_width / 2
        min_y = visible_height / 2
        max_y = self.world_height - visible_height / 2

        # 如果可视区域大于世界，居中显示
        if visible_width >= self.world_width:
            self.x = self.target_x = self.world_width / 2
        else:
            self.x = self.target_x = max(min_x, min(max_x, self.x))

        if visible_height >= self.world_height:
            self.y = self.target_y = self.world_height / 2
        else:
            self.y = self.target_y = max(min_y, min(max_y, self.y))

    def handle_event(self, event) -> bool:
        """处理摄像机相关事件"""
        if event.type == pygame.MOUSEWHEEL:
            # 缩放
            old_zoom = self.zoom
            if event.y > 0:  # 向上滚动，放大
                self.zoom = min(self.max_zoom, self.zoom + self.zoom_speed)
            else:  # 向下滚动，缩小
                self.zoom = max(self.min_zoom, self.zoom - self.zoom_speed)

            # 以鼠标为中心缩放
            if self.zoom != old_zoom:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self._zoom_at_point(mouse_x, mouse_y, old_zoom)

            return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # 中键按下，开始拖拽
                self.dragging = True
                self.drag_start = pygame.mouse.get_pos()
                self.drag_start_cam = (self.x, self.y)
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:  # 中键释放，结束拖拽
                self.dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if hasattr(self, 'dragging') and self.dragging:
                # 拖拽移动摄像机
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = (mouse_x - self.drag_start[0]) / self.zoom
                dy = (mouse_y - self.drag_start[1]) / self.zoom

                self.target_x = self.drag_start_cam[0] - dx
                self.target_y = self.drag_start_cam[1] - dy
                self.x = self.target_x
                self.y = self.target_y

                if self.enable_bounds:
                    self._apply_bounds()

                return True

        return False

    def _zoom_at_point(self, screen_x: int, screen_y: int, old_zoom: float):
        """在指定屏幕点进行缩放"""
        # 将屏幕坐标转换为世界坐标（使用旧缩放）
        world_x = self.x + (screen_x - self.screen_width / 2) / old_zoom
        world_y = self.y + (screen_y - self.screen_height / 2) / old_zoom

        # 计算新的摄像机位置，使世界坐标点保持在相同的屏幕位置
        self.target_x = world_x - (screen_x - self.screen_width / 2) / self.zoom
        self.target_y = world_y - (screen_y - self.screen_height / 2) / self.zoom

        self.x = self.target_x
        self.y = self.target_y

    def move_to(self, world_x: float, world_y: float, smooth: bool = True):
        """移动摄像机到指定世界坐标"""
        if smooth:
            self.target_x = world_x
            self.target_y = world_y
        else:
            self.x = self.target_x = world_x
            self.y = self.target_y = world_y

        if self.enable_bounds:
            self._apply_bounds()

    def follow_target(self, target_x: float, target_y: float, follow_speed: float = 0.05):
        """跟随目标"""
        self.target_x += (target_x - self.x) * follow_speed
        self.target_y += (target_y - self.y) * follow_speed

        if self.enable_bounds:
            self._apply_bounds()

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """将世界坐标转换为屏幕坐标"""
        screen_x = (world_x - self.x) * self.zoom + self.screen_width / 2
        screen_y = (world_y - self.y) * self.zoom + self.screen_height / 2
        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """将屏幕坐标转换为世界坐标"""
        world_x = self.x + (screen_x - self.screen_width / 2) / self.zoom
        world_y = self.y + (screen_y - self.screen_height / 2) / self.zoom
        return world_x, world_y

    def is_visible(self, world_x: float, world_y: float, margin: float = 50) -> bool:
        """检查世界坐标点是否在可视范围内"""
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        return (-margin <= screen_x <= self.screen_width + margin and
                -margin <= screen_y <= self.screen_height + margin)

    def get_visible_rect(self) -> Tuple[float, float, float, float]:
        """获取可视区域的世界坐标矩形 (x, y, width, height)"""
        visible_width = self.screen_width / self.zoom
        visible_height = self.screen_height / self.zoom

        x = self.x - visible_width / 2
        y = self.y - visible_height / 2

        return x, y, visible_width, visible_height

    def shake(self, intensity: float, duration: float):
        """摄像机震动效果"""
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_time = 0

    def get_info(self) -> dict:
        """获取摄像机信息"""
        return {
            'x': int(self.x),
            'y': int(self.y),
            'zoom': self.zoom,
            'visible_width': int(self.screen_width / self.zoom),
            'visible_height': int(self.screen_height / self.zoom)
        }

    def set_world_bounds(self, width: int, height: int):
        """设置世界边界"""
        self.world_width = width
        self.world_height = height

        if self.enable_bounds:
            self._apply_bounds()

    def reset(self):
        """重置摄像机到初始状态"""
        self.x = self.target_x = self.world_width / 2
        self.y = self.target_y = self.world_height / 2
        self.zoom = 1.0

        if hasattr(self, 'dragging'):
            self.dragging = False
