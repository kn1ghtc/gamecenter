#!/usr/bin/env python3
"""
Enhanced Asset Downloader for VFX and Audio
Downloads additional assets with better fallback handling
"""

import os
import sys
from pathlib import Path
import requests
import json
import base64

class VFXAudioDownloader:
    def __init__(self, base_dir="assets"):
        self.base_dir = Path(base_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def create_hit_spark_texture(self):
        """Create a hit spark texture programmatically"""
        try:
            from PIL import Image, ImageDraw
            import math
            
            # Create 128x128 hit spark texture
            size = 128
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            center = size // 2
            
            # Create radial spark pattern
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                # Inner spark
                x1 = center + int(20 * math.cos(rad))
                y1 = center + int(20 * math.sin(rad))
                x2 = center + int(45 * math.cos(rad))
                y2 = center + int(45 * math.sin(rad))
                draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 100, 200), width=3)
                
                # Outer spark
                x3 = center + int(25 * math.cos(rad + 0.3))
                y3 = center + int(25 * math.sin(rad + 0.3))
                x4 = center + int(50 * math.cos(rad + 0.3))
                y4 = center + int(50 * math.sin(rad + 0.3))
                draw.line([(x3, y3), (x4, y4)], fill=(255, 200, 50, 150), width=2)
            
            # Central glow
            draw.ellipse([center-15, center-15, center+15, center+15], 
                        fill=(255, 255, 255, 180))
            draw.ellipse([center-8, center-8, center+8, center+8], 
                        fill=(255, 255, 200, 220))
            
            spark_path = self.base_dir / "vfx" / "hit_spark.png"
            spark_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(spark_path)
            print(f"Created hit spark texture: {spark_path}")
            return True
            
        except ImportError:
            print("PIL not available, creating simple fallback")
            return False
        except Exception as e:
            print(f"Failed to create hit spark texture: {e}")
            return False

    def create_particle_textures(self):
        """Create particle textures programmatically"""
        try:
            from PIL import Image, ImageDraw
            import math
            
            # Create smoke particle
            size = 64
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            center = size // 2
            # Create soft circular gradient
            for r in range(center, 0, -2):
                alpha = int(120 * (1 - r / center))
                color = (200, 200, 200, alpha)
                draw.ellipse([center-r, center-r, center+r, center+r], 
                           fill=color, outline=None)
            
            particle_path = self.base_dir / "particles" / "smoke.png"
            particle_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(particle_path)
            print(f"Created smoke particle: {particle_path}")
            
            # Create energy particle (blue/white)
            img2 = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw2 = ImageDraw.Draw(img2)
            
            for r in range(center, 0, -2):
                alpha = int(150 * (1 - r / center))
                blue_val = int(100 + 155 * (1 - r / center))
                color = (blue_val, blue_val, 255, alpha)
                draw2.ellipse([center-r, center-r, center+r, center+r], 
                            fill=color, outline=None)
            
            energy_path = self.base_dir / "particles" / "energy.png"
            img2.save(energy_path)
            print(f"Created energy particle: {energy_path}")
            
            return True
            
        except Exception as e:
            print(f"Failed to create particle textures: {e}")
            return False

    def create_sound_effects(self):
        """Create basic sound effect files"""
        try:
            import wave
            import numpy as np
            
            # Create hit sound (short impact)
            sample_rate = 44100
            duration = 0.2  # 200ms
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Impact sound: quick frequency sweep with decay
            frequency = 800 * np.exp(-t * 10)  # Frequency drops quickly
            amplitude = np.exp(-t * 15)  # Fast decay
            
            # Add some noise for texture
            noise = np.random.normal(0, 0.1, len(t))
            waveform = amplitude * (np.sin(2 * np.pi * frequency * t) + 0.3 * noise)
            
            # Convert to 16-bit
            waveform = (waveform * 32767).astype(np.int16)
            
            hit_path = self.base_dir / "sounds" / "hit_generated.wav"
            hit_path.parent.mkdir(parents=True, exist_ok=True)
            
            with wave.open(str(hit_path), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(waveform.tobytes())
            
            print(f"Created hit sound: {hit_path}")
            
            # Create combo sound (higher pitched, musical)
            frequency = 1200 * np.exp(-t * 8)
            amplitude = np.exp(-t * 12)
            waveform2 = amplitude * np.sin(2 * np.pi * frequency * t)
            waveform2 = (waveform2 * 32767).astype(np.int16)
            
            combo_path = self.base_dir / "sounds" / "combo_generated.wav"
            with wave.open(str(combo_path), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(waveform2.tobytes())
            
            print(f"Created combo sound: {combo_path}")
            return True
            
        except ImportError:
            print("NumPy/Wave not available for sound generation")
            return False
        except Exception as e:
            print(f"Failed to create sound effects: {e}")
            return False

    def download_free_resources(self):
        """Try to download from known free resource URLs"""
        free_resources = [
            {
                "url": "https://freesound.org/data/previews/316/316847_3268719-lq.mp3",
                "name": "hit_sound.mp3", 
                "target": "sounds"
            },
            # Add more URLs as available
        ]
        
        success_count = 0
        for resource in free_resources:
            try:
                response = self.session.get(resource["url"], timeout=10)
                if response.status_code == 200:
                    target_path = self.base_dir / resource["target"] / resource["name"]
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded: {target_path}")
                    success_count += 1
            except Exception as e:
                print(f"Failed to download {resource['url']}: {e}")
        
        return success_count > 0

    def enhance_assets(self):
        """Create and download enhanced VFX and audio assets"""
        print("Enhancing VFX and Audio assets...")
        
        results = {
            "hit_spark": self.create_hit_spark_texture(),
            "particles": self.create_particle_textures(), 
            "sounds": self.create_sound_effects(),
            "downloads": self.download_free_resources()
        }
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"\nVFX/Audio enhancement completed: {success_count}/{total_count} successful")
        
        # Create enhanced asset index
        asset_index = {
            "vfx": {
                "hit_spark.png": "Generated radial spark texture",
                "energy_ball.png": "Generated energy particle"
            },
            "particles": {
                "smoke.png": "Generated smoke particle",
                "energy.png": "Generated energy particle"
            },
            "sounds": {
                "hit_generated.wav": "Generated impact sound",
                "combo_generated.wav": "Generated combo sound"
            }
        }
        
        index_path = self.base_dir / "asset_index.json"
        with open(index_path, 'w') as f:
            json.dump(asset_index, f, indent=2)
        
        print(f"Created asset index: {index_path}")
        return success_count > 0


def main():
    """Main function for VFX/Audio enhancement"""
    print("StreetBattle VFX/Audio Enhancer")
    print("=" * 35)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    enhancer = VFXAudioDownloader("assets")
    
    try:
        success = enhancer.enhance_assets()
        
        if success:
            print("\n✓ VFX/Audio enhancement completed successfully!")
        else:
            print("\n⚠ Some enhancements failed, but basic assets should be available.")
        
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())