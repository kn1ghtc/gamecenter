#!/usr/bin/env python3
"""
Animation Enhancement System for 2.5D Mode
2.5D模式动画增强系统

提供以下功能：
1. 动画帧插值（Frame Interpolation）- 平滑动画过渡
2. 残影效果（Motion Blur/After Image）- 快速移动时的视觉反馈
3. 动画缓动（Easing）- 更自然的动作曲线
4. 打击停顿（Hit Stop）- 增强打击感
5. 屏幕震动（Screen Shake）- 强化冲击感
"""

try:
    import pygame
    from pygame import Surface
    import math
    from typing import List, Tuple, Optional, Dict, Any
    from dataclasses import dataclass
    from collections import deque
except ImportError:
    pygame = None


@dataclass
class AfterImage:
    """残影数据类"""
    surface: Any  # pygame.Surface
    position: Tuple[float, float]
    alpha: int
    lifetime: float
    max_lifetime: float


class EasingFunctions:
    """缓动函数集合 - 提供多种动画曲线"""
    
    @staticmethod
    def linear(t: float) -> float:
        """线性 - 匀速运动"""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """二次缓入 - 慢速启动"""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """二次缓出 - 慢速结束"""
        return t * (2.0 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """二次缓入缓出 - 慢速启动和结束"""
        if t < 0.5:
            return 2.0 * t * t
        return -1.0 + (4.0 - 2.0 * t) * t
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """三次缓入 - 更强的慢速启动"""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """三次缓出 - 更强的慢速结束"""
        t -= 1.0
        return t * t * t + 1.0
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """三次缓入缓出"""
        if t < 0.5:
            return 4.0 * t * t * t
        t -= 1.0
        return 1.0 + 4.0 * t * t * t
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """弹性缓出 - 弹簧效果"""
        if t == 0 or t == 1:
            return t
        return pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """回退缓出 - 超出后回弹"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


class FrameInterpolator:
    """帧插值器 - 在两个动画帧之间进行平滑过渡"""
    
    def __init__(self, interpolation_factor: float = 0.5):
        """
        Args:
            interpolation_factor: 插值因子，0.0-1.0，值越大插值效果越明显
        """
        if pygame is None:
            raise RuntimeError("Pygame is required for Frame Interpolation")
        
        self.interpolation_factor = max(0.0, min(1.0, interpolation_factor))
        self.enabled = True
    
    def interpolate_frames(self, 
                          frame1: Surface, 
                          frame2: Surface, 
                          progress: float) -> Surface:
        """
        在两个帧之间进行插值混合
        
        Args:
            frame1: 当前帧
            frame2: 下一帧
            progress: 进度 (0.0-1.0)
        
        Returns:
            混合后的帧
        """
        if not self.enabled or progress <= 0.0:
            return frame1
        if progress >= 1.0:
            return frame2
        
        # 确保两个帧尺寸相同
        if frame1.get_size() != frame2.get_size():
            return frame1
        
        # 应用插值因子调整实际混合比例
        blend_ratio = progress * self.interpolation_factor
        
        # 创建混合帧
        blended = frame1.copy()
        temp = frame2.copy()
        
        # 设置透明度进行混合
        alpha = int(255 * blend_ratio)
        temp.set_alpha(alpha)
        
        blended.blit(temp, (0, 0))
        return blended
    
    def interpolate_position(self, 
                           pos1: Tuple[float, float],
                           pos2: Tuple[float, float],
                           progress: float,
                           easing_func=None) -> Tuple[float, float]:
        """
        在两个位置之间进行插值
        
        Args:
            pos1: 起始位置
            pos2: 目标位置
            progress: 进度 (0.0-1.0)
            easing_func: 缓动函数
        
        Returns:
            插值后的位置
        """
        if not self.enabled:
            return pos1
        
        # 应用缓动函数
        if easing_func:
            progress = easing_func(progress)
        
        x = pos1[0] + (pos2[0] - pos1[0]) * progress
        y = pos1[1] + (pos2[1] - pos1[1]) * progress
        return (x, y)


class MotionBlurRenderer:
    """运动模糊渲染器 - 创建残影效果"""
    
    def __init__(self, max_trail_length: int = 5, fade_speed: float = 0.8):
        """
        Args:
            max_trail_length: 最大残影数量
            fade_speed: 淡出速度 (值越大消失越快)
        """
        if pygame is None:
            raise RuntimeError("Pygame is required for Motion Blur")
        
        self.max_trail_length = max_trail_length
        self.fade_speed = fade_speed
        self.after_images: deque = deque(maxlen=max_trail_length)
        self.enabled = True
        self.velocity_threshold = 300.0  # 速度阈值，超过此值才产生残影
    
    def update(self, dt: float):
        """更新残影状态"""
        if not self.enabled:
            return
        
        # 更新所有残影的生命周期
        for after_image in list(self.after_images):
            after_image.lifetime -= dt * self.fade_speed
            
            # 更新透明度
            if after_image.lifetime > 0:
                life_ratio = after_image.lifetime / after_image.max_lifetime
                after_image.alpha = int(180 * life_ratio)  # 最大透明度180
            else:
                self.after_images.remove(after_image)
    
    def add_after_image(self, 
                       surface: Surface, 
                       position: Tuple[float, float],
                       velocity: Optional[Tuple[float, float]] = None,
                       force: bool = False):
        """
        添加残影
        
        Args:
            surface: 角色表面
            position: 当前位置
            velocity: 当前速度（用于判断是否需要残影）
            force: 强制添加残影（忽略速度阈值）
        """
        if not self.enabled and not force:
            return
        
        # 检查速度是否足够快
        if velocity and not force:
            speed = math.sqrt(velocity[0]**2 + velocity[1]**2)
            if speed < self.velocity_threshold:
                return
        
        # 创建残影副本
        after_image_surface = surface.copy()
        
        # 创建残影对象
        after_image = AfterImage(
            surface=after_image_surface,
            position=position,
            alpha=180,
            lifetime=0.15,  # 残影存在时间
            max_lifetime=0.15
        )
        
        self.after_images.append(after_image)
    
    def render(self, screen: Surface, camera_offset: Tuple[int, int] = (0, 0)):
        """渲染所有残影"""
        if not self.enabled:
            return
        
        for after_image in self.after_images:
            if after_image.alpha > 0:
                # 应用透明度
                temp_surface = after_image.surface.copy()
                temp_surface.set_alpha(after_image.alpha)
                
                # 计算渲染位置
                render_pos = (
                    int(after_image.position[0]) + camera_offset[0],
                    int(after_image.position[1]) + camera_offset[1]
                )
                
                # 渲染残影
                rect = temp_surface.get_rect()
                rect.midbottom = render_pos
                screen.blit(temp_surface, rect)
    
    def clear(self):
        """清除所有残影"""
        self.after_images.clear()


class HitStopManager:
    """打击停顿管理器 - 增强打击感"""
    
    def __init__(self):
        if pygame is None:
            raise RuntimeError("Pygame is required for Hit Stop")
        
        self.hitstop_timer = 0.0
        self.hitstop_intensity = 0.0
        self.enabled = True
        
        # 打击停顿配置
        self.light_hit_duration = 0.06   # 轻攻击停顿时间
        self.medium_hit_duration = 0.12  # 中攻击停顿时间
        self.heavy_hit_duration = 0.18   # 重攻击停顿时间
        self.special_hit_duration = 0.25 # 必杀技停顿时间
    
    def trigger_hitstop(self, hit_type: str = "light"):
        """
        触发打击停顿
        
        Args:
            hit_type: 打击类型 ("light", "medium", "heavy", "special")
        """
        if not self.enabled:
            return
        
        duration_map = {
            "light": self.light_hit_duration,
            "medium": self.medium_hit_duration,
            "heavy": self.heavy_hit_duration,
            "special": self.special_hit_duration
        }
        
        self.hitstop_timer = duration_map.get(hit_type, self.light_hit_duration)
        self.hitstop_intensity = 1.0
    
    def update(self, dt: float) -> float:
        """
        更新打击停顿状态
        
        Returns:
            修正后的dt（考虑打击停顿）
        """
        if not self.enabled or self.hitstop_timer <= 0:
            return dt
        
        self.hitstop_timer -= dt
        
        if self.hitstop_timer <= 0:
            self.hitstop_timer = 0.0
            self.hitstop_intensity = 0.0
            return dt
        else:
            # 在打击停顿期间，减缓时间流速
            return dt * 0.1  # 10%的时间流速
    
    def is_active(self) -> bool:
        """检查打击停顿是否激活"""
        return self.enabled and self.hitstop_timer > 0


class ImpactFlashRenderer:
    """冲击闪光渲染器 - 打击时的闪光效果"""
    
    def __init__(self):
        if pygame is None:
            raise RuntimeError("Pygame is required for Impact Flash")
        
        self.flash_timer = 0.0
        self.flash_color = (255, 255, 255)
        self.flash_alpha = 0
        self.enabled = True
    
    def trigger_flash(self, 
                     intensity: float = 1.0,
                     color: Tuple[int, int, int] = (255, 255, 255),
                     duration: float = 0.08):
        """
        触发闪光效果
        
        Args:
            intensity: 强度 (0.0-1.0)
            color: 闪光颜色
            duration: 持续时间
        """
        if not self.enabled:
            return
        
        self.flash_timer = duration
        self.flash_color = color
        self.flash_alpha = int(200 * intensity)
    
    def update(self, dt: float):
        """更新闪光状态"""
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_timer = 0.0
                self.flash_alpha = 0
    
    def render(self, screen: Surface):
        """渲染闪光效果"""
        if not self.enabled or self.flash_alpha <= 0:
            return
        
        # 创建闪光表面
        flash_surface = pygame.Surface(screen.get_size())
        flash_surface.fill(self.flash_color)
        flash_surface.set_alpha(self.flash_alpha)
        
        # 渲染闪光
        screen.blit(flash_surface, (0, 0))


class AnimationEnhancer:
    """动画增强系统 - 综合管理所有动画增强功能"""
    
    def __init__(self, screen_size: Tuple[int, int] = (1280, 720)):
        if pygame is None:
            raise RuntimeError("Pygame is required for Animation Enhancer")
        
        self.screen_size = screen_size
        
        # 初始化各个子系统
        self.frame_interpolator = FrameInterpolator(interpolation_factor=0.6)
        self.motion_blur = MotionBlurRenderer(max_trail_length=4, fade_speed=1.2)
        self.hitstop_manager = HitStopManager()
        self.impact_flash = ImpactFlashRenderer()
        
        # 全局启用/禁用
        self.enabled = True
    
    def update(self, dt: float) -> float:
        """
        更新所有增强系统
        
        Returns:
            修正后的dt
        """
        if not self.enabled:
            return dt
        
        # 更新打击停顿（可能修改dt）
        modified_dt = self.hitstop_manager.update(dt)
        
        # 更新其他系统
        self.motion_blur.update(dt)
        self.impact_flash.update(dt)
        
        return modified_dt
    
    def render_motion_blur(self, screen: Surface, camera_offset: Tuple[int, int] = (0, 0)):
        """渲染残影效果"""
        if self.enabled:
            self.motion_blur.render(screen, camera_offset)
    
    def render_impact_flash(self, screen: Surface):
        """渲染冲击闪光"""
        if self.enabled:
            self.impact_flash.render(screen)
    
    def on_hit(self, hit_type: str = "light", impact_position: Optional[Tuple[float, float]] = None):
        """
        打击事件处理
        
        Args:
            hit_type: 打击类型
            impact_position: 打击位置（用于额外效果）
        """
        if not self.enabled:
            return
        
        # 触发打击停顿
        self.hitstop_manager.trigger_hitstop(hit_type)
        
        # 触发闪光效果
        intensity_map = {
            "light": 0.3,
            "medium": 0.5,
            "heavy": 0.7,
            "special": 1.0
        }
        self.impact_flash.trigger_flash(intensity=intensity_map.get(hit_type, 0.3))
    
    def add_motion_blur_frame(self,
                             surface: Surface,
                             position: Tuple[float, float],
                             velocity: Optional[Tuple[float, float]] = None,
                             force: bool = False):
        """添加运动残影帧"""
        if self.enabled:
            self.motion_blur.add_after_image(surface, position, velocity, force)
    
    def interpolate_animation_frames(self,
                                    current_frame: Surface,
                                    next_frame: Surface,
                                    progress: float) -> Surface:
        """插值动画帧"""
        if self.enabled:
            return self.frame_interpolator.interpolate_frames(
                current_frame, next_frame, progress
            )
        return current_frame
    
    def toggle_feature(self, feature: str, enabled: bool):
        """
        切换特定功能
        
        Args:
            feature: 功能名称 ("interpolation", "motion_blur", "hitstop", "flash")
            enabled: 启用/禁用
        """
        feature_map = {
            "interpolation": self.frame_interpolator,
            "motion_blur": self.motion_blur,
            "hitstop": self.hitstop_manager,
            "flash": self.impact_flash
        }
        
        if feature in feature_map:
            feature_map[feature].enabled = enabled


# 全局实例
_global_enhancer: Optional[AnimationEnhancer] = None


def get_animation_enhancer() -> AnimationEnhancer:
    """获取全局动画增强器实例"""
    global _global_enhancer
    if _global_enhancer is None:
        _global_enhancer = AnimationEnhancer()
    return _global_enhancer


def reset_animation_enhancer():
    """重置全局动画增强器"""
    global _global_enhancer
    _global_enhancer = None


__all__ = [
    "AnimationEnhancer",
    "FrameInterpolator",
    "MotionBlurRenderer",
    "HitStopManager",
    "ImpactFlashRenderer",
    "EasingFunctions",
    "AfterImage",
    "get_animation_enhancer",
    "reset_animation_enhancer"
]
