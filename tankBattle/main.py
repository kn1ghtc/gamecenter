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

from config import GAME_CONFIG, SOUND_CONFIG, WIN_CONDITION
from tank_system import PlayerTank, EnemyTank
from bullet_system import BulletManager
from environment import EnvironmentManager
from level_manager import LevelManager
from save_system import SaveSystem, LevelSelector, SaveMenu
from special_walls import SpecialEffectManager
from ui_manager import UIManager

class GameManager:
    """游戏管理器 - 主要的游戏逻辑控制"""
    def __init__(self):
        # 初始化Pygame
        pygame.init()

        # 创建游戏窗口
        self.screen = pygame.display.set_mode((GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']))
        pygame.display.set_caption(GAME_CONFIG['TITLE'])
        self.clock = pygame.time.Clock()

        # 字体 - 支持中文显示，优化大小
        try:
            # 使用系统中可用的中文字体，调整为更小的尺寸
            self.font = pygame.font.SysFont(['arialunicode', 'pingfang', 'hiraginosansgb', 'stheitimedium'], 24)
            self.big_font = pygame.font.SysFont(['arialunicode', 'pingfang', 'hiraginosansgb', 'stheitimedium'], 32)
        except:
            # 降级到默认字体
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 32)

        # 游戏状态
        self.running = True
        self.paused = False
        self.game_state = 'menu'  # 'menu', 'level_select', 'playing', 'level_complete', 'game_over', 'victory', 'help'
        self.show_help = False

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
            'walls_destroyed': 0
        }

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
            self.player = PlayerTank(pos['x'], pos['y'])
        else:
            self.player = PlayerTank(100, GAME_CONFIG['HEIGHT'] // 2)

        # 设置环境对象
        for wall in level_objects['walls']:
            self.environment_manager.add_wall(wall)

        # 保存特殊围墙引用
        self.special_walls = level_objects.get('special_walls', [])

        if level_objects['player_base']:
            self.environment_manager.set_player_base(level_objects['player_base'])

        if level_objects['enemy_base']:
            self.environment_manager.set_enemy_base(level_objects['enemy_base'])

        # 设置敌人
        self.enemies = level_objects['enemies']

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

        for enemy in self.enemies[:]:
            if enemy.health <= 0:
                self.enemies.remove(enemy)
                self.score += 10
                self.stats['enemies_destroyed'] += 1
                if self.explosion_sound:
                    self.explosion_sound.play()
            else:
                enemy.update()
                enemy.update_ai(self.player, walls, self.bullet_manager)

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
                # 造成伤害
                destroyed = wall.take_damage(bullet.wall_damage)
                if destroyed:
                    self.stats['walls_destroyed'] += 1

                # 移除被摧毁的墙壁
                self.environment_manager.remove_destroyed_walls()

                # 如果不能穿墙，移除子弹
                if not bullet.can_pierce_wall:
                    self.bullet_manager.remove_bullet(bullet)
                    if self.explosion_sound:
                        self.explosion_sound.play()
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
                        # 敌人打破特殊围墙，随机选择一个敌人获得效果
                        if self.enemies:
                            beneficiary = random.choice(self.enemies)
                            self.special_effect_manager.trigger_effect(
                                effect_type, beneficiary, self.environment_manager, self.bullet_manager
                            )

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
        self.stats = {'shots_fired': 0, 'enemies_destroyed': 0, 'walls_destroyed': 0}
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
            self.clock.tick(GAME_CONFIG['FPS'])
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = GameManager()
    game.run()
