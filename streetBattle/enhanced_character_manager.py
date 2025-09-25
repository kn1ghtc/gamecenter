#!/usr/bin/env python3
"""
Enhanced Character Manager with Optimized Single-Tier Resource Support
Supports single high-quality tier per character: Sketchfab (Complete Community Resources)
Optimized for performance with 7.88GB premium assets and consolidated configurations.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from direct.actor.Actor import Actor
from panda3d.core import Vec3, Filename, getModelPath, VirtualFileSystem
from pathlib import Path
import glob

# Local audit helpers
try:
    from gamecenter.streetBattle.assets_audit import (
        is_bam_likely_valid, is_egg_valid, is_glb_valid, is_gltf_valid, is_egg_pz_valid
    )
except Exception:
    # Fallback stubs
    def is_bam_likely_valid(p): return os.path.getsize(p) > 256 if os.path.exists(p) else False
    def is_egg_valid(p): return os.path.getsize(p) > 256 if os.path.exists(p) else False
    def is_glb_valid(p): return os.path.getsize(p) > 1024 if os.path.exists(p) else False
    def is_gltf_valid(p): return os.path.getsize(p) > 512 if os.path.exists(p) else False
    def is_egg_pz_valid(p): return os.path.getsize(p) > 256 if os.path.exists(p) else False

class EnhancedCharacterManager:
    """Enhanced character manager with premium multi-tier resource support"""
    
    def __init__(self, base_app):
        self.base_app = base_app
        self.characters_data = {}
        self.character_models = {}
        self.resource_config = {}
        self.comprehensive_characters = {}
        
        # Setup paths
        script_root = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = Path(script_root) / "assets"
        self.characters_dir = self.assets_dir / "characters"
        
        # Initialize Panda3D search paths
        self._setup_panda3d_paths(script_root)
        
        # Load all configurations and databases
        self._load_all_databases()
        
        print(f"Enhanced Character Manager initialized:")
        print(f"- {len(self.comprehensive_characters)} total KOF characters")
        print(f"- Optimized single-tier resources (Sketchfab only)")
        print(f"- Resource tier: Sketchfab (7.88GB premium assets with animations)")
    
    def _setup_panda3d_paths(self, script_root: str):
        """Setup Panda3D search paths for our assets"""
        try:
            for p in [
                os.path.join(script_root, 'assets', 'characters'),
                os.path.join(script_root, 'assets', 'models'),
                os.path.join(script_root, 'assets'),
                script_root,
            ]:
                getModelPath().prependDirectory(Filename.fromOsSpecific(p))
            
            # Mount VFS for legacy texture paths
            try:
                vfs = VirtualFileSystem.getGlobalPtr()
                maps_dir = os.path.join(script_root, 'assets', 'characters', 'maps')
                
                # Create maps directory if it doesn't exist
                if not os.path.exists(maps_dir):
                    os.makedirs(maps_dir, exist_ok=True)
                    # Create a basic texture placeholder
                    placeholder_path = os.path.join(maps_dir, 'default_texture.jpg')
                    if not os.path.exists(placeholder_path):
                        with open(placeholder_path, 'wb') as f:
                            # Create minimal 1x1 JPEG header
                            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\x00\xff\xd9')
                
                local_maps = Filename.fromOsSpecific(maps_dir)
                panda_abs_maps = Filename('/c/Panda3D-1.10.15-x64/models/maps')
                vfs.mount(local_maps, panda_abs_maps, 0)
                print(f"[EnhancedCharacterManager] VFS mounted: {maps_dir} -> {panda_abs_maps}")
            except Exception as e:
                print(f"Warning: Failed to mount VFS for texture paths: {e}")
                # Try alternative approach without VFS
                try:
                    maps_dir = os.path.join(script_root, 'assets', 'characters', 'maps')
                    if not os.path.exists(maps_dir):
                        os.makedirs(maps_dir, exist_ok=True)
                except Exception:
                    pass
        except Exception as e:
            print(f"Warning: Failed to setup Panda3D paths: {e}")
    
    def _load_all_databases(self):
        """Load all character databases and resource configurations, supporting multi-path search for robustness."""
        # 多路径查找顺序：项目根目录、assets、assets/characters
        search_paths = [
            Path(__file__).parent.parent.parent,  # d:\pyproject
            self.assets_dir,
            self.assets_dir / "characters"
        ]

        def find_file(filename):
            for p in search_paths:
                candidate = p / filename
                if candidate.exists():
                    return candidate
            return None

        # Load comprehensive character database (84 characters)
        comprehensive_file = find_file("comprehensive_kof_characters.json")
        if comprehensive_file:
            try:
                with open(comprehensive_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.comprehensive_characters = {char['id']: char for char in data['characters']}
                print(f"Loaded comprehensive database: {len(self.comprehensive_characters)} characters from {comprehensive_file}")
            except Exception as e:
                print(f"Failed to load comprehensive database: {e}")
        else:
            print("[ERROR] comprehensive_kof_characters.json not found in any known path!")
            # Create empty comprehensive characters database as fallback
            self.comprehensive_characters = {}

        # Load enhanced profiles
        profiles_file = find_file("character_profiles.json")
        if profiles_file:
            try:
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                    # Merge profiles into comprehensive characters
                    for char_id, char_data in self.comprehensive_characters.items():
                        if char_id in profiles:
                            profile = profiles[char_id]
                            char_data.update({
                                'color_scheme': profile.get('color_scheme', {}),
                                'fighting_style': profile.get('fighting_style', char_data.get('fighting_style', 'Mixed Martial Arts')),
                                'difficulty': profile.get('difficulty', 3),
                                'enhanced': True
                            })
                print(f"Merged enhanced profiles from {profiles_file}")
            except Exception as e:
                print(f"Failed to load enhanced profiles: {e}")
        else:
            print("[INFO] character_profiles.json not found, skipping profile merge.")

        # Load premium resource configuration
        config_file = find_file("resource_configuration.json")
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.resource_config = json.load(f)
                print(f"Loaded premium resource configuration from {config_file}")
            except Exception as e:
                print(f"Failed to load resource config: {e}")
        else:
            print("[WARN] resource_configuration.json not found in any known path.")
        
        # Load enhanced profiles
        profiles_file = self.assets_dir / "character_profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                    # Merge profiles into comprehensive characters
                    for char_id, char_data in self.comprehensive_characters.items():
                        if char_id in profiles:
                            profile = profiles[char_id]
                            char_data.update({
                                'color_scheme': profile.get('color_scheme', {}),
                                'fighting_style': profile.get('fighting_style', char_data.get('fighting_style', 'Mixed Martial Arts')),
                                'difficulty': profile.get('difficulty', 3),
                                'enhanced': True
                            })
                print(f"Merged enhanced profiles")
            except Exception as e:
                print(f"Failed to load enhanced profiles: {e}")
        
        # premium resource configuration 已由 find_file 逻辑处理，无需 project_root 相关残留
    
    def get_all_character_names(self) -> List[str]:
        """Get all available character names from comprehensive database"""
        all_names = set()
        
        # Add comprehensive character names
        for char_id, char_data in self.comprehensive_characters.items():
            all_names.add(char_data['name'])
        
        return sorted(list(all_names))
    
    def get_character_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get character data by name from comprehensive database"""
        # Search comprehensive database
        for char_id, char_data in self.comprehensive_characters.items():
            if char_data['name'].lower() == name.lower():
                return char_data
        
        return None
    
    def get_character_by_id(self, char_id: str) -> Optional[Dict[str, Any]]:
        """Get character data by ID"""
        return self.comprehensive_characters.get(char_id)
    
    def _get_premium_resource_path(self, character_name: str, resource_tier: str = "auto") -> Tuple[Optional[str], Optional[Dict[str, str]]]:
        """Get premium resource path and animations based on tier selection"""
        char_data = self.get_character_by_name(character_name)
        if not char_data:
            return None, None
        
        char_id = char_data.get('id', character_name.lower().replace(' ', '_'))
        
        # Determine resource tier priority
        if resource_tier == "auto":
            tier_priority = self.resource_config.get('resource_priority', [
                {'name': 'sketchfab', 'priority': 1}
            ])
            tiers_to_try = [tier['name'] for tier in sorted(tier_priority, key=lambda x: x['priority'])]
        else:
            tiers_to_try = [resource_tier]
        
        # Try each tier in order
        for tier in tiers_to_try:
            tier_dir = self.characters_dir / char_id / tier
            if not tier_dir.exists():
                continue
            
            # Look for model files based on tier format preferences
            model_files = []
            if tier == "sketchfab":
                # Sketchfab: Single tier system - Try GLTF/GLB first (primary), then BAM fallback
                model_files = [
                    tier_dir / f"{char_id}.gltf",
                    tier_dir / f"{char_id}.glb", 
                    tier_dir / f"{char_id}.bam",
                    tier_dir / f"{char_id}.obj"
                    # Note: Optimized single-tier system uses only highest quality Sketchfab resources
                ]
            
            # Find first existing valid model
            for model_file in model_files:
                if model_file.exists() and self._is_model_file_valid(model_file):
                    # Get animations for this tier
                    animations = self._discover_tier_animations(tier_dir, char_id)
                    
                    print(f"[EnhancedCharacterManager] Using {tier} tier for {character_name}: {model_file.name}")
                    return str(model_file), animations
        
        return None, None
    
    def _is_model_file_valid(self, model_file: Path) -> bool:
        """Check if model file is valid based on format"""
        try:
            ext = model_file.suffix.lower()
            if ext == '.gltf':
                return is_gltf_valid(str(model_file))
            elif ext == '.glb':
                return is_glb_valid(str(model_file))
            elif ext == '.fbx':
                # FBX files in this project are placeholder files - reject them
                size = model_file.stat().st_size
                if size > 80 * 1024 * 1024:  # Files larger than 80MB are likely placeholders
                    # Check if file contains only null bytes (placeholder indicator)
                    with open(model_file, 'rb') as f:
                        sample = f.read(1024)  # Read first 1KB
                        if sample == b'\x00' * len(sample):
                            print(f"[EnhancedCharacterManager] Detected placeholder FBX: {model_file}")
                            return False
                return size > 1024 and size < 80 * 1024 * 1024  # Reasonable size check
            elif ext in ['.obj', '.dae', '.max', '.3ds']:
                return model_file.stat().st_size > 1024  # Basic size check
            elif ext == '.bam':
                return model_file.stat().st_size > 1024  # BAM files are valid
            else:
                return False
        except Exception:
            return False
    
    def _is_real_3d_resource(self, model_file: Path) -> bool:
        """Check if this is a real 3D resource (not a placeholder)"""
        try:
            if not model_file.exists():
                return False
                
            size = model_file.stat().st_size
            ext = model_file.suffix.lower()
            
            # Minimum size requirements for real resources
            min_sizes = {
                '.gltf': 2048,     # GLTF files with real geometry
                '.glb': 10240,     # GLB binary files
                '.obj': 1024,      # OBJ files
                '.fbx': 5120       # FBX files (but we generally avoid these)
            }
            
            min_size = min_sizes.get(ext, 1024)
            if size < min_size:
                return False
            
            # Additional content validation for GLTF
            if ext == '.gltf':
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        content = f.read(2048)  # Read first 2KB
                        
                    # Check for real GLTF content indicators
                    real_indicators = [
                        '"buffers":', '"meshes":', '"nodes":', '"scenes":',
                        '"accessors":', '"materials":', '"textures":'
                    ]
                    
                    # Must have at least 3 real GLTF components
                    indicator_count = sum(1 for indicator in real_indicators if indicator in content)
                    if indicator_count < 3:
                        return False
                        
                    # Check for placeholder indicators (reject if found)
                    placeholder_hints = [
                        'placeholder', 'dummy', 'temp', 'test',
                        '"byteLength": 0', '"count": 0'
                    ]
                    
                    if any(hint in content.lower() for hint in placeholder_hints):
                        return False
                        
                    return True
                except Exception:
                    return False
            
            # For OBJ files, check for real geometry
            elif ext == '.obj':
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        content = f.read(1024)  # Read first 1KB
                    
                    # Check for vertex data
                    vertex_count = content.count('v ')
                    face_count = content.count('f ')
                    
                    return vertex_count > 10 and face_count > 5  # Reasonable geometry
                except Exception:
                    return False
            
            # For other formats, rely on size check
            return True
            
        except Exception:
            return False
    
    def _discover_tier_animations(self, tier_dir: Path, char_id: str) -> Dict[str, str]:
        """Discover animations in a specific resource tier"""
        animations = {}
        
        anim_dir = tier_dir / "animations"
        if not anim_dir.exists():
            return animations
        
        # Animation file patterns for different formats
        patterns = ["*.gltf", "*.glb", "*.dae", "*.fbx", "*.obj", "*.bam", "*.egg", "*.egg.pz"]
        
        files = []
        for pattern in patterns:
            files.extend(anim_dir.glob(pattern))
        
        # Map files to standard animation keys
        for file_path in files:
            name = file_path.stem.lower()
            
            # Standard animation mapping
            if any(word in name for word in ['idle', 'stand', 'standby', 'ready', 'rest']):
                animations['idle'] = str(file_path)
            elif any(word in name for word in ['walk', 'run', 'move']):
                animations['walk'] = str(file_path)
            elif any(word in name for word in ['light', 'jab', 'lp', 'lk']):
                animations['light'] = str(file_path)
            elif any(word in name for word in ['heavy', 'hp', 'hk', 'strong']):
                animations['heavy'] = str(file_path)
            elif any(word in name for word in ['attack', 'punch', 'kick', 'strike']):
                animations['attack'] = str(file_path)
            elif any(word in name for word in ['hurt', 'hit', 'damage']):
                animations['hurt'] = str(file_path)
            elif 'jump' in name or 'air' in name:
                animations['jump'] = str(file_path)
            elif any(word in name for word in ['victory', 'win', 'taunt']):
                animations['victory'] = str(file_path)
            elif any(word in name for word in ['defeat', 'lose', 'ko', 'death']):
                animations['defeat'] = str(file_path)
            elif any(word in name for word in ['block', 'guard']):
                animations['block'] = str(file_path)
            elif any(word in name for word in ['crouch', 'duck']):
                animations['crouch'] = str(file_path)
        
        # Fill missing animations with generic attack if available
        if 'attack' in animations:
            for key in ['light', 'heavy']:
                if key not in animations:
                    animations[key] = animations['attack']
        
        return animations
    
    def create_enhanced_character_model(self, character_name: str, pos: Vec3 = Vec3(0, 0, 0), resource_tier: str = "auto") -> Optional[Actor]:
        """Create enhanced character model using ONLY real 3D resources - 84 character support, no 22-character fallbacks"""
        # Prioritize real resources from resource manager system
        from gamecenter.streetBattle.resource_manager import UnifiedResourceManager
        
        try:
            resource_manager = UnifiedResourceManager()
            
            # Skip auto-replacement to avoid path issues, manually check for resources
            print(f"[EnhancedCharacterManager] Checking for real resources for {character_name}...")
            
            # Get real 3D resource path for this character
            char_data = self.get_character_by_name(character_name)
            if not char_data:
                print(f"[EnhancedCharacterManager] Character {character_name} not found in comprehensive database")
                return None
            
            char_id = char_data.get('id', character_name.lower().replace(' ', '_'))
            
            # Check for real 3D resources (prioritize sketchfab and models_resource sources)
            real_resource_paths = []
            
            # Priority 1: Sketchfab high-quality models
            sketchfab_dir = self.characters_dir / char_id / "sketchfab"
            if sketchfab_dir.exists():
                for model_file in sketchfab_dir.glob("*.gltf"):
                    if self._is_real_3d_resource(model_file):
                        real_resource_paths.append((str(model_file), "sketchfab"))
                for model_file in sketchfab_dir.glob("*.glb"):
                    if self._is_real_3d_resource(model_file):
                        real_resource_paths.append((str(model_file), "sketchfab"))
            
            # Priority 2: Models_resource basic quality models
            models_resource_dir = self.characters_dir / char_id / "models_resource"
            if models_resource_dir.exists():
                for model_file in models_resource_dir.glob("*.gltf"):
                    if self._is_real_3d_resource(model_file):
                        real_resource_paths.append((str(model_file), "models_resource"))
                for model_file in models_resource_dir.glob("*.obj"):
                    if self._is_real_3d_resource(model_file):
                        real_resource_paths.append((str(model_file), "models_resource"))
            
            # Try each real resource
            for model_path, source in real_resource_paths:
                animations = self._discover_tier_animations(Path(model_path).parent, char_id)
                actor = self._create_actor_from_path(model_path, animations, character_name, pos)
                if actor:
                    print(f"[EnhancedCharacterManager] ✅ Using real 3D resource from {source}: {character_name}")
                    return actor
            
            # If no real resources found, attempt to download them
            print(f"[EnhancedCharacterManager] No real resources found for {character_name}, attempting download...")
            success = resource_manager.download_real_resources([character_name])
            if success:
                # Retry loading after download
                return self.create_enhanced_character_model(character_name, pos, resource_tier)
            
            print(f"[EnhancedCharacterManager] ❌ Could not obtain real 3D resources for {character_name}")
            return None
            
        except Exception as e:
            print(f"[EnhancedCharacterManager] Error loading real resources: {e}")
            return None
    
    def _create_actor_from_path(self, model_path: str, animations: Dict[str, str], character_name: str, pos: Vec3) -> Optional[Actor]:
        """Create Actor from specific model path and animations"""
        try:
            # Normalize paths for Panda3D (convert Windows paths to relative paths)
            def norm_path(p):
                # Convert absolute Windows path to relative path from script root
                if os.path.isabs(p):
                    script_root = os.path.dirname(os.path.abspath(__file__))
                    try:
                        relative_path = os.path.relpath(p, script_root)
                        return relative_path.replace('\\', '/')
                    except ValueError:
                        # If relpath fails, try to make it relative to assets
                        if 'assets' in p:
                            assets_index = p.find('assets')
                            relative_path = p[assets_index:]
                            return relative_path.replace('\\', '/')
                        return p.replace('\\', '/')
                return p.replace('\\', '/')
            
            model_path = norm_path(model_path)
            norm_animations = {k: norm_path(v) for k, v in animations.items()} if animations else {}
            
            # Create Actor
            if norm_animations:
                actor = Actor(model_path, norm_animations)
            else:
                actor = Actor(model_path)
            
            # Check if Actor is valid (has LOD info and is not empty)
            if actor and not actor.isEmpty():
                try:
                    # Test if Actor has valid LOD data (avoids IndexError later)
                    actor.getActorInfo()
                    
                    # Apply character customizations
                    char_data = self.get_character_by_name(character_name)
                    if char_data:
                        self._apply_character_enhancements(actor, char_data)
                    
                    # Position and cache
                    actor.setPos(pos)
                    self.character_models[character_name] = actor
                    
                    print(f"[EnhancedCharacterManager] Successfully loaded {character_name} from {os.path.basename(model_path)}")
                    if norm_animations:
                        print(f"  Animations: {list(norm_animations.keys())}")
                    
                    return actor
                except Exception as e:
                    print(f"[EnhancedCharacterManager] Actor LOD validation failed for {model_path}: {e}")
                    # Fall through to return None
            else:
                print(f"[EnhancedCharacterManager] Actor is empty for {model_path}")
                
            return None
                
        except Exception as e:
            print(f"[EnhancedCharacterManager] Error creating actor: {e}")
            return None
    
    def _create_legacy_character_model(self, character_name: str, pos: Vec3) -> Optional[Actor]:
        """Fallback to legacy character model creation"""
        try:
            char_data = self.get_character_by_name(character_name)
            if not char_data:
                print(f"Character {character_name} not found in any database")
                return None
            
            char_id = character_name.lower().replace(" ", "_")
            
            # Try legacy character-specific models
            candidate_models = [
                f"assets/characters/{char_id}/{char_id}.egg.pz",
                f"assets/characters/{char_id}/{char_id}.egg",
                f"assets/characters/{char_id}/{char_id}.bam.pz",
                f"assets/characters/{char_id}/{char_id}.bam",
                f"assets/characters/{char_id}/{char_id}.gltf",
                f"assets/characters/{char_id}/{char_id}.glb",
            ]
            
            for model_path in candidate_models:
                if os.path.exists(model_path) and self._validate_legacy_model(model_path):
                    try:
                        animations = self._discover_legacy_animations(char_id)
                        norm_path = model_path.replace('\\\\', '/')
                        
                        if animations:
                            actor = Actor(norm_path, animations)
                        else:
                            actor = Actor(norm_path)
                        
                        if actor and not actor.isEmpty():
                            self._apply_character_enhancements(actor, char_data)
                            actor.setPos(pos)
                            self.character_models[character_name] = actor
                            print(f"[EnhancedCharacterManager] Loaded legacy model for {character_name}: {os.path.basename(model_path)}")
                            return actor
                    except Exception as e:
                        print(f"Failed to load legacy model {model_path}: {e}")
                        continue
            
            # Final fallback to Arena FPS npc_1
            return self._create_arena_fps_fallback(character_name, pos, char_data)
            
        except Exception as e:
            print(f"Error in legacy character creation: {e}")
            return None
    
    def _validate_legacy_model(self, model_path: str) -> bool:
        """Validate legacy model file"""
        try:
            ext = os.path.splitext(model_path)[1].lower()
            if ext == '.bam':
                return is_bam_likely_valid(model_path)
            elif ext == '.gltf':
                return is_gltf_valid(model_path)
            elif ext == '.glb':
                return is_glb_valid(model_path)
            elif ext in ['.egg', '.egg.pz']:
                return is_egg_valid(model_path)
            return os.path.getsize(model_path) > 512
        except Exception:
            return False
    
    def _discover_legacy_animations(self, char_id: str) -> Dict[str, str]:
        """Discover legacy animations"""
        animations = {}
        anim_dir = f"assets/characters/{char_id}/animations"
        
        if not os.path.exists(anim_dir):
            return animations
        
        patterns = [
            os.path.join(anim_dir, '*.egg.pz'),
            os.path.join(anim_dir, '*.egg'),
            os.path.join(anim_dir, '*.bam'),
        ]
        
        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern))
        
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0].lower()
            norm_path = f.replace('\\\\', '/')
            
            if 'idle' in name or 'stand' in name:
                animations['idle'] = norm_path
            elif 'walk' in name or 'run' in name:
                animations['walk'] = norm_path
            elif 'light' in name or 'jab' in name:
                animations['light'] = norm_path
            elif 'heavy' in name or 'strong' in name:
                animations['heavy'] = norm_path
            elif 'attack' in name:
                animations['attack'] = norm_path
        
        # Fill missing with generic attack
        if 'attack' in animations:
            animations.setdefault('light', animations['attack'])
            animations.setdefault('heavy', animations['attack'])
        
        return animations
    
    def _create_arena_fps_fallback(self, character_name: str, pos: Vec3, char_data: Dict) -> Optional[Actor]:
        """Create Arena FPS fallback model"""
        try:
            # Use relative path for Panda3D (Panda3D has its own model path system)
            fallback_model = 'assets/models/npc_1.bam'
            
            print(f"[EnhancedCharacterManager] Trying Arena FPS fallback: {fallback_model}")
            
            # Check if file exists in filesystem (for debugging)
            abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), fallback_model)
            print(f"[EnhancedCharacterManager] File exists: {os.path.exists(abs_path)}")
            
            # Try to include walk animation
            walk_anim = 'assets/models/npc_1_ArmatureAction.bam'
            animations = {}
            walk_abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), walk_anim) 
            if os.path.exists(walk_abs_path):
                animations['walk'] = walk_anim
                print(f"[EnhancedCharacterManager] Found walk animation: {walk_anim}")
            
            try:
                if animations:
                    actor = Actor(fallback_model, animations)
                else:
                    actor = Actor(fallback_model)
                
                if actor and not actor.isEmpty():
                    # Test LOD validation like before
                    try:
                        actor.getActorInfo()
                        self._apply_character_enhancements(actor, char_data)
                        actor.setPos(pos)
                        print(f"[EnhancedCharacterManager] Successfully using Arena FPS fallback for {character_name}")
                        return actor
                    except Exception as lod_e:
                        print(f"[EnhancedCharacterManager] Arena FPS Actor LOD validation failed: {lod_e}")
                        return None
                else:
                    print(f"[EnhancedCharacterManager] Arena FPS Actor is empty")
                    
            except Exception as actor_e:
                print(f"[EnhancedCharacterManager] Failed to create Arena FPS Actor: {actor_e}")
            
        except Exception as e:
            print(f"[EnhancedCharacterManager] Arena FPS fallback exception: {e}")
        
        print(f"[EnhancedCharacterManager] Arena FPS fallback failed for {character_name}")
        return None
    
    def _apply_character_enhancements(self, actor: Actor, char_data: Dict[str, Any]):
        """Apply character-specific visual and gameplay enhancements"""
        try:
            # Apply enhanced color scheme if available
            color_scheme = char_data.get('color_scheme', {})
            if color_scheme:
                r = color_scheme.get('r', 1.0)
                g = color_scheme.get('g', 1.0) 
                b = color_scheme.get('b', 1.0)
                actor.setColorScale(r, g, b, 1.0)
                return
            
            # Fallback to legacy color variations
            colors = char_data.get('color_variations', [{}])
            if colors:
                primary_color = colors[0].get('primary', '#FFFFFF')
                try:
                    r = int(primary_color[1:3], 16) / 255.0
                    g = int(primary_color[3:5], 16) / 255.0
                    b = int(primary_color[5:7], 16) / 255.0
                    actor.setColorScale(r, g, b, 1.0)
                except Exception:
                    pass
            
            # Apply scaling based on character stats
            stats = char_data.get('stats', {})
            if stats:
                speed = stats.get('speed', 5)
                scale_factor = 0.8 + (speed / 10.0 * 0.4)
                actor.setScale(scale_factor)
            
        except Exception as e:
            print(f"Failed to apply character enhancements: {e}")
    
    def create_enhanced_player(self, character_name: str, pos: Vec3 = Vec3(0, 0, 0), resource_tier: str = "auto"):
        """Create enhanced Player instance using premium resources"""
        from gamecenter.streetBattle.player import Player
        
        char_data = self.get_character_by_name(character_name)
        if not char_data:
            # Fallback to basic player
            return Player(self.base_app.render, self.base_app.loader, 
                         name=character_name, pos=pos)
        
        # Create enhanced model
        actor_model = self.create_enhanced_character_model(character_name, pos, resource_tier)
        
        if actor_model:
            # Create player with enhanced model - pass Actor directly
            try:
                # First create empty player
                player = Player(self.base_app.render, self.base_app.loader, 
                               name=character_name, pos=pos)
                
                # Remove the placeholder node
                if hasattr(player, 'node') and player.node:
                    player.node.removeNode()
                
                # Set the Actor as the player's node and model
                player.node = actor_model
                player.model = actor_model
                actor_model.reparentTo(self.base_app.render)
                actor_model.setPos(pos)
                
                print(f"[EnhancedCharacterManager] Successfully attached Actor to player: {character_name}")
            except Exception as e:
                print(f"[EnhancedCharacterManager] Error attaching Actor to player: {e}")
                # Fallback to basic player
                return Player(self.base_app.render, self.base_app.loader, 
                             name=character_name, pos=pos)
            
            # Set character-specific attributes
            player.character_name = character_name
            player.character_id = char_data.get('id', character_name.lower().replace(' ', '_'))
            player.fighting_style = char_data.get('fighting_style', 'Mixed Martial Arts')
            
            # Apply enhanced stats if available
            stats = char_data.get('stats', {})
            if stats:
                player.max_health = stats.get('health', 100)
                player.health = player.max_health
                player.speed = stats.get('speed', 5)
                player.power = stats.get('power', 5)
            
            print(f"[EnhancedCharacterManager] Created enhanced player: {character_name}")
            if hasattr(actor_model, 'getAnimNames'):
                anims = actor_model.getAnimNames()
                if anims:
                    print(f"  Available animations: {list(anims)}")
            
            return player
        else:
            # Fallback to basic player
            print(f"[EnhancedCharacterManager] Falling back to basic player for {character_name}")
            return Player(self.base_app.render, self.base_app.loader, 
                         name=character_name, pos=pos)
    
    def get_random_character(self) -> str:
        """Get random character name from comprehensive database"""
        import random
        if self.comprehensive_characters:
            char_id = random.choice(list(self.comprehensive_characters.keys()))
            return self.comprehensive_characters[char_id]['name']
        elif self.characters_data:
            return random.choice(list(self.characters_data.keys()))
        else:
            return "Kyo Kusanagi"  # Ultimate fallback
    
    def get_characters_by_team(self) -> Dict[str, List[str]]:
        """Get characters organized by teams from comprehensive database"""
        if not self.comprehensive_characters:
            return {}
        
        # Use team information from comprehensive database
        teams = {}
        for char_id, char_data in self.comprehensive_characters.items():
            team = char_data.get('team', 'Miscellaneous')
            if team not in teams:
                teams[team] = []
            teams[team].append(char_data['name'])
        
        return teams
    
    def get_resource_tier_info(self, character_name: str) -> Dict[str, Any]:
        """Get information about available resource tiers for a character"""
        char_data = self.get_character_by_name(character_name)
        if not char_data:
            return {}
        
        char_id = char_data.get('id', character_name.lower().replace(' ', '_'))
        tier_info = {}
        
        for tier in ['sketchfab']:
            tier_dir = self.characters_dir / char_id / tier
            if tier_dir.exists():
                # Check for resource info file
                info_file = tier_dir / "resource_info.json"
                if info_file.exists():
                    try:
                        with open(info_file, 'r') as f:
                            tier_info[tier] = json.load(f)
                    except Exception:
                        tier_info[tier] = {"available": True, "status": "unknown"}
                else:
                    tier_info[tier] = {"available": True, "status": "detected"}
        
        return tier_info
    
    def print_character_database_summary(self):
        """Print summary of loaded character databases"""
        print("\\n=== CHARACTER DATABASE SUMMARY ===")
        print(f"Comprehensive KOF Characters: {len(self.comprehensive_characters)}")
        print(f"Legacy KOF97 Characters: {len(self.characters_data)}")
        
        if self.comprehensive_characters:
            # Group by series/debut
            debuts = {}
            for char_data in self.comprehensive_characters.values():
                debut = char_data.get('debut', 'Unknown')
                debuts[debut] = debuts.get(debut, 0) + 1
            
            print("\\nCharacters by debut game:")
            for debut, count in sorted(debuts.items()):
                print(f"  {debut}: {count} characters")
        
        if self.resource_config:
            print(f"\\nPremium resource tiers available: {len(self.resource_config.get('resource_priority', []))}")
            for tier in self.resource_config.get('resource_priority', []):
                print(f"  {tier['priority']}. {tier['name']} - {tier['description']}")


def main():
    """Test the enhanced character manager"""
    import sys
    import os
    
    # Add current directory to path for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    
    class MockBaseApp:
        def __init__(self):
            self.render = None
            self.loader = None
    
    print("Testing Enhanced Character Manager...")
    
    manager = EnhancedCharacterManager(MockBaseApp())
    manager.print_character_database_summary()
    
    # Test character retrieval
    test_chars = ["Kyo Kusanagi", "Iori Yagami", "Terry Bogard", "Mai Shiranui"]
    
    print("\\n=== CHARACTER TESTS ===")
    for char_name in test_chars:
        char_data = manager.get_character_by_name(char_name)
        if char_data:
            print(f"✓ {char_name}: {char_data.get('fighting_style', 'Unknown style')}")
            tier_info = manager.get_resource_tier_info(char_name)
            if tier_info:
                available_tiers = list(tier_info.keys())
                print(f"  Available tiers: {available_tiers}")
        else:
            print(f"✗ {char_name}: Not found")
    
    print(f"\\nTotal available characters: {len(manager.get_all_character_names())}")
    print("Enhanced Character Manager test completed!")


if __name__ == "__main__":
    main()