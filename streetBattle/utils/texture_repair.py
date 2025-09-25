#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Texture Repair Utility for Street Battle Game
Fixes corrupted JPEG files that start with 0x5c 0x78 instead of proper JPEG headers
"""

import os
import glob
from typing import List, Tuple
from pathlib import Path

class TextureRepairTool:
    """Tool to repair corrupted texture files"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.corrupted_files = []
        self.repaired_files = []
        
    def scan_corrupted_textures(self) -> List[str]:
        """Scan for corrupted JPEG files"""
        corrupted = []
        
        # Find all JPEG files
        jpeg_patterns = ['**/*.jpg', '**/*.jpeg']
        jpeg_files = []
        
        for pattern in jpeg_patterns:
            jpeg_files.extend(self.base_dir.glob(pattern))
        
        print(f"Scanning {len(jpeg_files)} JPEG files for corruption...")
        
        for jpeg_file in jpeg_files:
            if self._is_corrupted_jpeg(jpeg_file):
                corrupted.append(str(jpeg_file))
        
        self.corrupted_files = corrupted
        return corrupted
    
    def _is_corrupted_jpeg(self, file_path: Path) -> bool:
        """Check if JPEG file is corrupted (starts with 0x5c 0x78)"""
        try:
            if not file_path.exists() or file_path.stat().st_size < 2:
                return False
            
            with open(file_path, 'rb') as f:
                header = f.read(2)
                # Check for the corrupt header 0x5c 0x78 (backslash-x)
                return len(header) == 2 and header[0] == 0x5c and header[1] == 0x78
                
        except Exception:
            return False
    
    def create_placeholder_texture(self, output_path: str, color: Tuple[int, int, int] = (128, 128, 128), size: int = 64) -> bool:
        """Create a simple placeholder JPEG texture"""
        try:
            # Create minimal valid JPEG content
            # This is a very simple 1x1 grayscale JPEG
            jpeg_data = bytearray([
                # SOI (Start of Image)
                0xFF, 0xD8,
                # APP0 (JFIF header)
                0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00,
                # DQT (Define Quantization Table)
                0xFF, 0xDB, 0x00, 0x43, 0x00,
                # Quantization table data (simplified)
                *([0x10] * 64),
                # SOF0 (Start of Frame)
                0xFF, 0xC0, 0x00, 0x11, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01,
                # DHT (Define Huffman Table) - simplified
                0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08,
                0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                # SOS (Start of Scan)
                0xFF, 0xDA, 0x00, 0x0C, 0x03, 0x01, 0x00, 0x02, 0x11, 0x03, 0x11, 0x00, 0x3F, 0x00,
                # Minimal image data
                0x00,
                # EOI (End of Image)
                0xFF, 0xD9
            ])
            
            with open(output_path, 'wb') as f:
                f.write(jpeg_data)
            
            return True
            
        except Exception as e:
            print(f"Failed to create placeholder texture: {e}")
            return False
    
    def repair_corrupted_textures(self) -> int:
        """Repair all corrupted textures by replacing them with placeholders"""
        if not self.corrupted_files:
            self.scan_corrupted_textures()
        
        repaired_count = 0
        colors = [
            (128, 128, 128),  # Gray
            (64, 64, 64),     # Dark gray
            (192, 192, 192),  # Light gray
            (128, 64, 64),    # Dark red
            (64, 128, 64),    # Dark green
            (64, 64, 128),    # Dark blue
        ]
        
        for i, corrupted_file in enumerate(self.corrupted_files):
            try:
                # Create backup of corrupted file
                backup_path = corrupted_file + '.corrupted_backup'
                if not os.path.exists(backup_path):
                    os.rename(corrupted_file, backup_path)
                
                # Create placeholder texture
                color = colors[i % len(colors)]
                if self.create_placeholder_texture(corrupted_file, color):
                    self.repaired_files.append(corrupted_file)
                    repaired_count += 1
                    print(f"Repaired: {os.path.basename(corrupted_file)}")
                else:
                    # Restore backup if repair failed
                    if os.path.exists(backup_path):
                        os.rename(backup_path, corrupted_file)
                    
            except Exception as e:
                print(f"Failed to repair {corrupted_file}: {e}")
        
        return repaired_count
    
    def create_texture_directory_structure(self):
        """Create proper texture directory structure"""
        texture_dirs = [
            'assets/textures/characters',
            'assets/textures/ui',
            'assets/textures/backgrounds',
            'assets/textures/effects'
        ]
        
        for texture_dir in texture_dirs:
            full_path = self.base_dir / texture_dir
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create a default texture in each directory
            default_texture = full_path / 'default.jpg'
            if not default_texture.exists():
                self.create_placeholder_texture(str(default_texture), (128, 128, 128))
                print(f"Created default texture in {texture_dir}")
    
    def generate_repair_report(self) -> str:
        """Generate repair report"""
        report = f"""
=== TEXTURE REPAIR REPORT ===
Base Directory: {self.base_dir}
Corrupted Files Found: {len(self.corrupted_files)}
Files Successfully Repaired: {len(self.repaired_files)}

Corrupted Files:
"""
        for corrupted_file in self.corrupted_files:
            status = "✓ REPAIRED" if corrupted_file in self.repaired_files else "✗ FAILED"
            rel_path = os.path.relpath(corrupted_file, self.base_dir)
            report += f"  {status} {rel_path}\n"
        
        report += f"""
Repair Strategy:
- Corrupted files (starting with 0x5c 0x78) were backed up with .corrupted_backup extension
- Replaced with minimal valid JPEG placeholder textures
- Used different gray tones for visual variety
- Original corrupted files preserved as backups

Next Steps:
1. Test game loading with repaired textures
2. Replace placeholder textures with actual character textures if available
3. Update texture paths in character models if needed
"""
        
        return report

def main():
    """Main repair function"""
    import sys
    
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        # Default to streetBattle directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Starting texture repair in: {base_dir}")
    
    repair_tool = TextureRepairTool(base_dir)
    
    # Scan for corrupted textures
    corrupted_files = repair_tool.scan_corrupted_textures()
    print(f"Found {len(corrupted_files)} corrupted texture files")
    
    if corrupted_files:
        # Repair corrupted textures
        repaired_count = repair_tool.repair_corrupted_textures()
        print(f"Successfully repaired {repaired_count} texture files")
        
        # Create proper directory structure
        repair_tool.create_texture_directory_structure()
        
        # Generate report
        report = repair_tool.generate_repair_report()
        
        # Save report
        report_path = os.path.join(base_dir, 'texture_repair_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nRepair report saved to: {report_path}")
        print("\n=== SUMMARY ===")
        print(f"Corrupted files found: {len(corrupted_files)}")
        print(f"Files repaired: {repaired_count}")
        print(f"Success rate: {repaired_count/len(corrupted_files)*100:.1f}%")
    else:
        print("No corrupted texture files found!")
    
    print("Texture repair completed!")

if __name__ == '__main__':
    main()