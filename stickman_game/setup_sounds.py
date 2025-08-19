#!/usr/bin/env python3
"""
游戏声音资源下载器
从开源站点下载免费声音文件
"""

import os
import urllib.request
import pygame

# 确保声音目录存在
def ensure_sounds_directory():
    sounds_dir = os.path.join("assets", "sounds")
    if not os.path.exists(sounds_dir):
        os.makedirs(sounds_dir)
    return sounds_dir

# 免费开源声音文件URL (使用Pixabay等提供的免费资源)
SOUND_URLS = {
    # 注意：这些是示例URL，实际使用时需要替换为真实的免费资源链接
    'background_music': 'https://www.soundjay.com/misc/bell-ringing-05.wav',
    'gun_shot': 'https://www.soundjay.com/gun-sound-effect/gun-gunshot-02.wav', 
    'explosion': 'https://www.soundjay.com/explosion/explosion-02.wav',
    'jump': 'https://www.soundjay.com/misc/bell-ringing-01.wav',
    'victory_cheer': 'https://www.soundjay.com/human/applause-01.wav',
    'knife_throw': 'https://www.soundjay.com/misc/whoosh-01.wav'
}

def download_sound_file(url, filename):
    """下载声音文件"""
    try:
        print(f"正在下载: {filename}")
        urllib.request.urlretrieve(url, filename)
        print(f"✅ 下载成功: {filename}")
        return True
    except Exception as e:
        print(f"❌ 下载失败 {filename}: {e}")
        return False

def create_fallback_sounds():
    """创建备用的程序生成声音"""
    import pygame
    import math
    import random
    import numpy as np
    
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    
    def create_tone(frequency, duration, volume=0.5):
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            time_point = float(i) / sample_rate
            wave_value = int(32767 * volume * math.sin(2 * math.pi * frequency * time_point))
            decay = 1.0 - (time_point / duration) * 0.5
            wave_value = int(wave_value * decay)
            arr[i] = [wave_value, wave_value]
        
        return pygame.sndarray.make_sound(arr)
    
    def create_noise(duration, volume=0.3):
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            wave_value = int(32767 * volume * (random.random() * 2 - 1))
            decay = 1.0 - (float(i) / frames) * 0.8
            wave_value = int(wave_value * decay)
            arr[i] = [wave_value, wave_value]
        
        return pygame.sndarray.make_sound(arr)
    
    def create_gun_shot():
        """创建更真实的枪声效果 - 结合低频爆炸和高频尖锐声"""
        sample_rate = 22050
        duration = 0.15
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        for i in range(frames):
            time_point = float(i) / sample_rate
            progress = time_point / duration
            
            # 主要爆炸声 - 低频
            explosion_freq = 150 + 200 * (1 - progress)
            explosion_wave = math.sin(2 * math.pi * explosion_freq * time_point)
            
            # 尖锐的金属声 - 高频
            metal_freq = 2000 + 1000 * (1 - progress)
            metal_wave = math.sin(2 * math.pi * metal_freq * time_point) * 0.3
            
            # 噪音成分模拟火药爆炸
            noise_component = (random.random() * 2 - 1) * 0.4
            
            # 组合所有成分
            combined_wave = explosion_wave + metal_wave + noise_component
            
            # 快速衰减包络
            envelope = math.exp(-progress * 8)  # 快速衰减
            
            wave_value = int(32767 * 0.6 * combined_wave * envelope)
            wave_value = max(-32767, min(32767, wave_value))  # 限幅
            arr[i] = [wave_value, wave_value]
        
        return pygame.sndarray.make_sound(arr)
    
    # 创建备用声音
    sounds = {
        'gun_shot': create_gun_shot(),
        'explosion': create_noise(0.5, 0.6), 
        'jump': create_tone(400, 0.2, 0.3),
        'knife_throw': create_tone(600, 0.15, 0.3),
        'victory_cheer': create_tone(1000, 1.0, 0.4),
        'background_music': create_tone(220, 2.0, 0.2)
    }
    
    return sounds

def save_sound_to_wav(sound, filename):
    """保存pygame声音到wav文件"""
    try:
        import pygame
        import wave
        import numpy as np
        
        # 获取声音数据
        sound_array = pygame.sndarray.array(sound)
        
        # 确保是立体声格式
        if len(sound_array.shape) == 1:
            # 单声道转立体声
            sound_array = np.column_stack((sound_array, sound_array))
        
        # 保存为wav文件
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(2)  # 立体声
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(22050)  # 采样率
            wav_file.writeframes(sound_array.astype(np.int16).tobytes())
        
        return True
    except Exception as e:
        print(f"❌ 保存音频文件失败: {e}")
        return False

def setup_game_sounds():
    """设置游戏声音系统"""
    sounds_dir = ensure_sounds_directory()
    
    print("🎵 设置游戏声音系统...")
    
    # 首先尝试从免费资源下载（这些URL通常需要特殊处理）
    print("🎵 尝试下载声音文件...")
    downloaded_count = 0
    
    # 由于大部分免费音频站点不允许直接下载，我们直接生成程序化音效
    print("🎵 生成程序化声音效果...")
    fallback_sounds = create_fallback_sounds()
    
    # 保存声音文件到磁盘
    saved_count = 0
    for sound_name, sound in fallback_sounds.items():
        filename = os.path.join(sounds_dir, f"{sound_name}.wav")
        if save_sound_to_wav(sound, filename):
            print(f"✅ 保存声音文件: {sound_name}.wav")
            saved_count += 1
        else:
            print(f"❌ 保存失败: {sound_name}.wav")
    
    print(f"🎵 声音系统设置完成！保存了 {saved_count} 个音效文件")
    return fallback_sounds

if __name__ == "__main__":
    setup_game_sounds()
