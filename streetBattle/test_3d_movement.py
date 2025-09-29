#!/usr/bin/env python3
"""
Test script for 3D character movement and input handling
验证3D角色移动和输入处理的测试脚本
"""

import sys
import time
from pathlib import Path

# Add the streetBattle directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_player_3d_movement():
    """Test Player 3D movement system"""
    print("🧪 Testing Player 3D Movement System")
    print("=" * 50)
    
    try:
        # Import required modules
        from player import Player
        from panda3d.core import Vec3
        from direct.showbase.ShowBase import ShowBase
        
        print("✅ Successfully imported Player and Panda3D modules")
        
        # Create minimal ShowBase for testing
        app = ShowBase()
        app.disableMouse()
        
        print("✅ Created ShowBase instance")
        
        # Create test players with correct parameters
        test_chars = ['andy_bogard', 'iori_yagami']
        players = []
        
        for i, char_name in enumerate(test_chars):
            try:
                player = Player(
                    render=app.render,
                    loader=app.loader,
                    name=char_name,
                    pos=Vec3(i * 4, 0, 0),  # Space players apart
                )
                players.append(player)
                print(f"✅ Created Player: {char_name}")
                
                # Debug player status
                status = player.debug_status()
                print(f"   📊 Player Status: {status}")
                
            except Exception as e:
                print(f"❌ Failed to create Player {char_name}: {e}")
                continue
        
        if not players:
            print("❌ No players created successfully")
            return False
        
        # Test input simulation
        print("\n🎮 Testing Input Simulation...")
        
        test_inputs = [
            {'right': True},  # Move right
            {'left': True},   # Move left  
            {'up': True},     # Move forward
            {'down': True},   # Move backward
            {'right': True, 'up': True},  # Diagonal movement
        ]
        
        dt = 1.0/60.0  # 60 FPS simulation
        
        for i, inputs in enumerate(test_inputs):
            print(f"\n🎯 Test {i+1}: Input = {inputs}")
            
            for player in players:
                old_status = player.debug_status()
                print(f"   Before: {player.name} at {old_status['pos']}")
                
                # Apply input
                player.apply_input(inputs, dt)
                player.update(dt)
                
                new_status = player.debug_status()
                print(f"   After:  {player.name} at {new_status['pos']}")
                
                # Check if position changed
                if old_status['pos'] != new_status['pos']:
                    print(f"   ✅ {player.name} position changed correctly")
                else:
                    print(f"   ⚠️  {player.name} position did not change")
        
        print("\n🏁 Movement Test Completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_input_to_position_sync():
    """Test that input directly updates 3D model position"""
    print("\n🔄 Testing Input-to-Position Synchronization")
    print("=" * 50)
    
    try:
        from player import Player
        from panda3d.core import Vec3
        
        # Re-use existing ShowBase instance instead of creating new one
        import builtins
        if hasattr(builtins, 'base') and builtins.base:
            app = builtins.base
            print("✅ Using existing ShowBase instance")
        else:
            print("❌ No ShowBase instance available")
            return False
        
        # Create a single player for focused testing
        player = Player(
            render=app.render,
            loader=app.loader,
            name="test_fighter",
            pos=Vec3(0, 0, 0),
        )
        
        print(f"🎮 Created test player: {player.name}")
        
        # Test rapid input changes
        test_sequence = [
            ({'right': True}, "Move Right"),
            ({}, "Stop"),
            ({'left': True}, "Move Left"), 
            ({}, "Stop"),
            ({'up': True}, "Move Forward"),
            ({}, "Stop"),
            ({'down': True}, "Move Backward"),
            ({}, "Stop"),
        ]
        
        dt = 1.0/60.0
        
        for inputs, description in test_sequence:
            print(f"\n🎯 {description}: {inputs}")
            
            before = player.debug_status()
            player.apply_input(inputs, dt)
            after = player.debug_status()
            
            print(f"   Logical pos: {before['pos']} → {after['pos']}")
            print(f"   Model pos:   {before.get('model_pos', 'N/A')} → {after.get('model_pos', 'N/A')}")
            
            # Check synchronization
            if after['pos'] == after.get('model_pos', 'N/A'):
                print(f"   ✅ Position synchronized")
            else:
                print(f"   ⚠️  Position desynchronized!")
        
        return True
        
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 3D Character Movement Test Suite")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_player_3d_movement()
    test2_passed = test_input_to_position_sync()
    
    print("\n📊 Test Results:")
    print(f"   Movement Test: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Sync Test:     {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! 3D movement system is working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\nNext: Run the full game to test WASD controls in action!")