"""
Chess AI Agent 语音系统 (Voice System)
实现TTS语音合成和STT语音识别，支持实时语音陪伴聊天

核心功能：
- TTS文本转语音（支持多种语音和情感）
- STT语音转文本（实时语音识别）
- 语音对话管理
- 情感语音表达
- 多语言支持
- 语音指令识别
"""

import asyncio
import json
import logging
import os
import tempfile
import time
import threading
import queue
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import wave
import io

"""分开检测各个语音依赖，保证最小可用TTS路径"""
PYAUDIO_AVAILABLE = False
SR_AVAILABLE = False
PYTTSX3_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except Exception:
    PYAUDIO_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False

# 平台特定的语音识别支持
import platform
PLATFORM = platform.system()

# Windows语音识别支持
WIN_SPEECH_AVAILABLE = False
if PLATFORM == "Windows":
    try:
        import win32com.client
        WIN_SPEECH_AVAILABLE = True
    except Exception:
        WIN_SPEECH_AVAILABLE = False

# macOS语音识别支持
MACOS_SPEECH_AVAILABLE = False  
if PLATFORM == "Darwin":
    import subprocess
    try:
        # 检查macOS语音识别可用性
        result = subprocess.run(['which', 'osascript'], capture_output=True, text=True)
        MACOS_SPEECH_AVAILABLE = result.returncode == 0
    except Exception:
        MACOS_SPEECH_AVAILABLE = False

BASIC_VOICE_AVAILABLE = PYTTSX3_AVAILABLE  # 仅TTS也视为可用

try:
    import openai
    from openai import OpenAI
    OPENAI_VOICE_AVAILABLE = True
except ImportError:
    print("⚠️ OpenAI库未安装，无法使用OpenAI语音服务")
    OPENAI_VOICE_AVAILABLE = False

class VoiceProvider(Enum):
    """语音服务提供商"""
    SYSTEM = "system"      # 系统默认TTS
    OPENAI = "openai"      # OpenAI TTS/STT
    LOCAL = "local"        # 本地语音引擎

class EmotionType(Enum):
    """情感类型"""
    NEUTRAL = "neutral"
    EXCITED = "excited"
    FRIENDLY = "friendly"
    SERIOUS = "serious"
    ENCOURAGING = "encouraging"
    THINKING = "thinking"
    CONGRATULATING = "congratulating"

