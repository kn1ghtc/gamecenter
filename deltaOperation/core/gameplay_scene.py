"""游戏玩法场景 - 实际游戏逻辑"""
import pygame
from typing import Optional

from gamecenter.deltaOperation import config
from gamecenter.deltaOperation.core import (
    Player, LevelManager, Mission, PhysicsEngine
)
from gamecenter.deltaOperation.utils import Camera
from gamecenter.deltaOperation.utils.font import FontManager
from gamecenter.deltaOperation.ui.help_overlay import HelpOverlay
from gamecenter.deltaOperation.core.multiplayer import MultiplayerManager, MultiplayerConfig
from gamecenter.deltaOperation.utils.enhanced_visuals import get_particle_system


class GameplayScene:
    """游戏玩法场景
    
    职责:
    - 整合所有游戏系统
    - 处理游戏输入
    - 更新游戏逻辑
    - 渲染游戏画面
    """
    
    def __init__(self, screen: pygame.Surface, mission_id: int = 1, enable_multiplayer: bool = False):
        """初始化游戏场景
        
        Args:
            screen: 显示表面
            mission_id: 任务ID (1-12)
            enable_multiplayer: 是否启用双人模式
        """
        self.screen = screen
        self.mission_id = mission_id
        self.enable_multiplayer = enable_multiplayer
        
        # 核心系统
        self.physics_engine = PhysicsEngine()
        self.camera = Camera(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.particle_system = get_particle_system()  # 🆕 粒子系统
        
        # 游戏对象
        self.mission: Optional[Mission] = None
        self.level: Optional[LevelManager] = None
        self.player: Optional[Player] = None
        self.player2: Optional[Player] = None  # Player 2 instance
        self.multiplayer: Optional[MultiplayerManager] = None  # Multiplayer manager
        self.hud = None
        self.help_overlay = None  # 帮助覆盖层
        
        # 状态
        self.paused = False
        self.mission_complete = False
        self.mission_failed = False

        if not pygame.font.get_init():
            pygame.font.init()
        self._font_manager = FontManager()
        self._fallback_font = self._font_manager.get_font(24)
        
        print(f"[GameplayScene] 创建场景(任务 #{mission_id})")
        
    def on_enter(self):
        """进入场景时初始化"""
        print(f"\n[GameplayScene] 加载任务 #{self.mission_id}...")
        
        # 创建任务
        self.mission = Mission(mission_id=self.mission_id)
        
        # 创建关卡
        self.level = LevelManager(level_id=self.mission.config.level_id)
        self.level._create_default_level()  # 使用默认地图
        self.level.spawn_enemies()
        
        # 创建玩家
        self.player = Player(*self.level.player_spawn)
        
        # 装备武器
        from gamecenter.deltaOperation.core.weapon import WeaponFactory
        pistol = WeaponFactory.create_pistol()
        rifle = WeaponFactory.create_rifle()
        self.player.add_weapon(pistol)
        self.player.add_weapon(rifle)
        
        # 初始化双人模式（如果启用）
        if self.enable_multiplayer:
            mp_config = MultiplayerConfig(
                mode="shared",  # Center-locked camera
                max_distance=600.0,  # Max 600px separation
                resurrection_enabled=True,
                resurrection_time=3.0
            )
            self.multiplayer = MultiplayerManager(mp_config)
            
            # Spawn Player 2 near Player 1
            spawn_x = self.level.player_spawn[0] + 50
            spawn_y = self.level.player_spawn[1]
            self.player2 = self.multiplayer.initialize_players(self.player, spawn_x, spawn_y)
            
            print(f"  [✓] 双人模式已启用 (P1: {self.player.position.x:.0f},{self.player.position.y:.0f} | P2: {self.player2.position.x:.0f},{self.player2.position.y:.0f})")
        
        # 设置相机边界
        self.camera.set_bounds(
            0, 0,
            self.level.level_bounds.width,
            self.level.level_bounds.height
        )
        
        # 尝试加载HUD
        try:
            from gamecenter.deltaOperation.ui import HUD
            self.hud = HUD(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            print("  [✓] HUD系统已加载")
            
            # Connect player callbacks to HUD
            self.player.on_weapon_switch_callback = self.hud.on_weapon_switch
            self.player.on_reload_start_callback = self.hud.on_reload_start
        except Exception as e:
            print(f"  [!] HUD加载失败: {e}")
            self.hud = None
        
        # 创建帮助覆盖层
        self.help_overlay = HelpOverlay(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.help_overlay.set_level(self.mission_id)
        
        # 开始任务
        self.mission.start_mission()
        
        print(f"  [+] 任务'{self.mission.config.name}'已开始")
        print(f"    难度: {self.mission.config.difficulty}")
        print(f"    目标: {len(self.mission.config.objectives)}个")
        print(f"    敌人: {len(self.level.get_alive_enemies())}")
        
    def on_exit(self):
        """退出场景时清理"""
        print("[GameplayScene] 退出场景")
        
    def handle_event(self, event: pygame.event.Event):
        """处理事件
        
        Args:
            event: Pygame事件
        """
        if event.type == pygame.KEYDOWN:
            # 帮助系统 - H键
            if event.key == pygame.K_h:
                if self.help_overlay:
                    self.help_overlay.toggle()
            
            # 调试快捷键
            elif event.key == pygame.K_F1 and self.hud:
                self.hud.toggle_minimap()
            elif event.key == pygame.K_F2:
                self.camera.set_zoom(2.0)
            elif event.key == pygame.K_F3:
                self.camera.set_zoom(1.0)
            elif event.key == pygame.K_F4:
                self.camera.shake(20, 0.5)
                
    def update(self, delta_time: float):
        """更新游戏逻辑
        
        Args:
            delta_time: 距离上一帧的时间(秒)
        """
        if self.paused or not self.player or not self.level or not self.mission:
            return
            
        # 处理玩家输入
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # 更新玩家
        self.player.update(delta_time, self.physics_engine, self.level)
        
        # Player 2 update (if multiplayer enabled)
        if self.enable_multiplayer and self.player2:
            self.player2.handle_input(keys)
            self.player2.update(delta_time, self.physics_engine, self.level)
            
            # Update Player 2 weapon bullets
            if self.player2.current_weapon:
                self.player2.current_weapon.update_bullets(delta_time, self.physics_engine, self.level.tilemap)
            
            # Update multiplayer system
            self.multiplayer.update(delta_time)
        
        # 更新武器子弹
        if self.player.current_weapon:
            self.player.current_weapon.update_bullets(delta_time, self.physics_engine, self.level.tilemap)
        
        # 更新关卡(包括敌人AI) - pass both players for targeting
        players_list = [self.player]
        if self.enable_multiplayer and self.player2:
            players_list.append(self.player2)
        self.level.update(delta_time, self.physics_engine, players_list)
        
        # 更新任务 - consider both players for objectives
        self.mission.update(delta_time, self.level, self.player)
        
        # 🆕 更新粒子系统
        self.particle_system.update(delta_time)
        
        # 更新相机跟随 - dual-player mode uses multiplayer manager
        if self.enable_multiplayer and self.multiplayer:
            self.multiplayer.update_camera(self.camera)
        else:
            self.camera.follow(
                self.player.position.x,
                self.player.position.y,
                self.player.velocity.x / 100,  # 归一化速度用于前瞻
                self.player.velocity.y / 100
            )
        self.camera.update(delta_time)
        
        # 更新HUD
        if self.hud:
            self.hud.update(delta_time)
            
        # 检查任务状态 - multiplayer failure requires both players dead
        mission_failed = False
        if self.enable_multiplayer and self.multiplayer:
            mission_failed = self.multiplayer.both_players_dead()
        else:
            mission_failed = self.player.health <= 0
        
        if not self.mission_complete and self.mission.is_completed():
            self.mission_complete = True
            if self.hud:
                self.hud.show_mission_completed()
            print(f"\n✓✓✓ 任务完成! ✓✓✓")
            
        elif not self.mission_failed and (self.mission.is_failed() or mission_failed):
            self.mission_failed = True
            if self.hud:
                self.hud.show_mission_failed(getattr(self.mission, 'failure_reason', ''))
            print(f"\n✗✗✗ 任务失败! ✗✗✗")
            
    def render(self, screen: pygame.Surface):
        """渲染游戏画面
        
        Args:
            screen: 显示表面
        """
        # 清屏
        screen.fill((40, 40, 50))  # 深灰色背景
        
        if not self.level or not self.player:
            return
            
        # 渲染关卡(地图 + 敌人)
        self.level.render(screen)
        
        # 渲染玩家
        self.player.render(screen)
        

        # 🆕 渲染粒子效果（在HUD之前）
        camera_offset = (self.camera.x, self.camera.y)
        self.particle_system.render(screen, camera_offset)
        
        # Render Player 2 (if multiplayer enabled)
        if self.enable_multiplayer and self.player2:
            self.player2.render(screen)
            
            # Render Player 2 bullets
            if self.player2.current_weapon:
                self.player2.current_weapon.render_bullets(screen)
            
            # Render resurrection progress indicator
            progress = self.multiplayer.get_resurrection_progress()
            if progress is not None:
                self._render_resurrection_indicator(screen, progress)
        
        # 渲染子弹
        if self.player.current_weapon:
            self.player.current_weapon.render_bullets(screen)
        
        # 渲染HUD
        if self.hud:
            try:
                self.hud.render(screen, self.player, self.mission, self.level)
            except Exception as e:
                # HUD渲染失败不影响游戏,显示基础信息
                self._render_basic_info(screen)
        else:
            self._render_basic_info(screen)
            
        # 任务完成/失败遮罩
        if self.mission_complete:
            self._render_mission_complete(screen)
        elif self.mission_failed:
            self._render_mission_failed(screen)
        
        # 帮助覆盖层（最后渲染，覆盖在所有内容之上）
        if self.help_overlay:
            self.help_overlay.render(screen)
            
    def _render_basic_info(self, screen: pygame.Surface):
        """渲染基础信息(HUD不可用时)
        
        Args:
            screen: 显示表面
        """
        font = self._fallback_font
        
        # 血量
        health_text = font.render(
            f"HP: {int(self.player.health)}/{self.player.max_health}", 
            True, (255, 255, 255)
        )
        screen.blit(health_text, (20, 20))
        
        # 弹药
        weapon = getattr(self.player, "current_weapon", None) or getattr(self.player, "weapon", None)
        if weapon:
            ammo_text = font.render(
                f"{weapon.name}: {getattr(weapon, 'current_ammo', getattr(weapon, 'ammo_in_mag', 0))}/{getattr(weapon, 'reserve_ammo', 0)}",
                True, (255, 255, 255)
            )
            screen.blit(ammo_text, (20, 50))
            
        # 任务信息
        if self.mission:
            mission_text = font.render(
                f"任务: {self.mission.config.name}", 
                True, (255, 255, 0)
            )
            screen.blit(mission_text, (20, 80))
            
            # 击杀数
            kill_text = font.render(
                f"击杀: {self.mission.enemies_killed}", 
                True, (255, 255, 255)
            )
            screen.blit(kill_text, (20, 110))
            
            # 敌人剩余
            alive = len(self.level.get_alive_enemies()) if self.level else 0
            enemy_text = font.render(
                f"敌人: {alive}", 
                True, (255, 100, 100)
            )
            screen.blit(enemy_text, (20, 140))
    
    def _render_resurrection_indicator(self, screen: pygame.Surface, progress: float):
        """Render resurrection progress bar.
        
        Args:
            screen: Display surface
            progress: Progress ratio (0.0-1.0)
        """
        bar_width = 200
        bar_height = 20
        x = (config.WINDOW_WIDTH - bar_width) // 2
        y = config.WINDOW_HEIGHT - 100
        
        # Background
        bg_rect = pygame.Rect(x, y, bar_width, bar_height)
        pygame.draw.rect(screen, (60, 60, 60), bg_rect, border_radius=5)
        
        # Progress fill
        fill_width = int(bar_width * progress)
        fill_rect = pygame.Rect(x, y, fill_width, bar_height)
        pygame.draw.rect(screen, (0, 220, 120), fill_rect, border_radius=5)
        
        # Border
        pygame.draw.rect(screen, (200, 200, 200), bg_rect, 2, border_radius=5)
        
        # Text
        text = self._fallback_font.render(f"复活中... {int(progress * 100)}%", True, (255, 255, 255))
        text_x = (config.WINDOW_WIDTH - text.get_width()) // 2
        text_y = y - 30
        screen.blit(text, (text_x, text_y))
            
    def _render_mission_complete(self, screen: pygame.Surface):
        """渲染任务完成遮罩
        
        Args:
            screen: 显示表面
        """
        # 半透明遮罩
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 100, 0))
        screen.blit(overlay, (0, 0))
        
        # 文字
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 36)
        
        title = font_large.render("MISSION COMPLETE", True, (255, 255, 255))
        info = font_medium.render(
            f"Kills: {self.mission.enemies_killed}", 
            True, (200, 200, 200)
        )
        hint = font_medium.render("Press ESC to continue", True, (150, 150, 150))
        
        y_offset = config.WINDOW_HEIGHT // 2 - 100
        screen.blit(title, (config.WINDOW_WIDTH // 2 - title.get_width() // 2, y_offset))
        screen.blit(info, (config.WINDOW_WIDTH // 2 - info.get_width() // 2, y_offset + 80))
        screen.blit(hint, (config.WINDOW_WIDTH // 2 - hint.get_width() // 2, y_offset + 130))
        
    def _render_mission_failed(self, screen: pygame.Surface):
        """渲染任务失败遮罩
        
        Args:
            screen: 显示表面
        """
        # 半透明遮罩
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((100, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # 文字
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 36)
        
        title = font_large.render("MISSION FAILED", True, (255, 255, 255))
        hint = font_medium.render("Press ESC to exit", True, (150, 150, 150))
        
        y_offset = config.WINDOW_HEIGHT // 2 - 50
        screen.blit(title, (config.WINDOW_WIDTH // 2 - title.get_width() // 2, y_offset))
        screen.blit(hint, (config.WINDOW_WIDTH // 2 - hint.get_width() // 2, y_offset + 80))
        
    def is_mission_complete(self) -> bool:
        """检查任务是否完成"""
        return self.mission_complete
        
    def is_mission_failed(self) -> bool:
        """检查任务是否失败"""
        return self.mission_failed
