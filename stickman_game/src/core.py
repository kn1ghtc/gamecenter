"""
核心游戏组件 - 合并了输入管理、音效管理和存档管理
"""
import pygame
import math
import random
import json
import os
from datetime import datetime
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3未安装，将使用备用音效")
from .config import *


class InputManager:
    """简化输入管理器"""
    def __init__(self):
        self.keys_pressed = set()
    
    def handle_event(self, event):
        """处理输入事件"""
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)
    
    def is_key_pressed(self, key):
        """检查按键是否被按下"""
        return key in self.keys_pressed
    
    def get_current_input(self):
        """获取当前输入状态"""
        keys = pygame.key.get_pressed()
        return {
            'move_left': keys[CONTROLS['move_left']],
            'move_right': keys[CONTROLS['move_right']],
            'jump': keys[CONTROLS['jump']],
            'shoot': keys[CONTROLS['shoot']],
            'bomb': keys[CONTROLS['bomb']],
            'switch_weapon': keys[CONTROLS['switch_weapon']]
        }

class SoundManager:
    """音效管理器 - 支持真实声音文件和程序化备用音效"""
    
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.sound_enabled = True
        self.music_enabled = True
        self.sound_volume = 0.7
        self.music_volume = 0.5
        
        # 初始化文本转语音引擎
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                # 设置中文语音
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'mandarin' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                self.tts_engine.setProperty('rate', 150)  # 语速
                self.tts_engine.setProperty('volume', 0.8)  # 音量
            except Exception as e:
                print(f"TTS引擎初始化失败: {e}")
                self.tts_engine = None
        
        # 初始化pygame mixer
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self._load_sounds()
        except Exception as e:
            print(f"音效系统初始化失败: {e}")
            self.sound_enabled = False
    
    def _load_sounds(self):
        """加载声音文件，如果不存在则生成程序化音效"""
        if not self.sound_enabled:
            return
            
        # 获取游戏根目录
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sounds_dir = os.path.join(current_dir, "assets", "sounds")
        
        # 声音文件映射
        sound_files = {
            'jump': 'jump.wav',
            'shoot': 'gun_shot.wav', 
            'knife_throw': 'knife_throw.wav',
            'explosion': 'explosion.wav',
            'victory_cheer': 'victory_cheer.wav',
            'hit_enemy': 'gun_shot.wav',  # 重用枪声作为击中敌人音效
            'failure': 'explosion.wav',   # 重用爆炸声作为失败音效
            'menu_select': 'jump.wav',    # 重用跳跃声作为菜单选择音效
            'background': 'background_music.wav'
        }
        
        loaded_from_files = 0
        
        # 加载声音文件或生成备用声音
        for sound_name, filename in sound_files.items():
            filepath = os.path.join(sounds_dir, filename)
            # 转换路径分隔符为正斜杠（pygame兼容性）
            filepath = filepath.replace('\\', '/')
            
            if os.path.exists(filepath):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(filepath)
                    self.sounds[sound_name].set_volume(self.sound_volume)
                    loaded_from_files += 1
                except Exception as e:
                    # 生成备用声音
                    self._generate_fallback_sound(sound_name)
            else:
                # 生成程序化声音
                self._generate_fallback_sound(sound_name)
        
        # 简化打印输出
        if loaded_from_files > 0:
            print(f"音效系统就绪 ({loaded_from_files} 个音效)")
        else:
            print("音效系统就绪 (程序生成)")
    
    def _generate_fallback_sound(self, sound_name):
        """生成备用的程序化声音"""
        try:
            if sound_name == 'jump':
                self.sounds[sound_name] = self._create_simple_tone(400, 0.2, 0.3)
            elif sound_name == 'shoot':
                self.sounds[sound_name] = self._create_simple_tone(800, 0.1, 0.4)
            elif sound_name == 'knife_throw':
                self.sounds[sound_name] = self._create_simple_tone(600, 0.15, 0.3)
            elif sound_name == 'explosion':
                self.sounds[sound_name] = self._create_atomic_explosion_sound()
            elif sound_name == 'victory_cheer':
                self.sounds[sound_name] = self._create_success_sound()
            elif sound_name == 'hit_enemy':
                self.sounds[sound_name] = self._create_simple_tone(600, 0.15, 0.5)
            elif sound_name == 'failure':
                self.sounds[sound_name] = self._create_simple_tone(200, 0.5, 0.5)
            elif sound_name == 'menu_select':
                self.sounds[sound_name] = self._create_simple_tone(600, 0.1, 0.3)
            elif sound_name == 'background':
                self.sounds[sound_name] = self._create_simple_tone(220, 2.0, 0.2)
            else:
                # 默认音效
                self.sounds[sound_name] = self._create_simple_tone(500, 0.2, 0.3)
        except Exception as e:
            pass  # 静默处理音效生成失败
    
    def _create_simple_tone(self, frequency, duration, volume=0.5):
        """创建简单音调"""
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = []
        
        for i in range(frames):
            time_point = float(i) / sample_rate
            wave_value = int(32767 * volume * math.sin(2 * math.pi * frequency * time_point))
            # 添加衰减
            decay = 1.0 - (time_point / duration) * 0.5
            wave_value = int(wave_value * decay)
            arr.append([wave_value, wave_value])
        
        try:
            sound = pygame.sndarray.make_sound(arr)
            sound.set_volume(self.sound_volume)
            return sound
        except:
            return None
    
    def _create_noise(self, duration, volume=0.3):
        """创建噪音效果"""
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = []
        
        for i in range(frames):
            wave_value = int(32767 * volume * (random.random() * 2 - 1))
            # 添加衰减
            decay = 1.0 - (float(i) / frames) * 0.8
            wave_value = int(wave_value * decay)
            arr.append([wave_value, wave_value])
        
        try:
            sound = pygame.sndarray.make_sound(arr)
            sound.set_volume(self.sound_volume * 0.5)
            return sound
        except:
            return None
    
    def _create_success_sound(self):
        """创建成功音效 - 多音调组合"""
        # 创建上升音阶效果
        frequencies = [523, 659, 784, 1047]  # C-E-G-C
        duration_per_note = 0.15
        
        total_duration = duration_per_note * len(frequencies)
        sample_rate = 22050
        frames = int(total_duration * sample_rate)
        arr = []
        
        for i in range(frames):
            time_point = float(i) / sample_rate
            note_index = int(time_point / duration_per_note)
            if note_index >= len(frequencies):
                note_index = len(frequencies) - 1
            
            frequency = frequencies[note_index]
            wave_value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * time_point))
            
            # 整体衰减
            decay = 1.0 - (time_point / total_duration) * 0.3
            wave_value = int(wave_value * decay)
            arr.append([wave_value, wave_value])
        
        try:
            sound = pygame.sndarray.make_sound(arr)
            sound.set_volume(self.sound_volume)
            return sound
        except:
            return None
    
    def _create_atomic_explosion_sound(self):
        """创建原子弹爆炸音效 - 多层复合声音"""
        sample_rate = 22050
        duration = 1.5  # 更长的爆炸声
        frames = int(duration * sample_rate)
        arr = []
        
        for i in range(frames):
            time_point = float(i) / sample_rate
            
            # 第一层：低频轰鸣声（模拟爆炸的核心）
            bass_freq = 40 + 20 * math.sin(time_point * 3)
            bass_wave = 0.6 * math.sin(2 * math.pi * bass_freq * time_point)
            
            # 第二层：中频冲击波
            mid_freq = 120 + 80 * math.sin(time_point * 7)
            mid_wave = 0.4 * math.sin(2 * math.pi * mid_freq * time_point)
            
            # 第三层：高频碎片音效
            high_freq = 800 + 400 * random.random()
            high_wave = 0.2 * math.sin(2 * math.pi * high_freq * time_point)
            
            # 第四层：噪音层（模拟爆炸的混乱）
            noise = 0.3 * (random.random() * 2 - 1)
            
            # 混合所有层
            combined_wave = bass_wave + mid_wave + high_wave + noise
            
            # 创建爆炸的衰减曲线：先快速上升，然后缓慢衰减
            if time_point < 0.1:
                # 初始冲击波：快速上升
                envelope = time_point / 0.1
            elif time_point < 0.3:
                # 持续爆炸：保持强度
                envelope = 1.0
            else:
                # 缓慢衰减：模拟余震
                fade_time = time_point - 0.3
                fade_duration = duration - 0.3
                envelope = 1.0 - (fade_time / fade_duration) * 0.7
            
            # 添加随机震动效果
            tremolo = 1.0 + 0.1 * math.sin(time_point * 30)
            envelope *= tremolo
            
            # 应用包络并限制音量
            wave_value = int(32767 * 0.8 * combined_wave * envelope)
            wave_value = max(-32767, min(32767, wave_value))
            
            arr.append([wave_value, wave_value])
        
        try:
            sound = pygame.sndarray.make_sound(arr)
            sound.set_volume(self.sound_volume * 0.9)  # 稍微降低音量避免过响
            return sound
        except:
            return None
    
    def speak_text(self, text):
        """使用TTS播放文本"""
        if self.tts_engine and TTS_AVAILABLE:
            try:
                print(f"🔊 语音播放: {text}")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"语音播放失败: {e}")
                # 备用：播放失败音效
                if 'failure' in self.sounds:
                    self.play_sound('failure')
        else:
            # 没有TTS引擎时使用备用音效
            print(f"💬 文本: {text}")
            if 'failure' in self.sounds:
                self.play_sound('failure')
    
    def play_death_message(self, player_name="玩家"):
        """播放死亡消息"""
        death_message = f"{player_name}，你已死亡"
        self.speak_text(death_message)
    
    def play_sound(self, sound_name):
        """播放音效"""
        if not self.sound_enabled or sound_name not in self.sounds:
            return
        
        sound = self.sounds[sound_name]
        if sound:
            try:
                sound.play()
            except:
                pass

