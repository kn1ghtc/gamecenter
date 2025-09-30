"""
3D角色验证测试脚本
3D Character Validation Test Script

检查所有42个3D角色的Actor支持和动画集，并生成修复报告
Check all 42 3D characters for Actor support and animation sets, generate fix report
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from panda3d.core import Vec3
from direct.showbase.ShowBase import ShowBase


class Character3DValidator(ShowBase):
    """3D角色验证器"""
    
    def __init__(self):
        print("🔍 启动3D角色验证测试...")
        ShowBase.__init__(self)
        
        # 导入增强角色管理器
        try:
            from gamecenter.streetBattle.enhanced_character_manager import EnhancedCharacterManager
            from gamecenter.streetBattle.enhanced_3d_animation_system import Animation3DManager
            from gamecenter.streetBattle.smart_console import setup_optimized_console, console_info
            
            self.console = setup_optimized_console(quiet_mode=False)
            console_info("角色验证系统初始化", "test")
            
            self.char_manager = EnhancedCharacterManager(self)
            self.animation_manager = Animation3DManager()
            
            # 获取所有角色
            self.all_characters = self.char_manager.comprehensive_characters
            console_info(f"发现 {len(self.all_characters)} 个角色待验证", "test")
            
            # 验证结果
            self.validation_results = {
                'actor_support': {},      # 角色名: True/False
                'animation_support': {},  # 角色名: 动画数量
                'model_issues': {},       # 角色名: 问题描述
                'scaling_info': {},       # 角色名: 缩放信息
                'visibility_issues': []   # 可见性问题角色列表
            }
            
            # 开始验证
            self.validate_all_characters()
            
        except ImportError as e:
            print(f"❌ 导入失败: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            sys.exit(1)
    
    def validate_all_characters(self):
        """验证所有角色"""
        total_chars = len(self.all_characters)
        
        print(f"\n{'='*60}")
        print(f"🎭 开始验证 {total_chars} 个3D角色")
        print(f"{'='*60}")
        
        valid_count = 0
        actor_support_count = 0
        animation_support_count = 0
        
        for i, char_data in enumerate(self.all_characters.values()):
            char_name = char_data.get('name', f'Character_{i}')
            char_id = char_data.get('id', f'unknown_{i}')
            
            print(f"\n[{i+1:2d}/{total_chars}] 验证角色: {char_name} ({char_id})")
            print("-" * 50)
            
            # 验证Actor支持
            actor_result = self.validate_actor_support(char_name, char_id)
            self.validation_results['actor_support'][char_name] = actor_result['success']
            
            if actor_result['success']:
                actor_support_count += 1
                valid_count += 1
                
                # 验证动画支持
                anim_result = self.validate_animation_support(
                    char_name, char_id, actor_result['model']
                )
                self.validation_results['animation_support'][char_name] = anim_result['count']
                
                if anim_result['count'] > 0:
                    animation_support_count += 1
                
                # 验证缩放和可见性
                scale_result = self.validate_scaling_visibility(
                    char_name, actor_result['model']
                )
                self.validation_results['scaling_info'][char_name] = scale_result
                
                # 清理模型
                if actor_result['model']:
                    actor_result['model'].removeNode()
            else:
                self.validation_results['model_issues'][char_name] = actor_result['error']
            
            # 显示进度
            progress = (i + 1) / total_chars * 100
            print(f"进度: {progress:.1f}% ({i+1}/{total_chars})")
        
        # 生成验证报告
        self.generate_validation_report(
            total_chars, valid_count, actor_support_count, animation_support_count
        )
    
    def validate_actor_support(self, char_name, char_id):
        """验证Actor支持"""
        result = {
            'success': False,
            'model': None,
            'error': None,
            'file_path': None
        }
        
        try:
            # 尝试创建角色模型
            model = self.char_manager.create_character_model(char_name, Vec3(0, 0, 0))
            
            if model and not model.isEmpty():
                result['success'] = True
                result['model'] = model
                result['file_path'] = model.getName() if model else "Unknown"
                print(f"  ✅ Actor支持: 成功创建模型")
            else:
                result['error'] = "模型创建失败或为空"
                print(f"  ❌ Actor支持: {result['error']}")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"  ❌ Actor支持: 异常 - {e}")
        
        return result
    
    def validate_animation_support(self, char_name, char_id, model):
        """验证动画支持"""
        result = {
            'count': 0,
            'animations': [],
            'issues': []
        }
        
        try:
            if not model:
                result['issues'].append("模型为空，无法检查动画")
                print(f"  ❌ 动画支持: 模型为空")
                return result
            
            # 检查是否为Actor对象
            from direct.actor.Actor import Actor
            if isinstance(model, Actor):
                # 获取动画列表
                try:
                    anims = model.getAnimNames()
                    result['count'] = len(anims)
                    result['animations'] = list(anims)
                    
                    if result['count'] > 0:
                        print(f"  ✅ 动画支持: {result['count']} 个动画")
                        print(f"    动画列表: {', '.join(anims[:5])}{'...' if len(anims) > 5 else ''}")
                    else:
                        print(f"  ⚠️  动画支持: Actor对象但无动画")
                        result['issues'].append("Actor对象但无可用动画")
                        
                except Exception as e:
                    print(f"  ❌ 动画支持: 获取动画列表失败 - {e}")
                    result['issues'].append(f"获取动画列表失败: {e}")
            else:
                print(f"  ⚠️  动画支持: 非Actor对象，类型: {type(model).__name__}")
                result['issues'].append(f"非Actor对象: {type(model).__name__}")
                
        except Exception as e:
            result['issues'].append(f"验证异常: {e}")
            print(f"  ❌ 动画支持: 验证异常 - {e}")
        
        return result
    
    def validate_scaling_visibility(self, char_name, model):
        """验证缩放和可见性"""
        result = {
            'scale': None,
            'bounds': None,
            'visibility': False,
            'issues': []
        }
        
        try:
            if not model or model.isEmpty():
                result['issues'].append("模型为空或无效")
                print(f"  ❌ 缩放验证: 模型无效")
                return result
            
            # 获取缩放信息
            scale = model.getScale()
            result['scale'] = f"{scale.x:.3f}, {scale.y:.3f}, {scale.z:.3f}"
            
            # 获取边界框信息
            try:
                bounds = model.getTightBounds()
                if bounds:
                    min_p, max_p = bounds
                    size = max_p - min_p
                    result['bounds'] = f"尺寸: {size.x:.2f}×{size.y:.2f}×{size.z:.2f}"
                else:
                    result['bounds'] = "无法获取边界框"
            except:
                result['bounds'] = "边界框计算失败"
            
            # 检查可见性
            result['visibility'] = not model.isHidden()
            
            print(f"  📏 缩放信息: {result['scale']}")
            print(f"  📦 {result['bounds']}")
            print(f"  👁️  可见性: {'正常' if result['visibility'] else '隐藏'}")
            
        except Exception as e:
            result['issues'].append(f"缩放验证异常: {e}")
            print(f"  ❌ 缩放验证: 异常 - {e}")
        
        return result
    
    def generate_validation_report(self, total, valid, actor_support, animation_support):
        """生成验证报告"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"character_validation_report_{timestamp}.md"
        
        print(f"\n{'='*60}")
        print("📊 验证统计报告")
        print(f"{'='*60}")
        print(f"总角色数量: {total}")
        print(f"Actor支持: {actor_support} ({actor_support/total*100:.1f}%)")
        print(f"动画支持: {animation_support} ({animation_support/total*100:.1f}%)")
        print(f"完全有效: {valid} ({valid/total*100:.1f}%)")
        
        # 生成详细报告文件
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 3D角色验证报告\n\n")
            f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 统计概览\n\n")
            f.write(f"- **总角色数量**: {total}\n")
            f.write(f"- **Actor支持**: {actor_support} ({actor_support/total*100:.1f}%)\n")
            f.write(f"- **动画支持**: {animation_support} ({animation_support/total*100:.1f}%)\n")
            f.write(f"- **完全有效**: {valid} ({valid/total*100:.1f}%)\n\n")
            
            # Actor支持详情
            f.write("## ✅ Actor支持状态\n\n")
            for char_name, supported in self.validation_results['actor_support'].items():
                status = "✅" if supported else "❌"
                f.write(f"- {status} **{char_name}**\n")
            
            # 动画支持详情
            f.write("\n## 🎭 动画支持详情\n\n")
            for char_name, anim_count in self.validation_results['animation_support'].items():
                if anim_count > 0:
                    f.write(f"- ✅ **{char_name}**: {anim_count} 个动画\n")
                else:
                    f.write(f"- ⚠️ **{char_name}**: 无动画\n")
            
            # 问题角色
            f.write("\n## ❌ 问题角色\n\n")
            for char_name, issue in self.validation_results['model_issues'].items():
                f.write(f"- **{char_name}**: {issue}\n")
            
            # 修复建议
            f.write("\n## 🔧 修复建议\n\n")
            f.write("1. **无Actor支持的角色**: 检查模型文件路径和格式\n")
            f.write("2. **无动画的角色**: 添加默认动画或程序化动画\n")
            f.write("3. **缩放问题**: 统一使用智能缩放系统\n")
            f.write("4. **可见性问题**: 确保材质和纹理正确应用\n")
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        # 识别需要修复的角色
        problem_chars = []
        for char_name, supported in self.validation_results['actor_support'].items():
            if not supported:
                problem_chars.append(char_name)
        
        if problem_chars:
            print(f"\n⚠️  需要修复的角色 ({len(problem_chars)}):")
            for char in problem_chars[:10]:  # 显示前10个
                print(f"  - {char}")
            if len(problem_chars) > 10:
                print(f"  ... 还有 {len(problem_chars) - 10} 个")
        
        # 提供修复代码建议
        self.generate_fix_suggestions()
    
    def generate_fix_suggestions(self):
        """生成修复建议代码"""
        print(f"\n🔧 自动修复建议:")
        print("="*40)
        
        # 统计问题类型
        no_actor = sum(1 for supported in self.validation_results['actor_support'].values() if not supported)
        no_animation = sum(1 for count in self.validation_results['animation_support'].values() if count == 0)
        
        if no_actor > 0:
            print(f"1. {no_actor} 个角色无Actor支持 - 需要检查模型文件")
        
        if no_animation > 0:
            print(f"2. {no_animation} 个角色无动画 - 需要添加默认动画")
        
        print("\n建议在 enhanced_character_manager.py 中添加:")
        print("- 更好的错误处理和回退机制")
        print("- 统一的默认动画系统")
        print("- 自动缩放和可见性修复")
        
        print("\n✅ 验证完成！请查看详细报告文件。")


def main():
    """主函数"""
    try:
        print("🚀 启动3D角色验证系统...")
        validator = Character3DValidator()
        
        # 等待用户确认后退出
        input("\n按回车键退出验证系统...")
        
        # 清理
        validator.destroy()
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断验证")
    except Exception as e:
        print(f"❌ 验证系统运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()