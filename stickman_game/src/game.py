import pygame
import time
from .config import *
from .player import Player
from .entities import Enemy, Explosion
from .level_platform_system import LevelPlatformSystem
from .core import InputManager, SoundManager, SaveManager
from .menu import Menu
from .image_manager import ImageManager

class Game:
    def __init__(self):
        # 游戏状态
        self.state = 'menu'  # menu, playing, paused, game_over, level_complete
        self.running = True
        self.paused = False
        self.game_over = False
        self.level_complete = False

        # 显示设置
        self.screen = None
        self.fullscreen = False

        # 游戏时钟
        self.clock = pygame.time.Clock()

        # 管理器系统
        self.sound_manager = SoundManager()
        self.save_manager = SaveManager()
        self.level_platform_system = LevelPlatformSystem()  # 合并后的系统
        self.image_manager = ImageManager()

        # 菜单系统
        self.menu = Menu()
        # 从存档加载解锁关卡
        self.menu.max_unlocked_level = self.save_manager.get_max_unlocked_level()

        # 输入管理器
        self.input_manager = InputManager()

        # 游戏对象（在开始游戏时初始化）
        self.player = None
        self.current_level = 1

        # 实体列表
        self.enemies = []
        self.bullets = []
        self.bombs = []
        self.explosions = []

        # 游戏状态
        self.kills = 0
        self.current_score = 0
        self.level_score = 0

        # 中文字体 - 添加错误处理
        try:
            self.font = get_chinese_font(24) or pygame.font.Font(None, 24)
            self.font_medium = get_chinese_font(32) or pygame.font.Font(None, 32)
            self.big_font = get_chinese_font(48) or pygame.font.Font(None, 48)
            print("字体加载成功")
        except Exception as e:
            print(f"字体加载出现问题，使用默认字体: {e}")
            # 使用默认字体作为备用方案
            self.font = pygame.font.Font(None, 24)
            self.font_medium = pygame.font.Font(None, 32)
            self.big_font = pygame.font.Font(None, 48)

        # 时间系统
        self.level_start_time = 0
        self.time_remaining = 0
        self.game_start_time = time.time()

    def start_game(self, level=1):
        """开始游戏"""
        self.state = 'playing'
        self.current_level = level
        self.current_score = 0

        # 记录游戏开始
        self.save_manager.record_game_played()
        self.game_start_time = time.time()

        # 初始化游戏对象
        screen_width, screen_height = self.get_screen_size()
        scale_x = screen_width / SCREEN_WIDTH
        scale_y = screen_height / SCREEN_HEIGHT

        # 初始化玩家位置（使用配置常量）
        player_x = int(PLAYER_START_X * scale_x)
        player_y = int((SCREEN_HEIGHT - PLAYER_START_Y_OFFSET) * scale_y)

        self.player = Player(player_x, player_y)
        self.player.set_screen_size(screen_width, screen_height)

        # 初始化关卡
        self.init_level()

        # 播放开始音效
        self.sound_manager.play_sound('menu_select')

    def init_level(self):
        """初始化关卡"""
        level_data = self.level_platform_system.get_level(self.current_level)

        # 清除所有实体
        self.enemies.clear()
        self.bullets.clear()
        self.bombs.clear()
        self.explosions.clear()

        # 更新平台管理器的屏幕尺寸
        screen_width, screen_height = self.get_screen_size()
        self.level_platform_system.set_screen_size(screen_width, screen_height)

        # 生成关卡平台
        self.level_platform_system.generate_level_platforms(level_data)

        # 重置玩家位置和状态（根据屏幕缩放）
        if self.player:
            scale_x = screen_width / SCREEN_WIDTH
            scale_y = screen_height / SCREEN_HEIGHT

            # 更新玩家的屏幕尺寸
            self.player.set_screen_size(screen_width, screen_height)

            self.player.rect.x = int(PLAYER_START_X * scale_x)
            self.player.rect.y = int((SCREEN_HEIGHT - PLAYER_START_Y_OFFSET) * scale_y)
            self.player.velocity_y = 0
            self.player.health = MAX_HEALTH
            self.player.on_ground = False

        # 生成敌人（根据屏幕缩放）
        level_data = self.level_platform_system.get_level(self.current_level)
        difficulty_config = self.level_platform_system.calculate_difficulty(self.current_level)

        for enemy_data in level_data['enemies']:
            scale_x = screen_width / SCREEN_WIDTH
            scale_y = screen_height / SCREEN_HEIGHT

            enemy_x = int(enemy_data['x'] * scale_x)
            enemy_y = int(enemy_data['y'] * scale_y)

            # 全屏模式下确保敌人不会生成在太难到达的地方
            is_fullscreen = scale_x > 1.2 or scale_y > 1.2
            if is_fullscreen:
                # 将敌人位置稍微向下调整，更容易接触
                enemy_y = min(enemy_y, int(screen_height * 0.8))

            enemy = Enemy(enemy_x, enemy_y)
            # 设置敌人的屏幕尺寸
            enemy.set_screen_size(screen_width, screen_height)

            # 应用难度配置
            enemy.health = int(ENEMY_HEALTH * difficulty_config['enemy_health_multiplier'])
            enemy.speed = ENEMY_SPEED * difficulty_config['enemy_speed_multiplier']

            # 应用关卡特定属性
            if 'is_boss' in enemy_data and enemy_data['is_boss']:
                enemy.health = int(enemy.health * 2)  # Boss血量更多
                enemy.speed = enemy.speed * 0.8  # Boss移动较慢
            self.enemies.append(enemy)

        # 重置状态
        self.kills = 0
        self.level_score = 0
        self.level_complete = False
        self.game_over = False

        # 设置时间限制
        self.level_start_time = pygame.time.get_ticks()
        victory_conditions = level_data['victory_conditions']
        self.time_remaining = victory_conditions['time_limit']

    def restart_game(self):
        """重新开始当前关卡"""
        self.state = 'playing'
        self.game_over = False
        self.level_complete = False
        self.paused = False

        # 重新初始化当前关卡
        self.init_level()

        # 播放开始音效
        self.sound_manager.play_sound('menu_select')

    def next_level(self):
        """进入下一关"""
        if self.current_level < TOTAL_LEVELS:
            self.current_level += 1
            self.state = 'playing'
            self.level_complete = False
            self.game_over = False
            self.paused = False

            # 初始化新关卡
            self.init_level()

            # 播放开始音效
            self.sound_manager.play_sound('menu_select')
        else:
            # 所有关卡完成，返回菜单
            self.state = 'menu'

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # 全屏切换 - 在任何状态下都可用
                if event.key == CONTROLS['fullscreen']:
                    self.toggle_fullscreen()

                elif self.state == 'menu':
                    menu_result = self.menu.handle_event(event)
                    if menu_result:
                        if menu_result['action'] == 'start_game':
                            self.start_game(menu_result['level'])
                        elif menu_result['action'] == 'quit':
                            self.running = False

                elif self.state == 'playing':
                    if event.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused

                elif self.state == 'game_over':
                    if event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'menu'

                elif self.state == 'level_complete':
                    if event.key == pygame.K_r:
                        if self.current_level < TOTAL_LEVELS:
                            self.next_level()
                        else:
                            self.state = 'menu'
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'menu'

                elif self.paused:
                    if event.key == pygame.K_p:
                        self.paused = False

    def toggle_fullscreen(self):
        """切换全屏模式"""
        if not self.screen:
            return

        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            # 切换到全屏
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # 切换到窗口模式
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        pygame.display.set_caption("火柴人动作冒险游戏 - 单人模式")

        # 更新平台管理器的屏幕尺寸
        screen_width, screen_height = self.get_screen_size()
        self.level_platform_system.set_screen_size(screen_width, screen_height)

        # 如果游戏正在进行，重新生成当前关卡的平台
        if self.state == 'playing' and self.level_platform_system:
            level_data = self.level_platform_system.get_level(self.current_level)
            self.level_platform_system.generate_level_platforms(level_data)

    def get_screen_size(self):
        """获取当前屏幕尺寸"""
        if self.screen:
            return self.screen.get_size()
        return (SCREEN_WIDTH, SCREEN_HEIGHT)

    def _draw_background(self, screen, theme_colors):
        """绘制背景"""
        # 获取当前屏幕尺寸
        screen_width, screen_height = self.get_screen_size()

        # 根据关卡选择主题
        level_themes = ['forest', 'desert', 'snow']
        theme_index = (self.current_level - 1) // 10
        theme = level_themes[theme_index % len(level_themes)]

        # 尝试使用图片背景
        background = self.image_manager.get_scaled_background(theme, screen_width, screen_height)
        if background:
            screen.blit(background, (0, 0))
        else:
            # 备用：使用主题颜色
            screen.fill(theme_colors['background'])

    def update(self):
        """更新游戏状态"""
        if self.state == 'menu':
            self.menu.update()
            return
        elif self.state != 'playing' or self.paused:
            return

        # 更新时间
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.level_start_time) / 1000.0
        level_data = self.level_platform_system.get_level(self.current_level)
        time_limit = level_data['victory_conditions']['time_limit']
        self.time_remaining = max(0, time_limit - elapsed_time)

        # 时间到了游戏结束
        if self.time_remaining <= 0:
            self.game_over = True
            self.state = 'game_over'
            self.sound_manager.play_death_message("玩家")
            self.save_manager.record_death()
            return

        # 更新平台系统
        self.level_platform_system.update()

        # 获取输入
        keys = self.input_manager.get_current_input()

        # 更新玩家
        if self.player:
            self.player.update(keys, self.level_platform_system)

            # 统一武器使用
            if keys['shoot'] and self.player.can_use_weapon():
                projectile = self.player.use_weapon()
                if projectile:
                    if self.player.current_weapon == 'Knife':
                        self.bullets.append(projectile)  # 匕首也放在bullets列表中
                        self.sound_manager.play_sound('knife_throw')
                    elif self.player.current_weapon == 'Gun':
                        self.bullets.append(projectile)
                        self.sound_manager.play_sound('shoot')
                    elif self.player.current_weapon == 'Bomb':
                        self.bombs.append(projectile)
                        self.sound_manager.play_sound('explosion')

            # 玩家跳跃音效
            if keys['jump'] and self.player.on_ground:
                self.sound_manager.play_sound('jump')

        # 更新敌人
        for enemy in self.enemies[:]:
            if self.player:
                enemy.update(self.player.rect.centerx, self.player.rect.centery)

                # 检查敌人攻击玩家
                if enemy.rect.colliderect(self.player.rect):
                    self.player.take_damage(25)
                    if self.player.health <= 0:
                        self.game_over = True
                        self.state = 'game_over'
                        self.sound_manager.play_death_message("玩家")
                        self.save_manager.record_death()

        # 更新子弹（包括匕首）
        screen_width, screen_height = self.get_screen_size()

        for bullet in self.bullets[:]:
            # 检查是否是匕首类型
            if hasattr(bullet, 'range'):  # 匕首有range属性
                # 匕首更新可能返回False表示超出射程
                if not bullet.update():
                    self.bullets.remove(bullet)
                    continue
            else:
                bullet.update()

            # 子弹离开屏幕（使用动态屏幕宽度）
            if bullet.rect.x > screen_width or bullet.rect.x < 0:
                self.bullets.remove(bullet)
                continue

            # 子弹击中敌人
            for enemy in self.enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    self.bullets.remove(bullet)
                    self.enemies.remove(enemy)
                    self.kills += 1

                    # 计算积分（使用配置常量）
                    kill_score = BASE_KILL_SCORE + (self.current_level * LEVEL_SCORE_MULTIPLIER)
                    self.level_score += kill_score
                    self.current_score += kill_score

                    self.sound_manager.play_sound('hit_enemy')
                    break

        # 更新炸弹
        for bomb in self.bombs[:]:
            bomb.update()

            # 炸弹碰撞检测 - 任何碰撞都会爆炸
            exploded = False

            # 检查炸弹是否撞到地面（使用配置常量）
            if bomb.rect.bottom >= screen_height - GROUND_OFFSET:
                exploded = True

            # 检查炸弹是否撞到平台
            platform_collision = self.level_platform_system.check_platform_collision(bomb.rect, bomb.velocity_y)
            if platform_collision:
                exploded = True

            # 检查炸弹是否撞到敌人
            for enemy in self.enemies:
                if bomb.rect.colliderect(enemy.rect):
                    exploded = True
                    break

            # 检查炸弹是否撞到屏幕边界（使用动态屏幕宽度）
            if bomb.rect.x <= 0 or bomb.rect.x >= screen_width:
                exploded = True

            if exploded:
                # 创建爆炸
                explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                self.explosions.append(explosion)
                self.sound_manager.play_sound('explosion')

                # 爆炸伤害敌人（使用配置常量）
                enemies_killed = 0
                base_explosion_range = BOMB_RADIUS
                if hasattr(bomb, 'speed_boost'):
                    explosion_range = base_explosion_range * bomb.speed_boost
                else:
                    explosion_range = base_explosion_range

                for enemy in self.enemies[:]:
                    distance = ((enemy.rect.centerx - bomb.rect.centerx) ** 2 +
                              (enemy.rect.centery - bomb.rect.centery) ** 2) ** 0.5
                    if distance < explosion_range:  # 增强的爆炸范围
                        self.enemies.remove(enemy)
                        self.kills += 1
                        enemies_killed += 1

                # 爆炸击杀积分加成（使用配置常量）
                if enemies_killed > 0:
                    explosion_bonus = enemies_killed * EXPLOSION_KILL_SCORE + (self.current_level * EXPLOSION_LEVEL_BONUS)
                    self.level_score += explosion_bonus
                    self.current_score += explosion_bonus

                self.bombs.remove(bomb)

        # 更新爆炸效果
        for explosion in self.explosions[:]:
            explosion.update()
            if explosion.timer <= 0:
                self.explosions.remove(explosion)

        # 检查胜利条件
        self.check_victory()

    def check_victory(self):
        """检查胜利条件"""
        if not self.player:
            return

        level_data = self.level_platform_system.get_level(self.current_level)
        goal_area = level_data['goal_area']
        victory_conditions = level_data['victory_conditions']
        required_kills = victory_conditions['required_kills']

        # 缩放目标区域以适应当前屏幕尺寸
        screen_width, screen_height = self.get_screen_size()
        scale_x = screen_width / SCREEN_WIDTH
        scale_y = screen_height / SCREEN_HEIGHT

        scaled_goal_area = pygame.Rect(
            int(goal_area.x * scale_x),
            int(goal_area.y * scale_y),
            int(goal_area.width * scale_x),
            int(goal_area.height * scale_y)
        )

        # 检查玩家是否到达目标区域且击杀数足够
        player_in_goal = self.player.rect.colliderect(scaled_goal_area)
        kills_enough = self.kills >= required_kills

        if player_in_goal and kills_enough:
            self.level_complete = True
            self.state = 'level_complete'
            # 播放胜利欢呼声
            self.sound_manager.play_sound('victory_cheer')

            # 计算完成奖励（使用配置常量）
            time_bonus = int(self.time_remaining * 10)
            completion_bonus = COMPLETION_BASE_BONUS + (self.current_level * COMPLETION_LEVEL_MULTIPLIER)
            total_bonus = time_bonus + completion_bonus

            self.level_score += total_bonus
            self.current_score += total_bonus

            # 解锁下一关
            if self.current_level < TOTAL_LEVELS:
                self.save_manager.unlock_level(self.current_level + 1)

            # 更新最高分
            self.save_manager.update_high_score(self.current_score)

    def next_level(self):
        """进入下一关"""
        if self.current_level < TOTAL_LEVELS:
            self.current_level += 1
            self.init_level()
            self.state = 'playing'
        else:
            # 游戏通关
            self.state = 'menu'

    def restart_game(self):
        """重新开始游戏"""
        if self.player:
            self.player.health = MAX_HEALTH
        self.game_over = False
        self.level_complete = False
        self.level_score = 0
        self.init_level()
        self.state = 'playing'

    def draw(self, screen):
        """绘制游戏"""
        if self.state == 'menu':
            self.menu.draw(screen)
            return

        # 获取关卡主题颜色
        level_data = self.level_platform_system.get_level(self.current_level)
        theme_colors = level_data['theme_data']['colors']

        # 绘制背景
        self._draw_background(screen, theme_colors)

        # 获取当前屏幕尺寸
        screen_width, screen_height = self.get_screen_size()

        # 绘制地面（使用主题地面色）
        # 绘制地面（使用配置常量）
        pygame.draw.rect(screen, theme_colors['ground'],
                        (0, screen_height - GROUND_OFFSET, screen_width, GROUND_OFFSET))

        # 绘制平台系统
        self.level_platform_system.draw(screen, self.image_manager)

        # 绘制目标区域（适应屏幕缩放）
        goal_area = level_data['goal_area']
        screen_width, screen_height = self.get_screen_size()
        scale_x = screen_width / SCREEN_WIDTH
        scale_y = screen_height / SCREEN_HEIGHT

        # 在全屏模式下增强目标区域可见性
        is_fullscreen = scale_x > 1.2 or scale_y > 1.2

        # 缩放目标区域
        scaled_goal_area = pygame.Rect(
            int(goal_area.x * scale_x),
            int(goal_area.y * scale_y),
            int(goal_area.width * scale_x),
            int(goal_area.height * scale_y)
        )

        # 在全屏模式下，目标区域更加明显
        if is_fullscreen:
            # 绘制闪烁边框
            glow_time = pygame.time.get_ticks() // GLOW_CYCLE_TIME
            glow_color = GOLD_COLOR if glow_time % 2 == 0 else YELLOW
            pygame.draw.rect(screen, glow_color, scaled_goal_area)
            # 添加额外的边框
            pygame.draw.rect(screen, WHITE, scaled_goal_area, max(2, int(3 * min(scale_x, scale_y))))
        else:
            pygame.draw.rect(screen, GOLD_COLOR, scaled_goal_area)

        # 绘制目标标志（缩放）
        flag_x = scaled_goal_area.centerx
        flag_y = scaled_goal_area.top
        flag_size = max(1, int(30 * min(scale_x, scale_y)))  # 动态标志大小

        # 在全屏模式下加大标志尺寸
        if is_fullscreen:
            flag_size = int(flag_size * 1.5)

        pygame.draw.line(screen, BLACK, (flag_x, flag_y), (flag_x, flag_y + flag_size), max(1, int(3 * min(scale_x, scale_y))))

        # 旗帜大小也要缩放
        flag_width = max(3, int(25 * scale_x))
        flag_height = max(3, int(15 * scale_y))

        # 全屏模式下放大旗帜
        if is_fullscreen:
            flag_width = int(flag_width * 1.5)
            flag_height = int(flag_height * 1.5)

        pygame.draw.polygon(screen, RED, [
            (flag_x + 3, flag_y),
            (flag_x + 3, flag_y + flag_height),
            (flag_x + flag_width, flag_y + flag_height // 2)
        ])

        # 绘制目标提示文字
        text_size = 24 if is_fullscreen else 16
        try:
            goal_font = get_chinese_font(text_size) or pygame.font.Font(None, text_size)
            goal_text = goal_font.render("目标", True, BLACK)
        except:
            goal_text = pygame.font.Font(None, text_size).render("Goal", True, BLACK)
        screen.blit(goal_text, (flag_x - 15, flag_y + flag_size + 5))

        # 绘制游戏实体
        if self.player:
            self.player.draw(screen, self.image_manager)

        for enemy in self.enemies:
            enemy.draw(screen, self.image_manager)

        for bullet in self.bullets:
            bullet.draw(screen)

        for bomb in self.bombs:
            bomb.draw(screen)

        for explosion in self.explosions:
            explosion.draw(screen)

        # 绘制UI
        self.draw_ui(screen)

        # 绘制游戏状态覆盖层
        if self.paused:
            self.draw_pause_screen(screen)
        elif self.game_over:
            self.draw_game_over_screen(screen)
        elif self.level_complete:
            self.draw_level_complete_screen(screen)

    def draw_ui(self, screen):
        """绘制用户界面"""
        if not self.player:
            return

        # 获取当前屏幕尺寸
        screen_width, screen_height = self.get_screen_size()
        scale_x = screen_width / SCREEN_WIDTH
        scale_y = screen_height / SCREEN_HEIGHT
        is_fullscreen = scale_x > 1.2 or scale_y > 1.2

        level_data = self.level_platform_system.get_level(self.current_level)
        victory_conditions = level_data['victory_conditions']

        # 血量条
        # 绘制生命值条（使用配置常量）
        health_width = int((self.player.health / MAX_HEALTH) * HEALTH_BAR_WIDTH)
        pygame.draw.rect(screen, RED, (UI_MARGIN, UI_MARGIN, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, GREEN, (UI_MARGIN, UI_MARGIN, health_width, HEALTH_BAR_HEIGHT))
        health_text = self.font.render(f"生命: {self.player.health}/{MAX_HEALTH}", True, WHITE)
        screen.blit(health_text, (220, 10))

        # 全屏模式增强指示器
        if is_fullscreen:
            boost_text = self.font.render("⚡ 全屏增强模式", True, GOLD_COLOR)
            screen.blit(boost_text, (UI_MARGIN, screen_height - BOOST_INFO_Y_OFFSET))

            # 显示增强效果
            boosts = [
                f"跳跃力 +{int((getattr(self.player, 'jump_boost', 1.0) - 1.0) * 100)}%",
                f"武器速度 +{int((getattr(self.player, 'weapon_speed_boost', 1.0) - 1.0) * 100)}%",
                f"武器射程 +{int((getattr(self.player, 'weapon_range_boost', 1.0) - 1.0) * 100)}%"
            ]
            boost_detail = " | ".join(boosts)
            try:
                detail_font = get_chinese_font(14) or pygame.font.Font(None, 14)
                detail_text = detail_font.render(boost_detail, True, YELLOW)
            except:
                detail_text = pygame.font.Font(None, 14).render(boost_detail, True, YELLOW)
            screen.blit(detail_text, (10, screen_height - 35))

        # 关卡信息（使用中文字体）
        level_text = self.font.render(f"关卡: {level_data['level_name']}", True, WHITE)
        screen.blit(level_text, (10, 40))

        # 击杀信息
        kill_text = self.font.render(f"击杀: {self.kills}/{victory_conditions['required_kills']}", True, WHITE)
        screen.blit(kill_text, (10, 70))

        # 积分信息
        score_text = self.font.render(f"关卡积分: {self.level_score}", True, YELLOW)
        screen.blit(score_text, (UI_MARGIN, SCORE_Y_POSITION))

        total_score_text = self.font.render(f"总积分: {self.current_score}", True, GOLD)
        screen.blit(total_score_text, (10, 130))

        # 时间信息
        time_color = RED if self.time_remaining < 30 else WHITE
        time_text = self.font.render(f"时间: {int(self.time_remaining)}秒", True, time_color)
        screen.blit(time_text, (10, 160))

        # 性能监控（仅在全屏模式显示）
        if is_fullscreen:
            fps = int(self.clock.get_fps()) if hasattr(self, 'clock') else 0
            try:
                perf_font = get_chinese_font(14) or pygame.font.Font(None, 14)
                performance_text = perf_font.render(f"FPS: {fps}", True, WHITE)
            except:
                performance_text = pygame.font.Font(None, 14).render(f"FPS: {fps}", True, WHITE)
            screen.blit(performance_text, (screen_width - 80, 10))

        # 武器信息
        weapon_info = self.player.get_weapon_info()
        weapon_text = self.font.render(f"武器: {weapon_info}", True, WHITE)
        screen.blit(weapon_text, (10, 190))

        # 控制说明 - 更新为新的武器系统，适应屏幕宽度
        controls = [
            "方向键: 移动",
            "空格: 跳跃",
            "Z: 使用武器",
            "C: 切换武器",
            "P: 暂停",
            "F11: 全屏",
            "ESC: 返回菜单"
        ]

        # 控制说明位置适应屏幕宽度
        # 绘制控制信息（使用配置常量）
        controls_x = max(screen_width - CONTROL_INFO_WIDTH, CONTROL_INFO_MIN_X)

        for i, control in enumerate(controls):
            try:
                control_font = get_chinese_font(18) or pygame.font.Font(None, 18)
                text = control_font.render(control, True, WHITE)
            except:
                text = pygame.font.Font(None, 18).render(control, True, WHITE)
            screen.blit(text, (controls_x, 10 + i * 22))

        # 存档信息显示，适应屏幕宽度
        save_info = f"最高关卡: {self.save_manager.get_max_unlocked_level()}"
        try:
            save_font = get_chinese_font(16) or pygame.font.Font(None, 16)
            save_text = save_font.render(save_info, True, GRAY)
        except:
            save_text = pygame.font.Font(None, 16).render(save_info, True, GRAY)
        screen.blit(save_text, (controls_x, 180))

        # 全屏模式状态显示
        if self.fullscreen:
            fullscreen_info = f"全屏模式 ({screen_width}x{screen_height})"
            try:
                fullscreen_font = get_chinese_font(14) or pygame.font.Font(None, 14)
                fullscreen_text = fullscreen_font.render(fullscreen_info, True, GREEN)
            except:
                fullscreen_text = pygame.font.Font(None, 14).render(fullscreen_info, True, GREEN)
            screen.blit(fullscreen_text, (controls_x, CONTROLS_Y_POSITION))

    def draw_pause_screen(self, screen):
        """绘制暂停界面"""
        screen_width, screen_height = self.get_screen_size()

        overlay = pygame.Surface((screen_width, screen_height))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))

        pause_text = self.big_font.render("游戏暂停", True, WHITE)
        text_rect = pause_text.get_rect(center=(screen_width//2, screen_height//2))
        screen.blit(pause_text, text_rect)

        resume_text = self.font_medium.render("按P继续游戏", True, WHITE)
        resume_rect = resume_text.get_rect(center=(screen_width//2, screen_height//2 + 50))
        screen.blit(resume_text, resume_rect)

        # 显示当前积分
        score_display = self.font.render(f"当前积分: {self.current_score}", True, GOLD)
        score_rect = score_display.get_rect(center=(screen_width//2, screen_height//2 + 100))
        screen.blit(score_display, score_rect)

    def draw_game_over_screen(self, screen):
        """绘制游戏结束界面"""
        screen_width, screen_height = self.get_screen_size()

        overlay = pygame.Surface((screen_width, screen_height))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))

        game_over_text = self.big_font.render("游戏结束", True, RED)
        text_rect = game_over_text.get_rect(center=(screen_width//2, screen_height//2 - 50))
        screen.blit(game_over_text, text_rect)

        # 显示本次游戏积分
        score_text = self.font_medium.render(f"本次积分: {self.current_score}", True, YELLOW)
        score_rect = score_text.get_rect(center=(screen_width//2, screen_height//2))
        screen.blit(score_text, score_rect)

        restart_text = self.font_medium.render("按R重新开始，ESC返回菜单", True, WHITE)
        restart_rect = restart_text.get_rect(center=(screen_width//2, screen_height//2 + 50))
        screen.blit(restart_text, restart_rect)

    def draw_level_complete_screen(self, screen):
        """绘制关卡完成界面"""
        screen_width, screen_height = self.get_screen_size()

        overlay = pygame.Surface((screen_width, screen_height))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))

        complete_text = self.big_font.render("关卡完成!", True, GREEN)
        text_rect = complete_text.get_rect(center=(screen_width//2, screen_height//2 - 80))
        screen.blit(complete_text, text_rect)

        # 显示关卡积分
        level_score_text = self.font_medium.render(f"关卡积分: {self.level_score}", True, YELLOW)
        level_score_rect = level_score_text.get_rect(center=(screen_width//2, screen_height//2 - 30))
        screen.blit(level_score_text, level_score_rect)

        # 显示总积分
        total_score_text = self.font_medium.render(f"总积分: {self.current_score}", True, GOLD)
        total_score_rect = total_score_text.get_rect(center=(screen_width//2, screen_height//2 + 10))
        screen.blit(total_score_text, total_score_rect)

        # 显示统计信息
        stats_text = self.font.render(f"击杀: {self.kills} | 剩余时间: {int(self.time_remaining)}秒", True, WHITE)
        stats_rect = stats_text.get_rect(center=(screen_width//2, screen_height//2 + 50))
        screen.blit(stats_text, stats_rect)

        if self.current_level < TOTAL_LEVELS:
            next_text = self.font_medium.render("按R进入下一关，ESC返回菜单", True, WHITE)
        else:
            next_text = self.font_medium.render("恭喜通关！按ESC返回菜单", True, GOLD_COLOR)

        next_rect = next_text.get_rect(center=(screen_width//2, screen_height//2 + 90))
        screen.blit(next_text, next_rect)

    def run(self):
        """运行游戏主循环"""
        # 获取屏幕引用
        self.screen = pygame.display.get_surface()

        while self.running:
            self.handle_events()
            self.update()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
