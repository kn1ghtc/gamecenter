"""音效系统 - 游戏音频管理"""
import pygame
from pathlib import Path
from typing import Dict, Optional

from gamecenter.deltaOperation import config


class AudioSystem:
    """音频系统
    
    功能:
    - 背景音乐播放
    - 音效播放
    - 音量控制
    - 3D音效定位
    """
    
    def __init__(self):
        """初始化音频系统"""
        try:
            pygame.mixer.init()
            self.enabled = True
        except:
            print("[AudioSystem] Pygame mixer初始化失败,禁用音频")
            self.enabled = False
            return
            
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_volume = 0.6
        self.sfx_volume = 0.8
        self.master_volume = 0.8
        
        # 音效路径
        self.sounds_dir = config.ASSETS_DIR / "sounds"
        self.music_dir = config.ASSETS_DIR / "music"
        
        # 确保目录存在
        self.sounds_dir.mkdir(exist_ok=True)
        self.music_dir.mkdir(exist_ok=True)
        
        print("[AudioSystem] 音频系统初始化完成")
        
    def load_sound(self, name: str, filename: str) -> bool:
        """加载音效
        
        Args:
            name: 音效名称
            filename: 文件名
            
        Returns:
            是否加载成功
        """
        if not self.enabled:
            return False
            
        try:
            sound_path = self.sounds_dir / filename
            
            if not sound_path.exists():
                # 创建占位音效(静音)
                sound = pygame.mixer.Sound(buffer=bytes(4096))
                print(f"[AudioSystem] 音效文件不存在,使用占位: {filename}")
            else:
                sound = pygame.mixer.Sound(str(sound_path))
                
            self.sounds[name] = sound
            return True
        except Exception as e:
            print(f"[AudioSystem] 加载音效失败 {filename}: {e}")
            return False
            
    def play_sound(self, name: str, volume: float = 1.0, loops: int = 0) -> bool:
        """播放音效
        
        Args:
            name: 音效名称
            volume: 音量 (0.0-1.0)
            loops: 循环次数 (-1=无限)
            
        Returns:
            是否播放成功
        """
        if not self.enabled or name not in self.sounds:
            return False
            
        try:
            sound = self.sounds[name]
            final_volume = volume * self.sfx_volume * self.master_volume
            sound.set_volume(final_volume)
            sound.play(loops=loops)
            return True
        except Exception as e:
            print(f"[AudioSystem] 播放音效失败 {name}: {e}")
            return False
            
    def play_music(self, filename: str, loops: int = -1) -> bool:
        """播放背景音乐
        
        Args:
            filename: 音乐文件名
            loops: 循环次数 (-1=无限)
            
        Returns:
            是否播放成功
        """
        if not self.enabled:
            return False
            
        try:
            music_path = self.music_dir / filename
            
            if music_path.exists():
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
                pygame.mixer.music.play(loops=loops)
                print(f"[AudioSystem] 播放音乐: {filename}")
                return True
            else:
                print(f"[AudioSystem] 音乐文件不存在: {filename}")
                return False
        except Exception as e:
            print(f"[AudioSystem] 播放音乐失败: {e}")
            return False
            
    def stop_music(self):
        """停止背景音乐"""
        if self.enabled:
            pygame.mixer.music.stop()
            
    def pause_music(self):
        """暂停背景音乐"""
        if self.enabled:
            pygame.mixer.music.pause()
            
    def resume_music(self):
        """恢复背景音乐"""
        if self.enabled:
            pygame.mixer.music.unpause()
            
    def set_master_volume(self, volume: float):
        """设置主音量
        
        Args:
            volume: 音量 (0.0-1.0)
        """
        self.master_volume = max(0.0, min(1.0, volume))
        
    def set_music_volume(self, volume: float):
        """设置音乐音量
        
        Args:
            volume: 音量 (0.0-1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            
    def set_sfx_volume(self, volume: float):
        """设置音效音量
        
        Args:
            volume: 音量 (0.0-1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        
    def play_3d_sound(self, name: str, source_x: float, source_y: float,
                     listener_x: float, listener_y: float, max_distance: float = 1000):
        """播放3D定位音效
        
        Args:
            name: 音效名称
            source_x, source_y: 音源位置
            listener_x, listener_y: 听者位置
            max_distance: 最大听到距离
        """
        if not self.enabled or name not in self.sounds:
            return
            
        # 计算距离
        dx = source_x - listener_x
        dy = source_y - listener_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance > max_distance:
            return  # 太远听不到
            
        # 根据距离计算音量
        volume = 1.0 - (distance / max_distance)
        
        # 播放
        self.play_sound(name, volume=volume)
        
    def preload_common_sounds(self):
        """预加载常用音效"""
        common_sounds = {
            "pistol_shoot": "pistol.wav",
            "rifle_shoot": "rifle.wav",
            "shotgun_shoot": "shotgun.wav",
            "sniper_shoot": "sniper.wav",
            "reload": "reload.wav",
            "footstep": "footstep.wav",
            "explosion": "explosion.wav",
            "hit": "hit.wav",
            "death": "death.wav"
        }
        
        for name, filename in common_sounds.items():
            self.load_sound(name, filename)
            
        print(f"[AudioSystem] 预加载 {len(common_sounds)} 个音效")
    def play_sound_3d(self, sound_name: str, world_x: float, world_y: float, 
                      listener_x: float, listener_y: float, max_distance: float = 800) -> None:
        """播放3D定位音效
        
        Args:
            sound_name: 音效名称
            world_x, world_y: 音源世界坐标
            listener_x, listener_y: 听者（玩家）坐标
            max_distance: 最大听力距离
        """
        import math
        
        # 计算距离
        dx = world_x - listener_x
        dy = world_y - listener_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > max_distance:
            return  # 超出听力范围
        
        # 音量衰减（距离平方反比）
        volume = 1.0 - (distance / max_distance) ** 2
        volume = max(0.0, min(1.0, volume))
        
        # 左右声道平衡（简单立体声）
        angle = math.atan2(dy, dx)
        pan = math.sin(angle)  # -1(左) 到 1(右)
        left_volume = volume * (1 - max(0, pan))
        right_volume = volume * (1 - max(0, -pan))
        
        # 播放音效
        sound = self._get_sound(sound_name)
        if sound:
            channel = sound.play()
            if channel:
                channel.set_volume(left_volume * self.sound_volume, 
                                   right_volume * self.sound_volume)


