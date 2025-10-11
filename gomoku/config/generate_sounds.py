"""音效生成脚本
Generate sound effects for Gomoku using NumPy/SciPy.

生成落子、胜利、悔棋等音效。
"""

import os
import sys
from pathlib import Path

import numpy as np

# 添加项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def generate_stone_sound(filename: str, duration: float = 0.1, freq: int = 800) -> None:
    """生成落子音效（清脆的敲击声）
    
    Args:
        filename: 输出文件名
        duration: 持续时间（秒）
        freq: 频率（Hz）
    """
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 生成短促的音调
    wave = np.sin(2 * np.pi * freq * t)
    
    # 应用快速衰减包络
    envelope = np.exp(-10 * t / duration)
    wave = wave * envelope
    
    # 归一化并转换为16位整数
    wave = np.int16(wave / np.max(np.abs(wave)) * 32767 * 0.5)
    
    # 保存为WAV文件
    save_wav(filename, wave, sample_rate)
    print(f"✓ 已生成: {filename}")


def generate_win_sound(filename: str, duration: float = 1.0) -> None:
    """生成胜利音效（上升音阶）
    
    Args:
        filename: 输出文件名
        duration: 持续时间（秒）
    """
    sample_rate = 44100
    
    # 音阶: C5 -> E5 -> G5 -> C6
    freqs = [523, 659, 784, 1047]
    note_duration = duration / len(freqs)
    
    wave = np.array([])
    
    for freq in freqs:
        t = np.linspace(0, note_duration, int(sample_rate * note_duration))
        note = np.sin(2 * np.pi * freq * t)
        
        # 应用包络
        envelope = np.exp(-2 * t / note_duration)
        note = note * envelope
        
        wave = np.concatenate([wave, note])
    
    # 归一化
    wave = np.int16(wave / np.max(np.abs(wave)) * 32767 * 0.7)
    
    save_wav(filename, wave, sample_rate)
    print(f"✓ 已生成: {filename}")


def generate_undo_sound(filename: str, duration: float = 0.2) -> None:
    """生成悔棋音效（下降音）
    
    Args:
        filename: 输出文件名
        duration: 持续时间（秒）
    """
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 频率从高到低
    freq_start = 1000
    freq_end = 400
    freq = np.linspace(freq_start, freq_end, len(t))
    
    # 生成扫频
    phase = np.cumsum(2 * np.pi * freq / sample_rate)
    wave = np.sin(phase)
    
    # 应用包络
    envelope = np.exp(-5 * t / duration)
    wave = wave * envelope
    
    # 归一化
    wave = np.int16(wave / np.max(np.abs(wave)) * 32767 * 0.5)
    
    save_wav(filename, wave, sample_rate)
    print(f"✓ 已生成: {filename}")


def save_wav(filename: str, data: np.ndarray, sample_rate: int) -> None:
    """保存WAV文件
    
    Args:
        filename: 文件名
        data: 音频数据（16位整数数组）
        sample_rate: 采样率
    """
    try:
        # 尝试使用scipy
        from scipy.io import wavfile
        wavfile.write(filename, sample_rate, data)
    except ImportError:
        # 回退：手动写入WAV文件
        import struct
        
        with open(filename, 'wb') as f:
            # WAV文件头
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + len(data) * 2))
            f.write(b'WAVE')
            
            # fmt chunk
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))  # Chunk size
            f.write(struct.pack('<H', 1))   # Audio format (PCM)
            f.write(struct.pack('<H', 1))   # Channels
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))  # Byte rate
            f.write(struct.pack('<H', 2))   # Block align
            f.write(struct.pack('<H', 16))  # Bits per sample
            
            # data chunk
            f.write(b'data')
            f.write(struct.pack('<I', len(data) * 2))
            f.write(data.tobytes())


def main():
    """生成所有音效"""
    # 确定输出目录
    script_dir = Path(__file__).parent
    sound_dir = script_dir.parent / 'assets' / 'sounds'
    sound_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 50)
    print("🎵 生成五子棋音效文件...")
    print("=" * 50)
    
    # 生成音效
    generate_stone_sound(str(sound_dir / 'stone_black.wav'), freq=800)
    generate_stone_sound(str(sound_dir / 'stone_white.wav'), freq=900)
    generate_win_sound(str(sound_dir / 'win.wav'))
    generate_undo_sound(str(sound_dir / 'undo.wav'))
    
    print("=" * 50)
    print("✅ 音效生成完成！")
    print(f"📁 输出目录: {sound_dir}")
    print("=" * 50)


if __name__ == '__main__':
    main()
