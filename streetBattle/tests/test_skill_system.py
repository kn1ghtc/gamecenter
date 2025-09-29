"""
技能系统单元测试
测试技能配置和技能系统的功能
"""

import pytest
import json
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import ConfigManager


class TestSkillSystem:
    """技能系统测试类"""

    def setup_method(self):
        """测试方法前置设置"""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_manager = ConfigManager(self.config_dir)
        self.config_manager.load_all_configs()

    def test_skills_structure(self):
        """测试技能配置结构完整性"""
        skills_config = self.config_manager.get_config("skills")

        # 检查基本结构
        assert isinstance(skills_config, dict)
        assert 'skill_templates' in skills_config
        assert 'character_skills' in skills_config
        assert 'skill_categories' in skills_config

    def test_skill_templates(self):
        """测试技能模板"""
        skills_config = self.config_manager.get_config("skills")
        templates = skills_config.get('skill_templates', {})

        # 检查技能模板
        assert 'basic_strike' in templates
        assert 'heavy_strike' in templates
        
        # 检查模板结构
        basic_strike = templates['basic_strike']
        assert 'animation' in basic_strike
        assert 'hit_frames' in basic_strike
        assert 'hitstop' in basic_strike

    def test_character_skills(self):
        """测试角色技能配置"""
        skills_config = self.config_manager.get_config("skills")
        character_skills = skills_config.get('character_skills', {})

        # 检查主要角色技能配置
        assert 'kyo_kusanagi' in character_skills
        assert 'iori_yagami' in character_skills
        assert 'terry_bogard' in character_skills

        # 检查技能配置结构
        kyo_skills = character_skills['kyo_kusanagi']
        assert 'default_skill' in kyo_skills
        assert 'input_map' in kyo_skills
        assert 'skills' in kyo_skills

    def test_skill_consistency(self):
        """测试技能配置一致性"""
        skills_config = self.config_manager.get_config("skills")
        character_skills = skills_config.get('character_skills', {})

        # 检查技能名称一致性
        for character_id, skills_data in character_skills.items():
            if 'skills' in skills_data:
                for skill in skills_data['skills']:
                    assert 'name' in skill
                    assert 'damage' in skill
                    assert 'cooldown' in skill

    def test_skill_balance(self):
        """测试技能平衡性"""
        skills_config = self.config_manager.get_config("skills")
        character_skills = skills_config.get('character_skills', {})

        # 检查技能伤害平衡
        damage_values = []
        for character_id, skills_data in character_skills.items():
            if 'skills' in skills_data:
                for skill in skills_data['skills']:
                    if 'damage' in skill:
                        damage_values.append(skill['damage'])

        if damage_values:
            # 检查伤害值在合理范围内
            assert min(damage_values) >= 0
            assert max(damage_values) <= 100  # 假设最大伤害不超过100

    def test_skill_effects(self):
        """测试技能效果"""
        skills_config = self.config_manager.get_config("skills")
        character_skills = skills_config.get('character_skills', {})

        # 检查技能效果配置
        for character_id, skills_data in character_skills.items():
            if 'skills' in skills_data:
                for skill in skills_data['skills']:
                    # 检查基本属性
                    assert isinstance(skill.get('damage', 0), (int, float))
                    assert isinstance(skill.get('cooldown', 0), (int, float))

    def test_skill_uniqueness(self):
        """测试技能唯一性"""
        skills_config = self.config_manager.get_config("skills")
        character_skills = skills_config.get('character_skills', {})

        # 检查技能名称唯一性
        all_skill_names = set()
        for character_id, skills_data in character_skills.items():
            if 'skills' in skills_data:
                for skill in skills_data['skills']:
                    skill_name = skill.get('name')
                    if skill_name:
                        assert skill_name not in all_skill_names, f"技能名称重复: {skill_name}"
                        all_skill_names.add(skill_name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])