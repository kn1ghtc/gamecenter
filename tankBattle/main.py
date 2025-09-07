"""
Tank Battle Game - 重构版本
=========================
面向对象的坦克大战游戏

Controls:
- ↑/↓: Move forward/backward
- ←/→: Rotate left/right
- Space: Fire
- P: Pause

新特性:
- 面向对象设计
- 配置化系统
- 多种子弹类型
- 敌方基地系统
- 改进的胜利条件

Run: python main_oop.py
Requires: pygame (pip install pygame)
"""
import pygame
import sys
import os

from config import GAME_CONFIG, SOUND_CONFIG, WIN_CONDITION
from tank_system import PlayerTank, EnemyTank
from bullet_system import BulletManager
from environment import EnvironmentManager
from level_manager import LevelManager

class GameManager:
    """游戏管理器 - 主要的游戏逻辑控制"""
    def __init__(self):
        # 初始化Pygame
        pygame.init()

        # 创建游戏窗口
        self.screen = pygame.display.set_mode((GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']))
        pygame.display.set_caption(GAME_CONFIG['TITLE'])
        self.clock = pygame.time.Clock()

        # 字体
        self.font = pygame.font.SysFont(None, 32)
        self.big_font = pygame.font.SysFont(None, 48)

        # 游戏状态
        self.running = True
        self.paused = False
        self.game_state = 'playing'  # 'playing', 'level_complete', 'game_over', 'victory'

        # 游戏数据
        self.score = 0
        self.current_level = 1
        self.start_time = pygame.time.get_ticks()

        # 游戏对象管理器
        self.bullet_manager = BulletManager()
        self.environment_manager = EnvironmentManager()
        self.level_manager = LevelManager()

        # 游戏对象
        self.player = None
        self.enemies = []

        # 音效
        self.load_sounds()

        # 预生成所有关卡
        self.level_manager.prepare_all_levels()

        # 加载第一关
        self.load_level(self.current_level)

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
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_SPACE and not self.paused and self.game_state == 'playing':
                    self.handle_player_fire()
                elif event.key == pygame.K_RETURN:
                    if self.game_state == 'level_complete':
                        self.next_level()
                    elif self.game_state in ['game_over', 'victory']:
                        self.restart_game()

    def handle_player_fire(self):
        """处理玩家射击"""
        if not self.player or self.player.health <= 0:
            return

        bullet = self.player.fire()
        if bullet:
            self.bullet_manager.add_bullet(bullet)
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

        # 检查胜利/失败条件
        self.check_game_conditions()

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

        for wall in walls:
            if bullet.rect.colliderect(wall.rect):
                # 造成伤害
                wall.take_damage(bullet.wall_damage)

                # 移除被摧毁的墙壁
                self.environment_manager.remove_destroyed_walls()

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
        self.current_level += 1
        self.load_level(self.current_level)

    def restart_game(self):
        """重新开始游戏"""
        self.current_level = 1
        self.score = 0
        self.load_level(self.current_level)

    def draw(self):
        """绘制游戏画面"""
        # 清空屏幕
        self.screen.fill(GAME_CONFIG['BG_COLOR'])

        # 绘制环境
        self.environment_manager.draw(self.screen)

        # 绘制玩家
        if self.player:
            self.player.draw(self.screen)

        # 绘制敌人
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # 绘制子弹
        self.bullet_manager.draw(self.screen)

        # 绘制UI
        self.draw_ui()

        # 绘制游戏状态信息
        self.draw_game_state()

        # 更新显示
        pygame.display.flip()

    def draw_ui(self):
        """绘制用户界面"""
        # 分数
        score_text = self.font.render(f'Score: {self.score}', True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

        # 关卡
        level_text = self.font.render(f'Level: {self.current_level}', True, (255, 255, 255))
        self.screen.blit(level_text, (10, 40))

        # 玩家生命值
        if self.player:
            health_text = self.font.render(f'Health: {self.player.health}', True, (255, 255, 255))
            self.screen.blit(health_text, (10, 70))

        # 基地生命值
        player_base = self.environment_manager.player_base
        if player_base:
            base_text = self.font.render(f'Base: {player_base.health}', True, (255, 255, 255))
            self.screen.blit(base_text, (10, 100))

        # 敌人数量
        enemy_text = self.font.render(f'Enemies: {len(self.enemies)}', True, (255, 255, 255))
        self.screen.blit(enemy_text, (10, 130))

        # 暂停提示
        if self.paused:
            pause_text = self.big_font.render('PAUSED', True, (255, 255, 0))
            text_rect = pause_text.get_rect(center=(GAME_CONFIG['WIDTH'] // 2, GAME_CONFIG['HEIGHT'] // 2))
            self.screen.blit(pause_text, text_rect)

    def draw_game_state(self):
        """绘制游戏状态信息"""
        if self.game_state == 'level_complete':
            text = self.big_font.render('LEVEL COMPLETE!', True, (0, 255, 0))
            instruction = self.font.render('Press ENTER to continue', True, (255, 255, 255))
        elif self.game_state == 'game_over':
            text = self.big_font.render('GAME OVER', True, (255, 0, 0))
            instruction = self.font.render('Press ENTER to restart', True, (255, 255, 255))
        elif self.game_state == 'victory':
            text = self.big_font.render('VICTORY!', True, (255, 255, 0))
            instruction = self.font.render('Press ENTER to restart', True, (255, 255, 255))
        else:
            return

        # 居中显示
        text_rect = text.get_rect(center=(GAME_CONFIG['WIDTH'] // 2, GAME_CONFIG['HEIGHT'] // 2))
        instruction_rect = instruction.get_rect(center=(GAME_CONFIG['WIDTH'] // 2, GAME_CONFIG['HEIGHT'] // 2 + 50))

        self.screen.blit(text, text_rect)
        self.screen.blit(instruction, instruction_rect)

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
