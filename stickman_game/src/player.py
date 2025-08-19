"""
简化版玩家类
单人模式，方向键控制，空格跳跃
"""
import pygame
import time
from .config import *


class Knife:
    """匕首类"""
    def __init__(self, x, y, direction, range_boost=1.0):
        self.rect = pygame.Rect(x, y, 6, 3)
        self.speed = BULLET_SPEED * 1.5 * direction
        self.damage = BULLET_DAMAGE * 0.5
        self.direction = direction
        self.range = KNIFE_DEFAULT_RANGE * range_boost
        self.start_x = x
    
    def update(self):
        self.rect.x += self.speed
        distance_traveled = abs(self.rect.x - self.start_x)
        return distance_traveled <= self.range
    
    def draw(self, screen):
        # 绘制匕首形状
        if self.direction > 0:
            # 向右飞行的匕首
            points = [
                (self.rect.right, self.rect.centery),
                (self.rect.left + 2, self.rect.top),
                (self.rect.left, self.rect.centery),
                (self.rect.left + 2, self.rect.bottom)
            ]
        else:
            # 向左飞行的匕首
            points = [
                (self.rect.left, self.rect.centery),
                (self.rect.right - 2, self.rect.top),
                (self.rect.right, self.rect.centery),
                (self.rect.right - 2, self.rect.bottom)
            ]
        pygame.draw.polygon(screen, SILVER, points)

class Bullet:
    """子弹类"""
    def __init__(self, x, y, direction, speed_boost=1.0):
        self.rect = pygame.Rect(x, y, 5, 2)
        self.speed = BULLET_SPEED * direction * speed_boost
        self.damage = BULLET_DAMAGE
    
    def update(self):
        self.rect.x += self.speed
    
    def draw(self, screen):
        pygame.draw.rect(screen, YELLOW, self.rect)

class Bomb:
    """炸弹类"""
    def __init__(self, x, y, direction, speed_boost=1.0):
        self.rect = pygame.Rect(x, y, 8, 8)
        self.velocity_x = 8 * direction * speed_boost
        self.velocity_y = -10
        self.damage = BOMB_DAMAGE
        self.speed_boost = speed_boost  # 保存用于爆炸范围计算
    
    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        self.velocity_y += GRAVITY
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, self.rect.center, 4)

