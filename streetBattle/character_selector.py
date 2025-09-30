#!/usr/bin/env python3
"""
Enhanced Character Selection Interface for StreetBattle
统一化角色选择界面 - 修复版本
"""

from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenText, DirectScrolledFrame, OnscreenImage
from panda3d.core import (
    TextNode,
    Vec4,
    Vec3,
    Texture,
    PNMImage,
    TransparencyAttrib,
    Filename,
    getModelPath,
    AmbientLight,
    DirectionalLight,
    NodePath,
    CardMaker,
)
from direct.task import Task
import importlib
import math
import random
import json
import os
from pathlib import Path
import sys

# 导入路径修复模块（动态检测以避免开发环境缺失导致错误）
_path_fixer_module = None
try:
    _path_fixer_module = importlib.import_module(
        "gamecenter.streetBattle.tools.panda3d_path_fixer"
    )
except ModuleNotFoundError:
    _path_fixer_module = None


def safe_load_texture(loader, path_str):
    if _path_fixer_module and hasattr(_path_fixer_module, "safe_load_texture"):
        return _path_fixer_module.safe_load_texture(loader, path_str)
    return loader.loadTexture(str(path_str)) if path_str else None


def normalize_path_for_panda3d(path_str):
    if _path_fixer_module and hasattr(_path_fixer_module, "normalize_path_for_panda3d"):
        return _path_fixer_module.normalize_path_for_panda3d(path_str)
    return str(Path(path_str).as_posix()) if path_str else path_str

