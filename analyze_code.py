#!/usr/bin/env python3
"""
代码工程方法分析工具
Code Engineering Methodology Analysis Tool

本脚本提供对游戏中心项目的自动化代码分析功能
This script provides automated code analysis for the game center project
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.analysis_result = {
            'project_overview': {},
            'tankBattle_analysis': {},
            'stickman_game_analysis': {},
            'comparison': {},
            'recommendations': []
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                'file_path': str(file_path),
                'lines_of_code': len(content.split('\n')),
                'classes': [],
                'functions': [],
                'imports': [],
                'complexity_score': 0
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'methods': [],
                        'line_number': node.lineno
                    }
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info['methods'].append({
                                'name': item.name,
                                'line_number': item.lineno,
                                'args_count': len(item.args.args)
                            })
                    
                    analysis['classes'].append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    # 检查是否是类的方法
                    is_method = False
                    for class_node in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                        if node in class_node.body:
                            is_method = True
                            break
                    
                    if not is_method:
                        analysis['functions'].append({
                            'name': node.name,
                            'line_number': node.lineno,
                            'args_count': len(node.args.args)
                        })
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        analysis['imports'].append(f"{module}.{alias.name}")
            
            # 简单的复杂度评分
            analysis['complexity_score'] = self.calculate_complexity_score(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'error': str(e),
                'lines_of_code': 0,
                'classes': [],
                'functions': [],
                'imports': [],
                'complexity_score': 0
            }
    
    def calculate_complexity_score(self, analysis: Dict[str, Any]) -> int:
        """计算代码复杂度评分"""
        score = 0
        
        # 基于代码行数
        score += analysis['lines_of_code'] // 10
        
        # 基于类数量
        score += len(analysis['classes']) * 5
        
        # 基于函数数量
        score += len(analysis['functions']) * 3
        
        # 基于导入数量
        score += len(analysis['imports']) * 2
        
        # 基于方法数量
        for cls in analysis['classes']:
            score += len(cls['methods']) * 2
        
        return score
    
    def analyze_tankBattle(self) -> Dict[str, Any]:
        """分析tankBattle项目"""
        tank_dir = self.project_root / 'tankBattle'
        main_file = tank_dir / 'main.py'
        
        analysis = {
            'architecture_pattern': 'Monolithic',
            'file_count': 1,
            'main_file_analysis': {}
        }
        
        if main_file.exists():
            analysis['main_file_analysis'] = self.analyze_file(main_file)
        
        # 检查文档
        readme_file = tank_dir / 'readme.md'
        analysis['has_documentation'] = readme_file.exists()
        
        return analysis
    
    def analyze_stickman_game(self) -> Dict[str, Any]:
        """分析stickman_game项目"""
        stickman_dir = self.project_root / 'stickman_game'
        src_dir = stickman_dir / 'src'
        
        analysis = {
            'architecture_pattern': 'Modular',
            'file_count': 0,
            'module_analyses': {},
            'total_lines': 0
        }
        
        if src_dir.exists():
            python_files = list(src_dir.glob('*.py'))
            analysis['file_count'] = len(python_files)
            
            for py_file in python_files:
                file_analysis = self.analyze_file(py_file)
                analysis['module_analyses'][py_file.name] = file_analysis
                analysis['total_lines'] += file_analysis['lines_of_code']
        
        # 检查配置文件
        config_files = ['src/config.py', 'levels/level_config.json', 'levels/game_save.json']
        analysis['config_files'] = []
        for config_file in config_files:
            if (stickman_dir / config_file).exists():
                analysis['config_files'].append(config_file)
        
        return analysis
    
    def compare_projects(self, tank_analysis: Dict, stickman_analysis: Dict) -> Dict[str, Any]:
        """比较两个项目"""
        comparison = {
            'architecture_comparison': {
                'tankBattle': tank_analysis['architecture_pattern'],
                'stickman_game': stickman_analysis['architecture_pattern']
            },
            'size_comparison': {
                'tankBattle_lines': tank_analysis['main_file_analysis'].get('lines_of_code', 0),
                'stickman_game_lines': stickman_analysis['total_lines'],
                'size_ratio': 0
            },
            'modularity_comparison': {
                'tankBattle_files': tank_analysis['file_count'],
                'stickman_game_files': stickman_analysis['file_count'],
                'modularity_factor': 0
            }
        }
        
        # 计算比率
        tank_lines = comparison['size_comparison']['tankBattle_lines']
        stickman_lines = comparison['size_comparison']['stickman_game_lines']
        
        if tank_lines > 0:
            comparison['size_comparison']['size_ratio'] = stickman_lines / tank_lines
        
        tank_files = comparison['modularity_comparison']['tankBattle_files']
        stickman_files = comparison['modularity_comparison']['stickman_game_files']
        
        if tank_files > 0:
            comparison['modularity_comparison']['modularity_factor'] = stickman_files / tank_files
        
        return comparison
    
    def generate_recommendations(self, tank_analysis: Dict, stickman_analysis: Dict, comparison: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于复杂度分析的建议
        tank_complexity = tank_analysis['main_file_analysis'].get('complexity_score', 0)
        
        if tank_complexity > 100:
            recommendations.append("tankBattle: 代码复杂度过高，建议拆分为多个模块")
        
        if tank_analysis['file_count'] == 1:
            recommendations.append("tankBattle: 建议采用模块化架构，参考stickman_game的设计")
        
        if not tank_analysis.get('has_documentation'):
            recommendations.append("tankBattle: 缺少完整的文档，建议添加详细的README")
        
        # 基于模块化程度的建议
        if comparison['modularity_comparison']['modularity_factor'] > 5:
            recommendations.append("stickman_game: 模块化程度良好，但需要注意避免过度工程化")
        
        # 基于配置管理的建议
        config_count = len(stickman_analysis.get('config_files', []))
        if config_count > 0:
            recommendations.append("stickman_game: 配置管理良好，建议tankBattle也采用类似方式")
        
        # 代码质量建议
        recommendations.append("建议两个项目都添加单元测试和CI/CD流程")
        recommendations.append("建议建立统一的代码规范和格式化工具")
        recommendations.append("建议添加代码静态分析工具如pylint或flake8")
        
        return recommendations
    
    def run_analysis(self) -> Dict[str, Any]:
        """运行完整分析"""
        print("🔍 开始代码工程方法分析...")
        
        # 项目概览
        self.analysis_result['project_overview'] = {
            'project_name': 'Game Center',
            'project_path': str(self.project_root),
            'sub_projects': ['tankBattle', 'stickman_game']
        }
        
        # 分析tankBattle
        print("📊 分析tankBattle项目...")
        self.analysis_result['tankBattle_analysis'] = self.analyze_tankBattle()
        
        # 分析stickman_game
        print("📊 分析stickman_game项目...")
        self.analysis_result['stickman_game_analysis'] = self.analyze_stickman_game()
        
        # 项目比较
        print("⚖️ 比较项目架构...")
        self.analysis_result['comparison'] = self.compare_projects(
            self.analysis_result['tankBattle_analysis'],
            self.analysis_result['stickman_game_analysis']
        )
        
        # 生成建议
        print("💡 生成改进建议...")
        self.analysis_result['recommendations'] = self.generate_recommendations(
            self.analysis_result['tankBattle_analysis'],
            self.analysis_result['stickman_game_analysis'],
            self.analysis_result['comparison']
        )
        
        return self.analysis_result
    
    def save_analysis(self, output_file: str = 'code_analysis_report.json'):
        """保存分析结果"""
        output_path = self.project_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_result, f, indent=2, ensure_ascii=False)
        print(f"📄 分析报告已保存到: {output_path}")
    
    def print_summary(self):
        """打印分析摘要"""
        print("\n" + "="*60)
        print("📋 代码工程方法分析摘要")
        print("="*60)
        
        # 项目概览
        tank_lines = self.analysis_result['tankBattle_analysis']['main_file_analysis'].get('lines_of_code', 0)
        stickman_lines = self.analysis_result['stickman_game_analysis']['total_lines']
        
        print(f"\n🎮 项目规模对比:")
        print(f"   tankBattle:    {tank_lines:4d} 行代码, {self.analysis_result['tankBattle_analysis']['file_count']} 个文件")
        print(f"   stickman_game: {stickman_lines:4d} 行代码, {self.analysis_result['stickman_game_analysis']['file_count']} 个文件")
        
        # 架构对比
        print(f"\n🏗️ 架构模式对比:")
        print(f"   tankBattle:    {self.analysis_result['comparison']['architecture_comparison']['tankBattle']}")
        print(f"   stickman_game: {self.analysis_result['comparison']['architecture_comparison']['stickman_game']}")
        
        # 主要建议
        print(f"\n💡 主要改进建议:")
        for i, recommendation in enumerate(self.analysis_result['recommendations'][:5], 1):
            print(f"   {i}. {recommendation}")
        
        if len(self.analysis_result['recommendations']) > 5:
            print(f"   ... 还有 {len(self.analysis_result['recommendations']) - 5} 条建议")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    analyzer = CodeAnalyzer(project_root)
    analyzer.run_analysis()
    analyzer.print_summary()
    analyzer.save_analysis()
    
    print("\n✅ 代码工程方法分析完成！")
    print("📄 详细报告请查看 CODE_ANALYSIS.md 和 code_analysis_report.json")


if __name__ == "__main__":
    main()