class Player:
    """玩家类"""
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.velocity_y = 0
        self.on_ground = False
        self.health = MAX_HEALTH
        self.facing_right = True
        
        # 屏幕尺寸（默认值）
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        
        # 武器系统
        self.weapons = ['Knife', 'Gun', 'Bomb']
        self.current_weapon = 'Knife'
        self.weapon_index = 0
        
        # 弹药系统
        self.knife_count = -1  # 无限匕首
        self.gun_ammo = 10000  # 无限子弹
        self.bomb_count = 10000  # 无限炸弹

        # 冷却时间
        self.last_shot_time = 0
        self.last_bomb_time = 0
        self.last_weapon_switch_time = 0
        self.weapon_switch_cooldown = WEAPON_SWITCH_COOLDOWN
        
        # 动画
        self.animation_frame = 0
        self.animation_timer = 0
    
    def set_screen_size(self, width, height):
        """设置屏幕尺寸，用于边界检查和能力调整"""
        self.screen_width = width
        self.screen_height = height
        
        # 计算缩放因子
        scale_factor = min(width / SCREEN_WIDTH, height / SCREEN_HEIGHT)
        
        # 在大屏幕（全屏）模式下增强跳跃能力和武器性能
        if scale_factor > 1.2:  # 全屏模式
            from .config import FULLSCREEN_JUMP_BOOST, FULLSCREEN_WEAPON_SPEED_BOOST, FULLSCREEN_WEAPON_RANGE_BOOST
            self.jump_boost = FULLSCREEN_JUMP_BOOST  # 从配置读取
            self.weapon_speed_boost = FULLSCREEN_WEAPON_SPEED_BOOST  # 从配置读取
            self.weapon_range_boost = FULLSCREEN_WEAPON_RANGE_BOOST  # 从配置读取
        else:
            self.jump_boost = 1.0
            self.weapon_speed_boost = 1.0
            self.weapon_range_boost = 1.0
    
    def update(self, keys, level_platform_system=None):
        """更新玩家状态"""
        # 处理输入
        self.handle_input(keys)
        
        # 保存当前位置
        old_y = self.rect.y
        
        # 重力
        if not self.on_ground:
            self.velocity_y += GRAVITY
        
        # 移动
        self.rect.y += self.velocity_y
        
        # 平台碰撞检测
        if level_platform_system:
            platform_collision = level_platform_system.check_platform_collision(self.rect, self.velocity_y)
            if platform_collision and self.velocity_y > 0:
                # 站在平台上
                self.rect.bottom = platform_collision.top
                self.velocity_y = 0
                self.on_ground = True
            elif not platform_collision:
                # 检查地面碰撞（使用配置常量）
                if self.rect.bottom >= self.screen_height - GROUND_OFFSET:
                    self.rect.bottom = self.screen_height - GROUND_OFFSET
                    self.velocity_y = 0
                    self.on_ground = True
                else:
                    self.on_ground = False
        else:
            # 普通地面碰撞检测
            if self.rect.bottom >= self.screen_height - GROUND_OFFSET:
                self.rect.bottom = self.screen_height - GROUND_OFFSET
                self.velocity_y = 0
                self.on_ground = True
            else:
                self.on_ground = False
        
        # 屏幕边界（使用动态屏幕宽度）
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
        
        # 更新动画
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
    
    def handle_input(self, keys):
        """处理玩家输入"""
        # 移动
        if keys['move_left']:
            self.rect.x -= MOVE_SPEED
            self.facing_right = False
        if keys['move_right']:
            self.rect.x += MOVE_SPEED
            self.facing_right = True
        
        # 跳跃
        if keys['jump'] and self.on_ground:
            jump_force = JUMP_FORCE * getattr(self, 'jump_boost', 1.0)
            self.velocity_y = -jump_force
            self.on_ground = False
        
        # 切换武器（添加冷却检查）
        if keys['switch_weapon']:
            self.switch_weapon()
    
    def switch_weapon(self):
        """切换武器（带冷却）"""
        current_time = time.time()
        if current_time - self.last_weapon_switch_time >= self.weapon_switch_cooldown:
            self.weapon_index = (self.weapon_index + 1) % len(self.weapons)
            self.current_weapon = self.weapons[self.weapon_index]
            self.last_weapon_switch_time = current_time
            print(f"🔄 切换武器: {self.current_weapon}")  # 调试信息
    
    def can_use_weapon(self):
        """检查是否可以使用当前武器"""
        if self.current_weapon == 'Knife':
            return True  # 匕首无限使用
        elif self.current_weapon == 'Gun':
            return self.gun_ammo > 0 and self.can_shoot()
        elif self.current_weapon == 'Bomb':
            return self.bomb_count > 0 and self.can_throw_bomb()
        return False
    
    def use_weapon(self):
        """使用当前武器"""
        direction = 1 if self.facing_right else -1
        
        # 获取武器增强系数
        speed_boost = getattr(self, 'weapon_speed_boost', 1.0)
        range_boost = getattr(self, 'weapon_range_boost', 1.0)
        
        if self.current_weapon == 'Knife' and self.can_shoot():
            self.last_shot_time = time.time()
            knife_x = self.rect.right if self.facing_right else self.rect.left
            knife_y = self.rect.centery
            return Knife(knife_x, knife_y, direction, range_boost)
            
        elif self.current_weapon == 'Gun' and self.gun_ammo > 0 and self.can_shoot():
            self.last_shot_time = time.time()
            self.gun_ammo -= 1
            bullet_x = self.rect.right if self.facing_right else self.rect.left
            bullet_y = self.rect.centery
            return Bullet(bullet_x, bullet_y, direction, speed_boost)
            
        elif self.current_weapon == 'Bomb' and self.bomb_count > 0 and self.can_throw_bomb():
            self.last_bomb_time = time.time()
            self.bomb_count -= 1
            bomb_x = self.rect.centerx
            bomb_y = self.rect.centery
            return Bomb(bomb_x, bomb_y, direction, speed_boost)
        
        return None
    
    def can_shoot(self):
        """检查是否可以射击（兼容性方法）"""
        return time.time() - self.last_shot_time >= FIRE_COOLDOWN
    
    def can_throw_bomb(self):
        """检查是否可以投掷炸弹（兼容性方法）"""
        return time.time() - self.last_bomb_time >= BOMB_COOLDOWN
    
    def get_weapon_info(self):
        """获取当前武器信息"""
        if self.current_weapon == 'Knife':
            return f"Knife: ∞"
        elif self.current_weapon == 'Gun':
            return f"Gun: {self.gun_ammo}"
        elif self.current_weapon == 'Bomb':
            return f"Bomb: {self.bomb_count}"
        return ""
    
    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        if self.health < 0:
            self.health = 0
    
    def draw(self, screen, image_manager=None):
        """绘制玩家"""
        # 尝试使用图片精灵
        if image_manager:
            player_sprite = image_manager.get_sprite('player')
            if player_sprite:
                # 缩放精灵到玩家大小
                scaled_sprite = pygame.transform.scale(player_sprite, (self.rect.width, self.rect.height))
                
                # 如果面向左侧，翻转图片
                if not self.facing_right:
                    scaled_sprite = pygame.transform.flip(scaled_sprite, True, False)
                
                screen.blit(scaled_sprite, self.rect)
                
                # 绘制武器图标
                weapon_icon = image_manager.get_weapon_icon(self.current_weapon)
                if weapon_icon:
                    icon_size = 16
                    scaled_icon = pygame.transform.scale(weapon_icon, (icon_size, icon_size))
                    icon_x = self.rect.right + 5 if self.facing_right else self.rect.left - icon_size - 5
                    icon_y = self.rect.top - 5
                    screen.blit(scaled_icon, (icon_x, icon_y))
                
                # 绘制生命值条
                self._draw_health_bar(screen)
                return
        
        # 备用：使用原始火柴人绘制
        self._draw_stickman(screen)
    
    def _draw_health_bar(self, screen):
        """绘制生命值条"""
        if self.health < MAX_HEALTH:
            bar_width = 30
            bar_height = 4
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 10
            
            # 背景
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            # 当前生命值
            current_width = int((self.health / MAX_HEALTH) * bar_width)
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, current_width, bar_height))
    
    def _draw_stickman(self, screen):
        """绘制火柴人（备用方法）"""
        # 玩家身体（火柴人风格）
        center_x = self.rect.centerx
        center_y = self.rect.centery
        
        # 头部
        pygame.draw.circle(screen, WHITE, (center_x, center_y - 15), 8)
        
        # 身体
        pygame.draw.line(screen, WHITE, (center_x, center_y - 7), (center_x, center_y + 10), 3)
        
        # 手臂
        arm_offset = 5 if self.facing_right else -5
        pygame.draw.line(screen, WHITE, (center_x, center_y - 2), (center_x + arm_offset, center_y + 3), 2)
        pygame.draw.line(screen, WHITE, (center_x, center_y + 2), (center_x - arm_offset, center_y + 7), 2)
        
        # 腿部
        leg_offset = 3 if self.animation_frame % 2 == 0 else -3
        pygame.draw.line(screen, WHITE, (center_x, center_y + 10), (center_x + leg_offset, center_y + 20), 2)
        pygame.draw.line(screen, WHITE, (center_x, center_y + 10), (center_x - leg_offset, center_y + 20), 2)
        
        # 武器指示
        weapon_color = GREEN if self.current_weapon == 'Gun' else (BLUE if self.current_weapon == 'Knife' else RED)
        pygame.draw.circle(screen, weapon_color, (center_x + 15, center_y - 10), 3)
        
        # 绘制生命值条
        self._draw_health_bar(screen)
