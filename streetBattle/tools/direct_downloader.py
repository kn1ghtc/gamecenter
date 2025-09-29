#!/usr/bin/env python3
"""Manual batch downloader using direct URLs."""

import json
import time
import requests
import sys
from pathlib import Path

def download_from_url(character_id: str, download_url: str, output_dir: Path):
    """Download character from direct URL."""
    
    output_path = output_dir / f"{character_id}.zip"
    
    print(f"Downloading {character_id}...")
    
    try:
        response = requests.get(download_url, stream=True, timeout=300)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✅ Downloaded {character_id}: {size_mb:.1f}MB")
            return True
        else:
            print(f"❌ Download failed for {character_id}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading {character_id}: {e}")
        return False

def main():
    downloads_dir = Path("assets/downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for command line arguments
    if len(sys.argv) == 3:
        character_id = sys.argv[1]
        download_url = sys.argv[2]
        
        print(f"Downloading single character: {character_id}")
        success = download_from_url(character_id, download_url, downloads_dir)
        print(f"\n✅ Downloaded {1 if success else 0}/1 characters")
        return
    
    # Default: use built-in URLs from Chrome DevTools
    downloads = [
        {
            "character_id": "joe_higashi",
            "url": "https://sketchfab-prod-media.s3.amazonaws.com/archives/f01423aea435432daa6df4025ef9e215/gltf/a6605f2380fe46059131ea022ae68900/joe_higashi_-_kof_all_stars.zip?AWSAccessKeyId=ASIAZ4EAQ242LR5MMMQW&Signature=l5hFNOuoIlgqWVTiarCKKyhQ%2BHY%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEC8aCWV1LXdlc3QtMSJIMEYCIQDJ9rC5rbh3j2ugAOBM%2FvsSiC8m%2FoIacrnsmeP0WKmpSAIhAM9dn%2FFrVIhKq4q6ooAeKSIzoT28vFmgJhOtLgLc4KVfKrsFCLj%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQABoMNjc4ODc0MzcxODkyIgyXUN5bsTIWx2ZqU6AqjwWNsoVL1bWS7Ac2xgyHRkbh7tjjV89SQCdPuamiRnn71yUrK9vwKg6F1ohhRA9TBeBF3%2FZAl0mGVY7JQQB7jp8qxiPpZBgRkjYRfuRymnw9XKcMADNSTo0X9gTQuW9Ai76ZhQ8y2XX0QK%2FEbYbSKetu047KOwJ%2FIoxzB%2FGMCAopy4VYzWmRBwGWo4%2FtBYHeI4ZQBhT1ilvhKZ3rZde1q2quFXSxhdB5xcX1fpoWfgEBDmY5%2FBg49SlIEcC9sXpGM6A%2BB6moKfVzSvMfqk%2FI3DSCLnapRjoAhhmauBXHEGqPBbWaS2tB4gHkgDrr0RdrF%2B%2BIaEemrAL6yN1%2FG%2BfVAXGY4KaQkFMgiyKjSs6OzqTwW8xjlctYsYYbz3HP4gpuFOMLPz9GTzDr8adn2T9K47TNFBZdd68mXxdqUkIosESExi2lNo6EktFcCxU%2FWwbcWo9un8L9JHfhnurDayrEeqlLCnJTFzz4FJh8PwvJ%2FICzO%2B3xO1Ox1sAmeS7TJW8%2BlNEgWmPgcx1tROXA%2BexnPL4KGHxMR6iYfbfihD9bHWonp9QeYDqbQvI65Zxqap8gc2BMv8mH1kZfQq%2FtO57xgDiawqHb0oKnieltUKtBsWJXQ%2BckRgsPaLyxwf97TnjswM9%2BOTWkHcr0eMvi%2FPX446gUvMP6qm5U75EgcdgXYSj0iFb14KRopQByOkICMadOoAognI%2FhuHu103RqllozFjIs2O1obOLPf4RIBs2iBtz18ueVnTFtXFWMUg5c82zqUutqp3NbtfMnBSjK%2FtQA53v8xlcwnEC6vXsJDah3Ynu3qjG1ivUxnnerSjjNTGsNn%2FSqHInJXKwk2tBD%2BhqBhjq4umpm%2FbdPCvYIcKy3T%2B94MOiq48YGOrABfEpYMHIv52QbqR5fp1IwrTsEcePizgae7klxBjUMFMOj2kUw8FN4r2519Bu%2FkJyqfESGKHhLkfOTsMyvlArsjMHgKh56PsWxHyzx8lltlO%2F35qyDDAl2qv7FOrLIPKZCYPQQVdcRRMbJlYmGicNEYYMKjWH%2FDwI%2BBKHKi5nGBV4ObsgYNbUuNoY1QvCPVDVm8hKMlyaOZvzyvy%2BgwlpWmRdK5nAcbCE4yrBSFZpMyLU%3D&Expires=1759043395"
        }
    ]
    
    success_count = 0
    
    for download in downloads:
        if download_from_url(download["character_id"], download["url"], downloads_dir):
            success_count += 1
        
        time.sleep(2)  # Brief pause between downloads
    
    print(f"\n✅ Downloaded {success_count}/{len(downloads)} characters")

if __name__ == "__main__":
    main()