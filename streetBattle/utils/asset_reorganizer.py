#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asset Reorganizer for Street Battle Game
Moves misplaced assets to proper directories and updates code references
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import re

class AssetReorganizer:
    """Tool to reorganize misplaced assets"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.assets_dir = self.base_dir / "assets"
        self.moves_performed = []
        self.code_updates = []
        
        # Define proper directory structure
        self.target_dirs = {
            # Audio files
            'audio': {
                'extensions': ['.wav', '.mp3', '.ogg', '.flac', '.aiff'],
                'subdirs': ['music', 'sfx', 'voice']
            },
            # Image files
            'images': {
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tga'],
                'subdirs': ['ui', 'backgrounds', 'effects', 'particles']
            },
            # Texture files
            'textures': {
                'extensions': ['.jpg', '.jpeg', '.png', '.dds', '.tga'],
                'subdirs': ['characters', 'ui', 'backgrounds', 'effects']
            },
            # Model files
            'models': {
                'extensions': ['.bam', '.egg', '.obj', '.fbx', '.dae'],
                'subdirs': ['characters', 'props', 'environments']
            }
        }
    
    def scan_misplaced_assets(self) -> List[Tuple[Path, str]]:
        """Scan for assets in wrong locations"""
        misplaced = []
        
        # Check assets root directory
        for file_path in self.assets_dir.iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lower()
                
                # Find which category this file belongs to
                target_category = self._get_file_category(ext)
                if target_category:
                    misplaced.append((file_path, target_category))
        
        return misplaced
    
    def _get_file_category(self, extension: str) -> str:
        """Get the proper category for a file extension"""
        for category, config in self.target_dirs.items():
            if extension in config['extensions']:
                return category
        return None
    
    def _get_target_subdirectory(self, file_path: Path, category: str) -> str:
        """Determine the appropriate subdirectory for a file"""
        filename = file_path.name.lower()
        
        if category == 'audio':
            if any(word in filename for word in ['win', 'lose', 'victory', 'defeat']):
                return 'music'
            elif any(word in filename for word in ['hit', 'punch', 'kick', 'attack']):
                return 'sfx'
            elif any(word in filename for word in ['voice', 'speak', 'talk']):
                return 'voice'
            else:
                return 'sfx'  # Default for audio
        
        elif category == 'images' or category == 'textures':
            if any(word in filename for word in ['particle', 'effect', 'explosion', 'fire']):
                return 'effects'
            elif any(word in filename for word in ['background', 'stage', 'scene']):
                return 'backgrounds'
            elif any(word in filename for word in ['ui', 'button', 'menu', 'hud']):
                return 'ui'
            elif any(word in filename for word in ['character', 'player', 'fighter']):
                return 'characters'
            else:
                return 'effects'  # Default
        
        elif category == 'models':
            if any(word in filename for word in ['character', 'player', 'fighter']):
                return 'characters'
            elif any(word in filename for word in ['prop', 'object', 'item']):
                return 'props'
            else:
                return 'environments'  # Default
        
        return 'misc'
    
    def reorganize_assets(self) -> int:
        """Reorganize misplaced assets"""
        misplaced = self.scan_misplaced_assets()
        moved_count = 0
        
        for file_path, category in misplaced:
            try:
                # Determine target subdirectory
                subdir = self._get_target_subdirectory(file_path, category)
                
                # Create target directory
                target_dir = self.assets_dir / category / subdir
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file
                target_path = target_dir / file_path.name
                
                # Handle conflicts
                if target_path.exists():
                    # Create a unique name
                    base_name = target_path.stem
                    extension = target_path.suffix
                    counter = 1
                    while target_path.exists():
                        target_path = target_dir / f"{base_name}_{counter}{extension}"
                        counter += 1
                
                shutil.move(str(file_path), str(target_path))
                
                self.moves_performed.append({
                    'from': str(file_path),
                    'to': str(target_path),
                    'category': category,
                    'subdir': subdir
                })
                
                moved_count += 1
                print(f"Moved: {file_path.name} -> {category}/{subdir}/")
                
            except Exception as e:
                print(f"Failed to move {file_path}: {e}")
        
        return moved_count
    
    def find_code_references(self) -> Dict[str, List[str]]:
        """Find code files that might reference moved assets"""
        code_references = {}
        
        # Search for Python files
        python_files = list(self.base_dir.glob("**/*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for asset references
                references = []
                for move in self.moves_performed:
                    old_path = Path(move['from'])
                    filename = old_path.name
                    
                    # Search for various path patterns
                    patterns = [
                        filename,
                        f"assets/{filename}",
                        f"assets\\{filename}",
                        old_path.name.replace('.', r'\.'),
                    ]
                    
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            references.append({
                                'pattern': pattern,
                                'old_path': move['from'],
                                'new_path': move['to']
                            })
                
                if references:
                    code_references[str(py_file)] = references
                    
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
        
        return code_references
    
    def update_code_references(self, code_references: Dict[str, List[str]]) -> int:
        """Update code references to moved assets"""
        updated_files = 0
        
        for file_path, references in code_references.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for ref in references:
                    old_path = Path(ref['old_path'])
                    new_path = Path(ref['new_path'])
                    
                    # Convert to relative path from base directory
                    try:
                        old_rel = old_path.relative_to(self.base_dir)
                        new_rel = new_path.relative_to(self.base_dir)
                    except ValueError:
                        # If relative path fails, use the paths as-is
                        old_rel = old_path
                        new_rel = new_path
                    
                    # Replace various path formats
                    old_patterns = [
                        str(old_rel).replace('\\', '/'),
                        str(old_rel).replace('/', '\\'),
                        old_path.name,
                    ]
                    
                    new_path_str = str(new_rel).replace('\\', '/')
                    
                    for old_pattern in old_patterns:
                        content = content.replace(old_pattern, new_path_str)
                
                # Write back if changed
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    updated_files += 1
                    self.code_updates.append(file_path)
                    print(f"Updated references in: {os.path.basename(file_path)}")
                    
            except Exception as e:
                print(f"Error updating {file_path}: {e}")
        
        return updated_files
    
    def generate_reorganization_report(self) -> str:
        """Generate reorganization report"""
        report = f"""
