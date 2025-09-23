# -*- coding: utf-8 -*-
"""
国际象棋主要用户界面
基于Pygame的图形界面
"""
import pygame
import sys
import os
import time
import tempfile
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timedelta

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config.settings import *
from game.game_state import ChessGameState, GameState, GameMode
from game.pieces import PieceColor
from ai.ai_factory import ai_factory
from ui.board_renderer import ChessBoardRenderer, AnimationManager
from data.database import ChessDatabase
from game.board import ChessBoard

# 语音系统导入（延迟加载）
VOICE_AVAILABLE = False
ChessVoiceSystem = None
VoiceCommandRecognizer = None

def _lazy_import_voice_system():
    """延迟导入语音系统"""
    global VOICE_AVAILABLE, ChessVoiceSystem, VoiceCommandRecognizer
    if ChessVoiceSystem is None:
        try:
            from ai.voice_system import ChessVoiceSystem as _ChessVoiceSystem
            from ai.voice_system import VoiceSettings, VoiceProvider, EmotionType
            from ai.voice_system import VoiceCommandRecognizer as _VoiceCommandRecognizer
            
            ChessVoiceSystem = _ChessVoiceSystem
            VoiceCommandRecognizer = _VoiceCommandRecognizer
            VOICE_AVAILABLE = True
            return True
        except ImportError as e:
            print(f"⚠️ 语音系统不可用: {e}")
            VOICE_AVAILABLE = False
            return False
    return VOICE_AVAILABLE

try:
    # 备用直连ML模型（当ai_factory不可用或未实现MEDIUM时）
    from ai.ml_ai import ChessMLAI
except Exception:
    ChessMLAI = None

