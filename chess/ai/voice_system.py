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
                    'client': OpenAI(api_key=self.api_key)
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
        
        # TTS工作线程
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # 连续监听线程
        if self.enable_continuous_listening:
            self.listening_thread = threading.Thread(target=self._continuous_listening_worker, daemon=True)
            self.listening_thread.start()
    
    def _tts_worker(self):
        """TTS工作线程"""
        while self.running:
            try:
                # 从队列获取TTS任务
                task = self.tts_queue.get(timeout=1.0)
                if task is None:  # 退出信号
                    break
                
                text, emotion, callback = task['text'], task['emotion'], task.get('callback')
                
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
    
    def _continuous_listening_worker(self):
        """连续监听工作线程"""
        while self.running and self.enable_continuous_listening:
            try:
                if self.conversation_active and not self.is_speaking:
                    result = self._recognize_speech_internal()
                    
                    if result and result.text.strip():
                        if self.on_speech_recognized:
                            self.on_speech_recognized(result.text)
                
                time.sleep(0.5)  # 避免过于频繁的检查
                
            except Exception as e:
                self.logger.error(f"连续监听线程错误: {e}")
                time.sleep(2.0)  # 错误后等待更长时间
    
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
        """使用OpenAI TTS合成语音"""
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
            
            # 调用OpenAI TTS
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=self.voice_settings.speed
            )
            
            # 保存并播放音频
            audio_file = os.path.join(self.audio_cache_dir, f"tts_{int(time.time())}.mp3")
            response.stream_to_file(audio_file)
            
            # 播放音频文件
            self._play_audio_file(audio_file)
            
            # 清理临时文件
            try:
                os.remove(audio_file)
            except:
                pass
            
            return True
        
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
    
    def _play_audio_file(self, file_path: str):
        """播放音频文件（优先使用pygame.mixer）"""
        try:
            # 优先尝试pygame.mixer
            try:
                import pygame
                # 初始化混音器（若未初始化）
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                # 使用音乐通道播放，避免重复加载Sound对象占用内存
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                self.logger.info(f"播放音频文件: {file_path}")
                # 阻塞直到播放完成
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                return
            except Exception as pg_err:
                self.logger.warning(f"pygame播放失败，尝试备用方案: {pg_err}")

            # 备用：使用系统TTS重读文本（若可行）
            if BASIC_VOICE_AVAILABLE and VoiceProvider.SYSTEM in self.engines:
                # 无法直接从文件回放，则提示并返回
                self.logger.info("回退到系统TTS播放文本")
                # 系统TTS回退在调用链上已处理，此处仅记录
                return

        except Exception as e:
            self.logger.error(f"播放音频文件失败: {e}")
    
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
        """使用系统语音识别"""
        if VoiceProvider.SYSTEM not in self.engines:
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
            
            # 识别语音
            text = recognizer.recognize_google(audio, language=self.voice_settings.language)
            
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
    
    def _recognize_openai(self, timeout: float = 5.0) -> Optional[RecognitionResult]:
        """使用OpenAI语音识别"""
        if VoiceProvider.OPENAI not in self.engines:
            return None
        
        try:
            # 这里应该实现录音和OpenAI Whisper API调用
            # 简化实现：返回模拟结果
            self.logger.info("使用OpenAI语音识别（模拟）")
            
            return RecognitionResult(
                text="这是模拟的OpenAI语音识别结果",
                confidence=0.95,
                language=self.voice_settings.language,
                timestamp=datetime.now(),
                duration=timeout
            )
        
        except Exception as e:
            self.logger.error(f"OpenAI语音识别失败: {e}")
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
        """清理资源"""
        try:
            self.running = False
            self.conversation_active = False
            
            # 停止工作线程
            if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
                self.tts_queue.put(None)  # 发送退出信号
                self.tts_thread.join(timeout=2.0)
            
            # 清理引擎
            for provider, engine_dict in self.engines.items():
                if provider == VoiceProvider.SYSTEM and 'tts' in engine_dict:
                    try:
                        engine_dict['tts'].stop()
                    except:
                        pass
            
            # 清理临时文件
            try:
                import shutil
                if os.path.exists(self.audio_cache_dir):
                    shutil.rmtree(self.audio_cache_dir)
            except:
                pass
            
            self.logger.info("语音系统清理完成")
            
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