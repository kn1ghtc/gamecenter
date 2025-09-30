"""
3D角色模型和动画验证测试脚本
Test Script for 3D Character Models and Animations

此脚本验证所有42个KOF角色的3D模型和动画系统是否正常工作
This script verifies that all 42 KOF characters' 3D models and animation systems work correctly
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, loadPrcFileData

# Configure Panda3D for headless testing
loadPrcFileData("", "window-type none")  # No window for automated testing
loadPrcFileData("", "audio-library-name null")  # No audio

class CharacterModelTester(ShowBase):
    """测试3D角色模型加载和动画系统"""
    
    def __init__(self):
        super().__init__()
        
        print("=" * 80)
        print("3D角色模型和动画验证测试")
        print("=" * 80)
        
        # Initialize character manager
        from gamecenter.streetBattle.enhanced_character_manager import EnhancedCharacterManager
        self.char_manager = EnhancedCharacterManager(self)
        
        # Test results
        self.test_results = {
            'total_characters': 0,
            'successful_loads': 0,
            'failed_loads': 0,
            'characters_with_animations': 0,
            'characters_without_animations': 0,
            'detailed_results': []
        }
        
        self.run_tests()
    
    def run_tests(self):
        """运行所有角色的测试"""
        all_characters = self.char_manager.get_all_character_names()
        self.test_results['total_characters'] = len(all_characters)
        
        print(f"\\n开始测试 {len(all_characters)} 个角色...")
        print("-" * 80)
        
        for i, char_name in enumerate(all_characters, 1):
            print(f"\\n[{i}/{len(all_characters)}] 测试角色: {char_name}")
            result = self.test_character(char_name)
            self.test_results['detailed_results'].append(result)
            
            # Update statistics
            if result['model_loaded']:
                self.test_results['successful_loads'] += 1
            else:
                self.test_results['failed_loads'] += 1
            
            if result['has_animations']:
                self.test_results['characters_with_animations'] += 1
            else:
                self.test_results['characters_without_animations'] += 1
        
        # Print summary
        self.print_summary()
        
        # Save results to JSON
        self.save_results()
    
    def test_character(self, char_name: str) -> dict:
        """测试单个角色的模型和动画"""
        result = {
            'character_name': char_name,
            'model_loaded': False,
            'has_animations': False,
            'animation_count': 0,
            'animations': [],
            'model_type': None,
            'errors': []
        }
        
        try:
            # Attempt to load model
            model = self.char_manager.create_character_model(char_name, Vec3(0, 0, 0))
            
            if model:
                result['model_loaded'] = True
                print(f"  ✅ 模型加载成功")
                
                # Determine model type
                from direct.actor.Actor import Actor
                if isinstance(model, Actor):
                    result['model_type'] = "Actor"
                    
                    # Check for animations
                    try:
                        anims = list(model.getAnimNames())
                        if anims:
                            result['has_animations'] = True
                            result['animation_count'] = len(anims)
                            result['animations'] = anims
                            print(f"  ✅ Actor模型，包含 {len(anims)} 个动画: {anims}")
                        else:
                            print(f"  ⚠️  Actor模型，但没有动画")
                    except Exception as e:
                        result['errors'].append(f"动画检测失败: {str(e)}")
                        print(f"  ❌ 动画检测失败: {e}")
                else:
                    result['model_type'] = "NodePath"
                    print(f"  ⚠️  模型类型为NodePath（非Actor），无动画支持")
                
                # Test model visibility
                try:
                    bounds = model.getTightBounds()
                    if bounds:
                        min_p, max_p = bounds
                        size = max_p - min_p
                        print(f"  📏 模型尺寸: {size}")
                    else:
                        print(f"  ⚠️  无法获取模型边界")
                        result['errors'].append("无法获取模型边界")
                except Exception as e:
                    result['errors'].append(f"边界检测失败: {str(e)}")
                    print(f"  ❌ 边界检测失败: {e}")
                
                # Cleanup model
                try:
                    if hasattr(model, 'cleanup'):
                        model.cleanup()
                    model.removeNode()
                except Exception as e:
                    result['errors'].append(f"模型清理失败: {str(e)}")
                    print(f"  ⚠️  模型清理警告: {e}")
            else:
                print(f"  ❌ 模型加载失败")
                result['errors'].append("模型加载失败")
        
        except Exception as e:
            result['errors'].append(f"测试异常: {str(e)}")
            print(f"  ❌ 测试异常: {e}")
        
        return result
    
    def print_summary(self):
        """打印测试摘要"""
        print("\\n" + "=" * 80)
        print("测试摘要")
        print("=" * 80)
        
        total = self.test_results['total_characters']
        success = self.test_results['successful_loads']
        failed = self.test_results['failed_loads']
        with_anims = self.test_results['characters_with_animations']
        without_anims = self.test_results['characters_without_animations']
        
        print(f"\\n总角色数: {total}")
        print(f"成功加载: {success} ({success/total*100:.1f}%)")
        print(f"加载失败: {failed} ({failed/total*100:.1f}%)")
        print(f"\\n有动画: {with_anims} ({with_anims/total*100:.1f}%)")
        print(f"无动画: {without_anims} ({without_anims/total*100:.1f}%)")
        
        # List failed characters
        if failed > 0:
            print(f"\\n❌ 加载失败的角色:")
            for result in self.test_results['detailed_results']:
                if not result['model_loaded']:
                    print(f"  - {result['character_name']}")
                    if result['errors']:
                        for error in result['errors']:
                            print(f"    • {error}")
        
        # List characters without animations
        if without_anims > 0:
            print(f"\\n⚠️  没有动画的角色:")
            for result in self.test_results['detailed_results']:
                if result['model_loaded'] and not result['has_animations']:
                    print(f"  - {result['character_name']} ({result['model_type']})")
        
        # List characters with most animations
        print(f"\\n🎭 动画最多的角色 (Top 5):")
        sorted_by_anims = sorted(
            [r for r in self.test_results['detailed_results'] if r['animation_count'] > 0],
            key=lambda x: x['animation_count'],
            reverse=True
        )[:5]
        for result in sorted_by_anims:
            print(f"  - {result['character_name']}: {result['animation_count']} 个动画")
    
    def save_results(self):
        """保存测试结果到JSON文件"""
        output_file = Path(__file__).parent / "tests" / "character_model_test_results.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\\n💾 测试结果已保存到: {output_file}")


def main():
    """主测试入口"""
    try:
        tester = CharacterModelTester()
        print("\\n✅ 测试完成！")
        return 0
    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