=== ASSET REORGANIZATION REPORT ===
Base Directory: {self.base_dir}
Assets Moved: {len(self.moves_performed)}
Code Files Updated: {len(self.code_updates)}

MOVED ASSETS:
"""
        for move in self.moves_performed:
            old_name = Path(move['from']).name
            new_location = f"{move['category']}/{move['subdir']}"
            report += f"  {old_name} -> {new_location}\n"
        
        report += f"""
UPDATED CODE FILES:
"""
        for code_file in self.code_updates:
            report += f"  {os.path.basename(code_file)}\n"
        
        report += f"""
NEW DIRECTORY STRUCTURE:
assets/
  ├── audio/
  │   ├── music/
  │   ├── sfx/
  │   └── voice/
  ├── images/
  │   ├── ui/
  │   ├── backgrounds/
  │   ├── effects/
  │   └── particles/
  ├── textures/
  │   ├── characters/
  │   ├── ui/
  │   ├── backgrounds/
  │   └── effects/
  └── models/
      ├── characters/
      ├── props/
      └── environments/

RECOMMENDATIONS:
1. Test all audio and image loading in the game
2. Verify that moved particle.png works correctly
3. Check that win.ogg and lose.ogg play at the right times
4. Consider creating additional subdirectories as needed
"""
        
        return report

def main():
    """Main reorganization function"""
    import sys
    
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Starting asset reorganization in: {base_dir}")
    
    reorganizer = AssetReorganizer(base_dir)
    
    # Scan for misplaced assets
    misplaced = reorganizer.scan_misplaced_assets()
    print(f"Found {len(misplaced)} misplaced assets")
    
    if misplaced:
        # Show what will be moved
        print("Assets to be moved:")
        for file_path, category in misplaced:
            subdir = reorganizer._get_target_subdirectory(file_path, category)
            print(f"  {file_path.name} -> {category}/{subdir}/")
        
        # Confirm before proceeding
        response = input("\nProceed with reorganization? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Reorganization cancelled.")
            return
        
        # Reorganize assets
        moved_count = reorganizer.reorganize_assets()
        print(f"Successfully moved {moved_count} assets")
        
        # Find and update code references
        print("Scanning for code references...")
        code_references = reorganizer.find_code_references()
        
        if code_references:
            print(f"Found references in {len(code_references)} code files")
            updated_count = reorganizer.update_code_references(code_references)
            print(f"Updated {updated_count} code files")
        
        # Generate report
        report = reorganizer.generate_reorganization_report()
        
        # Save report
        report_path = os.path.join(base_dir, 'asset_reorganization_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nReorganization report saved to: {report_path}")
        print("\n=== SUMMARY ===")
        print(f"Assets moved: {moved_count}")
        print(f"Code files updated: {len(reorganizer.code_updates)}")
        print("Asset reorganization completed!")
    else:
        print("No misplaced assets found!")

if __name__ == '__main__':
    main()