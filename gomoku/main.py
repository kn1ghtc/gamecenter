"""五子棋游戏主程序
Gomoku (Five in a Row) - Main Entry Point

现代化五子棋游戏，包含智能AI、优雅UI、完整游戏功能。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import pygame

# 确保UTF-8编码（Windows环境）
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 绝对导入
from gamecenter.gomoku.ai_engine_manager import create_ai_engine
from gamecenter.gomoku.config.constants import (
    WINDOW_DEFAULT_HEIGHT, WINDOW_DEFAULT_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH, MAX_UNDO_COUNT, SETTINGS_FILE, AI_ENGINE_TYPE, AI_DEFAULT_DIFFICULTY
)
from gamecenter.gomoku.font_manager import get_font_manager
from gamecenter.gomoku.game_logic import Board, GameManager, GameState, Player
from gamecenter.gomoku.ui_manager import UIManager


class GomokuGame:
    """五子棋游戏主类"""
    
    def __init__(self):
        """初始化游戏"""
        pygame.init()
        
        # 加载设置
        self.settings = self._load_settings()
        
        # 创建窗口
        width = self.settings['display']['window_width']
        height = self.settings['display']['window_height']
        self.screen = pygame.display.set_mode(
            (width, height), 
            pygame.RESIZABLE
        )
        pygame.display.set_caption("五子棋 Gomoku - Modern Edition")
        
        # 创建游戏对象
        self.game_manager = GameManager(max_undo=MAX_UNDO_COUNT)
        self.ui_manager = UIManager(width, height)
        
        # AI设置（使用AI引擎管理器）
        difficulty_name = self.settings['game'].get('ai_difficulty', AI_DEFAULT_DIFFICULTY)
        engine_type = self.settings['game'].get('ai_engine_type', AI_ENGINE_TYPE)
        self.ai_controller = create_ai_engine(engine_type, difficulty_name, time_limit=5.0)
        self.ai_thinking = False
        self.ai_player = Player.WHITE  # AI默认执白
        self.game_mode = 'pvc'  # 默认人机对战 'pvp'双人 或 'pvc'人机
        
        # 时钟
        self.clock = pygame.time.Clock()
        self.running = True
        self.fullscreen = False
    
    def _load_settings(self) -> dict:
        """加载设置"""
        settings_path = Path(__file__).parent / SETTINGS_FILE
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            # 返回默认设置
            return {
                'game': {
                    'ai_difficulty': AI_DEFAULT_DIFFICULTY,
                    'ai_engine_type': AI_ENGINE_TYPE,
                    'max_undo_count': 3
                },
                'display': {
                    'window_width': WINDOW_DEFAULT_WIDTH,
                    'window_height': WINDOW_DEFAULT_HEIGHT,
                    'fullscreen': False
                },
                'audio': {'sound_enabled': True, 'volume': 0.7},
                'ui': {
                    'show_coordinates': False,
                    'hover_preview': True,
                    'ui_panel_width': 300  # 添加缺失的参数
                }
            }
    
    def _save_settings(self) -> None:
        """保存设置"""
        settings_path = Path(__file__).parent / SETTINGS_FILE
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def handle_events(self) -> None:
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.VIDEORESIZE:
                # 窗口大小调整
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.ui_manager.resize(event.w, event.h)
                self.settings['display']['window_width'] = event.w
                self.settings['display']['window_height'] = event.h
            
            elif event.type == pygame.KEYDOWN:
                self._handle_key_press(event.key)
            
            elif event.type == pygame.MOUSEMOTION:
                self.ui_manager.handle_mouse_motion(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self._handle_mouse_click(event.pos)
            
            # 按钮事件处理
            for button_name, button in self.ui_manager.buttons.items():
                if button.handle_event(event):
                    self._handle_button_click(button_name)
    
    def _handle_key_press(self, key: int) -> None:
        """处理按键"""
        if key == pygame.K_ESCAPE:
            self.running = False
        
        elif key == pygame.K_F11:
            # 全屏切换
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                width = self.settings['display']['window_width']
                height = self.settings['display']['window_height']
                self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            
            # 更新布局
            info = pygame.display.Info()
            self.ui_manager.resize(info.current_w, info.current_h)
        
        elif key == pygame.K_u:
            # 悔棋
            self._handle_undo()
        
        elif key == pygame.K_r:
            # 重新开始
            self._handle_new_game()
        
        elif key == pygame.K_F4:
            # 字体调试
            font_mgr = get_font_manager()
            font_mgr.toggle_debug()
    
    def _handle_mouse_click(self, pos: tuple) -> None:
        """处理鼠标点击"""
        if self.ai_thinking:
            return  # AI思考中，禁止落子
        
        board_pos = self.ui_manager.handle_click(pos)
        if board_pos:
            row, col = board_pos
            self._place_stone(row, col)
    
    def _place_stone(self, row: int, col: int) -> None:
        """放置棋子"""
        board = self.game_manager.board
        
        # 检查游戏状态
        if board.state != GameState.ONGOING:
            return
        
        # 落子
        if self.game_manager.place_stone(row, col):
            # 添加动画
            self.ui_manager.add_stone_animation(row, col)
            
            # 检查是否需要AI行动
            if (self.game_mode == 'pvc' and 
                board.state == GameState.ONGOING and
                board.current_player == self.ai_player):
                self.ai_thinking = True
    
    def _handle_button_click(self, button_name: str) -> None:
        """处理按钮点击"""
        if button_name == 'new_game':
            self._handle_new_game()
        
        elif button_name == 'undo':
            self._handle_undo()
        
        elif button_name == 'difficulty':
            self._cycle_difficulty()
        
        elif button_name == 'mode':
            self._toggle_game_mode()
        
        elif button_name == 'save':
            self._save_game()
    
    def _handle_new_game(self) -> None:
        """开始新游戏"""
        self.game_manager.reset()
        self.ai_thinking = False
        self.ai_controller.clear_cache()  # 清空缓存
    
    def _handle_undo(self) -> None:
        """悔棋"""
        if not self.game_manager.can_undo():
            return
        
        if self.game_mode == 'pvc':
            # 人机对战：悔棋两步
            self.game_manager.undo(count=2)
        else:
            # 双人对战：悔棋一步
            self.game_manager.undo(count=1)
        
        self.ai_thinking = False
    
    def _cycle_difficulty(self) -> None:
        """切换难度"""
        difficulties = ['easy', 'medium', 'hard']
        current = self.settings['game']['ai_difficulty']
        current_idx = difficulties.index(current) if current in difficulties else 1
        next_idx = (current_idx + 1) % len(difficulties)
        new_difficulty = difficulties[next_idx]
        
        self.settings['game']['ai_difficulty'] = new_difficulty
        self.ai_controller.set_difficulty(new_difficulty)
        
        # 更新按钮文字
        difficulty_names = {'easy': '简单', 'medium': '中等', 'hard': '困难'}
        depth_info = {'easy': 'D3', 'medium': 'D5', 'hard': 'D7'}
        self.ui_manager.buttons['difficulty'].text = f"AI难度: {difficulty_names[new_difficulty]} ({depth_info[new_difficulty]})"
    
    def _toggle_game_mode(self) -> None:
        """切换游戏模式（人机/双人）"""
        if self.game_mode == 'pvp':
            self.game_mode = 'pvc'
            mode_text = "人机对战"
        else:
            self.game_mode = 'pvp'
            mode_text = "双人对战"
        
        # 更新UI（如果有模式按钮）
        if 'mode' in self.ui_manager.buttons:
            self.ui_manager.buttons['mode'].text = f"模式: {mode_text}"
    
    def _save_game(self) -> None:
        """保存游戏"""
        save_dir = Path(__file__).parent / "saves"
        save_dir.mkdir(exist_ok=True)
        
        filename = f"gomoku_save_{len(self.game_manager.board.history)}.json"
        filepath = save_dir / filename
        
        try:
            self.game_manager.board.save_to_file(str(filepath))
            print(f"游戏已保存: {filepath}")
        except Exception as e:
            print(f"保存失败: {e}")
    
    def update(self) -> None:
        """更新游戏逻辑"""
        dt = self.clock.get_time()
        
        # 更新UI动画
        self.ui_manager.update(dt)
        
        # AI思考
        if self.ai_thinking:
            board = self.game_manager.board
            best_move = self.ai_controller.find_best_move(board, self.ai_player)
            
            if best_move:
                row, col = best_move
                self._place_stone(row, col)
                
                # 显示AI统计信息
                stats = self.ai_controller.get_stats()
                engine_name = self.ai_controller.get_engine_name()
                print(f"[{engine_name}] AI搜索: ", end="")
                if 'nodes_searched' in stats:
                    print(f"{stats['nodes_searched']} 节点, ", end="")
                if 'search_time' in stats:
                    print(f"{stats['search_time']:.3f}秒, ", end="")
                if 'nodes_per_second' in stats:
                    print(f"{stats['nodes_per_second']:.0f} nps", end="")
                if 'tt_hit_rate' in stats:
                    print(f", TT命中率: {stats['tt_hit_rate']:.1%}", end="")
                print()  # 换行
            
            self.ai_thinking = False
        
        # 更新悔棋按钮状态
        self.ui_manager.buttons['undo'].enabled = self.game_manager.can_undo()
    
    def draw(self) -> None:
        """绘制画面"""
        self.ui_manager.draw(self.screen, self.game_manager.board)
        
        # 绘制字体调试信息
        font_mgr = get_font_manager()
        if font_mgr.debug_mode:
            debug_info = font_mgr.get_debug_info()
            debug_surf = font_mgr.render_text(debug_info, 12, (255, 255, 0))
            self.screen.blit(debug_surf, (10, 10))
        
        pygame.display.flip()
    
    def run(self) -> None:
        """主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS
        
        # 退出时保存设置
        self._save_settings()
        pygame.quit()


def main() -> None:
    """主函数"""
    print("🎮 启动五子棋游戏...")
    print("=" * 50)
    print("操作说明:")
    print("  鼠标左键: 落子")
    print("  U键: 悔棋")
    print("  R键: 重新开始")
    print("  F11: 全屏切换")
    print("  ESC: 退出游戏")
    print("  F4: 字体调试信息")
    print("=" * 50)
    
    try:
        game = GomokuGame()
        game.run()
    except Exception as e:
        print(f"❌ 游戏运行错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


def run_game() -> None:
    """包导入接口"""
    main()


if __name__ == "__main__":
    main()
