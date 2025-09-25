#!/usr/bin/env python3
"""
Enhanced Audio Creator - 创建高质量音效文件
替换小音效文件为更好的版本
"""

import os
import wave
import numpy as np
from pathlib import Path
import random
import math

class EnhancedAudioCreator:
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = Path(assets_path)
        self.sample_rate = 44100
        
    def create_combo_sound(self, output_path: Path):
        """创建连击音效"""
        print("创建连击音效...")
        
        duration = 0.8  # 0.8秒
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # 创建上升音调的连击声音
        base_freq = 300
        frequencies = [base_freq * (1.2 ** i) for i in range(3)]  # 三个上升音调
        
        wave_data = np.zeros_like(t)
        for i, freq in enumerate(frequencies):
            start_time = i * 0.25
            end_time = start_time + 0.3
            
            # 创建时间窗口
            window = np.where((t >= start_time) & (t <= end_time), 1, 0)
            
            # 创建音调
            tone = np.sin(2 * np.pi * freq * t) * window
            
            # 添加包络
            envelope = np.exp(-(t - start_time) * 8) * window
            
            wave_data += tone * envelope * 0.4
        
        # 添加一些随机噪声增加真实感
        noise = np.random.normal(0, 0.05, len(t))
        wave_data += noise * 0.1
        
        # 标准化并转换
        wave_data = np.clip(wave_data, -1, 1)
        wave_data = (wave_data * 32767).astype(np.int16)
        
        self._write_wav(output_path, wave_data)
        print(f"✅ 连击音效: {output_path}")
    
    def create_hit_sound(self, output_path: Path):
        """创建打击音效"""
        print("创建打击音效...")
        
        duration = 0.4
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # 低频冲击声
        low_freq = 80
        mid_freq = 200
        high_freq = 1000
        
        # 组合不同频率
        low_wave = np.sin(2 * np.pi * low_freq * t) * 0.6
        mid_wave = np.sin(2 * np.pi * mid_freq * t) * 0.4
        high_wave = np.sin(2 * np.pi * high_freq * t) * 0.2
        
        # 急速衰减包络
        envelope = np.exp(-t * 12)
        
        wave_data = (low_wave + mid_wave + high_wave) * envelope
        
        # 添加噪声burst效果
        burst_noise = np.random.normal(0, 0.3, len(t))
        burst_envelope = np.exp(-t * 20)
        wave_data += burst_noise * burst_envelope * 0.3
        
        # 标准化并转换
        wave_data = np.clip(wave_data, -1, 1)
        wave_data = (wave_data * 32767).astype(np.int16)
        
        self._write_wav(output_path, wave_data)
        print(f"✅ 打击音效: {output_path}")
    
    def create_victory_sound(self, output_path: Path):
        """创建胜利音效"""
        print("创建胜利音效...")
        
        duration = 2.0
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # 胜利旋律 (简单的大调音阶)
        notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
        
        wave_data = np.zeros_like(t)
        
        for i, freq in enumerate(notes):
            start_time = i * 0.4
            end_time = start_time + 0.6
            
            note_mask = (t >= start_time) & (t <= end_time)
            note_t = t[note_mask] - start_time
            
            if len(note_t) > 0:
                # 基础音符
                note = np.sin(2 * np.pi * freq * note_t)
                # 添加和声
                harmony = 0.3 * np.sin(2 * np.pi * freq * 1.5 * note_t)
                
                # 包络
                envelope = np.exp(-note_t * 2) * (1 - np.exp(-note_t * 20))
                
                combined = (note + harmony) * envelope * 0.5
                wave_data[note_mask] += combined
        
        # 最终标准化
        wave_data = np.clip(wave_data, -1, 1)
        
        # 转换为OGG格式 (先写WAV再转换)
        temp_wav = output_path.with_suffix('.wav')
        wave_data_int = (wave_data * 32767).astype(np.int16)
        self._write_wav(temp_wav, wave_data_int)
        
        # 尝试转换为OGG
        try:
            import subprocess
            result = subprocess.run([
                'ffmpeg', '-i', str(temp_wav), '-c:a', 'libvorbis', 
                '-q:a', '4', str(output_path), '-y'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                temp_wav.unlink()  # 删除临时WAV文件
                print(f"✅ 胜利音效 (OGG): {output_path}")
            else:
                # 如果转换失败，保留WAV格式
                temp_wav.rename(output_path.with_suffix('.wav'))
                print(f"✅ 胜利音效 (WAV): {output_path.with_suffix('.wav')}")
                
        except FileNotFoundError:
            # ffmpeg不可用，保留WAV格式
            temp_wav.rename(output_path.with_suffix('.wav'))
            print(f"✅ 胜利音效 (WAV): {output_path.with_suffix('.wav')}")
    
    def create_defeat_sound(self, output_path: Path):
        """创建失败音效"""
        print("创建失败音效...")
        
        duration = 2.5
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # 失败音效 (下降音调)
        start_freq = 400
        end_freq = 200
        
        # 频率随时间下降
        freq_curve = start_freq * np.exp(-t * 0.8)
        
        # 生成音调
        phase = 2 * np.pi * np.cumsum(freq_curve) / self.sample_rate
        wave_data = np.sin(phase)
        
        # 慢慢衰减的包络
        envelope = np.exp(-t * 0.5)
        
        wave_data *= envelope * 0.6
        
        # 添加一些悲伤的颤音
        tremolo = 1 + 0.3 * np.sin(2 * np.pi * 4 * t)
        wave_data *= tremolo
        
        # 标准化并转换为OGG
        wave_data = np.clip(wave_data, -1, 1)
        
        temp_wav = output_path.with_suffix('.wav')
        wave_data_int = (wave_data * 32767).astype(np.int16)
        self._write_wav(temp_wav, wave_data_int)
        
        # 转换为OGG
        try:
            import subprocess
            result = subprocess.run([
                'ffmpeg', '-i', str(temp_wav), '-c:a', 'libvorbis',
                '-q:a', '4', str(output_path), '-y'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                temp_wav.unlink()
                print(f"✅ 失败音效 (OGG): {output_path}")
            else:
                temp_wav.rename(output_path.with_suffix('.wav'))
                print(f"✅ 失败音效 (WAV): {output_path.with_suffix('.wav')}")
                
        except FileNotFoundError:
            temp_wav.rename(output_path.with_suffix('.wav'))
            print(f"✅ 失败音效 (WAV): {output_path.with_suffix('.wav')}")
    
    def _write_wav(self, file_path: Path, wave_data: np.ndarray):
        """写入WAV文件"""
        with wave.open(str(file_path), 'w') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(wave_data.tobytes())
    
    def enhance_all_audio(self):
        """增强所有音效文件"""
        print("🎵 Enhanced Audio Creator - 增强音效创建器 🎵")
        print("=" * 50)
        
        # 需要替换的小音效文件
        small_audio_files = [
            ("combo.wav", self.create_combo_sound),
            ("hit.wav", self.create_hit_sound),
            ("audio/music/win.ogg", self.create_victory_sound),
            ("audio/music/lose.ogg", self.create_defeat_sound),
        ]
        
        for filename, create_func in small_audio_files:
            file_path = self.assets_path / filename
            
            # 检查文件大小
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"\n检查 {filename}: {file_size} bytes")
                
                if file_size < 50000:  # 小于50KB
                    print(f"⚠️ {filename} 文件太小，正在重新创建...")
                    
                    # 备份原文件
                    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                    try:
                        file_path.rename(backup_path)
                        print(f"📁 备份原文件到: {backup_path}")
                    except Exception as e:
                        print(f"备份失败: {e}")
                    
                    # 创建新的增强音效
                    try:
                        create_func(file_path)
                        
                        # 验证新文件
                        if file_path.exists():
                            new_size = file_path.stat().st_size
                            print(f"✅ 新文件大小: {new_size} bytes")
                            
                            # 如果新文件太小，恢复备份
                            if new_size < 1000:
                                print("⚠️ 新文件太小，恢复备份")
                                if backup_path.exists():
                                    backup_path.rename(file_path)
                        
                    except Exception as e:
                        print(f"❌ 创建 {filename} 失败: {e}")
                        # 恢复备份
                        if backup_path.exists():
                            backup_path.rename(file_path)
                
                else:
                    print(f"✅ {filename} 大小合适，无需替换")
            else:
                print(f"⚠️ {filename} 不存在，创建新文件...")
                try:
                    create_func(file_path)
                except Exception as e:
                    print(f"❌ 创建 {filename} 失败: {e}")
        
        print(f"\n🎉 音效增强完成！")


def main():
    """主函数"""
    try:
        creator = EnhancedAudioCreator()
        creator.enhance_all_audio()
        
        # 运行最终验证
        print("\n🔍 运行音效验证...")
        import subprocess
        result = subprocess.run([
            "python", "assets_audit.py",
            "--base", "assets",
            "--report", "assets/audio_enhanced_audit.json"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 音效验证完成")
            print(result.stdout)
        else:
            print(f"⚠️ 验证输出 {result.stdout}")
    
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请安装: pip install numpy")
    except Exception as e:
        print(f"❌ 音效创建失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()