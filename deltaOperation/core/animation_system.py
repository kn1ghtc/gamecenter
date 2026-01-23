"""
动画系统 - Animation System
为三角洲行动提供完整的精灵动画支持

Features:
- 精灵动画状态机
- 平滑帧插值
- 动画混合与过渡
- 动态生成精灵（当素材缺失时）
"""

import sys
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

import pygame

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gamecenter.deltaOperation import config


class AnimationState(Enum):
    """动画状态枚举"""
    IDLE = "idle"
    WALK = "walk"
    RUN = "run"
    JUMP = "jump"
    FALL = "fall"
    CROUCH = "crouch"
    SHOOT = "shoot"
    RELOAD = "reload"
    HIT = "hit"
    DEATH = "death"
    MELEE = "melee"
    CLIMB = "climb"


@dataclass
class AnimationFrame:
    """动画帧数据"""
    surface: pygame.Surface
    duration: float  # 帧持续时间（秒）
    offset_x: float = 0.0  # X偏移
    offset_y: float = 0.0  # Y偏移


@dataclass
class AnimationClip:
    """动画片段"""
    name: str
    frames: List[AnimationFrame]
    loop: bool = True
    speed_multiplier: float = 1.0
    
    @property
    def total_duration(self) -> float:
        """获取动画总时长"""
        return sum(f.duration for f in self.frames)
    
    def get_frame_at_time(self, time: float) -> Tuple[AnimationFrame, int]:
        """根据时间获取当前帧"""
        if not self.frames:
            return None, 0
        
        total = self.total_duration
        if total <= 0:
            return self.frames[0], 0
        
        # 处理循环
        if self.loop:
            time = time % total
        else:
            time = min(time, total - 0.001)
        
        # 查找当前帧
        accumulated = 0.0
        for i, frame in enumerate(self.frames):
            accumulated += frame.duration * self.speed_multiplier
            if time < accumulated:
                return frame, i
        
        return self.frames[-1], len(self.frames) - 1


