#!/usr/bin/env python3
"""Unified character resource downloader and converter.

This tool combines Sketchfab authentication, sequential downloading, and GLTF2BAM conversion
to automatically process character resources for the StreetBattle game.

Usage:
    python batch_character_downloader.py --batch-size 5
    python batch_character_downloader.py --characters kyo_kusanagi iori_yagami
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sketchfab_tools.cookie_session import SketchfabCookieSession, SketchfabCookieError
from sketchfab_tools.downloader import SketchfabSequentialDownloader
from sketchfab_tools.conversion import Gltf2BamConverter, ConversionError

logger = logging.getLogger("batch_character_downloader")


class BatchCharacterDownloader:
    """Batch download and convert characters with rate limiting."""
    
    def __init__(self, assets_dir: Path = None):
        self.assets_dir = assets_dir or PROJECT_ROOT / "assets"
        self.catalog_path = self.assets_dir / "resource_catalog.json"
        self.downloads_dir = self.assets_dir / "downloads" 
        self.characters_dir = self.assets_dir / "characters"
        
        # Ensure directories exist
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.characters_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize converter
        self.converter = Gltf2BamConverter()
        
    def load_catalog(self) -> dict:
        """Load character catalog."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Resource catalog not found: {self.catalog_path}")
            
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_character_list(self, catalog: dict) -> List[str]:
        """Get list of characters with Sketchfab UIDs."""
        characters = []
        for char_id, data in catalog.items():
            sketchfab_data = data.get('sketchfab', {})
            if sketchfab_data.get('uid'):
                characters.append(char_id)
        return characters
    
    def download_batch(self, characters: List[str], batch_size: int = 5) -> None:
        """Download characters in batches to avoid rate limiting."""
        logger.info(f"Starting batch download of {len(characters)} characters")
        
        # Split into batches
        batches = [characters[i:i + batch_size] for i in range(0, len(characters), batch_size)]
        
        try:
            # Create session
            session = SketchfabCookieSession(
                env_path=PROJECT_ROOT / ".env.local",
                rate_limit_seconds=5.0
            )
            
            # Create downloader
            downloader = SketchfabSequentialDownloader(
                catalog_path=self.catalog_path,
                download_root=self.downloads_dir,
                cookie_session=session,
                rate_limit_seconds=5.0
            )
            
            total_processed = 0
            
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"Processing batch {batch_num}/{len(batches)}: {', '.join(batch)}")
                
                try:
                    # Download batch
                    summaries = downloader.run(
                        characters=batch,
                        keep_archives=True,
                        update_presigned=True
                    )
                    
                    # Convert downloaded models
                    for summary in summaries:
                        self.convert_character(summary.character_id, summary.archive_path)
                        total_processed += 1
                    
                    logger.info(f"Batch {batch_num} completed: {len(summaries)} characters processed")
                    
                    # Wait between batches to avoid rate limiting
                    if batch_num < len(batches):
                        wait_time = 30  # 30 seconds between batches
                        logger.info(f"Waiting {wait_time} seconds before next batch...")
                        time.sleep(wait_time)
                        
                except Exception as e:
                    logger.error(f"Batch {batch_num} failed: {e}")
                    continue
            
            logger.info(f"Batch download completed: {total_processed}/{len(characters)} characters processed")
            
        except SketchfabCookieError as e:
            logger.error(f"Sketchfab authentication failed: {e}")
            logger.error("Please check your .env.local file and credentials")
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
    
    def convert_character(self, character_id: str, archive_path: Path) -> bool:
        """Convert downloaded character archive to BAM format."""
        try:
            logger.info(f"Converting {character_id} from {archive_path}")
            
            # Create character directory
            char_dir = self.characters_dir / character_id / "sketchfab"
            char_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract and find model file
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(char_dir)
            
            # Find GLTF/GLB file
            model_files = list(char_dir.rglob("*.gltf")) + list(char_dir.rglob("*.glb"))
            if not model_files:
                logger.warning(f"No GLTF/GLB file found for {character_id}")
                return False
            
            model_file = model_files[0]  # Use first found
            
            # Convert to BAM
            bam_path = char_dir / f"{character_id}.bam"
            animations_dir = char_dir / "animations"
            animations_dir.mkdir(exist_ok=True)
            
            result = self.converter.convert(
                source_path=model_file,
                output_path=bam_path,
                animations_dir=animations_dir,
                working_dir=char_dir
            )
            
            logger.info(f"✅ {character_id} converted successfully: {result.bam_path}")
            return True
            
        except ConversionError as e:
            logger.error(f"❌ Conversion failed for {character_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error converting {character_id}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Batch download and convert character resources")
    parser.add_argument(
        "--characters", 
        nargs="*", 
        help="Specific characters to download (default: all)"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=5, 
        help="Number of characters per batch (default: 5)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Preview operations without downloading"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create downloader
    downloader = BatchCharacterDownloader()
    
    try:
        # Load catalog
        catalog = downloader.load_catalog()
        all_characters = downloader.get_character_list(catalog)
        
        # Determine characters to process
        if args.characters:
            characters = [c for c in args.characters if c in all_characters]
            missing = [c for c in args.characters if c not in all_characters]
            if missing:
                logger.warning(f"Characters not found in catalog: {', '.join(missing)}")
        else:
            characters = all_characters
        
        logger.info(f"Found {len(characters)} characters to process")
        
        if args.dry_run:
            logger.info("DRY RUN - Characters that would be processed:")
            for char in characters:
                uid = catalog[char]['sketchfab']['uid']
                logger.info(f"  {char}: {uid}")
            return
        
        # Start batch download
        downloader.download_batch(characters, args.batch_size)
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()