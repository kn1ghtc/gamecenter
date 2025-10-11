#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小羊吃草 - 生态模拟游戏
==================

一款以生态平衡为核心的互动模拟游戏。
玩家可以观察和影响一个包含羊、兔子、牛和草地的生态系统。

主要特性：
- 真实的生态循环系统
- 动态的环境变化
- 智能的动物行为AI
- 互动的用户界面
- 可视化的数据统计

控制方式：
- WASD：移动摄像机
- 鼠标滚轮：缩放视角
- 左键：添加选中的动物
- 右键：查看动物/地块信息
- 空格：暂停/继续游戏

作者：AI Assistant
版本：1.0.0
"""

# 首先导入现代化工具，完全避免 pkg_resources 警告
from modern_tools import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT

import pygame
import sys
import math
import random
import os
from typing import Optional, Tuple

# 字体初始化 - 支持中文显示
def init_chinese_fonts():
    """初始化中文字体支持"""
    pygame.font.init()

    # 跨平台中文字体路径
    chinese_fonts = [
        # Windows 字体
        "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
        # macOS 字体
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Linux 字体
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]

    for font_path in chinese_fonts:
        try:
            if os.path.exists(font_path):
                test_font = pygame.font.Font(font_path, 24)
                test_font.render("测试", True, (0, 0, 0))
                print(f"✅ 成功加载中文字体: {font_path}")
                return font_path
        except Exception:
            continue

    # 尝试使用pygame系统字体
    for font_name in ['microsoftyahei', 'simhei', 'simsun', 'pingfang', 'notosanscjk']:
        try:
            font_path = pygame.font.match_font(font_name)
            if font_path:
                test_font = pygame.font.Font(font_path, 24)
                test_font.render("测试", True, (0, 0, 0))
                print(f"✅ 成功加载系统字体: {font_name}")
                return font_path
        except Exception:
            continue

    print("⚠️  未找到中文字体，使用系统默认字体")
    return None

# 初始化中文字体
CHINESE_FONT_PATH = init_chinese_fonts()

# 导入游戏模块
from game_entities import *
from ecosystem import EcoSystem
from ui_manager import UIManager
from camera import Camera

class EcoGrasslandGame:
    """小羊吃草生态模拟游戏主类"""

    def __init__(self):
        # 初始化Pygame
        pygame.init()

        # 游戏窗口设置（支持调整大小）
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("小羊吃草 - 生态模拟游戏 v1.0")
        self.fullscreen = False
        
        # 当前屏幕尺寸（动态适配）
        self.current_width = SCREEN_WIDTH
        self.current_height = SCREEN_HEIGHT

        # 设置图标（如果有的话）
        try:
            icon = pygame.Surface((32, 32))
            icon.fill((100, 200, 100))  # 绿色方块作为临时图标
            pygame.display.set_icon(icon)
        except:
            pass  # 忽略图标设置错误

        # 游戏时钟
        self.clock = pygame.time.Clock()
        self.target_fps = 60

        # 初始化游戏系统
        self.ecosystem = EcoSystem()
        self.ui_manager = UIManager(CHINESE_FONT_PATH, self.current_width, self.current_height)  # 传入中文字体路径和屏幕尺寸
        self.camera = Camera(self.current_width, self.current_height)

        # 设置摄像机初始位置和世界边界
        self.camera.set_world_bounds(MAP_WIDTH, MAP_HEIGHT)
        self.camera.move_to(MAP_WIDTH / 2, MAP_HEIGHT / 2, smooth=False)

        # 游戏状态
        self.running = True
        self.paused = False
        self.game_over = False
        self.game_over_reason = ""
        self.game_over_time = 0
        self.current_time = 0
        self.last_update_time = 0

        # 性能监控
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 60

        # 调试模式
        self.debug_mode = False

        print("🐑 小羊吃草生态模拟游戏已启动！")
        print("📖 按 H 查看帮助信息")

    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            # 退出游戏
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # 窗口大小改变事件
            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
                continue

            # 优先让UI处理事件
            if self.ui_manager.handle_event(event):
                continue

            # 让摄像机处理事件
            if self.camera.handle_event(event):
                continue

            # 键盘事件
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self._toggle_pause()
                elif event.key == pygame.K_h:
                    self._show_help()
                elif event.key == pygame.K_r:
                    self._restart_game()
                elif event.key == pygame.K_F3:
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_1:
                    self.ui_manager.selected_animal_type = AnimalType.SHEEP
                elif event.key == pygame.K_2:
                    self.ui_manager.selected_animal_type = AnimalType.RABBIT
                elif event.key == pygame.K_3:
                    self.ui_manager.selected_animal_type = AnimalType.COW

            # 鼠标事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键 - 添加动物
                    self._handle_left_click(event.pos)
                elif event.button == 3:  # 右键 - 查看信息
                    self._handle_right_click(event.pos)
            if self.camera.handle_event(event):
                continue

    def _toggle_pause(self):
        """切换暂停状态"""
        self.paused = not self.paused
        self.ui_manager.paused = self.paused
        print(f"游戏{'暂停' if self.paused else '继续'}")

    def _toggle_fullscreen(self):
        """切换全屏模式"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            # 获取全屏尺寸
            self.current_width, self.current_height = self.screen.get_size()
            print(f"🖥️  切换到全屏模式 ({self.current_width}x{self.current_height})")
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            self.current_width, self.current_height = SCREEN_WIDTH, SCREEN_HEIGHT
            print("🪟 切换到窗口模式")
        
        # 更新摄像机视口
        self.camera.screen_width = self.current_width
        self.camera.screen_height = self.current_height
        
        # 更新UI布局
        self.ui_manager.update_layout(self.current_width, self.current_height)
    
    def _handle_resize(self, width: int, height: int):
        """处理窗口大小改变"""
        self.current_width = width
        self.current_height = height
        self.camera.screen_width = width
        self.camera.screen_height = height
        
        # 更新UI布局
        self.ui_manager.update_layout(width, height)
        print(f"📐 窗口大小调整为: {width}x{height}")

    def _show_help(self):
        """显示帮助信息"""
        help_text = """
🐑 小羊吃草 - 生态模拟游戏 帮助
================================

🎮 控制方式：
  WASD / 方向键  - 移动摄像机
  鼠标滚轮      - 缩放视角
  左键          - 添加选中的动物
  右键          - 查看动物/地块信息
  中键拖拽      - 拖拽移动视角

⌨️  快捷键：
  空格键        - 暂停/继续游戏
  1/2/3        - 快速选择动物类型
  R            - 重新开始游戏
  H            - 显示此帮助
  F3           - 切换调试模式
  F11          - 切换全屏/窗口模式
  ESC          - 退出游戏

🦌 动物特性：
  羊 🐑         - 温和食草，群居动物
  兔子 🐰       - 繁殖快，食量小
  牛 🐄         - 食量大，移动慢
        """
        print(help_text)

    def _restart_game(self):
        """重新开始游戏"""
        print("🔄 重新开始游戏...")
        self.ecosystem = EcoSystem()
        self.camera.reset()
        self.current_time = 0
        self.paused = False
        self.game_over = False
        self.game_over_reason = ""
        self.game_over_time = 0
        self.ui_manager.paused = False
        self.ui_manager.game_over = False
        print("✅ 游戏已重置")

    def _handle_left_click(self, mouse_pos: Tuple[int, int]):
        """处理左键点击 - 添加动物"""
        print(f"🖱️  处理左键点击：{mouse_pos}")

        # 如果游戏结束，不允许添加动物
        if self.game_over:
            print("❌ 游戏已结束，无法添加动物。按 R 重新开始游戏。")
            return

        # 检查是否点击在UI区域（控制面板或统计面板）
        control_panel_area = pygame.Rect(10, 10, 200, 350)
        stats_panel_area = pygame.Rect(self.current_width - 200, 10, 190, 400)

        if (control_panel_area.collidepoint(mouse_pos) or
            stats_panel_area.collidepoint(mouse_pos)):
            print(f"❌ 点击在UI区域内，跳过添加动物")
            return

        # 将屏幕坐标转换为世界坐标
        world_x, world_y = self.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        print(f"🌍 世界坐标：({world_x:.1f}, {world_y:.1f})")

        # 检查是否在地图范围内
        if 0 <= world_x <= MAP_WIDTH and 0 <= world_y <= MAP_HEIGHT:
            print(f"🎯 当前选中动物类型：{self.ui_manager.selected_animal_type}")
            # 添加选中类型的动物
            animals_before = len(self.ecosystem.animals)
            self.ecosystem.add_animal(self.ui_manager.selected_animal_type, int(world_x), int(world_y))
            animals_after = len(self.ecosystem.animals)
            print(f"✅ 在 ({int(world_x)}, {int(world_y)}) 添加了 {self.ui_manager.selected_animal_type.name}")
            print(f"📊 动物数量变化：{animals_before} -> {animals_after}")
        else:
            print(f"❌ 点击位置超出地图范围：MAP_WIDTH={MAP_WIDTH}, MAP_HEIGHT={MAP_HEIGHT}")

    def _handle_right_click(self, mouse_pos: Tuple[int, int]):
        """处理右键点击 - 查看信息"""
        # 将屏幕坐标转换为世界坐标
        world_x, world_y = self.camera.screen_to_world(mouse_pos[0], mouse_pos[1])

        # 查找附近的动物
        nearby_animals = self.ecosystem.get_animals_in_area(int(world_x), int(world_y), 30)

        if nearby_animals:
            animal = nearby_animals[0]  # 取最近的动物
            self._show_animal_info(animal)
        else:
            # 显示地块信息
            grass = self.ecosystem.get_grass_at_position(world_x, world_y)
            if grass:
                self._show_grass_info(grass, world_x, world_y)

    def _show_animal_info(self, animal):
        """显示动物信息"""
        state_names = {
            AnimalState.WANDERING: "游荡",
            AnimalState.SEEKING_FOOD: "觅食",
            AnimalState.EATING: "进食",
            AnimalState.SEEKING_WATER: "找水",
            AnimalState.DRINKING: "饮水",
            AnimalState.RESTING: "休息",
            AnimalState.REPRODUCING: "繁殖"
        }

        type_names = {
            AnimalType.SHEEP: "羊",
            AnimalType.RABBIT: "兔子",
            AnimalType.COW: "牛"
        }

        print(f"\n🔍 动物信息：")
        print(f"种类：{type_names.get(animal.animal_type, '未知')} {animal.animal_type.name}")
        print(f"位置：({animal.x:.0f}, {animal.y:.0f})")
        print(f"状态：{state_names.get(animal.state, '未知')}")
        print(f"健康：{animal.health:.1f}/{animal.max_health}")
        print(f"能量：{animal.energy:.1f}/{animal.max_energy}")
        print(f"饥饿：{animal.hunger:.1f}/100 (阈值: {animal.hunger_threshold})")
        print(f"口渴：{animal.thirst:.1f}/100 (阈值: {animal.thirst_threshold})")
        print(f"疲劳：{animal.tiredness:.1f}/100 (阈值: {animal.tiredness_threshold})")
        print(f"年龄：{animal.age:.1f}天 (寿命: {animal.max_age}天)")
        print(f"速度：{animal.speed:.1f}")
        print(f"体型：{animal.size}")
        print(f"压力水平：{animal.stress_level:.1f}")
        print(f"社交需求：{animal.social_need:.1f}")
        if hasattr(animal, 'reproduction_cooldown'):
            print(f"繁殖冷却：{animal.reproduction_cooldown:.1f}天")

    def _show_grass_info(self, grass, world_x: float, world_y: float):
        """显示草地信息"""
        state_names = {
            GrassState.DEAD: "枯萎",
            GrassState.POOR: "稀疏",
            GrassState.NORMAL: "正常",
            GrassState.RICH: "茂盛"
        }

        print(f"\n🌱 草地信息：")
        print(f"位置：({world_x:.0f}, {world_y:.0f})")
        print(f"状态：{state_names.get(grass.state, '未知')}")
        print(f"状态值：{grass.state.value}/3")
        print(f"营养值：{grass.nutrition:.1f}")
        print(f"生长速度：{grass.growth_rate:.2f}")
        print(f"土壤质量：{grass.soil_quality:.2f}")
        print(f"水分含量：{grass.water_level:.2f}")
        print(f"年龄：{grass.age:.1f}天")
        print(f"抗压能力：{grass.stress_resistance:.2f}")
        print(f"放牧压力：{grass.grazing_pressure:.2f}")
        print(f"再生时间：{grass.regrowth_time/1000:.1f}秒")
        print(f"上次啃食：{(pygame.time.get_ticks() - grass.last_eaten_time)/1000:.1f}秒前")

    def update(self, dt: float):
        """更新游戏状态"""
        # 验证并限制dt值，防止异常的帧时间导致问题
        dt = max(0.001, min(dt, 0.1))  # 限制在1ms到100ms之间

        # 始终更新UI动画，无论游戏状态如何
        self.ui_manager.update(dt)

        if self.paused:
            # 暂停时不更新游戏逻辑，但检查游戏结束状态
            if self.ecosystem.is_ecosystem_collapsed():
                if not self.game_over:
                    self.game_over = True
                    self.game_over_reason = self.ecosystem.get_collapse_reason()
                    self.game_over_time = self.current_time
                    print(f"🏁 游戏结束！{self.game_over_reason}")
                    print("按 R 重新开始游戏，或按 ESC 退出")
            return

        # 游戏结束时停止所有交互，只更新UI显示
        if self.game_over:
            ecosystem_stats = self.ecosystem.get_ecosystem_stats()
            camera_info = self.camera.get_info()
            self.ui_manager.update_stats(ecosystem_stats, camera_info, self.current_time)
            self.ui_manager.update_controls()
            self.ui_manager.paused = self.paused
            self.ui_manager.game_over = self.game_over
            return

        # 正常游戏运行状态
        # 计算有效时间步长
        effective_dt = dt * self.ui_manager.time_acceleration
        self.current_time += int(effective_dt * 1000)

        # 更新摄像机
        self.camera.update(dt, pygame.key.get_pressed())

        # 更新生态系统
        self.ecosystem.update(self.current_time)

        # 检查游戏结束条件（在生态系统更新之后立即检查）
        if not self.game_over and self.ecosystem.is_ecosystem_collapsed():
            self.game_over = True
            self.game_over_reason = self.ecosystem.get_collapse_reason()
            self.game_over_time = self.current_time
            print(f"🏁 游戏结束！{self.game_over_reason}")
            print(f"📊 最终统计 - 动物总数: {len(self.ecosystem.animals)}")
            print("按 R 重新开始游戏，或按 ESC 退出")

        # 更新UI
        ecosystem_stats = self.ecosystem.get_ecosystem_stats()
        camera_info = self.camera.get_info()

        self.ui_manager.update_stats(ecosystem_stats, camera_info, self.current_time)
        self.ui_manager.update_controls()

        # 更新UI管理器状态
        self.ui_manager.paused = self.paused
        self.ui_manager.game_over = self.game_over

    def render(self):
        """渲染游戏画面"""
        try:
            # 清空屏幕 - 使用更自然的天空蓝色背景
            self.screen.fill((135, 206, 235))  # 天空蓝色背景

            # 绘制世界元素（按层次顺序），传入摄像机对象以便正确坐标转换与缩放
            self.ecosystem.draw_grass(self.screen, self.camera)
            self.ecosystem.draw_water(self.screen, self.camera)
            self.ecosystem.draw_obstacles(self.screen, self.camera)
            self.ecosystem.draw_animals(self.screen, self.camera)

            # 绘制调试信息
            if self.debug_mode:
                self._draw_debug_info()

            # 绘制UI（最后绘制，确保在最上层）
            mouse_pos = pygame.mouse.get_pos()
            self.ui_manager.draw(self.screen, mouse_pos)

            # 绘制FPS
            fps_text = f"FPS: {self.current_fps}"
            # 使用中文字体或默认字体
            try:
                if CHINESE_FONT_PATH:
                    font = pygame.font.Font(CHINESE_FONT_PATH, 24)
                else:
                    font = pygame.font.Font(None, 24)
            except:
                font = pygame.font.Font(None, 24)

            fps_surface = font.render(fps_text, True, (255, 255, 255))
            self.screen.blit(fps_surface, (self.current_width - 80, 10))

            # 绘制游戏结束界面
            if self.game_over:
                self._draw_game_over_screen()

            # 刷新显示
            pygame.display.flip()

        except ValueError as e:
            if "invalid color" in str(e).lower():
                print(f"🎨 渲染时颜色错误：{e}")
                # 尝试用基本颜色重新渲染
                try:
                    self.screen.fill((135, 206, 235))
                    pygame.display.flip()
                except:
                    self.screen.fill((0, 0, 0))  # 黑屏作为最后备选
                    pygame.display.flip()
            else:
                raise
        except Exception as e:
            print(f"❌ 渲染错误：{e}")
            # 基本的错误恢复
            try:
                self.screen.fill((0, 0, 0))  # 黑屏
                pygame.display.flip()
            except:
                pass  # 如果连基本渲染都失败，就跳过这一帧

    def _draw_debug_info(self):
        """绘制调试信息"""
        try:
            if CHINESE_FONT_PATH:
                font = pygame.font.Font(CHINESE_FONT_PATH, 24)
            else:
                font = pygame.font.Font(None, 24)
        except:
            font = pygame.font.Font(None, 24)

        y_offset = self.current_height - 120

        debug_info = [
            f"摄像机: ({self.camera.x:.0f}, {self.camera.y:.0f})",
            f"缩放: {self.camera.zoom:.2f}",
            f"动物数: {len(self.ecosystem.animals)}",
            f"时间: {self.current_time/1000:.1f}秒",
            f"生态压力: {self.ecosystem.ecosystem_pressure:.2f}"
        ]

        for i, text in enumerate(debug_info):
            surface = font.render(text, True, (255, 255, 0))
            self.screen.blit(surface, (10, y_offset + i * 20))

    def _draw_game_over_screen(self):
        """绘制游戏结束界面"""
        # 创建半透明覆盖层
        overlay = pygame.Surface((self.current_width, self.current_height))
        overlay.set_alpha(120)  # 降低透明度，让玩家仍能看到游戏世界
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        try:
            if CHINESE_FONT_PATH:
                title_font = pygame.font.Font(CHINESE_FONT_PATH, 48)
                text_font = pygame.font.Font(CHINESE_FONT_PATH, 24)
                small_font = pygame.font.Font(CHINESE_FONT_PATH, 18)
            else:
                title_font = pygame.font.Font(None, 48)
                text_font = pygame.font.Font(None, 24)
                small_font = pygame.font.Font(None, 18)
        except:
            title_font = pygame.font.Font(None, 48)
            text_font = pygame.font.Font(None, 24)
            small_font = pygame.font.Font(None, 18)

        # 判断是真正的游戏结束还是濒危状态
        dead_grass_ratio = self.ecosystem.dead_grass_count / self.ecosystem.total_grass_tiles
        if dead_grass_ratio > 0.95:
            # 真正的游戏结束
            title_text = "🏁 生态系统崩溃！"
            title_color = (255, 100, 100)
            action_text = "按 R 重新开始游戏"
        else:
            # 濒危状态，仍可恢复
            title_text = "⚠️ 生态危机！"
            title_color = (255, 200, 100)
            action_text = "您仍可添加动物重建生态！"

        # 绘制标题
        title_surface = title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(self.current_width // 2, self.current_height // 2 - 100))
        self.screen.blit(title_surface, title_rect)

        # 绘制原因
        reason_surface = text_font.render(self.game_over_reason, True, (255, 255, 255))
        reason_rect = reason_surface.get_rect(center=(self.current_width // 2, self.current_height // 2 - 40))
        self.screen.blit(reason_surface, reason_rect)

        # 绘制存活时间
        survival_time = self.game_over_time / 1000
        time_text = f"生态系统运行时间: {survival_time:.1f} 秒"
        time_surface = text_font.render(time_text, True, (255, 255, 255))
        time_rect = time_surface.get_rect(center=(self.current_width // 2, self.current_height // 2))
        self.screen.blit(time_surface, time_rect)

        # 绘制操作提示
        action_surface = small_font.render(action_text, True, (200, 255, 200))
        action_rect = action_surface.get_rect(center=(self.current_width // 2, self.current_height // 2 + 40))
        self.screen.blit(action_surface, action_rect)

        hint1 = "按 R 重新开始游戏"
        hint2 = "按 ESC 退出游戏"

        hint1_surface = small_font.render(hint1, True, (200, 255, 200))
        hint1_rect = hint1_surface.get_rect(center=(self.current_width // 2, self.current_height // 2 + 70))
        self.screen.blit(hint1_surface, hint1_rect)

        hint2_surface = small_font.render(hint2, True, (255, 200, 200))
        hint2_rect = hint2_surface.get_rect(center=(self.current_width // 2, self.current_height // 2 + 95))
        self.screen.blit(hint2_surface, hint2_rect)

    def _update_fps(self, dt: float):
        """更新FPS计数"""
        self.fps_counter += 1
        self.fps_timer += dt

        if self.fps_timer >= 1.0:  # 每秒更新一次FPS显示
            self.current_fps = int(self.fps_counter / self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = 0

    def run(self):
        """主游戏循环"""
        print("🎮 游戏循环开始...")

        while self.running:
            # 计算帧时间
            dt = self.clock.tick(self.target_fps) / 1000.0  # 转换为秒

            # 更新FPS计数
            self._update_fps(dt)

            # 处理事件
            self.handle_events()

            # 更新游戏逻辑
            self.update(dt)

            # 渲染画面
            self.render()

        print("👋 游戏结束，感谢游玩！")
        pygame.quit()
        sys.exit()

def main():
    """主函数"""
    try:
        game = EcoGrasslandGame()
        game.run()
    except KeyboardInterrupt:
        print("\n👋 游戏被用户中断")
    except ValueError as e:
        if "invalid color" in str(e).lower():
            print(f"🎨 颜色参数错误：{e}")
            print("这通常是由于颜色值超出范围导致的，已优化相关代码")
        else:
            print(f"❌ 数值错误：{e}")
        import traceback
        traceback.print_exc()
    except pygame.error as e:
        print(f"🎮 Pygame错误：{e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ 游戏运行出现错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
