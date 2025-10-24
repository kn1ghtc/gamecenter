"""
关卡帮助覆盖层 - 按H键显示/隐藏
显示当前关卡的详细提示、目标、敌人信息
"""

import pygame
import json
from pathlib import Path
from typing import Optional, Dict


class HelpOverlay:
    """帮助覆盖层 - 显示关卡提示和控制说明"""
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        初始化帮助覆盖层
        
        Args:
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 加载帮助数据
        self.help_data = self._load_help_data()
        
        # 覆盖层状态
        self.visible = False
        self.current_level = 1
        
        # 样式配置
        self.overlay_alpha = 220  # 半透明度
        self.padding = 40
        self.line_spacing = 8
        
        # 颜色方案
        self.colors = {
            "background": (20, 20, 30),
            "title": (255, 200, 50),
            "heading": (100, 200, 255),
            "text": (220, 220, 220),
            "tip": (150, 255, 150),
            "border": (100, 150, 200),
            "shadow": (0, 0, 0, 150)
        }
        
        # 字体（使用pygame默认字体）
        self.fonts = {
            "title": pygame.font.Font(None, 48),
            "heading": pygame.font.Font(None, 32),
            "body": pygame.font.Font(None, 24),
            "small": pygame.font.Font(None, 20)
        }
        
    def _load_help_data(self) -> Dict:
        """加载关卡帮助数据"""
        data_file = Path(__file__).parent.parent / "data" / "level_help.json"
        
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[HelpOverlay] 加载帮助数据失败: {e}")
        
        # 默认数据
        return {
            "1": {
                "title": "Tutorial Mission",
                "objective": "Learn basic controls and complete objectives",
                "tips": [
                    "WASD - Movement",
                    "Space - Shoot",
                    "R - Reload",
                    "Q - Switch Weapon"
                ],
                "enemies": "2 enemies",
                "difficulty": "Easy"
            }
        }
    
    def toggle(self):
        """切换显示/隐藏"""
        self.visible = not self.visible
    
    def show(self):
        """显示帮助"""
        self.visible = True
    
    def hide(self):
        """隐藏帮助"""
        self.visible = False
    
    def set_level(self, level_id: int):
        """设置当前关卡"""
        self.current_level = level_id
    
    def render(self, screen: pygame.Surface):
        """
        渲染帮助覆盖层
        
        Args:
            screen: 渲染目标
        """
        if not self.visible:
            return
        
        # 获取当前关卡数据
        level_key = str(self.current_level)
        if level_key not in self.help_data:
            level_key = "1"  # 默认使用第一关数据
        
        help_info = self.help_data[level_key]
        
        # 创建半透明背景
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(self.overlay_alpha)
        overlay.fill(self.colors["background"])
        screen.blit(overlay, (0, 0))
        
        # 计算内容区域
        content_width = self.screen_width - self.padding * 2
        content_height = self.screen_height - self.padding * 2
        content_x = self.padding
        content_y = self.padding
        
        # 绘制边框
        border_rect = pygame.Rect(
            content_x - 10,
            content_y - 10,
            content_width + 20,
            content_height + 20
        )
        pygame.draw.rect(screen, self.colors["border"], border_rect, 3, border_radius=10)
        
        # 渲染内容
        y_offset = content_y
        
        # 标题
        title_text = self.fonts["title"].render(
            help_info.get("title", "Mission Help"),
            True, self.colors["title"]
        )
        title_x = content_x + (content_width - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, y_offset))
        y_offset += title_text.get_height() + 20
        
        # 分隔线
        pygame.draw.line(
            screen,
            self.colors["border"],
            (content_x, y_offset),
            (content_x + content_width, y_offset),
            2
        )
        y_offset += 20
        
        # 目标
        objective_heading = self.fonts["heading"].render(
            "OBJECTIVE", True, self.colors["heading"]
        )
        screen.blit(objective_heading, (content_x, y_offset))
        y_offset += objective_heading.get_height() + 10
        
        objective_text = self.fonts["body"].render(
            help_info.get("objective", "Complete the mission"),
            True, self.colors["text"]
        )
        screen.blit(objective_text, (content_x + 20, y_offset))
        y_offset += objective_text.get_height() + 25
        
        # 提示列表
        tips_heading = self.fonts["heading"].render(
            "TIPS", True, self.colors["heading"]
        )
        screen.blit(tips_heading, (content_x, y_offset))
        y_offset += tips_heading.get_height() + 10
        
        tips = help_info.get("tips", [])
        for tip in tips:
            # 子弹点
            pygame.draw.circle(
                screen,
                self.colors["tip"],
                (content_x + 30, y_offset + 10),
                4
            )
            
            tip_text = self.fonts["body"].render(tip, True, self.colors["text"])
            screen.blit(tip_text, (content_x + 50, y_offset))
            y_offset += tip_text.get_height() + self.line_spacing
        
        y_offset += 15
        
        # 敌人信息和难度（双列）
        info_y = y_offset
        
        # 敌人信息（左列）
        enemies_heading = self.fonts["heading"].render(
            "ENEMIES", True, self.colors["heading"]
        )
        screen.blit(enemies_heading, (content_x, info_y))
        info_y += enemies_heading.get_height() + 8
        
        enemies_text = self.fonts["body"].render(
            help_info.get("enemies", "Unknown"),
            True, self.colors["text"]
        )
        screen.blit(enemies_text, (content_x + 20, info_y))
        
        # 难度（右列）
        difficulty_x = content_x + content_width // 2
        info_y = y_offset
        
        difficulty_heading = self.fonts["heading"].render(
            "DIFFICULTY", True, self.colors["heading"]
        )
        screen.blit(difficulty_heading, (difficulty_x, info_y))
        info_y += difficulty_heading.get_height() + 8
        
        difficulty = help_info.get("difficulty", "Medium")
        difficulty_color = {
            "Easy": (100, 255, 100),
            "简单": (100, 255, 100),
            "Medium": (255, 200, 100),
            "中等": (255, 200, 100),
            "Hard": (255, 100, 100),
            "困难": (255, 100, 100)
        }.get(difficulty, self.colors["text"])
        
        difficulty_text = self.fonts["body"].render(
            difficulty, True, difficulty_color
        )
        screen.blit(difficulty_text, (difficulty_x + 20, info_y))
        
        # 底部提示
        bottom_y = content_y + content_height - 40
        hint_text = self.fonts["small"].render(
            "Press H to close | ESC to exit mission",
            True, self.colors["text"]
        )
        hint_x = content_x + (content_width - hint_text.get_width()) // 2
        screen.blit(hint_text, (hint_x, bottom_y))
