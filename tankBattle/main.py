"""
Tank Battle Game - 增强版本
=========================
面向对象的坦克大战游戏 - 包含多种新功能

Controls:
- ↑/↓: Move forward/backward
- ←/→: Rotate left/right
- Space: Fire
- Q/E: Switch bullet type
- P: Pause
- H: Help
- U: Toggle UI
- R: Reset level
- +/-: Adjust UI transparency

新特性:
- 关卡选择和存档系统
- 多种子弹类型切换
- 特殊围墙和增强效果
- 透明UI系统
- 一键重置地图
- 玩家安全区域

Run: python main.py
Requires: pygame (pip install pygame)
"""
import pygame
import sys
import os
import random
import argparse
import math

from config import GAME_CONFIG, SOUND_CONFIG, WIN_CONDITION, PLAYER_CONFIG, AI_CONFIG, get_chinese_font
from tank_system import PlayerTank, EnemyTank
from bullet_system import BulletManager
from environment import EnvironmentManager
from level_manager import LevelManager
from save_system import SaveSystem, LevelSelector, SaveMenu
from special_walls import SpecialEffectManager
from ui_manager import UIManager

# AI系统集成
try:
    from ai.integration import get_ai_manager, get_performance_optimizer
    AI_MANAGER_AVAILABLE = True
    print("✓ AI管理器可用")
except ImportError as e:
    AI_MANAGER_AVAILABLE = False
    print(f"✗ AI管理器不可用: {e}")
    def get_ai_manager():
        return None
    def get_performance_optimizer():
        return None

