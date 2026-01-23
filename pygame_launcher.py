#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pygame游戏启动器
===============

集成gamecenter目录中所有pygame游戏的统一启动界面。
提供游戏选择、关卡记录和配置管理功能。

Author: kn1ghtc
Version: 1.0.0
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

# 确保UTF-8编码
os.system("chcp 65001 >nul 2>&1")

try:
    import pygame
    from pygame import Surface
except ImportError:
    print("[ERROR] pygame is required. Install with: pip install pygame")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class GameInfo:
    """游戏信息数据类"""
    id: str
    name: str
    description: str
    category: str
    difficulty: str
    module: str
    icon: str = "🎮"
    last_played: Optional[str] = None
    play_count: int = 0
    high_score: int = 0
    
    def get_emoji_icon(self) -> str:
        """根据游戏类型返回emoji图标"""
        icon_map = {
            'chess': '♟️',
            'gomoku': '⚫',
            'militaryChess': '🚩',
            'tankBattle': '🎯',
            'tetris': '🧱',
            'superMario': '🍄',
            'deltaOperation': '🔫',
            'streetBattle': '👊',
            'stickman_game': '🏃',
            'Eco_grassland': '🌿',
            'alien_invasion': '🚀'
        }
        return icon_map.get(self.id, '🎮')


@dataclass
class LauncherConfig:
    """启动器配置"""
    window_width: int = 1200
    window_height: int = 800
    theme_color: tuple = (30, 35, 50)
    accent_color: tuple = (100, 150, 255)
    text_color: tuple = (240, 240, 240)
    font_size: int = 24
    title_font_size: int = 48


class GameProgressManager:
    """游戏进度管理器"""
    
    def __init__(self, save_path: Optional[Path] = None):
        self.save_path = save_path or Path(__file__).parent / "game_progress.json"
        self.progress: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self) -> None:
        """加载保存的进度"""
        if self.save_path.exists():
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    self.progress = json.load(f)
                logger.info(f"Loaded game progress from {self.save_path}")
            except Exception as e:
                logger.warning(f"Failed to load progress: {e}")
                self.progress = {}
    
    def _save(self) -> None:
        """保存进度到文件"""
        try:
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def record_play(self, game_id: str) -> None:
        """记录游戏启动"""
        if game_id not in self.progress:
            self.progress[game_id] = {
                'play_count': 0,
                'high_score': 0,
                'last_played': None
            }
        
        self.progress[game_id]['play_count'] += 1
        self.progress[game_id]['last_played'] = datetime.now().isoformat()
        self._save()
    
    def get_progress(self, game_id: str) -> Dict[str, Any]:
        """获取游戏进度"""
        return self.progress.get(game_id, {
            'play_count': 0,
            'high_score': 0,
            'last_played': None
        })
    
    def update_score(self, game_id: str, score: int) -> None:
        """更新最高分"""
        if game_id not in self.progress:
            self.progress[game_id] = {'play_count': 0, 'high_score': 0, 'last_played': None}
        
        if score > self.progress[game_id].get('high_score', 0):
            self.progress[game_id]['high_score'] = score
            self._save()


