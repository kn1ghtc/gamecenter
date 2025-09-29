import pygame
import os

local_path = os.path.dirname(__file__)

class SoundManager:
    """管理游戏中所有声音的类"""

    def __init__(self):
        """初始化声音属性"""
        pygame.mixer.init() # 初始化混音器
        pygame.mixer.music.set_volume(0.5)

        # 加载背景音乐
        pygame.mixer.music.load(local_path+'/sounds/background.mp3')
        pygame.mixer.music.play(-1)

        # 加载子弹射击声音
        self.bullet_sound = pygame.mixer.Sound(local_path+'/sounds/bullet.wav')

        # 加载外星人爆炸声音
        self.alien_explode_sound = pygame.mixer.Sound(local_path+'/sounds/alien_explode.wav')

        # 加载飞船爆炸声音
        self.ship_explode_sound = pygame.mixer.Sound(local_path+'/sounds/ship_explode.wav')

    def play_bullet_sound(self):
        """播放子弹射击声音"""
        self.bullet_sound.play()

    def play_alien_explode_sound(self):
        """播放外星人爆炸声音"""
        self.alien_explode_sound.play()

    def play_ship_explode_sound(self):
        """播放飞船爆炸声音"""
        self.ship_explode_sound.play()
    def play_background_music(self):
        """播放背景音乐"""
        pygame.mixer.music.play(-1)
    def stop_background_music(self):
        """停止背景音乐"""
        pygame.mixer.music.stop()