class GameManager:
    """游戏管理器 - 主要的游戏逻辑控制"""
    def __init__(self, smoke_test: bool = False, smoke_test_frames: int = 0):
        # 初始化Pygame
        pygame.init()

        # 创建游戏窗口
        self.screen = pygame.display.set_mode((GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']))
        pygame.display.set_caption(GAME_CONFIG['TITLE'])
        self.clock = pygame.time.Clock()

        # 字体 - 使用改进的中文字体配置
        try:
            self.font = get_chinese_font(24)
            self.big_font = get_chinese_font(32)
            print(f"✓ 主游戏字体初始化成功")
        except Exception as e:
            print(f"⚠ 主游戏字体初始化失败: {e}")
            # 最终降级方案
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 32)

        # 游戏状态
        self.running = True
        self.paused = False
        self.game_state = 'menu'  # 'menu', 'level_select', 'playing', 'level_complete', 'game_over', 'victory', 'help'
        self.show_help = False

        # 测试模式
        self.smoke_test = smoke_test
        self.smoke_test_frames = smoke_test_frames
        self._frames_executed = 0

        # 游戏数据
        self.score = 0
        self.current_level = 1
        self.start_time = pygame.time.get_ticks()

        # 管理器
        self.bullet_manager = BulletManager()
        self.environment_manager = EnvironmentManager()
        self.level_manager = LevelManager()
        self.save_system = SaveSystem()
        self.special_effect_manager = SpecialEffectManager()
        self.ui_manager = UIManager()

        # AI系统管理器
        self.ai_manager = None
        self.performance_optimizer = None
        self._initialize_ai_system()

        # 菜单系统
        self.level_selector = LevelSelector(self.save_system)
        self.save_menu = SaveMenu(self.save_system)

        # 游戏对象
        self.player = None
        self.enemies = []
        self.special_walls = []

        # 音效
        self.load_sounds()

        # 预生成所有关卡
        self.level_manager.prepare_all_levels()

        # 统计数据
        self.stats = {
            'shots_fired': 0,
            'enemies_destroyed': 0,
            'walls_destroyed': 0,
            # 自测关键指标
            'barrier_blocked_shots': 0,          # 所有被隔离墙拦截的子弹
            'enemy_shots_into_barrier': 0,       # 敌方子弹打到隔离墙（非穿甲）
            'player_shots_into_barrier': 0,      # 玩家子弹打到隔离墙（非穿甲）
            'edge_spawn_unsafe_enemies': 0,      # 过近边缘生成的敌人数
            'total_enemies_loaded': 0,
            'edge_unsafe_positions': [],         # 记录不安全出生点坐标
        }

        # Smoke-test: 自动进入关卡进行无交互自测
        if self.smoke_test:
            # 强制重生成所有地图，避免沿用旧.map导致规则未更新
            self.regenerate_all_maps()
            self.current_level = 1
            self.load_level(self.current_level)
            self.game_state = 'playing'

    def _initialize_ai_system(self):
        """初始化AI系统"""
        if AI_MANAGER_AVAILABLE and AI_CONFIG['ENABLED']:
            try:
                self.ai_manager = get_ai_manager()
                self.performance_optimizer = get_performance_optimizer()
                if self.ai_manager:
                    print("✓ AI系统初始化成功")
                    # 获取系统状态
                    status = self.ai_manager.get_system_status()
                    print(f"  {status['summary']}")
                else:
                    print("○ AI管理器创建失败，使用基础AI")
            except Exception as e:
                print(f"⚠ AI系统初始化失败: {e}")
                self.ai_manager = None
                self.performance_optimizer = None
        else:
            print("○ AI系统被禁用或不可用")

    def load_sounds(self):
        """加载音效"""
        try:
            self.explosion_sound = pygame.mixer.Sound(SOUND_CONFIG['EXPLOSION'])
        except Exception:
            self.explosion_sound = None

        try:
            self.shoot_sound = pygame.mixer.Sound(SOUND_CONFIG['SHOOT'])
        except Exception:
            self.shoot_sound = None

    def load_level(self, level):
        """加载关卡"""
        # 清理当前状态
        self.bullet_manager.clear()
        self.environment_manager.clear()
        self.enemies.clear()
        self.special_walls.clear()
        self.special_effect_manager.clear_all_effects(self.player if self.player else None)

        # 准备关卡数据
        level_objects = self.level_manager.prepare_level(level)

        # 创建玩家
        if level_objects['player_pos']:
            pos = level_objects['player_pos']
            # level_data 中的玩家坐标为中心，需要转换为左上角
            self.player = PlayerTank(
                pos['x'] - PLAYER_CONFIG['SIZE'][0] // 2,
                pos['y'] - PLAYER_CONFIG['SIZE'][1] // 2
            )
        else:
            self.player = PlayerTank(100, GAME_CONFIG['HEIGHT'] // 2)

    # 设置环境对象
        for wall in level_objects['walls']:
            self.environment_manager.add_wall(wall)

        # 保存特殊围墙引用
        self.special_walls = level_objects.get('special_walls', [])

        # 传递中央隔离墙通道给环境管理器
        if 'barrier_passages' in level_objects:
            self.environment_manager.set_barrier_passages(level_objects['barrier_passages'])

        if level_objects['player_base']:
            self.environment_manager.set_player_base(level_objects['player_base'])

        if level_objects['enemy_base']:
            self.environment_manager.set_enemy_base(level_objects['enemy_base'])

        # 设置敌人
        self.enemies = level_objects['enemies']
        # 统计生成质量（是否靠边）
        self.stats['total_enemies_loaded'] = len(self.enemies)
        edge_margin_px = 24
        for e in self.enemies:
            if (e.rect.left <= edge_margin_px or e.rect.top <= edge_margin_px or
                e.rect.right >= GAME_CONFIG['WIDTH'] - edge_margin_px or
                e.rect.bottom >= GAME_CONFIG['HEIGHT'] - edge_margin_px):
                self.stats['edge_spawn_unsafe_enemies'] += 1
                if self.smoke_test:
                    self.stats['edge_unsafe_positions'].append(
                        (e.rect.left, e.rect.top, e.rect.right, e.rect.bottom)
                    )

        # 重置时间
        self.start_time = pygame.time.get_ticks()
        self.game_state = 'playing'

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_state == 'menu':
                    self.handle_menu_events(event)
                elif self.game_state == 'level_select':
                    self.handle_level_select_events(event)
                elif self.game_state == 'playing':
                    self.handle_playing_events(event)
                elif self.game_state in ['level_complete', 'game_over', 'victory']:
                    self.handle_end_game_events(event)
                elif self.game_state == 'help':
                    if event.key == pygame.K_h or event.key == pygame.K_ESCAPE:
                        self.game_state = 'playing'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == 'level_select':
                    selected_level = self.level_selector.handle_event(event, GAME_CONFIG)
                    if selected_level:
                        self.current_level = selected_level
                        self.load_level(self.current_level)
                        self.game_state = 'playing'

    def handle_menu_events(self, event):
        """处理主菜单事件"""
        if event.key == pygame.K_RETURN:
            self.game_state = 'level_select'
        elif event.key == pygame.K_l:
            # 加载存档菜单
            self.save_menu.mode = 'load'
            self.save_menu.refresh_saves()
            self.game_state = 'load_game'
        elif event.key == pygame.K_r:
            # 重新生成所有地图
            self.regenerate_all_maps()
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def handle_level_select_events(self, event):
        """处理关卡选择事件"""
        selected_level = self.level_selector.handle_event(event, GAME_CONFIG)
        if selected_level:
            self.current_level = selected_level
            self.load_level(self.current_level)
            self.game_state = 'playing'
        elif event.key == pygame.K_ESCAPE:
            self.game_state = 'menu'

    def handle_playing_events(self, event):
        """处理游戏中的事件"""
        if event.key == pygame.K_p:
            self.paused = not self.paused
        elif event.key == pygame.K_h:
            self.game_state = 'help'
        elif event.key == pygame.K_u:
            self.ui_manager.toggle_ui_visibility()
        elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
            self.ui_manager.adjust_transparency(0.1)
        elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
            self.ui_manager.adjust_transparency(-0.1)
        elif event.key == pygame.K_q and not self.paused:
            self.switch_bullet_type(-1)
        elif event.key == pygame.K_e and not self.paused:
            self.switch_bullet_type(1)
        elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
            # Ctrl+S 快速保存
            self.quick_save()
        elif event.key == pygame.K_ESCAPE:
            self.game_state = 'menu'

    def handle_end_game_events(self, event):
        """处理游戏结束事件"""
        if event.key == pygame.K_RETURN:
            if self.game_state == 'level_complete':
                self.next_level()
            elif self.game_state in ['game_over', 'victory']:
                self.restart_game()
        elif event.key == pygame.K_ESCAPE:
            self.game_state = 'menu'

    def switch_bullet_type(self, direction):
        """切换子弹类型"""
        if self.player:
            new_type = self.player.switch_bullet_type(direction)
            # 这里可以添加音效或UI提示

    def regenerate_all_maps(self):
        """重新生成所有地图关卡"""
        import shutil

        # 删除现有的地图文件
        assets_dir = self.level_manager.assets_dir
        if os.path.exists(assets_dir):
            try:
                # 删除所有 .map 文件
                for filename in os.listdir(assets_dir):
                    if filename.endswith('.map'):
                        file_path = os.path.join(assets_dir, filename)
                        os.remove(file_path)
                print("已删除所有现有地图文件")
            except Exception as e:
                print(f"删除地图文件时出错: {e}")

        # 重新生成所有关卡
        self.level_manager.prepare_all_levels()
        print("所有地图已重新生成")

        # 重置到第一关
        self.current_level = 1
        if self.game_state == 'playing':
            self.load_level(self.current_level)

    def quick_save(self):
        """快速保存"""
        if self.player:
            self.save_system.save_game(
                self.current_level,
                self.score,
                self.player.health,
                self.player.bullet_type
            )

    def handle_player_fire(self):
        """处理玩家射击"""
        if not self.player or self.player.health <= 0:
            return

        bullets = self.player.fire()
        if bullets:
            for bullet in bullets:
                self.bullet_manager.add_bullet(bullet)
                self.stats['shots_fired'] += 1

            if self.shoot_sound:
                self.shoot_sound.play()

    def update(self):
        """更新游戏状态"""
        if self.paused or self.game_state != 'playing':
            return

        # 处理玩家输入
        self.handle_player_input()

        # 更新游戏对象
        self.update_player()
        self.update_enemies()
        self.update_bullets()
        self.update_special_walls()
        self.update_special_effects()

        # 自测：自动朝上方射击以验证隔离墙阻挡效果
        if self.smoke_test and self.player and self.player.health > 0:
            # 朝上
            self.player.angle = -math.pi / 2
            # 每隔 12 帧射击一次
            if self._frames_executed % 12 == 0:
                self.handle_player_fire()

        # 检查胜利/失败条件
        self.check_game_conditions()

    def update_special_walls(self):
        """更新特殊围墙"""
        for wall in self.special_walls:
            wall.update()

    def update_special_effects(self):
        """更新特殊效果"""
        self.special_effect_manager.update(self.player)

    def handle_player_input(self):
        """处理玩家输入"""
        if not self.player or self.player.health <= 0:
            return

        keys = pygame.key.get_pressed()
        walls = self.environment_manager.get_all_walls()

        if keys[pygame.K_UP]:
            self.player.move(1, walls)
        if keys[pygame.K_DOWN]:
            self.player.move(-1, walls)
        if keys[pygame.K_LEFT]:
            self.player.rotate(-1)
        if keys[pygame.K_RIGHT]:
            self.player.rotate(1)

        # 持续射击：按住空格键时持续发射
        if keys[pygame.K_SPACE] and not self.paused:
            self.handle_player_fire()

    def update_player(self):
        """更新玩家"""
        if self.player:
            self.player.update()

    def update_enemies(self):
        """更新敌人"""
        walls = self.environment_manager.get_all_walls()
        
        # 为环境管理器设置AI坦克列表（用于避免友军伤害）
        self.environment_manager.all_enemies = self.enemies.copy()
        self.environment_manager.special_walls = self.special_walls.copy()

        for enemy in self.enemies[:]:
            if enemy.health <= 0:
                self.enemies.remove(enemy)
                self.score += 10
                self.stats['enemies_destroyed'] += 1
                if self.explosion_sound:
                    self.explosion_sound.play()
            else:
                enemy.update()
                enemy.update_ai(self.player, walls, self.bullet_manager, self.environment_manager)

    def update_bullets(self):
        """更新子弹"""
        # 更新子弹位置
        self.bullet_manager.update(GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT'])

        # 处理子弹碰撞
        for bullet in self.bullet_manager.get_bullets()[:]:
            self.handle_bullet_collisions(bullet)

    def handle_bullet_collisions(self, bullet):
        """处理子弹碰撞"""
        # 墙壁碰撞
        if self.check_bullet_wall_collision(bullet):
            return

        # 坦克碰撞
        if self.check_bullet_tank_collision(bullet):
            return

        # 基地碰撞
        self.check_bullet_base_collision(bullet)

    def check_bullet_wall_collision(self, bullet):
        """检查子弹与墙壁的碰撞"""
        walls = self.environment_manager.get_all_walls()

        # 检查普通围墙
        for wall in walls:
            if bullet.rect.colliderect(wall.rect):
                # 检查是否是隔离围墙
                if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                    # 隔离围墙特殊处理
                    if bullet.bullet_type == 'PIERCING' and wall.can_bullet_pass('piercing'):
                        # 穿甲子弹可以穿过隔离围墙，不被阻挡
                        continue
                    elif not wall.destructible:
                        # 非穿甲子弹碰到不可破坏的隔离围墙，直接移除子弹
                        self.bullet_manager.remove_bullet(bullet)
                        if self.explosion_sound:
                            self.explosion_sound.play()
                        # 统计
                        self.stats['barrier_blocked_shots'] += 1
                        if bullet.owner == 'enemy':
                            self.stats['enemy_shots_into_barrier'] += 1
                        elif bullet.owner == 'player':
                            self.stats['player_shots_into_barrier'] += 1
                        return True

                # 处理掩体弹：生成网格对齐的普通迷宫墙
                if bullet.creates_wall and bullet.owner == 'player':
                    barricade_wall = bullet.create_barricade_wall(self.environment_manager, wall)
                    if barricade_wall:
                        # 避免与特殊围墙重叠
                        overlap_special = any(barricade_wall.rect.colliderect(sw.rect) for sw in self.special_walls)
                        if not overlap_special:
                            self.environment_manager.add_wall(barricade_wall)

                # 造成伤害
                if hasattr(wall, 'take_damage'):
                    if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier':
                        # 隔离围墙有特殊的take_damage方法
                        destroyed = wall.take_damage(bullet.wall_damage, bullet.bullet_type.lower())
                    else:
                        # 普通围墙
                        destroyed = wall.take_damage(bullet.wall_damage)
                else:
                    destroyed = False
                if destroyed:
                    self.stats['walls_destroyed'] += 1

                # 移除被摧毁的墙壁
                self.environment_manager.remove_destroyed_walls()

                # 移除子弹（掩体弹碰撞后也要移除）
                if not bullet.can_pierce_wall or bullet.creates_wall:
                    self.bullet_manager.remove_bullet(bullet)
                    if self.explosion_sound:
                        self.explosion_sound.play()
                    # 统计：被隔离墙拦截（非穿甲）
                    if hasattr(wall, 'wall_type') and wall.wall_type == 'barrier' and not bullet.can_pierce_wall:
                        self.stats['barrier_blocked_shots'] += 1
                        if bullet.owner == 'enemy':
                            self.stats['enemy_shots_into_barrier'] += 1
                        elif bullet.owner == 'player':
                            self.stats['player_shots_into_barrier'] += 1
                    return True

        # 检查特殊围墙
        for wall in self.special_walls[:]:
            if wall.health > 0 and bullet.rect.colliderect(wall.rect):
                destroyed, effect_type = wall.take_damage(bullet.wall_damage)

                if effect_type:
                    # 根据子弹所有者决定谁获得效果
                    if bullet.owner == 'player':
                        # 玩家打破特殊围墙，玩家获得效果
                        self.special_effect_manager.trigger_effect(
                            effect_type, self.player, self.environment_manager, self.bullet_manager
                        )
                    elif bullet.owner == 'enemy':
                        # 敌人打破特殊围墙，子弹射击者获得效果和特殊子弹能力
                        shooting_enemy = bullet.shooting_tank
                        if shooting_enemy:
                            self.special_effect_manager.trigger_effect(
                                effect_type, shooting_enemy, self.environment_manager, self.bullet_manager
                            )
                            # 给予该AI坦克特殊子弹能力
                            if hasattr(shooting_enemy, 'grant_special_bullet_effect'):
                                shooting_enemy.grant_special_bullet_effect(effect_type)
                        elif self.enemies:
                            # 备用：如果没有shooting_tank信息，随机选择一个敌人
                            beneficiary = random.choice(self.enemies)
                            self.special_effect_manager.trigger_effect(
                                effect_type, beneficiary, self.environment_manager, self.bullet_manager
                            )
                            if hasattr(beneficiary, 'grant_special_bullet_effect'):
                                beneficiary.grant_special_bullet_effect(effect_type)

                if destroyed:
                    self.special_walls.remove(wall)
                    self.stats['walls_destroyed'] += 1

                # 如果不能穿墙，移除子弹
                if not bullet.can_pierce_wall:
                    self.bullet_manager.remove_bullet(bullet)
                    if self.explosion_sound:
                        self.explosion_sound.play()
                    return True

        return False

    def check_bullet_tank_collision(self, bullet):
        """检查子弹与坦克的碰撞"""
        if bullet.owner == 'player':
            # 玩家子弹击中敌人
            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    enemy.take_damage(bullet.damage)
                    self.bullet_manager.remove_bullet(bullet)
                    if self.explosion_sound:
                        self.explosion_sound.play()
                    return True

        elif bullet.owner == 'enemy':
            # 敌方子弹击中玩家
            if self.player and bullet.rect.colliderect(self.player.rect):
                self.player.take_damage(bullet.damage)
                self.bullet_manager.remove_bullet(bullet)
                if self.explosion_sound:
                    self.explosion_sound.play()
                return True

        return False

    def check_bullet_base_collision(self, bullet):
        """检查子弹与基地的碰撞"""
        player_base = self.environment_manager.player_base
        enemy_base = self.environment_manager.enemy_base

        # 敌方子弹击中玩家基地
        if (bullet.owner == 'enemy' and player_base and
            bullet.rect.colliderect(player_base.rect)):
            player_base.take_damage(bullet.damage)
            self.bullet_manager.remove_bullet(bullet)
            if self.explosion_sound:
                self.explosion_sound.play()

        # 玩家子弹击中敌方基地
        elif (bullet.owner == 'player' and enemy_base and
              bullet.rect.colliderect(enemy_base.rect)):
            enemy_base.take_damage(bullet.damage)
            self.bullet_manager.remove_bullet(bullet)
            if self.explosion_sound:
                self.explosion_sound.play()

    def check_game_conditions(self):
        """检查游戏胜负条件"""
        player_base = self.environment_manager.player_base
        enemy_base = self.environment_manager.enemy_base

        # 失败条件
        if (not self.player or self.player.health <= 0 or
            (player_base and player_base.health <= 0)):
            self.game_state = 'game_over'
            return

        # 胜利条件
        victory = False

        if WIN_CONDITION['BOTH_REQUIRED']:
            # 需要同时满足两个条件
            enemy_base_destroyed = (enemy_base is None or enemy_base.health <= 0)
            all_enemies_eliminated = len(self.enemies) == 0

            if WIN_CONDITION['DESTROY_ENEMY_BASE'] and WIN_CONDITION['ELIMINATE_ALL_ENEMIES']:
                victory = enemy_base_destroyed and all_enemies_eliminated
            elif WIN_CONDITION['DESTROY_ENEMY_BASE']:
                victory = enemy_base_destroyed
            elif WIN_CONDITION['ELIMINATE_ALL_ENEMIES']:
                victory = all_enemies_eliminated
        else:
            # 满足任一条件即可
            if WIN_CONDITION['DESTROY_ENEMY_BASE'] and enemy_base and enemy_base.health <= 0:
                victory = True
            elif WIN_CONDITION['ELIMINATE_ALL_ENEMIES'] and len(self.enemies) == 0:
                victory = True

        # 时间限制检查
        if WIN_CONDITION['TIME_LIMIT']:
            elapsed = pygame.time.get_ticks() - self.start_time
            if elapsed > WIN_CONDITION['TIME_LIMIT']:
                self.game_state = 'game_over'
                return

        if victory:
            if self.current_level >= self.level_manager.max_level:
                self.game_state = 'victory'
            else:
                self.game_state = 'level_complete'

    def next_level(self):
        """进入下一关"""
        # 保存当前进度
        if self.player:
            self.save_system.save_game(
                self.current_level,
                self.score,
                self.player.health,
                self.player.bullet_type
            )

        self.current_level += 1
        self.load_level(self.current_level)

    def restart_game(self):
        """重新开始游戏"""
        self.current_level = 1
        self.score = 0
        self.stats = {
            'shots_fired': 0,
            'enemies_destroyed': 0,
            'walls_destroyed': 0,
            'barrier_blocked_shots': 0,
            'enemy_shots_into_barrier': 0,
            'player_shots_into_barrier': 0,
            'edge_spawn_unsafe_enemies': 0,
            'total_enemies_loaded': 0,
            'edge_unsafe_positions': [],
        }
        self.game_state = 'menu'

    def draw(self):
        """绘制游戏画面"""
        # 清空屏幕
        self.screen.fill(GAME_CONFIG['BG_COLOR'])

        if self.game_state == 'menu':
            self.draw_main_menu()
        elif self.game_state == 'level_select':
            self.level_selector.draw(self.screen, GAME_CONFIG)
        elif self.game_state == 'playing':
            self.draw_game()
        elif self.game_state == 'help':
            self.draw_game()  # 先绘制游戏画面
            self.ui_manager.draw_help_overlay(self.screen)
        elif self.game_state in ['level_complete', 'game_over', 'victory']:
            self.draw_game()
            self.ui_manager.draw_game_state_overlay(self.screen, self.game_state)

        # 更新显示
        pygame.display.flip()

    def draw_main_menu(self):
        """绘制主菜单"""
        # 标题
        title = self.big_font.render('坦克大战', True, (255, 255, 255))
        title_rect = title.get_rect(center=(GAME_CONFIG['WIDTH'] // 2, 120))
        self.screen.blit(title, title_rect)

        # 菜单选项
        menu_items = [
            "按回车键开始游戏",
            "按 L 键加载存档",
            "按 R 键重新生成所有地图",
            "按 ESC 键退出"
        ]

        for i, item in enumerate(menu_items):
            color = (255, 255, 100) if item.startswith("按 R") else (200, 200, 200)
            text = self.font.render(item, True, color)
            text_rect = text.get_rect(center=(GAME_CONFIG['WIDTH'] // 2, 200 + i * 35))
            self.screen.blit(text, text_rect)

        # 游戏说明
        instructions = [
            "游戏特色:",
            "• 多种弹药类型 (Q/E切换)",
            "• 特殊围墙效果",
            "• 关卡选择系统",
            "• 透明UI界面 (U键切换)",
            "• 动态地图生成系统"
        ]

        for i, instruction in enumerate(instructions):
            color = (255, 255, 100) if instruction.endswith(":") else (150, 150, 150)
            text = self.font.render(instruction, True, color)
            self.screen.blit(text, (50, 380 + i * 22))

    def draw_game(self):
        """绘制游戏画面"""
        # 绘制环境
        self.environment_manager.draw(self.screen)

        # 绘制特殊围墙
        for wall in self.special_walls:
            wall.draw(self.screen)

        # 绘制玩家
        if self.player:
            self.player.draw(self.screen)

        # 绘制敌人
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # 绘制子弹
        self.bullet_manager.draw(self.screen)

        # 绘制UI
        game_data = {
            'level': self.current_level,
            'score': self.score,
            'player': self.player,
            'player_base': self.environment_manager.player_base,
            'enemies': self.enemies,
            'special_effects': self.special_effect_manager.get_active_effects_info()
        }
        self.ui_manager.draw_game_ui(self.screen, game_data)

        # 绘制暂停覆盖层
        if self.paused:
            self.ui_manager.draw_pause_overlay(self.screen)

    def draw_ui(self):
        """绘制用户界面（已废弃，使用UIManager）"""
        pass

    def draw_game_state(self):
        """绘制游戏状态信息（已废弃，使用UIManager）"""
        pass

    def run(self):
        """主游戏循环"""
        while self.running:
            # 自测模式可放宽帧率以加速
            self.clock.tick(GAME_CONFIG['FPS'] if not self.smoke_test else max(15, GAME_CONFIG['FPS']))
            self.handle_events()
            self.update()
            # 自测模式下跳过绘制，加快运行
            if not self.smoke_test:
                self.draw()

            if self.smoke_test:
                self._frames_executed += 1
                if 0 < self.smoke_test_frames <= self._frames_executed:
                    # 输出摘要并退出
                    self._print_smoke_test_summary()
                    break

        pygame.quit()
        sys.exit()

    def _print_smoke_test_summary(self):
        """打印自测摘要到标准输出"""
        print("==== Smoke Test Summary ====")
        print(f"Frames: {self._frames_executed}")
        print(f"Level: {self.current_level}")
        print(f"Enemies loaded: {self.stats['total_enemies_loaded']}")
        print(f"Edge-unsafe enemy spawns: {self.stats['edge_spawn_unsafe_enemies']}")
        print(f"Shots fired (player): {self.stats['shots_fired']}")
        print(f"Enemies destroyed: {self.stats['enemies_destroyed']}")
        print(f"Walls destroyed: {self.stats['walls_destroyed']}")
        print(f"Barrier blocked shots: {self.stats['barrier_blocked_shots']}")
        print(f" - Enemy shots into barrier: {self.stats['enemy_shots_into_barrier']}")
        print(f" - Player shots into barrier: {self.stats['player_shots_into_barrier']}")
        if self.stats['edge_unsafe_positions']:
            print(f"Unsafe spawn rects: {self.stats['edge_unsafe_positions']}")
        print("============================")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tank Battle Game')
    parser.add_argument('--smoke-test', action='store_true', help='以自测模式运行，跳过渲染，仅运行固定帧数并输出摘要')
    parser.add_argument('--frames', type=int, default=900, help='自测模式下运行的帧数，默认900帧')
    args = parser.parse_args()

    game = GameManager(smoke_test=args.smoke_test, smoke_test_frames=args.frames)
    game.run()