class PygameLauncher:
    """Pygame游戏启动器主类"""
    
    # 游戏列表配置
    GAMES: List[Dict[str, str]] = [
        {
            'id': 'chess',
            'name': '中国象棋',
            'description': 'AI对弈中国象棋，支持语音输入',
            'category': 'strategy',
            'difficulty': 'medium',
            'module': 'gamecenter.chess'
        },
        {
            'id': 'gomoku',
            'name': '五子棋',
            'description': '人机对战五子棋',
            'category': 'strategy',
            'difficulty': 'easy',
            'module': 'gamecenter.gomoku'
        },
        {
            'id': 'militaryChess',
            'name': '军旗',
            'description': '双人对战军棋游戏',
            'category': 'strategy',
            'difficulty': 'hard',
            'module': 'gamecenter.militaryChess'
        },
        {
            'id': 'tankBattle',
            'name': '坦克大战',
            'description': '经典坦克对战，支持AI训练',
            'category': 'shooting',
            'difficulty': 'medium',
            'module': 'gamecenter.tankBattle'
        },
        {
            'id': 'tetris',
            'name': '俄罗斯方块',
            'description': '经典益智游戏',
            'category': 'puzzle',
            'difficulty': 'easy',
            'module': 'gamecenter.tetris'
        },
        {
            'id': 'superMario',
            'name': '超级玛丽',
            'description': '30关平台跳跃游戏',
            'category': 'action',
            'difficulty': 'medium',
            'module': 'gamecenter.superMario'
        },
        {
            'id': 'deltaOperation',
            'name': '三角洲行动',
            'description': '12关闯关枪战游戏',
            'category': 'shooting',
            'difficulty': 'hard',
            'module': 'gamecenter.deltaOperation'
        },
        {
            'id': 'streetBattle',
            'name': '街头霸王',
            'description': '2.5D/3D格斗游戏',
            'category': 'action',
            'difficulty': 'hard',
            'module': 'gamecenter.streetBattle'
        },
        {
            'id': 'stickman_game',
            'name': '火柴人格斗',
            'description': '火柴人动作游戏',
            'category': 'action',
            'difficulty': 'easy',
            'module': 'gamecenter.stickman_game'
        },
        {
            'id': 'Eco_grassland',
            'name': '生态草原',
            'description': '生态模拟经营游戏',
            'category': 'simulation',
            'difficulty': 'medium',
            'module': 'gamecenter.Eco_grassland'
        },
        {
            'id': 'alien_invasion',
            'name': '外星人入侵',
            'description': '太空射击游戏',
            'category': 'shooting',
            'difficulty': 'easy',
            'module': 'gamecenter.alien_invasion'
        }
    ]
    
    # 游戏类型emoji和颜色
    CATEGORY_STYLES = {
        'strategy': {'emoji': '🧠', 'color': (100, 180, 100)},
        'shooting': {'emoji': '🎯', 'color': (200, 100, 100)},
        'puzzle': {'emoji': '🧩', 'color': (100, 150, 200)},
        'action': {'emoji': '⚡', 'color': (200, 150, 100)},
        'simulation': {'emoji': '🌍', 'color': (100, 200, 150)}
    }
    
    # 难度颜色
    DIFFICULTY_COLORS = {
        'easy': (100, 200, 100),
        'medium': (200, 180, 100),
        'hard': (200, 100, 100)
    }
    
    def __init__(self, config: Optional[LauncherConfig] = None):
        self.config = config or LauncherConfig()
        self.progress_manager = GameProgressManager()
        self.games = self._init_games()
        self.selected_index = 0
        self.scroll_offset = 0
        self.running = True
        self.filter_category: Optional[str] = None
        
        # Pygame初始化
        pygame.init()
        pygame.display.set_caption("🎮 Pygame游戏中心")
        self.screen = pygame.display.set_mode(
            (self.config.window_width, self.config.window_height)
        )
        self.clock = pygame.time.Clock()
        
        # 字体初始化
        self._init_fonts()
    
    def _init_fonts(self) -> None:
        """初始化字体"""
        # 尝试加载中文字体
        font_candidates = [
            "Microsoft YaHei",
            "SimHei",
            "PingFang SC",
            "Noto Sans CJK SC",
            "WenQuanYi Micro Hei"
        ]
        
        self.font = None
        self.title_font = None
        self.small_font = None
        
        for font_name in font_candidates:
            try:
                self.font = pygame.font.SysFont(font_name, self.config.font_size)
                self.title_font = pygame.font.SysFont(font_name, self.config.title_font_size)
                self.small_font = pygame.font.SysFont(font_name, 18)
                logger.info(f"Using font: {font_name}")
                break
            except Exception:
                continue
        
        if self.font is None:
            self.font = pygame.font.Font(None, self.config.font_size)
            self.title_font = pygame.font.Font(None, self.config.title_font_size)
            self.small_font = pygame.font.Font(None, 18)
    
    def _init_games(self) -> List[GameInfo]:
        """初始化游戏列表"""
        games = []
        for game_data in self.GAMES:
            progress = self.progress_manager.get_progress(game_data['id'])
            game = GameInfo(
                id=game_data['id'],
                name=game_data['name'],
                description=game_data['description'],
                category=game_data['category'],
                difficulty=game_data['difficulty'],
                module=game_data['module'],
                last_played=progress.get('last_played'),
                play_count=progress.get('play_count', 0),
                high_score=progress.get('high_score', 0)
            )
            games.append(game)
        return games
    
    def _get_filtered_games(self) -> List[GameInfo]:
        """获取过滤后的游戏列表"""
        if self.filter_category is None:
            return self.games
        return [g for g in self.games if g.category == self.filter_category]
    
    def _handle_events(self) -> None:
        """处理输入事件"""
        filtered_games = self._get_filtered_games()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.filter_category:
                        self.filter_category = None
                        self.selected_index = 0
                    else:
                        self.running = False
                
                elif event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                    self._adjust_scroll()
                
                elif event.key == pygame.K_DOWN:
                    max_index = len(filtered_games) - 1
                    self.selected_index = min(max_index, self.selected_index + 1)
                    self._adjust_scroll()
                
                elif event.key == pygame.K_RETURN:
                    if filtered_games:
                        self._launch_game(filtered_games[self.selected_index])
                
                # 类别过滤快捷键
                elif event.key == pygame.K_1:
                    self._toggle_filter('strategy')
                elif event.key == pygame.K_2:
                    self._toggle_filter('action')
                elif event.key == pygame.K_3:
                    self._toggle_filter('shooting')
                elif event.key == pygame.K_4:
                    self._toggle_filter('puzzle')
                elif event.key == pygame.K_5:
                    self._toggle_filter('simulation')
                elif event.key == pygame.K_0:
                    self.filter_category = None
                    self.selected_index = 0
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    self._handle_mouse_click(event.pos)
                elif event.button == 4:  # 滚轮上
                    self.scroll_offset = max(0, self.scroll_offset - 40)
                elif event.button == 5:  # 滚轮下
                    self.scroll_offset += 40
    
    def _toggle_filter(self, category: str) -> None:
        """切换类别过滤"""
        if self.filter_category == category:
            self.filter_category = None
        else:
            self.filter_category = category
        self.selected_index = 0
        self.scroll_offset = 0
    
    def _adjust_scroll(self) -> None:
        """调整滚动位置"""
        item_height = 100
        visible_height = self.config.window_height - 200
        selected_y = self.selected_index * item_height
        
        if selected_y < self.scroll_offset:
            self.scroll_offset = selected_y
        elif selected_y + item_height > self.scroll_offset + visible_height:
            self.scroll_offset = selected_y + item_height - visible_height
    
    def _handle_mouse_click(self, pos: tuple) -> None:
        """处理鼠标点击"""
        x, y = pos
        filtered_games = self._get_filtered_games()
        
        # 游戏列表区域
        list_start_y = 150
        item_height = 100
        
        for i, game in enumerate(filtered_games):
            item_y = list_start_y + i * item_height - self.scroll_offset
            if list_start_y <= item_y < self.config.window_height - 50:
                if item_y <= y < item_y + item_height:
                    if self.selected_index == i:
                        self._launch_game(game)
                    else:
                        self.selected_index = i
                    break
    
    def _launch_game(self, game: GameInfo) -> None:
        """启动选中的游戏"""
        logger.info(f"Launching game: {game.name} ({game.module})")
        self.progress_manager.record_play(game.id)
        
        # 最小化当前窗口
        pygame.display.iconify()
        
        try:
            # 使用subprocess启动游戏
            game_path = Path(__file__).parent / game.id / "main.py"
            
            if game_path.exists():
                subprocess.run([sys.executable, str(game_path)], cwd=str(game_path.parent))
            else:
                # 尝试模块导入方式
                module_name = game.module + ".main"
                subprocess.run([
                    sys.executable, "-c",
                    f"from {module_name} import main; main()"
                ], cwd=str(Path(__file__).parent.parent))
            
        except Exception as e:
            logger.error(f"Failed to launch {game.name}: {e}")
        
        # 恢复窗口
        pygame.display.set_mode(
            (self.config.window_width, self.config.window_height)
        )
    
    def _render(self) -> None:
        """渲染界面"""
        self.screen.fill(self.config.theme_color)
        filtered_games = self._get_filtered_games()
        
        # 标题
        title_text = "🎮 Pygame游戏中心"
        title_surface = self.title_font.render(title_text, True, self.config.text_color)
        title_rect = title_surface.get_rect(centerx=self.config.window_width // 2, y=30)
        self.screen.blit(title_surface, title_rect)
        
        # 类别过滤按钮
        self._render_filter_buttons()
        
        # 游戏列表
        list_start_y = 150
        item_height = 100
        list_height = self.config.window_height - list_start_y - 60
        
        for i, game in enumerate(filtered_games):
            item_y = list_start_y + i * item_height - self.scroll_offset
            
            # 只渲染可见区域
            if item_y + item_height < list_start_y or item_y > self.config.window_height - 60:
                continue
            
            is_selected = (i == self.selected_index)
            self._render_game_item(game, 50, item_y, self.config.window_width - 100, item_height - 10, is_selected)
        
        # 底部说明
        help_text = "↑↓ 选择 | Enter 启动 | 1-5 过滤类别 | 0 显示全部 | ESC 退出"
        help_surface = self.small_font.render(help_text, True, (150, 150, 150))
        help_rect = help_surface.get_rect(centerx=self.config.window_width // 2, y=self.config.window_height - 35)
        self.screen.blit(help_surface, help_rect)
        
        pygame.display.flip()
    
    def _render_filter_buttons(self) -> None:
        """渲染类别过滤按钮"""
        categories = [
            ('strategy', '1:策略'),
            ('action', '2:动作'),
            ('shooting', '3:射击'),
            ('puzzle', '4:益智'),
            ('simulation', '5:模拟'),
            (None, '0:全部')
        ]
        
        button_width = 100
        start_x = (self.config.window_width - len(categories) * button_width) // 2
        y = 100
        
        for i, (cat, label) in enumerate(categories):
            x = start_x + i * button_width
            is_active = (self.filter_category == cat) if cat else (self.filter_category is None)
            
            color = self.CATEGORY_STYLES.get(cat, {}).get('color', (100, 100, 100)) if cat else (100, 100, 100)
            if is_active:
                pygame.draw.rect(self.screen, color, (x, y, button_width - 10, 30), border_radius=5)
                text_color = (255, 255, 255)
            else:
                pygame.draw.rect(self.screen, (50, 55, 70), (x, y, button_width - 10, 30), border_radius=5)
                text_color = (180, 180, 180)
            
            text_surface = self.small_font.render(label, True, text_color)
            text_rect = text_surface.get_rect(center=(x + (button_width - 10) // 2, y + 15))
            self.screen.blit(text_surface, text_rect)
    
    def _render_game_item(self, game: GameInfo, x: int, y: int, width: int, height: int, is_selected: bool) -> None:
        """渲染单个游戏项"""
        # 背景
        bg_color = (50, 55, 70) if is_selected else (40, 45, 60)
        border_color = self.config.accent_color if is_selected else (60, 65, 80)
        
        pygame.draw.rect(self.screen, bg_color, (x, y, width, height), border_radius=8)
        pygame.draw.rect(self.screen, border_color, (x, y, width, height), 2, border_radius=8)
        
        # 游戏图标
        icon = game.get_emoji_icon()
        icon_surface = self.title_font.render(icon, True, (255, 255, 255))
        self.screen.blit(icon_surface, (x + 20, y + (height - 48) // 2))
        
        # 游戏名称
        name_surface = self.font.render(game.name, True, self.config.text_color)
        self.screen.blit(name_surface, (x + 90, y + 15))
        
        # 描述
        desc_surface = self.small_font.render(game.description, True, (180, 180, 180))
        self.screen.blit(desc_surface, (x + 90, y + 45))
        
        # 类别标签
        cat_style = self.CATEGORY_STYLES.get(game.category, {'emoji': '🎮', 'color': (100, 100, 100)})
        cat_surface = self.small_font.render(f"{cat_style['emoji']} {game.category}", True, cat_style['color'])
        self.screen.blit(cat_surface, (x + 90, y + 68))
        
        # 难度标签
        diff_color = self.DIFFICULTY_COLORS.get(game.difficulty, (150, 150, 150))
        diff_text = {'easy': '简单', 'medium': '中等', 'hard': '困难'}.get(game.difficulty, game.difficulty)
        diff_surface = self.small_font.render(diff_text, True, diff_color)
        self.screen.blit(diff_surface, (x + 200, y + 68))
        
        # 游玩次数
        if game.play_count > 0:
            play_text = f"已玩 {game.play_count} 次"
            play_surface = self.small_font.render(play_text, True, (120, 150, 180))
            self.screen.blit(play_surface, (x + width - 150, y + 20))
        
        # 选中指示器
        if is_selected:
            indicator = self.font.render("▶", True, self.config.accent_color)
            self.screen.blit(indicator, (x + width - 40, y + (height - 24) // 2))
    
    def run(self) -> None:
        """运行启动器主循环"""
        logger.info("Pygame Launcher started")
        
        while self.running:
            self._handle_events()
            self._render()
            self.clock.tick(60)
        
        pygame.quit()
        logger.info("Pygame Launcher closed")


def main():
    """主入口函数"""
    launcher = PygameLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
