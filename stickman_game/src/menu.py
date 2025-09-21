#!/usr/bin/env python3
"""
游戏菜单系统
包含主菜单和关卡选择
"""

import pygame
import math
from .config import *


class Menu:
    """主菜单类"""
    def __init__(self):
        # 字体初始化 - 添加错误处理
        try:
            self.font_large = get_chinese_font(48) or pygame.font.Font(None, 48)
            self.font_medium = get_chinese_font(32) or pygame.font.Font(None, 32)
            self.font_small = get_chinese_font(24) or pygame.font.Font(None, 24)
            print("菜单字体加载成功")
        except Exception as e:
            print(f"菜单字体加载出现问题，使用默认字体: {e}")
            # 使用默认字体作为备用方案
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)

        self.state = 'main'  # main, level_select, settings
        self.selected_option = 0
        self.selected_level = 1
        self.max_unlocked_level = 1  # 最大可玩关卡

        # 主菜单选项
        self.main_options = [
            "开始游戏",
            "关卡选择",
            "游戏设置",
            "退出游戏"
        ]

        # 设置菜单选项
        self.settings_options = [
            "音效音量",
            "音乐音量",
            "返回主菜单"
        ]
        self.selected_setting = 0
        self.sound_volume = 0.7
        self.music_volume = 0.5

        # 动画效果
        self.animation_timer = 0
        self.title_offset = 0

    def handle_event(self, event):
        """处理菜单事件"""
        if event.type == pygame.KEYDOWN:
            if self.state == 'main':
                return self.handle_main_menu_input(event)
            elif self.state == 'level_select':
                return self.handle_level_select_input(event)
            elif self.state == 'settings':
                return self.handle_settings_input(event)
        return None

    def handle_main_menu_input(self, event):
        """处理主菜单输入"""
        if event.key == pygame.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.main_options)
        elif event.key == pygame.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.main_options)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if self.selected_option == 0:  # 开始游戏
                return {'action': 'start_game', 'level': 1}
            elif self.selected_option == 1:  # 关卡选择
                self.state = 'level_select'
            elif self.selected_option == 2:  # 游戏设置
                self.state = 'settings'
            elif self.selected_option == 3:  # 退出游戏
                return {'action': 'quit'}
        return None

    def handle_level_select_input(self, event):
        """处理关卡选择输入"""
        if event.key == pygame.K_ESCAPE:
            self.state = 'main'
        elif event.key == pygame.K_LEFT:
            if self.selected_level > 1:
                self.selected_level -= 1
        elif event.key == pygame.K_RIGHT:
            if self.selected_level < min(TOTAL_LEVELS, self.max_unlocked_level):
                self.selected_level += 1
        elif event.key == pygame.K_UP:
            if self.selected_level > 5:
                self.selected_level -= 5
        elif event.key == pygame.K_DOWN:
            if self.selected_level <= min(TOTAL_LEVELS, self.max_unlocked_level) - 5:
                self.selected_level += 5
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if self.selected_level <= self.max_unlocked_level:
                return {'action': 'start_game', 'level': self.selected_level}
        return None

    def handle_settings_input(self, event):
        """处理设置菜单输入"""
        if event.key == pygame.K_ESCAPE:
            self.state = 'main'
        elif event.key == pygame.K_UP:
            self.selected_setting = (self.selected_setting - 1) % len(self.settings_options)
        elif event.key == pygame.K_DOWN:
            self.selected_setting = (self.selected_setting + 1) % len(self.settings_options)
        elif event.key == pygame.K_LEFT:
            if self.selected_setting == 0:  # 音效音量
                self.sound_volume = max(0.0, self.sound_volume - 0.1)
            elif self.selected_setting == 1:  # 音乐音量
                self.music_volume = max(0.0, self.music_volume - 0.1)
        elif event.key == pygame.K_RIGHT:
            if self.selected_setting == 0:  # 音效音量
                self.sound_volume = min(1.0, self.sound_volume + 0.1)
            elif self.selected_setting == 1:  # 音乐音量
                self.music_volume = min(1.0, self.music_volume + 0.1)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if self.selected_setting == 2:  # 返回主菜单
                self.state = 'main'
        return None

    def update(self):
        """更新菜单动画"""
        self.animation_timer += 1
        self.title_offset = math.sin(self.animation_timer * 0.1) * 5

    def draw(self, screen):
        """绘制菜单"""
        screen.fill((20, 30, 50))  # 深蓝色背景

        if self.state == 'main':
            self.draw_main_menu(screen)
        elif self.state == 'level_select':
            self.draw_level_select(screen)
        elif self.state == 'settings':
            self.draw_settings(screen)

    def get_screen_center(self, screen):
        """获取屏幕中心点，适配全屏"""
        screen_width, screen_height = screen.get_size()
        return screen_width // 2, screen_height // 2

    def get_ui_scale(self, screen):
        """获取UI缩放比例，适配全屏"""
        screen_width, screen_height = screen.get_size()
        scale_x = screen_width / SCREEN_WIDTH
        scale_y = screen_height / SCREEN_HEIGHT
        return min(scale_x, scale_y)  # 使用较小的缩放比例保持比例

    def draw_main_menu(self, screen):
        """绘制主菜单"""
        screen_width, screen_height = screen.get_size()
        center_x, center_y = self.get_screen_center(screen)
        ui_scale = self.get_ui_scale(screen)

        # 游戏标题 - 适配屏幕尺寸
        title_y = int(center_y * 0.3 + self.title_offset)
        title_text = self.font_large.render("火柴人冒险", True, GOLD)
        title_rect = title_text.get_rect(center=(center_x, title_y))
        screen.blit(title_text, title_rect)

        # 副标题 - 适配屏幕尺寸
        subtitle_y = int(center_y * 0.45)
        subtitle_text = self.font_medium.render("30关挑战模式", True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(center_x, subtitle_y))
        screen.blit(subtitle_text, subtitle_rect)

        # 菜单选项 - 适配屏幕尺寸
        start_y = int(center_y * 0.65)
        option_spacing = max(50, int(60 * ui_scale))

        for i, option in enumerate(self.main_options):
            color = YELLOW if i == self.selected_option else WHITE
            option_text = self.font_medium.render(option, True, color)
            option_rect = option_text.get_rect(center=(center_x, start_y + i * option_spacing))
            screen.blit(option_text, option_rect)

            # 选中指示器 - 适配屏幕尺寸
            if i == self.selected_option:
                indicator_size = int((10 + math.sin(self.animation_timer * 0.2) * 3) * ui_scale)
                indicator_offset = int(30 * ui_scale)
                pygame.draw.polygon(screen, YELLOW, [
                    (option_rect.left - indicator_offset, option_rect.centery),
                    (option_rect.left - indicator_offset//2, option_rect.centery - indicator_size),
                    (option_rect.left - indicator_offset//2, option_rect.centery + indicator_size)
                ])

        # 控制说明 - 适配屏幕尺寸
        controls = [
            "↑↓ 选择  回车/空格 确认",
            "游戏控制: 方向键移动 空格跳跃",
            "Z-射击 X-炸弹 C-切换武器"
        ]

        control_start_y = screen_height - int(100 * ui_scale)
        control_spacing = max(20, int(25 * ui_scale))

        for i, control in enumerate(controls):
            control_text = self.font_small.render(control, True, GRAY)
            control_rect = control_text.get_rect(center=(center_x, control_start_y + i * control_spacing))
            screen.blit(control_text, control_rect)

    def draw_level_select(self, screen):
        """绘制关卡选择界面"""
        screen_width, screen_height = screen.get_size()
        center_x, center_y = self.get_screen_center(screen)
        ui_scale = self.get_ui_scale(screen)

        # 标题 - 适配屏幕尺寸
        title_y = int(screen_height * 0.1)
        title_text = self.font_large.render("选择关卡", True, GOLD)
        title_rect = title_text.get_rect(center=(center_x, title_y))
        screen.blit(title_text, title_rect)

        # 关卡网格 - 适配屏幕尺寸
        levels_per_row = 6
        rows = (TOTAL_LEVELS + levels_per_row - 1) // levels_per_row

        margin = int(100 * ui_scale)
        start_x = margin
        start_y = int(screen_height * 0.25)
        cell_width = (screen_width - 2 * margin) // levels_per_row
        cell_height = max(60, int(80 * ui_scale))

        for level in range(1, TOTAL_LEVELS + 1):
            row = (level - 1) // levels_per_row
            col = (level - 1) % levels_per_row

            x = start_x + col * cell_width
            y = start_y + row * cell_height

            # 关卡状态
            is_unlocked = level <= self.max_unlocked_level
            is_selected = level == self.selected_level

            # 关卡背景
            if is_selected:
                color = YELLOW
            elif is_unlocked:
                color = GREEN
            else:
                color = GRAY

            pygame.draw.rect(screen, color, (x, y, cell_width - 10, cell_height - 10))
            pygame.draw.rect(screen, BLACK, (x, y, cell_width - 10, cell_height - 10), 2)

            # 关卡号码
            level_text = self.font_medium.render(str(level), True, BLACK if is_unlocked else WHITE)
            level_rect = level_text.get_rect(center=(x + cell_width//2 - 5, y + cell_height//2 - 5))
            screen.blit(level_text, level_rect)

            # 关卡主题图标
            theme_color = self.get_theme_color(level)
            pygame.draw.circle(screen, theme_color, (x + cell_width - 25, y + 15), 8)

        # 当前选中关卡信息
        level_info = self.get_level_info(self.selected_level)
        info_y = start_y + rows * cell_height + max(20, int(30 * ui_scale))

        info_text = self.font_medium.render(f"关卡 {self.selected_level}: {level_info['title']}", True, WHITE)
        info_rect = info_text.get_rect(center=(center_x, info_y))
        screen.blit(info_text, info_rect)

        desc_text = self.font_small.render(level_info['description'], True, GRAY)
        desc_rect = desc_text.get_rect(center=(center_x, info_y + max(30, int(40 * ui_scale))))
        screen.blit(desc_text, desc_rect)

        # 控制说明
        control_text = self.font_small.render("方向键选择关卡  回车开始  ESC返回", True, WHITE)
        control_rect = control_text.get_rect(center=(center_x, screen_height - max(50, int(60 * ui_scale))))
        screen.blit(control_text, control_rect)

    def draw_settings(self, screen):
        """绘制设置界面"""
        screen_width, screen_height = screen.get_size()
        center_x, center_y = self.get_screen_center(screen)
        ui_scale = self.get_ui_scale(screen)

        title_text = self.font_large.render("游戏设置", True, GOLD)
        title_rect = title_text.get_rect(center=(center_x, int(screen_height * 0.2)))
        screen.blit(title_text, title_rect)

        # 设置选项
        start_y = int(center_y * 0.8)
        option_spacing = max(60, int(80 * ui_scale))

        for i, option in enumerate(self.settings_options):
            color = YELLOW if i == self.selected_setting else WHITE

            if i == 0:  # 音效音量
                option_text = f"{option}: {int(self.sound_volume * 100)}%"
            elif i == 1:  # 音乐音量
                option_text = f"{option}: {int(self.music_volume * 100)}%"
            else:
                option_text = option

            text = self.font_medium.render(option_text, True, color)
            text_rect = text.get_rect(center=(center_x, start_y + i * option_spacing))
            screen.blit(text, text_rect)

            # 选中指示器
            if i == self.selected_setting:
                pygame.draw.rect(screen, YELLOW, (text_rect.left - 20, text_rect.top - 5, text_rect.width + 40, text_rect.height + 10), 2)

            # 音量条
            if i < 2:  # 只为音量选项绘制音量条
                bar_width = max(200, int(250 * ui_scale))
                bar_height = max(10, int(12 * ui_scale))
                bar_x = center_x - bar_width//2
                bar_y = start_y + i * option_spacing + max(25, int(30 * ui_scale))

                # 背景条
                pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height))

                # 音量条
                volume = self.sound_volume if i == 0 else self.music_volume
                fill_width = int(bar_width * volume)
                pygame.draw.rect(screen, GREEN, (bar_x, bar_y, fill_width, bar_height))

                # 边框
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # 控制说明
        control_text = self.font_small.render("上下键选择  左右键调节音量  回车确认  ESC返回", True, WHITE)
        control_rect = control_text.get_rect(center=(center_x, screen_height - max(100, int(120 * ui_scale))))
        screen.blit(control_text, control_rect)

        back_text = self.font_small.render("按ESC返回主菜单", True, GRAY)
        back_rect = back_text.get_rect(center=(center_x, screen_height - max(50, int(60 * ui_scale))))
        screen.blit(back_text, back_rect)

    def get_theme_color(self, level):
        """获取关卡主题颜色"""
        if level <= 10:
            return FOREST_GREEN
        elif level <= 20:
            return DESERT_YELLOW
        else:
            return SNOW_WHITE

    def get_level_info(self, level):
        """获取关卡信息"""
        if level <= 10:
            theme = "森林"
        elif level <= 20:
            theme = "沙漠"
        else:
            theme = "雪地"

        difficulty = (level - 1) // 5 + 1
        enemy_count = 2 + (level - 1) // 3

        return {
            'title': f"{theme}探险",
            'description': f"难度{difficulty} | {enemy_count}个敌人 | 主题:{theme}"
        }

    def unlock_level(self, level):
        """解锁关卡"""
        if level > self.max_unlocked_level:
            self.max_unlocked_level = level