class VoiceGender(Enum):
    """语音性别"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

@dataclass
class VoiceSettings:
    """语音设置"""
    provider: VoiceProvider
    voice_id: str = "default"
    gender: VoiceGender = VoiceGender.NEUTRAL
    language: str = "zh-CN"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    emotion: EmotionType = EmotionType.NEUTRAL

@dataclass
class VoiceMessage:
    """语音消息"""
    text: str
    emotion: EmotionType
    timestamp: datetime
    audio_file: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class RecognitionResult:
    """语音识别结果"""
    text: str
    confidence: float
    language: str
    timestamp: datetime
    duration: float
    alternative_texts: List[str] = None
    
    def __post_init__(self):
        if self.alternative_texts is None:
            self.alternative_texts = []

class ChessVoiceSystem:
    """Chess AI Agent 语音系统"""
    
    def __init__(self,
                 api_key: str = None,
                 voice_settings: VoiceSettings = None,
                 enable_continuous_listening: bool = False,
                 audio_cache_dir: str = None):
        """
        初始化语音系统
        
        Args:
            api_key: OpenAI API密钥
            voice_settings: 语音设置
            enable_continuous_listening: 启用连续监听
            audio_cache_dir: 音频缓存目录
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.enable_continuous_listening = enable_continuous_listening
        
        # 语音设置
        self.voice_settings = voice_settings or VoiceSettings(VoiceProvider.SYSTEM)
        
        # 音频缓存目录
        self.audio_cache_dir = audio_cache_dir or os.path.join(
            tempfile.gettempdir(), "chess_ai_voice_cache"
        )
        os.makedirs(self.audio_cache_dir, exist_ok=True)
        
        # 日志设置
        self.logger = logging.getLogger(f"ChessVoiceSystem_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # 状态管理
        self.is_speaking = False
        self.is_listening = False
        self.conversation_active = False
        
        # 语音队列
        self.tts_queue = queue.Queue()
        self.stt_queue = queue.Queue()
        
        # 延迟清理文件队列
        self.cleanup_queue = queue.Queue()
        
        # 回调函数
        self.on_speech_recognized: Optional[Callable[[str], None]] = None
        self.on_speech_error: Optional[Callable[[str], None]] = None
        self.on_speech_start: Optional[Callable[[], None]] = None
        self.on_speech_end: Optional[Callable[[], None]] = None
        
        # 统计信息
        self.stats = {
            'tts_calls': 0,
            'stt_calls': 0,
            'total_speech_time': 0.0,
            'total_listening_time': 0.0,
            'recognition_errors': 0,
            'synthesis_errors': 0
        }
        
        # 初始化语音引擎
        self._init_voice_engines()
        
        # 启动工作线程
        self._start_worker_threads()
        
        self.logger.info(f"语音系统初始化完成，提供商: {self.voice_settings.provider.value}")
    
    def _init_voice_engines(self):
        """初始化语音引擎"""
        self.engines = {}
        
        # 初始化系统TTS（仅需pyttsx3），若可用则尽力初始化STT
        if BASIC_VOICE_AVAILABLE:
            try:
                engine_dict = {'tts': pyttsx3.init()}
                if SR_AVAILABLE:
                    try:
                        engine_dict['stt'] = sr.Recognizer()
                    except Exception:
                        pass
                self.engines[VoiceProvider.SYSTEM] = engine_dict
                self._configure_system_tts()
                self.logger.info("✅ 系统语音引擎初始化成功")
            except Exception as e:
                self.logger.error(f"系统语音引擎初始化失败: {e}")
        
        # 初始化OpenAI语音
        if OPENAI_VOICE_AVAILABLE and self.api_key:
            try:
                self.engines[VoiceProvider.OPENAI] = {
                    'client': OpenAI(
                        api_key=self.api_key,
                        timeout=30.0  # 设置30秒超时
                    )
                }
                self.logger.info("✅ OpenAI语音服务初始化成功")
            except Exception as e:
                self.logger.error(f"OpenAI语音服务初始化失败: {e}")
    
    def _configure_system_tts(self):
        """配置系统TTS设置"""
        if VoiceProvider.SYSTEM not in self.engines:
            return
        
        tts_engine = self.engines[VoiceProvider.SYSTEM]['tts']
        
        try:
            # 设置语音属性
            tts_engine.setProperty('rate', int(150 * self.voice_settings.speed))
            tts_engine.setProperty('volume', self.voice_settings.volume)
            
            # 选择语音
            voices = tts_engine.getProperty('voices')
            if voices:
                # 选择合适的语音（简化选择逻辑）
                selected_voice = voices[0]  # 默认选择第一个
                
                for voice in voices:
                    # 优先选择中文语音
                    if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                        selected_voice = voice
                        break
                    # 或者根据性别选择
                    elif (self.voice_settings.gender == VoiceGender.FEMALE and 
                          'female' in voice.name.lower()):
                        selected_voice = voice
                        break
                
                tts_engine.setProperty('voice', selected_voice.id)
                self.logger.info(f"选择语音: {selected_voice.name}")
        
        except Exception as e:
            self.logger.warning(f"配置系统TTS失败: {e}")
    
    def _start_worker_threads(self):
        """启动工作线程"""
        self.running = True
        self._stop_event = threading.Event()
        
        # TTS工作线程
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # 延迟清理工作线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        # 连续监听线程
        if self.enable_continuous_listening:
            self.listening_thread = threading.Thread(target=self._continuous_listening_worker, daemon=True)
            self.listening_thread.start()
    
    def _tts_worker(self):
        """TTS工作线程（改进版）"""
        while self.running and not self._stop_event.is_set():
            try:
                # 从队列获取TTS任务
                task = self.tts_queue.get(timeout=0.5)
                if task is None:  # 退出信号
                    break
                
                text, emotion, callback = task['text'], task['emotion'], task.get('callback')
                
                # 检查是否需要停止
                if self._stop_event.is_set():
                    if callback:
                        callback(False)
                    self.tts_queue.task_done()
                    continue
                
                # 执行语音合成
                success = self._synthesize_speech_internal(text, emotion)
                
                # 调用回调函数
                if callback:
                    callback(success)
                
                self.tts_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"TTS工作线程错误: {e}")
                # 添加短暂延迟避免无限循环
                time.sleep(0.1)
    
    def _continuous_listening_worker(self):
        """连续监听工作线程（改进版）"""
        while self.running and not self._stop_event.is_set():
            try:
                if self.conversation_active and not self.is_speaking:
                    # 添加短超时的语音识别避免长时间阻塞
                    result = self._recognize_speech_internal(timeout=3.0, phrase_timeout=1.5)
                    
                    if result and result.text.strip() and not self._stop_event.is_set():
                        if self.on_speech_recognized:
                            try:
                                self.on_speech_recognized(result.text)
                            except Exception as e:
                                self.logger.error(f"语音识别回调错误: {e}")
                
                # 检查停止事件
                if self._stop_event.wait(timeout=0.5):
                    break
                
            except Exception as e:
                self.logger.error(f"连续监听线程错误: {e}")
                # 错误后等待更长时间避免资源消耗
                if not self._stop_event.wait(timeout=2.0):
                    continue
                else:
                    break
    
    def _cleanup_worker(self):
        """延迟清理文件工作线程 - 增强版本，支持重试和强制清理"""
        while self.running and not self._stop_event.is_set():
            try:
                # 获取要清理的文件和延迟时间
                cleanup_task = self.cleanup_queue.get(timeout=1.0)
                if cleanup_task is None:  # 退出信号
                    break
                
                file_path, delay_seconds = cleanup_task
                
                # 等待指定延迟时间
                if not self._stop_event.wait(timeout=delay_seconds):
                    # 改进的文件删除策略，支持多次重试
                    max_retries = 5
                    retry_delays = [0.5, 1.0, 2.0, 4.0, 8.0]  # 指数退避重试延迟
                    
                    for attempt in range(max_retries):
                        try:
                            if os.path.exists(file_path):
                                # Windows特定：尝试强制解除文件锁定
                                if hasattr(os, 'name') and os.name == 'nt':
                                    # 强制垃圾回收，释放可能的文件句柄
                                    import gc
                                    gc.collect()
                                    
                                    # 确保pygame音乐播放器已完全释放
                                    try:
                                        import pygame
                                        if pygame.mixer.get_init():
                                            pygame.mixer.music.stop()
                                            # 不重新初始化，避免影响其他音频
                                    except:
                                        pass
                                
                                # 尝试删除文件
                                os.remove(file_path)
                                self.logger.debug(f"成功清理临时文件: {file_path} (尝试 {attempt + 1}/{max_retries})")
                                break  # 删除成功，跳出重试循环
                            else:
                                self.logger.debug(f"文件已不存在，无需清理: {file_path}")
                                break
                        except PermissionError as pe:
                            if attempt < max_retries - 1:  # 不是最后一次尝试
                                retry_delay = retry_delays[attempt]
                                self.logger.warning(f"文件被占用，将在 {retry_delay}s 后重试删除: {file_path} (尝试 {attempt + 1}/{max_retries})")
                                if self._stop_event.wait(timeout=retry_delay):
                                    break  # 如果收到停止信号，退出重试
                            else:
                                # 最后一次尝试失败，记录错误但不强制删除
                                self.logger.error(f"多次尝试删除失败，文件可能被其他程序占用: {file_path}")
                        except Exception as cleanup_err:
                            self.logger.warning(f"删除临时文件失败: {file_path}, 错误: {cleanup_err}")
                            if attempt == max_retries - 1:  # 最后一次尝试
                                self.logger.error(f"文件清理彻底失败: {file_path}")
                            break
                
                self.cleanup_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"清理工作线程错误: {e}")
                # 添加短暂延迟避免无限循环
                time.sleep(0.5)
    
    def _schedule_file_cleanup(self, file_path: str, delay_seconds: float = 2.0):
        """调度延迟文件清理"""
        try:
            self.cleanup_queue.put((file_path, delay_seconds))
            self.logger.debug(f"调度延迟清理文件: {file_path} (延迟{delay_seconds}秒)")
        except Exception as e:
            self.logger.error(f"调度文件清理失败: {e}")
    
    async def speak_async(self, 
                         text: str, 
                         emotion: EmotionType = EmotionType.NEUTRAL,
                         wait_for_completion: bool = True) -> bool:
        """
        异步语音合成
        
        Args:
            text: 要合成的文本
            emotion: 情感类型
            wait_for_completion: 是否等待完成
            
        Returns:
            合成是否成功
        """
        try:
            self.stats['tts_calls'] += 1
            
            if wait_for_completion:
                # 同步执行
                return await asyncio.to_thread(self._synthesize_speech_internal, text, emotion)
            else:
                # 异步执行（加入队列）
                future = asyncio.Future()
                
                def callback(success):
                    if not future.done():
                        future.set_result(success)
                
                self.tts_queue.put({
                    'text': text,
                    'emotion': emotion,
                    'callback': callback
                })
                
                return await future
        
        except Exception as e:
            self.logger.error(f"异步语音合成失败: {e}")
            self.stats['synthesis_errors'] += 1
            return False
    
    def speak(self, 
              text: str, 
              emotion: EmotionType = EmotionType.NEUTRAL,
              blocking: bool = True) -> bool:
        """
        同步语音合成
        
        Args:
            text: 要合成的文本  
            emotion: 情感类型
            blocking: 是否阻塞等待
            
        Returns:
            合成是否成功
        """
        try:
            self.stats['tts_calls'] += 1
            
            if blocking:
                return self._synthesize_speech_internal(text, emotion)
            else:
                # 加入队列异步执行
                self.tts_queue.put({
                    'text': text,
                    'emotion': emotion,
                    'callback': None
                })
                return True
        
        except Exception as e:
            self.logger.error(f"语音合成失败: {e}")
            self.stats['synthesis_errors'] += 1
            return False
    
    def _synthesize_speech_internal(self, text: str, emotion: EmotionType) -> bool:
        """内部语音合成实现"""
        if not text or not text.strip():
            return False
        
        self.is_speaking = True
        start_time = time.time()
        
        try:
            # 根据配置的提供商选择合成方法
            if self.voice_settings.provider == VoiceProvider.OPENAI:
                success = self._synthesize_openai(text, emotion)
                # 如果OpenAI语音失败，自动回退到系统TTS
                if not success:
                    success = self._synthesize_system(text, emotion)
            else:
                success = self._synthesize_system(text, emotion)
            
            duration = time.time() - start_time
            self.stats['total_speech_time'] += duration
            
            self.logger.info(f"语音合成完成: {text[:30]}... ({duration:.2f}s)")
            return success
        
        except Exception as e:
            self.logger.error(f"语音合成内部错误: {e}")
            return False
        
        finally:
            self.is_speaking = False
    
    def _synthesize_system(self, text: str, emotion: EmotionType) -> bool:
        """使用系统TTS合成语音"""
        if VoiceProvider.SYSTEM not in self.engines:
            return False
        
        try:
            tts_engine = self.engines[VoiceProvider.SYSTEM]['tts']
            
            # 根据情感调整语音参数
            rate = int(150 * self.voice_settings.speed)
            if emotion == EmotionType.EXCITED:
                rate = int(rate * 1.2)
            elif emotion == EmotionType.THINKING:
                rate = int(rate * 0.8)
            
            tts_engine.setProperty('rate', rate)
            
            # 执行语音合成
            tts_engine.say(text)
            tts_engine.runAndWait()
            
            return True
        
        except Exception as e:
            self.logger.error(f"系统TTS合成失败: {e}")
            return False
    
    def _synthesize_openai(self, text: str, emotion: EmotionType) -> bool:
        """使用OpenAI TTS合成语音 - 改进文件处理策略"""
        if VoiceProvider.OPENAI not in self.engines:
            return False
        
        try:
            client = self.engines[VoiceProvider.OPENAI]['client']
            
            # 选择合适的语音模型
            voice_map = {
                EmotionType.FRIENDLY: "alloy",
                EmotionType.SERIOUS: "echo", 
                EmotionType.ENCOURAGING: "fable",
                EmotionType.NEUTRAL: "nova"
            }
            
            voice = voice_map.get(emotion, "nova")
            
            self.logger.info(f"调用OpenAI TTS: 文本={text[:50]}..., 语音={voice}")
            
            # 调用OpenAI TTS，添加超时处理
            try:
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    speed=self.voice_settings.speed
                )
                self.logger.info("OpenAI TTS响应成功，开始保存音频")
            except Exception as api_err:
                self.logger.error(f"OpenAI API调用失败: {api_err}")
                return False
            
            # 改进的音频文件处理策略
            timestamp = int(time.time() * 1000)  # 毫秒时间戳提高唯一性
            original_file = os.path.join(self.audio_cache_dir, f"tts_orig_{timestamp}.mp3")
            playback_file = os.path.join(self.audio_cache_dir, f"tts_play_{timestamp}.mp3")
            
            try:
                # 1. 保存原始文件
                response.stream_to_file(original_file)
                self.logger.info(f"音频保存到: {original_file}")
                
                # 2. 复制文件用于播放，避免原文件被锁定
                import shutil
                shutil.copy2(original_file, playback_file)
                self.logger.debug(f"复制播放文件: {playback_file}")
                
                # 3. 立即删除原始文件，保留播放文件
                try:
                    os.remove(original_file)
                    self.logger.debug(f"清理原始文件: {original_file}")
                except Exception as cleanup_err:
                    self.logger.warning(f"清理原始文件失败: {cleanup_err}")
                
                # 4. 播放复制的音频文件
                self._play_audio_file_safe(playback_file)
                
                # 5. 延迟清理播放文件，使用更长的延迟时间
                self._schedule_file_cleanup(playback_file, delay_seconds=5.0)
                
                return True
                
            except Exception as save_err:
                self.logger.error(f"保存或播放音频失败: {save_err}")
                # 清理所有可能的文件
                for cleanup_file in [original_file, playback_file]:
                    try:
                        if os.path.exists(cleanup_file):
                            os.remove(cleanup_file)
                            self.logger.debug(f"清理失败的音频文件: {cleanup_file}")
                    except Exception as cleanup_err:
                        self.logger.warning(f"清理失败音频文件失败: {cleanup_err}")
                return False
            
        except Exception as e:
            self.logger.error(f"OpenAI TTS合成失败: {e}")
            return False
    
    def _create_emotional_ssml(self, text: str, emotion: EmotionType) -> str:
        """创建带情感的SSML"""
        emotion_styles = {
            EmotionType.EXCITED: "excited",
            EmotionType.FRIENDLY: "friendly",
            EmotionType.SERIOUS: "serious",
            EmotionType.ENCOURAGING: "cheerful",
            EmotionType.THINKING: "calm"
        }
        
        style = emotion_styles.get(emotion, "neutral")
        
        ssml = f"""
        <speak version='1.0' xml:lang='zh-CN'>
            <voice xml:lang='zh-CN' xml:gender='Female' name='zh-CN-XiaoxiaoNeural'>
                <prosody style='{style}'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        return ssml
    
    def _play_audio_file_safe(self, file_path: str):
        """安全播放音频文件（改进版本，减少文件锁定）"""
        try:
            # 优先尝试pygame.mixer
            try:
                import pygame
                # 初始化混音器（若未初始化，且只初始化一次）
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                
                # 在后台线程播放，避免阻塞主线程
                def play_in_background():
                    try:
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.play()
                        self.logger.info(f"后台播放音频文件: {file_path}")
                        
                        # 非阻塞等待播放完成
                        max_wait_time = 15.0  # 最大等待15秒
                        wait_start = time.time()
                        check_interval = 0.1
                        
                        while pygame.mixer.music.get_busy():
                            if time.time() - wait_start > max_wait_time:
                                self.logger.warning("音频播放超时，强制停止")
                                pygame.mixer.music.stop()
                                break
                            time.sleep(check_interval)
                        
                        # 播放完成后尝试立即停止，释放文件句柄
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()  # 如果支持的话
                        
                        self.logger.info("音频播放完成，已释放文件句柄")
                        
                    except Exception as bg_err:
                        self.logger.warning(f"后台播放过程出错: {bg_err}")
                
                # 启动后台播放线程
                threading.Thread(target=play_in_background, daemon=True).start()
                
                # 主线程立即返回，不阻塞
                return
                
            except Exception as pg_err:
                self.logger.warning(f"pygame播放失败，尝试备用方案: {pg_err}")

            # 备用方案：异步系统播放器
            self._play_audio_system_async(file_path)

        except Exception as e:
            self.logger.error(f"播放音频文件失败: {e}")
    
    def _play_audio_system_async(self, file_path: str):
        """异步使用系统播放器播放音频"""
        def play_system():
            try:
                import platform
                system = platform.system()
                
                if system == "Windows":
                    # Windows: 使用异步播放
                    try:
                        import subprocess
                        # 使用非阻塞方式启动播放器
                        subprocess.Popen(['powershell', '-c', f'(New-Object Media.SoundPlayer "{file_path}").PlaySync()'], 
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                        self.logger.info("使用Windows系统播放器播放音频")
                    except Exception as win_err:
                        # 回退到winsound
                        import winsound
                        winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        self.logger.info("使用winsound异步播放音频")
                elif system == "Darwin":  # macOS
                    subprocess.Popen(['afplay', file_path], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.logger.info("使用afplay异步播放音频")
                else:  # Linux
                    subprocess.Popen(['aplay', file_path], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.logger.info("使用aplay异步播放音频")
                    
            except Exception as e:
                self.logger.error(f"系统播放器异步播放失败: {e}")
        
        # 在后台线程执行播放
        threading.Thread(target=play_system, daemon=True).start()

    def _play_audio_file(self, file_path: str):
        """播放音频文件（保留原方法用于兼容性）"""
        return self._play_audio_file_safe(file_path)
    
    async def listen_async(self, 
                          timeout: float = 5.0,
                          phrase_timeout: float = 1.0) -> Optional[RecognitionResult]:
        """
        异步语音识别
        
        Args:
            timeout: 总超时时间
            phrase_timeout: 短语超时时间
            
        Returns:
            识别结果
        """
        try:
            self.stats['stt_calls'] += 1
            
            return await asyncio.to_thread(
                self._recognize_speech_internal,
                timeout,
                phrase_timeout
            )
        
        except Exception as e:
            self.logger.error(f"异步语音识别失败: {e}")
            self.stats['recognition_errors'] += 1
            return None
    
    def listen(self, 
               timeout: float = 5.0,
               phrase_timeout: float = 1.0) -> Optional[RecognitionResult]:
        """
        同步语音识别
        
        Args:
            timeout: 总超时时间
            phrase_timeout: 短语超时时间
            
        Returns:
            识别结果
        """
        try:
            self.stats['stt_calls'] += 1
            
            return self._recognize_speech_internal(timeout, phrase_timeout)
        
        except Exception as e:
            self.logger.error(f"语音识别失败: {e}")
            self.stats['recognition_errors'] += 1
            return None
    
    def _recognize_speech_internal(self, 
                                  timeout: float = 5.0,
                                  phrase_timeout: float = 1.0) -> Optional[RecognitionResult]:
        """内部语音识别实现"""
        if not BASIC_VOICE_AVAILABLE:
            self.logger.warning("语音识别库不可用")
            return None
        
        self.is_listening = True
        start_time = time.time()
        
        try:
            if self.on_speech_start:
                self.on_speech_start()
            
            # 根据配置的提供商选择识别方法
            if self.voice_settings.provider == VoiceProvider.OPENAI:
                result = self._recognize_openai(timeout)
            else:
                result = self._recognize_system(timeout, phrase_timeout)
            
            duration = time.time() - start_time
            self.stats['total_listening_time'] += duration
            
            if result:
                self.logger.info(f"语音识别成功: {result.text} (置信度: {result.confidence:.2f})")
            
            return result
        
        except Exception as e:
            self.logger.error(f"语音识别内部错误: {e}")
            return None
        
        finally:
            self.is_listening = False
            if self.on_speech_end:
                self.on_speech_end()
    
    def _recognize_system(self, 
                         timeout: float = 5.0,
                         phrase_timeout: float = 1.0) -> Optional[RecognitionResult]:
        """使用系统语音识别（优先平台原生，备用SR库）"""
        
        # 1. 优先使用平台原生语音识别
        if PLATFORM == "Windows" and WIN_SPEECH_AVAILABLE:
            return self._recognize_windows_native(timeout)
        elif PLATFORM == "Darwin" and MACOS_SPEECH_AVAILABLE:
            return self._recognize_macos_native(timeout)
        
        # 2. 备用：使用speech_recognition库
        if VoiceProvider.SYSTEM not in self.engines or 'stt' not in self.engines[VoiceProvider.SYSTEM]:
            self.logger.warning("语音识别引擎不可用")
            return None
        
        try:
            recognizer = self.engines[VoiceProvider.SYSTEM]['stt']
            
            # 使用麦克风
            with sr.Microphone() as source:
                self.logger.info("🎤 请说话...")
                
                # 调整环境噪声
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # 监听语音
                audio = recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_timeout
                )
            
            # 识别语音 - 优先中文，备用英文
            try:
                text = recognizer.recognize_google(audio, language="zh-CN")
            except:
                try:
                    text = recognizer.recognize_google(audio, language="en-US")
                except:
                    # 尝试其他引擎
                    try:
                        text = recognizer.recognize_sphinx(audio)
                    except:
                        raise sr.UnknownValueError("所有识别引擎都失败")
            
            return RecognitionResult(
                text=text,
                confidence=1.0,  # Google API不提供置信度
                language=self.voice_settings.language,
                timestamp=datetime.now(),
                duration=phrase_timeout
            )
        
        except sr.WaitTimeoutError:
            self.logger.info("语音识别超时")
            return None
        except sr.UnknownValueError:
            self.logger.warning("无法识别语音")
            return None
        except sr.RequestError as e:
            self.logger.error(f"语音识别服务错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"语音识别异常: {e}")
            return None
    
    def _recognize_windows_native(self, timeout: float = 5.0) -> Optional[RecognitionResult]:
        """Windows原生语音识别（改进版）"""
        try:
            self.logger.info("🎤 使用Windows语音识别，请说话...")
            
            start_time = time.time()
            
            # 简化的PowerShell脚本，避免复杂的语音引擎初始化
            powershell_script = f'''
try {{
    Add-Type -AssemblyName System.Speech
    $recognize = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $recognize.SetInputToDefaultAudioDevice()
    
    # 设置更短的超时时间避免卡住
    $recognize.BabbleTimeout = New-TimeSpan -Seconds {min(timeout, 8)}
    $recognize.InitialSilenceTimeout = New-TimeSpan -Seconds {min(timeout, 8)}
    $recognize.EndSilenceTimeout = New-TimeSpan -Seconds 1
    
    # 加载简单的听写语法
    $grammar = New-Object System.Speech.Recognition.DictationGrammar
    $recognize.LoadGrammar($grammar)
    
    # 异步识别，避免长时间阻塞
    $result = $recognize.Recognize()
    
    if ($result -and $result.Text) {{
        Write-Output $result.Text.Trim()
    }} else {{
        Write-Output "TIMEOUT"
    }}
}} catch {{
    Write-Output "ERROR: $($_.Exception.Message)"
}} finally {{
    if ($recognize) {{
        $recognize.Dispose()
    }}
}}
'''
            
            # 使用更安全的subprocess调用
            import subprocess
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("PowerShell语音识别超时")
            
            try:
                # 在Windows上设置超时处理（注意Windows不支持SIGALRM）
                process = subprocess.Popen([
                    'powershell', '-Command', powershell_script
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, 
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                
                # 等待进程完成，最多等待timeout+3秒
                try:
                    stdout, stderr = process.communicate(timeout=timeout+3)
                    
                    if process.returncode == 0 and stdout:
                        text = stdout.strip()
                        if text and text not in ["TIMEOUT", "ERROR"]:
                            return RecognitionResult(
                                text=text,
                                confidence=0.8,
                                language="zh-CN",
                                timestamp=datetime.now(),
                                duration=time.time() - start_time
                            )
                        elif text.startswith("ERROR"):
                            self.logger.warning(f"PowerShell语音识别错误: {text}")
                    
                except subprocess.TimeoutExpired:
                    self.logger.warning("PowerShell语音识别超时，强制终止进程")
                    process.kill()
                    process.wait()
                
                return None
                
            except Exception as e:
                self.logger.error(f"PowerShell进程执行失败: {e}")
                return None
            
        except Exception as e:
            self.logger.error(f"Windows语音识别失败: {e}")
            return None
    
    def _recognize_macos_native(self, timeout: float = 5.0) -> Optional[RecognitionResult]:
        """macOS原生语音识别（改进版）"""
        try:
            self.logger.info("🎤 使用macOS语音识别，请说话...")
            
            start_time = time.time()
            
            # 简化的macOS语音识别实现
            import subprocess
            
            # 使用macOS的say命令提示用户
            try:
                subprocess.run(['say', '请说话'], check=False, timeout=2)
            except:
                pass
            
            # 使用简化的语音识别方法
            try:
                # 创建一个更安全的AppleScript
                applescript = f'''
try
    set timeoutSeconds to {min(timeout, 10)}
    
    -- 简单的语音识别提示
    tell application "System Events"
        -- 这里可以添加更复杂的语音识别逻辑
        -- 目前只是一个占位符实现
        delay 0.5
    end tell
    
    return "macOS语音识别功能需要用户手动激活系统听写"
    
on error errMsg
    return "ERROR: " & errMsg
end try
'''
                
                process = subprocess.Popen([
                    'osascript', '-e', applescript
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout+2)
                    
                    if process.returncode == 0 and stdout:
                        text = stdout.strip()
                        if text and not text.startswith("ERROR"):
                            # 返回提示信息而不是实际的语音识别结果
                            # 实际的macOS语音识别需要更复杂的实现
                            return RecognitionResult(
                                text="请使用系统听写功能 (Fn+Fn 或 Ctrl+Space)",
                                confidence=0.7,
                                language="zh-CN", 
                                timestamp=datetime.now(),
                                duration=time.time() - start_time
                            )
                        elif text.startswith("ERROR"):
                            self.logger.warning(f"AppleScript错误: {text}")
                
                except subprocess.TimeoutExpired:
                    self.logger.warning("AppleScript超时，强制终止进程")
                    process.kill()
                    process.wait()
            
            except Exception as e:
                self.logger.error(f"AppleScript执行失败: {e}")
            
            # 返回友好的提示信息
            return RecognitionResult(
                text="请使用macOS系统听写功能进行语音输入",
                confidence=0.5,
                language="zh-CN",
                timestamp=datetime.now(),
                duration=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"macOS语音识别失败: {e}")
            return None
    
    def _recognize_openai(self, timeout: float = 5.0) -> Optional[RecognitionResult]:
        """使用OpenAI Whisper语音识别"""
        if VoiceProvider.OPENAI not in self.engines:
            return None
        
        try:
            client = self.engines[VoiceProvider.OPENAI]['client']
            
            self.logger.info("🎤 使用OpenAI Whisper识别，请说话...")
            
            # 录制音频
            audio_file = self._record_audio(timeout)
            if not audio_file:
                return None
            
            try:
                # 调用OpenAI Whisper API
                with open(audio_file, 'rb') as audio:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language="zh"  # 中文识别
                    )
                
                # 清理临时文件
                try:
                    os.remove(audio_file)
                except:
                    pass
                
                return RecognitionResult(
                    text=transcript.text,
                    confidence=0.95,  # Whisper通常有很高的准确度
                    language=self.voice_settings.language,
                    timestamp=datetime.now(),
                    duration=timeout
                )
                
            except Exception as api_error:
                self.logger.error(f"OpenAI Whisper API调用失败: {api_error}")
                # 清理文件
                try:
                    os.remove(audio_file)
                except:
                    pass
                return None
        
        except Exception as e:
            self.logger.error(f"OpenAI语音识别失败: {e}")
            return None
    
    def _record_audio(self, duration: float = 5.0) -> Optional[str]:
        """录制音频到临时文件"""
        if not PYAUDIO_AVAILABLE:
            self.logger.error("PyAudio不可用，无法录制音频")
            return None
        
        try:
            # 音频参数
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000  # Whisper推荐的采样率
            
            # 创建PyAudio对象
            audio = pyaudio.PyAudio()
            
            # 开始录制
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            self.logger.info(f"🔴 开始录制音频 ({duration}秒)...")
            
            frames = []
            for _ in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            self.logger.info("⏹️ 录制完成")
            
            # 停止录制
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # 保存到临时文件
            temp_file = os.path.join(
                self.audio_cache_dir, 
                f"recording_{int(time.time())}.wav"
            )
            
            with wave.open(temp_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            
            return temp_file
            
        except Exception as e:
            self.logger.error(f"录制音频失败: {e}")
            return None
    
    def start_conversation(self):
        """开始语音对话"""
        self.conversation_active = True
        self.logger.info("🗣️ 开始语音对话")
        
        if self.on_speech_start:
            self.on_speech_start()
    
    def stop_conversation(self):
        """停止语音对话"""
        self.conversation_active = False
        self.logger.info("🔇 停止语音对话")
        
        if self.on_speech_end:
            self.on_speech_end()
    
    async def voice_interaction(self, 
                               prompt: str = "请说话...",
                               timeout: float = 10.0,
                               response_callback: Optional[Callable[[str], str]] = None) -> Optional[str]:
        """
        完整的语音交互流程：提示 -> 听取 -> 处理 -> 回应
        
        Args:
            prompt: 语音提示内容
            timeout: 听取超时时间
            response_callback: 处理语音输入的回调函数，返回要语音输出的文本
            
        Returns:
            识别到的用户语音文本
        """
        try:
            # 1. 语音提示
            if prompt:
                await self.speak_async(prompt, EmotionType.FRIENDLY, wait_for_completion=True)
                await asyncio.sleep(0.5)  # 短暂暂停
            
            # 2. 听取用户语音
            result = await self.listen_async(timeout=timeout)
            if not result or not result.text.strip():
                await self.speak_async("抱歉，我没有听清楚，请再说一遍。", EmotionType.NEUTRAL)
                return None
            
            user_text = result.text.strip()
            self.logger.info(f"👤 用户说: {user_text}")
            
            # 3. 处理用户输入
            if response_callback:
                try:
                    response_text = response_callback(user_text)
                    if response_text:
                        # 4. 语音回应
                        await self.speak_async(response_text, EmotionType.FRIENDLY, wait_for_completion=False)
                except Exception as e:
                    self.logger.error(f"回调处理失败: {e}")
                    await self.speak_async("抱歉，处理您的请求时出现了问题。", EmotionType.NEUTRAL)
            
            return user_text
            
        except Exception as e:
            self.logger.error(f"语音交互失败: {e}")
            await self.speak_async("抱歉，语音交互出现了错误。", EmotionType.NEUTRAL)
            return None
    
    def listen_for_wake_word(self, wake_words: List[str] = None) -> bool:
        """
        监听唤醒词
        
        Args:
            wake_words: 唤醒词列表，默认为["小助手", "象棋", "chess"]
            
        Returns:
            是否检测到唤醒词
        """
        if wake_words is None:
            wake_words = ["小助手", "象棋", "chess", "assistant", "hello"]
        
        try:
            result = self.listen(timeout=3.0, phrase_timeout=2.0)
            if result and result.text:
                text_lower = result.text.lower()
                for wake_word in wake_words:
                    if wake_word.lower() in text_lower:
                        self.logger.info(f"检测到唤醒词: {wake_word}")
                        return True
            return False
        except Exception as e:
            self.logger.error(f"监听唤醒词失败: {e}")
            return False
    
    def set_voice_settings(self, settings: VoiceSettings):
        """更新语音设置"""
        self.voice_settings = settings
        
        # 重新配置引擎
        if settings.provider == VoiceProvider.SYSTEM:
            self._configure_system_tts()
        
        self.logger.info(f"语音设置已更新: {settings.provider.value}")
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """获取可用语音列表"""
        voices = []
        
        # 系统语音
        if VoiceProvider.SYSTEM in self.engines:
            try:
                tts_engine = self.engines[VoiceProvider.SYSTEM]['tts']
                system_voices = tts_engine.getProperty('voices')
                
                for voice in system_voices:
                    voices.append({
                        'provider': 'system',
                        'id': voice.id,
                        'name': voice.name,
                        'languages': getattr(voice, 'languages', []),
                        'gender': 'unknown'
                    })
            except Exception as e:
                self.logger.warning(f"获取系统语音列表失败: {e}")
        
        # OpenAI语音
        if VoiceProvider.OPENAI in self.engines:
            openai_voices = [
                {'provider': 'openai', 'id': 'alloy', 'name': 'Alloy', 'gender': 'neutral'},
                {'provider': 'openai', 'id': 'echo', 'name': 'Echo', 'gender': 'male'},
                {'provider': 'openai', 'id': 'fable', 'name': 'Fable', 'gender': 'neutral'},
                {'provider': 'openai', 'id': 'nova', 'name': 'Nova', 'gender': 'female'},
                {'provider': 'openai', 'id': 'shimmer', 'name': 'Shimmer', 'gender': 'female'}
            ]
            voices.extend(openai_voices)
        
        return voices
    
    def get_voice_stats(self) -> Dict[str, Any]:
        """获取语音系统统计信息"""
        return {
            **self.stats,
            'provider': self.voice_settings.provider.value,
            'conversation_active': self.conversation_active,
            'is_speaking': self.is_speaking,
            'is_listening': self.is_listening,
            'continuous_listening': self.enable_continuous_listening,
            'available_providers': list(self.engines.keys()),
            'cache_directory': self.audio_cache_dir,
            'average_speech_time': (
                self.stats['total_speech_time'] / self.stats['tts_calls']
                if self.stats['tts_calls'] > 0 else 0
            ),
            'average_listening_time': (
                self.stats['total_listening_time'] / self.stats['stt_calls']
                if self.stats['stt_calls'] > 0 else 0
            )
        }
    
    def cleanup(self):
        """清理资源（改进版）"""
        try:
            self.logger.info("开始清理语音系统资源...")
            
            # 设置停止标志
            self.running = False
            self.conversation_active = False
            
            # 设置停止事件（如果存在）
            if hasattr(self, '_stop_event'):
                self._stop_event.set()
            
            # 停止TTS工作线程
            if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
                try:
                    self.tts_queue.put(None)  # 发送退出信号
                    self.tts_thread.join(timeout=3.0)
                    if self.tts_thread.is_alive():
                        self.logger.warning("TTS线程未能正常退出")
                except Exception as e:
                    self.logger.warning(f"停止TTS线程时发生错误: {e}")
            
            # 停止连续监听线程
            if hasattr(self, 'listening_thread') and self.listening_thread.is_alive():
                try:
                    self.listening_thread.join(timeout=3.0)
                    if self.listening_thread.is_alive():
                        self.logger.warning("监听线程未能正常退出")
                except Exception as e:
                    self.logger.warning(f"停止监听线程时发生错误: {e}")
            
            # 清理TTS引擎
            for provider, engine_dict in self.engines.items():
                if provider == VoiceProvider.SYSTEM and 'tts' in engine_dict:
                    try:
                        tts_engine = engine_dict['tts']
                        if hasattr(tts_engine, 'stop'):
                            tts_engine.stop()
                        if hasattr(tts_engine, 'endLoop'):
                            tts_engine.endLoop()
                    except Exception as e:
                        self.logger.warning(f"清理TTS引擎时发生错误: {e}")
            
            # 清理队列
            try:
                while not self.tts_queue.empty():
                    try:
                        self.tts_queue.get_nowait()
                        self.tts_queue.task_done()
                    except queue.Empty:
                        break
            except Exception as e:
                self.logger.warning(f"清理TTS队列时发生错误: {e}")
            
            try:
                while not self.stt_queue.empty():
                    try:
                        self.stt_queue.get_nowait()
                    except queue.Empty:
                        break
            except Exception as e:
                self.logger.warning(f"清理STT队列时发生错误: {e}")
            
            # 清理临时音频文件
            try:
                import shutil
                if os.path.exists(self.audio_cache_dir):
                    # 只清理临时文件，不删除整个目录
                    for file in os.listdir(self.audio_cache_dir):
                        if file.endswith(('.mp3', '.wav', '.tmp')):
                            try:
                                os.remove(os.path.join(self.audio_cache_dir, file))
                            except:
                                pass
            except Exception as e:
                self.logger.warning(f"清理临时文件时发生错误: {e}")
            
            # 重置状态
            self.is_speaking = False
            self.is_listening = False
            
            self.logger.info("✅ 语音系统资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理语音系统失败: {e}")

# 语音指令识别器
class VoiceCommandRecognizer:
    """语音指令识别器"""
    
    def __init__(self):
        self.chess_commands = {
            # 移动指令
            '移动': ['move', '走', '下'],
            '悔棋': ['undo', '撤销', '退回'],
            '提示': ['hint', '建议', '帮助'],
            
            # 游戏控制
            '开始游戏': ['new game', '新游戏', '重新开始'],
            '暂停': ['pause', '暂停游戏'],
            '继续': ['resume', '继续游戏'],
            '结束': ['quit', '结束游戏', '退出'],
            
            # 分析指令
            '分析': ['analyze', '分析局面', '评估'],
            '最佳移动': ['best move', '最好的走法', '推荐移动'],
            
            # 对话指令
            '解释': ['explain', '解释这步棋', '为什么'],
            '教学': ['teach', '教我', '学习'],
            '历史': ['history', '棋谱', '回顾']
        }
    
    def recognize_command(self, text: str) -> Optional[Dict[str, Any]]:
        """识别语音指令"""
        text_lower = text.lower()
        
        for command, variations in self.chess_commands.items():
            for variation in variations:
                if variation.lower() in text_lower:
                    return {
                        'command': command,
                        'original_text': text,
                        'confidence': 1.0,
                        'parameters': self._extract_parameters(text, command)
                    }
        
        return None
    
    def _extract_parameters(self, text: str, command: str) -> Dict[str, Any]:
        """提取指令参数"""
        parameters = {}
        
        # 简化实现：基于指令类型提取参数
        if command == '移动':
            # 尝试提取棋子位置
            # 例如："移动马到e4"
            pass
        elif command == '分析':
            # 提取分析深度等参数
            pass
        
        return parameters

# 工厂函数
def create_voice_system(**kwargs) -> ChessVoiceSystem:
    """创建语音系统实例"""
    return ChessVoiceSystem(**kwargs)

def create_command_recognizer() -> VoiceCommandRecognizer:
    """创建语音指令识别器"""
    return VoiceCommandRecognizer()

# 测试和演示
if __name__ == "__main__":
    print("🎙️ 测试Chess AI Agent语音系统...")
    
    async def test_voice_system():
        # 创建语音系统
        voice_system = create_voice_system(
            voice_settings=VoiceSettings(
                provider=VoiceProvider.SYSTEM,
                language="zh-CN",
                speed=1.0,
                emotion=EmotionType.FRIENDLY
            ),
            enable_continuous_listening=False
        )
        
        print(f"✅ 语音系统创建成功")
        
        # 获取可用语音
        voices = voice_system.get_available_voices()
        print(f"📢 可用语音数量: {len(voices)}")
        
        # 测试语音合成
        print("\n🔊 测试语音合成...")
        test_messages = [
            ("欢迎来到国际象棋世界！", EmotionType.FRIENDLY),
            ("让我们开始一局精彩的对弈吧！", EmotionType.EXCITED),
            ("这是一个很好的移动选择。", EmotionType.ENCOURAGING),
            ("让我仔细分析一下这个局面...", EmotionType.THINKING)
        ]
        
        for text, emotion in test_messages:
            print(f"🎵 合成语音: {text} [{emotion.value}]")
            success = await voice_system.speak_async(text, emotion, wait_for_completion=True)
            print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
            
            # 短暂暂停
            await asyncio.sleep(0.5)
        
        # 测试语音识别
        if BASIC_VOICE_AVAILABLE:
            print("\n🎤 测试语音识别...")
            print("请在5秒内说话...")
            
            result = await voice_system.listen_async(timeout=5.0)
            if result:
                print(f"✅ 识别结果: {result.text}")
                print(f"   置信度: {result.confidence:.2f}")
            else:
                print("❌ 语音识别失败或超时")
        
        # 测试语音指令识别
        print("\n🤖 测试语音指令识别...")
        command_recognizer = create_command_recognizer()
        
        test_commands = [
            "开始新游戏",
            "移动马到e4", 
            "分析当前局面",
            "给我一些提示",
            "解释这步棋为什么这么走"
        ]
        
        for command_text in test_commands:
            command = command_recognizer.recognize_command(command_text)
            if command:
                print(f"✅ 识别指令: '{command_text}' -> {command['command']}")
            else:
                print(f"❓ 未识别指令: '{command_text}'")
        
        # 显示统计信息
        stats = voice_system.get_voice_stats()
        print(f"\n📊 语音系统统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 清理资源
        voice_system.cleanup()
        print("\n🎉 语音系统测试完成!")
    
    # 运行测试
    asyncio.run(test_voice_system())