class AnimationController:
    """动画控制器 - 管理角色动画状态"""
    
    def __init__(self, width: int = 48, height: int = 64):
        """初始化动画控制器
        
        Args:
            width: 角色宽度
            height: 角色高度
        """
        self.width = width
        self.height = height
        
        # 动画数据
        self.clips: Dict[AnimationState, AnimationClip] = {}
        self.current_state = AnimationState.IDLE
        self.current_time = 0.0
        
        # 过渡状态
        self.transitioning = False
        self.transition_from: Optional[AnimationState] = None
        self.transition_progress = 0.0
        self.transition_duration = 0.1  # 100ms过渡时间
        
        # 回调
        self.on_animation_complete: Optional[callable] = None
        
        # 初始化默认动画
        self._generate_default_animations()
    
    def _generate_default_animations(self):
        """生成默认动画（当没有素材时使用）"""
        colors = {
            AnimationState.IDLE: (50, 150, 250),       # 蓝色
            AnimationState.WALK: (80, 180, 250),       # 浅蓝
            AnimationState.RUN: (100, 200, 250),       # 更浅蓝
            AnimationState.JUMP: (255, 180, 0),        # 橙色
            AnimationState.FALL: (255, 220, 100),      # 浅橙
            AnimationState.CROUCH: (100, 100, 200),    # 紫蓝
            AnimationState.SHOOT: (255, 80, 80),       # 红色
            AnimationState.RELOAD: (255, 255, 100),    # 黄色
            AnimationState.HIT: (255, 100, 100),       # 浅红
            AnimationState.DEATH: (80, 80, 80),        # 灰色
            AnimationState.MELEE: (255, 150, 50),      # 橙红
            AnimationState.CLIMB: (100, 200, 100),     # 绿色
        }
        
        frame_counts = {
            AnimationState.IDLE: 4,
            AnimationState.WALK: 8,
            AnimationState.RUN: 8,
            AnimationState.JUMP: 4,
            AnimationState.FALL: 2,
            AnimationState.CROUCH: 2,
            AnimationState.SHOOT: 3,
            AnimationState.RELOAD: 6,
            AnimationState.HIT: 2,
            AnimationState.DEATH: 6,
            AnimationState.MELEE: 4,
            AnimationState.CLIMB: 4,
        }
        
        frame_durations = {
            AnimationState.IDLE: 0.2,
            AnimationState.WALK: 0.1,
            AnimationState.RUN: 0.08,
            AnimationState.JUMP: 0.12,
            AnimationState.FALL: 0.15,
            AnimationState.CROUCH: 0.15,
            AnimationState.SHOOT: 0.05,
            AnimationState.RELOAD: 0.25,
            AnimationState.HIT: 0.15,
            AnimationState.DEATH: 0.2,
            AnimationState.MELEE: 0.08,
            AnimationState.CLIMB: 0.12,
        }
        
        loop_states = {
            AnimationState.IDLE: True,
            AnimationState.WALK: True,
            AnimationState.RUN: True,
            AnimationState.JUMP: False,
            AnimationState.FALL: True,
            AnimationState.CROUCH: True,
            AnimationState.SHOOT: False,
            AnimationState.RELOAD: False,
            AnimationState.HIT: False,
            AnimationState.DEATH: False,
            AnimationState.MELEE: False,
            AnimationState.CLIMB: True,
        }
        
        for state in AnimationState:
            base_color = colors.get(state, (128, 128, 128))
            num_frames = frame_counts.get(state, 4)
            duration = frame_durations.get(state, 0.1)
            loop = loop_states.get(state, True)
            
            frames = []
            for i in range(num_frames):
                # 创建动画帧
                surface = self._create_animated_sprite(
                    state, base_color, i, num_frames
                )
                frames.append(AnimationFrame(
                    surface=surface,
                    duration=duration
                ))
            
            self.clips[state] = AnimationClip(
                name=state.value,
                frames=frames,
                loop=loop
            )
    
    def _create_animated_sprite(
        self, 
        state: AnimationState, 
        base_color: Tuple[int, int, int],
        frame_index: int,
        total_frames: int
    ) -> pygame.Surface:
        """创建动画精灵帧
        
        Args:
            state: 动画状态
            base_color: 基础颜色
            frame_index: 帧索引
            total_frames: 总帧数
        """
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 计算动画相位（用于呼吸/运动效果）
        phase = (frame_index / total_frames) * math.pi * 2
        
        # 根据状态创建不同的视觉效果
        if state in [AnimationState.IDLE, AnimationState.CROUCH]:
            # 呼吸效果
            scale_y = 1.0 + math.sin(phase) * 0.02
            offset_y = math.sin(phase) * 2
            self._draw_soldier_body(surface, base_color, 0, offset_y, 1.0, scale_y, state)
            
        elif state in [AnimationState.WALK, AnimationState.RUN]:
            # 行走摆动效果
            leg_angle = math.sin(phase) * 25 if state == AnimationState.WALK else math.sin(phase) * 40
            arm_angle = -math.sin(phase) * 20 if state == AnimationState.WALK else -math.sin(phase) * 35
            bob_y = abs(math.sin(phase)) * 3
            self._draw_soldier_walking(surface, base_color, leg_angle, arm_angle, bob_y, state)
            
        elif state == AnimationState.JUMP:
            # 跳跃姿态
            progress = frame_index / max(1, total_frames - 1)
            if progress < 0.3:
                # 起跳蓄力
                squat = progress / 0.3
                self._draw_soldier_jumping(surface, base_color, 'crouch', squat)
            elif progress < 0.6:
                # 上升
                self._draw_soldier_jumping(surface, base_color, 'rise', 0)
            else:
                # 下落
                self._draw_soldier_jumping(surface, base_color, 'fall', 0)
                
        elif state == AnimationState.SHOOT:
            # 射击后坐力
            recoil = math.sin(phase * 2) * 5 if frame_index > 0 else 0
            self._draw_soldier_shooting(surface, base_color, recoil)
            
        elif state == AnimationState.RELOAD:
            # 换弹动作
            progress = frame_index / max(1, total_frames - 1)
            self._draw_soldier_reloading(surface, base_color, progress)
            
        elif state == AnimationState.HIT:
            # 受击闪烁
            flash = 1.0 if frame_index % 2 == 0 else 0.5
            self._draw_soldier_hit(surface, base_color, flash)
            
        elif state == AnimationState.DEATH:
            # 死亡倒地
            progress = frame_index / max(1, total_frames - 1)
            self._draw_soldier_death(surface, base_color, progress)
            
        else:
            # 默认姿态
            self._draw_soldier_body(surface, base_color, 0, 0, 1.0, 1.0, state)
        
        return surface
    
    def _draw_soldier_body(
        self, 
        surface: pygame.Surface, 
        color: Tuple[int, int, int],
        offset_x: float, 
        offset_y: float,
        scale_x: float,
        scale_y: float,
        state: AnimationState
    ):
        """绘制士兵基本身体"""
        w, h = self.width, self.height
        cx = w // 2 + int(offset_x)
        
        # 头部
        head_radius = int(8 * scale_x)
        head_y = int(12 + offset_y)
        pygame.draw.circle(surface, color, (cx, head_y), head_radius)
        
        # 头盔
        helmet_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.arc(surface, helmet_color, 
                       (cx - head_radius, head_y - head_radius, 
                        head_radius * 2, head_radius * 2),
                       math.pi, 0, 3)
        
        # 身体
        body_top = head_y + head_radius
        body_height = int(25 * scale_y)
        body_width = int(20 * scale_x)
        body_rect = pygame.Rect(cx - body_width//2, body_top, body_width, body_height)
        pygame.draw.rect(surface, color, body_rect, border_radius=4)
        
        # 战术背心
        vest_color = tuple(max(0, c - 20) for c in color)
        vest_rect = body_rect.inflate(-4, -6)
        pygame.draw.rect(surface, vest_color, vest_rect, border_radius=2)
        
        # 腿部
        leg_top = body_top + body_height
        leg_height = int(20 * scale_y)
        leg_width = 7
        
        if state != AnimationState.CROUCH:
            # 左腿
            pygame.draw.rect(surface, color, 
                           (cx - leg_width - 2, leg_top, leg_width, leg_height),
                           border_radius=2)
            # 右腿
            pygame.draw.rect(surface, color,
                           (cx + 2, leg_top, leg_width, leg_height),
                           border_radius=2)
        else:
            # 蹲伏姿态
            pygame.draw.ellipse(surface, color,
                              (cx - 12, leg_top - 5, 24, 15))
        
        # 手臂
        arm_width = 5
        arm_length = int(15 * scale_y)
        arm_y = body_top + 3
        
        # 左臂
        pygame.draw.rect(surface, color,
                        (cx - body_width//2 - arm_width, arm_y, arm_width, arm_length),
                        border_radius=2)
        # 右臂（持枪）
        pygame.draw.rect(surface, color,
                        (cx + body_width//2, arm_y, arm_width, arm_length),
                        border_radius=2)
    
    def _draw_soldier_walking(
        self, 
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        leg_angle: float,
        arm_angle: float,
        bob_y: float,
        state: AnimationState
    ):
        """绘制行走的士兵"""
        w, h = self.width, self.height
        cx = w // 2
        
        # 身体上下摆动
        offset_y = int(bob_y)
        
        # 头部
        head_radius = 8
        head_y = 12 + offset_y
        pygame.draw.circle(surface, color, (cx, head_y), head_radius)
        
        # 头盔
        helmet_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.arc(surface, helmet_color,
                       (cx - head_radius, head_y - head_radius,
                        head_radius * 2, head_radius * 2),
                       math.pi, 0, 3)
        
        # 身体
        body_top = head_y + head_radius
        body_height = 25
        body_width = 20
        body_rect = pygame.Rect(cx - body_width//2, body_top, body_width, body_height)
        pygame.draw.rect(surface, color, body_rect, border_radius=4)
        
        # 腿部（带摆动）
        leg_length = 18
        leg_width = 7
        leg_top = body_top + body_height
        
        # 左腿
        left_leg_x = cx - 6 + int(math.sin(math.radians(leg_angle)) * 8)
        left_leg_points = self._calculate_limb_points(
            cx - 4, leg_top, leg_length, leg_width, leg_angle
        )
        pygame.draw.polygon(surface, color, left_leg_points)
        
        # 右腿
        right_leg_x = cx + 6 + int(math.sin(math.radians(-leg_angle)) * 8)
        right_leg_points = self._calculate_limb_points(
            cx + 4, leg_top, leg_length, leg_width, -leg_angle
        )
        pygame.draw.polygon(surface, color, right_leg_points)
        
        # 手臂（摆动）
        arm_length = 14
        arm_width = 5
        arm_y = body_top + 5
        
        # 左臂
        left_arm_points = self._calculate_limb_points(
            cx - body_width//2, arm_y, arm_length, arm_width, arm_angle
        )
        pygame.draw.polygon(surface, color, left_arm_points)
        
        # 右臂（持枪，摆动较小）
        right_arm_points = self._calculate_limb_points(
            cx + body_width//2, arm_y, arm_length, arm_width, -arm_angle * 0.5
        )
        pygame.draw.polygon(surface, color, right_arm_points)
        
        # 武器
        weapon_color = (80, 80, 90)
        weapon_x = cx + body_width//2 + 3
        weapon_y = arm_y + 5
        pygame.draw.rect(surface, weapon_color, (weapon_x, weapon_y, 15, 4))
    
    def _draw_soldier_jumping(
        self,
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        phase: str,
        progress: float
    ):
        """绘制跳跃的士兵"""
        w, h = self.width, self.height
        cx = w // 2
        
        if phase == 'crouch':
            # 蓄力蹲姿
            squat_offset = int(progress * 10)
            self._draw_soldier_body(surface, color, 0, squat_offset, 1.0, 0.85, AnimationState.CROUCH)
        elif phase == 'rise':
            # 上升姿态 - 手脚展开
            head_y = 10
            pygame.draw.circle(surface, color, (cx, head_y), 8)
            
            # 身体
            body_top = head_y + 8
            body_rect = pygame.Rect(cx - 10, body_top, 20, 22)
            pygame.draw.rect(surface, color, body_rect, border_radius=4)
            
            # 腿分开向下
            leg_top = body_top + 22
            pygame.draw.polygon(surface, color, [
                (cx - 5, leg_top),
                (cx - 12, leg_top + 18),
                (cx - 5, leg_top + 18)
            ])
            pygame.draw.polygon(surface, color, [
                (cx + 5, leg_top),
                (cx + 12, leg_top + 18),
                (cx + 5, leg_top + 18)
            ])
            
            # 手臂向上
            arm_y = body_top + 3
            pygame.draw.polygon(surface, color, [
                (cx - 10, arm_y),
                (cx - 18, arm_y - 10),
                (cx - 15, arm_y - 10),
                (cx - 7, arm_y)
            ])
            pygame.draw.polygon(surface, color, [
                (cx + 10, arm_y),
                (cx + 18, arm_y - 10),
                (cx + 15, arm_y - 10),
                (cx + 7, arm_y)
            ])
        else:
            # 下落姿态
            head_y = 12
            pygame.draw.circle(surface, color, (cx, head_y), 8)
            
            body_top = head_y + 8
            body_rect = pygame.Rect(cx - 10, body_top, 20, 25)
            pygame.draw.rect(surface, color, body_rect, border_radius=4)
            
            # 腿向前
            leg_top = body_top + 25
            pygame.draw.rect(surface, color, (cx - 10, leg_top, 20, 15), border_radius=2)
            
            # 手向上
            arm_y = body_top + 5
            pygame.draw.rect(surface, color, (cx - 15, arm_y - 8, 5, 15), border_radius=2)
            pygame.draw.rect(surface, color, (cx + 10, arm_y - 8, 5, 15), border_radius=2)
    
    def _draw_soldier_shooting(
        self,
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        recoil: float
    ):
        """绘制射击的士兵"""
        self._draw_soldier_body(surface, color, -recoil, 0, 1.0, 1.0, AnimationState.SHOOT)
        
        # 武器闪光
        w, h = self.width, self.height
        cx = w // 2
        if abs(recoil) > 2:
            flash_color = (255, 255, 200)
            pygame.draw.circle(surface, flash_color, (cx + 25, 25), 6)
    
    def _draw_soldier_reloading(
        self,
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        progress: float
    ):
        """绘制换弹的士兵"""
        w, h = self.width, self.height
        cx = w // 2
        
        # 基本身体
        self._draw_soldier_body(surface, color, 0, 0, 1.0, 1.0, AnimationState.RELOAD)
        
        # 弹匣动画
        mag_color = (60, 60, 70)
        if progress < 0.3:
            # 取出旧弹匣
            mag_y = 28 + int(progress / 0.3 * 20)
            pygame.draw.rect(surface, mag_color, (cx + 5, mag_y, 8, 12), border_radius=1)
        elif progress < 0.7:
            # 准备新弹匣（在手中）
            mag_y = 50 - int((progress - 0.3) / 0.4 * 22)
            pygame.draw.rect(surface, mag_color, (cx - 15, mag_y, 8, 12), border_radius=1)
        else:
            # 插入新弹匣
            mag_y = 28
            pygame.draw.rect(surface, mag_color, (cx + 5, mag_y, 8, 12), border_radius=1)
    
    def _draw_soldier_hit(
        self,
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        flash: float
    ):
        """绘制受击的士兵"""
        # 闪烁颜色
        hit_color = tuple(min(255, int(c * flash + 100 * (1 - flash))) for c in color)
        self._draw_soldier_body(surface, hit_color, 3, 0, 1.0, 1.0, AnimationState.HIT)
    
    def _draw_soldier_death(
        self,
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        progress: float
    ):
        """绘制死亡的士兵"""
        w, h = self.width, self.height
        cx = w // 2
        
        # 倒地旋转
        angle = progress * 90  # 倒向地面
        
        # 简化版：逐渐躺平
        if progress < 0.5:
            # 后仰
            self._draw_soldier_body(surface, color, progress * 10, progress * 5, 
                                   1.0, 1.0 - progress * 0.3, AnimationState.DEATH)
        else:
            # 躺平
            gray_color = tuple(int(c * 0.6) for c in color)
            # 身体横躺
            body_y = int(h * 0.7)
            pygame.draw.ellipse(surface, gray_color, (5, body_y - 8, w - 10, 16))
            # 头
            head_x = 10
            pygame.draw.circle(surface, gray_color, (head_x, body_y), 8)
    
    def _calculate_limb_points(
        self,
        x: float,
        y: float,
        length: float,
        width: float,
        angle: float
    ) -> List[Tuple[int, int]]:
        """计算肢体多边形顶点"""
        angle_rad = math.radians(angle)
        
        # 计算端点
        end_x = x + math.sin(angle_rad) * length
        end_y = y + math.cos(angle_rad) * length
        
        # 计算宽度方向的偏移
        perp_x = math.cos(angle_rad) * width / 2
        perp_y = -math.sin(angle_rad) * width / 2
        
        return [
            (int(x - perp_x), int(y - perp_y)),
            (int(x + perp_x), int(y + perp_y)),
            (int(end_x + perp_x * 0.8), int(end_y + perp_y * 0.8)),
            (int(end_x - perp_x * 0.8), int(end_y - perp_y * 0.8))
        ]
    
    def set_state(self, new_state: AnimationState, force: bool = False):
        """设置动画状态
        
        Args:
            new_state: 新状态
            force: 是否强制切换（忽略过渡）
        """
        if new_state == self.current_state and not force:
            return
        
        if force:
            self.current_state = new_state
            self.current_time = 0.0
            self.transitioning = False
        else:
            self.transition_from = self.current_state
            self.current_state = new_state
            self.transitioning = True
            self.transition_progress = 0.0
            self.current_time = 0.0
    
    def update(self, delta_time: float):
        """更新动画
        
        Args:
            delta_time: 时间增量（秒）
        """
        self.current_time += delta_time
        
        # 更新过渡
        if self.transitioning:
            self.transition_progress += delta_time / self.transition_duration
            if self.transition_progress >= 1.0:
                self.transitioning = False
                self.transition_progress = 1.0
        
        # 检查非循环动画是否完成
        clip = self.clips.get(self.current_state)
        if clip and not clip.loop:
            if self.current_time >= clip.total_duration:
                if self.on_animation_complete:
                    self.on_animation_complete(self.current_state)
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """获取当前动画帧"""
        clip = self.clips.get(self.current_state)
        if not clip:
            return None
        
        frame, _ = clip.get_frame_at_time(self.current_time)
        if frame is None:
            return None
        
        # 处理过渡混合
        if self.transitioning and self.transition_from:
            prev_clip = self.clips.get(self.transition_from)
            if prev_clip:
                prev_frame, _ = prev_clip.get_frame_at_time(self.current_time)
                if prev_frame:
                    # Alpha混合
                    blended = self._blend_frames(
                        prev_frame.surface, 
                        frame.surface, 
                        self.transition_progress
                    )
                    return blended
        
        return frame.surface
    
    def _blend_frames(
        self,
        from_surface: pygame.Surface,
        to_surface: pygame.Surface,
        progress: float
    ) -> pygame.Surface:
        """混合两帧动画
        
        Args:
            from_surface: 源帧
            to_surface: 目标帧
            progress: 进度（0-1）
        """
        result = from_surface.copy()
        to_copy = to_surface.copy()
        to_copy.set_alpha(int(255 * progress))
        result.blit(to_copy, (0, 0))
        return result
    
    def load_sprite_sheet(
        self,
        path: Path,
        state: AnimationState,
        frame_count: int,
        frame_width: int,
        frame_height: int,
        frame_duration: float = 0.1,
        loop: bool = True
    ) -> bool:
        """从精灵表加载动画
        
        Args:
            path: 精灵表路径
            state: 动画状态
            frame_count: 帧数
            frame_width: 帧宽度
            frame_height: 帧高度
            frame_duration: 帧持续时间
            loop: 是否循环
            
        Returns:
            是否成功
        """
        try:
            sprite_sheet = pygame.image.load(str(path)).convert_alpha()
            frames = []
            
            for i in range(frame_count):
                # 计算帧在精灵表中的位置
                col = i % (sprite_sheet.get_width() // frame_width)
                row = i // (sprite_sheet.get_width() // frame_width)
                
                rect = pygame.Rect(
                    col * frame_width,
                    row * frame_height,
                    frame_width,
                    frame_height
                )
                
                frame_surface = sprite_sheet.subsurface(rect).copy()
                # 缩放到角色尺寸
                if frame_width != self.width or frame_height != self.height:
                    frame_surface = pygame.transform.scale(
                        frame_surface, (self.width, self.height)
                    )
                
                frames.append(AnimationFrame(
                    surface=frame_surface,
                    duration=frame_duration
                ))
            
            self.clips[state] = AnimationClip(
                name=state.value,
                frames=frames,
                loop=loop
            )
            return True
            
        except Exception as e:
            print(f"[AnimationController] 加载精灵表失败: {e}")
            return False


# 单例获取函数
_animation_controller_cache: Dict[str, AnimationController] = {}

def get_animation_controller(entity_type: str = "player", width: int = 48, height: int = 64) -> AnimationController:
    """获取动画控制器（缓存单例）
    
    Args:
        entity_type: 实体类型（player/enemy/etc）
        width: 宽度
        height: 高度
    """
    key = f"{entity_type}_{width}_{height}"
    if key not in _animation_controller_cache:
        _animation_controller_cache[key] = AnimationController(width, height)
    return _animation_controller_cache[key]
