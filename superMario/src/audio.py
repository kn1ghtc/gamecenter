#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Audio System
Handles sound effects and background music
"""

import pygame
import os
from pathlib import Path

class AudioSystem:
    """Manages all audio playback in the game"""

    def __init__(self, assets_dir="assets"):
        """Initialize audio system"""
        self.assets_dir = Path(assets_dir)
        self.sounds_dir = self.assets_dir / "sounds"

        # Audio settings
        self.master_volume = 0.7
        self.sfx_volume = 0.8
        self.music_volume = 0.6

        # Sound effects cache
        self.sound_effects = {}

        # Background music
        self.current_music = None
        self.music_playing = False

        # Load sound effects
        self._load_sound_effects()

    def _load_sound_effects(self):
        """Load all sound effects"""
        sound_files = {
            "jump": "jump.wav",
            "coin": "coin.wav",
            "powerup": "powerup.wav",
            "enemy_die": "enemy_die.wav",
            "player_die": "player_die.wav",
            "level_complete": "level_complete.wav",
            "game_over": "game_over.wav",
            "pause": "pause.wav",
            "menu_select": "menu_select.wav"
        }

        for sound_name, filename in sound_files.items():
            sound_path = self.sounds_dir / filename
            if sound_path.exists():
                try:
                    self.sound_effects[sound_name] = pygame.mixer.Sound(str(sound_path))
                    self.sound_effects[sound_name].set_volume(self.sfx_volume * self.master_volume)
                except Exception as e:
                    print(f"Failed to load sound {sound_name}: {e}")
                    self.sound_effects[sound_name] = None
            else:
                print(f"Sound file not found: {filename}")
                self.sound_effects[sound_name] = None

    def play_sound(self, sound_name):
        """Play a sound effect"""
        if sound_name in self.sound_effects and self.sound_effects[sound_name]:
            try:
                self.sound_effects[sound_name].play()
            except Exception as e:
                print(f"Failed to play sound {sound_name}: {e}")

    def play_jump_sound(self):
        """Play jump sound"""
        self.play_sound("jump")

    def play_coin_sound(self):
        """Play coin collection sound"""
        self.play_sound("coin")

    def play_powerup_sound(self):
        """Play powerup collection sound"""
        self.play_sound("powerup")

    def play_enemy_die_sound(self):
        """Play enemy defeat sound"""
        self.play_sound("enemy_die")

    def play_player_die_sound(self):
        """Play player death sound"""
        self.play_sound("player_die")

    def play_level_complete_sound(self):
        """Play level completion sound"""
        self.play_sound("level_complete")

    def play_game_over_sound(self):
        """Play game over sound"""
        self.play_sound("game_over")

    def play_pause_sound(self):
        """Play pause sound"""
        self.play_sound("pause")

    def play_menu_select_sound(self):
        """Play menu selection sound"""
        self.play_sound("menu_select")

    def play_background_music(self, music_file=None):
        """Play background music with WAV preferred and MP3 fallback"""
        candidates = []
        if music_file:
            candidates.append(music_file)
        # Prefer local generated wav, then mp3
        candidates.extend(["background_music.wav", "background_music.mp3"])

        chosen = None
        for fname in candidates:
            p = self.sounds_dir / fname
            if p.exists():
                chosen = fname
                break

        if chosen is None:
            print("Background music file not found: background_music.wav/mp3")
            return

        try:
            pygame.mixer.music.load(str(self.sounds_dir / chosen))
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            pygame.mixer.music.play(-1)
            self.music_playing = True
            self.current_music = chosen
        except Exception as e:
            print(f"Failed to play background music: {e}")

    def stop_background_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
        self.music_playing = False
        self.current_music = None

    def pause_background_music(self):
        """Pause background music"""
        pygame.mixer.music.pause()
        self.music_playing = False

    def unpause_background_music(self):
        """Unpause background music"""
        pygame.mixer.music.unpause()
        self.music_playing = True

    def set_master_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))
        self._update_all_volumes()

    def set_sfx_volume(self, volume):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))
        self._update_sfx_volumes()

    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_playing:
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)

    def _update_all_volumes(self):
        """Update all audio volumes"""
        self._update_sfx_volumes()
        if self.music_playing:
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)

    def _update_sfx_volumes(self):
        """Update sound effect volumes"""
        for sound in self.sound_effects.values():
            if sound:
                sound.set_volume(self.sfx_volume * self.master_volume)

    def get_master_volume(self):
        """Get master volume"""
        return self.master_volume

    def get_sfx_volume(self):
        """Get sound effects volume"""
        return self.sfx_volume

    def get_music_volume(self):
        """Get music volume"""
        return self.music_volume

    def is_music_playing(self):
        """Check if music is currently playing"""
        return self.music_playing

    def fade_out_music(self, time_ms=1000):
        """Fade out background music"""
        pygame.mixer.music.fadeout(time_ms)
        self.music_playing = False

class AudioManager:
    """High-level audio manager for the game"""

    def __init__(self, assets_dir="assets"):
        """Initialize audio manager"""
        self.audio_system = AudioSystem(assets_dir)
        self.level_music = {}
        self._load_level_music()

    def _load_level_music(self):
        """Load music for different levels"""
        # This could be expanded to have different music for different levels
        self.level_music = {
            "menu": "background_music.mp3",
            "game": "background_music.mp3",
            "boss": "background_music.mp3"  # Could have different boss music
        }

    def start_menu_music(self):
        """Start menu background music"""
        self.audio_system.play_background_music(self.level_music.get("menu"))

    def start_game_music(self):
        """Start game background music"""
        self.audio_system.play_background_music(self.level_music.get("game"))

    def start_boss_music(self):
        """Start boss fight music"""
        self.audio_system.play_background_music(self.level_music.get("boss"))

    def stop_music(self):
        """Stop all music"""
        self.audio_system.stop_background_music()

    def toggle_music(self):
        """Toggle music on/off"""
        if self.audio_system.is_music_playing():
            self.audio_system.stop_background_music()
        else:
            self.start_game_music()

    def pause_music(self):
        """Pause music"""
        self.audio_system.pause_background_music()

    def unpause_music(self):
        """Unpause music"""
        self.audio_system.unpause_background_music()

    def play_jump(self):
        """Play jump sound"""
        self.audio_system.play_jump_sound()

    def play_coin(self):
        """Play coin sound"""
        self.audio_system.play_coin_sound()

    def play_powerup(self):
        """Play powerup sound"""
        self.audio_system.play_powerup_sound()

    def play_enemy_defeat(self):
        """Play enemy defeat sound"""
        self.audio_system.play_enemy_die_sound()

    def play_player_death(self):
        """Play player death sound"""
        self.audio_system.play_player_die_sound()

    def play_level_complete(self):
        """Play level complete sound"""
        self.audio_system.play_level_complete_sound()

    def play_game_over(self):
        """Play game over sound"""
        self.audio_system.play_game_over_sound()

    def set_master_volume(self, volume):
        """Set master volume"""
        self.audio_system.set_master_volume(volume)

    def set_sfx_volume(self, volume):
        """Set SFX volume"""
        self.audio_system.set_sfx_volume(volume)

    def set_music_volume(self, volume):
        """Set music volume"""
        self.audio_system.set_music_volume(volume)

# Global audio manager instance
_audio_manager = None

def get_audio_manager(assets_dir="assets"):
    """Get the global audio manager instance"""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager(assets_dir)
    return _audio_manager