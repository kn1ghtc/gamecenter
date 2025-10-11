#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化用户界面管理器
采用现代UI设计原则，提供美观、直观的游戏界面
支持中文字体渲染、渐变效果、阴影等现代视觉效果
"""

import pygame
import math
import os
from typing import Optional, Tuple, Dict, Any
from game_entities import AnimalType, GrassState

# 现代UI颜色方案 - 基于Material Design和现代游戏UI趋势
MODERN_COLORS = {
    # 主色调 - 深色主题配色
    'bg_primary': (26, 32, 44),          # 深蓝灰色主背景
    'bg_secondary': (45, 55, 72),        # 次要背景色
    'bg_tertiary': (74, 85, 104),        # 第三层背景色

    # 表面色彩
    'surface': (68, 90, 124),            # 表面色
    'surface_variant': (90, 103, 129),   # 表面变体色
    'surface_light': (160, 174, 192),    # 浅色表面

    # 强调色
    'primary': (99, 179, 237),           # 主强调色（亮蓝）
    'primary_variant': (79, 172, 254),   # 主色变体
    'secondary': (129, 230, 217),        # 次要强调色（青绿）
    'accent': (255, 193, 7),             # 提醒色（琥珀）

    # 语义色彩
    'success': (72, 187, 120),           # 成功（绿）
    'warning': (255, 193, 7),            # 警告（橙）
    'error': (248, 113, 113),            # 错误（红）
    'info': (99, 179, 237),              # 信息（蓝）

    # 文字色彩
    'text_primary': (247, 250, 252),     # 主要文字
    'text_secondary': (160, 174, 192),   # 次要文字
    'text_muted': (113, 128, 150),       # 静音文字
    'text_inverse': (26, 32, 44),        # 反色文字

    # 边框和分隔
    'border': (74, 85, 104),             # 边框色
    'border_light': (113, 128, 150),     # 浅色边框
    'divider': (45, 55, 72),             # 分隔线

    # 状态色彩
    'hover': (160, 174, 192, 30),        # 悬停效果
    'active': (99, 179, 237, 50),        # 激活状态
    'disabled': (113, 128, 150, 100),    # 禁用状态

    # 阴影
    'shadow_light': (0, 0, 0, 20),       # 浅阴影
    'shadow_medium': (0, 0, 0, 40),      # 中等阴影
    'shadow_heavy': (0, 0, 0, 60),       # 深阴影
}

def draw_gradient_rect(surface: pygame.Surface, rect: pygame.Rect,
                      color1: tuple, color2: tuple, vertical: bool = True):
    """绘制渐变矩形"""
    # 验证颜色值
    def validate_color(color):
        if not color or len(color) < 3:
            return (128, 128, 128)  # 默认灰色
        return tuple(max(0, min(255, int(c))) for c in color[:3])

    color1 = validate_color(color1)
    color2 = validate_color(color2)

    if vertical:
        for y in range(rect.height):
            ratio = y / rect.height if rect.height > 0 else 0
            r = max(0, min(255, int(color1[0] * (1 - ratio) + color2[0] * ratio)))
            g = max(0, min(255, int(color1[1] * (1 - ratio) + color2[1] * ratio)))
            b = max(0, min(255, int(color1[2] * (1 - ratio) + color2[2] * ratio)))
            pygame.draw.line(surface, (r, g, b),
                           (rect.x, rect.y + y), (rect.x + rect.width - 1, rect.y + y))
    else:
        for x in range(rect.width):
            ratio = x / rect.width if rect.width > 0 else 0
            r = max(0, min(255, int(color1[0] * (1 - ratio) + color2[0] * ratio)))
            g = max(0, min(255, int(color1[1] * (1 - ratio) + color2[1] * ratio)))
            b = max(0, min(255, int(color1[2] * (1 - ratio) + color2[2] * ratio)))
            pygame.draw.line(surface, (r, g, b),
                           (rect.x + x, rect.y), (rect.x + x, rect.y + rect.height - 1))

def draw_rounded_rect(surface: pygame.Surface, rect: pygame.Rect,
                     color: tuple, radius: int = 8):
    """绘制圆角矩形"""
    if radius > min(rect.width, rect.height) // 2:
        radius = min(rect.width, rect.height) // 2

    # 验证并清理颜色值
    if not color or len(color) < 3:
        color = (100, 100, 100)  # 默认灰色

    # 确保颜色值在有效范围内
    rgb_color = tuple(max(0, min(255, int(c))) for c in color[:3])

    # 验证rect尺寸
    if rect.width <= 0 or rect.height <= 0:
        return

    # 创建临时surface用于圆角绘制
    temp_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(temp_surf, rgb_color, (0, 0, rect.width, rect.height), border_radius=radius)

    # 如果有alpha值，应用到整个surface
    if len(color) > 3:
        temp_surf.set_alpha(color[3])

    surface.blit(temp_surf, rect)

def draw_shadow(surface: pygame.Surface, rect: pygame.Rect,
               shadow_color: tuple = MODERN_COLORS['shadow_medium'],
               offset: Tuple[int, int] = (2, 2), blur: int = 4):
    """绘制阴影效果"""
    shadow_rect = rect.copy()
    shadow_rect.x += offset[0]
    shadow_rect.y += offset[1]

    # 简化的阴影效果
    for i in range(blur):
        alpha = shadow_color[3] // (i + 1) if len(shadow_color) == 4 else 30 // (i + 1)
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        # 修复颜色参数 - 只使用RGB三个分量
        rgb_shadow_color = shadow_color[:3]
        pygame.draw.rect(shadow_surf, rgb_shadow_color, (0, 0, shadow_rect.width, shadow_rect.height), border_radius=8)
        shadow_surf.set_alpha(alpha)
        surface.blit(shadow_surf, (shadow_rect.x + i, shadow_rect.y + i))

def create_font_with_fallback(font_path: Optional[str], size: int) -> pygame.font.Font:
    """创建带中文支持的字体，包含回退机制"""
    fonts_to_try = []

    # 首先尝试用户指定的字体
    if font_path:
        fonts_to_try.append(font_path)

    # macOS 中文字体
    macos_fonts = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Helvetica.ttc"
    ]

    # Windows 中文字体
    windows_fonts = [
        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/arial.ttf"    # Arial
    ]

    # Linux 中文字体
    linux_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    ]

    fonts_to_try.extend(macos_fonts + windows_fonts + linux_fonts)

    for font_path in fonts_to_try:
        try:
            if os.path.exists(font_path):
                font = pygame.font.Font(font_path, size)
                # 测试中文渲染
                test_surface = font.render("测试", True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    return font
        except Exception:
            continue

    # 如果所有字体都失败，使用系统默认字体
    return pygame.font.Font(None, size)

class ModernButton:
    """现代化按钮组件"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 font: pygame.font.Font, style: str = "primary"):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.style = style

        # 状态
        self.is_hovered = False
        self.is_pressed = False
        self.is_disabled = False

        # 动画
        self.hover_animation = 0.0
        self.press_animation = 0.0

        # 样式配置
        self.styles = {
            "primary": {
                "bg": MODERN_COLORS['primary'],
                "bg_hover": MODERN_COLORS['primary_variant'],
                "text": MODERN_COLORS['text_inverse'],
                "border": MODERN_COLORS['primary_variant']
            },
            "secondary": {
                "bg": MODERN_COLORS['bg_secondary'],
                "bg_hover": MODERN_COLORS['bg_tertiary'],
                "text": MODERN_COLORS['text_primary'],
                "border": MODERN_COLORS['border_light']
            },
            "success": {
                "bg": MODERN_COLORS['success'],
                "bg_hover": (60, 150, 100),
                "text": MODERN_COLORS['text_inverse'],
                "border": MODERN_COLORS['success']
            },
            "warning": {
                "bg": MODERN_COLORS['warning'],
                "bg_hover": (230, 170, 0),
                "text": MODERN_COLORS['text_inverse'],
                "border": MODERN_COLORS['warning']
            }
        }

    def handle_event(self, event, mouse_pos: Tuple[int, int]) -> bool:
        """处理按钮事件"""
        if self.is_disabled:
            return False

        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed:
                self.is_pressed = False
                if self.is_hovered:
                    return True

        return False

    def update(self, dt: float):
        """更新按钮动画"""
        # 限制dt值以防止动画异常
        dt = max(0.0, min(dt, 0.1))  # 限制dt在0-0.1之间

        # 悬停动画
        target_hover = 1.0 if self.is_hovered else 0.0
        self.hover_animation += (target_hover - self.hover_animation) * 8 * dt
        self.hover_animation = max(0.0, min(self.hover_animation, 1.0))  # 限制在0-1之间

        # 按压动画
        target_press = 1.0 if self.is_pressed else 0.0
        self.press_animation += (target_press - self.press_animation) * 12 * dt
        self.press_animation = max(0.0, min(self.press_animation, 1.0))  # 限制在0-1之间

    def draw(self, screen: pygame.Surface):
        """绘制现代化按钮"""
        if self.is_disabled:
            return

        style = self.styles.get(self.style, self.styles["primary"])

        # 计算动画颜色
        base_color = style["bg"]
        hover_color = style["bg_hover"]

        # 确保颜色值有效
        if not base_color or not hover_color:
            bg_color = (100, 100, 100)  # 默认灰色
        else:
            # 混合颜色并确保值在有效范围内
            r = max(0, min(255, int(base_color[0] + (hover_color[0] - base_color[0]) * self.hover_animation)))
            g = max(0, min(255, int(base_color[1] + (hover_color[1] - base_color[1]) * self.hover_animation)))
            b = max(0, min(255, int(base_color[2] + (hover_color[2] - base_color[2]) * self.hover_animation)))
            bg_color = (r, g, b)

        # 按压偏移
        offset_y = int(2 * self.press_animation)
        button_rect = self.rect.copy()
        button_rect.y += offset_y

        # 绘制阴影
        if not self.is_pressed:
            draw_shadow(screen, button_rect, MODERN_COLORS['shadow_medium'], (0, 4), 6)

        # 绘制按钮背景
        draw_rounded_rect(screen, button_rect, bg_color, 8)

        # 绘制边框
        border_color = style["border"]
        pygame.draw.rect(screen, border_color, button_rect, 2, border_radius=8)

        # 绘制文字
        text_color = style["text"]
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        screen.blit(text_surface, text_rect)

