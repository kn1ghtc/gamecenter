"""
AI系统集成管理器
==============
统一管理所有AI组件，提供统一接口

功能：
- AI组件可用性检测
- 智能体创建工厂
- 性能优化管理
- 错误处理和回退
"""

import os
import sys
import logging
import traceback
from typing import Optional, Dict, Any, Type
from dataclasses import dataclass

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AICapabilities:
    """AI能力配置"""
    reinforcement_learning: bool = False
    advanced_pathfinding: bool = False
    tactical_ai: bool = False
    behavior_prediction: bool = False
    performance_optimization: bool = False

class AISystemManager:
    """AI系统管理器"""
    
    def __init__(self):
        self.capabilities = AICapabilities()
        self.components = {}
        self.ai_instances = {}
        
        # 检测可用组件
        self._detect_components()
    
    def _detect_components(self):
        """检测AI组件可用性"""
        logger.info("检测AI组件可用性...")
        
        # 检测PyTorch
        try:
            import torch
            self.capabilities.reinforcement_learning = True
            logger.info("✓ PyTorch可用 - 强化学习功能已启用")
        except ImportError:
            logger.warning("✗ PyTorch不可用 - 强化学习功能禁用")
        
        # 检测scikit-learn
        try:
            from sklearn.ensemble import RandomForestClassifier
            self.capabilities.behavior_prediction = True
            logger.info("✓ scikit-learn可用 - 行为预测功能已启用")
        except ImportError:
            logger.warning("✗ scikit-learn不可用 - 行为预测功能禁用")
        
        # 检测numpy
        try:
            import numpy as np
            self.capabilities.advanced_pathfinding = True
            self.capabilities.tactical_ai = True
            logger.info("✓ NumPy可用 - 高级路径规划和战术AI已启用")
        except ImportError:
            logger.error("✗ NumPy不可用 - 基础AI功能可能受限")
            self.capabilities.advanced_pathfinding = False
            self.capabilities.tactical_ai = False
        
        # 性能优化总是可用
        self.capabilities.performance_optimization = True
        
        logger.info(f"AI组件检测完成: {self._get_capability_summary()}")
    
    def _get_capability_summary(self) -> str:
        """获取能力摘要"""
        enabled = []
        if self.capabilities.reinforcement_learning:
            enabled.append("强化学习")
        if self.capabilities.advanced_pathfinding:
            enabled.append("高级路径规划")
        if self.capabilities.tactical_ai:
            enabled.append("战术AI")
        if self.capabilities.behavior_prediction:
            enabled.append("行为预测")
        
        return f"{len(enabled)}/4个高级功能可用 ({', '.join(enabled)})"
    
    def create_smart_tank(self, tank_instance, ai_level: str = 'auto') -> Any:
        """创建智能坦克AI实例"""
        try:
            if ai_level == 'auto':
                # 自动选择最佳AI级别
                if self.capabilities.reinforcement_learning and self.capabilities.tactical_ai:
                    ai_level = 'enhanced'
                elif self.capabilities.tactical_ai:
                    ai_level = 'smart'
                else:
                    ai_level = 'basic'
            
            logger.info(f"创建AI级别: {ai_level}")
            
            if ai_level == 'enhanced' and self.capabilities.reinforcement_learning:
                return self._create_enhanced_ai(tank_instance)
            elif ai_level == 'smart' and self.capabilities.tactical_ai:
                return self._create_smart_ai(tank_instance)
            else:
                return self._create_basic_ai(tank_instance)
                
        except Exception as e:
            logger.error(f"创建智能坦克失败: {e}")
            logger.error(traceback.format_exc())
            return self._create_basic_ai(tank_instance)
    
    def _create_enhanced_ai(self, tank_instance):
        """创建增强AI（强化学习+战术AI）"""
        try:
            from .tactical_ai import SmartTankAI
            ai_instance = SmartTankAI(tank_instance)
            
            # 尝试加载预训练模型
            self._load_pretrained_models(ai_instance)
            
            logger.info("✓ 增强AI创建成功")
            return ai_instance
            
        except Exception as e:
            logger.error(f"增强AI创建失败: {e}")
            return self._create_smart_ai(tank_instance)
    
    def _create_smart_ai(self, tank_instance):
        """创建智能AI（仅战术AI）"""
        try:
            from .tactical_ai import SmartTankAI
            ai_instance = SmartTankAI(tank_instance)
            
            # 禁用强化学习组件
            ai_instance.rl_agent = None
            ai_instance.has_advanced_components = False
            
            logger.info("✓ 智能AI创建成功")
            return ai_instance
            
        except Exception as e:
            logger.error(f"智能AI创建失败: {e}")
            return self._create_basic_ai(tank_instance)
    
    def _create_basic_ai(self, tank_instance):
        """创建基础AI（回退选项）"""
        logger.info("✓ 使用基础AI系统")
        return None  # 返回None表示使用原有的AI系统
    
    def _load_pretrained_models(self, ai_instance):
        """加载预训练模型"""
        model_dir = os.path.join(os.path.dirname(__file__), 'models')
        
        if ai_instance.rl_agent and os.path.exists(model_dir):
            model_path = os.path.join(model_dir, 'tank_rl_model.pth')
            if os.path.exists(model_path):
                try:
                    ai_instance.rl_agent.load_model(model_path)
                    logger.info("✓ 预训练强化学习模型加载成功")
                except Exception as e:
                    logger.warning(f"预训练模型加载失败: {e}")
    
    def optimize_performance(self, tank_count: int) -> Dict[str, Any]:
        """根据坦克数量优化性能"""
        config = {
            'ai_update_frequency': 1,
            'pathfinding_cache_size': 1000,
            'decision_timeout_ms': 50,
            'enable_threading': False
        }
        
        if tank_count <= 2:
            config['ai_update_frequency'] = 1
        elif tank_count <= 4:
            config['ai_update_frequency'] = 2
        elif tank_count <= 8:
            config['ai_update_frequency'] = 3
        else:
            config['ai_update_frequency'] = 4
            config['pathfinding_cache_size'] = 500
            config['decision_timeout_ms'] = 30
        
        logger.info(f"性能优化配置: 更新频率={config['ai_update_frequency']}, 缓存={config['pathfinding_cache_size']}")
        return config
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'capabilities': {
                'reinforcement_learning': self.capabilities.reinforcement_learning,
                'advanced_pathfinding': self.capabilities.advanced_pathfinding,
                'tactical_ai': self.capabilities.tactical_ai,
                'behavior_prediction': self.capabilities.behavior_prediction
            },
            'active_instances': len(self.ai_instances),
            'components_loaded': len(self.components),
            'summary': self._get_capability_summary()
        }

