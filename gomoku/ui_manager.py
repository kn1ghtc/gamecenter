"""UI管理器模块
UI manager for Gomoku with adaptive layout and modern design.

包含自适应布局、木纹棋盘、3D棋子效果、落子动画、交互反馈等功能。
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple, Sequence

import pygame

from gamecenter.gomoku.config.config_manager import get_config_manager
from gamecenter.gomoku.font_manager import get_font_manager
from gamecenter.gomoku.game_logic import Board, Player, GameState


_CONFIG = get_config_manager()
_UI_CONFIG = _CONFIG.get_ui_config()
LAYOUT = _UI_CONFIG.get('layout', {})
FONTS = _UI_CONFIG.get('fonts', {})
ANIMATION = _UI_CONFIG.get('animation', {})
RENDERING = _UI_CONFIG.get('rendering', {})
INTERACTION = _UI_CONFIG.get('interaction', {})
COLORS = _CONFIG.get_colors()
BOARD_SIZE = _CONFIG.get_gameplay_config().get('board_size', 15)


@dataclass(frozen=True)
class PlayerPanelData:
    """Player panel rendering data."""

    name: str
    player: Player
    score: int
    last_move: Optional[str]
    last_move_time: Optional[float]
    total_time: float
    status_line: str
    is_active: bool
    is_ai: bool
    is_thinking: bool
    thinking_time: float


@dataclass(frozen=True)
class UISidebarState:
    """Aggregated sidebar state for rendering."""

    game_mode_label: str
    current_turn_text: str
    status_type: str
    move_count: int
    players: Sequence[PlayerPanelData]
    info_lines: Sequence[str]


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
        effective_width = self.window_width - self.ui_panel_width - self.board_margin * 2
        effective_height = self.window_height - self.board_margin * 2

        max_width = max(1.0, float(effective_width))
        max_height = max(1.0, float(effective_height))
        divisor = float(max(1, self.board_size - 1))

        width_limit = max_width / divisor
        height_limit = max_height / divisor
        is_width_limited = width_limit <= height_limit
        if is_width_limited:
            self.cell_size = max(1.0, width_limit)
        else:
            self.cell_size = max(1.0, height_limit)

        self.board_width = self.cell_size * divisor
        self.board_height = self.cell_size * divisor

        # 计算右侧面板起点，确保不会出现负值
        self.panel_x = max(0, self.window_width - self.ui_panel_width)

        # 左侧保留边距，必要时向左压缩以保证棋盘完全可见
        left_bound = self.board_margin
        right_bound = self.panel_x - self.board_margin

        if right_bound <= left_bound:
            # 面板占据多数宽度时退化为贴边展示
            available_x = self.panel_x - self.board_width - self.board_margin
            self.board_x = max(0.0, available_x)
        else:
            usable_width = right_bound - left_bound
            if is_width_limited and self.board_width <= usable_width:
                # 左右同时贴合可用区域
                self.board_x = left_bound
                self.board_width = usable_width
                self.cell_size = self.board_width / divisor
                self.board_height = self.cell_size * divisor
            else:
                # 宽度不足时仍保持右缘贴近面板并防止超出左界
                self.board_x = max(0.0, right_bound - self.board_width)

        vertical_space = self.window_height - self.board_height - self.board_margin * 2
        if vertical_space > 0:
            self.board_y = self.board_margin + vertical_space // 2
        else:
            self.board_y = self.board_margin
        
        # 棋子半径
        self.stone_radius = max(2, int(self.cell_size * 0.45))
        
        # UI面板区域
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
        return (int(round(x)), int(round(y)))
    
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
        col = int(round(rel_x / self.cell_size))
        row = int(round(rel_y / self.cell_size))
        
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
        width = int(math.ceil(self.layout.board_width + self.layout.board_margin * 2))
        height = int(math.ceil(self.layout.board_height + self.layout.board_margin * 2))

        surface = pygame.Surface((width, height))
        base_color = COLORS['board_bg']
        surface.fill(base_color)
        
        if RENDERING['board_wood_texture']:
            # 添加木纹效果
            rng = random.Random(42)  # 使用固定种子保持一致性
            for _ in range(height // 3):
                y = rng.randint(0, max(0, height - 1))
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
            int(round(self.layout.board_x - self.layout.board_margin)),
            int(round(self.layout.board_y - self.layout.board_margin)),
            int(math.ceil(self.layout.board_width + self.layout.board_margin * 2)),
            int(math.ceil(self.layout.board_height + self.layout.board_margin * 2))
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
        spacing = LAYOUT['button_spacing']
        btn_width = LAYOUT['button_width']
        btn_height = LAYOUT['button_height']

        # 初始位置占位，实际布局在绘制面板时动态调整
        base_y = self.layout.window_height // 2
        self.buttons = {
            'new_game': Button(panel_x, base_y, btn_width, btn_height, '新游戏'),
            'undo': Button(panel_x, base_y + (btn_height + spacing), btn_width, btn_height, '悔棋'),
            'difficulty': Button(panel_x, base_y + (btn_height + spacing) * 2, btn_width, btn_height, 'AI难度: 中等'),
            'mode': Button(panel_x, base_y + (btn_height + spacing) * 3, btn_width, btn_height, '模式: 人机对战'),
            'save': Button(panel_x, base_y + (btn_height + spacing) * 4, btn_width, btn_height, '保存棋局'),
        }
        self._button_order = ['new_game', 'undo', 'difficulty', 'mode', 'save']
    
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
    
    def draw(self, screen: pygame.Surface, board: Board, sidebar_state: UISidebarState) -> None:
        """绘制完整UI
        
        Args:
            screen: Pygame屏幕Surface
            board: 棋盘实例
            sidebar_state: 侧边栏渲染状态
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
        self._draw_ui_panel(screen, board, sidebar_state)
    
    def _draw_ui_panel(self, screen: pygame.Surface, board: Board, sidebar_state: UISidebarState) -> None:
        """绘制UI面板"""
        panel_rect = pygame.Rect(
            self.layout.panel_x,
            0,
            self.layout.ui_panel_width,
            self.layout.window_height,
        )
        pygame.draw.rect(screen, COLORS['ui_panel'], panel_rect)

        padding = LAYOUT.get('panel_padding', 15)
        player_height = LAYOUT.get('player_info_height', 140)
        panel_spacing = LAYOUT.get('player_panel_spacing', 18)
        info_margin = LAYOUT.get('info_section_margin', 20)

        # 标题
        title_surf = self.font_mgr.render_text("五子棋", FONTS['title'], COLORS['ui_text'], bold=True)
        title_rect = title_surf.get_rect(
            centerx=panel_rect.centerx,
            top=panel_rect.top + padding,
        )
        screen.blit(title_surf, title_rect)

        # 玩家面板
        panel_width = self.layout.ui_panel_width - padding * 2
        panel_x = panel_rect.left + padding
        current_y = title_rect.bottom + panel_spacing

        for player_data in sidebar_state.players:
            player_rect = pygame.Rect(panel_x, current_y, panel_width, player_height)
            self._draw_player_panel(screen, player_rect, player_data)
            current_y = player_rect.bottom + panel_spacing

        # 布局按钮
        button_start_y = current_y + info_margin
        self._layout_buttons(panel_rect, button_start_y)
        for name in self._button_order:
            self.buttons[name].draw(screen)

        # 游戏状态信息
        status_start_y = self._button_bottom() + info_margin
        self._draw_game_status(screen, panel_rect, sidebar_state, status_start_y)

    def _draw_player_panel(self, screen: pygame.Surface, rect: pygame.Rect, data: PlayerPanelData) -> None:
        """绘制单个玩家信息面板"""
        active_bg = COLORS.get('panel_active_bg', self._shift_color(COLORS['ui_panel'], 20))
        inactive_bg = COLORS.get('panel_inactive_bg', self._shift_color(COLORS['ui_panel'], -5))
        border_active = COLORS.get('panel_border_active', COLORS['info'])
        border_inactive = COLORS.get('panel_border_inactive', COLORS['ui_text_dim'])

        bg_color = active_bg if data.is_active else inactive_bg
        border_color = border_active if data.is_active else border_inactive

        pygame.draw.rect(screen, bg_color, rect, border_radius=12)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=12)

        indicator_radius = 12
        indicator_color = (20, 20, 20) if data.player == Player.BLACK else (240, 240, 240)
        indicator_pos = (rect.left + 24, rect.top + 28)
        pygame.draw.circle(screen, indicator_color, indicator_pos, indicator_radius)
        pygame.draw.circle(screen, COLORS['board_border'], indicator_pos, indicator_radius, 2)

        text_x = indicator_pos[0] + indicator_radius + 14
        current_y = rect.top + 12

        title_text = f"{data.name}  |  积分 {data.score}"
        title_color = COLORS['ui_text']
        title_surf = self.font_mgr.render_text(title_text, FONTS['large'], title_color, bold=True)
        screen.blit(title_surf, (text_x, current_y))
        current_y += title_surf.get_height() + 6

        status_color = COLORS['info'] if data.is_thinking else COLORS['ui_text']
        status_text = data.status_line
        status_surf = self.font_mgr.render_text(status_text, FONTS['normal'], status_color)
        screen.blit(status_surf, (text_x, current_y))
        current_y += status_surf.get_height() + 6

        last_move = data.last_move or "--"
        last_move_time = self._format_time_text(data.last_move_time)
        move_line = f"最近落子: {last_move}  |  用时 {last_move_time}"
        move_surf = self.font_mgr.render_text(move_line, FONTS['small'], COLORS['ui_text_dim'])
        screen.blit(move_surf, (text_x, current_y))
        current_y += move_surf.get_height() + 4

        total_time_text = self._format_time_text(data.total_time)
        total_line = f"累计用时: {total_time_text}"
        total_surf = self.font_mgr.render_text(total_line, FONTS['small'], COLORS['ui_text_dim'])
        screen.blit(total_surf, (text_x, current_y))

        if data.is_thinking and data.thinking_time > 0:
            thinking_text = f"思考中: {self._format_time_text(data.thinking_time)}"
            thinking_surf = self.font_mgr.render_text(thinking_text, FONTS['small'], COLORS['info'])
            screen.blit(thinking_surf, (text_x, current_y + total_surf.get_height() + 4))

    def _layout_buttons(self, panel_rect: pygame.Rect, start_y: int) -> None:
        panel_x = panel_rect.left + LAYOUT.get('panel_padding', 15)
        spacing = LAYOUT.get('button_spacing', 12)
        for index, name in enumerate(self._button_order):
            button = self.buttons[name]
            button.rect.x = panel_x
            button.rect.y = start_y + index * (button.rect.height + spacing)

    def _button_bottom(self) -> int:
        last_button = self.buttons[self._button_order[-1]]
        return last_button.rect.bottom

    def _draw_game_status(self, screen: pygame.Surface, panel_rect: pygame.Rect,
                           sidebar_state: UISidebarState, start_y: int) -> None:
        """绘制游戏状态信息"""
        text_x = panel_rect.left + LAYOUT.get('panel_padding', 15)
        center_x = panel_rect.centerx

        mode_surf = self.font_mgr.render_text(sidebar_state.game_mode_label, FONTS['normal'], COLORS['ui_text_dim'])
        mode_rect = mode_surf.get_rect(topleft=(text_x, start_y))
        screen.blit(mode_surf, mode_rect)

        status_color = self._get_status_color(sidebar_state.status_type)
        status_surf = self.font_mgr.render_text(sidebar_state.current_turn_text, FONTS['large'], status_color, bold=True)
        status_rect = status_surf.get_rect(centerx=center_x, top=mode_rect.bottom + 6)
        screen.blit(status_surf, status_rect)

        moves_text = f"总步数: {sidebar_state.move_count}"
        moves_surf = self.font_mgr.render_text(moves_text, FONTS['normal'], COLORS['ui_text_dim'])
        moves_rect = moves_surf.get_rect(centerx=center_x, top=status_rect.bottom + 6)
        screen.blit(moves_surf, moves_rect)

        info_y = moves_rect.bottom + 10
        for line in sidebar_state.info_lines:
            info_surf = self.font_mgr.render_text(line, FONTS['small'], COLORS['ui_text_dim'])
            info_rect = info_surf.get_rect(centerx=center_x, top=info_y)
            screen.blit(info_surf, info_rect)
            info_y += info_surf.get_height() + 4

    def _get_status_color(self, status_type: str) -> tuple:
        if status_type in {GameState.BLACK_WIN.value, 'black_win'}:
            return COLORS.get('success', COLORS['ui_text'])
        if status_type in {GameState.WHITE_WIN.value, 'white_win'}:
            return COLORS.get('success', COLORS['ui_text'])
        if status_type in {GameState.DRAW.value, 'draw'}:
            return COLORS.get('warning', COLORS['ui_text'])
        return COLORS['ui_text']

    @staticmethod
    def _shift_color(color: tuple, delta: int) -> tuple:
        return tuple(max(0, min(255, c + delta)) for c in color)

    @staticmethod
    def _format_time_text(value: Optional[float]) -> str:
        if value is None:
            return "--"
        return f"{value:.2f}s"
    
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
