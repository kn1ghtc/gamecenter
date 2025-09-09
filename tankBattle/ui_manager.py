"""
UI管理器 - 处理透明UI和显示控制
"""
import pygame
from config import UI_CONFIG, COLORS, get_chinese_font

class UIManager:
    """UI管理器"""
    def __init__(self):
        # 使用改进的中文字体配置
        try:
            self.font = get_chinese_font(UI_CONFIG['FONT_SIZE'])
            self.big_font = get_chinese_font(UI_CONFIG['BIG_FONT_SIZE'])
            print(f"✓ UI字体初始化成功: {self.font}")
        except Exception as e:
            print(f"⚠ UI字体初始化失败: {e}")
            # 最终降级方案
            self.font = pygame.font.Font(None, UI_CONFIG['FONT_SIZE'])
            self.big_font = pygame.font.Font(None, UI_CONFIG['BIG_FONT_SIZE'])

        self.ui_visible = UI_CONFIG['SHOW_UI']
        self.ui_transparency = UI_CONFIG['UI_TRANSPARENCY']
        self.ui_background = UI_CONFIG['UI_BACKGROUND']
        self.ui_position = UI_CONFIG['UI_POSITION']
        self.ui_margin = UI_CONFIG['UI_MARGIN']

        # 创建UI表面
        self.ui_surface = None
        self.ui_rect = None

    def toggle_ui_visibility(self):
        """切换UI显示状态"""
        self.ui_visible = not self.ui_visible
        return self.ui_visible

    def adjust_transparency(self, delta):
        """调整透明度"""
        self.ui_transparency = max(0.1, min(1.0, self.ui_transparency + delta))
        return self.ui_transparency

    def draw_game_ui(self, surface, game_data):
        """绘制游戏UI"""
        if not self.ui_visible:
            return

        # 准备UI数据
        ui_elements = self._prepare_ui_elements(game_data)

        # 计算UI尺寸 - 更紧凑的布局
        ui_width = 200  # 缩小宽度
        ui_height = len(ui_elements) * 22 + 15  # 减少行间距

        # 创建透明UI表面
        ui_surface = pygame.Surface((ui_width, ui_height), pygame.SRCALPHA)

        # 绘制背景（如果启用）
        if self.ui_background:
            bg_alpha = int(100 * self.ui_transparency)
            bg_color = (*COLORS['BLACK'], bg_alpha)
            pygame.draw.rect(ui_surface, bg_color, (0, 0, ui_width, ui_height), border_radius=8)

            # 绘制边框
            border_alpha = int(200 * self.ui_transparency)
            border_color = (*COLORS['WHITE'], border_alpha)
            pygame.draw.rect(ui_surface, border_color, (0, 0, ui_width, ui_height), 2, border_radius=8)

        # 绘制UI元素 - 减少间距
        y_offset = 8
        for element in ui_elements:
            text_color = (*element['color'], int(255 * self.ui_transparency))
            text_surface = self.font.render(element['text'], True, text_color)
            ui_surface.blit(text_surface, (8, y_offset))
            y_offset += 22  # 减少行间距

        # 计算UI位置
        ui_pos = self._calculate_ui_position(surface, ui_width, ui_height)

        # 绘制到主表面
        surface.blit(ui_surface, ui_pos)

        # 绘制特殊效果指示器
        self._draw_special_effects_indicator(surface, game_data)

    def _prepare_ui_elements(self, game_data):
        """准备UI元素数据"""
        elements = []

        # 基本信息
        elements.append({
            'text': f'关卡: {game_data.get("level", 1)}',
            'color': COLORS['WHITE']
        })

        elements.append({
            'text': f'分数: {game_data.get("score", 0)}',
            'color': COLORS['WHITE']
        })

        # 玩家信息
        if game_data.get('player'):
            player = game_data['player']
            elements.append({
                'text': f'生命: {player.health}/{player.max_health}',
                'color': COLORS['GREEN'] if player.health > player.max_health // 2 else COLORS['RED']
            })

            # 子弹类型
            bullet_type = getattr(player, 'bullet_type', 'NORMAL')
            elements.append({
                'text': f'弹药: {bullet_type}',
                'color': self._get_bullet_type_color(bullet_type)
            })

        # 基地信息
        if game_data.get('player_base'):
            base = game_data['player_base']
            elements.append({
                'text': f'基地: {base.health}/{base.max_health}',
                'color': COLORS['BLUE']
            })

        # 敌人数量
        enemy_count = len(game_data.get('enemies', []))
        elements.append({
            'text': f'敌人: {enemy_count}',
            'color': COLORS['RED']
        })

        return elements

    def _get_bullet_type_color(self, bullet_type):
        """获取子弹类型对应的颜色"""
        from config import BULLET_TYPES
        bullet_config = BULLET_TYPES.get(bullet_type, BULLET_TYPES['NORMAL'])
        color = bullet_config.get('COLOR', COLORS['WHITE'])
        return color if color else COLORS['WHITE']

    def _calculate_ui_position(self, surface, ui_width, ui_height):
        """计算UI位置"""
        screen_width = surface.get_width()
        screen_height = surface.get_height()

        if self.ui_position == 'TOP_LEFT':
            return (self.ui_margin, self.ui_margin)
        elif self.ui_position == 'TOP_RIGHT':
            return (screen_width - ui_width - self.ui_margin, self.ui_margin)
        elif self.ui_position == 'BOTTOM_LEFT':
            return (self.ui_margin, screen_height - ui_height - self.ui_margin)
        elif self.ui_position == 'BOTTOM_RIGHT':
            return (screen_width - ui_width - self.ui_margin, screen_height - ui_height - self.ui_margin)
        else:
            return (self.ui_margin, self.ui_margin)

    def _draw_special_effects_indicator(self, surface, game_data):
        """绘制特殊效果指示器"""
        if not self.ui_visible:
            return

        special_effects = game_data.get('special_effects', {})
        if not special_effects:
            return

        # 特殊效果指示器位置 - 调整位置和大小
        indicator_x = surface.get_width() - 170
        indicator_y = 50

        # 创建特殊效果面板 - 更紧凑
        panel_width = 150
        panel_height = len(special_effects) * 20 + 30

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)

        # 背景
        if self.ui_background:
            bg_alpha = int(120 * self.ui_transparency)
            bg_color = (*COLORS['BLUE'], bg_alpha)
            pygame.draw.rect(panel_surface, bg_color, (0, 0, panel_width, panel_height), border_radius=6)

        # 标题 - 使用较小字体
        title_alpha = int(255 * self.ui_transparency)
        title_color = (*COLORS['YELLOW'], title_alpha)
        title_text = self.font.render('特殊效果', True, title_color)
        panel_surface.blit(title_text, (8, 8))

        # 效果列表 - 减少间距
        y_offset = 28
        for effect_name, remaining_time in special_effects.items():
            effect_display_name = self._get_effect_display_name(effect_name)
            time_seconds = remaining_time // 60  # 转换为秒

            effect_text = f'{effect_display_name}: {time_seconds}s'
            text_alpha = int(255 * self.ui_transparency)
            text_color = (*COLORS['WHITE'], text_alpha)

            text_surface = self.font.render(effect_text, True, text_color)
            panel_surface.blit(text_surface, (8, y_offset))
            y_offset += 20  # 减少行间距

        surface.blit(panel_surface, (indicator_x, indicator_y))

    def _get_effect_display_name(self, effect_name):
        """获取特殊效果的显示名称"""
        effect_names = {
            'piercing_ammo': '穿甲弹',
            'explosive_ammo': '爆炸弹',
            'speed_boost': '速度提升',
            'shield': '护盾',
            'multi_shot': '多重射击',
            'ghost_mode': '幽灵模式'
        }
        return effect_names.get(effect_name, effect_name)

    def draw_pause_overlay(self, surface):
        """绘制暂停覆盖层"""
        # 创建半透明覆盖层
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*COLORS['BLACK'], 128))
        surface.blit(overlay, (0, 0))

        # 暂停文字
        pause_text = self.big_font.render('游戏暂停', True, COLORS['YELLOW'])
        text_rect = pause_text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(pause_text, text_rect)

        # 操作提示
        hint_text = self.font.render('按 P 继续游戏', True, COLORS['WHITE'])
        hint_rect = hint_text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + 50))
        surface.blit(hint_text, hint_rect)

    def draw_game_state_overlay(self, surface, game_state):
        """绘制游戏状态覆盖层"""
        if game_state not in ['level_complete', 'game_over', 'victory']:
            return

        # 创建覆盖层
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*COLORS['BLACK'], 180))
        surface.blit(overlay, (0, 0))

        # 状态文字和颜色
        if game_state == 'level_complete':
            main_text = '关卡完成!'
            main_color = COLORS['GREEN']
            hint_text = '按回车键继续下一关'
        elif game_state == 'game_over':
            main_text = '游戏结束'
            main_color = COLORS['RED']
            hint_text = '按回车键重新开始'
        elif game_state == 'victory':
            main_text = '恭喜通关!'
            main_color = COLORS['YELLOW']
            hint_text = '按回车键重新开始'

        # 主要文字
        main_surface = self.big_font.render(main_text, True, main_color)
        main_rect = main_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(main_surface, main_rect)

        # 提示文字
        hint_surface = self.font.render(hint_text, True, COLORS['WHITE'])
        hint_rect = hint_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + 60))
        surface.blit(hint_surface, hint_rect)

    def draw_help_overlay(self, surface):
        """绘制帮助覆盖层"""
        # 创建覆盖层
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*COLORS['BLACK'], 200))
        surface.blit(overlay, (0, 0))

        # 帮助内容
        help_content = [
            "游戏操作说明",
            "",
            "移动控制:",
            "  ↑/↓ - 前进/后退",
            "  ←/→ - 左转/右转",
            "",
            "战斗控制:",
            "  空格 - 射击（按住连续射击）",
            "  Q/E - 切换弹药类型",
            "",
            "游戏控制:",
            "  P - 暂停/继续",
            "  H - 显示/隐藏帮助",
            "  U - 显示/隐藏UI",
            "  +/- - 调整UI透明度",
            "",
            "弹药类型:",
            "  普通弹 - 基础伤害",
            "  穿甲弹 - 可穿透墙壁",
            "  爆炸弹 - 范围伤害",
            "  快速弹 - 高射速",
            "  重型弹 - 高伤害",
            "",
            "特殊围墙效果:",
            "  黄色 穿甲弹 - 获得穿甲弹药",
            "  棕色 爆炸弹 - 获得爆炸弹药",
            "  蓝色 围墙消除 - 清除周围围墙",
            "  绿色 传送 - 传送到基地附近",
            "  紫色 生命互换 - 与基地交换生命",
            "  亮黄 速度提升 - 移动速度翻倍",
            "  白色 护盾 - 临时免疫伤害",
            "  青色 多重射击 - 同时发射3发子弹",
            "  黑色 幽灵模式 - 可穿越围墙",
            "",
            "地图布局:",
            "  上半部分 - 敌方势力范围",
            "  下半部分 - 己方势力范围",
            "  中间围墙 - 战线分割，有3个通道",
            "",
            "按 H 关闭帮助"
        ]

        # 绘制帮助文字
        start_y = 50  # 从更高位置开始
        line_height = 17  # 减少行间距
        for i, line in enumerate(help_content):
            if line == "游戏操作说明":
                color = COLORS['YELLOW']
                font = self.big_font
            elif line.endswith(":"):
                color = COLORS['GREEN']
                font = self.font
            elif "特殊围墙" in line or "穿甲弹" in line or "爆炸弹" in line or "围墙消除" in line or \
                 "传送" in line or "生命互换" in line or "速度提升" in line or "护盾" in line or \
                 "多重射击" in line or "幽灵模式" in line:
                color = COLORS['YELLOW']  # 特殊围墙用黄色
                font = self.font
            else:
                color = COLORS['WHITE']
                font = self.font

            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (50, start_y + i * line_height))

    def get_settings(self):
        """获取UI设置"""
        return {
            'ui_visible': self.ui_visible,
            'ui_transparency': self.ui_transparency,
            'ui_background': self.ui_background,
            'ui_position': self.ui_position
        }

    def update_settings(self, **kwargs):
        """更新UI设置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