from gamecenter.streetBattle.portrait_manager import PortraitManager
from gamecenter.streetBattle.ui_asset_manager import UIAssetManager

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
        selector_root = Path(__file__).resolve().parent
        self.assets_root_path = selector_root / 'assets'
        self.assets_root = str(self.assets_root_path)
        self.config_root = os.path.join(selector_root, 'config')
        self.characters_config_root = os.path.join(self.config_root, 'characters')
        self.portrait_cache = {}
        self.visible = False
        self._nav_bindings: set[str] = set()
        self._placeholder_portrait_texture: Texture | None = None

        try:
            self.portrait_manager: PortraitManager | None = PortraitManager(
                self.base_app.loader,
                self.assets_root_path
            )
        except Exception as portrait_manager_error:
            print(f"⚠️ Portrait manager unavailable: {portrait_manager_error}")
            self.portrait_manager = None

        # 3D preview rendering resources
        self.preview_buffer = None
        self.preview_texture: Texture | None = None
        self.preview_render: NodePath | None = None
        self.preview_camera = None
        self.preview_ground = None
        self.preview_model = None
        self.preview_model_owned = False
        self.preview_model_cache: dict[str, NodePath | None] = {}
        self.preview_character_id: str | None = None
        self.preview_lights: list[NodePath] = []
        
        # 统一字体配置
        self.fonts = {
            'title': None,
            'body': None,
            'accent': None
        }
        
        # 统一颜色配置
        self.colors = {
            'card_default': (0.08, 0.12, 0.18, 0.92),
            'card_hover': (0.18, 0.26, 0.38, 0.95),
            'card_selected': (0.82, 0.58, 0.24, 0.98),
            'text_normal': (0.93, 0.95, 0.98, 0.98),
            'text_selected': (1.0, 1.0, 1.0, 1.0),
            'preview_bg': (0.05, 0.07, 0.12, 0.9),
            'grid_bg': (0, 0, 0, 0)
        }
        
        # 加载统一角色列表
        self.unified_characters = self._load_unified_character_list()
        
        # 初始化3D预览渲染（在构建UI之前，以便将纹理绑定到UI元素）
        self._setup_preview_renderer()

        # 初始化UI组件
        print("[CharacterSelector] Initializing UI components...")
        self._initialize_ui()
    
    def _is_valid_node(self, node):
        """Safely determine whether a Panda3D node is valid."""
        try:
            return bool(node) and hasattr(node, "isEmpty") and not node.isEmpty()
        except Exception:
            return False

    def _get_placeholder_portrait_texture(self) -> Texture | None:
        """生成或返回通用占位头像纹理，避免节点创建失败"""
        if self._placeholder_portrait_texture:
            return self._placeholder_portrait_texture

        try:
            placeholder_image = PNMImage(4, 4)
            placeholder_image.fill(0.2, 0.2, 0.25)

            # 添加简单边框以突出占位符
            border_color = (0.5, 0.5, 0.6)
            for x in range(4):
                placeholder_image.setXel(x, 0, *border_color)
                placeholder_image.setXel(x, 3, *border_color)
            for y in range(4):
                placeholder_image.setXel(0, y, *border_color)
                placeholder_image.setXel(3, y, *border_color)

            texture = Texture("placeholder_portrait")
            texture.load(placeholder_image)
            self._placeholder_portrait_texture = texture
            return texture
        except Exception as error:
            print(f"⚠️ 无法生成占位头像纹理: {error}")
            return None

    def _load_unified_character_list(self):
        """加载统一角色列表"""
        def _list_to_dict(payload):
            if isinstance(payload, dict):
                return payload
            result = {}
            if isinstance(payload, list):
                for entry in payload:
                    if not isinstance(entry, dict):
                        continue
                    char_id = entry.get('id') or entry.get('name')
                    if not char_id:
                        continue
                    result[char_id] = entry
            return result

        try:
            candidate_paths = [
                os.path.join(self.characters_config_root, 'unified_roster.json'),
                os.path.join(self.characters_config_root, 'manifest.json'),
                os.path.join(os.path.dirname(self.assets_root), 'assets', 'unified_character_list.json'),
            ]
            
            print(f"[CharacterSelector] 搜索角色配置文件...")
            for path in candidate_paths:
                print(f"  检查: {path}")
                if not os.path.exists(path):
                    print(f"    ❌ 文件不存在")
                    continue
                    
                print(f"    ✓ 文件存在，尝试加载...")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict) and 'characters' in data:
                        data = data['characters']
                    roster = _list_to_dict(data)
                    if roster:
                        print(f"✓ 加载统一角色列表: {len(roster)} 个角色 ({os.path.basename(path)})")
                        # 输出前3个角色作为调试信息
                        sample_chars = list(roster.keys())[:3]
                        print(f"  示例角色: {', '.join(sample_chars)}")
                        return roster
                    else:
                        print(f"    ⚠️ 文件加载成功但没有有效角色数据")
                except Exception as load_error:
                    print(f"    ❌ 加载失败: {load_error}")
                    
            print("❌ 所有候选路径都未找到有效的角色配置文件")
            print("Warning: No roster configuration found. Only characters with portraits will be available.")
            return {}
        except Exception as e:
            print(f"❌ 加载统一角色列表失败: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _setup_preview_renderer(self):
        """Create an offscreen renderer for real 3D character previews."""
        try:
            buffer = self.base_app.win.makeTextureBuffer("selector_character_preview", 512, 512)
            if not buffer:
                raise RuntimeError("Texture buffer creation returned None")

            buffer.setClearColor((0.05, 0.05, 0.08, 1))
            self.preview_buffer = buffer
            self.preview_texture = buffer.getTexture()

            # Dedicated scene graph for previews to avoid leaking into the main render tree
            self.preview_render = NodePath("selector_preview_root")

            # Camera configured for hero-shot framing
            self.preview_camera = self.base_app.makeCamera(buffer, scene=self.preview_render)
            self.preview_camera.reparentTo(self.preview_render)
            lens = self.preview_camera.node().getLens()
            lens.setNearFar(0.1, 200.0)
            lens.setFov(36)
            self.preview_camera.setPos(0, -6.5, 2.5)
            self.preview_camera.lookAt(0, 0, 1.2)

            # Soft ambient light
            ambient = AmbientLight('selector_preview_ambient')
            ambient.setColor(Vec4(0.55, 0.55, 0.6, 1))
            ambient_np = self.preview_render.attachNewNode(ambient)
            self.preview_render.setLight(ambient_np)
            self.preview_lights.append(ambient_np)

            # Key directional light for dramatic highlights
            key_light = DirectionalLight('selector_preview_key')
            key_light.setColor(Vec4(0.9, 0.9, 0.85, 1))
            key_np = self.preview_render.attachNewNode(key_light)
            key_np.setHpr(-35, -25, 0)
            self.preview_render.setLight(key_np)
            self.preview_lights.append(key_np)

            # Rim light for silhouette definition
            rim_light = DirectionalLight('selector_preview_rim')
            rim_light.setColor(Vec4(0.4, 0.4, 0.5, 1))
            rim_np = self.preview_render.attachNewNode(rim_light)
            rim_np.setHpr(160, -15, 0)
            self.preview_render.setLight(rim_np)
            self.preview_lights.append(rim_np)

            # Minimal ground plane to capture shadows and ground the character
            ground = CardMaker('selector_preview_ground')
            ground.setFrame(-3, 3, -3, 3)
            self.preview_ground = self.preview_render.attachNewNode(ground.generate())
            self.preview_ground.setHpr(0, -90, 0)
            self.preview_ground.setPos(0, 0, 0)
            self.preview_ground.setColor(0.12, 0.12, 0.18, 1)
            self.preview_ground.setTransparency(TransparencyAttrib.MAlpha)

            print("[CharacterSelector] 3D preview renderer initialized")
        except Exception as exc:
            print(f"⚠️ 无法创建3D预览渲染器: {exc}")
            self.preview_buffer = None
            self.preview_texture = None
            self.preview_render = None
            self.preview_camera = None
            self.preview_ground = None
            self.preview_model = None
            self.preview_lights = []
    
    def _initialize_ui(self):
        """初始化UI界面"""
        # 主框架
        print("[CharacterSelector] Creating main frame...")
        self.main_frame = DirectFrame(
            parent=self.base_app.aspect2d,
            frameColor=(0, 0, 0, 0),
            frameSize=(-2, 2, -1.5, 1.5),
            pos=(0, 0, 0)
        )
        print("[CharacterSelector] Main frame created")
        self.main_frame.hide()
        self.ui_elements.append(self.main_frame)
        
        # 背景
        print("[CharacterSelector] Creating background frame...")
        self.background = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.05, 0.05, 0.1, 0.95),
            frameSize=(-2, 2, -1.5, 1.5),
            relief=0
        )
        print("[CharacterSelector] Background frame created")
        
        # 标题
        print("[CharacterSelector] Creating title text...")
        self.title_text = OnscreenText(
            text="Choose Your Fighter",
            parent=self.main_frame,
            pos=(0, 1.35),
            scale=0.08,
            fg=self.colors['text_normal'],
            align=TextNode.ACenter,
            font=self.fonts.get('title')
        )
        print("[CharacterSelector] Title text created")
        
        # 🎮 显示当前渲染模式
        current_mode = "3D"  # 默认
        if hasattr(self.base_app, 'settings_manager') and self.base_app.settings_manager:
            mode_setting = self.base_app.settings_manager.get("preferred_version", "3d")
            current_mode = mode_setting.upper()
        
        self.mode_indicator = OnscreenText(
            text=f"Mode: {current_mode}",
            parent=self.main_frame,
            pos=(0, 1.20),
            scale=0.05,
            fg=(1, 0.8, 0.2, 1) if current_mode == "2.5D" else (0.7, 0.9, 1, 1),
            align=TextNode.ACenter
        )
        print(f"[CharacterSelector] Mode indicator created: {current_mode}")
        
        # 角色网格区域（去除滚动框）
        print("[CharacterSelector] Creating grid container...")
        self.grid_container = DirectFrame(
            parent=self.main_frame,
            frameColor=self.colors['grid_bg'],
            frameSize=(-1.8, 0.5, -1.2, 1.2),  # 右侧边界调整为0.5，符合测试要求
            pos=(0, 0, 0),
            relief=0
        )
        print("[CharacterSelector] Grid container created")
        self.grid_container.setPos(-0.12, 0, 0)
        
        # 角色预览区域
        print("[CharacterSelector] Creating preview container...")
        self.preview_container = DirectFrame(
            parent=self.main_frame,
            frameColor=self.colors['preview_bg'],
            frameSize=(0.9, 1.9, -1.2, 1.2),
            pos=(0, 0, 0),
            relief=1
        )
        print("[CharacterSelector] Preview container created")
        self.preview_container.setTransparency(TransparencyAttrib.MAlpha)
        
        # 预览标题
        print("[CharacterSelector] Creating preview title...")
        self.preview_title = OnscreenText(
            text="Fighter Spotlight",
            parent=self.preview_container,
            pos=(1.4, 1.0),
            scale=0.05,
            fg=self.colors['text_normal'],
            align=TextNode.ACenter
        )
        print("[CharacterSelector] Preview title created")
        
        # 预览图像
        print("[CharacterSelector] Creating preview image...")
        placeholder_texture = self._get_placeholder_portrait_texture()
        onscreen_kwargs = {
            'parent': self.preview_container,
            'pos': (1.4, 0, 0.3),
            'scale': (0.35, 1, 0.35)
        }
        if self.preview_texture:
            onscreen_kwargs['image'] = self.preview_texture
        elif placeholder_texture:
            onscreen_kwargs['image'] = placeholder_texture

        self.preview_image = OnscreenImage(**onscreen_kwargs)
        print("[CharacterSelector] Preview image created")
        if self._is_valid_node(self.preview_image):
            self.preview_image.setTransparency(TransparencyAttrib.MAlpha)
            if not self.preview_texture:
                self.preview_image.hide()
        else:
            print("⚠️ Preview image node invalid; disabling preview sprite")
            self.preview_image = None
        
        # 预览信息文本
        print("[CharacterSelector] Creating preview info text...")
        self.preview_info = OnscreenText(
            text="Select a fighter to preview",
            parent=self.preview_container,
            pos=(1.4, -0.3),
            scale=0.04,
            fg=self.colors['text_normal'],
            align=TextNode.ACenter,
            wordwrap=20
        )
        print("[CharacterSelector] Preview info text created")
        
        # 创建角色按钮
        print("[CharacterSelector] Building character grid...")
        self._create_character_grid()
        print("[CharacterSelector] Character grid initialization complete")
    
    def _create_character_grid(self):
        """创建角色网格（自适应布局，无滚动条）"""
        # 获取可用角色列表
        available_characters = []
        
        # ✅ 优先从settings_manager获取渲染模式，确保正确读取
        preferred_mode = "3d"  # 默认为3D模式
        if hasattr(self.base_app, 'settings_manager') and self.base_app.settings_manager:
            preferred_mode = self.base_app.settings_manager.get("preferred_version", "3d")
            print(f"[CharacterSelector] 从settings_manager读取渲染模式: {preferred_mode}")
        else:
            print(f"[CharacterSelector] settings_manager不可用，使用默认模式: {preferred_mode}")
        
        print(f"[CharacterSelector] 当前渲染模式: {preferred_mode}")
        print(f"[CharacterSelector] 可用角色总数: {len(self.unified_characters)}")
        
        for char_id, char_info in self.unified_characters.items():
            # ✅ 跳过disabled角色（NodePath模型）
            if char_info.get('disabled', False):
                disabled_reason = char_info.get('disabled_reason', 'No reason provided')
                print(f"[CharacterSelector] 跳过禁用角色: {char_info.get('display_name', char_id)} - {disabled_reason}")
                continue
            
            # ✅ 根据渲染模式决定是否跳过角色
            if preferred_mode == "3d":
                # 3D模式下需要有3D模型
                if not char_info.get('has_3d_model', True):
                    print(f"[CharacterSelector] 跳过无3D模型的角色: {char_info.get('display_name', char_id)}")
                    continue
            elif preferred_mode == "2.5d":
                # 2.5D模式下需要有精灵资源
                if not char_info.get('has_sprite', False):
                    print(f"[CharacterSelector] 跳过无精灵资源的角色: {char_info.get('display_name', char_id)}")
                    continue
            
            # ✅ 检查是否有头像（用于显示在选择界面）
            has_portrait = char_info.get('has_portrait')
            if has_portrait is None:
                has_portrait = bool(char_info.get('portrait_path'))
            
            if has_portrait:
                available_characters.append({
                    'id': char_id,
                    'display_name': char_info.get('display_name') or char_info.get('name') or char_id.replace('_', ' ').title(),
                    'portrait_path': char_info.get('portrait_path', ''),
                    'sprite_path': char_info.get('sprite_path', ''),
                    'has_sprite': char_info.get('has_sprite', False),
                    'has_3d_model': char_info.get('has_3d_model', False)
                })
            else:
                print(f"[CharacterSelector] 跳过无头像的角色: {char_info.get('display_name', char_id)}")
        
        if not available_characters:
            print("❌ 没有可用角色")
            print(f"   渲染模式: {preferred_mode}")
            print(f"   总角色数: {len(self.unified_characters)}")
            print(f"   请检查角色配置文件中的 has_3d_model/has_sprite 和 has_portrait 字段")
            return
        
        self.all_characters = available_characters
        total_chars = len(available_characters)
        print(f"✓ 找到 {total_chars} 个可用角色（{preferred_mode}模式）")
        
        # 固定网格布局: 每行 8 列，保证竞技场风格的一致性
        cols = min(8, max(1, total_chars))
        rows = math.ceil(total_chars / cols)

        grid_width = 1.4
        grid_height = 2.25

        # 依据固定间距重新计算按钮尺寸，保持舒适点击区域
        horizontal_gap = 0.05
        vertical_gap = 0.06
        button_width = (grid_width - horizontal_gap * (cols - 1)) / cols
        button_height = (grid_height - vertical_gap * (rows - 1)) / rows

        button_width = max(0.14, min(0.28, button_width))
        button_height = max(0.26, min(0.38, button_height))

        spacing_x = button_width + horizontal_gap
        spacing_y = button_height + vertical_gap

        total_grid_width = (cols - 1) * spacing_x
        total_grid_height = (rows - 1) * spacing_y

        # 将网格向左微调，确保右侧留出UI空间并适配0.5边界
        right_margin_target = 0.48
        offset_x = max(0.0, (total_grid_width / 2) + (button_width / 2) - right_margin_target)
        start_x = -total_grid_width / 2 - offset_x
        start_y = total_grid_height / 2

        button_right_edge = start_x + (cols - 1) * spacing_x + button_width / 2

        print(f"Grid layout locked to {cols} columns × {rows} rows")
        print(f"Button size: {button_width:.3f} × {button_height:.3f}, right edge: {button_right_edge:.3f}")
        
        # 创建角色按钮
        for idx, char_data in enumerate(available_characters):
            row = idx // cols
            col = idx % cols
            
            x = start_x + col * spacing_x
            y = start_y - row * spacing_y
            
            self._create_character_button(char_data, x, y, button_width, button_height)
        
        print(f"✓ Built {total_chars} character buttons in layout {cols}x{rows}")
        print(f"Grid width: {grid_width:.2f}, button width: {button_width:.3f}, spacing: {spacing_x:.3f}")
    
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

        accent_bar = DirectFrame(
            parent=button_frame,
            frameColor=(1, 1, 1, 0.08),
            frameSize=(-width/2, width/2, height/2 - 0.08, height/2),
            relief=0
        )
        self.ui_elements.append(accent_bar)
        
        # 角色头像
        portrait_texture = self._load_character_portrait(char_data)
        if portrait_texture:
            portrait_image = OnscreenImage(
                image=portrait_texture,
                parent=button_frame,
                pos=(0, 0, height * 0.1),
                scale=(width * 0.8, 1, height * 0.6)
            )
            if self._is_valid_node(portrait_image):
                portrait_image.setTransparency(TransparencyAttrib.MAlpha)
                self.ui_elements.append(portrait_image)
            else:
                portrait_image = None
                print(f"⚠️ 无法为 {display_name} 创建头像节点")
        
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
            accent_bar['frameColor'] = (1, 1, 1, 0.18)
            self._preview_character(char_data)
        
        def on_exit(event=None):
            if self.selected_character != char_id:
                button_frame['frameColor'] = self.colors['card_default']
                accent_bar['frameColor'] = (1, 1, 1, 0.08)
        
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
        """加载角色头像，并确保跨平台路径兼容"""
        char_id = char_data['id']

        if char_id in self.portrait_cache:
            return self.portrait_cache[char_id]

        profile_payload = dict(self.unified_characters.get(char_id, {}))
        portrait_rel = profile_payload.get('portrait_path') or char_data.get('portrait_path')

        if portrait_rel:
            portrait_candidate = (self.assets_root_path.parent / portrait_rel).resolve()
            profile_payload['portrait_local'] = str(portrait_candidate)

        def _fallback_texture_factory() -> Texture:
            placeholder = self._get_placeholder_portrait_texture()
            if placeholder:
                return placeholder

            fallback_img = PNMImage(2, 2)
            fallback_img.fill(0.2, 0.2, 0.25)
            fallback_tex = Texture("fallback_portrait")
            fallback_tex.load(fallback_img)
            return fallback_tex

        texture: Texture | None = None

        try:
            if self.portrait_manager:
                texture = self.portrait_manager.get_texture(
                    char_id,
                    profile_payload,
                    _fallback_texture_factory
                )
        except Exception as exc:
            print(f"⚠️ Portrait manager error for {char_id}: {exc}")
            texture = None

        if texture is None and portrait_rel:
            direct_path = (self.assets_root_path.parent / portrait_rel).resolve()
            if direct_path.exists():
                try:
                    panda_filename = Filename.fromOsSpecific(str(direct_path))
                    panda_filename.makeCanonical()
                    texture = self.base_app.loader.loadTexture(panda_filename)
                except Exception as exc:
                    print(f"⚠️ Fallback portrait load failed for {char_id}: {exc}")

        if texture is None:
            texture = _fallback_texture_factory()

        if texture:
            try:
                texture.setMinfilter(Texture.FTLinearMipmapLinear)
                texture.setMagfilter(Texture.FTLinear)
            except Exception:
                pass
            self.portrait_cache[char_id] = texture
            return texture

        print(f"⚠️ Unable to resolve portrait for {char_id}")
        return None

    def _clear_preview_model(self):
        """移除当前的3D预览模型"""
        if self.preview_model:
            try:
                if self.preview_model_owned and hasattr(self.preview_model, 'cleanup'):
                    self.preview_model.cleanup()
            except Exception:
                pass
            try:
                if self.preview_model_owned:
                    self.preview_model.removeNode()
                else:
                    self.preview_model.detachNode()
            except Exception:
                pass
        self.preview_model = None
        self.preview_character_id = None
        self.preview_model_owned = False

    def _fit_preview_model(self, node: NodePath):
        """根据模型包围盒调整缩放和位置，使其适合预览镜头"""
        try:
            bounds = node.getTightBounds()
            if not bounds:
                return
            min_pt, max_pt = bounds
            size_vec = max_pt - min_pt
            max_dim = max(size_vec.x, size_vec.y, size_vec.z, 0.01)
            scale = 2.2 / max_dim
            node.setScale(scale)

            # Center model vertically based on bounds
            center = (min_pt + max_pt) * 0.5
            node.setPos(-center.x * scale, -center.y * scale, -center.z * scale)
        except Exception as exc:
            print(f"⚠️ 预览模型缩放失败: {exc}")
            node.setScale(0.4)

    def _update_preview_model(self, char_data):
        """在预览窗口中展示真实的3D角色模型"""
        if not self.preview_render or not self.preview_texture:
            return

        char_id = char_data.get('id')
        if not char_id:
            return

        # 避免重复加载相同角色
        if self.preview_character_id == char_id and self.preview_model:
            return

        cached_model = self.preview_model_cache.get(char_id)
        if cached_model is None and char_id not in self.preview_model_cache:
            try:
                model = self.char_manager.create_enhanced_character_model(char_id, Vec3(0, 0, 0)) if self.char_manager else None
            except Exception as exc:
                print(f"⚠️ 预览模型加载失败 ({char_id}): {exc}")
                model = None

            if model and hasattr(model, 'detachNode'):
                try:
                    model.detachNode()
                except Exception:
                    pass

            if model and hasattr(model, 'copyTo'):
                # 缓存原始模型，预览实例使用 copyTo 防止破坏原始数据
                self.preview_model_cache[char_id] = model
                cached_model = model
            else:
                self.preview_model_cache[char_id] = model
                cached_model = model

        self._clear_preview_model()

        if not cached_model:
            print(f"⚠️ 没有可用的3D资源用于预览: {char_id}")
            return

        try:
            if hasattr(cached_model, 'copyTo'):
                preview_instance = cached_model.copyTo(self.preview_render)
                self.preview_model_owned = True
            else:
                preview_instance = cached_model
                preview_instance.reparentTo(self.preview_render)
                self.preview_model_owned = False

            preview_instance.setHpr(20, 0, 0)
            self._fit_preview_model(preview_instance)
            self.preview_model = preview_instance
            self.preview_character_id = char_id

            if self.preview_image and self._is_valid_node(self.preview_image):
                self.preview_image.show()
        except Exception as exc:
            print(f"⚠️ 创建预览实例失败: {exc}")
            self._clear_preview_model()
    
    def _preview_character(self, char_data):
        """预览角色信息"""
        char_id = char_data['id']
        display_name = char_data['display_name']
        
        # 更新预览图像
        if not self.preview_texture:
            portrait_texture = self._load_character_portrait(char_data)
            if portrait_texture and self.preview_image and self._is_valid_node(self.preview_image):
                self.preview_image['image'] = portrait_texture
                self.preview_image.show()
            elif self.preview_image and self._is_valid_node(self.preview_image):
                self.preview_image.hide()
        
        # 更新预览信息
        info_text = f"{display_name}\n\n"
        info_text += f"Character ID: {char_id}\n"
        info_text += f"Portrait: {'✓' if char_data.get('portrait_path') else '✗'}\n"
        info_text += f"Sprites: {'✓' if char_data.get('has_sprite') else '✗'}\n"

        self.preview_info['text'] = info_text

        # 刷新3D预览
        self._update_preview_model(char_data)
    
    def _on_character_selected(self, char_data):
        """角色选择处理"""
        char_id = char_data['id']
        
        print(f"🎯 Selected fighter: {char_data['display_name']} ({char_id})")
        
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
    
    def show(self, callback=None, mode: str | None = None, player_number: int = 1):
        """显示角色选择界面并根据模式定制体验"""
        self.callback = callback
        if mode:
            self.mode = mode
        self.player_number = max(1, int(player_number or 1))
        self.main_frame.show()
        self.visible = True
        
        # 启用键盘导航
        self._setup_navigation()
        
        # 初始化选择高亮
        self.current_selection_index = 0
        self._update_selection_highlight()
        
        mode_info = f" | mode: {self.mode}" if mode else ""
        print(f"✓ Character selector visible{mode_info}")
        print(f"🎮 Navigation: Use WASD or arrow keys to navigate, Enter/Space to select, Escape to cancel")
    
    def _setup_navigation(self):
        """设置键盘导航"""
        # 清除之前的绑定
        self._clear_navigation()
        
        # 绑定键盘事件
        from direct.showbase.DirectObject import DirectObject
        if not hasattr(self, '_event_handler'):
            self._event_handler = DirectObject()
        
        # 方向键导航 (支持WASD和箭头键)
        self._event_handler.accept('arrow_left', self._navigate_left)
        self._event_handler.accept('arrow_right', self._navigate_right) 
        self._event_handler.accept('arrow_up', self._navigate_up)
        self._event_handler.accept('arrow_down', self._navigate_down)
        
        # WASD键导航
        self._event_handler.accept('a', self._navigate_left)
        self._event_handler.accept('d', self._navigate_right)
        self._event_handler.accept('w', self._navigate_up)
        self._event_handler.accept('s', self._navigate_down)
        
        # 确认选择
        self._event_handler.accept('enter', self._confirm_selection)
        self._event_handler.accept('space', self._confirm_selection)
        
        # 退出
        self._event_handler.accept('escape', self._cancel_selection)
        
        print("🎮 Character selector navigation enabled")
    
    def _clear_navigation(self):
        """清除键盘绑定"""
        if hasattr(self, '_event_handler'):
            self._event_handler.ignoreAll()
    
    def _navigate_left(self):
        """左移选择"""
        if not self.character_buttons:
            return
        
        cols = 8  # 8列布局
        current_row = self.current_selection_index // cols
        current_col = self.current_selection_index % cols
        
        if current_col > 0:
            self.current_selection_index -= 1
            self._update_selection_highlight()
    
    def _navigate_right(self):
        """右移选择"""
        if not self.character_buttons:
            return
            
        cols = 8  # 8列布局
        current_row = self.current_selection_index // cols
        current_col = self.current_selection_index % cols
        
        if current_col < cols - 1 and self.current_selection_index + 1 < len(self.character_buttons):
            self.current_selection_index += 1
            self._update_selection_highlight()
    
    def _navigate_up(self):
        """上移选择"""
        if not self.character_buttons:
            return
            
        cols = 8  # 8列布局
        if self.current_selection_index >= cols:
            self.current_selection_index -= cols
            self._update_selection_highlight()
    
    def _navigate_down(self):
        """下移选择"""
        if not self.character_buttons:
            return
            
        cols = 8  # 8列布局
        if self.current_selection_index + cols < len(self.character_buttons):
            self.current_selection_index += cols
            self._update_selection_highlight()
    
    def _update_selection_highlight(self):
        """更新选择高亮"""
        if not self.character_buttons or self.current_selection_index >= len(self.character_buttons):
            return
        
        # 清除所有高亮
        for btn_data in self.character_buttons:
            btn_data['frame']['frameColor'] = self.colors['card_default']
        
        # 高亮当前选择
        selected_btn = self.character_buttons[self.current_selection_index]
        selected_btn['frame']['frameColor'] = self.colors['card_hover']
        
        # 更新预览
        char_id = selected_btn['char_id']
        char_data = self.unified_characters.get(char_id)
        if char_data:
            self._preview_character(char_data)
    
    def _confirm_selection(self):
        """确认当前选择"""
        if not self.character_buttons or self.current_selection_index >= len(self.character_buttons):
            return
        
        selected_btn = self.character_buttons[self.current_selection_index]
        char_id = selected_btn['char_id']
        char_data = self.unified_characters.get(char_id)
        
        if char_data:
            self._on_character_selected(char_data)
    
    def _cancel_selection(self):
        """取消选择"""
        if self.callback:
            try:
                self.callback(None)  # 传递None表示取消
            except Exception as e:
                print(f"Cancel callback error: {e}")
        else:
            self.hide()
    
    def hide(self):
        """隐藏角色选择界面"""
        self.main_frame.hide()
        self.visible = False
        self._clear_preview_model()
        self._clear_navigation()  # 清除键盘绑定
        print("✓ Character selector hidden")
    
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

        # 清理3D预览资源
        self._clear_preview_model()
        self.preview_model_cache.clear()

        for light_np in self.preview_lights:
            try:
                self.preview_render.clearLight(light_np)
            except Exception:
                pass
            try:
                light_np.removeNode()
            except Exception:
                pass
        self.preview_lights.clear()

        if self.preview_ground:
            try:
                self.preview_ground.removeNode()
            except Exception:
                pass
            self.preview_ground = None

        if self.preview_camera:
            try:
                self.preview_camera.removeNode()
            except Exception:
                pass
            self.preview_camera = None

        if self.preview_buffer:
            try:
                self.base_app.graphicsEngine.removeWindow(self.preview_buffer)
            except Exception:
                pass
            self.preview_buffer = None

        if self.preview_render:
            try:
                self.preview_render.removeNode()
            except Exception:
                pass
            self.preview_render = None

        print("✓ 角色选择器资源已清理")

    def destroy(self):
        """销毁角色选择器（cleanup的别名）"""
        self.cleanup()


CharacterSelector = EnhancedCharacterSelector

