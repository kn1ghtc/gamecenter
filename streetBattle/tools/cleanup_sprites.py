#!/usr/bin/env python3
"""
清理sprites目录，删除不属于有效角色列表的目录
"""
import os
import json
import shutil
import sys
from pathlib import Path

def load_valid_characters():
    """从resource_catalog.json加载有效角色列表"""
    catalog_path = Path("assets/resource_catalog.json")
    if not catalog_path.exists():
        print(f"Error: {catalog_path} not found!")
        return set()
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid_chars = set(data.keys())
    print(f"Found {len(valid_chars)} valid characters in catalog")
    return valid_chars

def cleanup_sprites_directory(valid_characters, dry_run=False):
    """清理sprites目录"""
    sprites_dir = Path("assets/sprites")
    if not sprites_dir.exists():
        print(f"Error: {sprites_dir} not found!")
        return
    
    # 获取所有子目录
    directories = [d for d in sprites_dir.iterdir() if d.is_dir()]
    
    removed_count = 0
    kept_count = 0
    
    print(f"\nAnalyzing {len(directories)} directories in sprites folder...")
    
    for dir_path in directories:
        dir_name = dir_path.name
        
        # 跳过特殊目录
        if dir_name in ['hero', 'shadow']:
            print(f"  Keeping special directory: {dir_name}")
            kept_count += 1
            continue
            
        if dir_name in valid_characters:
            print(f"  ✓ Keeping valid character: {dir_name}")
            kept_count += 1
        else:
            print(f"  ✗ Removing invalid character: {dir_name}")
            if not dry_run:
                try:
                    shutil.rmtree(dir_path)
                    print(f"    Deleted: {dir_path}")
                except Exception as e:
                    print(f"    Error deleting {dir_path}: {e}")
            removed_count += 1
    
    print(f"\nSummary:")
    print(f"  Kept: {kept_count} directories")
    print(f"  {'Would remove' if dry_run else 'Removed'}: {removed_count} directories")
    
    return removed_count, kept_count

def main():
    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("=== Sprites Directory Cleanup Tool ===")
    print(f"Working directory: {os.getcwd()}")
    
    # 检查是否为dry-run模式
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("Running in DRY-RUN mode - no files will be deleted")
    
    # 加载有效角色列表
    valid_characters = load_valid_characters()
    if not valid_characters:
        print("No valid characters found, exiting...")
        return
    
    # 清理目录
    removed, kept = cleanup_sprites_directory(valid_characters, dry_run)
    
    if not dry_run and removed > 0:
        print(f"\nCleanup completed! Removed {removed} invalid directories.")
    elif dry_run:
        print(f"\nDry-run completed. Would remove {removed} directories.")
    else:
        print("\nNo cleanup needed - all directories are valid.")

if __name__ == "__main__":
    main()