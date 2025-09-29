#!/usr/bin/env python3
"""
Enhanced Character Selection Interface for StreetBattle
统一化角色选择界面 - 修复版本
"""

from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenText, DirectScrolledFrame, OnscreenImage
from panda3d.core import TextNode, Vec4, Texture, PNMImage, TransparencyAttrib, Filename, getModelPath
from direct.task import Task
import math
import random
import json
import os
from pathlib import Path
import sys

# 导入路径修复模块
try:
    from tools.panda3d_path_fixer import safe_load_texture, normalize_path_for_panda3d
except ImportError:
    def safe_load_texture(loader, path_str):
        return loader.loadTexture(str(path_str)) if path_str else None
    def normalize_path_for_panda3d(path_str):
        return str(Path(path_str).as_posix()) if path_str else path_str

from .portrait_manager import PortraitManager
from .ui_asset_manager import UIAssetManager

class EnhancedCharacterSelector:
    """增强版角色选择界面 - 统一化管理"""
    
    def __init__(self, base_app, character_manager):
        self.base_app = base_app
        self.char_manager = character_manager
        self.callback = None
        self.ui_elements = []
        self.selected_character = None
        self.character_buttons = []
        self.character_cards = []
        self.card_lookup = {}
        self.card_portrait_nodes = {}
        self.mode = 'single'
        self.player_number = 1
        self.current_selection_index = 0
        self.all_characters = []
        self.assets_root = os.path.join(os.path.dirname(__file__), 'assets')
        self.portrait_cache = {}
        self.visible = False
        self._nav_bindings: set[str] = set()
        
        # 统一字体配置
        self.fonts = {
            'title': None,
            'body': None,
            'accent': None
        }
        
        # 统一颜色配置
        self.colors = {
            'card_default': (0.15, 0.2, 0.3, 0.85),
            'card_hover': (0.25, 0.35, 0.5, 0.9),
            'card_selected': (0.8, 0.6, 0.2, 0.95),
            'text_normal': (0.9, 0.9, 0.9, 0.9),
            'text_selected': (1.0, 1.0, 1.0, 1.0),
            'preview_bg': (0.1, 0.1, 0.15, 0.8)
        }
        
        # 加载统一角色列表
        self.unified_characters = self._load_unified_character_list()
        
        # 初始化UI组件
        self._initialize_ui()
    
    def _load_unified_character_list(self):
        """加载统一角色列表"""
        try:
            unified_list_path = os.path.join(os.path.dirname(self.assets_root), 'assets', 'unified_character_list.json')
            if os.path.exists(unified_list_path):
                with open(unified_list_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✓ 加载统一角色列表: {len(data)} 个角色")
                    return data
            else:
                print("⚠️ 统一角色列表不存在，使用空列表")
                return {}
        except Exception as e:
            print(f"❌ 加载统一角色列表失败: {e}")
            return {}
    
    def _initialize_ui(self):
        """初始化UI界面"""
        # 主框架
        self.main_frame = DirectFrame(
            parent=self.base_app.aspect2d,
            frameColor=(0, 0, 0, 0),
            frameSize=(-2, 2, -1.5, 1.5),
            pos=(0, 0, 0)
        )
        self.main_frame.hide()
        self.ui_elements.append(self.main_frame)
        
        # 背景
        self.background = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.05, 0.05, 0.1, 0.95),
            frameSize=(-2, 2, -1.5, 1.5),
            relief=0
        )
        
        # 标题
        self.title_text = OnscreenText(
            text="选择你的战士 - Choose Your Fighter",
            parent=self.main_frame,
            pos=(0, 1.35),
            scale=0.08,
            fg=self.colors['text_normal'],
            align=TextNode.ACenter,
            font=self.fonts.get('title')
        )
        
        # 角色网格区域（去除滚动框）
        self.grid_container = DirectFrame(
            parent=self.main_frame,
            frameColor=(0, 0, 0, 0),
            frameSize=(-1.8, 0.8, -1.2, 1.2),
            pos=(0, 0, 0),
            relief=0
        )
        
        # 角色预览区域
        self.preview_container = DirectFrame(
            parent=self.main_frame,
            frameColor=self.colors['preview_bg'],
            frameSize=(0.9, 1.9, -1.2, 1.2),
            pos=(0, 0, 0),
            relief=1
        )
        
        # 预览标题
        self.preview_title = OnscreenText(
            text="角色预览",
            parent=self.preview_container,
            pos=(1.4, 1.0),
            scale=0.05,
            fg=self.colors['text_normal'],
            align=TextNode.ACenter
        )
        
        # 预览图像
        self.preview_image = OnscreenImage(
            parent=self.preview_container,
            pos=(1.4, 0, 0.3),
            scale=(0.35, 1, 0.35)
        )
        self.preview_image.setTransparency(TransparencyAttrib.MAlpha)
        
        # 预览信息文本
        self.preview_info = OnscreenText(
            text="请选择一个角色",
            parent=self.preview_container,
            pos=(1.4, -0.3),
            scale=0.04,
            fg=self.colors['text_normal'],
            align=TextNode.ACenter,
            wordwrap=20
        )
        
        # 创建角色按钮
        self._create_character_grid()
    
    def _create_character_grid(self):
        """创建角色网格（自适应布局，无滚动条）"""
        # 获取可用角色列表
        available_characters = []
        
        for char_id, char_info in self.unified_characters.items():
            if char_info.get('has_portrait', False):
                available_characters.append({
                    'id': char_id,
                    'display_name': char_info.get('display_name', char_id.title()),
                    'portrait_path': char_info.get('portrait_path', ''),
                    'sprite_path': char_info.get('sprite_path', ''),
                    'has_sprite': char_info.get('has_sprite', False)
                })
        
        if not available_characters:
            print("❌ 没有可用角色")
            return
        
        self.all_characters = available_characters
        total_chars = len(available_characters)
        
        # 计算网格布局（自适应）
        cols = min(6, max(1, int(math.sqrt(total_chars * 1.5))))
        rows = math.ceil(total_chars / cols)
        
        # 计算按钮尺寸和间距
        grid_width = 2.6  # 网格区域宽度
        grid_height = 2.2  # 网格区域高度
        
        button_width = (grid_width - 0.1) / cols - 0.05
        button_height = (grid_height - 0.1) / rows - 0.05
        
        # 确保按钮不会太小或太大
        button_width = max(0.25, min(0.4, button_width))
        button_height = max(0.3, min(0.4, button_height))
        
        spacing_x = button_width + 0.05
        spacing_y = button_height + 0.05
        
        # 计算起始位置（居中）
        total_grid_width = (cols - 1) * spacing_x
        total_grid_height = (rows - 1) * spacing_y
        
        start_x = -total_grid_width / 2
        start_y = total_grid_height / 2
        
        # 创建角色按钮
        for idx, char_data in enumerate(available_characters):
            row = idx // cols
            col = idx % cols
            
            x = start_x + col * spacing_x
            y = start_y - row * spacing_y
            
            self._create_character_button(char_data, x, y, button_width, button_height)
        
        print(f"✓ 创建 {total_chars} 个角色按钮，布局: {cols}x{rows}")
    
    def _create_character_button(self, char_data, x, y, width, height):
        """创建单个角色按钮"""
        char_id = char_data['id']
        display_name = char_data['display_name']
        
        # 按钮容器
        button_frame = DirectFrame(
            parent=self.grid_container,
            frameColor=self.colors['card_default'],
            frameSize=(-width/2, width/2, -height/2, height/2),
            pos=(x, 0, y),
            relief=1
        )
        button_frame.setTransparency(TransparencyAttrib.MAlpha)
        
        # 角色头像
        portrait_texture = self._load_character_portrait(char_data)
        if portrait_texture:
            portrait_image = OnscreenImage(
                image=portrait_texture,
                parent=button_frame,
                pos=(0, 0, height * 0.1),
                scale=(width * 0.8, 1, height * 0.6)
            )
            portrait_image.setTransparency(TransparencyAttrib.MAlpha)
        
        # 角色名称
        name_text = OnscreenText(
            text=display_name,
            parent=button_frame,
            pos=(0, -height/2 + 0.05),
            scale=min(0.04, width * 0.08),
            fg=self.colors['text_normal'],
            align=TextNode.ACenter,
            wordwrap=max(10, int(len(display_name) * 0.8))
        )
        
        # 点击按钮
        click_button = DirectButton(
            parent=button_frame,
            frameColor=(0, 0, 0, 0),
            frameSize=(-width/2, width/2, -height/2, height/2),
            relief=0,
            command=self._on_character_selected,
            extraArgs=[char_data]
        )
        
        # 鼠标悬停效果
        def on_enter(event=None):
            button_frame['frameColor'] = self.colors['card_hover']
            self._preview_character(char_data)
        
        def on_exit(event=None):
            if self.selected_character != char_id:
                button_frame['frameColor'] = self.colors['card_default']
        
        click_button.bind("DGG.WITHIN", on_enter)
        click_button.bind("DGG.WITHOUT", on_exit)
        
        # 存储引用
        self.character_buttons.append({
            'char_id': char_id,
            'button': click_button,
            'frame': button_frame,
            'data': char_data
        })
        
        self.card_lookup[char_id] = button_frame
        self.ui_elements.extend([button_frame, click_button])
    
    def _load_character_portrait(self, char_data):
        """加载角色头像"""
        char_id = char_data['id']
        
        # 检查缓存
        if char_id in self.portrait_cache:
            return self.portrait_cache[char_id]
        
        # 尝试从统一路径加载
        portrait_path = char_data.get('portrait_path', '')
        if portrait_path:
            full_path = os.path.join(os.path.dirname(self.assets_root), portrait_path)
            if os.path.exists(full_path):
                try:
                    texture = safe_load_texture(self.base_app.loader, full_path)
                    if texture:
                        self.portrait_cache[char_id] = texture
                        return texture
                except Exception as e:
                    print(f"Failed to load portrait {full_path}: {e}")
        
        # 尝试从标准路径加载
        standard_paths = [
            f"assets/images/portraits/{char_id}.png",
            f"assets/portraits/{char_id}.png",
            f"portraits/{char_id}.png"
        ]
        
        for path in standard_paths:
            full_path = os.path.join(os.path.dirname(self.assets_root), path)
            if os.path.exists(full_path):
                try:
                    texture = safe_load_texture(self.base_app.loader, full_path)
                    if texture:
                        self.portrait_cache[char_id] = texture
                        return texture
                except Exception as e:
                    continue
        
        print(f"⚠️ 无法加载角色头像: {char_id}")
        return None
    
    def _preview_character(self, char_data):
        """预览角色信息"""
        char_id = char_data['id']
        display_name = char_data['display_name']
        
        # 更新预览图像
        portrait_texture = self._load_character_portrait(char_data)
        if portrait_texture:
            self.preview_image['image'] = portrait_texture
            self.preview_image.show()
        else:
            self.preview_image.hide()
        
        # 更新预览信息
        info_text = f"{display_name}\n\n"
        info_text += f"角色ID: {char_id}\n"
        info_text += f"头像: {'✓' if char_data.get('portrait_path') else '✗'}\n"
        info_text += f"精灵: {'✓' if char_data.get('has_sprite') else '✗'}\n"
        
        self.preview_info['text'] = info_text
    
    def _on_character_selected(self, char_data):
        """角色选择处理"""
        char_id = char_data['id']
        
        print(f"🎯 选择角色: {char_data['display_name']} ({char_id})")
        
        # 更新选中状态
        for btn_data in self.character_buttons:
            if btn_data['char_id'] == char_id:
                btn_data['frame']['frameColor'] = self.colors['card_selected']
            else:
                btn_data['frame']['frameColor'] = self.colors['card_default']
        
        self.selected_character = char_id
        
        # 更新预览
        self._preview_character(char_data)
        
        # 调用回调
        if self.callback:
            try:
                self.callback(char_id)
            except Exception as e:
                print(f"Character selection callback error: {e}")
    
    def show(self, callback=None):
        """显示角色选择界面"""
        self.callback = callback
        self.main_frame.show()
        self.visible = True
        print("✓ 角色选择界面已显示")
    
    def hide(self):
        """隐藏角色选择界面"""
        self.main_frame.hide()
        self.visible = False
        print("✓ 角色选择界面已隐藏")
    
    def cleanup(self):
        """清理资源"""
        for element in self.ui_elements:
            try:
                element.destroy()
            except:
                pass
        
        self.ui_elements.clear()
        self.character_buttons.clear()
        self.card_lookup.clear()
        self.portrait_cache.clear()
        
        print("✓ 角色选择器资源已清理")

