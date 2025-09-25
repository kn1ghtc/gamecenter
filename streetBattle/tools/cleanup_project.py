#!/usr/bin/env python3
"""
StreetBattle项目清理工具
安全清理无用旧资源，保留高质量资源和必要代码
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime

def cleanup_streetbattle_project():
    """清理StreetBattle项目中的无用文件"""
    
    project_root = Path(__file__).parent
    cleanup_report = {
        "timestamp": datetime.now().isoformat(),
        "deleted_files": [],
        "deleted_dirs": [],
        "preserved_files": [],
        "summary": {}
    }
    
    print("=== StreetBattle 项目清理工具 ===")
    print(f"项目根目录: {project_root}")
    
    # 定义要删除的文件模式
    delete_patterns = [
        "*.bak", "*.old", "*.tmp", "*.temp",
        "*~", "*.swp", ".DS_Store", "Thumbs.db",
        "test_3d_resources.py"  # 临时测试文件
    ]
    
    # 定义要删除的小文件（可能是占位符）
    small_file_threshold = 50  # 字节
    
    # 定义要保留的重要文件模式  
    preserve_patterns = [
        "*.py", "*.json", "*.fbx", "*.gltf", "*.glb", "*.bam", "*.egg",
        "*.wav", "*.ogg", "*.png", "*.jpg", "*.jpeg", "*.txt", "*.md",
        "materials.txt", "resource_info.json", "character_config.json"
    ]
    
    deleted_count = 0
    preserved_count = 0
    
    # 遍历所有文件
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        
        # 跳过.git等隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = root_path / file
            relative_path = file_path.relative_to(project_root)
            
            should_delete = False
            delete_reason = ""
            
            # 检查删除模式
            for pattern in delete_patterns:
                if file_path.match(pattern):
                    should_delete = True
                    delete_reason = f"匹配删除模式: {pattern}"
                    break
            
            # 检查是否为过小的可疑文件（可能是占位符）
            if not should_delete and file_path.stat().st_size < small_file_threshold:
                if file.endswith('.txt') and 'placeholder' in file_path.read_text(encoding='utf-8', errors='ignore').lower():
                    should_delete = True
                    delete_reason = f"占位符文件 (<{small_file_threshold}字节)"
            
            # 检查保留模式 - 重要文件不删除
            if should_delete:
                for preserve_pattern in preserve_patterns:
                    if file_path.match(preserve_pattern):
                        # 特殊检查：materials.txt等重要配置文件
                        if file in ['materials.txt', 'resource_info.json', 'character_config.json']:
                            should_delete = False
                            delete_reason = ""
                            break
            
            if should_delete:
                try:
                    file_path.unlink()
                    cleanup_report["deleted_files"].append({
                        "path": str(relative_path),
                        "reason": delete_reason,
                        "size": file_path.stat().st_size if file_path.exists() else 0
                    })
                    deleted_count += 1
                    print(f"✓ 删除: {relative_path} ({delete_reason})")
                except Exception as e:
                    print(f"✗ 删除失败: {relative_path} - {e}")
            else:
                preserved_count += 1
                if file.endswith(('.py', '.json', '.fbx', '.gltf', '.glb')):
                    cleanup_report["preserved_files"].append(str(relative_path))
    
    # 清理空目录
    empty_dirs_removed = 0
    for root, dirs, files in os.walk(project_root, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):  # 空目录
                    relative_path = dir_path.relative_to(project_root)
                    dir_path.rmdir()
                    cleanup_report["deleted_dirs"].append(str(relative_path))
                    empty_dirs_removed += 1
                    print(f"✓ 删除空目录: {relative_path}")
            except OSError:
                pass  # 目录不为空或无法删除
    
    # 生成清理报告
    cleanup_report["summary"] = {
        "deleted_files": deleted_count,
        "deleted_directories": empty_dirs_removed,
        "preserved_files": preserved_count,
        "total_processed": deleted_count + preserved_count
    }
    
    # 保存清理报告
    report_file = project_root / "assets" / "cleanup_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(cleanup_report, f, indent=2, ensure_ascii=False)
    
    print(f"\\n=== 清理完成 ===")
    print(f"删除文件: {deleted_count}")
    print(f"删除空目录: {empty_dirs_removed}")
    print(f"保留重要文件: {preserved_count}")
    print(f"清理报告: {report_file}")
    
    return cleanup_report

if __name__ == "__main__":
    cleanup_streetbattle_project()