class ChessUI:
    """国际象棋用户界面"""
    
    def __init__(self):
        # 优先初始化音频以提高兼容性与降低延迟
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            pass
        pygame.init()
        pygame.font.init()
        # 默认窗口 1024x768，并允许调整大小
        self.window_width, self.window_height = 1024, 768
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Professional Chess Game")
        self.clock = pygame.time.Clock()

        # 游戏组件
        self.game_state = ChessGameState()
        self.board_renderer = ChessBoardRenderer()
        self.animation_manager = AnimationManager()

        # AI对手（延迟加载）
        self.ai_opponents = {
            'EASY': None,    # BasicAI
            'MEDIUM': None,  # ChessMLAI
            'HARD': None     # GPTChessAI
        }

        # UI组件
        self.fonts = self._init_fonts()
        self.buttons = {}
        self.panels = {}
        self._init_ui_components()

        # 事件处理
        self.game_state.add_observer(self._on_game_event)

        # 资源与状态
        self.sounds = self._load_sounds()
        # 数据库（用于保存对局与训练样本）
        try:
            self.db = ChessDatabase(DATABASE_PATH)
        except Exception:
            # 回退：尝试使用相对路径
            chess_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fallback_db = os.path.join(chess_dir, "data", "chess_games.db")
            os.makedirs(os.path.dirname(fallback_db), exist_ok=True)
            self.db = ChessDatabase(fallback_db)

        # 运行标志
        self.running = True
        # 轻量提示（Toast）：列表元素为 (text, expire_ts)
        self._toasts = []
        
        # 语音系统初始化（延迟）
        self.voice_system = None
        self.voice_command_recognizer = None
        self.is_voice_listening = False
        self.voice_input_active = False
        self.voice_available = False
    
    def _ensure_voice_system(self):
        """确保语音系统已加载"""
        if not self.voice_available and self.voice_system is None:
            self.voice_available = self._init_voice_system()
        return self.voice_available
    
    def _speak_with_emotion(self, text, emotion_name="FRIENDLY"):
        """安全的语音播放，按需加载EmotionType"""
        if not self._ensure_voice_system() or not self.voice_system:
            return
            
        try:
            from ai.voice_system import EmotionType
            emotion = getattr(EmotionType, emotion_name, EmotionType.FRIENDLY)
            self.voice_system.speak(text, emotion, blocking=False)
        except Exception as e:
            print(f"⚠️ 语音播放失败: {e}")
    
    def _init_voice_system(self):
        """初始化语音系统（按需加载）"""
        if not _lazy_import_voice_system():
            return False
        
        try:
            from ai.voice_system import VoiceSettings, VoiceProvider, EmotionType
            from config.settings import PATHS
            
            # 使用配置中的语音缓存目录
            voice_cache_dir = PATHS['voice_cache']
            
            # 创建语音设置
            voice_settings = VoiceSettings(
                provider=VoiceProvider.SYSTEM,  # 优先使用系统语音
                language="zh-CN",
                speed=1.0,
                emotion=EmotionType.FRIENDLY
            )
            
            # 创建语音系统
            self.voice_system = ChessVoiceSystem(
                voice_settings=voice_settings,
                enable_continuous_listening=False,  # 手动控制监听
                audio_cache_dir=voice_cache_dir
            )
            
            # 创建语音指令识别器
            self.voice_command_recognizer = VoiceCommandRecognizer()
            
            # 设置回调函数
            self.voice_system.on_speech_start = self._on_voice_start
            self.voice_system.on_speech_end = self._on_voice_end
            self.voice_system.on_speech_recognized = self._on_voice_recognized
            self.voice_system.on_speech_error = self._on_voice_error
            
            print("✅ 语音系统初始化成功")
            self.voice_available = True
            return True
            
        except Exception as e:
            print(f"❌ 语音系统初始化异常: {e}")
            self.voice_system = None
            self.voice_available = False
            return False
    
    def _on_voice_start(self):
        """语音开始回调"""
        self.is_voice_listening = True
        self._toast("正在监听...", 0.5)
    
    def _on_voice_end(self):
        """语音结束回调"""
        self.is_voice_listening = False
    
    def _on_voice_recognized(self, text: str):
        """语音识别回调"""
        print(f"识别到语音: {text}")
        self._process_voice_input(text)
    
    def _on_voice_error(self, error: str):
        """语音错误回调"""
        print(f"❌ 语音错误: {error}")
        self._toast("语音识别失败，请重试", 2.0)
    
    def _process_voice_input(self, text: str):
        """处理语音输入"""
        try:
            # 先尝试识别语音指令
            if self.voice_command_recognizer:
                command = self.voice_command_recognizer.recognize_command(text)
                if command:
                    self._execute_voice_command(command)
                    return
            
            # 如果不是指令，且在陪伴模式下，作为聊天内容处理
            if (self.game_state.ai_level == 'COMPANION' and 
                'COMPANION' in self.ai_opponents and 
                self.ai_opponents['COMPANION']):
                
                ai = self.ai_opponents['COMPANION']
                if hasattr(ai, 'handle_voice_input'):
                    response = ai.handle_voice_input(text)
                    print(f"🤖 AI回应: {response}")
                elif hasattr(ai, 'chat'):
                    # 异步聊天处理，传递当前棋盘状态
                    def handle_chat():
                        try:
                            if hasattr(ai.chat, '__call__'):
                                if asyncio.iscoroutinefunction(ai.chat):
                                    # 异步方法，传递当前棋盘
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    response = loop.run_until_complete(ai.chat(text, self.game_state.board))
                                    loop.close()
                                else:
                                    # 同步方法，传递当前棋盘
                                    response = ai.chat(text, self.game_state.board)
                                
                                print(f"🤖 AI回应: {response}")
                                
                                # 语音播放回应
                                if response:
                                    self._speak_with_emotion(response, "FRIENDLY")
                        except Exception as e:
                            print(f"❌ 聊天处理失败: {e}")
                            
                    # 在后台线程中处理
                    import threading
                    threading.Thread(target=handle_chat, daemon=True).start()
                else:
                    print(f"💬 用户说: {text}")
            else:
                print(f"💬 语音输入: {text} (当前模式不支持对话)")
        
        except Exception as e:
            print(f"❌ 语音处理失败: {e}")
    
    def _execute_voice_command(self, command: Dict):
        """执行语音指令"""
        try:
            cmd_name = command['command']
            print(f"🎯 执行语音指令: {cmd_name}")
            
            if cmd_name == '开始游戏':
                self._handle_button_click('new_game')
            elif cmd_name == '悔棋':
                self._handle_button_click('undo')
            elif cmd_name == '暂停':
                self._handle_button_click('pause')
            elif cmd_name == '继续':
                self._handle_button_click('pause')  # 同一个按钮处理暂停/继续
            elif cmd_name == '结束':
                self._handle_button_click('menu')
            elif cmd_name in ['分析', '最佳移动', '提示']:
                self._handle_button_click('assistant')
            elif cmd_name in ['解释', '教学']:
                if (self.game_state.ai_level == 'COMPANION' and 
                    'COMPANION' in self.ai_opponents):
                    ai = self.ai_opponents['COMPANION'] 
                    if ai and hasattr(ai, 'handle_player_question'):
                        question = "请解释刚才的走法或当前局面"
                        response = ai.handle_player_question(question)
                        print(f"💡 AI解释: {response}")
                        if response:
                            self._speak_with_emotion(response, "FRIENDLY")
            else:
                print(f"⚠️ 未知语音指令: {cmd_name}")
                
        except Exception as e:
            print(f"❌ 语音指令执行失败: {e}")
    
    async def _start_voice_input_async(self):
        """异步开始语音输入"""
        try:
            if not self.voice_system:
                self._toast("语音系统不可用", 2.0)
                return
            
            if self.voice_input_active:
                self._toast("语音输入已在进行中", 1.0)
                return
            
            self.voice_input_active = True
            self._toast("请说话 (5秒内)...", 0.5)
            
            # 监听语音
            result = await self.voice_system.listen_async(timeout=5.0, phrase_timeout=3.0)
            
            if result and result.text.strip():
                user_text = result.text.strip()
                print(f"👤 用户说: {user_text}")
                self._process_voice_input(user_text)
            else:
                self._toast("未识别到语音", 1.5)
        
        except Exception as e:
            print(f"❌ 语音输入失败: {e}")
            self._toast("语音输入失败", 2.0)
        
        finally:
            self.voice_input_active = False
    
    def _start_voice_input(self):
        """开始语音输入（同步包装）"""
        try:
            # 在后台线程中运行异步语音输入
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._start_voice_input_async())
                loop.close()
            
            import threading
            threading.Thread(target=run_async, daemon=True).start()
            
        except Exception as e:
            print(f"❌ 启动语音输入失败: {e}")
    
    async def _voice_interaction_async(self, prompt: str = "请告诉我您需要什么帮助"):
        """异步语音交互"""
        try:
            if not self.voice_system:
                return
            
            # 使用语音系统的完整交互流程
            def handle_response(user_text: str) -> str:
                """处理用户语音输入并返回回复"""
                try:
                    ai_level = self.game_state.ai_level
                    if (ai_level == 'COMPANION' and 
                        'COMPANION' in self.ai_opponents and 
                        self.ai_opponents['COMPANION']):
                        
                        ai = self.ai_opponents['COMPANION']
                        if hasattr(ai, 'chat'):
                            if asyncio.iscoroutinefunction(ai.chat):
                                # 异步方法，传递当前棋盘状态
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                response = loop.run_until_complete(ai.chat(user_text, self.game_state.board))
                                loop.close()
                                return response
                            else:
                                # 同步方法，传递当前棋盘状态
                                return ai.chat(user_text, self.game_state.board)
                    
                    return f"我听到您说：{user_text}。不过当前不在陪伴模式，无法进行深度对话。"
                except Exception as e:
                    return f"处理您的话语时出现问题：{e}"
            
            # 进行语音交互
            user_text = await self.voice_system.voice_interaction(
                prompt=prompt,
                timeout=8.0,
                response_callback=handle_response
            )
            
            if user_text:
                print(f"✅ 语音交互完成: {user_text}")
            
        except Exception as e:
            print(f"❌ 语音交互失败: {e}")
    
    def _start_voice_interaction(self):
        """开始语音交互（同步包装）"""
        try:
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._voice_interaction_async())
                loop.close()
            
            import threading
            threading.Thread(target=run_async, daemon=True).start()
            
        except Exception as e:
            print(f"❌ 启动语音交互失败: {e}")
    
    def _init_fonts(self) -> Dict:
        """初始化字体 - 支持中文显示"""
        from config.settings import FONT_SIZES
        
        # 尝试加载支持中文的字体
        chinese_fonts = [
            # Windows系统字体
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            # macOS系统字体
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            # Linux系统字体
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
        ]
        
        fonts = {}
        loaded_font = None
        
        # 尝试加载中文字体
        for font_path in chinese_fonts:
            try:
                if os.path.exists(font_path):
                    # 测试字体是否能正常加载
                    test_font = pygame.font.Font(font_path, FONT_SIZES['BUTTON'])
                    loaded_font = font_path
                    print(f"✅ 成功加载中文字体: {font_path}")
                    break
            except Exception as e:
                continue
        
        # 如果没有找到中文字体，使用系统默认字体
        if loaded_font is None:
            print("⚠️ 未找到中文字体，使用系统默认字体（可能不显示中文）")
            fonts = {
                'title': pygame.font.Font(None, FONT_SIZES['TITLE']),
                'large': pygame.font.Font(None, FONT_SIZES['LARGE']),
                'button': pygame.font.Font(None, FONT_SIZES['BUTTON']),
                'info': pygame.font.Font(None, FONT_SIZES['INFO']),
                'small': pygame.font.Font(None, FONT_SIZES['SMALL'])
            }
        else:
            # 使用找到的中文字体
            fonts = {
                'title': pygame.font.Font(loaded_font, FONT_SIZES['TITLE']),
                'large': pygame.font.Font(loaded_font, FONT_SIZES['LARGE']),
                'button': pygame.font.Font(loaded_font, FONT_SIZES['BUTTON']),
                'info': pygame.font.Font(loaded_font, FONT_SIZES['INFO']),
                'small': pygame.font.Font(loaded_font, FONT_SIZES['SMALL'])
            }
        
        return fonts
    def _render_text_safe(self, text: str, font, color, fallback_text: str = None):
        """安全渲染文本，处理emoji和特殊字符"""
        try:
            # 首先尝试直接渲染
            return font.render(text, True, color)
        except UnicodeError:
            # 如果遇到Unicode错误，使用备用文本
            if fallback_text:
                try:
                    return font.render(fallback_text, True, color)
                except:
                    return font.render("???", True, color)
            else:
                # 移除emoji和特殊字符，只保留基础字符
                safe_text = ''.join(char for char in text if ord(char) < 127)
                if safe_text:
                    return font.render(safe_text, True, color)
                else:
                    return font.render("Text", True, color)
        except Exception as e:
            print(f"⚠️ 文本渲染失败 '{text}': {e}")
            return font.render("Text", True, color)
    

    def _init_ui_components(self):
        """初始化面板与按钮，使用自适应布局"""
        # 初始化结构
        self.buttons = {}
        self.panels = {}
        # 首次或窗口变化时重算布局
        self._recompute_layout()

    def _recompute_layout(self):
        """根据窗口大小重算棋盘和侧栏布局，避免遮挡并自适应"""
        from config.settings import UI_MARGINS
        
        # 棋盘尽量为正方形，占高度约90%，预留顶部标题和底部空间
        usable_height = max(self.window_height - 140, 480)
        board_size = min(usable_height, int(self.window_width * 0.66))
        self.square_size = max(board_size // 8, 48)
        board_pixel = self.square_size * 8
        
        # 使用配置的边距
        board_x = UI_MARGINS['BOARD_MARGIN'] * 2
        board_y = 80
        self.board_area = pygame.Rect(board_x, board_y, board_pixel, board_pixel)
        
        # 右侧面板宽度自适应
        right_panel_width = max(int(self.window_width * 0.28), 320)
        self.right_panel = pygame.Rect(
            self.board_area.right + UI_MARGINS['PANEL_PADDING'] * 2, 
            80, 
            right_panel_width, 
            board_pixel
        )
        # 渲染器尺寸同步
        self.board_renderer.square_size = self.square_size
        self.board_renderer.board_size = board_pixel
        self.board_renderer.board_surface = None  # 触发重建
        # 面板区域（信息/历史/吃子）
        info_h = max(int(self.right_panel.height * 0.26), 180)
        moves_h = max(int(self.right_panel.height * 0.38), 220)
        captured_h = max(self.right_panel.height - info_h - moves_h - 30, 80)
        self.panels['board'] = pygame.Rect(self.board_area)
        self.panels['info'] = pygame.Rect(self.right_panel.x, self.right_panel.y, right_panel_width, info_h)
        self.panels['moves'] = pygame.Rect(self.right_panel.x, self.panels['info'].bottom + 10, right_panel_width, moves_h)
        self.panels['captured'] = pygame.Rect(self.right_panel.x, self.panels['moves'].bottom + 10, right_panel_width, captured_h)
        # 菜单与游戏按钮布局
        self._layout_buttons(right_panel_width)

    def _layout_buttons(self, panel_width):
        """布置按钮，防止遮挡并自适应宽度"""
        from config.settings import UI_MARGINS
        
        # 主菜单按钮区（靠右上角）
        menu_button_width = max(int(self.window_width * 0.18), 180)
        menu_button_x = self.window_width - menu_button_width - UI_MARGINS['PANEL_PADDING'] * 2
        
        button_spacing = UI_MARGINS['BUTTON_SPACING'] * 6  # 菜单按钮间距稍大
        self.buttons['vs_human'] = pygame.Rect(menu_button_x, 100, menu_button_width, 40)
        self.buttons['vs_ai_easy'] = pygame.Rect(menu_button_x, 100 + button_spacing, menu_button_width, 40)
        self.buttons['vs_ai_medium'] = pygame.Rect(menu_button_x, 100 + button_spacing * 2, menu_button_width, 40)
        self.buttons['vs_ai_hard'] = pygame.Rect(menu_button_x, 100 + button_spacing * 3, menu_button_width, 40)
        self.buttons['vs_ai_companion'] = pygame.Rect(menu_button_x, 100 + button_spacing * 4, menu_button_width, 50)

        # 游戏界面按钮：两排 + 陪伴专用按钮，放在 captured 面板下方，整宽
        gap_x = UI_MARGINS['BUTTON_SPACING']
        gap_y = UI_MARGINS['BUTTON_SPACING']
        button_height = max(int(panel_width * 0.11), 36)
        col_width = (panel_width - gap_x) // 2
        left_x = self.panels['captured'].x
        right_x = left_x + col_width + gap_x
        base_y = self.panels['captured'].bottom + UI_MARGINS['PANEL_PADDING']
        # 确保按钮不超出窗口底部，如果空间不足则自适应减小按钮高度
        total_needed = 4 * button_height + 3 * gap_y
        avail_h = (self.window_height - 10) - base_y
        if avail_h < total_needed:
            min_btn_h = 28
            # 重新计算适配后的按钮高度（至少28）
            button_height = max(min_btn_h, (avail_h - 3 * gap_y) // 4) if avail_h > (3 * gap_y + min_btn_h) else min_btn_h
            # 如果仍然不足以容纳，则将起始Y上移以完全显示
            total_needed = 4 * button_height + 3 * gap_y
            if base_y + total_needed > self.window_height - 10:
                base_y = max(80, self.window_height - 10 - total_needed)
        # 行1
        self.buttons['new_game'] = pygame.Rect(left_x, base_y, col_width, button_height)
        self.buttons['menu'] = pygame.Rect(right_x, base_y, col_width, button_height)
        # 行2
        row2_y = base_y + button_height + gap_y
        self.buttons['undo'] = pygame.Rect(left_x, row2_y, col_width, button_height)
        self.buttons['pause'] = pygame.Rect(right_x, row2_y, col_width, button_height)
        # 行3（整宽）合并为单一“助手”按钮
        row3_y = row2_y + button_height + gap_y
        self.buttons['assistant'] = pygame.Rect(left_x, row3_y, panel_width, button_height)
    
    def _load_sounds(self) -> Dict:
        """加载音效（优先加载本地 OGG 文件），带回退与日志"""
        sounds: Dict[str, pygame.mixer.Sound] = {}
        # 主路径
        primary_dir = os.path.join(PATHS['assets'], "sounds")
        # 备用：以当前文件定位到仓库根的 assets/sounds
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        fallback_dir = os.path.join(repo_root, 'assets', 'sounds')
        sound_dir = primary_dir if os.path.isdir(primary_dir) else fallback_dir

        # 目标文件
        files = {
            'move': os.path.join(sound_dir, 'move.ogg'),
            'capture': os.path.join(sound_dir, 'capture.ogg'),
            'check': os.path.join(sound_dir, 'check.ogg')
        }

        try:
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                except Exception as e:
                    print(f"⚠️ 音频初始化失败（首次）：{e}")
                    # 尝试使用默认参数再次初始化
                    try:
                        pygame.mixer.init()
                    except Exception as e2:
                        print(f"⚠️ 音频初始化失败（默认）：{e2}")
                        return sounds

            for key, path in files.items():
                if os.path.exists(path):
                    try:
                        snd = pygame.mixer.Sound(path)
                        snd.set_volume(0.6)
                        sounds[key] = snd
                    except Exception as e:
                        print(f"⚠️ 加载音效失败 {key} -> {path}: {e}")
                else:
                    # 路径不存在时记录一次
                    print(f"ℹ️ 音效文件未找到: {path}")

            if sounds:
                print(f"🔊 音效加载完成: {', '.join(sounds.keys())}")
            else:
                print(f"⚠️ 未能加载任何音效，目录: {sound_dir}")
        except Exception as e:
            print(f"⚠️ 音效系统初始化异常: {e}")

        return sounds
    
    def _on_game_event(self, event: str, data: Dict):
        """处理游戏事件"""
        if event == 'move_made':
            # 播放音效（若能识别吃子则播放 capture，否则播放 move）
            try:
                is_capture = bool(data.get('captured_piece') or data.get('was_capture'))
            except Exception:
                is_capture = False
            key = 'capture' if is_capture and 'capture' in self.sounds else 'move'
            if key in self.sounds:
                try:
                    self.sounds[key].play()
                except Exception as e:
                    print(f"⚠️ 播放音效失败: {e}")
                
            # 添加移动动画
            from_pos = data['from']
            to_pos = data['to']
            piece = self.game_state.board.get_piece_at(to_pos)
            if piece:
                self.animation_manager.add_move_animation(piece, from_pos, to_pos)
        
        elif event == 'game_ended':
            # 保存对局并提示
            try:
                self._save_game_to_db(data)
            except Exception as e:
                print(f"⚠️ 保存对局到数据库失败: {e}")
            self._show_game_over_message(data)
    
    def run(self):
        """主游戏循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self._handle_events()
            self._update(dt)
            self._render()
        
        pygame.quit()
        
        # 清理语音系统
        if hasattr(self, 'voice_system') and self.voice_system:
            try:
                self.voice_system.cleanup()
            except Exception as e:
                print(f"⚠️ 语音系统清理失败: {e}")
        
        # 清理临时文件
        try:
            from config.settings import cleanup_temp_files
            cleanup_temp_files()
            print("✅ 临时文件清理完成")
        except Exception as e:
            print(f"⚠️ 临时文件清理失败: {e}")
        
        sys.exit()
    
    def _handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self._handle_mouse_click(event.pos)
            
            elif event.type == pygame.KEYDOWN:
                self._handle_key_press(event.key)

            elif event.type == pygame.VIDEORESIZE:
                # 窗口缩放时重建显示并重算布局（节流防抖）
                self.window_width, self.window_height = max(event.w, 800), max(event.h, 600)
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                now_ts = time.time()
                last_ts = getattr(self, '_last_layout_ts', 0)
                if now_ts - last_ts > 0.05:
                    self._recompute_layout()
                    self._last_layout_ts = now_ts
    
    def _handle_mouse_click(self, pos: tuple):
        """处理鼠标点击"""
        # 检查按钮点击
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(pos):
                self._handle_button_click(button_name)
                return
        
        # 检查棋盘点击
        if self.panels['board'].collidepoint(pos):
            # 转换为棋盘坐标
            board_offset = (self.panels['board'].x, self.panels['board'].y)
            relative_pos = (pos[0] - board_offset[0], pos[1] - board_offset[1])
            board_pos = self.board_renderer.pixel_to_board_position(relative_pos)
            
            if board_pos and self.game_state.state == GameState.PLAYING:
                self.game_state.select_square(board_pos)
    
    def _handle_button_click(self, button_name: str):
        """处理按钮点击"""
        if button_name == 'new_game':
            self.game_state.start_new_game(GameMode.HUMAN_VS_HUMAN)
        
        elif button_name == 'vs_human':
            self.game_state.start_new_game(GameMode.HUMAN_VS_HUMAN)
        
        elif button_name == 'vs_ai_easy':
            self._start_ai_game('EASY')
        
        elif button_name == 'vs_ai_medium':
            self._start_ai_game('MEDIUM')
        
        elif button_name == 'vs_ai_hard':
            self._start_ai_game('HARD')
        
        elif button_name == 'vs_ai_companion':
            self._start_ai_game('COMPANION')
        
        elif button_name == 'undo':
            self.game_state.undo_move()
        
        elif button_name == 'pause':
            if self.game_state.state == GameState.PLAYING:
                self.game_state.pause_game()
            elif self.game_state.state == GameState.PAUSED:
                self.game_state.resume_game()
        
        elif button_name == 'menu':
            self.game_state.go_to_menu()
        
        elif button_name == 'assistant':
            self._toast("助手已激活：请在提示音后说话", 2.5)
            self._handle_assistant()
    
    def _handle_key_press(self, key):
        """处理键盘按键"""
        if key == pygame.K_ESCAPE:
            if self.game_state.state == GameState.PLAYING:
                self.game_state.go_to_menu()
            else:
                self.running = False
        
        elif key == pygame.K_u:
            self.game_state.undo_move()
        
        elif key == pygame.K_SPACE:
            if self.game_state.state == GameState.PLAYING:
                self.game_state.pause_game()
            elif self.game_state.state == GameState.PAUSED:
                self.game_state.resume_game()
    
    def _update(self, dt: float):
        """更新游戏状态 - 支持异步AI处理"""
        self.animation_manager.update(dt)
        
        # 检查异步AI移动结果
        if hasattr(self, '_ai_move_ready') and self._ai_move_ready is not None:
            move = self._ai_move_ready
            thinking_time = getattr(self, '_ai_thinking_time', 0)
            
            # 清除标记
            self._ai_move_ready = None
            self._ai_thinking = False
            
            # 应用AI移动
            try:
                if move:
                    from_pos, to_pos = move
                    print(f"🎯 AI选择移动: {from_pos} -> {to_pos} (思考时间: {thinking_time:.1f}s)")
                    self.game_state.attempt_move(from_pos, to_pos)
                    
                    # 如果是陪伴模式，异步处理移动后的交互
                    ai_level = self.game_state.ai_level
                    if ai_level == 'COMPANION' and ai_level in self.ai_opponents:
                        ai = self.ai_opponents[ai_level]
                        def handle_companion_interaction():
                            try:
                                if hasattr(ai, 'handle_player_move'):
                                    ai.handle_player_move(from_pos, to_pos)
                            except Exception as e:
                                print(f"⚠️ 陪伴模式移动处理失败: {e}")
                        
                        # 在后台线程处理陪伴交互，不阻塞UI
                        import threading
                        threading.Thread(target=handle_companion_interaction, daemon=True).start()
                else:
                    print("⚠️ AI未能生成有效移动")
            except Exception as e:
                print(f"❌ AI移动应用失败: {e}")
        
        # AI移动处理
        if (self.game_state.state == GameState.PLAYING and 
            not self.game_state.is_human_turn() and 
            not self.animation_manager.is_animating()):
            self._make_ai_move()
    
    def _make_ai_move(self):
        """执行AI移动 - 异步优化版本"""
        current_player = self.game_state.board.current_player
        ai_level = self.game_state.ai_level
        
        # 防止重复触发AI思考
        if hasattr(self, '_ai_thinking') and self._ai_thinking:
            return
        
        # 延迟加载AI实例
        if ai_level not in self.ai_opponents or self.ai_opponents[ai_level] is None:
            print(f"🤖 加载{ai_level}级AI...")
            ai = ai_factory.create_ai(ai_level)
            if ai:
                self.ai_opponents[ai_level] = ai
                print(f"✅ {ai_level}级AI加载成功")
                
                # 如果是陪伴模式，开始新游戏
                if ai_level == 'COMPANION':
                    try:
                        ai.start_new_game()
                        print("🎮 陪伴模式游戏开始")
                    except Exception as e:
                        print(f"⚠️ 陪伴模式初始化失败: {e}")
            else:
                print(f"❌ {ai_level}级AI加载失败")
                return
        
        ai = self.ai_opponents[ai_level]
        if ai:
            # 标记AI思考状态
            self._ai_thinking = True
            self._ai_thinking_start_time = time.time()
            
            # 异步执行AI移动计算
            def ai_thinking_worker():
                try:
                    print(f"🧠 {ai_level}级AI开始思考...")
                    
                    # 执行AI移动计算
                    if ai_level == 'COMPANION' and hasattr(ai, 'get_best_move') and asyncio.iscoroutinefunction(ai.get_best_move):
                        # 陪伴模式的异步AI
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            move = loop.run_until_complete(ai.get_best_move(self.game_state.board, current_player, time_limit=3))
                        finally:
                            loop.close()
                    else:
                        # 传统AI
                        move = ai.get_best_move(self.game_state.board, current_player)
                    
                    # 计算思考时间
                    thinking_time = time.time() - self._ai_thinking_start_time
                    
                    # 在主线程中应用移动
                    def apply_move():
                        try:
                            self._ai_thinking = False
                            
                            if move:
                                from_pos, to_pos = move
                                print(f"🎯 AI选择移动: {from_pos} -> {to_pos} (思考时间: {thinking_time:.1f}s)")
                                self.game_state.attempt_move(from_pos, to_pos)
                                
                                # 如果是陪伴模式，异步处理移动后的交互
                                if ai_level == 'COMPANION':
                                    def handle_companion_interaction():
                                        try:
                                            if hasattr(ai, 'handle_player_move'):
                                                ai.handle_player_move(from_pos, to_pos)
                                        except Exception as e:
                                            print(f"⚠️ 陪伴模式移动处理失败: {e}")
                                    
                                    # 在后台线程处理陪伴交互，不阻塞UI
                                    threading.Thread(target=handle_companion_interaction, daemon=True).start()
                            else:
                                print("⚠️ AI未能生成有效移动")
                                
                        except Exception as e:
                            print(f"❌ AI移动应用失败: {e}")
                            self._ai_thinking = False
                    
                    # 使用线程安全的方式更新UI
                    import threading
                    if hasattr(threading, 'main_thread') and threading.current_thread() != threading.main_thread():
                        # 如果不在主线程，需要调度到主线程执行UI更新
                        # 这里使用一个简单的标记系统，让主线程在update中检查
                        self._ai_move_ready = move
                        self._ai_thinking_time = thinking_time
                    else:
                        # 直接在主线程执行
                        apply_move()
                        
                except Exception as e:
                    print(f"❌ AI思考过程异常: {e}")
                    self._ai_thinking = False
                    import traceback
                    traceback.print_exc()
            
            # 启动AI思考线程
            import threading
            ai_thread = threading.Thread(target=ai_thinking_worker, daemon=True)
            ai_thread.start()
            
            print(f"🔄 AI正在后台思考，UI保持响应...")
    
    def _start_ai_game(self, difficulty: str):
        """开始AI对战游戏"""
        print(f"🎮 开始与{difficulty}级AI对战...")
        
        # 预加载AI（显示加载进度）
        if difficulty not in self.ai_opponents or self.ai_opponents[difficulty] is None:
            print(f"🔄 正在加载{difficulty}级AI...")
            ai = None
            try:
                # 优先通过工厂创建
                ai = ai_factory.create_ai(difficulty)
            except Exception as e:
                print(f"⚠️ AI工厂创建失败: {e}")
                ai = None

            # MEDIUM 使用训练好的ML模型作为回退
            if (ai is None or not hasattr(ai, 'get_best_move')) and difficulty == 'MEDIUM' and ChessMLAI:
                try:
                    model_path = AI_LEVELS['MEDIUM'].get('model_path')
                    print(f"📦 直接加载ML模型: {model_path}")
                    ai = ChessMLAI(model_path)
                except Exception as e:
                    print(f"⚠️ ML模型加载失败: {e}")
                    ai = None
            if ai:
                self.ai_opponents[difficulty] = ai
                print(f"✅ {difficulty}级AI加载完成")
            else:
                print(f"❌ {difficulty}级AI加载失败，使用备用AI")
                # 如果高级AI失败，使用基础AI作为备用
                backup_ai = ai_factory.create_ai('EASY')
                if backup_ai:
                    self.ai_opponents[difficulty] = backup_ai
                    print("✅ 备用AI加载成功")
        
        # 开始游戏
        self.game_state.start_new_game(GameMode.HUMAN_VS_AI, difficulty)
    
    def _handle_voice_chat(self):
        """处理语音聊天"""
        try:
            ai_level = self.game_state.ai_level
            if ai_level == 'COMPANION' and ai_level in self.ai_opponents:
                ai = self.ai_opponents[ai_level]
                if ai and hasattr(ai, 'start_voice_chat_interaction'):
                    print("🗣️ 提示：将开始语音输入。请在提示音后说话，短句清晰，2-3秒内结束。")
                    response = ai.start_voice_chat_interaction()
                    self._toast("AI正在播报回答...", 3.0)
                    print(f"AI回应: {response}")
                else:
                    print("⚠️ 陪伴模式AI不支持语音聊天")
            else:
                print("⚠️ 语音聊天仅在陪伴模式下可用")
        except Exception as e:
            print(f"❌ 语音聊天失败: {e}")
    
    def _handle_ask_question(self):
        """处理问答"""
        try:
            ai_level = self.game_state.ai_level
            if ai_level == 'COMPANION' and ai_level in self.ai_opponents:
                ai = self.ai_opponents[ai_level]
                if ai and hasattr(ai, 'handle_player_question'):
                    # 这里可以弹出输入框，现在先用预设问题
                    questions = [
                        "这个位置我应该怎么走？",
                        "能分析一下当前局面吗？",
                        "有什么好的开局建议？",
                        "我刚才那步棋走得怎么样？"
                    ]
                    import random
                    question = random.choice(questions)
                    response = ai.handle_player_question(question)
                    self._toast("AI正在播报回答...", 3.0)
                    print(f"❓ 问题: {question}")
                    print(f"💡 AI回答: {response}")
                else:
                    print("⚠️ 陪伴模式AI不支持问答")
            else:
                print("⚠️ 问答功能仅在陪伴模式下可用")
        except Exception as e:
            print(f"❌ 问答失败: {e}")

    def _handle_assistant(self):
        """统一助手：语音输入→意图识别→聊天/分析"""
        try:
            # 检查语音系统可用性
            if not self.voice_available or not self.voice_system:
                self._fallback_text_assistant()
                return
            
            ai_level = self.game_state.ai_level
            if ai_level == 'COMPANION' and ai_level in self.ai_opponents:
                ai = self.ai_opponents[ai_level]
                
                # 优先使用完整的语音交互
                if ai and hasattr(ai, 'chat'):
                    print("🗣️ 助手：开始语音交互，请在提示音后清晰说话...")
                    self._start_voice_interaction()
                elif ai and hasattr(ai, 'start_voice_chat_interaction'):
                    print("🗣️ 助手：开始语音聊天，请在提示音后说话")
                    def handle_voice_chat():
                        try:
                            reply = ai.start_voice_chat_interaction()
                            self._toast("AI正在播报回答...", 3.0)
                            print(f"🤖 助手回答: {reply}")
                        except Exception as e:
                            print(f"❌ 语音聊天失败: {e}")
                    
                    import threading
                    threading.Thread(target=handle_voice_chat, daemon=True).start()
                else:
                    self._fallback_text_assistant()
            else:
                # 非陪伴模式：仅提供语音指令输入
                if self.voice_available and self.voice_system:
                    print("🗣️ 语音指令模式：请说出指令（如：开始游戏、悔棋、分析局面等）")
                    self._start_voice_input()
                else:
                    print("⚠️ 助手仅在陪伴模式下可用，或当前语音系统不可用")
                    self._toast("助手仅在陪伴模式下可用", 2.0)
        except Exception as e:
            print(f"❌ 助手处理失败: {e}")
            self._fallback_text_assistant()
    
    def _fallback_text_assistant(self):
        """备用文本助手（当语音不可用时）"""
        try:
            ai_level = self.game_state.ai_level
            if ai_level == 'COMPANION' and ai_level in self.ai_opponents:
                ai = self.ai_opponents[ai_level]
                if ai and hasattr(ai, 'handle_player_question'):
                    self._toast("AI正在分析当前局面...", 2.0)
                    response = ai.handle_player_question("请分析当前局面并给出建议。")
                    self._toast("分析完成，请查看控制台", 3.0)
                    print(f"💡 AI分析: {response}")
                else:
                    print("⚠️ 陪伴模式AI不支持文本助手功能")
            else:
                print("⚠️ 助手功能仅在陪伴模式下可用")
                self._toast("助手功能仅在陪伴模式下可用", 2.0)
        except Exception as e:
            print(f"❌ 备用助手失败: {e}")
    
    def _update_assistant_button_text(self):
        """更新助手按钮文本（根据当前状态）"""
        # 使用备用文本，避免emoji显示问题
        if self.voice_available and hasattr(self, 'voice_system') and self.voice_system:
            assistant_text = "语音助手"
        else:
            assistant_text = "文字助手"
        
        if hasattr(self, 'is_voice_listening') and self.is_voice_listening:
            assistant_text = "正在听取..."
        elif hasattr(self, 'voice_input_active') and self.voice_input_active:
            assistant_text = "语音处理中..."
        
        self.assistant_button_text = assistant_text
        return assistant_text

    # --- 数据与持久化 ---
    def _save_game_to_db(self, data: Dict):
        """保存当前对局到数据库（用于后续训练）"""
        end_time_dt = datetime.now()
        game_info = self.game_state.get_game_info()
        duration_sec = float(game_info.get('game_time', 0.0) or 0.0)
        start_time_dt = end_time_dt - timedelta(seconds=duration_sec)

        # 结果映射
        result = data.get('result', 'draw')
        if result not in ('white_wins', 'black_wins', 'draw'):
            # 兼容其他标记
            if result in ('white', 'White'):
                result = 'white_wins'
            elif result in ('black', 'Black'):
                result = 'black_wins'
            else:
                result = 'draw'

        total_moves = len(self.game_state.board.move_history)
        final_position = self._encode_board_simple_fen()

        # 玩家信息（尽量推断）
        mode = self.game_state.mode
        ai_level = self.game_state.ai_level if mode == GameMode.HUMAN_VS_AI else None
        white_type = 'human'
        black_type = 'human'
        if mode == GameMode.HUMAN_VS_AI:
            # 简化：默认白方为人类、黑方为AI（具体方位可根据项目需求调整）
            white_type = 'human'
            black_type = 'ai'

        game_data = {
            'start_time': start_time_dt.isoformat(timespec='seconds'),
            'end_time': end_time_dt.isoformat(timespec='seconds'),
            'white_player': 'Human' if white_type == 'human' else f"AI-{ai_level or ''}",
            'black_player': 'Human' if black_type == 'human' else f"AI-{ai_level or ''}",
            'white_type': white_type,
            'black_type': black_type,
            'ai_level': ai_level,
            'result': result,
            'total_moves': total_moves,
            'game_duration': duration_sec,
            'pgn': '',  # 可后续替换为真实PGN
            'final_position': final_position
        }

        game_id = self.db.save_game(game_data)

        # 使用临时棋盘回放每一步，以获取 position_after（简化FEN）
        temp_board = ChessBoard()

        # 保存每一步（尽力填充字段）
        for idx, mv in enumerate(self.game_state.board.move_history, start=1):
            try:
                if isinstance(mv, dict):
                    from_pos = mv.get('from')
                    to_pos = mv.get('to')
                    notation = mv.get('notation', None)
                    player_color = mv.get('player') or ( 'white' if idx % 2 == 1 else 'black')
                else:
                    # 对象形式的兼容
                    from_pos = getattr(mv, 'from_pos', None)
                    to_pos = getattr(mv, 'to_pos', None)
                    notation = getattr(mv, 'notation', None)
                    player_color = getattr(mv, 'player_color', ('white' if idx % 2 == 1 else 'black'))

                from_sq = self._board_pos_to_square(from_pos) if from_pos else ''
                to_sq = self._board_pos_to_square(to_pos) if to_pos else ''

                # 终局棋盘获取到达后的棋子类型（尽力而为）
                piece = self.game_state.board.get_piece_at(to_pos) if to_pos else None
                piece_type = piece.piece_type.name if piece else ''

                # 在临时棋盘上回放一步并记录该步后的简化FEN
                position_after_simple = ''
                try:
                    if from_pos and to_pos:
                        temp_board.make_move(from_pos, to_pos)
                        position_after_simple = self._encode_board_simple_fen_from_board(temp_board)
                except Exception:
                    position_after_simple = ''

                self.db.save_move(game_id, {
                    'move_number': idx,
                    'player_color': player_color,
                    'from_square': from_sq,
                    'to_square': to_sq,
                    'piece_type': piece_type,
                    'captured_piece': None,
                    'special_move': None,
                    'notation': notation or f"{from_sq}-{to_sq}",
                    'evaluation': None,
                    'think_time': None,
                    'position_after': position_after_simple
                })
            except Exception as e:
                print(f"⚠️ 保存移动失败（第{idx}步）: {e}")

    def _board_pos_to_square(self, pos):
        """将(行,列)坐标转换为代数记谱（a1..h8），假设(0,0)=a8"""
        try:
            row, col = pos
            file_char = chr(ord('a') + col)
            rank_char = str(8 - row)
            return f"{file_char}{rank_char}"
        except Exception:
            return ''

    def _encode_board_simple_fen(self) -> str:
        """生成简化FEN风格的棋盘编码（与训练侧兼容）"""
        pieces_list = []
        try:
            for row in range(8):
                for col in range(8):
                    piece = self.game_state.board.get_piece_at((row, col))
                    if piece:
                        color = 'W' if piece.color.name == 'WHITE' else 'B'
                        piece_type = piece.piece_type.name[0]
                        pieces_list.append(f"{row}{col}{color}{piece_type}")
        except Exception:
            pass
        return ';'.join(pieces_list)

    def _encode_board_simple_fen_from_board(self, board: ChessBoard) -> str:
        """基于给定棋盘生成简化FEN"""
        pieces_list = []
        try:
            for row in range(8):
                for col in range(8):
                    piece = board.get_piece_at((row, col))
                    if piece:
                        color = 'W' if piece.color.name == 'WHITE' else 'B'
                        piece_type = piece.piece_type.name[0]
                        pieces_list.append(f"{row}{col}{color}{piece_type}")
        except Exception:
            pass
        return ';'.join(pieces_list)
    
    def _render(self):
        """渲染画面"""
        self.screen.fill(COLORS['BACKGROUND'])
        
        if self.game_state.state == GameState.MENU:
            self._render_menu()
        else:
            self._render_game()
        # 渲染提示气泡
        self._render_toasts()
        
        pygame.display.flip()

    def _toast(self, text: str, seconds: float = 2.0):
        """添加一个将在指定秒数后消失的提示"""
        expire = time.time() + max(0.5, float(seconds))
        self._toasts.append((text, expire))

    def _render_toasts(self):
        """在右上角渲染最多三条提示气泡"""
        now = time.time()
        # 过滤过期项
        self._toasts = [(t, e) for (t, e) in self._toasts if e > now]
        if not self._toasts:
            return
        # 基础位置
        x = self.window_width - 20
        y = 20
        # 仅显示最后三条
        for text, _ in self._toasts[-3:]:
            surf = self._render_text_safe(text, self.fonts['button'], (255, 255, 255), text.replace("🎤", "MIC").replace("🔴", "REC").replace("🎙️", "VOICE"))
            padding = 8
            rect = surf.get_rect()
            rect.topleft = (x - rect.width - padding*2, y)
            # 背景半透明黑
            bg = pygame.Surface((rect.width + padding*2, rect.height + padding*2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            self.screen.blit(bg, rect.move(-padding, -padding))
            self.screen.blit(surf, rect)
            y += rect.height + padding*2 + 8
    
    def _render_menu(self):
        """渲染主菜单"""
        # 标题
        title = self._render_text_safe("🏆 Professional Chess", self.fonts['title'], 
                                     COLORS['TEXT'], "Professional Chess")
        title_rect = title.get_rect(center=(self.window_width // 2, 100))
        self.screen.blit(title, title_rect)
        # 副标题
        subtitle = self.fonts['info'].render("Choose your game mode", True, COLORS['TEXT'])
        subtitle_rect = subtitle.get_rect(center=(self.window_width // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        # 菜单按钮（仅菜单相关）
        menu_buttons = [
            ('vs_human', "Human vs Human"),
            ('vs_ai_easy', "vs AI (Easy)"),
            ('vs_ai_medium', "vs AI (Medium)"),
            ('vs_ai_hard', "vs AI (Hard)"),
            ('vs_ai_companion', "AI Companion(陪伴模式)")
        ]
        for button_name, text in menu_buttons:
            if button_name in self.buttons:
                self._draw_button(self.buttons[button_name], text, self.fonts['button'])
    
    def _render_game(self):
        """渲染游戏界面"""
        # 渲染棋盘
        board_offset = (self.panels['board'].x, self.panels['board'].y)
        self.board_renderer.render_board(self.screen, board_offset)
        
        # 渲染高亮和提示
        if self.game_state.highlighted_squares:
            self.board_renderer.render_highlights(self.screen, 
                                                 self.game_state.highlighted_squares, 
                                                 board_offset)
        
        if self.game_state.move_hints:
            self.board_renderer.render_move_hints(self.screen, 
                                                 self.game_state.move_hints, 
                                                 board_offset)
        
        # 渲染上一步移动
        if self.game_state.board.move_history:
            last_move = self.game_state.board.move_history[-1]
            self.board_renderer.render_last_move(self.screen, last_move, board_offset)
        
        # 渲染将军警告
        current_player = self.game_state.board.current_player
        if self.game_state.board.is_in_check(current_player):
            king_pos = self.game_state.board.get_king_position(current_player)
            if king_pos:
                self.board_renderer.render_check_warning(self.screen, king_pos, board_offset)
        
        # 渲染棋子（不在动画中的）
        pieces_to_render = {}
        animated_pieces = {anim['piece'] for anim in self.animation_manager.animations if anim['type'] == 'move'}
        
        for pos, piece in self.game_state.board.pieces.items():
            if piece not in animated_pieces:
                pieces_to_render[pos] = piece
        
        self.board_renderer.render_pieces(self.screen, pieces_to_render, board_offset)
        
        # 渲染动画
        self.animation_manager.render_animations(self.screen, self.board_renderer, board_offset)
        
        # 渲染UI面板
        self._render_game_info()
        self._render_move_history()
        self._render_captured_pieces()
        self._render_game_buttons()
        
        # 渲染AI思考进度指示器
        self._render_ai_thinking_indicator()
    
    def _render_game_info(self):
        """渲染游戏信息面板"""
        panel = self.panels['info']
        pygame.draw.rect(self.screen, COLORS['UI_PANEL'], panel)
        pygame.draw.rect(self.screen, COLORS['TEXT'], panel, 2)
        
        y_offset = panel.y + 10
        
        # 当前玩家
        current_player_info = self.game_state.get_current_player_info()
        text = f"Current: {current_player_info['name']}"
        if current_player_info['in_check']:
            text += " (IN CHECK!)"
        
        rendered_text = self.fonts['info'].render(text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
        y_offset += 30
        
        # 游戏模式
        mode_text = f"Mode: {self.game_state.mode.value}"
        rendered_text = self.fonts['small'].render(mode_text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
        y_offset += 25
        
        # AI难度
        if self.game_state.mode == GameMode.HUMAN_VS_AI:
            ai_text = f"AI Level: {self.game_state.ai_level}"
            rendered_text = self.fonts['small'].render(ai_text, True, COLORS['TEXT'])
            self.screen.blit(rendered_text, (panel.x + 10, y_offset))
            y_offset += 25
        
        # 移动计数
        move_count = len(self.game_state.board.move_history)
        move_text = f"Moves: {move_count}"
        rendered_text = self.fonts['small'].render(move_text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
        y_offset += 25
        
        # 游戏时间
        game_info = self.game_state.get_game_info()
        time_text = f"Time: {int(game_info['game_time'] // 60):02d}:{int(game_info['game_time'] % 60):02d}"
        rendered_text = self.fonts['small'].render(time_text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
    
    def _render_move_history(self):
        """渲染移动历史"""
        panel = self.panels['moves']
        pygame.draw.rect(self.screen, COLORS['UI_PANEL'], panel)
        pygame.draw.rect(self.screen, COLORS['TEXT'], panel, 2)
        
        # 标题
        title = self.fonts['info'].render("Move History", True, COLORS['TEXT'])
        self.screen.blit(title, (panel.x + 10, panel.y + 10))
        
        # 显示最近的移动
        y_offset = panel.y + 40
        moves = self.game_state.board.move_history[-8:]  # 显示最近8步
        
        for i, move in enumerate(moves):
            move_num = len(self.game_state.board.move_history) - len(moves) + i + 1
            notation = getattr(move, 'notation', f"{move['from']} -> {move['to']}")
            text = f"{move_num}. {notation}"
            
            rendered_text = self.fonts['small'].render(text, True, COLORS['TEXT'])
            self.screen.blit(rendered_text, (panel.x + 10, y_offset))
            y_offset += 20
            
            if y_offset > panel.bottom - 20:
                break
    
    def _render_captured_pieces(self):
        """渲染被吃棋子"""
        panel = self.panels['captured']
        pygame.draw.rect(self.screen, COLORS['UI_PANEL'], panel)
        pygame.draw.rect(self.screen, COLORS['TEXT'], panel, 2)
        
        title = self.fonts['info'].render("Captured", True, COLORS['TEXT'])
        self.screen.blit(title, (panel.x + 10, panel.y + 10))
        
        # 显示被吃的棋子
        y_offset = panel.y + 35
        
        for color in ['white', 'black']:
            captured = self.game_state.board.captured_pieces[color]
            if captured:
                color_text = f"{color.capitalize()}: "
                # 使用简单文字而不是Unicode符号，避免字体渲染问题
                piece_names = []
                for piece in captured:
                    piece_name = piece.piece_type.name.capitalize()
                    piece_names.append(piece_name)
                
                pieces_text = ", ".join(piece_names)
                text = color_text + pieces_text
                
                rendered_text = self.fonts['small'].render(text, True, COLORS['TEXT'])
                self.screen.blit(rendered_text, (panel.x + 10, y_offset))
                y_offset += 20
    
    def _render_game_buttons(self):
        """渲染游戏按钮"""
        game_buttons = [
            ('new_game', "New Game"),
            ('undo', "Undo"),
            ('pause', "Pause" if self.game_state.state == GameState.PLAYING else "Resume"),
            ('menu', "Menu"),
            ('assistant', "🤖 Assistant")  # 总是显示助手按钮
        ]
        
        # 如果是陪伴模式，添加“助手”按钮
        if (self.game_state.mode == GameMode.HUMAN_VS_AI and 
            self.game_state.ai_level == 'COMPANION'):
            companion_buttons = [
                ('assistant', "🤖 Assistant")
            ]
            game_buttons.extend(companion_buttons)
        
        for button_name, text in game_buttons:
            if button_name in self.buttons:
                # 动态更新助手按钮文本
                if button_name == 'assistant':
                    text = self._update_assistant_button_text()
                
                # 陪伴模式按钮使用特殊颜色
                is_companion_button = button_name in ['assistant']
                if is_companion_button:
                    self._draw_companion_button(self.buttons[button_name], text, self.fonts['small'])
                else:
                    self._draw_button(self.buttons[button_name], text, self.fonts['small'])
    
    def _draw_button(self, rect: pygame.Rect, text: str, font: pygame.font.Font, 
                    hover: bool = False):
        """绘制按钮"""
        color = COLORS['BUTTON_HOVER'] if hover else COLORS['BUTTON']
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLORS['TEXT'], rect, 2)
        
        text_surface = font.render(text, True, COLORS['TEXT'])
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_companion_button(self, rect: pygame.Rect, text: str, font: pygame.font.Font):
        """绘制陪伴模式特殊按钮"""
        # 使用渐变色背景表示这是特殊功能
        companion_color = (100, 149, 237)  # 天蓝色
        companion_hover_color = (135, 206, 250)  # 浅天蓝色
        
        pygame.draw.rect(self.screen, companion_color, rect)
        pygame.draw.rect(self.screen, COLORS['TEXT'], rect, 2)
        
        # 添加发光效果
        glow_rect = rect.inflate(4, 4)
        pygame.draw.rect(self.screen, companion_hover_color, glow_rect, 1)
        
        text_surface = font.render(text, True, COLORS['TEXT'])
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _show_game_over_message(self, game_data: Dict):
        """显示游戏结束消息"""
        winner = game_data.get('winner', 'draw')
        
        if winner == 'draw':
            message = "Game Over - Draw!"
        else:
            message = f"Game Over - {winner.capitalize()} Wins!"
        
        # 这里可以实现一个模态对话框
        print(message)  # 临时使用print
    
    def _render_ai_thinking_indicator(self):
        """渲染AI思考进度指示器"""
        # 只有在AI思考时才显示
        if not hasattr(self, '_ai_thinking') or not self._ai_thinking:
            return
            
        # 计算思考时间
        thinking_time = time.time() - getattr(self, '_ai_thinking_start_time', time.time())
        
        # 在棋盘右上角显示思考指示器
        indicator_rect = pygame.Rect(
            self.panels['board'].right - 200, 
            self.panels['board'].y + 10, 
            180, 60
        )
        
        # 半透明背景
        overlay = pygame.Surface((indicator_rect.width, indicator_rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 半透明黑色
        self.screen.blit(overlay, indicator_rect.topleft)
        
        # 边框
        pygame.draw.rect(self.screen, COLORS['ACCENT'], indicator_rect, 2)
        
        # 文本内容
        ai_level = getattr(self.game_state, 'ai_level', 'AI')
        thinking_text = f"{ai_level} AI 思考中..."
        time_text = f"{thinking_time:.1f}s"
        
        # 渲染文本
        try:
            # 主文本
            text_surface = self.fonts['small'].render(thinking_text, True, COLORS['TEXT'])
            text_rect = pygame.Rect(indicator_rect.x + 10, indicator_rect.y + 10, 
                                  indicator_rect.width - 20, 20)
            text_pos = text_rect.topleft
            self.screen.blit(text_surface, text_pos)
            
            # 时间文本
            time_surface = self.fonts['small'].render(time_text, True, COLORS['ACCENT'])
            time_rect = pygame.Rect(indicator_rect.x + 10, indicator_rect.y + 35, 
                                  indicator_rect.width - 20, 20)
            time_pos = time_rect.topleft
            self.screen.blit(time_surface, time_pos)
            
            # 动态进度条（使用点点点动画）
            dots_count = int(thinking_time * 2) % 4  # 每0.5秒变化一次，0-3个点
            dots_text = "." * dots_count
            if dots_text:
                dots_surface = self.fonts['small'].render(dots_text, True, COLORS['ACCENT'])
                dots_pos = (indicator_rect.right - 30, indicator_rect.y + 10)
                self.screen.blit(dots_surface, dots_pos)
            
        except Exception as e:
            # 如果渲染失败，至少显示一个简单指示器
            pygame.draw.circle(self.screen, COLORS['ACCENT'], 
                             (indicator_rect.centerx, indicator_rect.centery), 10)
            # 旋转动画效果
            angle = int(thinking_time * 180) % 360
            import math
            x = indicator_rect.centerx + int(15 * math.cos(math.radians(angle)))
            y = indicator_rect.centery + int(15 * math.sin(math.radians(angle)))
            pygame.draw.circle(self.screen, COLORS['HIGHLIGHT'], (x, y), 3)
        
        # 如果思考时间过长，显示警告
        if thinking_time > 8.0:
            warning_text = "AI响应较慢，请稍等..."
            warning_surface = self.fonts['small'].render(warning_text, True, (255, 200, 0))
            warning_pos = (indicator_rect.x, indicator_rect.bottom + 5)
            self.screen.blit(warning_surface, warning_pos)

def main():
    """主函数"""
    chess_ui = ChessUI()
    chess_ui.run()

if __name__ == "__main__":
    main()