class ModernPanel:
    """现代化面板组件"""

    def __init__(self, x: int, y: int, width: int, height: int, title: str,
                 font: pygame.font.Font, style: str = "default"):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.font = font
        self.style = style

        # 创建更小的字体用于内容显示
        try:
            content_font_size = max(8, self.font.get_height() - 6)  # 进一步减小字体
            self.small_font = create_font_with_fallback(None, content_font_size)
        except:
            self.small_font = create_font_with_fallback(None, 10)

        self.content = []

        # 滚动支持
        self.scroll_y = 0
        self.max_scroll = 0

        # 动画和透明度
        self.opacity = 0.85  # 设置半透明

    def set_content(self, content: list):
        """设置面板内容"""
        self.content = content
        # 计算最大滚动距离 - 使用更小的行高
        line_height = 16  # 从24减少到16
        content_height = len(content) * line_height
        available_height = self.rect.height - 40  # 减少标题区域占用，从60减少到40
        self.max_scroll = max(0, content_height - available_height)

    def handle_scroll(self, event):
        """处理滚动事件"""
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 20))

    def draw(self, screen: pygame.Surface):
        """绘制现代化面板"""
        # 创建半透明的背景surface
        panel_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # 绘制阴影到主屏幕
        draw_shadow(screen, self.rect, MODERN_COLORS['shadow_medium'], (0, 4), 8)

        # 在临时surface上绘制面板
        # 绘制背景渐变 - 使用半透明颜色
        bg_color1 = (*MODERN_COLORS['bg_secondary'][:3], int(255 * self.opacity))
        bg_color2 = (*MODERN_COLORS['bg_primary'][:3], int(255 * self.opacity))
        draw_gradient_rect(panel_surface, pygame.Rect(0, 0, self.rect.width, self.rect.height),
                          bg_color1[:3], bg_color2[:3])  # 渐变不支持alpha

        # 应用整体透明度
        panel_surface.set_alpha(int(255 * self.opacity))

        # 绘制边框到临时surface
        border_color = (*MODERN_COLORS['border'][:3], int(255 * self.opacity))
        pygame.draw.rect(panel_surface, border_color[:3], (0, 0, self.rect.width, self.rect.height), 2, border_radius=12)

        # 绘制标题区域 - 调整大小
        title_rect = pygame.Rect(0, 0, self.rect.width, 35)  # 从50减少到35
        title_bg_color = (*MODERN_COLORS['bg_tertiary'][:3], int(255 * self.opacity))
        draw_rounded_rect(panel_surface, title_rect, title_bg_color[:3], 12)

        # 绘制标题文字
        title_surface = self.font.render(self.title, True, MODERN_COLORS['text_primary'])
        title_text_rect = title_surface.get_rect(center=(title_rect.centerx, title_rect.centery))
        panel_surface.blit(title_surface, title_text_rect)

        # 将面板surface绘制到主屏幕
        screen.blit(panel_surface, self.rect)

        # 绘制内容区域 - 调整位置和大小
        content_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 40,  # 调整边距和起始位置
                                 self.rect.width - 20, self.rect.height - 50)

        # 创建剪切区域
        screen.set_clip(content_rect)

        # 绘制内容
        y_offset = content_rect.y - self.scroll_y
        line_height = 16  # 减小行高以适应更多内容
        for i, line in enumerate(self.content):
            if y_offset > content_rect.bottom:
                break
            if y_offset + line_height >= content_rect.y:
                # 根据内容类型选择颜色
                if str(line).startswith("==="):
                    color = MODERN_COLORS['accent']
                    text = str(line).replace("===", "").strip()
                elif str(line).startswith("•"):
                    color = MODERN_COLORS['text_secondary']
                    text = str(line)
                elif ":" in str(line):
                    color = MODERN_COLORS['text_primary']
                    text = str(line)
                else:
                    color = MODERN_COLORS['text_muted']
                    text = str(line)

                # 如果文本太长，进行截断
                max_width = content_rect.width - 10
                text_surface = self.small_font.render(text, True, color)
                if text_surface.get_width() > max_width:
                    # 简单的文本截断
                    while len(text) > 0 and self.small_font.size(text + "...")[0] > max_width:
                        text = text[:-1]
                    text += "..."
                    text_surface = self.small_font.render(text, True, color)

                screen.blit(text_surface, (content_rect.x, y_offset))

            y_offset += line_height

        # 移除剪切
        screen.set_clip(None)

        # 绘制滚动条
        if self.max_scroll > 0:
            self._draw_scrollbar(screen, content_rect)

    def _draw_scrollbar(self, screen: pygame.Surface, content_rect: pygame.Rect):
        """绘制滚动条"""
        scrollbar_width = 6
        scrollbar_x = self.rect.right - scrollbar_width - 8
        scrollbar_y = content_rect.y
        scrollbar_height = content_rect.height

        # 滚动条背景
        scrollbar_bg = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
        draw_rounded_rect(screen, scrollbar_bg, MODERN_COLORS['bg_tertiary'], 3)

        # 滚动条滑块
        if self.max_scroll > 0:
            thumb_height = max(20, int(scrollbar_height * (scrollbar_height / (scrollbar_height + self.max_scroll))))
            thumb_y = scrollbar_y + int((scrollbar_height - thumb_height) * (self.scroll_y / self.max_scroll))
            thumb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)
            draw_rounded_rect(screen, thumb_rect, MODERN_COLORS['primary'], 3)

