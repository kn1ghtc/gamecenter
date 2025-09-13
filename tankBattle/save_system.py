"""
存档系统模块
处理游戏进度保存和加载
"""
import os
import json
import pygame
from datetime import datetime
from config import get_chinese_font

class SaveSystem:
    """存档管理系统"""
    def __init__(self):
        self.save_dir = 'saves'
        self.save_file = os.path.join(self.save_dir, 'game_progress.json')
        self.max_saves = 10

        # 确保存档目录存在
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        # 加载存档数据
        self.load_data()

    def load_data(self):
        """加载存档数据"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = self._create_default_data()
        else:
            self.data = self._create_default_data()

    def _create_default_data(self):
        """创建默认存档数据"""
        return {
            'last_level': 1,
            'max_level_reached': 1,
            'total_score': 0,
            'play_time': 0,  # 总游戏时间（秒）
            'saves': [],
            'settings': {
                'ui_visible': True,
                'ui_transparency': 0.7
            },
            'statistics': {
                'games_played': 0,
                'enemies_destroyed': 0,
                'walls_destroyed': 0,
                'shots_fired': 0
            }
        }

    def save_data(self):
        """保存数据到文件"""
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def save_game(self, level, score, player_health, bullet_type='NORMAL'):
        """保存游戏进度"""
        save_data = {
            'id': len(self.data['saves']) + 1,
            'level': level,
            'score': score,
            'player_health': player_health,
            'bullet_type': bullet_type,
            'timestamp': datetime.now().isoformat(),
            'play_time': self.data['play_time']
        }

        # 添加到存档列表
        self.data['saves'].append(save_data)

        # 限制存档数量
        if len(self.data['saves']) > self.max_saves:
            self.data['saves'] = self.data['saves'][-self.max_saves:]

        # 更新最大关卡记录
        if level > self.data['max_level_reached']:
            self.data['max_level_reached'] = level

        self.data['last_level'] = level
        self.data['total_score'] = max(self.data['total_score'], score)

        return self.save_data()

    def load_game(self, save_id):
        """加载游戏进度"""
        for save in self.data['saves']:
            if save['id'] == save_id:
                return save
        return None

    def get_saves_list(self):
        """获取存档列表"""
        return sorted(self.data['saves'], key=lambda x: x['timestamp'], reverse=True)

    def delete_save(self, save_id):
        """删除存档"""
        self.data['saves'] = [save for save in self.data['saves'] if save['id'] != save_id]
        return self.save_data()

    def update_statistics(self, **kwargs):
        """更新统计数据"""
        for key, value in kwargs.items():
            if key in self.data['statistics']:
                self.data['statistics'][key] += value

    def get_max_level_reached(self):
        """获取已达到的最大关卡"""
        return self.data['max_level_reached']

    def get_settings(self):
        """获取设置"""
        return self.data['settings']

    def update_settings(self, **kwargs):
        """更新设置"""
        for key, value in kwargs.items():
            if key in self.data['settings']:
                self.data['settings'][key] = value
        return self.save_data()

    def add_play_time(self, seconds):
        """添加游戏时间"""
        self.data['play_time'] += seconds
        return self.save_data()

class LevelSelector:
    """关卡选择器"""
    def __init__(self, save_system):
        self.save_system = save_system
        # 使用改进的中文字体配置
        try:
            self.font = get_chinese_font(24)
            self.big_font = get_chinese_font(32)
            print(f"✓ 关卡选择器字体初始化成功")
        except Exception as e:
            print(f"⚠ 关卡选择器字体初始化失败: {e}")
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 32)

        self.selected_level = 1
        self.max_level = save_system.get_max_level_reached()
        self.levels_per_row = 10
        self.level_button_size = (60, 60)
        self.level_button_margin = 10

    def handle_event(self, event, game_config):
        """处理关卡选择事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected_level = max(1, self.selected_level - 1)
            elif event.key == pygame.K_RIGHT:
                self.selected_level = min(self.max_level, self.selected_level + 1)
            elif event.key == pygame.K_UP:
                self.selected_level = max(1, self.selected_level - self.levels_per_row)
            elif event.key == pygame.K_DOWN:
                self.selected_level = min(self.max_level, self.selected_level + self.levels_per_row)
            elif event.key == pygame.K_RETURN:
                return self.selected_level
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                clicked_level = self._get_clicked_level(event.pos, game_config)
                if clicked_level and clicked_level <= self.max_level:
                    self.selected_level = clicked_level
                    return clicked_level

        return None

    def _get_clicked_level(self, mouse_pos, game_config):
        """获取点击的关卡"""
        start_x = (game_config['WIDTH'] - self.levels_per_row * (self.level_button_size[0] + self.level_button_margin)) // 2
        start_y = 150

        mouse_x, mouse_y = mouse_pos

        for level in range(1, self.max_level + 1):
            row = (level - 1) // self.levels_per_row
            col = (level - 1) % self.levels_per_row

            button_x = start_x + col * (self.level_button_size[0] + self.level_button_margin)
            button_y = start_y + row * (self.level_button_size[1] + self.level_button_margin)

            button_rect = pygame.Rect(button_x, button_y, *self.level_button_size)
            if button_rect.collidepoint(mouse_x, mouse_y):
                return level

        return None

    def draw(self, surface, game_config):
        """绘制关卡选择界面"""
        surface.fill((30, 30, 30))

        # 标题
        title = self.big_font.render('选择关卡', True, (255, 255, 255))
        title_rect = title.get_rect(center=(game_config['WIDTH'] // 2, 50))
        surface.blit(title, title_rect)

        # 关卡按钮
        start_x = (game_config['WIDTH'] - self.levels_per_row * (self.level_button_size[0] + self.level_button_margin)) // 2
        start_y = 150

        for level in range(1, self.max_level + 1):
            row = (level - 1) // self.levels_per_row
            col = (level - 1) % self.levels_per_row

            button_x = start_x + col * (self.level_button_size[0] + self.level_button_margin)
            button_y = start_y + row * (self.level_button_size[1] + self.level_button_margin)

            # 按钮颜色
            if level == self.selected_level:
                button_color = (100, 200, 100)  # 选中的关卡
            else:
                button_color = (80, 80, 80)     # 普通关卡

            # 绘制按钮
            button_rect = pygame.Rect(button_x, button_y, *self.level_button_size)
            pygame.draw.rect(surface, button_color, button_rect)
            pygame.draw.rect(surface, (255, 255, 255), button_rect, 2)

            # 关卡数字
            level_text = self.font.render(str(level), True, (255, 255, 255))
            text_rect = level_text.get_rect(center=button_rect.center)
            surface.blit(level_text, text_rect)

        # 操作提示
        instructions = [
            "使用方向键选择关卡",
            "回车键确认选择",
            "鼠标点击直接选择"
        ]

        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, (200, 200, 200))
            surface.blit(text, (50, game_config['HEIGHT'] - 100 + i * 25))

class SaveMenu:
    """存档菜单"""
    def __init__(self, save_system):
        self.save_system = save_system
        # 使用改进的中文字体配置
        try:
            self.font = get_chinese_font(20)
            self.big_font = get_chinese_font(28)
            print("✓ 存档菜单字体初始化成功")
        except Exception as e:
            print(f"⚠ 存档菜单字体初始化失败: {e}")
            # 最终降级方案
            self.font = pygame.font.Font(None, 20)
            self.big_font = pygame.font.Font(None, 28)

        self.selected_index = 0
        self.saves = []
        self.mode = 'load'  # 'load' 或 'save'

    def refresh_saves(self):
        """刷新存档列表"""
        self.saves = self.save_system.get_saves_list()

    def handle_event(self, event):
        """处理存档菜单事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.saves) - 1, self.selected_index + 1)
            elif event.key == pygame.K_RETURN:
                if self.saves and 0 <= self.selected_index < len(self.saves):
                    return self.saves[self.selected_index]
            elif event.key == pygame.K_DELETE:
                if self.saves and 0 <= self.selected_index < len(self.saves):
                    save_id = self.saves[self.selected_index]['id']
                    self.save_system.delete_save(save_id)
                    self.refresh_saves()
                    if self.selected_index >= len(self.saves):
                        self.selected_index = max(0, len(self.saves) - 1)

        return None

    def draw(self, surface, game_config):
        """绘制存档菜单"""
        surface.fill((30, 30, 30))

        # 标题
        title_text = '加载游戏' if self.mode == 'load' else '保存游戏'
        title = self.big_font.render(title_text, True, (255, 255, 255))
        title_rect = title.get_rect(center=(game_config['WIDTH'] // 2, 50))
        surface.blit(title, title_rect)

        # 存档列表
        if not self.saves:
            no_saves = self.font.render('没有存档', True, (200, 200, 200))
            no_saves_rect = no_saves.get_rect(center=(game_config['WIDTH'] // 2, 200))
            surface.blit(no_saves, no_saves_rect)
        else:
            start_y = 120
            for i, save in enumerate(self.saves):
                y_pos = start_y + i * 60

                # 选中背景
                if i == self.selected_index:
                    bg_rect = pygame.Rect(50, y_pos - 5, game_config['WIDTH'] - 100, 50)
                    pygame.draw.rect(surface, (60, 60, 60), bg_rect)

                # 存档信息
                timestamp = datetime.fromisoformat(save['timestamp']).strftime('%Y-%m-%d %H:%M')
                save_text = f"存档 {save['id']} - 关卡 {save['level']} - 分数 {save['score']} - {timestamp}"

                color = (255, 255, 255) if i == self.selected_index else (200, 200, 200)
                text_surface = self.font.render(save_text, True, color)
                surface.blit(text_surface, (70, y_pos))

        # 操作提示
        instructions = [
            "↑↓ 选择存档",
            "回车 确认",
            "Delete 删除存档",
            "ESC 返回"
        ]

        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, (150, 150, 150))
            surface.blit(text, (50, game_config['HEIGHT'] - 100 + i * 20))
