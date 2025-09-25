class AudioSystem:
    def __init__(self, base=None):
        self.base = base
        self.sounds = {}
        self.music = None

        # attempt to load default BGM if present (non-fatal)
        if self.base:
            try:
                # common path for optimized project assets
                self.load_bgm('assets/audio/bgm_loop.ogg')
            except Exception:
                pass

    def load_sfx(self, path, name=None):
        key = name or path
        if not self.base:
            # register placeholder
            self.sounds[key] = None
            return None
        try:
            s = self.base.loader.loadSfx(path)
            self.sounds[key] = s
            return s
        except Exception:
            self.sounds[key] = None
            return None

    def play_sfx(self, name_or_path):
        # try by registered name first
        s = self.sounds.get(name_or_path)
        if s:
            try:
                s.play()
                return
            except Exception:
                pass

        # fallback: if base available, try to load on-the-fly
        if self.base:
            try:
                s2 = self.base.loader.loadSfx(name_or_path)
                if s2:
                    s2.play()
                    return
            except Exception:
                pass

        # final fallback: console
        print('SFX play (fallback):', name_or_path)

    def load_bgm(self, path):
        if not self.base:
            return None
        try:
            self.music = self.base.loader.loadMusic(path)
            return self.music
        except Exception:
            self.music = None
            return None

    def play_bgm(self, loop=True):
        if self.music:
            try:
                self.music.setLoop(loop)
                self.music.play()
            except Exception:
                print('BGM play failed')
        else:
            print('No BGM loaded')
    
    def cleanup(self):
        """Enhanced cleanup to prevent AL lib errors"""
        try:
            print("Starting audio cleanup...")
            
            # Stop and clear music first
            if self.music:
                try:
                    self.music.stop()
                    print("Background music stopped")
                except Exception as e:
                    print(f"Music stop warning: {e}")
                finally:
                    self.music = None
            
            # Stop all sound effects
            stopped_count = 0
            for name, sound in self.sounds.items():
                if sound:
                    try:
                        sound.stop()
                        stopped_count += 1
                    except Exception as e:
                        print(f"Sound stop warning for {name}: {e}")
            
            print(f"Stopped {stopped_count} sound effects")
            self.sounds.clear()
            
            # Additional OpenAL cleanup
            try:
                if self.base and hasattr(self.base, 'audio3d'):
                    # Try to detach all audio from Audio3D manager
                    audio3d = self.base.audio3d
                    if audio3d:
                        audio3d.detachListener()
                        print("Audio3D listener detached")
            except Exception as e:
                print(f"Audio3D cleanup warning: {e}")
            
            # Force garbage collection to release audio resources
            import gc
            gc.collect()
            
            print("Audio system cleanup completed")
            
        except Exception as e:
            print(f"Audio cleanup error: {e}")
        finally:
            # Ensure everything is cleared even if errors occurred
            self.music = None
            self.sounds = {}