class UIManager:
    """用户界面管理器"""

    def __init__(self, font_path: Optional[str] = None, screen_width: int = 1200, screen_height: int = 800):
        """初始化UI管理器"""
        # 屏幕尺寸（用于动态布局）
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 初始化字体 - 使用更小的字体以适应面板
        try:
            if font_path:
                self.main_font = pygame.font.Font(font_path, 16)  # 从24减少到16
                self.small_font = pygame.font.Font(font_path, 12)  # 从18减少到12
                self.large_font = pygame.font.Font(font_path, 20)  # 从32减少到20
                self.tiny_font = pygame.font.Font(font_path, 10)   # 新增更小字体
            else:
                self.main_font = pygame.font.Font(None, 16)
                self.small_font = pygame.font.Font(None, 12)
                self.large_font = pygame.font.Font(None, 20)
                self.tiny_font = pygame.font.Font(None, 10)
        except:
            # 备用字体
            self.main_font = pygame.font.Font(None, 16)
            self.small_font = pygame.font.Font(None, 12)
            self.large_font = pygame.font.Font(None, 20)
            self.tiny_font = pygame.font.Font(None, 10)

        # 游戏状态
        self.selected_animal_type = AnimalType.SHEEP
        self.paused = False
        self.game_over = False
        self.time_acceleration = 1.0

        # UI颜色
        self.colors = {
            'background': (0, 0, 0, 150),
            'panel': (40, 40, 40, 200),
            'accent': (100, 200, 255),
            'success': (100, 255, 100),
            'warning': (255, 200, 100),
            'danger': (255, 100, 100),
            'text': (255, 255, 255),
            'text_dark': (200, 200, 200)
        }

        # 创建UI元素
        self._create_ui_elements()

        # 统计数据
        self.stats = {}
        self.camera_info = {}
        self.current_time = 0

    def _create_ui_elements(self):
        """创建UI元素"""
        # 左侧控制面板 - 使用小字体标题
        self.control_panel = ModernPanel(10, 10, 200, 350, "控制面板", self.small_font)

        # 右侧统计面板 - 使用小字体标题（动态位置）
        stats_x = self.screen_width - 200
        self.stats_panel = ModernPanel(stats_x, 10, 190, 400, "生态统计", self.small_font)

        # 动物选择按钮
        self.animal_buttons = {}
        button_width = 60
        button_height = 40
        start_x = 20
        start_y = 50

        animal_types = [
            (AnimalType.SHEEP, "羊 🐑"),
            (AnimalType.RABBIT, "兔 🐰"),
            (AnimalType.COW, "牛 🐄")
        ]

        for i, (animal_type, text) in enumerate(animal_types):
            y_pos = start_y + i * (button_height + 10)
            button = ModernButton(start_x, y_pos, button_width * 2, button_height,
                          text, self.small_font, "primary")
            self.animal_buttons[animal_type] = button

        # 控制按钮
        self.pause_button = ModernButton(20, 200, 60, 30, "暂停", self.small_font, "warning")
        self.reset_button = ModernButton(90, 200, 60, 30, "重置", self.small_font, "secondary")
        self.help_button = ModernButton(160, 200, 40, 30, "帮助", self.small_font, "info")

        # 帮助对话框
        self.show_help_dialog = False
        self.help_dialog = None

        # 时间控制按钮
        self.speed_buttons = {}
        speeds = [0.5, 1.0, 2.0, 4.0]
        for i, speed in enumerate(speeds):
            x_pos = 20 + i * 40
            text = f"{speed}x" if speed != 1.0 else "1x"
            button = ModernButton(x_pos, 240, 35, 25, text, self.small_font, "secondary")
            self.speed_buttons[speed] = button
    
    def update_layout(self, width: int, height: int):
        """更新UI布局以适应新的屏幕尺寸"""
        self.screen_width = width
        self.screen_height = height
        
        # 更新右侧统计面板位置（右对齐）
        stats_x = self.screen_width - 200
        self.stats_panel.rect.x = stats_x
        
        # 如果有帮助对话框，也需要更新其位置（居中）
        if self.help_dialog:
            dialog_width = self.help_dialog.rect.width
            dialog_height = self.help_dialog.rect.height
            self.help_dialog.rect.x = (self.screen_width - dialog_width) // 2
            self.help_dialog.rect.y = (self.screen_height - dialog_height) // 2

    def update(self, dt: float):
        """更新UI动画"""
        # 验证dt值，防止异常的帧时间
        dt = max(0.001, min(dt, 0.1))  # 限制在1ms到100ms之间

        # 更新所有按钮动画
        for button in self.animal_buttons.values():
            button.update(dt)

        self.pause_button.update(dt)
        self.reset_button.update(dt)
        self.help_button.update(dt)

        for button in self.speed_buttons.values():
            button.update(dt)

    def handle_event(self, event) -> bool:
        """处理UI事件"""
        mouse_pos = pygame.mouse.get_pos()

        # 检查是否点击在UI区域
        ui_areas = [
            self.control_panel.rect,
            self.stats_panel.rect
        ]

        clicked_ui = any(area.collidepoint(mouse_pos) for area in ui_areas)

        # 处理面板滚动
        self.control_panel.handle_scroll(event)
        self.stats_panel.handle_scroll(event)

        # 处理动物选择按钮
        for animal_type, button in self.animal_buttons.items():
            if button.handle_event(event, mouse_pos):
                print(f"🐾 选择动物类型：{animal_type.name}")
                self.selected_animal_type = animal_type
                return True

        # 处理控制按钮
        if self.pause_button.handle_event(event, mouse_pos):
            self.paused = not self.paused
            self.pause_button.text = "继续" if self.paused else "暂停"
            return True

        if self.reset_button.handle_event(event, mouse_pos):
            # 重置游戏的信号
            return True

        if self.help_button.handle_event(event, mouse_pos):
            self.show_help_dialog = True
            return True

        # 处理帮助对话框
        if self.show_help_dialog and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_h:
                self.show_help_dialog = False
                return True

        # 处理时间控制按钮
        for speed, button in self.speed_buttons.items():
            if button.handle_event(event, mouse_pos):
                self.time_acceleration = speed
                return True

        return clicked_ui

    def update_stats(self, ecosystem_stats: Dict[str, Any], camera_info: Dict[str, Any], current_time: int):
        """更新统计信息"""
        self.stats = ecosystem_stats
        self.camera_info = camera_info
        self.current_time = current_time

    def update_controls(self):
        """更新控制面板内容"""
        selected_name = {
            AnimalType.SHEEP: "羊",
            AnimalType.RABBIT: "兔子",
            AnimalType.COW: "牛"
        }.get(self.selected_animal_type, "未知")

        time_str = f"{self.current_time // 60000:02d}:{(self.current_time // 1000) % 60:02d}"

        # 检查生态系统状态
        status_text = "运行"
        if self.game_over:
            status_text = "已结束"
        elif self.paused:
            status_text = "暂停"
        elif hasattr(self, 'stats') and self.stats:
            # 检查是否濒危
            from ecosystem import EcoSystem
            if hasattr(EcoSystem, 'is_ecosystem_endangered'):
                # 模拟检查濒危状态（简化版）
                total_animals = self.stats.get('total_animals', 0)
                dead_grass_percentage = self.stats.get('dead_grass_percentage', 0)
                if total_animals == 0:
                    status_text = "⚠️ 无动物"
                elif dead_grass_percentage > 80:
                    status_text = "⚠️ 濒危"

        control_content = [
            f"当前选择: {selected_name}",
            f"状态: {status_text}",
            f"游戏时间: {time_str}",
            "",  # 空行分隔
            f"时间倍速: {self.time_acceleration}x",
        ]

        self.control_panel.set_content(control_content)

    def _update_stats_panel(self):
        """更新统计面板内容"""
        if not self.stats:
            return

        # 计算生态健康度
        total_animals = self.stats.get('total_animals', 0)
        carrying_capacity = self.stats.get('carrying_capacity', 1)
        ecosystem_pressure = self.stats.get('ecosystem_pressure', 0)
        dead_grass_percentage = self.stats.get('dead_grass_percentage', 0)

        # 生态健康评级
        if ecosystem_pressure < 0.3:
            health_status = "优秀"
            health_color = "🟢"
        elif ecosystem_pressure < 0.6:
            health_status = "良好"
            health_color = "🟡"
        elif ecosystem_pressure < 0.8:
            health_status = "警告"
            health_color = "🟠"
        else:
            health_status = "危险"
            health_color = "🔴"

        stats_content = [
            "=== 动物统计 ===",
            f"总数量: {total_animals}",
            f"羊: {self.stats.get('sheep_count', 0)}",
            f"兔子: {self.stats.get('rabbit_count', 0)}",
            f"牛: {self.stats.get('cow_count', 0)}",
            "",
            "=== 环境状态 ===",
            f"承载力: {carrying_capacity}",
            f"生态压力: {ecosystem_pressure:.2f}",
            f"枯萎草地: {dead_grass_percentage:.1f}%",
            f"健康度: {health_color} {health_status}",
            "",
            "=== 摄像机 ===",
            f"位置: ({self.camera_info.get('x', 0)}, {self.camera_info.get('y', 0)})",
            f"缩放: {self.camera_info.get('zoom', 1.0):.2f}x",
            f"视野: {self.camera_info.get('visible_width', 0)}x{self.camera_info.get('visible_height', 0)}"
        ]

        self.stats_panel.set_content(stats_content)

    def draw(self, screen: pygame.Surface, mouse_pos: Tuple[int, int]):
        """绘制UI界面"""
        # 更新统计面板
        self._update_stats_panel()

        # 绘制面板
        self.control_panel.draw(screen)
        self.stats_panel.draw(screen)

        # 绘制按钮
        for button in self.animal_buttons.values():
            button.draw(screen)

        # 高亮当前选中的动物按钮
        if self.selected_animal_type in self.animal_buttons:
            selected_button = self.animal_buttons[self.selected_animal_type]
            pygame.draw.rect(screen, (255, 255, 0), selected_button.rect, 3)

        self.pause_button.draw(screen)
        self.reset_button.draw(screen)
        self.help_button.draw(screen)

        # 绘制时间控制按钮
        for speed, button in self.speed_buttons.items():
            button.draw(screen)
            # 高亮当前时间倍速
            if abs(speed - self.time_acceleration) < 0.01:
                pygame.draw.rect(screen, (0, 255, 0), button.rect, 2)

        # 绘制顶部标题
        title_text = "小羊吃草 - 生态模拟游戏"
        title_surface = self.large_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 30))

        # 标题背景
        bg_rect = title_rect.inflate(20, 10)
        pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect)
        pygame.draw.rect(screen, (100, 200, 255), bg_rect, 2)

        screen.blit(title_surface, title_rect)

        # 绘制生态健康指示器
        if self.stats:
            self._draw_health_indicator(screen)

        # 绘制鼠标提示
        self._draw_mouse_tooltip(screen, mouse_pos)

        # 绘制帮助对话框
        if self.show_help_dialog:
            self._draw_help_dialog(screen)

    def _draw_health_indicator(self, screen: pygame.Surface):
        """绘制生态健康指示器"""
        pressure = self.stats.get('ecosystem_pressure', 0)

        # 健康条位置
        bar_x = screen.get_width() // 2 - 100
        bar_y = 70
        bar_width = 200
        bar_height = 20

        # 背景
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))

        # 健康条
        health_width = int(bar_width * (1 - pressure))
        if pressure < 0.3:
            color = (0, 255, 0)  # 绿色
        elif pressure < 0.6:
            color = (255, 255, 0)  # 黄色
        elif pressure < 0.8:
            color = (255, 165, 0)  # 橙色
        else:
            color = (255, 0, 0)  # 红色

        pygame.draw.rect(screen, color, (bar_x, bar_y, health_width, bar_height))

        # 边框
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

        # 文字
        health_text = f"生态健康: {(1-pressure)*100:.0f}%"
        text_surface = self.small_font.render(health_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height + 15))
        screen.blit(text_surface, text_rect)

    def _draw_mouse_tooltip(self, screen: pygame.Surface, mouse_pos: Tuple[int, int]):
        """绘制鼠标提示"""
        # 检查鼠标是否在UI区域
        if (mouse_pos[0] < 220 or mouse_pos[0] > screen.get_width() - 200 or
            mouse_pos[1] < 100):
            return

        # 显示当前选择的动物信息
        animal_names = {
            AnimalType.SHEEP: "羊 🐑",
            AnimalType.RABBIT: "兔子 🐰",
            AnimalType.COW: "牛 🐄"
        }

        tooltip_text = f"左键添加: {animal_names.get(self.selected_animal_type, '未知')}"
        text_surface = self.small_font.render(tooltip_text, True, (255, 255, 255))

        # 计算提示框位置
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] - 25

        # 防止超出屏幕
        if tooltip_x + text_surface.get_width() > screen.get_width():
            tooltip_x = mouse_pos[0] - text_surface.get_width() - 15
        if tooltip_y < 0:
            tooltip_y = mouse_pos[1] + 15

        # 绘制背景
        bg_rect = text_surface.get_rect()
        bg_rect.x = tooltip_x - 5
        bg_rect.y = tooltip_y - 2
        bg_rect.width += 10
        bg_rect.height += 4

        pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect)
        pygame.draw.rect(screen, (100, 200, 255), bg_rect, 1)

        # 绘制文字
        screen.blit(text_surface, (tooltip_x, tooltip_y))

    def _draw_help_dialog(self, screen: pygame.Surface):
        """绘制帮助对话框"""
        # 对话框尺寸和位置
        dialog_width = 600
        dialog_height = 450
        dialog_x = (screen.get_width() - dialog_width) // 2
        dialog_y = (screen.get_height() - dialog_height) // 2

        # 半透明背景遮罩
        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # 对话框背景
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(screen, (40, 50, 60), dialog_rect)
        pygame.draw.rect(screen, (100, 200, 255), dialog_rect, 3)

        # 标题
        title_text = "🐑 小羊吃草 - 游戏帮助"
        title_surface = self.large_font.render(title_text, True, (255, 255, 255))
        title_x = dialog_x + (dialog_width - title_surface.get_width()) // 2
        screen.blit(title_surface, (title_x, dialog_y + 20))

        # 帮助内容
        help_content = [
            "🎮 控制方式：",
            "  WASD / 方向键  - 移动摄像机",
            "  鼠标滚轮      - 缩放视角",
            "  左键          - 添加选中的动物",
            "  右键          - 查看动物/地块信息",
            "  中键拖拽      - 拖拽移动视角",
            "",
            "⌨️  快捷键：",
            "  空格键        - 暂停/继续游戏",
            "  1/2/3        - 快速选择动物类型",
            "  R            - 重新开始游戏",
            "  H            - 显示此帮助",
            "  F3           - 切换调试模式",
            "  ESC          - 退出游戏",
            "",
            "🦌 动物特性：",
            "  羊 🐑         - 温和食草，群居动物",
            "  兔子 🐰       - 繁殖快，食量小",
            "  牛 🐄         - 食量大，移动慢",
            "",
            "按 ESC 或 H 键关闭帮助"
        ]

        # 绘制帮助内容
        y_offset = dialog_y + 70
        for line in help_content:
            if line.strip():  # 非空行
                text_surface = self.small_font.render(line, True, (255, 255, 255))
                screen.blit(text_surface, (dialog_x + 30, y_offset))
            y_offset += 18

    def show_notification(self, message: str, duration: int = 3000):
        """显示通知消息"""
        # 这里可以实现通知系统
        print(f"📢 {message}")
