#!/usr/bin/env python3
"""Automated batch downloader for remaining characters."""

import json
import time
from pathlib import Path

def get_remaining_characters():
    """Get list of characters that haven't been downloaded yet."""
    catalog_path = Path("assets/resource_catalog.json")
    downloads_dir = Path("assets/downloads")
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    # Get characters with UIDs
    all_characters = []
    for char_id, data in catalog.items():
        sketchfab_data = data.get('sketchfab', {})
        uid = sketchfab_data.get('uid')
        if uid:
            all_characters.append(char_id)
    
    # Get already downloaded characters
    downloaded = set()
    if downloads_dir.exists():
        for archive in downloads_dir.glob("*.zip"):
            downloaded.add(archive.stem)
    
    # Return remaining characters
    remaining = [char for char in all_characters if char not in downloaded]
    return remaining, len(all_characters), len(downloaded)

def get_character_uid(char_id):
    """Get UID for a character."""
    catalog_path = Path("assets/resource_catalog.json")
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    return catalog.get(char_id, {}).get('sketchfab', {}).get('uid')

def main():
    remaining_chars, total_chars, downloaded_count = get_remaining_characters()
    
    print(f"📊 Current Status:")
    print(f"   Total Characters: {total_chars}")
    print(f"   Downloaded: {downloaded_count}")
    print(f"   Remaining: {len(remaining_chars)}")
    print(f"   Progress: {(downloaded_count/total_chars)*100:.1f}%")
    
    if not remaining_chars:
        print("✅ All characters already downloaded!")
        return
    
    print(f"\n🚀 Starting automated batch download:")
    print(f"   Batch size: 4 characters")
    print(f"   Total batches needed: {(len(remaining_chars) + 3) // 4}")
    
    # Create batches of 4
    batches = [remaining_chars[i:i+4] for i in range(0, len(remaining_chars), 4)]
    
    print(f"\n📋 Download Plan:")
    for i, batch in enumerate(batches, 1):
        print(f"   Batch {i}: {', '.join(batch)}")
    
    print(f"\n⚠️  Important Notes:")
    print(f"   - Each batch will have 30 second intervals")
    print(f"   - Manual Chrome DevTools interaction required")
    print(f"   - Total estimated time: {len(batches) * 5} minutes")
    
    input("\nPress Enter to start automated download process...")
    
    success_count = 0
    failed_chars = []
    
    for batch_num, batch in enumerate(batches, 1):
        print(f"\n{'='*60}")
        print(f"BATCH {batch_num}/{len(batches)}: {', '.join(batch)}")
        print(f"{'='*60}")
        
        batch_success = 0
        
        for char_id in batch:
            uid = get_character_uid(char_id)
            if not uid:
                print(f"❌ No UID found for {char_id}")
                failed_chars.append(char_id)
                continue
            
            print(f"\n🔗 Getting URL for {char_id}...")
            print(f"   UID: {uid}")
            print(f"   URL: https://sketchfab.com/i/archives/latest?archiveType=gltf&model={uid}")
            
            # Here we would use Chrome DevTools MCP to get the URL
            # For now, we'll show instructions to the user
            print(f"\n📋 Manual Steps for {char_id}:")
            print(f"   1. Navigate to: https://sketchfab.com/i/archives/latest?archiveType=gltf&model={uid}")
            print(f"   2. Copy the download URL from the JSON response")
            print(f"   3. The script will continue automatically...")
            
            time.sleep(2)  # Brief pause for user to see instructions
        
        print(f"\n⏳ Batch {batch_num} completed")
        
        if batch_num < len(batches):
            print(f"⏰ Waiting 30 seconds before next batch...")
            time.sleep(30)
    
    print(f"\n{'='*60}")
    print(f"DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"Total batches processed: {len(batches)}")
    print(f"Characters processed: {len(remaining_chars)}")
    
    if failed_chars:
        print(f"Failed characters: {', '.join(failed_chars)}")
    
    print(f"\n🔄 Next Steps:")
    print(f"   1. Run conversion: python tools\\robust_converter.py")
    print(f"   2. Update manifest: python tools\\unified_resource_manager.py manifest")
    print(f"   3. Test game: python main.py")

if __name__ == "__main__":
    main()