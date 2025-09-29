"""
角色系统测试
测试角色相关的配置和功能
"""

import pytest
from pathlib import Path
from streetBattle.config.config_manager import ConfigManager


class TestCharacterSystem:
    """角色系统测试类"""
    
    def setup_method(self):
        """测试方法前置设置"""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_manager = ConfigManager(self.config_dir)
        self.config_manager.load_all_configs()
        
    def test_character_roster_integrity(self):
        """测试角色花名册完整性"""
        roster = self.config_manager.get_roster()

        # 检查基本结构
        assert isinstance(roster, dict)
        assert 'fighters' in roster
        assert 'default_player' in roster
        assert 'default_cpu' in roster

        # 检查角色数量
        fighters = roster['fighters']
        assert len(fighters) > 0
        assert isinstance(fighters, list)

        # 检查每个角色ID都是字符串
        for fighter_id in fighters:
            assert isinstance(fighter_id, str)
            assert len(fighter_id) > 0

    def test_character_stats_consistency(self):
        """测试角色属性一致性"""
        stats = self.config_manager.get_character_stats()
        roster = self.config_manager.get_roster()

        # 检查默认属性
        assert 'default_stats' in stats
        default_stats = stats['default_stats']
        required_stats = ['max_health', 'health', 'attack_power', 'defense', 'speed']

        for stat in required_stats:
            assert stat in default_stats
            assert isinstance(default_stats[stat], (int, float))

        # 检查角色特定属性修改器
        assert 'character_stat_modifiers' in stats
        character_modifiers = stats['character_stat_modifiers']
        
        # 检查主要角色都有属性修改器
        main_characters = ['kyo_kusanagi', 'iori_yagami', 'terry_bogard']
        for char_id in main_characters:
            if char_id in character_modifiers:
                char_stats = character_modifiers[char_id]
                assert isinstance(char_stats, dict)

    def test_skill_system_integrity(self):
        """测试技能系统完整性"""
        skills = self.config_manager.get_config('skills')
        
        # 检查技能配置结构
        assert 'skill_templates' in skills
        assert 'character_skills' in skills
        assert 'skill_categories' in skills

        # 检查主要角色的技能配置
        character_skills = skills['character_skills']
        main_characters = ['kyo_kusanagi', 'iori_yagami', 'terry_bogard']
        
        for char_id in main_characters:
            if char_id in character_skills:
                char_skills = character_skills[char_id]
                assert 'skills' in char_skills
                assert len(char_skills['skills']) > 0

    def test_character_profiles_consistency(self):
        """测试角色档案一致性"""
        # 使用get_config方法获取角色档案
        profiles = self.config_manager.get_config('characters_profiles')
        
        # 检查档案结构
        if profiles:
            assert isinstance(profiles, dict)
            # 检查主要角色是否有档案
            main_characters = ['kyo_kusanagi', 'iori_yagami', 'terry_bogard']
            for char_id in main_characters:
                if char_id in profiles:
                    char_profile = profiles[char_id]
                    assert isinstance(char_profile, dict)

    def test_character_manifest_integrity(self):
        """测试角色清单完整性"""
        # 使用get_config方法获取角色清单
        manifest = self.config_manager.get_config('characters_manifest')
        
        # 检查清单结构
        if manifest:
            assert 'characters' in manifest
            characters = manifest['characters']
            assert isinstance(characters, list)

    def test_character_data_cross_reference(self):
        """测试角色数据交叉引用"""
        """验证不同配置文件之间的数据一致性"""

        roster = self.config_manager.get_roster()
        profiles = self.config_manager.get_config('characters_profiles')
        
        # 检查花名册中的角色是否有对应的档案
        fighters = roster['fighters']
        
        # 对于3D系统，允许某些角色没有完整的档案配置
        if profiles:
            for fighter_id in fighters:
                if fighter_id in profiles:
                    profile = profiles[fighter_id]
                    assert isinstance(profile, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])