# 全局管理器实例
_ai_manager = None

def get_ai_manager() -> AISystemManager:
    """获取全局AI管理器实例"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AISystemManager()
    return _ai_manager

def create_smart_tank(tank_instance, ai_level: str = 'auto'):
    """创建智能坦克的便捷函数"""
    manager = get_ai_manager()
    return manager.create_smart_tank(tank_instance, ai_level)

def get_ai_capabilities() -> AICapabilities:
    """获取AI能力配置"""
    manager = get_ai_manager()
    return manager.capabilities

# 性能优化器
class AIPerformanceOptimizer:
    """AI性能优化器"""
    
    def __init__(self):
        self.decision_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.max_cache_size = 1000
    
    def cache_decision(self, state_key: str, decision: Dict, ttl_frames: int = 30):
        """缓存决策结果"""
        if len(self.decision_cache) >= self.max_cache_size:
            # 清除最旧的缓存
            oldest_key = min(self.decision_cache.keys(), 
                           key=lambda k: self.decision_cache[k]['timestamp'])
            del self.decision_cache[oldest_key]
        
        self.decision_cache[state_key] = {
            'decision': decision,
            'timestamp': 0,  # 简化的时间戳
            'ttl': ttl_frames
        }
    
    def get_cached_decision(self, state_key: str) -> Optional[Dict]:
        """获取缓存的决策"""
        if state_key in self.decision_cache:
            cached = self.decision_cache[state_key]
            
            # 简化的TTL检查
            if cached['ttl'] > 0:
                cached['ttl'] -= 1
                self.cache_hits += 1
                return cached['decision']
            else:
                del self.decision_cache[state_key]
        
        self.cache_misses += 1
        return None
    
    def get_cache_stats(self) -> Dict[str, float]:
        """获取缓存统计"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0.0
        
        return {
            'hit_rate': hit_rate,
            'cache_size': len(self.decision_cache),
            'total_queries': total
        }
    
    def clear_cache(self):
        """清除缓存"""
        self.decision_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

# 全局优化器实例
_performance_optimizer = AIPerformanceOptimizer()

def get_performance_optimizer() -> AIPerformanceOptimizer:
    """获取性能优化器"""
    return _performance_optimizer
