"""菜单系统 - 主菜单和任务选择"""
import pygame
from typing import Optional, Callable
from gamecenter.deltaOperation import config


class Button:
    """按钮组件"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback: Optional[Callable] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.clicked = False
        
    def handle_event(self, event: pygame.event.Event):
        """处理事件"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.clicked = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.clicked and self.hovered and event.button == 1:
                if self.callback:
                    self.callback()
            self.clicked = False
            
    def render(self, screen: pygame.Surface):
        """渲染按钮"""
        # 颜色根据状态变化
        if self.clicked:
            color = (100, 100, 100)
        elif self.hovered:
            color = (80, 80, 120)
        else:
            color = (60, 60, 80)
            
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        
        # 文字
        font = pygame.font.Font(None, 32)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class MainMenu:
    """主菜单场景"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.selected_mission = 1
        
        # 创建按钮
        center_x = config.WINDOW_WIDTH // 2
        start_y = 300
        button_width = 300
        button_height = 60
        spacing = 80
        
        self.buttons = [
            Button(center_x - button_width // 2, start_y, button_width, button_height,
                  "Start Mission", self.start_game),
            Button(center_x - button_width // 2, start_y + spacing, button_width, button_height,
                  "Select Mission", self.select_mission),
            Button(center_x - button_width // 2, start_y + spacing * 2, button_width, button_height,
                  "Settings", self.open_settings),
            Button(center_x - button_width // 2, start_y + spacing * 3, button_width, button_height,
                  "Exit", self.exit_game)
        ]
        
        self.exit_requested = False
        self.start_requested = False
        
    def start_game(self):
        """开始游戏"""
        self.start_requested = True
        print(f"[MainMenu] Starting mission #{self.selected_mission}")
        
    def select_mission(self):
        """选择任务"""
        self.selected_mission = (self.selected_mission % 12) + 1
        print(f"[MainMenu] Selected mission #{self.selected_mission}")
        
    def open_settings(self):
        """打开设置"""
        print("[MainMenu] Settings not implemented yet")
        
    def exit_game(self):
        """退出游戏"""
        self.exit_requested = True
        print("[MainMenu] Exit requested")
        
    def handle_event(self, event: pygame.event.Event):
        """处理事件"""
        for button in self.buttons:
            button.handle_event(event)
            
    def update(self, delta_time: float):
        """更新"""
        pass
        
    def render(self, screen: pygame.Surface):
        """渲染菜单"""
        # 背景
        screen.fill((30, 30, 40))
        
        # 标题
        font_large = pygame.font.Font(None, 72)
        title = font_large.render("Delta Force", True, (255, 255, 255))
        title_rect = title.get_rect(center=(config.WINDOW_WIDTH // 2, 150))
        screen.blit(title, title_rect)
        
        # 副标题
        font_medium = pygame.font.Font(None, 36)
        subtitle = font_medium.render("Shadow Operations", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(center=(config.WINDOW_WIDTH // 2, 210))
        screen.blit(subtitle, subtitle_rect)
        
        # 当前任务
        mission_text = font_medium.render(f"Mission: #{self.selected_mission}", 
                                         True, (255, 255, 0))
        mission_rect = mission_text.get_rect(center=(config.WINDOW_WIDTH // 2, 260))
        screen.blit(mission_text, mission_rect)
        
        # 按钮
        for button in self.buttons:
            button.render(screen)
            
        # 版本信息
        font_small = pygame.font.Font(None, 24)
        version = font_small.render("v1.0.0-alpha | 60% Complete", 
                                   True, (100, 100, 100))
        screen.blit(version, (20, config.WINDOW_HEIGHT - 40))
        
    def should_start_game(self) -> bool:
        """检查是否开始游戏"""
        return self.start_requested
        
    def should_exit(self) -> bool:
        """检查是否退出"""
        return self.exit_requested
        
    def get_selected_mission(self) -> int:
        """获取选中的任务"""
        return self.selected_mission
