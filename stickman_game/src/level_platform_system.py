#!/usr/bin/env python3
"""
合并的关卡和平台系统 - 统一管理关卡、平台生成和敌人配置
"""

import random
import math
import pygame
from .config import *


class Platform:
    """基础平台类"""
    def __init__(self, x, y, width, height, platform_type="static"):
        self.rect = pygame.Rect(x, y, width, height)
        self.type = platform_type
        self.color = BROWN
        
    def update(self):
        pass
    
    def draw(self, screen, image_manager=None):
        if image_manager:
            platform_sprite = image_manager.get_image('platform_sprite')
            if platform_sprite:
                self._draw_tiled_sprite(screen, platform_sprite)
                pygame.draw.rect(screen, BLACK, self.rect, 1)
                return
        
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
    
    def _draw_tiled_sprite(self, screen, sprite):
        """绘制平铺精灵"""
        sprite_width, sprite_height = sprite.get_size()
        tiles_x = max(1, self.rect.width // sprite_width)
        tiles_y = max(1, self.rect.height // sprite_height)
        
        for x in range(tiles_x):
            for y in range(tiles_y):
                tile_x = self.rect.x + x * sprite_width
                tile_y = self.rect.y + y * sprite_height
                
                if tile_x + sprite_width > self.rect.right:
                    clip_width = self.rect.right - tile_x
                    clipped_sprite = sprite.subsurface(0, 0, clip_width, sprite_height)
                    screen.blit(clipped_sprite, (tile_x, tile_y))
                elif tile_y + sprite_height > self.rect.bottom:
                    clip_height = self.rect.bottom - tile_y
                    clipped_sprite = sprite.subsurface(0, 0, sprite_width, clip_height)
                    screen.blit(clipped_sprite, (tile_x, tile_y))
                else:
                    screen.blit(sprite, (tile_x, tile_y))


class MovingPlatform(Platform):
    """移动平台"""
    def __init__(self, x, y, width, height, move_range=PLATFORM_BASE_WIDTH, speed=1, direction="horizontal"):
        super().__init__(x, y, width, height, "moving")
        self.start_pos = (x, y)
        self.move_range = move_range
        self.speed = speed
        self.direction = direction
        self.move_offset = 0
        self.move_direction = 1
        self.color = BLUE
        
    def update(self):
        self.move_offset += self.speed * self.move_direction
        
        if abs(self.move_offset) >= self.move_range:
            self.move_direction *= -1
            self.move_offset = max(-self.move_range, min(self.move_range, self.move_offset))
        
        if self.direction == "horizontal":
            self.rect.x = self.start_pos[0] + self.move_offset
        else:
            self.rect.y = self.start_pos[1] + self.move_offset


class LevelPlatformSystem:
    """统一的关卡和平台管理系统"""
    
    def __init__(self):
        # 关卡配置
        self.current_level = 1
        self.max_level = TOTAL_LEVELS
        
        # 平台管理
        self.platforms = []
        self.moving_platforms = []
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        
        # 关卡主题配置
        self.themes = {
            'forest': {
                'name': '森林',
                'levels': range(1, 11),
                'colors': {
                    'background': (135, 206, 250),
                    'ground': FOREST_GREEN,
                    'accent': (34, 139, 34)
                },
                'enemy_types': ['woodland_guard', 'tree_spirit'],
                'special_features': ['moving_platforms', 'hidden_paths']
            },
            'desert': {
                'name': '沙漠',
                'levels': range(11, 21),
                'colors': {
                    'background': (255, 218, 185),
                    'ground': DESERT_YELLOW,
                    'accent': (238, 203, 173)
                },
                'enemy_types': ['sand_warrior', 'desert_scorpion'],
                'special_features': ['sandstorms', 'quicksand']
            },
            'snow': {
                'name': '雪地',
                'levels': range(21, 31),
                'colors': {
                    'background': (176, 196, 222),
                    'ground': SNOW_WHITE,
                    'accent': (248, 248, 255)
                },
                'enemy_types': ['ice_guardian', 'frost_beast'],
                'special_features': ['ice_platforms', 'blizzard']
            }
        }
    
    def set_screen_size(self, width, height):
        """设置屏幕尺寸"""
        self.screen_width = width
        self.screen_height = height
    
    # === 关卡系统方法 ===
    
    def get_level(self, level_number):
        """获取指定关卡的完整配置"""
        if level_number < 1 or level_number > self.max_level:
            level_number = 1
        
        theme = self.get_level_theme(level_number)
        theme_data = self.themes[theme]
        difficulty_config = self.calculate_difficulty(level_number)
        
        # 生成关卡内容
        enemies = self.generate_reachable_enemies(level_number, difficulty_config, theme)
        platforms = self.generate_reachable_platforms(level_number, theme)
        goal_area = self.generate_reachable_goal(level_number, theme, platforms)
        victory_conditions = self.get_victory_conditions(level_number, len(enemies))
        
        return {
            'level': level_number,
            'theme': theme,
            'theme_data': theme_data,
            'enemies': enemies,
            'platforms': platforms,
            'goal_area': goal_area,
            'victory_conditions': victory_conditions,
            'difficulty_config': difficulty_config,
            'level_name': f"{theme_data['name']}第{level_number - (min(theme_data['levels']) - 1)}关"
        }
    
    def get_level_theme(self, level_number):
        """确定关卡主题"""
        for theme, data in self.themes.items():
            if level_number in data['levels']:
                return theme
        return 'forest'
    
    def calculate_difficulty(self, level_number):
        """智能难度计算"""
        base_difficulty = 1 + (level_number - 1) * 0.2
        tier_bonus = ((level_number - 1) // 10) * 0.3
        micro_adjustment = ((level_number - 1) % 5) * 0.05
        total_difficulty = base_difficulty + tier_bonus + micro_adjustment
        
        base_enemy_count = ENEMIES_PER_LEVEL
        enemy_count = base_enemy_count + (level_number - 1) // 3
        enemy_count = min(enemy_count, base_enemy_count * 2)
        
        return {
            'enemy_count': enemy_count,
            'enemy_health_multiplier': 1 + (level_number - 1) * 0.05,
            'enemy_speed_multiplier': 1 + (level_number - 1) * 0.03,
            'required_kill_ratio': max(0.5, 1 - (level_number - 1) * 0.01),
            'time_limit': max(MIN_TIME_LIMIT, BASE_TIME_LIMIT - level_number * TIME_REDUCTION_PER_LEVEL),
            'difficulty_score': total_difficulty
        }
    
    def generate_reachable_enemies(self, level_number, difficulty_config, theme):
        """生成可到达的敌人布局"""
        enemies = []
        enemy_count = difficulty_config['enemy_count']
        
        safe_zones = [
            (PLAYER_START_X, PLAYER_START_X + 150),
            (SCREEN_WIDTH // 2 - 100, SCREEN_WIDTH // 2 + 100),
            (SCREEN_WIDTH - 250, SCREEN_WIDTH - PLAYER_START_X)
        ]
        
        for i in range(enemy_count):
            attempts = 0
            while attempts < 20:
                x = random.randint(300, SCREEN_WIDTH - 300)
                y = SCREEN_HEIGHT - PLAYER_START_Y_OFFSET
                
                in_safe_zone = any(zone_start <= x <= zone_end for zone_start, zone_end in safe_zones)
                
                if not in_safe_zone:
                    break
                attempts += 1
            
            enemies.append(self.create_enemy(x, y, theme, level_number))
        
        return enemies
    
    def generate_reachable_platforms(self, level_number, theme):
        """生成可到达的平台系统"""
        platforms = []
        
        if level_number <= 5:
            platforms.extend([
                {'type': 'static', 'x': 200, 'y': SCREEN_HEIGHT - 120, 'width': 80, 'height': 20},
                {'type': 'static', 'x': 350, 'y': SCREEN_HEIGHT - 180, 'width': 90, 'height': 20},
                {'type': 'static', 'x': 500, 'y': SCREEN_HEIGHT - 140, 'width': 85, 'height': 20},
                {'type': 'static', 'x': 680, 'y': SCREEN_HEIGHT - 200, 'width': 90, 'height': 20},
                {'type': 'static', 'x': 820, 'y': SCREEN_HEIGHT - 160, 'width': 80, 'height': 20},
            ])
        elif level_number <= 15:
            platforms.extend([
                {'type': 'static', 'x': 180, 'y': SCREEN_HEIGHT - 150, 'width': 90, 'height': 20},
                {'type': 'moving', 'x': 320, 'y': SCREEN_HEIGHT - 220, 'width': 80, 'height': 20, 'move_range': 60, 'speed': 1},
                {'type': 'static', 'x': 480, 'y': SCREEN_HEIGHT - 180, 'width': 85, 'height': 20},
                {'type': 'moving', 'x': 620, 'y': SCREEN_HEIGHT - 280, 'width': 75, 'height': 20, 'move_range': 80, 'speed': 1.5},
                {'type': 'static', 'x': 750, 'y': SCREEN_HEIGHT - 240, 'width': 90, 'height': 20},
                {'type': 'static', 'x': 880, 'y': SCREEN_HEIGHT - 180, 'width': 80, 'height': 20},
            ])
        else:
            platforms.extend([
                {'type': 'static', 'x': 120, 'y': SCREEN_HEIGHT - 160, 'width': 70, 'height': 20},
                {'type': 'moving', 'x': 250, 'y': SCREEN_HEIGHT - 240, 'width': 80, 'height': 20, 'move_range': 100, 'speed': 2},
                {'type': 'static', 'x': 420, 'y': SCREEN_HEIGHT - 200, 'width': 75, 'height': 20},
                {'type': 'moving', 'x': 550, 'y': SCREEN_HEIGHT - 320, 'width': 70, 'height': 20, 'move_range': 120, 'speed': 1.8, 'direction': 'vertical'},
                {'type': 'moving', 'x': 680, 'y': SCREEN_HEIGHT - 280, 'width': 80, 'height': 20, 'move_range': 90, 'speed': 1.2},
                {'type': 'static', 'x': 820, 'y': SCREEN_HEIGHT - 220, 'width': 85, 'height': 20},
                {'type': 'moving', 'x': 920, 'y': SCREEN_HEIGHT - 300, 'width': 60, 'height': 20, 'move_range': 40, 'speed': 1},
            ])
        
        return platforms
    
    def generate_reachable_goal(self, level_number, theme, platforms):
        """生成可到达的目标区域"""
        if level_number <= 5:
            goal_x = SCREEN_WIDTH - 120
            goal_y = SCREEN_HEIGHT - 220
        elif level_number <= 15:
            goal_x = SCREEN_WIDTH - 140
            goal_y = SCREEN_HEIGHT - 280
        else:
            goal_x = SCREEN_WIDTH - 100
            goal_y = SCREEN_HEIGHT - 350
        
        return pygame.Rect(goal_x, goal_y, 60, 60)
    
    def create_enemy(self, x, y, theme, level_number):
        """创建敌人"""
        theme_data = self.themes[theme]
        enemy_types = theme_data['enemy_types']
        is_boss_level = level_number % 10 == 0
        
        return {
            'x': x, 'y': y,
            'type': random.choice(enemy_types),
            'is_boss': is_boss_level,
            'ai_type': self.get_ai_type(level_number),
            'patrol_range': random.randint(80, PLATFORM_BASE_WIDTH),
            'aggro_range': random.randint(ENEMY_BASE_DETECTION_RANGE, 150)
        }
    
    def get_ai_type(self, level_number):
        """根据关卡确定AI类型"""
        if level_number <= 5:
            return 'simple'
        elif level_number <= 15:
            return 'aggressive'
        else:
            return random.choice(['tactical', 'berserker'])
    
    def get_victory_conditions(self, level_number, enemy_count):
        """获取胜利条件"""
        required_kills = max(1, int(enemy_count * 0.7))
        return {
            'type': 'reach_goal_and_kill',
            'required_kills': required_kills,
            'time_limit': max(MIN_TIME_LIMIT, BASE_TIME_LIMIT - level_number * TIME_REDUCTION_PER_LEVEL),
            'reach_goal': True
        }
    
    def check_victory_condition(self, game_state):
        """检查胜利条件"""
        level_data = self.get_level(game_state['current_level'])
        victory_conditions = level_data['victory_conditions']
        
        kills_met = game_state['kills'] >= victory_conditions['required_kills']
        player_rect = game_state['player_rect']
        goal_area = level_data['goal_area']
        goal_reached = player_rect.colliderect(goal_area)
        time_ok = game_state['time_remaining'] > 0
        
        return kills_met and goal_reached and time_ok
    
    # === 平台系统方法 ===
    
    def clear_platforms(self):
        """清除所有平台"""
        self.platforms.clear()
        self.moving_platforms.clear()
    
    def add_platform(self, platform_data):
        """添加平台"""
        if platform_data['type'] == 'static':
            platform = Platform(
                platform_data['x'], platform_data['y'],
                platform_data['width'], platform_data['height'],
                'static'
            )
            self.platforms.append(platform)
        elif platform_data['type'] == 'moving':
            platform = MovingPlatform(
                platform_data['x'], platform_data['y'],
                platform_data['width'], platform_data['height'],
                platform_data.get('move_range', 80),
                platform_data.get('speed', 1),
                platform_data.get('direction', 'horizontal')
            )
            self.moving_platforms.append(platform)
    
    def generate_level_platforms(self, level_data):
        """根据关卡数据生成平台，支持屏幕尺寸自适应"""
        self.clear_platforms()
        
        scale_x = self.screen_width / SCREEN_WIDTH
        scale_y = self.screen_height / SCREEN_HEIGHT
        is_fullscreen = scale_x > 1.2 or scale_y > 1.2
        
        if 'platforms' in level_data:
            for platform_data in level_data['platforms']:
                scaled_platform_data = platform_data.copy()
                scaled_platform_data['x'] = int(platform_data['x'] * scale_x)
                scaled_platform_data['y'] = int(platform_data['y'] * scale_y)
                
                if is_fullscreen:
                    scaled_platform_data['width'] = int(platform_data['width'] * scale_x * 1.3)
                else:
                    scaled_platform_data['width'] = int(platform_data['width'] * scale_x)
                    
                scaled_platform_data['height'] = int(platform_data['height'] * scale_y)
                
                if 'move_range' in platform_data:
                    if platform_data.get('direction', 'horizontal') == 'horizontal':
                        scaled_platform_data['move_range'] = int(platform_data['move_range'] * scale_x)
                    else:
                        scaled_platform_data['move_range'] = int(platform_data['move_range'] * scale_y)
                
                self.add_platform(scaled_platform_data)
        
        if is_fullscreen:
            self._add_fullscreen_helper_platforms(scale_x, scale_y)
    
    def _add_fullscreen_helper_platforms(self, scale_x, scale_y):
        """在全屏模式下添加辅助平台"""
        platform_count = max(3, int(self.screen_width / PLATFORM_COUNT_DIVISOR))
        platform_width = int(PLATFORM_BASE_WIDTH * scale_x)
        platform_height = int(20 * scale_y)
        
        for i in range(platform_count):
            x_ratio = (i + 1) / (platform_count + 1)
            platform_x = int(self.screen_width * x_ratio) - platform_width // 2
            
            base_height = int(self.screen_height * 0.4)
            height_variation = int(self.screen_height * 0.1)
            platform_y = base_height + (i % 3 - 1) * height_variation
            
            platform_x = max(PLATFORM_MARGIN, min(platform_x, self.screen_width - platform_width - PLATFORM_MARGIN))
            platform_y = max(PLATFORM_MIN_Y, min(platform_y, self.screen_height - PLATFORM_Y_OFFSET))
            
            helper_platform = {
                'x': platform_x,
                'y': platform_y,
                'width': platform_width,
                'height': platform_height,
                'type': 'static'
            }
            self.add_platform(helper_platform)
        
        if self.screen_width > 1600:
            edge_platform_left = {
                'x': PLATFORM_MARGIN,
                'y': int(self.screen_height * 0.3),
                'width': int(80 * scale_x),
                'height': platform_height,
                'type': 'static'
            }
            self.add_platform(edge_platform_left)
            
            edge_platform_right = {
                'x': self.screen_width - int(130 * scale_x),
                'y': int(self.screen_height * 0.3),
                'width': int(80 * scale_x),
                'height': platform_height,
                'type': 'static'
            }
            self.add_platform(edge_platform_right)
    
    def update(self):
        """更新所有平台"""
        for platform in self.moving_platforms:
            platform.update()
    
    def draw(self, screen, image_manager=None):
        """绘制所有平台"""
        for platform in self.platforms + self.moving_platforms:
            platform.draw(screen, image_manager)
    
    def check_platform_collision(self, player_rect, velocity_y):
        """检查平台碰撞"""
        if velocity_y <= 0:
            return None
        
        all_platforms = self.platforms + self.moving_platforms
        
        for platform in all_platforms:
            if (player_rect.left < platform.rect.right and 
                player_rect.right > platform.rect.left):
                if (player_rect.bottom > platform.rect.top and
                    player_rect.bottom < platform.rect.bottom):
                    return platform.rect
        
        return None
    
    def get_all_platform_rects(self):
        """获取所有平台的矩形"""
        return [platform.rect for platform in self.platforms + self.moving_platforms]
