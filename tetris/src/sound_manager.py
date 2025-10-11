"""
音效和音乐系统模块

负责游戏音效播放和背景音乐管理
"""
import pygame
import os


class SoundManager:
    """音效管理器类"""
    
    def __init__(self, resource_manager, enabled=True):
        """
        初始化音效管理器
        
        参数:
            resource_manager: 资源管理器实例
            enabled: 是否启用音效
        """
        self.resource_manager = resource_manager
        self.enabled = enabled
        self.sounds = {}
        self.music_volume = 0.3
        self.sfx_volume = 0.5
        
        # 初始化pygame mixer
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._load_sounds()
        except Exception as e:
            print(f"音效系统初始化失败: {e}")
            self.enabled = False
    
    def _load_sounds(self):
        """加载所有音效"""
        sound_keys = [
            'sound_rotate',
            'sound_move',
            'sound_clear',
            'sound_drop',
            'sound_level_up',
            'sound_game_over'
        ]
        
        for key in sound_keys:
            path = self.resource_manager.get_resource_path(key)
            if path and os.path.exists(path):
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(self.sfx_volume)
                    self.sounds[key] = sound
                except Exception as e:
                    print(f"无法加载音效 {key}: {e}")
    
    def play_sound(self, sound_key):
        """
        播放音效
        
        参数:
            sound_key: 音效键名
        """
        if not self.enabled or sound_key not in self.sounds:
            return
        
        try:
            self.sounds[sound_key].play()
        except Exception as e:
            print(f"播放音效失败 {sound_key}: {e}")
    
    def play_move(self):
        """播放移动音效"""
        self.play_sound('sound_move')
    
    def play_rotate(self):
        """播放旋转音效"""
        self.play_sound('sound_rotate')
    
    def play_drop(self):
        """播放下落音效"""
        self.play_sound('sound_drop')
    
    def play_clear(self):
        """播放消行音效"""
        self.play_sound('sound_clear')
    
    def play_level_up(self):
        """播放升级音效"""
        self.play_sound('sound_level_up')
    
    def play_game_over(self):
        """播放游戏结束音效"""
        self.play_sound('sound_game_over')
    
    def play_music(self, loop=True):
        """
        播放背景音乐
        
        参数:
            loop: 是否循环播放
        """
        if not self.enabled:
            return
        
        music_path = self.resource_manager.get_resource_path('music_bg')
        if music_path and os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1 if loop else 0)
            except Exception as e:
                print(f"播放背景音乐失败: {e}")
    
    def stop_music(self):
        """停止背景音乐"""
        if self.enabled:
            try:
                pygame.mixer.music.stop()
            except:
                pass
    
    def pause_music(self):
        """暂停背景音乐"""
        if self.enabled:
            try:
                pygame.mixer.music.pause()
            except:
                pass
    
    def unpause_music(self):
        """继续播放背景音乐"""
        if self.enabled:
            try:
                pygame.mixer.music.unpause()
            except:
                pass
    
    def set_music_volume(self, volume):
        """
        设置音乐音量
        
        参数:
            volume: 音量 (0.0 到 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except:
                pass
    
    def set_sfx_volume(self, volume):
        """
        设置音效音量
        
        参数:
            volume: 音量 (0.0 到 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
    
    def toggle_sound(self):
        """切换音效开关"""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music()
        return self.enabled
    
    def cleanup(self):
        """清理音效系统"""
        self.stop_music()
        if self.enabled:
            try:
                pygame.mixer.quit()
            except:
                pass
