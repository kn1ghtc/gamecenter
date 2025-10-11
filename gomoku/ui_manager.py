"""UI管理器模块
UI manager for Gomoku with adaptive layout and modern design.

包含自适应布局、木纹棋盘、3D棋子效果、落子动画、交互反馈等功能。
"""

from __future__ import annotations

import math
import random
import time
from typing import List, Optional, Tuple

import pygame

from gamecenter.gomoku.config.constants import COLORS, BOARD_SIZE, CELL_SIZE
from gamecenter.gomoku.config.ui_config import LAYOUT, FONTS, ANIMATION, RENDERING, INTERACTION
from gamecenter.gomoku.font_manager import get_font_manager
from gamecenter.gomoku.game_logic import Board, Player, GameState


class AdaptiveLayout:
    """自适应布局计算器"""
    
    def __init__(self, window_width: int, window_height: int, board_size: int = BOARD_SIZE):
        """初始化布局
        
        Args:
            window_width: 窗口宽度
            window_height: 窗口高度
            board_size: 棋盘大小
        """
        self.window_width = window_width
        self.window_height = window_height
        self.board_size = board_size
        
        self.ui_panel_width = LAYOUT['ui_panel_width']
        self.board_margin = LAYOUT['board_margin']
        
        self._calculate_layout()
    
    def _calculate_layout(self) -> None:
        """计算布局参数"""
        # 计算棋盘可用空间
        available_width = self.window_width - self.ui_panel_width - self.board_margin * 2
        available_height = self.window_height - self.board_margin * 2
        
        # 计算格子大小（保持正方形）
        max_cell_size = min(
            available_width // (self.board_size - 1),
            available_height // (self.board_size - 1)
        )
        
        self.cell_size = max(20, max_cell_size)  # 最小20像素
        
        # 计算棋盘实际大小
        self.board_width = self.cell_size * (self.board_size - 1)
        self.board_height = self.cell_size * (self.board_size - 1)
        
        # 计算棋盘起始位置（居中）
        self.board_x = (self.window_width - self.ui_panel_width - self.board_width) // 2
        self.board_y = (self.window_height - self.board_height) // 2
        
        # 棋子半径
        self.stone_radius = int(self.cell_size * 0.45)
        
        # UI面板区域
        self.panel_x = self.window_width - self.ui_panel_width
        self.panel_y = 0
    
    def board_to_pixel(self, row: int, col: int) -> Tuple[int, int]:
        """将棋盘坐标转换为像素坐标
        
        Args:
            row, col: 棋盘坐标
        
        Returns:
            (x, y) 像素坐标
        """
        x = self.board_x + col * self.cell_size
        y = self.board_y + row * self.cell_size
        return (x, y)
    
    def pixel_to_board(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """将像素坐标转换为棋盘坐标
        
        Args:
            x, y: 像素坐标
        
        Returns:
            (row, col) 棋盘坐标，超出范围返回None
        """
        # 计算相对于棋盘的坐标
        rel_x = x - self.board_x
        rel_y = y - self.board_y
        
        # 转换为棋盘坐标
        col = round(rel_x / self.cell_size)
        row = round(rel_y / self.cell_size)
        
        # 检查有效性
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            # 检查是否在有效点击范围内
            px, py = self.board_to_pixel(row, col)
            distance = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            if distance <= self.stone_radius:
                return (row, col)
        
        return None


class BoardRenderer:
    """棋盘渲染器"""
    
    def __init__(self, layout: AdaptiveLayout):
        """初始化渲染器
        
        Args:
            layout: 布局计算器
        """
        self.layout = layout
        self.wood_texture = self._generate_wood_texture()
    
    def _generate_wood_texture(self) -> pygame.Surface:
        """生成木纹纹理"""
        width = self.layout.board_width + self.layout.board_margin * 2
        height = self.layout.board_height + self.layout.board_margin * 2
        
        surface = pygame.Surface((width, height))
        base_color = COLORS['board_bg']
        surface.fill(base_color)
        
        if RENDERING['board_wood_texture']:
            # 添加木纹效果
            rng = random.Random(42)  # 使用固定种子保持一致性
            for i in range(height // 3):
                y = rng.randint(0, height)
                darkness = rng.randint(-15, 5)
                line_color = tuple(max(0, min(255, c + darkness)) for c in base_color)
                pygame.draw.line(surface, line_color, (0, y), (width, y), 1)
        
        return surface
    
    def draw_board(self, screen: pygame.Surface) -> None:
        """绘制棋盘
        
        Args:
            screen: Pygame屏幕Surface
        """
        # 绘制木纹背景
        board_rect = pygame.Rect(
            self.layout.board_x - self.layout.board_margin,
            self.layout.board_y - self.layout.board_margin,
            self.layout.board_width + self.layout.board_margin * 2,
            self.layout.board_height + self.layout.board_margin * 2
        )
        screen.blit(self.wood_texture, board_rect.topleft)
        
        # 绘制边框
        pygame.draw.rect(screen, COLORS['board_border'], board_rect, 3)
        
        # 绘制棋盘线
        for i in range(self.layout.board_size):
            # 横线
            start_x, start_y = self.layout.board_to_pixel(i, 0)
            end_x, end_y = self.layout.board_to_pixel(i, self.layout.board_size - 1)
            pygame.draw.line(screen, COLORS['board_line'], 
                           (start_x, start_y), (end_x, end_y), 2)
            
            # 竖线
            start_x, start_y = self.layout.board_to_pixel(0, i)
            end_x, end_y = self.layout.board_to_pixel(self.layout.board_size - 1, i)
            pygame.draw.line(screen, COLORS['board_line'],
                           (start_x, start_y), (end_x, end_y), 2)
        
        # 绘制星位点（天元和四个星位）
        star_positions = [
            (3, 3), (3, 11), (11, 3), (11, 11), (7, 7)  # 标准五个星位
        ]
        for row, col in star_positions:
            x, y = self.layout.board_to_pixel(row, col)
            pygame.draw.circle(screen, COLORS['board_star'], (x, y), 5)
    
    def draw_stone(self, screen: pygame.Surface, row: int, col: int, 
                  player: Player, alpha: float = 1.0, scale: float = 1.0) -> None:
        """绘制棋子
        
        Args:
            screen: Pygame屏幕Surface
            row, col: 棋盘坐标
            player: 玩家
            alpha: 透明度（0.0-1.0）
            scale: 缩放比例
        """
        if player == Player.EMPTY:
            return
        
        x, y = self.layout.board_to_pixel(row, col)
        radius = int(self.layout.stone_radius * scale)
        
        # 创建棋子Surface
        stone_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        # 选择颜色
        if player == Player.BLACK:
            base_color = COLORS['black_stone']
            highlight_color = COLORS['black_highlight']
        else:
            base_color = COLORS['white_stone']
            highlight_color = COLORS['white_highlight']
        
        # 绘制阴影
        if RENDERING['shadow_enabled'] and alpha == 1.0:
            shadow_offset = RENDERING['shadow_offset']
            pygame.draw.circle(screen, COLORS['stone_shadow'],
                             (x + shadow_offset, y + shadow_offset), radius)
        
        # 绘制3D效果
        if RENDERING['stone_3d_effect']:
            # 径向渐变效果
            for i in range(radius, 0, -1):
                # 计算颜色渐变
                factor = i / radius
                color = tuple(int(base_color[j] * (0.6 + 0.4 * factor)) for j in range(3))
                pygame.draw.circle(stone_surf, color, (radius, radius), i)
            
            # 高光
            highlight_radius = radius // 3
            highlight_offset_x = -radius // 4
            highlight_offset_y = -radius // 4
            pygame.draw.circle(stone_surf, highlight_color,
                             (radius + highlight_offset_x, radius + highlight_offset_y),
                             highlight_radius)
        else:
            # 简单圆形
            pygame.draw.circle(stone_surf, base_color, (radius, radius), radius)
        
        # 应用透明度
        if alpha < 1.0:
            stone_surf.set_alpha(int(255 * alpha))
        
        # 绘制到屏幕
        screen.blit(stone_surf, (x - radius, y - radius))
    
    def draw_last_move_marker(self, screen: pygame.Surface, row: int, col: int) -> None:
        """绘制最后一步标记
        
        Args:
            screen: Pygame屏幕Surface
            row, col: 棋盘坐标
        """
        if not INTERACTION['show_last_move']:
            return
        
        x, y = self.layout.board_to_pixel(row, col)
        marker_size = self.layout.stone_radius // 2
        
        # 绘制红色方框
        rect = pygame.Rect(x - marker_size, y - marker_size,
                          marker_size * 2, marker_size * 2)
        pygame.draw.rect(screen, COLORS['last_move'], rect, 3)
    
    def draw_winning_line(self, screen: pygame.Surface, 
                         winning_line: List[Tuple[int, int]],
                         blink_state: bool) -> None:
        """绘制获胜线
        
        Args:
            screen: Pygame屏幕Surface
            winning_line: 获胜线坐标列表
            blink_state: 闪烁状态
        """
        if not blink_state or not winning_line:
            return
        
        # 绘制金色连线
        points = [self.layout.board_to_pixel(r, c) for r, c in winning_line]
        pygame.draw.lines(screen, COLORS['winning_line'], False, points, 8)
        
        # 在每个点上绘制圆圈
        for x, y in points:
            pygame.draw.circle(screen, COLORS['winning_line'], (x, y),
                             self.layout.stone_radius + 5, 4)


class Button:
    """按钮控件"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str):
        """初始化按钮
        
        Args:
            x, y: 位置
            width, height: 尺寸
            text: 按钮文字
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.state = 'normal'  # normal, hover, pressed, disabled
        self.enabled = True
    
    def draw(self, screen: pygame.Surface) -> None:
        """绘制按钮"""
        # 选择颜色
        if not self.enabled:
            color = COLORS['button_disabled']
        elif self.state == 'pressed':
            color = COLORS['button_pressed']
        elif self.state == 'hover':
            color = COLORS['button_hover']
        else:
            color = COLORS['button_normal']
        
        # 绘制背景
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['ui_text'], self.rect, 2, border_radius=8)
        
        # 绘制文字
        font_mgr = get_font_manager()
        text_surf = font_mgr.render_text(self.text, FONTS['button'], 
                                        COLORS['button_text'], bold=True)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件
        
        Args:
            event: Pygame事件
        
        Returns:
            是否被点击
        """
        if not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.state = 'hover'
            else:
                self.state = 'normal'
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.state = 'pressed'
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.rect.collidepoint(event.pos) and self.state == 'pressed':
                    self.state = 'hover'
                    return True
                self.state = 'normal'
        
        return False


class UIManager:
    """UI管理器"""
    
    def __init__(self, window_width: int, window_height: int):
        """初始化UI管理器
        
        Args:
            window_width: 窗口宽度
            window_height: 窗口高度
        """
        self.layout = AdaptiveLayout(window_width, window_height)
        self.board_renderer = BoardRenderer(self.layout)
        self.font_mgr = get_font_manager()
        
        # 动画状态
        self.stone_animations: List[Tuple[int, int, float, float]] = []  # (row, col, start_time, duration)
        self.winning_line_blink_time = 0
        self.winning_line_blink_state = False
        
        # 交互状态
        self.hover_pos: Optional[Tuple[int, int]] = None
        
        # 创建按钮
        self._create_buttons()
    
    def _create_buttons(self) -> None:
        """创建UI按钮"""
        panel_x = self.layout.panel_x + LAYOUT['panel_padding']
        start_y = 100
        spacing = LAYOUT['button_spacing']
        btn_width = LAYOUT['button_width']
        btn_height = LAYOUT['button_height']
        
        self.buttons = {
            'new_game': Button(panel_x, start_y, btn_width, btn_height, '新游戏'),
            'undo': Button(panel_x, start_y + (btn_height + spacing), 
                          btn_width, btn_height, '悔棋'),
            'difficulty': Button(panel_x, start_y + (btn_height + spacing) * 2,
                               btn_width, btn_height, '难度: 中等'),
            'save': Button(panel_x, start_y + (btn_height + spacing) * 3,
                          btn_width, btn_height, '保存'),
        }
    
    def update(self, dt: float) -> None:
        """更新动画
        
        Args:
            dt: 时间增量（毫秒）
        """
        current_time = time.time() * 1000  # 转换为毫秒
        
        # 更新落子动画
        self.stone_animations = [
            (r, c, st, dur) for r, c, st, dur in self.stone_animations
            if current_time - st < dur
        ]
        
        # 更新获胜线闪烁
        if current_time - self.winning_line_blink_time > ANIMATION['winning_line_blink']:
            self.winning_line_blink_state = not self.winning_line_blink_state
            self.winning_line_blink_time = current_time
    
    def draw(self, screen: pygame.Surface, board: Board) -> None:
        """绘制完整UI
        
        Args:
            screen: Pygame屏幕Surface
            board: 棋盘实例
        """
        # 清屏
        screen.fill(COLORS['ui_bg'])
        
        # 绘制棋盘
        self.board_renderer.draw_board(screen)
        
        # 绘制所有棋子
        current_time = time.time() * 1000
        for row in range(board.size):
            for col in range(board.size):
                player = board.get_stone(row, col)
                if player != Player.EMPTY:
                    # 检查是否在动画中
                    scale = 1.0
                    alpha = 1.0
                    for anim_r, anim_c, start_time, duration in self.stone_animations:
                        if anim_r == row and anim_c == col:
                            progress = min(1.0, (current_time - start_time) / duration)
                            scale = ANIMATION['stone_scale_start'] + (1.0 - ANIMATION['stone_scale_start']) * progress
                            break
                    
                    self.board_renderer.draw_stone(screen, row, col, player, alpha, scale)
        
        # 绘制最后一步标记
        if board.history:
            last_move = board.history[-1]
            self.board_renderer.draw_last_move_marker(screen, last_move.row, last_move.col)
        
        # 绘制获胜线
        if board.winning_line:
            self.board_renderer.draw_winning_line(screen, board.winning_line,
                                                 self.winning_line_blink_state)
        
        # 绘制悬停预览
        if INTERACTION['hover_preview'] and self.hover_pos and board.state == GameState.ONGOING:
            row, col = self.hover_pos
            if board.is_empty(row, col):
                self.board_renderer.draw_stone(screen, row, col, board.current_player, alpha=0.5)
        
        # 绘制UI面板
        self._draw_ui_panel(screen, board)
    
    def _draw_ui_panel(self, screen: pygame.Surface, board: Board) -> None:
        """绘制UI面板"""
        panel_rect = pygame.Rect(self.layout.panel_x, 0, 
                                self.layout.ui_panel_width, self.layout.window_height)
        pygame.draw.rect(screen, COLORS['ui_panel'], panel_rect)
        
        # 绘制标题
        title_surf = self.font_mgr.render_text("五子棋", FONTS['title'], 
                                              COLORS['ui_text'], bold=True)
        title_rect = title_surf.get_rect(centerx=panel_rect.centerx, top=30)
        screen.blit(title_surf, title_rect)
        
        # 绘制按钮
        for button in self.buttons.values():
            button.draw(screen)
        
        # 绘制游戏状态
        self._draw_game_status(screen, board, panel_rect)
    
    def _draw_game_status(self, screen: pygame.Surface, board: Board, panel_rect: pygame.Rect) -> None:
        """绘制游戏状态信息"""
        y = panel_rect.bottom - 300
        x = panel_rect.centerx
        
        # 当前回合
        if board.state == GameState.ONGOING:
            player_text = "黑方" if board.current_player == Player.BLACK else "白方"
            status_text = f"当前回合: {player_text}"
            color = COLORS['ui_text']
        elif board.state == GameState.BLACK_WIN:
            status_text = "黑方胜利！"
            color = COLORS['success']
        elif board.state == GameState.WHITE_WIN:
            status_text = "白方胜利！"
            color = COLORS['success']
        else:
            status_text = "平局"
            color = COLORS['warning']
        
        status_surf = self.font_mgr.render_text(status_text, FONTS['normal'], color, bold=True)
        status_rect = status_surf.get_rect(centerx=x, top=y)
        screen.blit(status_surf, status_rect)
        
        # 步数
        y += 40
        moves_text = f"步数: {len(board.history)}"
        moves_surf = self.font_mgr.render_text(moves_text, FONTS['small'], COLORS['ui_text_dim'])
        moves_rect = moves_surf.get_rect(centerx=x, top=y)
        screen.blit(moves_surf, moves_rect)
    
    def add_stone_animation(self, row: int, col: int) -> None:
        """添加落子动画
        
        Args:
            row, col: 落子位置
        """
        start_time = time.time() * 1000
        duration = ANIMATION['stone_drop_duration']
        self.stone_animations.append((row, col, start_time, duration))
    
    def handle_mouse_motion(self, pos: Tuple[int, int]) -> None:
        """处理鼠标移动
        
        Args:
            pos: 鼠标位置
        """
        self.hover_pos = self.layout.pixel_to_board(pos[0], pos[1])
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """处理鼠标点击
        
        Args:
            pos: 鼠标位置
        
        Returns:
            点击的棋盘坐标，无效点击返回None
        """
        return self.layout.pixel_to_board(pos[0], pos[1])
    
    def resize(self, window_width: int, window_height: int) -> None:
        """调整窗口大小
        
        Args:
            window_width: 新窗口宽度
            window_height: 新窗口高度
        """
        self.layout = AdaptiveLayout(window_width, window_height)
        self.board_renderer = BoardRenderer(self.layout)
        self._create_buttons()
