"""
游戏实体类
包含敌人和爆炸效果
"""
import pygame
import random
import math
from .config import *


class Enemy:
    """敌人类"""
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        self.health = ENEMY_HEALTH
        self.speed = ENEMY_SPEED
        self.direction = random.choice([-1, 1])
        self.attack_cooldown = 0
        self.animation_frame = 0
        self.animation_timer = 0
        
        # 屏幕边界（默认值，可以通过set_screen_size更新）
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        
        # AI状态
        self.state = 'patrol'  # patrol, chase, attack
        self.target_x = 0
        self.target_y = 0
    
    def set_screen_size(self, width, height):
        """设置屏幕尺寸，用于边界检查"""
        self.screen_width = width
        self.screen_height = height
    
    def update(self, player_x, player_y):
        """更新敌人状态"""
        # 计算与玩家的距离
        distance_to_player = math.sqrt((player_x - self.rect.centerx) ** 2 + 
                                     (player_y - self.rect.centery) ** 2)
        
        # 智能AI决策 - 使用配置常量
        from .config import FULLSCREEN_ENEMY_DETECTION_BOOST
        base_detection_range = ENEMY_BASE_DETECTION_RANGE
        base_chase_range = ENEMY_BASE_CHASE_RANGE
        
        if self.screen_width > ENEMY_FULLSCREEN_THRESHOLD:  # 全屏模式
            detection_range = int(base_detection_range * FULLSCREEN_ENEMY_DETECTION_BOOST)
            chase_range = int(base_chase_range * FULLSCREEN_ENEMY_DETECTION_BOOST)
        else:
            detection_range = base_detection_range
            chase_range = base_chase_range
        
        if distance_to_player < detection_range:
            self.state = 'chase'
            self.target_x = player_x
            self.target_y = player_y
        elif distance_to_player < chase_range:
            self.state = 'patrol'
        
        # 执行动作
        if self.state == 'chase':
            # 智能追逐 - 防止卡死
            move_speed = self.speed
            
            # 水平移动
            if abs(self.rect.centerx - player_x) > 10:  # 添加死区防止抖动
                if self.rect.centerx < player_x:
                    self.rect.x += move_speed
                    self.direction = 1
                elif self.rect.centerx > player_x:
                    self.rect.x -= move_speed
                    self.direction = -1
            
            # 防止追逐时撞墙卡死（使用配置常量）
            margin = PLATFORM_MARGIN // 2
            if self.rect.left <= margin:
                self.rect.left = margin
                self.direction = 1
            elif self.rect.right >= self.screen_width - margin:
                self.rect.right = self.screen_width - margin
                self.direction = -1
                
        elif self.state == 'patrol':
            # 巡逻模式 - 增强边界检测
            self.rect.x += self.speed * self.direction
            
            # 碰到边界转向（使用配置常量）
            if self.rect.left <= PLATFORM_MARGIN:
                self.rect.left = PLATFORM_MARGIN
                self.direction = 1
            elif self.rect.right >= self.screen_width - PLATFORM_MARGIN:
                self.rect.right = self.screen_width - PLATFORM_MARGIN
                self.direction = -1
        
        # 重力和地面碰撞
        if self.rect.bottom < self.screen_height - GROUND_OFFSET:
            self.rect.bottom = self.screen_height - GROUND_OFFSET
        
        # 攻击冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # 更新动画
        self.animation_timer += 1
        if self.animation_timer >= 15:
            self.animation_frame = (self.animation_frame + 1) % 3
            self.animation_timer = 0
    
    def can_attack(self):
        """检查是否可以攻击"""
        return self.attack_cooldown <= 0
    
    def attack(self):
        """攻击"""
        if self.can_attack():
            self.attack_cooldown = ENEMY_ATTACK_COOLDOWN
            return ENEMY_DAMAGE
        return 0
    
    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        return self.health <= 0
    
    def draw(self, screen, image_manager=None):
        """绘制敌人"""
        # 尝试使用图片精灵
        if image_manager:
            enemy_sprite = image_manager.get_sprite('enemy')
            if enemy_sprite:
                # 缩放精灵到敌人大小
                scaled_sprite = pygame.transform.scale(enemy_sprite, (self.rect.width, self.rect.height))
                screen.blit(scaled_sprite, self.rect)
                
                # 绘制生命值条
                self._draw_health_bar(screen)
                
                # 绘制状态指示器
                self._draw_state_indicator(screen)
                return
        
        # 备用：使用原始绘制
        self._draw_stickman(screen)
    
    def _draw_health_bar(self, screen):
        """绘制生命值条"""
        if self.health < ENEMY_HEALTH:
            bar_width = 25
            bar_height = 3
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 8
            
            # 背景
            pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height))
            # 当前生命值
            current_width = int((self.health / ENEMY_HEALTH) * bar_width)
            pygame.draw.rect(screen, RED, (bar_x, bar_y, current_width, bar_height))
    
    def _draw_state_indicator(self, screen):
        """绘制状态指示器"""
        center_x = self.rect.centerx
        center_y = self.rect.centery
        
        if self.state == 'chase':
            pygame.draw.circle(screen, YELLOW, (center_x, center_y - 20), 3)
        elif self.state == 'attack':
            pygame.draw.circle(screen, RED, (center_x, center_y - 20), 3)
    
    def _draw_stickman(self, screen):
        """绘制火柴人（备用方法）"""
        center_x = self.rect.centerx
        center_y = self.rect.centery
        
        # 敌人身体（红色火柴人）
        head_radius = 6
        
        # 头部
        pygame.draw.circle(screen, RED, (center_x, center_y - 12), head_radius)
        pygame.draw.circle(screen, BLACK, (center_x, center_y - 12), head_radius, 1)
        
        # 身体
        pygame.draw.line(screen, RED, (center_x, center_y - 6), (center_x, center_y + 6), 2)
        
        # 手臂（动画效果）
        arm_angle = self.animation_frame * 10
        arm_length = 8
        arm_x = center_x + int(arm_length * math.cos(math.radians(arm_angle)))
        arm_y = center_y + int(arm_length * math.sin(math.radians(arm_angle)))
        pygame.draw.line(screen, RED, (center_x, center_y), (arm_x, arm_y), 2)
        
        # 腿部（行走动画）
        leg_offset = 4 if self.animation_frame % 2 == 0 else -4
        pygame.draw.line(screen, RED, (center_x, center_y + 6), (center_x + leg_offset, center_y + 14), 2)
        pygame.draw.line(screen, RED, (center_x, center_y + 6), (center_x - leg_offset, center_y + 14), 2)
        
        # 绘制生命值条和状态指示器
        self._draw_health_bar(screen)
        self._draw_state_indicator(screen)
        if self.state == 'chase':
            pygame.draw.circle(screen, YELLOW, (center_x, center_y - 20), 3)
        elif self.state == 'attack':
            pygame.draw.circle(screen, ORANGE, (center_x, center_y - 20), 3)
        
        # 生命值条
        if self.health < ENEMY_HEALTH:
            bar_width = 25
            bar_height = 3
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 8
            
            # 背景
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            # 当前生命值
            current_width = int((self.health / ENEMY_HEALTH) * bar_width)
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, current_width, bar_height))
            pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # 身体
        pygame.draw.line(screen, RED, (center_x, center_y - 6), (center_x, center_y + 8), 2)
        
        # 手臂（持刀动画）
        arm_offset = 4 if self.direction > 0 else -4
        knife_x = center_x + arm_offset * 2
        knife_y = center_y - 2
        
        pygame.draw.line(screen, RED, (center_x, center_y - 1), (knife_x, knife_y), 2)
        # 刀子
        pygame.draw.line(screen, GRAY, (knife_x, knife_y), (knife_x + arm_offset, knife_y - 3), 2)
        
        # 另一只手臂
        pygame.draw.line(screen, RED, (center_x, center_y + 1), (center_x - arm_offset, center_y + 5), 2)
        
        # 腿部
        leg_offset = 2 if self.animation_frame % 2 == 0 else -2
        pygame.draw.line(screen, RED, (center_x, center_y + 8), (center_x + leg_offset, center_y + 16), 2)
        pygame.draw.line(screen, RED, (center_x, center_y + 8), (center_x - leg_offset, center_y + 16), 2)
        
        # 生命值条
        if self.health < ENEMY_HEALTH:
            bar_width = 25
            bar_height = 3
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 8
            
            # 背景
            pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
            # 当前生命值
            current_width = int((self.health / ENEMY_HEALTH) * bar_width)
            pygame.draw.rect(screen, RED, (bar_x, bar_y, current_width, bar_height))

class Explosion:
    """爆炸效果类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 30  # 持续0.5秒（30帧）
        self.radius = 10
        self.max_radius = 80
        
    def update(self):
        """更新爆炸效果"""
        self.timer -= 1
        # 爆炸扩散
        progress = 1 - (self.timer / 30)
        self.radius = int(self.max_radius * progress)
    
    def draw(self, screen):
        """绘制爆炸效果"""
        if self.timer > 0:
            # 多层爆炸效果
            colors = [YELLOW, ORANGE, RED]
            radii = [self.radius, self.radius * 0.7, self.radius * 0.4]
            
            for i, (color, radius) in enumerate(zip(colors, radii)):
                if radius > 0:
                    pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(radius))
            
            # 火花效果
            for i in range(8):
                angle = (i * 45) * math.pi / 180
                spark_x = self.x + math.cos(angle) * self.radius * 0.8
                spark_y = self.y + math.sin(angle) * self.radius * 0.8
                pygame.draw.circle(screen, WHITE, (int(spark_x), int(spark_y)), 2)
