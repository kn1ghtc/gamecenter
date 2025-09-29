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

        # 项目目录结构
        self.project_root = Path(__file__).resolve().parent
        self.audio_root = self.project_root / "assets" / "audio"
        self.config_root = self.project_root / "config"
        
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
                self.audio_root / "bgm",
                self.audio_root / "sfx" / "combat",
                self.audio_root / "sfx" / "ui",
                self.audio_root / "voice" / "characters",
                self.audio_root / "voice" / "announcer",
                self.audio_root / "ambient",
                self.audio_root / "music",
            ]

            for audio_dir in audio_dirs:
                audio_dir.mkdir(parents=True, exist_ok=True)
            
            print("✅ 音频目录结构已创建")
            
        except Exception as e:
            print(f"❌ 音频库初始化失败: {e}")
    
    def _load_audio_configuration(self):
        """加载音频配置文件"""
        config_file = self.config_root / "audio_config.json"

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.audio_config.update(loaded_config)
                print("✅ 音频配置已加载")
                self._ensure_real_audio_config()
            except Exception as e:
                print(f"⚠️  音频配置加载失败: {e}")
                self._create_default_audio_config()
        else:
            # 创建默认配置
            self._create_default_audio_config()
    
    def _resolve_audio_file(self, reference: str | Path) -> Path:
        """将音频资源引用解析为绝对路径"""
        path = Path(reference)
        if path.is_absolute():
            return path
        if path.parts:
            first = path.parts[0]
            if first == 'assets':
                return self.project_root / path
            if first == 'audio':
                return self.audio_root / Path(*path.parts[1:])
        return self.audio_root / path

    def _ensure_real_audio_config(self):
        """如果检测到仍然使用占位符，则重建音频配置"""
        def _has_real_audio(mapping: Dict[str, str]) -> bool:
            for value in mapping.values():
                if not value:
                    continue
                try:
                    audio_path = self._resolve_audio_file(value)
                except Exception:
                    continue
                if audio_path.exists() and audio_path.stat().st_size > 2048:
                    return True
            return False

        sections = {
            "bgm_tracks": "背景音乐",
            "combat_sfx": "战斗音效",
            "ui_sfx": "界面音效",
        }

        for key, label in sections.items():
            if not _has_real_audio(self.audio_config.get(key, {})):
                print(f"⚠️ 音频配置缺少真实的{label}资源，正在重新生成...")
                self._create_default_audio_config()
                return

        for character_id, voice_map in self.audio_config.get("character_voices", {}).items():
            if not _has_real_audio(voice_map):
                print(f"⚠️ 角色 {character_id} 的语音资源缺失，将重建音频配置...")
                self._create_default_audio_config()
                return

    def _lookup_audio_reference(self, key: str) -> Optional[str]:
        """根据配置查找音频引用"""
        combat = self.audio_config.get("combat_sfx", {})
        if key in combat:
            return combat[key]

        ui_sfx = self.audio_config.get("ui_sfx", {})
        if key in ui_sfx:
            return ui_sfx[key]

        if "_" in key:
            character_id, voice_type = key.split("_", 1)
            character_voice_map = self.audio_config.get("character_voices", {}).get(character_id, {})
            if voice_type in character_voice_map:
                return character_voice_map[voice_type]

        return None

    def _create_default_audio_config(self):
        """创建基于真实资源的默认音频配置"""

        def rel(path: Path) -> str:
            try:
                return path.relative_to(self.project_root).as_posix()
            except ValueError:
                return path.as_posix()

        def ensure(path: Path, label: str) -> str:
            if not path.exists():
                print(f"⚠️ 音频资源缺失: {label} -> {path}")
            return rel(path)

        bgm_defaults = {
            "main_menu": ensure(self.audio_root / "bgm_loop.ogg", "main_menu"),
            "character_select": ensure(self.audio_root / "music" / "win.ogg", "character_select"),
            "battle_stage_1": ensure(self.audio_root / "bgm_loop.wav", "battle_stage_1"),
            "battle_stage_2": ensure(self.audio_root / "music" / "lose.ogg", "battle_stage_2"),
            "battle_stage_3": ensure(self.audio_root / "bgm_loop.ogg", "battle_stage_3"),
            "victory_theme": ensure(self.audio_root / "victory_enhanced.wav", "victory_theme"),
            "credits": ensure(self.audio_root / "bgm_loop.wav", "credits"),
        }

        combat_sfx_defaults = {
            "light_punch": ensure(self.audio_root / "hit.wav", "light_punch"),
            "heavy_punch": ensure(self.audio_root / "combo_enhanced.wav", "heavy_punch"),
            "light_kick": ensure(self.audio_root / "combo_generated.wav", "light_kick"),
            "heavy_kick": ensure(self.audio_root / "combo.wav", "heavy_kick"),
            "special_hit": ensure(self.audio_root / "victory_enhanced.wav", "special_hit"),
            "block": ensure(self.audio_root / "defeat_enhanced.wav", "block"),
            "jump": ensure(self.audio_root / "combo_generated.wav", "jump"),
            "land": ensure(self.audio_root / "hit.wav", "land"),
            "combo_hit": ensure(self.audio_root / "combo.wav", "combo_hit"),
            "super_move": ensure(self.audio_root / "victory_enhanced.wav", "super_move"),
        }

        ui_sfx_defaults = {
            "menu_select": ensure(self.audio_root / "combo_generated.wav", "menu_select"),
            "menu_confirm": ensure(self.audio_root / "combo_enhanced.wav", "menu_confirm"),
            "menu_cancel": ensure(self.audio_root / "hit.wav", "menu_cancel"),
            "game_start": ensure(self.audio_root / "victory_enhanced.wav", "game_start"),
            "round_start": ensure(self.audio_root / "combo.wav", "round_start"),
            "round_end": ensure(self.audio_root / "defeat_enhanced.wav", "round_end"),
            "match_end": ensure(self.audio_root / "victory_enhanced.wav", "match_end"),
        }

        voice_template = {
            "attack_1": ensure(self.audio_root / "combo.wav", "voice_attack_1"),
            "attack_2": ensure(self.audio_root / "combo_enhanced.wav", "voice_attack_2"),
            "special_move": ensure(self.audio_root / "victory_enhanced.wav", "voice_special"),
            "victory": ensure(self.audio_root / "victory_enhanced.wav", "voice_victory"),
            "defeat": ensure(self.audio_root / "defeat_enhanced.wav", "voice_defeat"),
        }

        character_ids = ["kyo", "iori", "mr_big", "ramon", "wolfgang"]
        character_voices = {char: dict(voice_template) for char in character_ids}

        default_config = {
            "master_volume": 1.0,
            "bgm_volume": 0.7,
            "sfx_volume": 0.8,
            "voice_volume": 0.9,
            "ui_volume": 0.6,
            "character_voices": character_voices,
            "combat_sfx": combat_sfx_defaults,
            "ui_sfx": ui_sfx_defaults,
            "bgm_tracks": bgm_defaults,
        }

        self.config_root.mkdir(exist_ok=True)
        config_path = self.config_root / "audio_config.json"
        with config_path.open('w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

        self.audio_config.update(default_config)
        print("✅ 基于真实资源的默认音频配置已创建")
    
    def load_character_voice_pack(self, character_id: str) -> bool:
        """加载角色语音包"""
        try:
            # 获取角色语音配置
            char_voices = self.audio_config.get("character_voices", {}).get(character_id, {})
            if not char_voices:
                print(f"⚠️  未在配置中找到角色语音映射: {character_id}")
                return False
            
            loaded_count = 0
            for voice_type, filename in char_voices.items():
                voice_path = self._resolve_audio_file(filename)
                if not voice_path.exists():
                    print(f"⚠️  角色语音缺失 {character_id} - {voice_type}: {voice_path}")
                    continue
                sound_key = f"{character_id}_{voice_type}"
                
                if self.load_sfx(voice_path.as_posix(), sound_key):
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
            combat_sfx = self.audio_config.get("combat_sfx", {})
            
            loaded_count = 0
            for sfx_type, filename in combat_sfx.items():
                sfx_path = self._resolve_audio_file(filename)
                if not sfx_path.exists():
                    print(f"⚠️  战斗音效缺失 {sfx_type}: {sfx_path}")
                    continue

                if self.load_sfx(sfx_path.as_posix(), sfx_type):
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
            ui_sfx = self.audio_config.get("ui_sfx", {})
            
            loaded_count = 0
            for sfx_type, filename in ui_sfx.items():
                sfx_path = self._resolve_audio_file(filename)
                if not sfx_path.exists():
                    print(f"⚠️  界面音效缺失 {sfx_type}: {sfx_path}")
                    continue

                if self.load_sfx(sfx_path.as_posix(), sfx_type):
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
            bgm_tracks = self.audio_config.get("bgm_tracks", {})
            
            loaded_count = 0
            for track_name, filename in bgm_tracks.items():
                bgm_path = self._resolve_audio_file(filename)
                if not bgm_path.exists():
                    print(f"⚠️  背景音乐缺失 {track_name}: {bgm_path}")
                    continue

                if self.load_bgm(bgm_path.as_posix(), track_name):
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
        
        config_file = self.config_root / "audio_mixer.json"
        self.config_root.mkdir(exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mixer_config, f, indent=2, ensure_ascii=False)
        
        print("✅ 动态音频混音器配置已创建")
        return mixer_config
    
    # 继承原有的基础方法并增强
    def load_sfx(self, path: str, name: Optional[str] = None) -> bool:
        """增强的音效加载"""
        key = name or path
        resolved_path = self._resolve_audio_file(path)
        resolved_str = resolved_path.as_posix()

        if not self.base:
            exists = resolved_path.exists()
            self.sounds[key] = {"path": resolved_str, "loaded": False, "exists": exists}
            return exists
        
        try:
            sound = self.base.loader.loadSfx(resolved_str)
            if sound:
                self.sounds[key] = {
                    "sound": sound,
                    "path": resolved_str,
                    "loaded": True,
                    "category": AudioCategory.SFX,
                    "priority": AudioPriority.NORMAL
                }
                return True
        except Exception as e:
            print(f"⚠️  音效加载失败 {resolved_str}: {e}")
        
        self.sounds[key] = {"path": resolved_str, "loaded": False}
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
        
        # 回退: 如果有base，尝试解析路径即时加载
        if self.base:
            attempted: set[str] = set()
            candidate_refs: List[str] = []

            if sound_data and sound_data.get("path"):
                candidate_refs.append(sound_data["path"])

            candidate_refs.append(name_or_path)

            lookup_ref = self._lookup_audio_reference(name_or_path)
            if lookup_ref:
                candidate_refs.append(lookup_ref)

            for reference in candidate_refs:
                if not reference:
                    continue
                resolved_candidate = self._resolve_audio_file(reference)
                candidate_str = resolved_candidate.as_posix()
                if candidate_str in attempted:
                    continue
                attempted.add(candidate_str)

                try:
                    sound = self.base.loader.loadSfx(candidate_str)
                    if sound:
                        sound.setVolume(volume * self.sfx_volume * self.master_volume)
                        sound.play()
                        self.sounds[name_or_path] = {
                            "sound": sound,
                            "path": candidate_str,
                            "loaded": True,
                            "category": AudioCategory.SFX,
                            "priority": priority
                        }
                        return True
                except Exception as e:
                    print(f"⚠️  即时音效播放失败 {candidate_str}: {e}")
        
        # 最终回退: 控制台输出
        print(f'🔊 SFX播放 (占位): {name_or_path} (音量: {volume:.2f})')
        return False
    
    def load_bgm(self, path: str, name: Optional[str] = None) -> bool:
        """增强的背景音乐加载"""
        key = name or path
        resolved_path = self._resolve_audio_file(path)
        resolved_str = resolved_path.as_posix()
        if not self.base:
            exists = resolved_path.exists()
            self.music_tracks[key] = {"path": resolved_str, "loaded": False, "exists": exists}
            return exists
        
        try:
            music = self.base.loader.loadMusic(resolved_str)
            if music:
                self.music_tracks[key] = {
                    "music": music,
                    "path": resolved_str,
                    "loaded": True
                }
                return True
        except Exception as e:
            print(f"⚠️  背景音乐加载失败 {resolved_str}: {e}")
        
        self.music_tracks[key] = {"path": resolved_str, "loaded": False}
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
        
        # 尝试在需要时即时加载背景音乐
        bgm_reference = self.audio_config.get("bgm_tracks", {}).get(track_name)
        if bgm_reference and self.load_bgm(bgm_reference, track_name):
            return self.play_bgm(track_name, loop=loop, volume=volume)

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
            self.config_root.mkdir(exist_ok=True)
            config_file = self.config_root / "audio_runtime.json"
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


def verify_audio_assets(audio_system: EnhancedAudioSystem) -> Dict[str, List[str]]:
    """验证音频资源是否落实为真实文件"""
    report: Dict[str, List[str]] = {"available": [], "missing": []}

    def collect(category: str, mapping: Dict[str, str]):
        for key, reference in mapping.items():
            path = audio_system._resolve_audio_file(reference)
            entry = f"{category}:{key} -> {path.as_posix()}"
            if path.exists() and path.stat().st_size > 1024:
                report["available"].append(entry)
            else:
                report["missing"].append(entry)

    collect("BGM", audio_system.audio_config.get("bgm_tracks", {}))
    collect("SFX", audio_system.audio_config.get("combat_sfx", {}))
    collect("UI", audio_system.audio_config.get("ui_sfx", {}))

    for character_id, voice_map in audio_system.audio_config.get("character_voices", {}).items():
        collect(f"VOICE:{character_id}", voice_map)

    if report["missing"]:
        print("⚠️ 以下音频资源缺失或无效:")
        for item in report["missing"]:
            print(f"   - {item}")
    else:
        print("✅ 所有音频映射均指向真实文件")

    return report


def main():
    """测试增强音频系统"""
    print("🎮 Street Battle 增强音频系统测试")
    print("=" * 50)
    
    # 创建音频系统
    audio_system = EnhancedAudioSystem()
    
    # 确认音频资产状态
    verify_audio_assets(audio_system)
    
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