#!/usr/bin/env python3
"""Manual downloader using Chrome DevTools MCP to get presigned URLs."""

import json
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import requests

def download_with_presigned_url(character_id: str, uid: str, output_dir: Path):
    """Download using presigned URL from Sketchfab."""
    
    print(f"Getting presigned URL for {character_id} ({uid})")
    
    # The URL pattern for getting presigned URLs
    url = f"https://sketchfab.com/i/archives/latest?archiveType=gltf&model={uid}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'url' in data:
                download_url = data['url']
                size = data.get('size', 0)
                
                print(f"Found download URL for {character_id}: {size} bytes")
                
                # Download the file
                output_path = output_dir / f"{character_id}.zip"
                
                print(f"Downloading {character_id}...")
                download_response = requests.get(download_url, stream=True, timeout=300)
                
                if download_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"✅ Downloaded {character_id}: {output_path}")
                    return True
                else:
                    print(f"❌ Download failed for {character_id}: HTTP {download_response.status_code}")
                    return False
            else:
                print(f"❌ No download URL found for {character_id}")
                return False
        else:
            print(f"❌ Failed to get presigned URL for {character_id}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading {character_id}: {e}")
        return False

def main():
    # Load catalog
    catalog_path = Path("assets/resource_catalog.json")
    downloads_dir = Path("assets/downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    # Get next batch of characters to download
    target_characters = [
        "terry_bogard",
        "andy_bogard", 
        "joe_higashi"
    ]
    
    print(f"Starting batch download: {', '.join(target_characters)}")
    
    success_count = 0
    
    for char_id in target_characters:
        if char_id not in catalog:
            print(f"❌ {char_id} not found in catalog")
            continue
        
        uid = catalog[char_id].get('sketchfab', {}).get('uid')
        if not uid:
            print(f"❌ No UID found for {char_id}")
            continue
        
        if download_with_presigned_url(char_id, uid, downloads_dir):
            success_count += 1
        
        # Rate limiting - wait between downloads
        if char_id != target_characters[-1]:  # Don't wait after last download
            print("Waiting 5 seconds...")
            time.sleep(5)
    
    print(f"\n✅ Downloaded {success_count}/{len(target_characters)} characters")

if __name__ == "__main__":
    main()