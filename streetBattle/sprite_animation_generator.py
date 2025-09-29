#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprite Animation Generator for Street Battle Game
Based on high-quality character portraits, generates 7 types of sprite animations
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import numpy as np
import math

class SpriteAnimationGenerator:
    """Generate sprite animations for 2.5D fighting game"""
    
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = Path(assets_dir)
        self.sprites_dir = self.assets_dir / "sprites"
        self.portraits_dir = self.assets_dir / "images" / "portraits"
        self.frame_size = (128, 128)
        
        # Animation types and their frame counts
        self.animation_types = {
            "idle": {"frames": 4, "fps": 8, "loop": True},
            "walk": {"frames": 6, "fps": 12, "loop": True},
            "attack": {"frames": 5, "fps": 15, "loop": False},
            "hit": {"frames": 3, "fps": 10, "loop": False},
            "jump": {"frames": 4, "fps": 12, "loop": False},
            "victory": {"frames": 6, "fps": 8, "loop": True},
            "block": {"frames": 2, "fps": 6, "loop": True}
        }
        
        # Load character list
        self.characters = self._load_character_list()
        
        print(f"Sprite Animation Generator initialized")
        print(f"- Target directory: {self.sprites_dir}")
        print(f"- Character count: {len(self.characters)}")
        print(f"- Animation types: {list(self.animation_types.keys())}")
    
    def _load_character_list(self) -> List[str]:
        """Load character list from unified character file"""
        char_file = self.assets_dir / "unified_character_list.json"
        if char_file.exists():
            try:
                with open(char_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle different JSON formats
                    if 'characters' in data and isinstance(data['characters'], list):
                        return [char['id'] for char in data['characters']]
                    elif isinstance(data, dict):
                        # Direct character dict format
                        return list(data.keys())
                    elif isinstance(data, list):
                        return [char['id'] for char in data if isinstance(char, dict) and 'id' in char]
            except Exception as e:
                print(f"Failed to load character list: {e}")
        
        # Alternative: check character_portraits_index.json
        portraits_index = self.assets_dir / "character_portraits_index.json"
        if portraits_index.exists():
            try:
                with open(portraits_index, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return list(data.keys())
            except Exception as e:
                print(f"Failed to load from portraits index: {e}")
        
        # Fallback: scan sprites directory
        if self.sprites_dir.exists():
            return [d.name for d in self.sprites_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        return []
    
    def _clean_previous_sprites(self, character_id: str):
        """Clean up previously generated sprite files"""
        char_sprite_dir = self.sprites_dir / character_id
        if char_sprite_dir.exists():
            # Remove all PNG files but keep manifest.json
            for file_path in char_sprite_dir.rglob("*.png"):
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Warning: Could not remove {file_path}: {e}")
            
            # Remove old animation directories
            for anim_type in self.animation_types.keys():
                anim_dir = char_sprite_dir / anim_type
                if anim_dir.exists():
                    try:
                        shutil.rmtree(anim_dir)
                    except Exception as e:
                        print(f"Warning: Could not remove {anim_dir}: {e}")
    
    def _load_character_portrait(self, character_id: str) -> Optional[Image.Image]:
        """Load character portrait image"""
        portrait_candidates = [
            self.portraits_dir / f"{character_id}.png",
            self.portraits_dir / f"{character_id}_official.png",
            self.portraits_dir / f"{character_id}.jpg",
        ]
        
        for portrait_path in portrait_candidates:
            if portrait_path.exists():
                try:
                    img = Image.open(portrait_path).convert("RGBA")
                    print(f"Loaded portrait: {portrait_path}")
                    return img
                except Exception as e:
                    print(f"Failed to load {portrait_path}: {e}")
                    continue
        
        print(f"No portrait found for {character_id}")
        return None
    
    def _extract_character_figure(self, portrait: Image.Image) -> Image.Image:
        """Extract main character figure from portrait, removing backgrounds"""
        # Convert to RGBA if not already
        if portrait.mode != 'RGBA':
            portrait = portrait.convert('RGBA')
        
        # Get the alpha channel or create edge-based mask
        data = np.array(portrait)
        
        # If image has transparency, use it
        if data.shape[2] == 4:
            mask = data[:, :, 3] > 128
        else:
            # Create mask based on edge detection and color analysis
            gray = np.mean(data[:, :, :3], axis=2)
            
            # Find edges
            from scipy import ndimage
            edges = ndimage.sobel(gray)
            
            # Create mask based on non-background areas
            # Assume background is relatively uniform and at the edges
            height, width = gray.shape
            edge_pixels = np.concatenate([
                gray[0, :],  # top row
                gray[-1, :], # bottom row
                gray[:, 0],  # left column
                gray[:, -1]  # right column
            ])
            
            bg_color = np.median(edge_pixels)
            color_diff = np.abs(gray - bg_color)
            
            # Combine color difference and edge information
            mask = (color_diff > 20) | (edges > np.percentile(edges, 85))
            
            # Morphological operations to clean up mask
            from scipy.ndimage import binary_closing, binary_opening
            mask = binary_closing(mask, structure=np.ones((5, 5)))
            mask = binary_opening(mask, structure=np.ones((3, 3)))
        
        # Apply mask to create clean character cutout
        result = data.copy()
        result[~mask] = [0, 0, 0, 0]  # Make background transparent
        
        return Image.fromarray(result, 'RGBA')
    
    def _create_idle_frames(self, character_figure: Image.Image, count: int = 4) -> List[Image.Image]:
        """Create idle animation frames with subtle breathing effect"""
        frames = []
        base_width, base_height = character_figure.size
        
        for i in range(count):
            # Subtle scale variation for breathing effect
            phase = (i / count) * 2 * math.pi
            scale_factor = 1.0 + 0.02 * math.sin(phase)  # 2% variation
            
            # Slight vertical movement
            y_offset = int(2 * math.sin(phase))
            
            # Create frame
            frame = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            
            # Scale character slightly
            scaled_size = (int(base_width * scale_factor), int(base_height * scale_factor))
            temp_char = character_figure.resize(scaled_size, Image.Resampling.LANCZOS)
            
            # Center and position character
            char_x = (self.frame_size[0] - scaled_size[0]) // 2
            char_y = (self.frame_size[1] - scaled_size[1]) // 2 + y_offset
            
            frame.paste(temp_char, (char_x, char_y), temp_char)
            frames.append(frame)
        
        return frames
    
    def _create_walk_frames(self, character_figure: Image.Image, count: int = 6) -> List[Image.Image]:
        """Create walking animation frames"""
        frames = []
        base_width, base_height = character_figure.size
        
        for i in range(count):
            # Walking cycle with bob and lean
            phase = (i / count) * 2 * math.pi
            
            # Vertical bobbing
            y_offset = int(3 * abs(math.sin(phase)))
            
            # Horizontal lean
            lean_angle = 5 * math.sin(phase)  # degrees
            
            # Slight horizontal movement
            x_offset = int(2 * math.sin(phase * 2))
            
            # Create frame
            frame = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            
            # Rotate character slightly for lean
            if abs(lean_angle) > 0.5:
                temp_char = character_figure.rotate(lean_angle, resample=Image.Resampling.BICUBIC, expand=False)
            else:
                temp_char = character_figure
            
            # Position character
            char_x = (self.frame_size[0] - base_width) // 2 + x_offset
            char_y = (self.frame_size[1] - base_height) // 2 + y_offset
            
            frame.paste(temp_char, (char_x, char_y), temp_char)
            frames.append(frame)
        
        return frames
    
    def _create_attack_frames(self, character_figure: Image.Image, count: int = 5) -> List[Image.Image]:
        """Create attack animation frames"""
        frames = []
        base_width, base_height = character_figure.size
        
        for i in range(count):
            # Attack motion: wind up, strike, follow through
            progress = i / (count - 1)
            
            if progress < 0.3:  # Wind up
                scale_factor = 1.0 + 0.05 * (progress / 0.3)
                x_offset = int(-5 * (progress / 0.3))
                lean_angle = -10 * (progress / 0.3)
            elif progress < 0.6:  # Strike
                strike_progress = (progress - 0.3) / 0.3
                scale_factor = 1.05 + 0.1 * strike_progress
                x_offset = int(-5 + 15 * strike_progress)
                lean_angle = -10 + 20 * strike_progress
            else:  # Follow through
                follow_progress = (progress - 0.6) / 0.4
                scale_factor = 1.15 - 0.15 * follow_progress
                x_offset = int(10 - 8 * follow_progress)
                lean_angle = 10 - 12 * follow_progress
            
            # Add attack blur effect
            if 0.3 <= progress <= 0.6:
                # Motion blur during strike
                temp_char = character_figure.filter(ImageFilter.BLUR)
                enhancer = ImageEnhance.Brightness(temp_char)
                temp_char = enhancer.enhance(1.2)  # Brighten during strike
            else:
                temp_char = character_figure
            
            # Create frame
            frame = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            
            # Scale and rotate
            scaled_size = (int(base_width * scale_factor), int(base_height * scale_factor))
            temp_char = temp_char.resize(scaled_size, Image.Resampling.LANCZOS)
            if abs(lean_angle) > 0.5:
                temp_char = temp_char.rotate(lean_angle, resample=Image.Resampling.BICUBIC, expand=False)
            
            # Position
            char_x = (self.frame_size[0] - scaled_size[0]) // 2 + x_offset
            char_y = (self.frame_size[1] - scaled_size[1]) // 2
            
            frame.paste(temp_char, (char_x, char_y), temp_char)
            frames.append(frame)
        
        return frames
    
    def _create_hit_frames(self, character_figure: Image.Image, count: int = 3) -> List[Image.Image]:
        """Create hit reaction animation frames"""
        frames = []
        base_width, base_height = character_figure.size
        
        for i in range(count):
            progress = i / (count - 1)
            
            # Hit reaction: recoil and recovery
            if progress < 0.5:  # Recoil
                recoil_progress = progress / 0.5
                x_offset = int(-8 * recoil_progress)
                lean_angle = -15 * recoil_progress
                scale_factor = 0.95 + 0.05 * recoil_progress
            else:  # Recovery
                recovery_progress = (progress - 0.5) / 0.5
                x_offset = int(-8 + 6 * recovery_progress)
                lean_angle = -15 + 12 * recovery_progress
                scale_factor = 1.0 - 0.05 * recovery_progress
            
            # Add hit flash effect
            temp_char = character_figure.copy()
            if progress < 0.3:
                # Red flash effect during initial hit
                enhancer = ImageEnhance.Color(temp_char)
                temp_char = enhancer.enhance(0.5)  # Desaturate
                
                # Add red tint
                red_overlay = Image.new('RGBA', temp_char.size, (255, 100, 100, 100))
                temp_char = Image.alpha_composite(temp_char, red_overlay)
            
            # Create frame
            frame = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            
            # Scale and rotate
            scaled_size = (int(base_width * scale_factor), int(base_height * scale_factor))
            temp_char = temp_char.resize(scaled_size, Image.Resampling.LANCZOS)
            if abs(lean_angle) > 0.5:
                temp_char = temp_char.rotate(lean_angle, resample=Image.Resampling.BICUBIC, expand=False)
            
            # Position
            char_x = (self.frame_size[0] - scaled_size[0]) // 2 + x_offset
            char_y = (self.frame_size[1] - scaled_size[1]) // 2
            
            frame.paste(temp_char, (char_x, char_y), temp_char)
            frames.append(frame)
        
        return frames
    
    def _create_jump_frames(self, character_figure: Image.Image, count: int = 4) -> List[Image.Image]:
        """Create jump animation frames"""
        frames = []
        base_width, base_height = character_figure.size
        
        for i in range(count):
            progress = i / (count - 1)
            
            # Jump arc
            jump_height = int(25 * math.sin(progress * math.pi))  # Parabolic jump
            y_offset = -jump_height
            
            # Lean for jump dynamics
            if progress < 0.5:
                lean_angle = -5 * (progress / 0.5)  # Lean back for takeoff
            else:
                lean_angle = -5 + 10 * ((progress - 0.5) / 0.5)  # Lean forward for landing
            
            # Compress/stretch for squash and stretch
            if progress < 0.2:  # Crouch before jump
                scale_y = 1.0 - 0.1 * (progress / 0.2)
                scale_x = 1.0 + 0.05 * (progress / 0.2)
            elif progress > 0.8:  # Prepare for landing
                land_progress = (progress - 0.8) / 0.2
                scale_y = 1.0 - 0.05 * land_progress
                scale_x = 1.0 + 0.03 * land_progress
            else:  # In air
                scale_y = 1.05
                scale_x = 0.98
            
            # Create frame
            frame = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            
            # Scale character
            scaled_width = int(base_width * scale_x)
            scaled_height = int(base_height * scale_y)
            temp_char = character_figure.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            
            # Rotate for lean
            if abs(lean_angle) > 0.5:
                temp_char = temp_char.rotate(lean_angle, resample=Image.Resampling.BICUBIC, expand=False)
            
            # Position
            char_x = (self.frame_size[0] - scaled_width) // 2
            char_y = (self.frame_size[1] - scaled_height) // 2 + y_offset
            
            frame.paste(temp_char, (char_x, char_y), temp_char)
            frames.append(frame)
        
        return frames
    
    def _create_victory_frames(self, character_figure: Image.Image, count: int = 6) -> List[Image.Image]:
        """Create victory celebration animation frames"""
        frames = []
        base_width, base_height = character_figure.size
        
        for i in range(count):
            phase = (i / count) * 2 * math.pi
            
            # Victory pose with raised arms effect (simulate by scaling and positioning)
            scale_factor = 1.0 + 0.1 * abs(math.sin(phase))
            y_offset = int(-5 * abs(math.sin(phase)))  # Slight bounce
            
            # Add sparkle effect
            temp_char = character_figure.copy()
            if i % 2 == 0:
                enhancer = ImageEnhance.Brightness(temp_char)
                temp_char = enhancer.enhance(1.2)  # Brighten alternately
            
            # Create frame
            frame = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            
            # Scale character
            scaled_size = (int(base_width * scale_factor), int(base_height * scale_factor))
            temp_char = temp_char.resize(scaled_size, Image.Resampling.LANCZOS)
            
            # Position
            char_x = (self.frame_size[0] - scaled_size[0]) // 2
            char_y = (self.frame_size[1] - scaled_size[1]) // 2 + y_offset
            
            frame.paste(temp_char, (char_x, char_y), temp_char)
            frames.append(frame)
        
        return frames
    
    def _create_block_frames(self, character_figure: Image.Image, count: int = 2) -> List[Image.Image]:
        """Create blocking animation frames"""
        frames = []
        base_width, base_height = character_figure.size
        
        for i in range(count):
            # Defensive posture
            if i == 0:
                # Normal defensive pose
                lean_angle = -3
                scale_factor = 0.98
                x_offset = -2
            else:
                # Tensed blocking
                lean_angle = -5
                scale_factor = 0.95
                x_offset = -4
            
            # Add defensive effect (slightly darkened)
            temp_char = character_figure.copy()
            enhancer = ImageEnhance.Brightness(temp_char)
            temp_char = enhancer.enhance(0.9)
            
            # Create frame
            frame = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            
            # Scale and rotate
            scaled_size = (int(base_width * scale_factor), int(base_height * scale_factor))
            temp_char = temp_char.resize(scaled_size, Image.Resampling.LANCZOS)
            if abs(lean_angle) > 0.5:
                temp_char = temp_char.rotate(lean_angle, resample=Image.Resampling.BICUBIC, expand=False)
            
            # Position
            char_x = (self.frame_size[0] - scaled_size[0]) // 2 + x_offset
            char_y = (self.frame_size[1] - scaled_size[1]) // 2
            
            frame.paste(temp_char, (char_x, char_y), temp_char)
            frames.append(frame)
        
        return frames
    
    def _create_spritesheet(self, frames: List[Image.Image], animation_type: str) -> Image.Image:
        """Create spritesheet from animation frames"""
        if not frames:
            return None
        
        # Arrange frames in a horizontal row
        sheet_width = self.frame_size[0] * len(frames)
        sheet_height = self.frame_size[1]
        
        spritesheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
        
        for i, frame in enumerate(frames):
            x_pos = i * self.frame_size[0]
            spritesheet.paste(frame, (x_pos, 0), frame)
        
        return spritesheet
    
    def _save_individual_frames(self, frames: List[Image.Image], char_dir: Path, animation_type: str):
        """Save individual animation frames"""
        anim_dir = char_dir / animation_type
        anim_dir.mkdir(exist_ok=True)
        
        for i, frame in enumerate(frames):
            frame_path = anim_dir / f"{animation_type}_{i:02d}.png"
            frame.save(frame_path, "PNG")
    
    def _create_manifest(self, character_id: str, display_name: str) -> Dict:
        """Create sprite manifest for character"""
        manifest = {
            "source": f"Generated from enhanced portrait: {display_name}",
            "license": "Educational/Research Use",
            "character_id": character_id,
            "display_name": display_name,
            "sprite_version": "2.0_enhanced",
            "color_mod": {
                "multiply": [1.0, 1.0, 1.0],
                "add": [0, 0, 0]
            },
            "states": {}
        }
        
        # Add animation states
        for anim_type, config in self.animation_types.items():
            frames_count = config["frames"]
            manifest["states"][anim_type] = {
                "sheet": f"{character_id}_spritesheet.png",
                "frame_size": list(self.frame_size),
                "sequence": list(range(frames_count)),
                "fps": config["fps"],
                "loop": config["loop"],
                "durations": [1.0 / config["fps"]] * frames_count
            }
        
        return manifest
    
    def generate_character_sprites(self, character_id: str, display_name: str = None) -> bool:
        """Generate all sprite animations for a character"""
        if not display_name:
            display_name = character_id.replace('_', ' ').title()
        
        print(f"\n🎨 Generating sprites for {display_name} ({character_id})")
        
        # Load character portrait
        portrait = self._load_character_portrait(character_id)
        if not portrait:
            print(f"❌ No portrait found for {character_id}")
            return False
        
        # Clean previous sprites
        self._clean_previous_sprites(character_id)
        
        # Extract character figure
        character_figure = self._extract_character_figure(portrait)
        
        # Resize character to fit frame while maintaining aspect ratio
        char_width, char_height = character_figure.size
        max_char_size = min(self.frame_size[0] - 20, self.frame_size[1] - 20)  # Leave 10px margin
        
        if char_width > max_char_size or char_height > max_char_size:
            scale = max_char_size / max(char_width, char_height)
            new_size = (int(char_width * scale), int(char_height * scale))
            character_figure = character_figure.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create character sprite directory
        char_dir = self.sprites_dir / character_id
        char_dir.mkdir(exist_ok=True)
        
        # Generate all animation types
        all_frames = []
        success_count = 0
        
        for anim_type, config in self.animation_types.items():
            try:
                print(f"  Generating {anim_type} animation...")
                
                # Generate frames based on animation type
                if anim_type == "idle":
                    frames = self._create_idle_frames(character_figure, config["frames"])
                elif anim_type == "walk":
                    frames = self._create_walk_frames(character_figure, config["frames"])
                elif anim_type == "attack":
                    frames = self._create_attack_frames(character_figure, config["frames"])
                elif anim_type == "hit":
                    frames = self._create_hit_frames(character_figure, config["frames"])
                elif anim_type == "jump":
                    frames = self._create_jump_frames(character_figure, config["frames"])
                elif anim_type == "victory":
                    frames = self._create_victory_frames(character_figure, config["frames"])
                elif anim_type == "block":
                    frames = self._create_block_frames(character_figure, config["frames"])
                else:
                    frames = []
                
                if frames:
                    # Save individual frames
                    self._save_individual_frames(frames, char_dir, anim_type)
                    
                    # Add to combined spritesheet
                    all_frames.extend(frames)
                    success_count += 1
                    print(f"    ✅ {anim_type}: {len(frames)} frames")
                else:
                    print(f"    ❌ {anim_type}: Failed to generate frames")
                    
            except Exception as e:
                print(f"    ❌ {anim_type}: Error - {e}")
        
        # Create combined spritesheet
        if all_frames:
            try:
                spritesheet = self._create_spritesheet(all_frames, "combined")
                if spritesheet:
                    sheet_path = char_dir / f"{character_id}_spritesheet.png"
                    spritesheet.save(sheet_path, "PNG")
                    print(f"  💾 Saved combined spritesheet: {sheet_path}")
            except Exception as e:
                print(f"  ❌ Failed to create spritesheet: {e}")
        
        # Create and save manifest
        try:
            manifest = self._create_manifest(character_id, display_name)
            manifest_path = char_dir / "manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            print(f"  📋 Saved manifest: {manifest_path}")
        except Exception as e:
            print(f"  ❌ Failed to create manifest: {e}")
        
        print(f"✅ Completed {character_id}: {success_count}/{len(self.animation_types)} animations generated")
        return success_count > 0
    
    def regenerate_problematic_characters(self):
        """Regenerate sprites for mr_big and wolfgang_krauser with single character focus"""
        problematic_chars = ["mr_big", "wolfgang_krauser"]
        
        for char_id in problematic_chars:
            print(f"\n🔧 Fixing {char_id} - ensuring single character portrait")
            
            # Load and process portrait specifically for single character extraction
            portrait = self._load_character_portrait(char_id)
            if not portrait:
                continue
            
            # Enhanced character extraction for these specific cases
            character_figure = self._extract_single_character_figure(portrait, char_id)
            
            if character_figure:
                # Continue with sprite generation
                self.generate_character_sprites(char_id)
            else:
                print(f"❌ Failed to extract single character from {char_id} portrait")
    
    def _extract_single_character_figure(self, portrait: Image.Image, character_id: str) -> Optional[Image.Image]:
        """Enhanced single character extraction for problematic characters"""
        if portrait.mode != 'RGBA':
            portrait = portrait.convert('RGBA')
        
        data = np.array(portrait)
        height, width = data.shape[:2]
        
        # For mr_big and wolfgang_krauser, focus on center-dominant figure
        if character_id in ["mr_big", "wolfgang_krauser"]:
            # Find the largest connected component that's roughly centered
            gray = np.mean(data[:, :, :3], axis=2)
            
            # Enhanced background detection
            # Sample more edge pixels for better background color estimation
            edge_sample_size = max(10, min(width//10, height//10))
            edge_pixels = np.concatenate([
                gray[:edge_sample_size, :].flatten(),  # top rows
                gray[-edge_sample_size:, :].flatten(), # bottom rows
                gray[:, :edge_sample_size].flatten(),  # left columns
                gray[:, -edge_sample_size:].flatten()  # right columns
            ])
            
            bg_color = np.median(edge_pixels)
            bg_std = np.std(edge_pixels)
            
            # Create more aggressive foreground mask
            color_diff = np.abs(gray - bg_color)
            foreground_mask = color_diff > (bg_std + 15)  # More selective
            
            # Find connected components
            from scipy.ndimage import label, center_of_mass
            labeled_array, num_features = label(foreground_mask)
            
            if num_features > 1:
                # Find the component closest to center and largest
                center_y, center_x = height // 2, width // 2
                best_component = 1
                best_score = 0
                
                for i in range(1, num_features + 1):
                    component_mask = labeled_array == i
                    component_size = np.sum(component_mask)
                    
                    if component_size < 1000:  # Skip very small components
                        continue
                    
                    # Find center of mass of this component
                    cy, cx = center_of_mass(component_mask)
                    
                    # Score based on size and proximity to center
                    center_distance = np.sqrt((cy - center_y)**2 + (cx - center_x)**2)
                    max_distance = np.sqrt(center_y**2 + center_x**2)
                    
                    # Favor larger components closer to center
                    size_score = component_size / (width * height)
                    center_score = 1.0 - (center_distance / max_distance)
                    total_score = size_score * 0.7 + center_score * 0.3
                    
                    if total_score > best_score:
                        best_score = total_score
                        best_component = i
                
                # Use only the best component
                final_mask = labeled_array == best_component
            else:
                final_mask = foreground_mask
            
            # Clean up the mask
            from scipy.ndimage import binary_closing, binary_opening, binary_fill_holes
            final_mask = binary_fill_holes(final_mask)
            final_mask = binary_closing(final_mask, structure=np.ones((7, 7)))
            final_mask = binary_opening(final_mask, structure=np.ones((3, 3)))
            
            # Apply mask
            result = data.copy()
            result[~final_mask] = [0, 0, 0, 0]
            
            return Image.fromarray(result, 'RGBA')
        
        # Default extraction for other characters
        return self._extract_character_figure(portrait)
    
    def generate_all_character_sprites(self) -> Dict[str, bool]:
        """Generate sprites for all characters"""
        results = {}
        success_count = 0
        
        print(f"\n🚀 Starting sprite generation for {len(self.characters)} characters...")
        
        # Load character names for display
        char_names = {}
        portraits_index_path = self.assets_dir / "character_portraits_index.json"
        if portraits_index_path.exists():
            try:
                with open(portraits_index_path, 'r', encoding='utf-8') as f:
                    portraits_data = json.load(f)
                    for char_id, data in portraits_data.items():
                        char_names[char_id] = data.get('display_name', char_id.replace('_', ' ').title())
            except Exception as e:
                print(f"Warning: Could not load character names: {e}")
        
        for char_id in self.characters:
            display_name = char_names.get(char_id, char_id.replace('_', ' ').title())
            
            try:
                success = self.generate_character_sprites(char_id, display_name)
                results[char_id] = success
                if success:
                    success_count += 1
            except Exception as e:
                print(f"❌ Failed to generate sprites for {char_id}: {e}")
                results[char_id] = False
        
        print(f"\n🎯 Sprite generation completed!")
        print(f"✅ Success: {success_count}/{len(self.characters)} characters")
        print(f"❌ Failed: {len(self.characters) - success_count}/{len(self.characters)} characters")
        
        # Generate summary
        failed_chars = [char_id for char_id, success in results.items() if not success]
        if failed_chars:
            print(f"\nFailed characters: {', '.join(failed_chars)}")
        
        return results
    
    def get_character_list(self) -> List[str]:
        """Get the list of available characters (public method for testing)"""
        return self.characters


def main():
    """Main function for testing and batch processing"""
    import sys
    
    # Initialize generator
    assets_dir = Path(__file__).parent.parent / "assets"
    generator = SpriteAnimationGenerator(str(assets_dir))
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "fix-problematic":
            # Fix mr_big and wolfgang_krauser
            generator.regenerate_problematic_characters()
        elif sys.argv[1] == "single":
            if len(sys.argv) > 2:
                char_id = sys.argv[2]
                generator.generate_character_sprites(char_id)
            else:
                print("Usage: python sprite_animation_generator.py single <character_id>")
        else:
            print("Usage: python sprite_animation_generator.py [fix-problematic|single <char_id>]")
    else:
        # Generate for all characters
        generator.generate_all_character_sprites()


if __name__ == "__main__":
    main()