class SaveManager:
    """存档管理器"""
    
    def __init__(self):
        # 获取游戏根目录
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 确保levels目录存在
        levels_dir = os.path.join(current_dir, "levels")
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)
            
        self.save_file = os.path.join(levels_dir, "game_save.json")
        self.stats_file = os.path.join(levels_dir, "game_stats.json")
        self.load_data()
    
    def load_data(self):
        """加载存档数据"""
        # 加载游戏进度
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    self.save_data = json.load(f)
            else:
                self.save_data = {
                    'max_unlocked_level': 1,
                    'high_score': 0,
                    'settings': {
                        'sound_volume': 0.7,
                        'music_volume': 0.5
                    }
                }
        except:
            self.save_data = {
                'max_unlocked_level': 1,
                'high_score': 0,
                'settings': {
                    'sound_volume': 0.7,
                    'music_volume': 0.5
                }
            }
        
        # 加载统计数据
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats_data = json.load(f)
            else:
                self.stats_data = {
                    'games_played': 0,
                    'total_deaths': 0,
                    'total_kills': 0,
                    'total_playtime': 0,
                    'last_played': None
                }
        except:
            self.stats_data = {
                'games_played': 0,
                'total_deaths': 0,
                'total_kills': 0,
                'total_playtime': 0,
                'last_played': None
            }
    
    def save_data_to_file(self):
        """保存数据到文件"""
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.save_data, f, indent=2, ensure_ascii=False)
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def get_max_unlocked_level(self):
        """获取最大解锁关卡"""
        return self.save_data.get('max_unlocked_level', 1)
    
    def unlock_level(self, level):
        """解锁关卡"""
        current_max = self.save_data.get('max_unlocked_level', 1)
        if level > current_max:
            self.save_data['max_unlocked_level'] = level
            self.save_data_to_file()
    
    def update_high_score(self, score):
        """更新最高分"""
        current_high = self.save_data.get('high_score', 0)
        if score > current_high:
            self.save_data['high_score'] = score
            self.save_data_to_file()
            return True
        return False
    
    def record_game_played(self):
        """记录游戏开始"""
        self.stats_data['games_played'] += 1
        self.stats_data['last_played'] = datetime.now().isoformat()
        self.save_data_to_file()
    
    def record_death(self):
        """记录死亡"""
        self.stats_data['total_deaths'] += 1
        self.save_data_to_file()
    
    def record_kill(self):
        """记录击杀"""
        self.stats_data['total_kills'] += 1
        self.save_data_to_file()
    
    def get_save_info(self):
        """获取存档信息"""
        max_level = self.get_max_unlocked_level()
        high_score = self.save_data.get('high_score', 0)
        games_played = self.stats_data.get('games_played', 0)
        
        return f"最高关卡: {max_level} | 最高分: {high_score} | 游戏次数: {games_played}"
