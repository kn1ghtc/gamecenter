#!/usr/bin/env python3
"""
Generate a simple background music file for StreetBattle game
Creates a loopable ambient fighting game BGM
"""
import numpy as np
import wave
import struct
import os

def generate_bgm():
    # Audio parameters
    sample_rate = 44100
    duration = 30  # 30 seconds loop
    channels = 2  # stereo
    
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a dark, fighting game ambient BGM
    # Base drone at low frequency
    base_freq = 55  # A1 note for dark atmosphere
    base_wave = 0.3 * np.sin(2 * np.pi * base_freq * t)
    
    # Add harmonic overtones
    second_harmonic = 0.15 * np.sin(2 * np.pi * base_freq * 2 * t)
    third_harmonic = 0.1 * np.sin(2 * np.pi * base_freq * 3 * t)
    
    # Add subtle rhythm pulse
    pulse_freq = 1.5  # 1.5 Hz pulse for fighting tension
    pulse = 0.05 * np.sin(2 * np.pi * pulse_freq * t) * np.sin(2 * np.pi * base_freq * 0.5 * t)
    
    # Add some atmospheric high frequency content
    atmo_freq = 880  # A5 for atmospheric high end
    atmo_wave = 0.02 * np.sin(2 * np.pi * atmo_freq * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * t))
    
    # Combine all elements
    mono_wave = base_wave + second_harmonic + third_harmonic + pulse + atmo_wave
    
    # Apply envelope to avoid clicks at loop point
    envelope = np.ones_like(mono_wave)
    fade_samples = int(0.1 * sample_rate)  # 100ms fade
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    mono_wave *= envelope
    
    # Create stereo version with slight delay for width
    delay_samples = int(0.01 * sample_rate)  # 10ms delay
    left_channel = mono_wave
    right_channel = np.roll(mono_wave, delay_samples) * 0.9
    
    # Interleave channels for stereo
    stereo_wave = np.zeros(len(mono_wave) * 2)
    stereo_wave[0::2] = left_channel
    stereo_wave[1::2] = right_channel
    
    # Normalize
    max_val = np.max(np.abs(stereo_wave))
    if max_val > 0:
        stereo_wave = stereo_wave / max_val * 0.7  # Leave headroom
    
    # Convert to 16-bit integers
    stereo_wave_int = (stereo_wave * 32767).astype(np.int16)
    
    # Write WAV file first
    wav_path = "assets/bgm_loop.wav"
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(stereo_wave_int.tobytes())
    
    print(f"Generated BGM: {wav_path}")
    print(f"Duration: {duration}s, Sample rate: {sample_rate}Hz, Channels: {channels}")
    return wav_path

if __name__ == "__main__":
    try:
        # Ensure assets directory exists
        os.makedirs("assets", exist_ok=True)
        
        bgm_path = generate_bgm()
        print(f"Background music generated successfully: {bgm_path}")
        
        # Try to convert to OGG if ffmpeg is available
        try:
            import subprocess
            ogg_path = "assets/bgm_loop.ogg"
            result = subprocess.run([
                "ffmpeg", "-i", bgm_path, "-codec:a", "libvorbis", 
                "-q:a", "4", "-y", ogg_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Converted to OGG: {ogg_path}")
                # Keep both formats
            else:
                print("FFmpeg conversion failed, keeping WAV format")
                print("Error:", result.stderr)
        except FileNotFoundError:
            print("FFmpeg not available, keeping WAV format")
            
    except Exception as e:
        print(f"Error generating BGM: {e}")