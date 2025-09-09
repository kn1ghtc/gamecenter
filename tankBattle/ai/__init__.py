"""
AI智能化坦克系统
===============
高级AI模块，包含强化学习、路径规划、战术分析等功能

模块说明：
- reinforcement_learning.py: 深度Q网络和强化学习框架
- pathfinding.py: 高级路径规划算法
- tactical_ai.py: 战术AI和多层决策系统
- behavior_prediction.py: 玩家行为预测
- battlefield_analyzer.py: 战场分析器
- integration.py: AI系统集成管理器
"""

__version__ = "1.0.0"
__author__ = "Tank Battle AI Team"

# AI组件可用性检查
try:
    import torch
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    AI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"AI组件依赖缺失: {e}")
    AI_COMPONENTS_AVAILABLE = False

# 导出主要类
if AI_COMPONENTS_AVAILABLE:
    try:
        from .integration import AISystemManager, create_smart_tank
        from .reinforcement_learning import TankRLAgent, TankDQN
        from .pathfinding import AdvancedPathfinding
        from .tactical_ai import SmartTankAI
        
        __all__ = [
            'AISystemManager',
            'create_smart_tank', 
            'TankRLAgent',
            'AdvancedPathfinding',
            'SmartTankAI',
            'AI_COMPONENTS_AVAILABLE'
        ]
    except ImportError:
        # 组件未完全加载，使用基础导出
        __all__ = ['AI_COMPONENTS_AVAILABLE']
else:
    __all__ = ['AI_COMPONENTS_AVAILABLE']
