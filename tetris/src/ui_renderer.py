"""
UI渲染模块

负责游戏界面的美化渲染，包括背景、面板、文字显示等
"""
import os
import pygame
import math
from .settings import (
    COLORS, FONT_SIZES, BLOCK_SIZE,
    BOARD_OFFSET_X, BOARD_OFFSET_Y, BOARD_WIDTH, BOARD_HEIGHT,
    UI_PANEL_X, UI_PANEL_WIDTH, PREVIEW_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
)


class UIRenderer:
    """UI渲染器类"""
    
    def __init__(self, resource_manager):
        """
        初始化UI渲染器
        
        参数:
            resource_manager: 资源管理器实例
        """
        self.resource_manager = resource_manager
        self.fonts = {}
        self._init_fonts()
        
        # 背景动画
        self.bg_offset = 0
        self.bg_speed = 0.2
    
    def _init_fonts(self):
        """初始化字体（优先使用系统字体，确保快速启动）"""
        # 优先尝试系统字体
        font_path = None
        
        # Windows系统字体列表（按优先级）
        system_fonts = [
            ('Microsoft YaHei UI', True),  # 微软雅黑UI
            ('Microsoft YaHei', True),      # 微软雅黑
            ('SimHei', True),               # 黑体
            ('Arial', False),               # Arial（英文后备）
        ]
        
        for font_name, is_chinese in system_fonts:
            try:
                # 尝试使用系统字体
                test_font = pygame.font.SysFont(font_name, 24)
                if test_font:
                    # 使用找到的系统字体
                    for name, size in FONT_SIZES.items():
                        self.fonts[name] = pygame.font.SysFont(font_name, size)
                    return
            except:
                continue
        
        # 如果系统字体都失败，尝试下载的字体
        font_path = self.resource_manager.get_font_path(fallback=False)
        
        # 加载字体
        for name, size in FONT_SIZES.items():
            try:
                if font_path and os.path.exists(font_path):
                    self.fonts[name] = pygame.font.Font(font_path, size)
                else:
                    # 最后的后备：pygame默认字体
                    self.fonts[name] = pygame.font.Font(None, size)
            except:
                # 确保一定有字体可用
                self.fonts[name] = pygame.font.Font(None, size)
    
    def draw_background(self, surface):
        """
        绘制动态背景
        
        参数:
            surface: pygame绘制表面
        """
        # 渐变背景
        for y in range(WINDOW_HEIGHT):
            ratio = y / WINDOW_HEIGHT
            r = int(COLORS['BLACK'][0] + (COLORS['UI_BG'][0] - COLORS['BLACK'][0]) * ratio)
            g = int(COLORS['BLACK'][1] + (COLORS['UI_BG'][1] - COLORS['BLACK'][1]) * ratio)
            b = int(COLORS['BLACK'][2] + (COLORS['UI_BG'][2] - COLORS['BLACK'][2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))
        
        # 动态网格效果
        self.bg_offset = (self.bg_offset + self.bg_speed) % 40
        
        grid_color = (*COLORS['DARK_GRAY'], 30)
        for x in range(0, WINDOW_WIDTH, 40):
            offset_x = int(x + self.bg_offset)
            pygame.draw.line(surface, COLORS['DARK_GRAY'], (offset_x, 0), (offset_x, WINDOW_HEIGHT), 1)
        
        for y in range(0, WINDOW_HEIGHT, 40):
            offset_y = int(y + self.bg_offset)
            pygame.draw.line(surface, COLORS['DARK_GRAY'], (0, offset_y), (WINDOW_WIDTH, offset_y), 1)
    
    def draw_board_frame(self, surface):
        """
        绘制游戏板边框
        
        参数:
            surface: pygame绘制表面
        """
        # 主边框
        board_rect = pygame.Rect(
            BOARD_OFFSET_X - 4,
            BOARD_OFFSET_Y - 4,
            BOARD_WIDTH * BLOCK_SIZE + 8,
            BOARD_HEIGHT * BLOCK_SIZE + 8
        )
        
        # 绘制多层边框创建3D效果
        pygame.draw.rect(surface, COLORS['UI_BORDER'], board_rect, 4)
        pygame.draw.rect(surface, COLORS['DARK_GRAY'], board_rect.inflate(-4, -4), 2)
        
        # 内部阴影
        shadow_rect = board_rect.inflate(-8, -8)
        pygame.draw.rect(surface, COLORS['BLACK'], shadow_rect, 1)
    
    def draw_panel_background(self, surface, x, y, width, height, title=None):
        """
        绘制面板背景
        
        参数:
            surface: pygame绘制表面
            x, y: 面板位置
            width, height: 面板大小
            title: 面板标题
        """
        # 半透明背景
        panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        panel_surf.fill((*COLORS['UI_BG'], 200))
        surface.blit(panel_surf, (x, y))
        
        # 边框
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, COLORS['UI_BORDER'], panel_rect, 2)
        
        # 标题
        if title:
            title_text = self.fonts['MEDIUM'].render(title, True, COLORS['TEXT_PRIMARY'])
            title_x = x + (width - title_text.get_width()) // 2
            title_y = y + 10
            surface.blit(title_text, (title_x, title_y))
            
            # 标题下划线
            line_y = title_y + title_text.get_height() + 5
            pygame.draw.line(
                surface, COLORS['UI_BORDER'],
                (x + 10, line_y), (x + width - 10, line_y), 2
            )
    
    def draw_next_piece_preview(self, surface, next_piece, x, y):
        """
        绘制下一个方块预览
        
        参数:
            surface: pygame绘制表面
            next_piece: 下一个方块对象
            x, y: 绘制位置
        """
        # 绘制面板
        self.draw_panel_background(surface, x, y, PREVIEW_SIZE + 20, PREVIEW_SIZE + 60, "NEXT")
        
        if next_piece:
            # 计算居中位置
            shape_width = len(next_piece.shape[0]) * BLOCK_SIZE
            shape_height = len(next_piece.shape) * BLOCK_SIZE
            
            start_x = x + 10 + (PREVIEW_SIZE - shape_width) // 2
            start_y = y + 50 + (PREVIEW_SIZE - shape_height) // 2
            
            # 绘制方块
            for row_idx, row in enumerate(next_piece.shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        block_x = start_x + col_idx * BLOCK_SIZE
                        block_y = start_y + row_idx * BLOCK_SIZE
                        next_piece.draw_block_3d(
                            surface, block_x, block_y,
                            BLOCK_SIZE, next_piece.color
                        )
    
    def draw_score_panel(self, surface, score, level, lines, x, y):
        """
        绘制分数面板
        
        参数:
            surface: pygame绘制表面
            score: 当前分数
            level: 当前关卡
            lines: 消除行数
            x, y: 面板位置
        """
        panel_height = 200
        self.draw_panel_background(surface, x, y, UI_PANEL_WIDTH, panel_height, "STATS")
        
        # 分数
        score_label = self.fonts['SMALL'].render("Score:", True, COLORS['TEXT_SECONDARY'])
        score_value = self.fonts['LARGE'].render(str(score), True, COLORS['TEXT_PRIMARY'])
        surface.blit(score_label, (x + 15, y + 60))
        surface.blit(score_value, (x + 15, y + 85))
        
        # 关卡
        level_label = self.fonts['SMALL'].render("Level:", True, COLORS['TEXT_SECONDARY'])
        level_value = self.fonts['MEDIUM'].render(str(level), True, COLORS['LEVEL_UP'])
        surface.blit(level_label, (x + 15, y + 130))
        surface.blit(level_value, (x + 15, y + 150))
        
        # 消行数
        lines_label = self.fonts['TINY'].render(f"Lines: {lines}", True, COLORS['TEXT_SECONDARY'])
        surface.blit(lines_label, (x + 15, y + panel_height - 30))
    
    def draw_controls_panel(self, surface, x, y):
        """
        绘制操作说明面板
        
        参数:
            surface: pygame绘制表面
            x, y: 面板位置
        """
        panel_height = 280
        self.draw_panel_background(surface, x, y, UI_PANEL_WIDTH, panel_height, "CONTROLS")
        
        controls = [
            ("← / →", "Move"),
            ("↓", "Soft Drop"),
            ("Space", "Hard Drop"),
            ("↑ / Z", "Rotate"),
            ("P", "Pause"),
            ("R", "Restart"),
            ("Esc", "Quit")
        ]
        
        y_offset = y + 60
        for key, action in controls:
            key_text = self.fonts['TINY'].render(key, True, COLORS['UI_BORDER'])
            action_text = self.fonts['TINY'].render(action, True, COLORS['TEXT_SECONDARY'])
            
            surface.blit(key_text, (x + 15, y_offset))
            surface.blit(action_text, (x + 100, y_offset))
            y_offset += 30
    
    def draw_game_over_overlay(self, surface, score, level):
        """
        绘制游戏结束覆盖层
        
        参数:
            surface: pygame绘制表面
            score: 最终分数
            level: 最终关卡
        """
        # 半透明背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # 游戏结束标题
        title_text = self.fonts['TITLE'].render("GAME OVER", True, COLORS['RED'])
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(title_text, title_rect)
        
        # 分数显示
        score_text = self.fonts['LARGE'].render(f"Final Score: {score}", True, COLORS['TEXT_PRIMARY'])
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(score_text, score_rect)
        
        # 关卡显示
        level_text = self.fonts['MEDIUM'].render(f"Level Reached: {level}", True, COLORS['LEVEL_UP'])
        level_rect = level_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        surface.blit(level_text, level_rect)
        
        # 重新开始提示
        restart_text = self.fonts['SMALL'].render("Press R to Restart or ESC to Quit", True, COLORS['TEXT_SECONDARY'])
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT * 2 // 3))
        surface.blit(restart_text, restart_rect)
    
    def draw_pause_overlay(self, surface):
        """
        绘制暂停覆盖层
        
        参数:
            surface: pygame绘制表面
        """
        # 半透明背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # 暂停文字
        pause_text = self.fonts['TITLE'].render("PAUSED", True, COLORS['TEXT_PRIMARY'])
        pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(pause_text, pause_rect)
        
        # 提示文字
        hint_text = self.fonts['MEDIUM'].render("Press P to Continue", True, COLORS['TEXT_SECONDARY'])
        hint_rect = hint_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        surface.blit(hint_text, hint_rect)
    
    def draw_level_up_notification(self, surface, level, alpha=255):
        """
        绘制升级通知
        
        参数:
            surface: pygame绘制表面
            level: 新关卡
            alpha: 透明度
        """
        # 创建通知表面
        notif_surf = pygame.Surface((400, 100), pygame.SRCALPHA)
        
        # 背景
        pygame.draw.rect(notif_surf, (*COLORS['UI_BG'], alpha), notif_surf.get_rect())
        pygame.draw.rect(notif_surf, (*COLORS['LEVEL_UP'], alpha), notif_surf.get_rect(), 3)
        
        # 文字
        text = self.fonts['LARGE'].render(f"LEVEL {level}!", True, (*COLORS['LEVEL_UP'][:3], alpha))
        text_rect = text.get_rect(center=(200, 50))
        notif_surf.blit(text, text_rect)
        
        # 居中显示
        x = (WINDOW_WIDTH - 400) // 2
        y = WINDOW_HEIGHT // 4
        surface.blit(notif_surf, (x, y))
    
    def draw_combo_text(self, surface, combo, x, y, alpha=255):
        """
        绘制连击文字
        
        参数:
            surface: pygame绘制表面
            combo: 连击数
            x, y: 显示位置
            alpha: 透明度
        """
        if combo <= 1:
            return
        
        combo_text = self.fonts['LARGE'].render(f"COMBO x{combo}!", True, (*COLORS['COMBO'][:3], alpha))
        combo_rect = combo_text.get_rect(center=(x, y))
        
        # 创建带透明度的表面
        text_surf = pygame.Surface(combo_rect.size, pygame.SRCALPHA)
        text_surf.blit(combo_text, (0, 0))
        
        surface.blit(text_surf, combo_rect.topleft)
