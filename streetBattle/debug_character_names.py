"""
Debug script to check character names and identify "Street Fighter Unknown" source
"""

import sys
import os
import json
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_character_manager import EnhancedCharacterManager

def debug_character_names():
    """Debug character name mappings"""
    print("🔍 Debugging Character Names...")
    
    # Mock base_app for testing
    class MockApp:
        def __init__(self):
            self.render = None
            self.loader = None
    
    mock_app = MockApp()
    
    # Initialize character manager
    char_manager = EnhancedCharacterManager(mock_app)
    
    print(f"\n📊 Character Manager Stats:")
    print(f"  - Comprehensive characters: {len(char_manager.comprehensive_characters)}")
    print(f"  - Characters data: {len(char_manager.characters_data)}")
    print(f"  - Unified roster: {len(char_manager.unified_roster)}")
    
    # Test get_random_character 10 times
    print(f"\n🎲 Random Character Tests:")
    for i in range(10):
        random_char = char_manager.get_random_character()
        print(f"  {i+1}. {random_char}")
        if "Unknown" in random_char:
            print(f"    ⚠️  Found Unknown character: {random_char}")
    
    # Check for "Street Fighter Unknown" or "Unknown" in data
    print(f"\n🔍 Checking for 'Unknown' entries:")
    
    # Check comprehensive_characters
    if char_manager.comprehensive_characters:
        print(f"\n📁 Comprehensive Characters ({len(char_manager.comprehensive_characters)}):")
        unknown_count = 0
        for char_id, char_data in char_manager.comprehensive_characters.items():
            char_name = char_data.get('name', char_id)
            if 'unknown' in char_name.lower() or 'unknown' in char_id.lower():
                print(f"  ❌ UNKNOWN: {char_id} -> {char_name}")
                unknown_count += 1
        
        if unknown_count == 0:
            print(f"  ✅ No 'Unknown' entries found in comprehensive_characters")
        
        # Show first 5 entries for reference
        print(f"\n📝 Sample entries:")
        for i, (char_id, char_data) in enumerate(list(char_manager.comprehensive_characters.items())[:5]):
            char_name = char_data.get('name', char_id)
            print(f"  {i+1}. {char_id} -> {char_name}")
    
    # Check characters_data
    if char_manager.characters_data:
        print(f"\n📁 Characters Data ({len(char_manager.characters_data)}):")
        unknown_count = 0
        for char_name in char_manager.characters_data.keys():
            if 'unknown' in char_name.lower():
                print(f"  ❌ UNKNOWN: {char_name}")
                unknown_count += 1
        
        if unknown_count == 0:
            print(f"  ✅ No 'Unknown' entries found in characters_data")
    
    # Check unified_roster
    if char_manager.unified_roster:
        print(f"\n📁 Unified Roster ({len(char_manager.unified_roster)}):")
        unknown_count = 0
        for char_id, char_data in char_manager.unified_roster.items():
            display_name = char_data.get('display_name', char_id)
            if 'unknown' in display_name.lower() or 'unknown' in char_id.lower():
                print(f"  ❌ UNKNOWN: {char_id} -> {display_name}")
                unknown_count += 1
        
        if unknown_count == 0:
            print(f"  ✅ No 'Unknown' entries found in unified_roster")
    
    # Check the specific files for debugging
    print(f"\n📂 Checking data files:")
    data_dirs = [".", "data", "assets", "config"]
    for data_dir in data_dirs:
        data_path = Path(__file__).parent / data_dir
        if data_path.exists():
            json_files = list(data_path.glob("*.json"))
            print(f"  📁 {data_dir}/: {len(json_files)} JSON files")
            for json_file in json_files:
                if any(keyword in json_file.name.lower() for keyword in ['character', 'roster', 'manifest']):
                    print(f"    📄 {json_file.name}")

if __name__ == "__main__":
    debug_character_names()