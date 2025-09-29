#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强音频系统 - 专业格斗游戏音频管理器
Enhanced Audio System - Professional Fighting Game Audio Manager
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from enum import Enum
import threading
import time


class AudioCategory(Enum):
    """音频分类枚举"""
    BGM = "bgm"
    SFX = "sfx"
    VOICE = "voice"
    UI = "ui"
    AMBIENT = "ambient"


class AudioPriority(Enum):
    """音频优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EnhancedAudioSystem:
    """增强的音频系统，支持专业音频管理"""
    
    def __init__(self, base=None):
        self.base = base
        self.sounds: Dict[str, Any] = {}
        self.music_tracks: Dict[str, Any] = {}
        self.current_bgm = None
        self.bgm_volume = 0.7
        self.sfx_volume = 0.8
        self.voice_volume = 0.9
        self.master_volume = 1.0
        
        # 音频配置
        self.audio_config = {
            "sample_rate": 44100,
            "channels": 2,
            "buffer_size": 1024,
            "fade_duration": 1.0,
            "max_simultaneous_sounds": 32
        }
        
        # 活动音频跟踪
        self.active_sounds: List[Any] = []
        self.sound_history: List[str] = []
        self.max_history = 100
        
        # 初始化音频库
        self._initialize_audio_library()
        
        # 加载音频配置
        self._load_audio_configuration()
    
    def _initialize_audio_library(self):
        """初始化音频库"""
        try:
            # 创建音频目录结构
            audio_dirs = [
                "assets/audio/bgm",
                "assets/audio/sfx/combat",
                "assets/audio/sfx/ui",
                "assets/audio/voice/characters",
                "assets/audio/voice/announcer",
                "assets/audio/ambient"
            ]
            
            for audio_dir in audio_dirs:
                Path(audio_dir).mkdir(parents=True, exist_ok=True)
            
            print("✅ 音频目录结构已创建")
            
        except Exception as e:
            print(f"❌ 音频库初始化失败: {e}")
    
    def _load_audio_configuration(self):
        """加载音频配置文件"""
        config_file = Path("config/audio_config.json")
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.audio_config.update(loaded_config)
                print("✅ 音频配置已加载")
            except Exception as e:
                print(f"⚠️  音频配置加载失败: {e}")
        else:
            # 创建默认配置
            self._create_default_audio_config()
    
    def _create_default_audio_config(self):
        """创建默认音频配置"""
        default_config = {
            "master_volume": 1.0,
            "bgm_volume": 0.7,
            "sfx_volume": 0.8,
            "voice_volume": 0.9,
            "ui_volume": 0.6,
            
            # 格斗游戏音频映射
            "character_voices": {
                "kyo": {
                    "attack_1": "kyo_attack_01.ogg",
                    "attack_2": "kyo_attack_02.ogg",
                    "special_move": "kyo_special.ogg",
                    "victory": "kyo_victory.ogg",
                    "defeat": "kyo_defeat.ogg"
                },
                "iori": {
                    "attack_1": "iori_attack_01.ogg",
                    "attack_2": "iori_attack_02.ogg",
                    "special_move": "iori_special.ogg",
                    "victory": "iori_victory.ogg",
                    "defeat": "iori_defeat.ogg"
                },
                "mr_big": {
                    "attack_1": "mr_big_attack_01.ogg",
                    "attack_2": "mr_big_attack_02.ogg",
                    "special_move": "mr_big_special.ogg",
                    "victory": "mr_big_victory.ogg",
                    "defeat": "mr_big_defeat.ogg"
                },
                "ramon": {
                    "attack_1": "ramon_attack_01.ogg",
                    "attack_2": "ramon_attack_02.ogg",
                    "special_move": "ramon_special.ogg",
                    "victory": "ramon_victory.ogg",
                    "defeat": "ramon_defeat.ogg"
                },
                "wolfgang": {
                    "attack_1": "wolfgang_attack_01.ogg",
                    "attack_2": "wolfgang_attack_02.ogg",
                    "special_move": "wolfgang_special.ogg",
                    "victory": "wolfgang_victory.ogg",
                    "defeat": "wolfgang_defeat.ogg"
                }
            },
            
            # 战斗音效
            "combat_sfx": {
                "light_punch": "punch_light.ogg",
                "heavy_punch": "punch_heavy.ogg",
                "light_kick": "kick_light.ogg",
                "heavy_kick": "kick_heavy.ogg",
                "special_hit": "special_hit.ogg",
                "block": "block.ogg",
                "jump": "jump.ogg",
                "land": "land.ogg",
                "combo_hit": "combo_hit.ogg",
                "super_move": "super_move.ogg"
            },
            
            # 界面音效
            "ui_sfx": {
                "menu_select": "menu_select.ogg",
                "menu_confirm": "menu_confirm.ogg",
                "menu_cancel": "menu_cancel.ogg",
                "game_start": "game_start.ogg",
                "round_start": "round_start.ogg",
                "round_end": "round_end.ogg",
                "match_end": "match_end.ogg"
            },
            
            # 背景音乐
            "bgm_tracks": {
                "main_menu": "main_menu.ogg",
                "character_select": "character_select.ogg",
                "battle_stage_1": "battle_01.ogg",
                "battle_stage_2": "battle_02.ogg",
                "battle_stage_3": "battle_03.ogg",
                "victory_theme": "victory.ogg",
                "credits": "credits.ogg"
            }
        }
        
        # 保存配置
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "audio_config.json", 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self.audio_config.update(default_config)
        print("✅ 默认音频配置已创建")
    
    def load_character_voice_pack(self, character_id: str) -> bool:
        """加载角色语音包"""
        try:
            voice_dir = Path(f"assets/audio/voice/characters/{character_id}")
            if not voice_dir.exists():
                print(f"⚠️  角色语音目录不存在: {character_id}")
                return False
            
            # 获取角色语音配置
            char_voices = self.audio_config.get("character_voices", {}).get(character_id, {})
            
            loaded_count = 0
            for voice_type, filename in char_voices.items():
                voice_path = voice_dir / filename
                sound_key = f"{character_id}_{voice_type}"
                
                if self.load_sfx(str(voice_path), sound_key):
                    loaded_count += 1
            
            print(f"✅ 已加载 {character_id} 语音包: {loaded_count} 个音频文件")
            return loaded_count > 0
            
        except Exception as e:
            print(f"❌ 角色语音包加载失败 {character_id}: {e}")
            return False
    
    def play_character_voice(self, character_id: str, voice_type: str, volume: float = 1.0):
        """播放角色语音"""
        sound_key = f"{character_id}_{voice_type}"
        self.play_sfx(sound_key, volume * self.voice_volume)
    
    def load_combat_sfx_pack(self) -> bool:
        """加载战斗音效包"""
        try:
            combat_dir = Path("assets/audio/sfx/combat")
            combat_sfx = self.audio_config.get("combat_sfx", {})
            
            loaded_count = 0
            for sfx_type, filename in combat_sfx.items():
                sfx_path = combat_dir / filename
                if self.load_sfx(str(sfx_path), sfx_type):
                    loaded_count += 1
            
            print(f"✅ 已加载战斗音效包: {loaded_count} 个音频文件")
            return loaded_count > 0
            
        except Exception as e:
            print(f"❌ 战斗音效包加载失败: {e}")
            return False
    
    def play_combat_sfx(self, sfx_type: str, volume: float = 1.0):
        """播放战斗音效"""
        self.play_sfx(sfx_type, volume * self.sfx_volume)
    
    def load_ui_sfx_pack(self) -> bool:
        """加载界面音效包"""
        try:
            ui_dir = Path("assets/audio/sfx/ui")
            ui_sfx = self.audio_config.get("ui_sfx", {})
            
            loaded_count = 0
            for sfx_type, filename in ui_sfx.items():
                sfx_path = ui_dir / filename
                if self.load_sfx(str(sfx_path), sfx_type):
                    loaded_count += 1
            
            print(f"✅ 已加载界面音效包: {loaded_count} 个音频文件")
            return loaded_count > 0
            
        except Exception as e:
            print(f"❌ 界面音效包加载失败: {e}")
            return False
    
    def play_ui_sfx(self, sfx_type: str, volume: float = 1.0):
        """播放界面音效"""
        ui_volume = self.audio_config.get("ui_volume", 0.6)
        self.play_sfx(sfx_type, volume * ui_volume)
    
    def load_bgm_library(self) -> bool:
        """加载背景音乐库"""
        try:
            bgm_dir = Path("assets/audio/bgm")
            bgm_tracks = self.audio_config.get("bgm_tracks", {})
            
            loaded_count = 0
            for track_name, filename in bgm_tracks.items():
                bgm_path = bgm_dir / filename
                if self.load_bgm(str(bgm_path), track_name):
                    loaded_count += 1
            
            print(f"✅ 已加载背景音乐库: {loaded_count} 个音乐文件")
            return loaded_count > 0
            
        except Exception as e:
            print(f"❌ 背景音乐库加载失败: {e}")
            return False
    
    def crossfade_bgm(self, track_name: str, fade_duration: float = 2.0):
        """淡入淡出切换背景音乐"""
        def fade_task():
            try:
                # 淡出当前音乐
                if self.current_bgm:
                    original_volume = self.bgm_volume
                    for i in range(20):
                        volume = original_volume * (1.0 - i / 20.0)
                        self.set_bgm_volume(volume)
                        time.sleep(fade_duration / 40.0)
                    
                    self.stop_bgm()
                
                # 播放新音乐并淡入
                if self.play_bgm(track_name, volume=0.0):
                    for i in range(20):
                        volume = self.bgm_volume * (i / 20.0)
                        self.set_bgm_volume(volume)
                        time.sleep(fade_duration / 40.0)
                    
                    self.set_bgm_volume(self.bgm_volume)
                
            except Exception as e:
                print(f"❌ 音乐淡入淡出失败: {e}")
        
        # 在后台线程执行淡入淡出
        fade_thread = threading.Thread(target=fade_task)
        fade_thread.daemon = True
        fade_thread.start()
    
    def create_dynamic_audio_mixer(self):
        """创建动态音频混音器"""
        mixer_config = {
            "real_time_volume_control": True,
            "spatial_audio_support": True,
            "reverb_effects": {
                "arena": {"room_size": 0.7, "damping": 0.5},
                "outdoor": {"room_size": 0.9, "damping": 0.3},
                "underground": {"room_size": 0.5, "damping": 0.8}
            },
            "compression": {
                "enabled": True,
                "threshold": -20.0,
                "ratio": 4.0,
                "attack": 0.003,
                "release": 0.1
            }
        }
        
        config_file = Path("config/audio_mixer.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mixer_config, f, indent=2, ensure_ascii=False)
        
        print("✅ 动态音频混音器配置已创建")
        return mixer_config
    
    # 继承原有的基础方法并增强
    def load_sfx(self, path: str, name: Optional[str] = None) -> bool:
        """增强的音效加载"""
        key = name or path
        if not self.base:
            # 注册占位符用于测试
            self.sounds[key] = {"path": path, "loaded": False}
            return True
        
        try:
            sound = self.base.loader.loadSfx(path)
            if sound:
                self.sounds[key] = {
                    "sound": sound,
                    "path": path,
                    "loaded": True,
                    "category": AudioCategory.SFX,
                    "priority": AudioPriority.NORMAL
                }
                return True
        except Exception as e:
            print(f"⚠️  音效加载失败 {path}: {e}")
        
        self.sounds[key] = {"path": path, "loaded": False}
        return False
    
    def play_sfx(self, name_or_path: str, volume: float = 1.0, priority: AudioPriority = AudioPriority.NORMAL):
        """增强的音效播放"""
        # 记录播放历史
        self.sound_history.append(name_or_path)
        if len(self.sound_history) > self.max_history:
            self.sound_history.pop(0)
        
        # 尝试通过注册名称播放
        sound_data = self.sounds.get(name_or_path)
        if sound_data and sound_data.get("loaded"):
            try:
                sound = sound_data["sound"]
                sound.setVolume(volume * self.sfx_volume * self.master_volume)
                sound.play()
                return True
            except Exception as e:
                print(f"⚠️  音效播放失败 {name_or_path}: {e}")
        
        # 回退: 如果有base，尝试即时加载播放
        if self.base:
            try:
                sound = self.base.loader.loadSfx(name_or_path)
                if sound:
                    sound.setVolume(volume * self.sfx_volume * self.master_volume)
                    sound.play()
                    return True
            except Exception as e:
                print(f"⚠️  即时音效播放失败 {name_or_path}: {e}")
        
        # 最终回退: 控制台输出
        print(f'🔊 SFX播放 (占位): {name_or_path} (音量: {volume:.2f})')
        return False
    
    def load_bgm(self, path: str, name: Optional[str] = None) -> bool:
        """增强的背景音乐加载"""
        key = name or path
        if not self.base:
            self.music_tracks[key] = {"path": path, "loaded": False}
            return True
        
        try:
            music = self.base.loader.loadMusic(path)
            if music:
                self.music_tracks[key] = {
                    "music": music,
                    "path": path,
                    "loaded": True
                }
                return True
        except Exception as e:
            print(f"⚠️  背景音乐加载失败 {path}: {e}")
        
        self.music_tracks[key] = {"path": path, "loaded": False}
        return False
    
    def play_bgm(self, track_name: str, loop: bool = True, volume: float = None) -> bool:
        """增强的背景音乐播放"""
        if volume is None:
            volume = self.bgm_volume
        
        track_data = self.music_tracks.get(track_name)
        if track_data and track_data.get("loaded"):
            try:
                music = track_data["music"]
                music.setVolume(volume * self.master_volume)
                music.setLoop(loop)
                music.play()
                self.current_bgm = track_name
                print(f"🎵 播放背景音乐: {track_name}")
                return True
            except Exception as e:
                print(f"⚠️  背景音乐播放失败 {track_name}: {e}")
        
        print(f'🎵 BGM播放 (占位): {track_name} (循环: {loop}, 音量: {volume:.2f})')
        return False
    
    def stop_bgm(self):
        """停止背景音乐"""
        if self.current_bgm and self.current_bgm in self.music_tracks:
            track_data = self.music_tracks[self.current_bgm]
            if track_data.get("loaded"):
                try:
                    track_data["music"].stop()
                except Exception as e:
                    print(f"⚠️  背景音乐停止失败: {e}")
        
        self.current_bgm = None
        print("🔇 背景音乐已停止")
    
    def set_master_volume(self, volume: float):
        """设置主音量"""
        self.master_volume = max(0.0, min(1.0, volume))
        print(f"🔊 主音量设置为: {self.master_volume:.2f}")
    
    def set_bgm_volume(self, volume: float):
        """设置背景音乐音量"""
        self.bgm_volume = max(0.0, min(1.0, volume))
        if self.current_bgm and self.current_bgm in self.music_tracks:
            track_data = self.music_tracks[self.current_bgm]
            if track_data.get("loaded"):
                try:
                    track_data["music"].setVolume(self.bgm_volume * self.master_volume)
                except Exception:
                    pass
    
    def set_sfx_volume(self, volume: float):
        """设置音效音量"""
        self.sfx_volume = max(0.0, min(1.0, volume))
        print(f"🔊 音效音量设置为: {self.sfx_volume:.2f}")
    
    def set_voice_volume(self, volume: float):
        """设置语音音量"""
        self.voice_volume = max(0.0, min(1.0, volume))
        print(f"🔊 语音音量设置为: {self.voice_volume:.2f}")
    
    def get_audio_status(self) -> Dict[str, Any]:
        """获取音频系统状态"""
        return {
            "master_volume": self.master_volume,
            "bgm_volume": self.bgm_volume,
            "sfx_volume": self.sfx_volume,
            "voice_volume": self.voice_volume,
            "current_bgm": self.current_bgm,
            "loaded_sounds": len([s for s in self.sounds.values() if s.get("loaded")]),
            "loaded_music": len([m for m in self.music_tracks.values() if m.get("loaded")]),
            "total_sounds": len(self.sounds),
            "total_music": len(self.music_tracks),
            "recent_sounds": self.sound_history[-10:] if self.sound_history else []
        }
    
    def cleanup(self):
        """增强的清理方法"""
        try:
            print("🧹 开始增强音频清理...")
            
            # 停止所有音乐
            for track_name, track_data in self.music_tracks.items():
                if track_data.get("loaded"):
                    try:
                        track_data["music"].stop()
                    except Exception as e:
                        print(f"⚠️  音乐停止警告 {track_name}: {e}")
            
            # 停止所有音效
            stopped_count = 0
            for sound_name, sound_data in self.sounds.items():
                if sound_data.get("loaded"):
                    try:
                        sound_data["sound"].stop()
                        stopped_count += 1
                    except Exception as e:
                        print(f"⚠️  音效停止警告 {sound_name}: {e}")
            
            print(f"🔇 已停止 {stopped_count} 个音效")
            
            # 清理资源
            self.sounds.clear()
            self.music_tracks.clear()
            self.current_bgm = None
            self.sound_history.clear()
            
            # 保存音频配置
            self._save_audio_configuration()
            
            print("✅ 增强音频系统清理完成")
            
        except Exception as e:
            print(f"❌ 音频清理错误: {e}")
        finally:
            # 确保所有内容都被清理
            self.sounds = {}
            self.music_tracks = {}
            self.current_bgm = None
    
    def _save_audio_configuration(self):
        """保存音频配置"""
        try:
            config_file = Path("config/audio_runtime.json")
            runtime_config = {
                "master_volume": self.master_volume,
                "bgm_volume": self.bgm_volume,
                "sfx_volume": self.sfx_volume,
                "voice_volume": self.voice_volume,
                "last_bgm": self.current_bgm,
                "audio_history": self.sound_history[-20:] if self.sound_history else []
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(runtime_config, f, indent=2, ensure_ascii=False)
            
            print("✅ 音频运行时配置已保存")
        except Exception as e:
            print(f"⚠️  音频配置保存失败: {e}")


AudioSystem = EnhancedAudioSystem


def create_sample_audio_files():
    """创建示例音频文件占位符"""
    print("🎵 创建示例音频文件占位符...")
    
    # 音频文件结构
    audio_structure = {
        "assets/audio/bgm": [
            "main_menu.ogg", "character_select.ogg", "battle_01.ogg", 
            "battle_02.ogg", "battle_03.ogg", "victory.ogg", "credits.ogg"
        ],
        "assets/audio/sfx/combat": [
            "punch_light.ogg", "punch_heavy.ogg", "kick_light.ogg", 
            "kick_heavy.ogg", "special_hit.ogg", "block.ogg", "jump.ogg", 
            "land.ogg", "combo_hit.ogg", "super_move.ogg"
        ],
        "assets/audio/sfx/ui": [
            "menu_select.ogg", "menu_confirm.ogg", "menu_cancel.ogg", 
            "game_start.ogg", "round_start.ogg", "round_end.ogg", "match_end.ogg"
        ]
    }
    
    # 角色语音文件
    characters = ["kyo", "iori", "mr_big", "ramon", "wolfgang"]
    voice_types = ["attack_01.ogg", "attack_02.ogg", "special.ogg", "victory.ogg", "defeat.ogg"]
    
    for char in characters:
        char_dir = f"assets/audio/voice/characters/{char}"
        audio_structure[char_dir] = voice_types
    
    # 创建占位符文件
    created_count = 0
    for directory, files in audio_structure.items():
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            placeholder_file = dir_path / filename
            if not placeholder_file.exists():
                # 创建音频元数据占位符
                metadata = {
                    "type": "audio_placeholder",
                    "format": "ogg",
                    "sample_rate": 44100,
                    "channels": 2,
                    "duration": 2.0,
                    "description": f"Audio placeholder for {filename}",
                    "ready_for_recording": True
                }
                
                with open(placeholder_file.with_suffix('.json'), 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                created_count += 1
    
    print(f"✅ 创建了 {created_count} 个音频占位符")


def main():
    """测试增强音频系统"""
    print("🎮 Street Battle 增强音频系统测试")
    print("=" * 50)
    
    # 创建音频系统
    audio_system = EnhancedAudioSystem()
    
    # 创建示例音频文件
    create_sample_audio_files()
    
    # 加载音频包
    print("\n📦 加载音频包...")
    audio_system.load_combat_sfx_pack()
    audio_system.load_ui_sfx_pack()
    audio_system.load_bgm_library()
    
    # 加载角色语音包
    print("\n🎭 加载角色语音包...")
    for char in ["kyo", "iori", "mr_big", "ramon", "wolfgang"]:
        audio_system.load_character_voice_pack(char)
    
    # 测试音频播放
    print("\n🔊 测试音频播放...")
    audio_system.play_ui_sfx("menu_select")
    audio_system.play_combat_sfx("punch_heavy")
    audio_system.play_character_voice("kyo", "attack_1")
    audio_system.play_bgm("main_menu")
    
    # 测试音量控制
    print("\n🎚️  测试音量控制...")
    audio_system.set_master_volume(0.8)
    audio_system.set_sfx_volume(0.9)
    audio_system.set_voice_volume(0.7)
    
    # 显示系统状态
    print("\n📊 音频系统状态:")
    status = audio_system.get_audio_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # 创建动态混音器
    print("\n🎛️  创建动态混音器...")
    audio_system.create_dynamic_audio_mixer()
    
    # 清理
    print("\n🧹 清理音频系统...")
    audio_system.cleanup()
    
    print("\n✨ 增强音频系统测试完成!")
    print("\n💡 下一步:")
    print("1. 录制或获取真实音频文件")
    print("2. 替换占位符文件")
    print("3. 集成到游戏主循环")
    print("4. 测试实时音频效果")


if __name__ == "__main__":
    main()