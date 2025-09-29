#!/usr/bin/env python3
"""Simple character converter for testing."""

import subprocess
import sys
import zipfile
from pathlib import Path

def convert_single_character(character_id: str, archive_path: Path, output_dir: Path):
    """Convert a single character manually."""
    
    print(f"Converting {character_id} from {archive_path}")
    
    # Create output directory
    char_dir = output_dir / character_id / "sketchfab"
    char_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract archive
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(char_dir)
    
    # Find GLTF/GLB files
    gltf_files = list(char_dir.rglob("*.gltf"))
    glb_files = list(char_dir.rglob("*.glb"))
    
    if not gltf_files and not glb_files:
        print(f"No GLTF/GLB files found for {character_id}")
        return False
    
    # Use GLTF if available, otherwise GLB
    model_file = gltf_files[0] if gltf_files else glb_files[0]
    print(f"Using model file: {model_file}")
    
    # Output BAM file
    bam_path = char_dir / f"{character_id}.bam"
    
    # Simple gltf2bam command
    cmd = [
        "gltf2bam",
        "--textures", "ref",
        "--animations", "embed",  # Embed animations to avoid complexity
        str(model_file),
        str(bam_path)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ Successfully converted {character_id} to {bam_path}")
            return True
        else:
            print(f"❌ Conversion failed for {character_id}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Conversion timed out for {character_id}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error converting {character_id}: {e}")
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
    
    success_count = 0
    
    for archive in archives:
        character_id = archive.stem
        if convert_single_character(character_id, archive, characters_dir):
            success_count += 1
    
    print(f"\nConverted {success_count}/{len(archives)} characters successfully")

if __name__ == "__main__":
    main()