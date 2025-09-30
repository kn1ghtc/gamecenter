"""
Script to test and fix duplicate 3D model display issue
"""

import sys
import os
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

def test_duplicate_models():
    """Test for duplicate model creation and display"""
    print("🔍 Testing for duplicate 3D model issues...")
    
    # Mock base_app for testing
    class MockApp:
        def __init__(self):
            self.render = None
            self.loader = None
    
    mock_app = MockApp()
    
    # Initialize character manager
    from enhanced_character_manager import EnhancedCharacterManager
    char_manager = EnhancedCharacterManager(mock_app)
    
    print(f"\n📊 Initial state:")
    print(f"  - Cached models: {len(char_manager.character_models)}")
    
    # Test creating the same character multiple times
    test_char = "Kyo Kusanagi"
    from panda3d.core import Vec3
    
    print(f"\n🔄 Testing multiple creation of {test_char}:")
    
    for i in range(3):
        print(f"  Attempt {i+1}:")
        model = char_manager.create_character_model(test_char, Vec3(i, 0, 0))
        print(f"    Created model: {model is not None}")
        print(f"    Cached models: {len(char_manager.character_models)}")
        print(f"    Model cache keys: {list(char_manager.character_models.keys())}")
        
        if model:
            # Check if model is already in scene (cached)
            if test_char in char_manager.character_models:
                cached_model = char_manager.character_models[test_char]
                is_same = model == cached_model
                print(f"    Same as cached: {is_same}")
                if not is_same:
                    print(f"    ⚠️  DIFFERENT MODEL INSTANCES!")
    
    # Test fix: Clear character models cache
    print(f"\n🧹 Testing cache clearing:")
    char_manager.clear_character_models()
    print(f"  Models after clearing: {len(char_manager.character_models)}")

def test_scene_cleanup():
    """Test scene cleanup to remove duplicate models"""
    print("\n🎯 Testing scene cleanup for duplicate models...")
    
    # This would require actual Panda3D scene access
    # For now, just document the approach
    cleanup_instructions = """
    Scene cleanup approach for duplicate models:
    
    1. Before starting battle:
       - Call char_manager.clear_character_models()
       - Call render.findAllMatches("**/*_placeholder").removeNode()
       - Call render.findAllMatches("**/*3d_model*").removeNode()
    
    2. During Player creation:
       - Check if model already exists in scene
       - Remove existing instance before creating new one
       - Use unique naming for each Player's model
    
    3. After battle:
       - Clean up all character models
       - Reset character manager state
    """
    
    print(cleanup_instructions)

if __name__ == "__main__":
    test_duplicate_models()
    test_scene_cleanup()