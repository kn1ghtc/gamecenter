#!/usr/bin/env python3
"""Unified resource management script.

This script provides a single entry point for all resource management operations:
- Download character models from Sketchfab
- Convert models to BAM format
- Manage character manifests
- Clean up resources

Usage:
    python unified_resource_manager.py download --batch-size 3
    python unified_resource_manager.py convert --characters kyo_kusanagi
    python unified_resource_manager.py clean --dry-run
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.batch_character_downloader import BatchCharacterDownloader

logger = logging.getLogger("unified_resource_manager")


class UnifiedResourceManager:
    """Unified resource management for StreetBattle character assets."""
    
    def __init__(self):
        self.assets_dir = PROJECT_ROOT / "assets"
        self.characters_dir = self.assets_dir / "characters"
        self.downloads_dir = self.assets_dir / "downloads"
        self.manifest_path = self.assets_dir / "characters_manifest.json"
        self.catalog_path = self.assets_dir / "resource_catalog.json"
        
        self.downloader = BatchCharacterDownloader(self.assets_dir)
    
    def download_characters(self, characters: Optional[List[str]] = None, batch_size: int = 3, dry_run: bool = False):
        """Download character resources in batches."""
        logger.info("=== CHARACTER DOWNLOAD PHASE ===")
        
        catalog = self.downloader.load_catalog()
        all_characters = self.downloader.get_character_list(catalog)
        
        if characters:
            characters = [c for c in characters if c in all_characters]
        else:
            characters = all_characters
        
        logger.info(f"Processing {len(characters)} characters in batches of {batch_size}")
        
        if dry_run:
            logger.info("DRY RUN - Would download:")
            for char in characters:
                uid = catalog[char]['sketchfab']['uid']
                logger.info(f"  - {char}: {uid}")
            return
        
        self.downloader.download_batch(characters, batch_size)
    
    def convert_existing_downloads(self, characters: Optional[List[str]] = None):
        """Convert already downloaded archives to BAM format."""
        logger.info("=== CONVERSION PHASE ===")
        
        if not self.downloads_dir.exists():
            logger.warning("Downloads directory not found")
            return
        
        archive_files = list(self.downloads_dir.glob("*.zip"))
        if not archive_files:
            logger.warning("No archive files found in downloads directory")
            return
        
        converted_count = 0
        for archive_path in archive_files:
            character_id = archive_path.stem
            
            if characters and character_id not in characters:
                continue
            
            if self.downloader.convert_character(character_id, archive_path):
                converted_count += 1
        
        logger.info(f"Converted {converted_count} characters")
    
    def clean_resources(self, dry_run: bool = False):
        """Clean up resource directories."""
        logger.info("=== CLEANUP PHASE ===")
        
        targets = [self.characters_dir, self.downloads_dir]
        
        for target in targets:
            if not target.exists():
                continue
            
            if dry_run:
                logger.info(f"[DRY RUN] Would clean: {target}")
                continue
            
            for item in target.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    logger.info(f"Removed directory: {item}")
                elif item.is_file():
                    item.unlink()
                    logger.info(f"Removed file: {item}")
        
        # Recreate directories
        if not dry_run:
            self.characters_dir.mkdir(parents=True, exist_ok=True)
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    def update_manifest(self):
        """Update character manifest with available resources."""
        logger.info("=== MANIFEST UPDATE ===")
        
        if not self.characters_dir.exists():
            logger.warning("Characters directory not found")
            return
        
        manifest = {
            "characters": [],
            "last_updated": "2025-09-28",
            "total_count": 0
        }
        
        for char_dir in self.characters_dir.iterdir():
            if not char_dir.is_dir():
                continue
            
            char_id = char_dir.name
            sketchfab_dir = char_dir / "sketchfab"
            
            if not sketchfab_dir.exists():
                continue
            
            # Check for BAM file
            bam_file = sketchfab_dir / f"{char_id}.bam"
            animations_dir = sketchfab_dir / "animations"
            
            char_entry = {
                "id": char_id,
                "name": char_id.replace("_", " ").title(),
                "has_model": bam_file.exists(),
                "has_animations": animations_dir.exists() and any(animations_dir.glob("*.bam")),
                "model_path": f"characters/{char_id}/sketchfab/{char_id}.bam" if bam_file.exists() else None,
                "animations_path": f"characters/{char_id}/sketchfab/animations/" if animations_dir.exists() else None
            }
            
            manifest["characters"].append(char_entry)
        
        manifest["total_count"] = len(manifest["characters"])
        
        # Save manifest
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated manifest with {manifest['total_count']} characters")
        logger.info(f"Manifest saved to: {self.manifest_path}")
    
    def status(self):
        """Show current resource status."""
        logger.info("=== RESOURCE STATUS ===")
        
        # Check catalog
        if self.catalog_path.exists():
            catalog = self.downloader.load_catalog()
            logger.info(f"Catalog: {len(catalog)} characters defined")
        else:
            logger.warning("Catalog not found")
            return
        
        # Check downloads
        download_count = len(list(self.downloads_dir.glob("*.zip"))) if self.downloads_dir.exists() else 0
        logger.info(f"Downloads: {download_count} archives available")
        
        # Check converted characters
        converted_count = 0
        if self.characters_dir.exists():
            for char_dir in self.characters_dir.iterdir():
                if char_dir.is_dir():
                    bam_file = char_dir / "sketchfab" / f"{char_dir.name}.bam"
                    if bam_file.exists():
                        converted_count += 1
        
        logger.info(f"Converted: {converted_count} characters ready")
        
        # Show progress
        total_chars = len(catalog)
        progress = (converted_count / total_chars) * 100 if total_chars > 0 else 0
        logger.info(f"Progress: {progress:.1f}% ({converted_count}/{total_chars})")


def main():
    parser = argparse.ArgumentParser(description="Unified resource management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download character resources")
    download_parser.add_argument("--characters", nargs="*", help="Specific characters to download")
    download_parser.add_argument("--batch-size", type=int, default=3, help="Batch size (default: 3)")
    download_parser.add_argument("--dry-run", action="store_true", help="Preview operations")
    
    # Convert command  
    convert_parser = subparsers.add_parser("convert", help="Convert downloaded archives")
    convert_parser.add_argument("--characters", nargs="*", help="Specific characters to convert")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean resource directories")
    clean_parser.add_argument("--dry-run", action="store_true", help="Preview cleanup")
    
    # Status command
    subparsers.add_parser("status", help="Show resource status")
    
    # Manifest command
    subparsers.add_parser("manifest", help="Update character manifest")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Create manager
    manager = UnifiedResourceManager()
    
    try:
        if args.command == "download":
            manager.download_characters(
                characters=args.characters,
                batch_size=args.batch_size,
                dry_run=args.dry_run
            )
        elif args.command == "convert":
            manager.convert_existing_downloads(characters=args.characters)
        elif args.command == "clean":
            manager.clean_resources(dry_run=args.dry_run)
        elif args.command == "status":
            manager.status()
        elif args.command == "manifest":
            manager.update_manifest()
    
    except Exception as e:
        logger.error(f"Command failed: {e}")


if __name__ == "__main__":
    main()