#!/usr/bin/env python3
"""
代码工程方法比较可视化工具
Code Engineering Methodology Visualization Tool
"""

import json
from pathlib import Path

# Try to import optional dependencies
try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def load_analysis_data():
    """加载分析数据"""
    with open('code_analysis_report.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def create_comparison_charts(data):
    """创建比较图表"""
    
    if not HAS_MATPLOTLIB:
        print("❌ matplotlib/numpy未安装，跳过图表生成")
        return None
        
    import numpy as np
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('游戏中心代码工程方法分析 / Game Center Code Engineering Analysis', fontsize=16, fontweight='bold')
    
    # 1. 代码规模对比
    projects = ['tankBattle', 'stickman_game']
    lines = [data['comparison']['size_comparison']['tankBattle_lines'],
             data['comparison']['size_comparison']['stickman_game_lines']]
    files = [data['comparison']['modularity_comparison']['tankBattle_files'],
             data['comparison']['modularity_comparison']['stickman_game_files']]
    
    x = np.arange(len(projects))
    width = 0.35
    
    ax1.bar(x - width/2, lines, width, label='代码行数 / Lines of Code', color='#3498db')
    ax1.bar(x + width/2, [f*50 for f in files], width, label='文件数×50 / Files×50', color='#e74c3c')
    ax1.set_xlabel('项目 / Project')
    ax1.set_ylabel('数量 / Count')
    ax1.set_title('代码规模对比 / Code Size Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(projects)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 复杂度分析
    tank_complexity = data['tankBattle_analysis']['main_file_analysis']['complexity_score']
    stickman_modules = data['stickman_game_analysis']['module_analyses']
    
    module_names = list(stickman_modules.keys())
    module_complexity = [stickman_modules[name]['complexity_score'] for name in module_names]
    
    # 创建复杂度对比
    ax2.barh(['tankBattle'], [tank_complexity], color='#e74c3c', alpha=0.7, label='tankBattle')
    
    y_pos = np.arange(len(module_names))
    ax2.barh(module_names, module_complexity, color='#3498db', alpha=0.7)
    
    ax2.set_xlabel('复杂度评分 / Complexity Score')
    ax2.set_title('模块复杂度对比 / Module Complexity Comparison')
    ax2.grid(True, alpha=0.3)
    
    # 3. 类和方法统计
    tank_classes = len(data['tankBattle_analysis']['main_file_analysis']['classes'])
    tank_methods = sum(len(cls['methods']) for cls in data['tankBattle_analysis']['main_file_analysis']['classes'])
    
    stickman_classes = sum(len(module['classes']) for module in stickman_modules.values())
    stickman_methods = sum(sum(len(cls['methods']) for cls in module['classes']) for module in stickman_modules.values())
    
    categories = ['类数量\nClasses', '方法数量\nMethods']
    tank_stats = [tank_classes, tank_methods]
    stickman_stats = [stickman_classes, stickman_methods]
    
    x = np.arange(len(categories))
    ax3.bar(x - width/2, tank_stats, width, label='tankBattle', color='#e74c3c', alpha=0.7)
    ax3.bar(x + width/2, stickman_stats, width, label='stickman_game', color='#3498db', alpha=0.7)
    ax3.set_xlabel('统计类型 / Statistics Type')
    ax3.set_ylabel('数量 / Count')
    ax3.set_title('代码结构统计 / Code Structure Statistics')
    ax3.set_xticks(x)
    ax3.set_xticklabels(categories)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 架构质量雷达图
    categories_radar = ['模块化\nModularity', '配置管理\nConfig Mgmt', '错误处理\nError Handling', 
                        '文档质量\nDocumentation', '扩展性\nExtensibility', '可测试性\nTestability']
    
    # 评分（1-5分）
    tank_scores = [1, 2, 2, 3, 2, 1]  # tankBattle评分
    stickman_scores = [5, 5, 4, 4, 4, 3]  # stickman_game评分
    
    angles = np.linspace(0, 2 * np.pi, len(categories_radar), endpoint=False)
    angles = np.concatenate((angles, [angles[0]]))
    
    tank_scores += [tank_scores[0]]
    stickman_scores += [stickman_scores[0]]
    
    ax4.plot(angles, tank_scores, 'o-', linewidth=2, label='tankBattle', color='#e74c3c')
    ax4.fill(angles, tank_scores, alpha=0.25, color='#e74c3c')
    ax4.plot(angles, stickman_scores, 'o-', linewidth=2, label='stickman_game', color='#3498db')
    ax4.fill(angles, stickman_scores, alpha=0.25, color='#3498db')
    
    ax4.set_xticks(angles[:-1])
    ax4.set_xticklabels(categories_radar)
    ax4.set_ylim(0, 5)
    ax4.set_title('架构质量评估 / Architecture Quality Assessment')
    ax4.legend()
    ax4.grid(True)
    
    plt.tight_layout()
    plt.savefig('code_analysis_visualization.png', dpi=300, bbox_inches='tight')
    print("📊 可视化图表已保存为 code_analysis_visualization.png")
    
    return fig


def generate_summary_report(data):
    """生成总结报告"""
    
    report = f"""
# 游戏中心代码工程方法分析总结报告
# Game Center Code Engineering Methodology Summary Report

## 执行摘要 / Executive Summary

本报告分析了游戏中心项目中两个子项目的代码工程方法论：
- **tankBattle**: 传统单体式架构的2D坦克游戏
- **stickman_game**: 现代模块化架构的火柴人冒险游戏

This report analyzes the code engineering methodologies of two sub-projects in the game center:
- **tankBattle**: Traditional monolithic 2D tank game
- **stickman_game**: Modern modular stickman adventure game

## 关键发现 / Key Findings

### 1. 架构模式对比 / Architecture Pattern Comparison
- **tankBattle**: {data['comparison']['architecture_comparison']['tankBattle']} (单体式)
- **stickman_game**: {data['comparison']['architecture_comparison']['stickman_game']} (模块化)

### 2. 规模对比 / Scale Comparison
- **代码总量比例**: stickman_game 是 tankBattle 的 {data['comparison']['size_comparison']['size_ratio']:.1f} 倍
- **模块化程度**: stickman_game 有 {data['comparison']['modularity_comparison']['stickman_game_files']} 个模块，tankBattle 只有 {data['comparison']['modularity_comparison']['tankBattle_files']} 个文件

### 3. 复杂度分析 / Complexity Analysis
- **tankBattle 复杂度**: {data['tankBattle_analysis']['main_file_analysis']['complexity_score']} (过高)
- **stickman_game 平均模块复杂度**: {sum(module['complexity_score'] for module in data['stickman_game_analysis']['module_analyses'].values()) // len(data['stickman_game_analysis']['module_analyses'])} (适中)

### 4. 代码结构统计 / Code Structure Statistics

#### tankBattle:
- 类数量: {len(data['tankBattle_analysis']['main_file_analysis']['classes'])}
- 方法总数: {sum(len(cls['methods']) for cls in data['tankBattle_analysis']['main_file_analysis']['classes'])}
- 导入模块: {len(data['tankBattle_analysis']['main_file_analysis']['imports'])}

#### stickman_game:
- 类数量: {sum(len(module['classes']) for module in data['stickman_game_analysis']['module_analyses'].values())}
- 方法总数: {sum(sum(len(cls['methods']) for cls in module['classes']) for module in data['stickman_game_analysis']['module_analyses'].values())}
- 配置文件: {len(data['stickman_game_analysis']['config_files'])}

## 工程方法论评估 / Engineering Methodology Assessment

### tankBattle 优点 / Strengths:
1. **快速原型开发**: 单文件结构便于快速实现和测试
2. **简单部署**: 无复杂依赖关系，易于分发
3. **学习友好**: 代码结构简单，适合初学者理解

### tankBattle 缺点 / Weaknesses:
1. **可维护性差**: 所有功能耦合在一个文件中
2. **扩展困难**: 添加新功能需要修改核心文件
3. **测试困难**: 无法进行单元测试
4. **代码复用性低**: 功能难以在其他项目中复用

### stickman_game 优点 / Strengths:
1. **高度模块化**: 清晰的职责分离，易于维护
2. **配置外部化**: 集中的配置管理系统
3. **良好的扩展性**: 易于添加新功能和模块
4. **错误处理完善**: 健壮的异常处理机制
5. **资源管理优秀**: 完整的图像和音频管理系统

### stickman_game 缺点 / Weaknesses:
1. **复杂度较高**: 初学者可能难以理解整体架构
2. **部署复杂**: 需要管理多个文件和依赖
3. **可能过度工程化**: 对于简单游戏可能过于复杂

## 工程方法论建议 / Engineering Methodology Recommendations

### 对 tankBattle 的建议:
{chr(10).join(f"- {rec}" for rec in data['recommendations'] if 'tankBattle' in rec)}

### 对 stickman_game 的建议:
{chr(10).join(f"- {rec}" for rec in data['recommendations'] if 'stickman_game' in rec)}

### 通用建议:
{chr(10).join(f"- {rec}" for rec in data['recommendations'] if 'tankBattle' not in rec and 'stickman_game' not in rec)}

## 最佳实践总结 / Best Practices Summary

基于分析，推荐的游戏开发工程方法论包括：

1. **渐进式架构**: 从简单的单体式开始，随着项目复杂度增长逐步模块化
2. **配置管理**: 使用外部配置文件管理游戏参数
3. **职责分离**: 将不同功能分离到独立的模块中
4. **错误处理**: 实现完善的异常处理和优雅降级
5. **资源管理**: 建立统一的资源加载和管理系统
6. **文档标准**: 建立一致的代码文档标准
7. **测试策略**: 为关键功能添加单元测试

## 结论 / Conclusion

stickman_game 展示了更成熟和专业的软件工程实践，适合作为游戏开发的模板和标准。
tankBattle 虽然简单，但在快速原型开发和学习阶段有其价值。

建议项目采用 stickman_game 的工程方法论作为标准，并逐步将 tankBattle 重构为类似的架构。

---
*报告生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*分析工具版本: v1.0*
"""
    
    with open('ENGINEERING_ANALYSIS_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("📋 总结报告已保存为 ENGINEERING_ANALYSIS_SUMMARY.md")


def main():
    """主函数"""
    try:
        print("📊 开始生成代码工程方法论分析...")
        
        # 加载数据
        data = load_analysis_data()
        
        # 创建图表 (如果可能)
        if HAS_MATPLOTLIB:
            create_comparison_charts(data)
        else:
            print("❌ 缺少matplotlib库，跳过可视化图表生成")
        
        # 生成总结报告
        generate_summary_report(data)
        
        files_generated = [
            "📋 ENGINEERING_ANALYSIS_SUMMARY.md - 总结报告",
            "📄 code_analysis_report.json - 详细数据", 
            "📖 CODE_ANALYSIS.md - 完整分析文档"
        ]
        
        if HAS_MATPLOTLIB:
            files_generated.insert(0, "📊 code_analysis_visualization.png - 可视化图表")
        
        print("✅ 分析完成！生成的文件:")
        for f in files_generated:
            print(f"   {f}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        # 仍然尝试生成报告
        try:
            data = load_analysis_data()
            generate_summary_report(data)
            print("📋 已生成文本版本的总结报告")
        except:
            pass


if __name__ == "__main__":
    main()