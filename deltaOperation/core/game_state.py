"""
游戏状态管理器 - 统一管理所有游戏场景和状态
"""

import pygame
from typing import Optional, Dict, Any
from gamecenter.deltaOperation import config
from gamecenter.deltaOperation.utils.font import FontManager


class GameState:
    """
    游戏状态管理器
    负责场景切换、状态维护、事件分发
    """
    
    # 游戏状态枚举
    STATE_MAIN_MENU = "main_menu"
    STATE_GAME_PLAY = "gameplay"
    STATE_PAUSE = "pause"
    STATE_MISSION_BRIEFING = "briefing"
    STATE_GAME_OVER = "gameover"
    STATE_VICTORY = "victory"
    
    def __init__(self, screen: pygame.Surface, headless: bool = False, enable_multiplayer: bool = False):
        """
        初始化游戏状态管理器
        
        Args:
            screen: Pygame显示表面
            headless: 是否为无头模式
            enable_multiplayer: 是否启用双人模式
        """
        self.screen = screen
        self.headless = headless
        self.enable_multiplayer = enable_multiplayer
        self.current_state = self.STATE_MAIN_MENU
        self.quit_requested = False
        
        # 游戏数据
        self.player_data: Dict[str, Any] = {
            "health": config.PLAYER_CONFIG["max_health"],
            "score": 0,
            "current_mission": 1,
            "weapons": ["pistol"],
            "inventory": []
        }
        
        # 场景对象(延迟加载)
        self.scenes: Dict[str, Any] = {}
        
        # 字体
        self.font = None
        self._font_manager: Optional[FontManager] = None
        self._init_font()
        
        # 自动加载游戏场景(方便测试)
        self._load_gameplay_scene()
        
        print("[GameState] 初始化完成")
    
    def _init_font(self):
        """初始化字体"""
        try:
            if not pygame.font.get_init():
                pygame.font.init()

            font_path = config.ASSETS_DIR / "fonts" / "military.ttf"
            if font_path.exists():
                self.font = pygame.font.Font(str(font_path), 24)
            else:
                self._font_manager = FontManager()
                self.font = self._font_manager.get_font(24)
        except Exception as e:
            print(f"[GameState] 字体加载失败: {e}")
            self.font = pygame.font.Font(None, 24)
            
    def _load_gameplay_scene(self):
        """加载游戏玩法场景"""
        try:
            from gamecenter.deltaOperation.core.gameplay_scene import GameplayScene
            gameplay = GameplayScene(
                self.screen,
                mission_id=1,
                enable_multiplayer=self.enable_multiplayer
            )
            self.scenes[self.STATE_GAME_PLAY] = gameplay
            # 自动进入游戏(方便测试)
            self.change_state(self.STATE_GAME_PLAY)
            print("[GameState] 游戏场景已加载")
        except Exception as e:
            print(f"[GameState] 游戏场景加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_event(self, event: pygame.event.Event):
        """
        处理Pygame事件
        
        Args:
            event: Pygame事件对象
        """
        # ESC键暂停/恢复
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.current_state == self.STATE_GAME_PLAY:
                    self.change_state(self.STATE_PAUSE)
                elif self.current_state == self.STATE_PAUSE:
                    self.change_state(self.STATE_GAME_PLAY)
                elif self.current_state == self.STATE_MAIN_MENU:
                    self.quit_requested = True
        
        # 将事件传递给当前场景
        current_scene = self.scenes.get(self.current_state)
        if current_scene and hasattr(current_scene, "handle_event"):
            current_scene.handle_event(event)
    
    def update(self, delta_time: float):
        """
        更新游戏逻辑
        
        Args:
            delta_time: 距离上一帧的时间(秒)
        """
        # 更新当前场景
        current_scene = self.scenes.get(self.current_state)
        if current_scene and hasattr(current_scene, "update"):
            current_scene.update(delta_time)
    
    def render(self):
        """渲染当前场景"""
        # 清屏
        self.screen.fill((0, 0, 0))
        
        # 渲染当前场景
        current_scene = self.scenes.get(self.current_state)
        if current_scene and hasattr(current_scene, "render"):
            current_scene.render(self.screen)
        else:
            # 默认渲染占位文本
            self._render_placeholder()
    
    def _render_placeholder(self):
        """渲染占位界面(开发中)"""
        text_lines = [
            "Delta Force: Shadow Operations",
            "",
            f"当前状态: {self.current_state}",
            "",
            "按 ESC 退出",
            "",
            "[系统正在开发中...]"
        ]
        
        y_offset = 100
        for line in text_lines:
            if line:
                text_surf = self.font.render(line, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=(config.WINDOW_WIDTH // 2, y_offset))
                self.screen.blit(text_surf, text_rect)
            y_offset += 40
    
    def change_state(self, new_state: str):
        """
        切换游戏状态
        
        Args:
            new_state: 新状态名称
        """
        print(f"[GameState] 状态切换: {self.current_state} -> {new_state}")
        
        # 离开当前状态
        current_scene = self.scenes.get(self.current_state)
        if current_scene and hasattr(current_scene, "on_exit"):
            current_scene.on_exit()
        
        # 切换状态
        self.current_state = new_state
        
        # 进入新状态
        new_scene = self.scenes.get(new_state)
        if new_scene and hasattr(new_scene, "on_enter"):
            new_scene.on_enter()
    
    def should_quit(self) -> bool:
        """检查是否请求退出"""
        return self.quit_requested
    
    def get_player_data(self) -> Dict[str, Any]:
        """获取玩家数据"""
        return self.player_data.copy()
    
    def set_player_data(self, data: Dict[str, Any]):
        """设置玩家数据"""
        self.player_data.update(data)
