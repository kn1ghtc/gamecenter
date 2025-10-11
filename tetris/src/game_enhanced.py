"""
俄罗斯方块主游戏类

实现完整的游戏逻辑，包括100关卡系统、积分系统、
自适应屏幕、动态效果等特性
"""
import os
import sys
import pygame
from .settings import *
from .tetromino import Tetromino
from .board import Board
from .resource_manager import get_resource_manager
from .ui_renderer import UIRenderer
from .sound_manager import SoundManager

# Windows控制台UTF-8编码
os.system("chcp 65001 >nul 2>&1")


class TetrisGame:
    """
    俄罗斯方块主游戏类

    管理游戏主循环、渲染和用户输入，支持100关卡系统
    """

    def __init__(self):
        """初始化游戏"""
        pygame.init()
        
        # 创建窗口
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - Tetris Enhanced")
        
        # 资源管理（禁用自动下载，提升启动速度）
        self.resource_manager = get_resource_manager(auto_download=False)
        
        # 初始化各个系统
        self.clock = pygame.time.Clock()
        self.ui_renderer = UIRenderer(self.resource_manager)
        self.sound_manager = SoundManager(self.resource_manager)
        
        # 游戏状态
        self.board = Board()
        self.current_piece = None
        self.next_piece = None
        self.ghost_positions = []
        
        # 分数和关卡系统
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.combo = 0
        
        # 时间控制
        self.fall_time = 0
        self.fall_speed = get_level_speed(self.level)
        self.move_time = 0
        self.rotate_time = 0
        
        # 游戏状态标志
        self.game_over = False
        self.paused = False
        self.running = True
        
        # 输入状态
        self.keys_pressed = {}
        self.last_move_time = 0
        self.last_rotate_time = 0
        
        # 动画效果
        self.level_up_animation = 0
        self.combo_animation = 0
        self.combo_pos_y = WINDOW_HEIGHT // 3
    
    def start_game(self):
        """开始新游戏"""
        self.board.clear()
        self.current_piece = Tetromino()
        self.next_piece = Tetromino()
        self._place_piece_at_top()
        
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.combo = 0
        
        self.fall_time = 0
        self.fall_speed = get_level_speed(self.level)
        
        self.game_over = False
        self.paused = False
        
        self.level_up_animation = 0
        self.combo_animation = 0
        
        # 播放背景音乐
        self.sound_manager.play_music()
    
    def _place_piece_at_top(self):
        """将方块放置在顶部中间"""
        self.current_piece.x = self.board.width // 2 - len(self.current_piece.shape[0]) // 2
        self.current_piece.y = 0
        self._update_ghost_positions()
    
    def _update_ghost_positions(self):
        """更新幽灵方块位置"""
        if self.current_piece:
            self.ghost_positions = self.current_piece.get_ghost_positions(
                self.board, self.current_piece.y
            )
    
    def handle_input(self):
        """处理用户输入"""
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # 游戏结束后的输入
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        return False
                    continue
                
                # 暂停
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                    if self.paused:
                        self.sound_manager.pause_music()
                    else:
                        self.sound_manager.unpause_music()
                    continue
                
                if self.paused:
                    continue
                
                # 移动控制
                if event.key == pygame.K_LEFT:
                    if self.move_piece(-1, 0):
                        self.sound_manager.play_move()
                    self.last_move_time = current_time
                
                elif event.key == pygame.K_RIGHT:
                    if self.move_piece(1, 0):
                        self.sound_manager.play_move()
                    self.last_move_time = current_time
                
                elif event.key == pygame.K_DOWN:
                    if self.move_piece(0, 1):
                        self.score += SCORE_SOFT_DROP
                        self.sound_manager.play_move()
                
                # 旋转
                elif event.key == pygame.K_UP or event.key == pygame.K_z:
                    if self.rotate_piece():
                        self.sound_manager.play_rotate()
                    self.last_rotate_time = current_time
                
                # 硬下落
                elif event.key == pygame.K_SPACE:
                    drop_distance = self.hard_drop()
                    self.score += drop_distance * SCORE_HARD_DROP
                    self.sound_manager.play_drop()
                    self.lock_current_piece()
                
                # 重新开始
                elif event.key == pygame.K_r:
                    self.start_game()
                
                # 退出
                elif event.key == pygame.K_ESCAPE:
                    return False
        
        # 持续按键处理（自动重复）
        if not self.game_over and not self.paused:
            keys = pygame.key.get_pressed()
            
            # 左右移动自动重复
            if keys[pygame.K_LEFT] and current_time - self.last_move_time > MOVE_DELAY:
                if self.move_piece(-1, 0):
                    self.sound_manager.play_move()
                self.last_move_time = current_time
            
            elif keys[pygame.K_RIGHT] and current_time - self.last_move_time > MOVE_DELAY:
                if self.move_piece(1, 0):
                    self.sound_manager.play_move()
                self.last_move_time = current_time
            
            # 下移自动重复
            if keys[pygame.K_DOWN]:
                if current_time - self.fall_time > max(50, self.fall_speed // 10):
                    if self.move_piece(0, 1):
                        self.score += SCORE_SOFT_DROP
                    self.fall_time = current_time
        
        return True
    
    def move_piece(self, dx, dy):
        """
        移动当前方块

        参数:
            dx: x方向移动距离
            dy: y方向移动距离
            
        返回:
            bool: 是否移动成功
        """
        if self.board.is_valid_move(self.current_piece,
                                     self.current_piece.x + dx,
                                     self.current_piece.y + dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            self._update_ghost_positions()
            return True
        return False
    
    def rotate_piece(self):
        """
        旋转当前方块
        
        返回:
            bool: 是否旋转成功
        """
        # 保存原始状态
        original_rotation = self.current_piece.rotation_state
        
        # 尝试旋转
        self.current_piece.rotate_clockwise()
        
        # 检查是否有效
        if self.board.is_valid_move(self.current_piece,
                                     self.current_piece.x,
                                     self.current_piece.y):
            self._update_ghost_positions()
            return True
        
        # 尝试Wall Kick（墙踢）
        kick_offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1)]
        
        for dx, dy in kick_offsets:
            if self.board.is_valid_move(self.current_piece,
                                         self.current_piece.x + dx,
                                         self.current_piece.y + dy):
                self.current_piece.x += dx
                self.current_piece.y += dy
                self._update_ghost_positions()
                return True
        
        # 旋转失败，恢复原状态
        self.current_piece.rotation_state = original_rotation
        self.current_piece.shape = self.current_piece.shapes_list[original_rotation]
        return False
    
    def hard_drop(self):
        """
        硬下落（直接落到底部）
        
        返回:
            int: 下落的距离
        """
        distance = 0
        while self.move_piece(0, 1):
            distance += 1
        return distance
    
    def lock_current_piece(self):
        """锁定当前方块并生成新方块"""
        # 锁定方块到游戏板
        self.board.lock_piece(self.current_piece)
        
        # 检查并消除完整行
        full_lines = self.board.find_full_lines()
        
        if full_lines:
            # 开始消行动画
            self.board.start_clear_animation(full_lines)
            self.sound_manager.play_clear()
            
            # 计算分数
            lines_count = len(full_lines)
            self.lines_cleared += lines_count
            
            # 连击系统
            self.combo += 1
            combo_multiplier = 1.0 + (self.combo - 1) * (COMBO_MULTIPLIER - 1.0)
            
            # 根据消除行数给分
            base_score = 0
            if lines_count == 1:
                base_score = SCORE_SINGLE_LINE
            elif lines_count == 2:
                base_score = SCORE_DOUBLE_LINE
            elif lines_count == 3:
                base_score = SCORE_TRIPLE_LINE
            elif lines_count >= 4:
                base_score = SCORE_TETRIS
            
            # 应用连击倍数和关卡倍数
            self.score += int(base_score * combo_multiplier * self.level)
            
            # 显示连击动画
            if self.combo > 1:
                self.combo_animation = 2000  # 2秒
                self.combo_pos_y = WINDOW_HEIGHT // 3
            
            # 检查是否升级
            new_level = min(MAX_LEVEL, 1 + self.lines_cleared // LINES_PER_LEVEL)
            if new_level > self.level:
                self.level = new_level
                self.fall_speed = get_level_speed(self.level)
                self.level_up_animation = 3000  # 3秒
                self.sound_manager.play_level_up()
        else:
            # 没有消行，重置连击
            self.combo = 0
        
        # 生成新方块
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()
        self._place_piece_at_top()
        
        # 检查游戏是否结束
        if not self.board.is_valid_move(self.current_piece,
                                         self.current_piece.x,
                                         self.current_piece.y):
            self.game_over = True
            self.sound_manager.play_game_over()
            self.sound_manager.stop_music()
    
    def update(self, dt):
        """
        更新游戏状态
        
        参数:
            dt: 时间增量（毫秒）
        """
        if self.game_over or self.paused:
            return
        
        # 更新消行动画
        if self.board.is_clearing:
            animation_done = self.board.update_clear_animation(dt)
            if animation_done:
                # 动画完成后才锁定新方块
                pass
        else:
            # 方块自动下落
            self.fall_time += dt
            if self.fall_time >= self.fall_speed:
                if not self.move_piece(0, 1):
                    # 无法下移，锁定方块
                    self.lock_current_piece()
                self.fall_time = 0
        
        # 更新粒子效果
        self.board.update_particles(dt)
        
        # 更新动画
        if self.level_up_animation > 0:
            self.level_up_animation -= dt
        
        if self.combo_animation > 0:
            self.combo_animation -= dt
            self.combo_pos_y -= 0.5  # 上浮效果
    
    def draw(self):
        """渲染游戏画面"""
        # 绘制背景
        self.ui_renderer.draw_background(self.screen)
        
        # 绘制游戏板边框
        self.ui_renderer.draw_board_frame(self.screen)
        
        # 绘制游戏板上的方块
        self._draw_board()
        
        # 绘制幽灵方块
        self._draw_ghost_piece()
        
        # 绘制当前方块
        self._draw_current_piece()
        
        # 绘制粒子效果
        self.board.draw_particles(self.screen, BOARD_OFFSET_X, BOARD_OFFSET_Y)
        
        # 绘制消行动画
        self._draw_clear_animation()
        
        # 绘制UI面板
        self.ui_renderer.draw_next_piece_preview(
            self.screen, self.next_piece,
            UI_PANEL_X, BOARD_OFFSET_Y
        )
        
        self.ui_renderer.draw_score_panel(
            self.screen, self.score, self.level, self.lines_cleared,
            UI_PANEL_X, BOARD_OFFSET_Y + PREVIEW_SIZE + 80
        )
        
        self.ui_renderer.draw_controls_panel(
            self.screen,
            UI_PANEL_X, BOARD_OFFSET_Y + PREVIEW_SIZE + 310
        )
        
        # 绘制升级通知
        if self.level_up_animation > 0:
            alpha = min(255, int(self.level_up_animation / 3000 * 255))
            self.ui_renderer.draw_level_up_notification(self.screen, self.level, alpha)
        
        # 绘制连击文字
        if self.combo_animation > 0:
            alpha = min(255, int(self.combo_animation / 2000 * 255))
            self.ui_renderer.draw_combo_text(
                self.screen, self.combo,
                WINDOW_WIDTH // 2, int(self.combo_pos_y), alpha
            )
        
        # 绘制暂停和游戏结束覆盖层
        if self.paused:
            self.ui_renderer.draw_pause_overlay(self.screen)
        
        if self.game_over:
            self.ui_renderer.draw_game_over_overlay(self.screen, self.score, self.level)
        
        pygame.display.flip()
    
    def _draw_board(self):
        """绘制游戏板上的已锁定方块"""
        for y in range(self.board.height):
            for x in range(self.board.width):
                if self.board.grid[y][x]:
                    block_x = BOARD_OFFSET_X + x * BLOCK_SIZE
                    block_y = BOARD_OFFSET_Y + y * BLOCK_SIZE
                    
                    # 使用Tetromino的3D绘制方法
                    temp_piece = Tetromino()
                    temp_piece.color = self.board.grid[y][x]
                    temp_piece.draw_block_3d(
                        self.screen, block_x, block_y,
                        BLOCK_SIZE, temp_piece.color
                    )
    
    def _draw_ghost_piece(self):
        """绘制幽灵方块（显示将要落在哪里）"""
        if not self.current_piece or self.game_over:
            return
        
        for x, y in self.ghost_positions:
            if y >= 0:  # 只绘制可见部分
                block_x = BOARD_OFFSET_X + x * BLOCK_SIZE
                block_y = BOARD_OFFSET_Y + y * BLOCK_SIZE
                
                # 绘制半透明的幽灵方块
                ghost_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                color = COLORS.get(self.current_piece.color, COLORS['WHITE'])
                ghost_color = (*color[:3], 80)  # 半透明
                pygame.draw.rect(ghost_surf, ghost_color, ghost_surf.get_rect())
                pygame.draw.rect(ghost_surf, (*color[:3], 150), ghost_surf.get_rect(), 2)
                
                self.screen.blit(ghost_surf, (block_x, block_y))
    
    def _draw_current_piece(self):
        """绘制当前方块"""
        if not self.current_piece or self.game_over:
            return
        
        positions = self.current_piece.get_positions()
        for x, y in positions:
            if y >= 0:  # 只绘制可见部分
                block_x = BOARD_OFFSET_X + x * BLOCK_SIZE
                block_y = BOARD_OFFSET_Y + y * BLOCK_SIZE
                
                self.current_piece.draw_block_3d(
                    self.screen, block_x, block_y,
                    BLOCK_SIZE, self.current_piece.color
                )
    
    def _draw_clear_animation(self):
        """绘制消行动画"""
        if not self.board.is_clearing:
            return
        
        progress = self.board.get_clear_animation_progress()
        
        for line_y in self.board.clearing_lines:
            # 从中心向两侧消失的效果
            for x in range(self.board.width):
                distance_from_center = abs(x - self.board.width / 2)
                delay_factor = distance_from_center / (self.board.width / 2)
                
                # 计算当前块的消失进度
                block_progress = max(0, min(1, progress - delay_factor * 0.5))
                
                if block_progress < 1 and self.board.grid[line_y][x]:
                    alpha = int(255 * (1 - block_progress))
                    
                    block_x = BOARD_OFFSET_X + x * BLOCK_SIZE
                    block_y = BOARD_OFFSET_Y + line_y * BLOCK_SIZE
                    
                    # 缩放效果
                    scale = 1 - block_progress * 0.5
                    scaled_size = int(BLOCK_SIZE * scale)
                    offset = (BLOCK_SIZE - scaled_size) // 2
                    
                    color = COLORS.get(self.board.grid[line_y][x], COLORS['WHITE'])
                    
                    # 创建带透明度的表面
                    block_surf = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                    block_surf.fill((*color[:3], alpha))
                    
                    self.screen.blit(block_surf, (block_x + offset, block_y + offset))
    
    def run(self):
        """运行游戏主循环"""
        self.start_game()
        
        while self.running:
            dt = self.clock.tick(FPS)
            
            self.running = self.handle_input()
            self.update(dt)
            self.draw()
        
        # 清理
        self.sound_manager.cleanup()
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = TetrisGame()
    game.run()
