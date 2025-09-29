#!/usr/bin/env python3
"""Robust character converter with fallback options."""

import subprocess
import sys
import zipfile
from pathlib import Path

def convert_with_fallback(character_id: str, model_file: Path, bam_path: Path):
    """Try different conversion options as fallback."""
    
    conversion_options = [
        # Option 1: With animations embedded
        ["gltf2bam", "--textures", "ref", "--animations", "embed", str(model_file), str(bam_path)],
        # Option 2: Skip animations
        ["gltf2bam", "--textures", "ref", "--animations", "skip", str(model_file), str(bam_path)],
        # Option 3: Legacy materials
        ["gltf2bam", "--textures", "ref", "--animations", "skip", "--legacy-materials", str(model_file), str(bam_path)],
    ]
    
    for i, cmd in enumerate(conversion_options, 1):
        print(f"Attempt {i}/3: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and bam_path.exists():
                print(f"✅ Conversion successful with option {i}")
                return True
            else:
                print(f"❌ Option {i} failed")
                if result.stderr:
                    print(f"Error: {result.stderr[:200]}...")
                    
        except subprocess.TimeoutExpired:
            print(f"❌ Option {i} timed out")
        except Exception as e:
            print(f"❌ Option {i} error: {e}")
    
    return False

def convert_single_character(character_id: str, archive_path: Path, output_dir: Path):
    """Convert a single character with robust error handling."""
    
    print(f"\n{'='*50}")
    print(f"Converting {character_id}")
    print(f"{'='*50}")
    
    # Create output directory
    char_dir = output_dir / character_id / "sketchfab"
    char_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract archive if not already extracted
    gltf_files = list(char_dir.rglob("*.gltf"))
    glb_files = list(char_dir.rglob("*.glb"))
    
    if not gltf_files and not glb_files:
        print(f"Extracting {archive_path}...")
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(char_dir)
        
        # Re-scan for model files
        gltf_files = list(char_dir.rglob("*.gltf"))
        glb_files = list(char_dir.rglob("*.glb"))
    
    if not gltf_files and not glb_files:
        print(f"❌ No GLTF/GLB files found for {character_id}")
        return False
    
    # Output BAM file
    bam_path = char_dir / f"{character_id}.bam"
    
    # Try GLTF files first, then GLB
    model_files = gltf_files + glb_files
    
    for model_file in model_files:
        print(f"Trying model file: {model_file}")
        
        if convert_with_fallback(character_id, model_file, bam_path):
            print(f"✅ Successfully converted {character_id} using {model_file.name}")
            return True
    
    print(f"❌ All conversion attempts failed for {character_id}")
    return False

def main():
    assets_dir = Path("assets")
    downloads_dir = assets_dir / "downloads"
    characters_dir = assets_dir / "characters"
    
    if not downloads_dir.exists():
        print("Downloads directory not found")
        return
    
    archives = list(downloads_dir.glob("*.zip"))
    if not archives:
        print("No archive files found")
        return
    
    print(f"Found {len(archives)} archives to process")
    
    success_count = 0
    failed_characters = []
    
    for archive in archives:
        character_id = archive.stem
        if convert_single_character(character_id, archive, characters_dir):
            success_count += 1
        else:
            failed_characters.append(character_id)
    
    print(f"\n{'='*60}")
    print(f"CONVERSION SUMMARY")
    print(f"{'='*60}")
    print(f"Successful: {success_count}/{len(archives)} characters")
    
    if failed_characters:
        print(f"Failed: {', '.join(failed_characters)}")
    
    print(f"Success rate: {(success_count/len(archives)*100):.1f}%")

if __name__ == "__main__":
    main()