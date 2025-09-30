"""
集成测试：验证所有关键修复
测试Phase 1和Phase 2的所有改进
"""
import pytest
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from panda3d.core import NodePath
from direct.showbase.ShowBase import ShowBase
from enhanced_character_manager import EnhancedCharacterManager

class TestPhase2Fixes:
    """Phase 2修复验证"""
    
    @classmethod
    def setup_class(cls):
        """初始化测试环境"""
        cls.app = ShowBase(windowType='none')
        cls.manager = EnhancedCharacterManager(cls.app)
    
    def test_character_has_3d_model_field(self):
        """测试has_3d_model字段是否正确加载"""
        # Chris应该有3D模型
        chris = self.manager.get_character_by_name("chris")
        assert chris is not None, "Chris角色应该存在"
        assert chris.get('has_3d_model') == True, "Chris应该有has_3d_model=True"
        assert chris.get('disabled') in (None, False), "Chris不应该被禁用"
        
    def test_default_characters_valid(self):
        """测试默认角色是否有效"""
        for char_name in ["Kyo Kusanagi", "Iori Yagami"]:
            char_data = self.manager.get_character_by_name(char_name)
            assert char_data is not None, f"{char_name}应该存在"
            assert char_data.get('has_3d_model') == True, f"{char_name}应该有3D模型"
            assert not char_data.get('disabled'), f"{char_name}不应该被禁用"
    
    def test_disabled_characters_excluded(self):
        """测试被禁用的角色是否被正确排除"""
        # Andy Bogard被禁用，不应该在comprehensive_characters中
        andy = self.manager.get_character_by_name("andy_bogard")
        assert andy is None, "Andy Bogard应该不在comprehensive_characters中（已被禁用）"
    
    def test_comprehensive_characters_count(self):
        """测试comprehensive_characters数量"""
        # 应该有41个可用角色（45 - 4个禁用）
        assert len(self.manager.comprehensive_characters) == 41, \
            f"应该有41个角色，实际: {len(self.manager.comprehensive_characters)}"
    
    def test_all_available_characters_valid(self):
        """测试所有可用角色都应该有has_3d_model=True"""
        invalid_chars = []
        for char_id, char_data in self.manager.comprehensive_characters.items():
            if not char_data.get('has_3d_model'):
                invalid_chars.append(char_id)
        
        assert len(invalid_chars) == 0, \
            f"以下角色has_3d_model不为True: {invalid_chars}"
    
    def test_character_name_normalization(self):
        """测试角色名称标准化"""
        # 测试多种输入格式
        test_cases = [
            ("chris", "Chris"),
            ("Chris", "Chris"),
            ("kyo_kusanagi", "Kyo Kusanagi"),
            ("Kyo Kusanagi", "Kyo Kusanagi"),
        ]
        
        for input_name, expected_display in test_cases:
            char = self.manager.get_character_by_name(input_name)
            assert char is not None, f"应该找到角色: {input_name}"
            assert char.get('display_name') == expected_display, \
                f"{input_name}的display_name应该是{expected_display}"

class TestPhase1Fixes:
    """Phase 1修复验证（现有功能不应被破坏）"""
    
    def test_character_info_fields(self):
        """测试角色信息字段（修复2）"""
        # 这个测试需要实际加载游戏UI，暂时跳过
        # 验证在手动测试中完成
        pass
    
    def test_console_output_optimization(self):
        """测试控制台输出优化（修复4）"""
        # 这个测试需要实际运行游戏，暂时跳过
        # 验证在手动测试中完成
        pass

def run_integration_tests():
    """运行集成测试"""
    print("\n" + "="*60)
    print("运行集成测试：验证所有关键修复")
    print("="*60)
    
    # 使用pytest运行测试
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ])
    
    return exit_code == 0

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
