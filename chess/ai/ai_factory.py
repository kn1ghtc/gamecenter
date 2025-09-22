"""
AI工厂模块
集中管理和创建不同类型的AI实例
"""
import sys
import os
from typing import Optional, Dict, Any, List

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ai.basic_ai import BasicAI
from ai.ml_ai import ChessMLAI
from ai.gpt_ai import GPTChessAI
from ai.chess_ai_agent_adapter import ChessAIAgentAdapter
from game.pieces import PieceColor

class AIFactory:
    """AI工厂类 - 管理不同难度的AI实例"""
    
    def __init__(self):
        self._ai_cache = {}
        self._ai_configs = {
            'EASY': {
                'class': BasicAI,
                'params': {'depth': 2, 'time_limit': 1.0},
                'description': '简单AI - 基础算法，适合初学者'
            },
            'MEDIUM': {
                'class': ChessMLAI,
                'params': {},  # 让ML AI自己处理模型路径
                'description': '中等AI - 机器学习，会不断学习改进'
            },
            'HARD': {
                'class': GPTChessAI,
                'params': {'model': 'gpt-4o-mini'},
                'description': '专家AI - GPT-4o-mini，顶级象棋水平'
            },
            'COMPANION': {
                'class': ChessAIAgentAdapter,
                'params': {
                    'personality': 'friendly_mentor',
                    'voice_enabled': True  # 移除不支持的enable_memory参数
                },
                'description': '智能陪伴助理 - 超级智能象棋伙伴，具备语音聊天、记忆学习能力'
            }
        }
    
    def create_ai(self, difficulty: str, **kwargs) -> Optional[Any]:
        """
        创建AI实例
        
        Args:
            difficulty: AI难度等级 ('EASY', 'MEDIUM', 'HARD')
            **kwargs: 额外参数覆盖默认配置
            
        Returns:
            AI实例或None（如果创建失败）
        """
        if difficulty not in self._ai_configs:
            print(f"❌ 未知的AI难度等级: {difficulty}")
            return None
        
        # 检查缓存
        cache_key = f"{difficulty}_{hash(frozenset(kwargs.items()))}"
        if cache_key in self._ai_cache:
            print(f"♻️ 使用缓存的AI实例: {difficulty}")
            return self._ai_cache[cache_key]
        
        config = self._ai_configs[difficulty]
        ai_class = config['class']
        
        # 合并默认参数和用户参数
        params = {**config['params'], **kwargs}
        
        try:
            print(f"🤖 创建{difficulty}级AI...")
            print(f"   描述: {config['description']}")
            
            ai_instance = ai_class(**params)
            
            # 缓存实例
            self._ai_cache[cache_key] = ai_instance
            
            print(f"✅ {difficulty}级AI创建成功")
            return ai_instance
            
        except Exception as e:
            print(f"❌ 创建{difficulty}级AI失败: {e}")
            
            # 如果是ML或GPT AI失败，尝试创建基础AI作为备用
            if difficulty != 'EASY':
                print(f"🔄 尝试创建基础AI作为{difficulty}级的备用...")
                return self._create_fallback_ai(difficulty)
            
            return None
    
    def _create_fallback_ai(self, original_difficulty: str) -> Optional[Any]:
        """创建备用基础AI"""
        try:
            if original_difficulty == 'MEDIUM':
                # 中等难度的备用AI使用更深的搜索
                fallback_ai = BasicAI(depth=4, time_limit=3.0)
            elif original_difficulty == 'HARD':
                # 困难难度的备用AI使用最深的搜索
                fallback_ai = BasicAI(depth=5, time_limit=5.0)
            else:
                fallback_ai = BasicAI(depth=2, time_limit=1.0)
            
            print(f"✅ 备用AI创建成功，深度={fallback_ai.max_depth}")
            return fallback_ai
            
        except Exception as e:
            print(f"❌ 备用AI创建失败: {e}")
            return None
    
    def get_ai_info(self, difficulty: str) -> Dict[str, Any]:
        """获取AI信息"""
        if difficulty not in self._ai_configs:
            return {}
        
        config = self._ai_configs[difficulty]
        info = {
            'difficulty': difficulty,
            'description': config['description'],
            'class_name': config['class'].__name__,
            'default_params': config['params']
        }
        
        # 如果AI已创建，添加运行时信息
        cache_keys = [k for k in self._ai_cache.keys() if k.startswith(difficulty)]
        if cache_keys:
            ai_instance = self._ai_cache[cache_keys[0]]
            
            if hasattr(ai_instance, 'get_stats'):
                info['stats'] = ai_instance.get_stats()
            elif hasattr(ai_instance, 'get_model_info'):
                info['model_info'] = ai_instance.get_model_info()
        
        return info
    
    def clear_cache(self):
        """清空AI缓存"""
        self._ai_cache.clear()
        print("🗑️ AI缓存已清空")
    
    def get_available_difficulties(self) -> List[str]:
        """获取可用的难度等级"""
        return list(self._ai_configs.keys())
    
    def test_ai_creation(self):
        """测试所有AI的创建"""
        print("🧪 测试AI创建...")
        results = {}
        
        for difficulty in self._ai_configs.keys():
            print(f"\n测试 {difficulty} 级AI:")
            ai = self.create_ai(difficulty)
            results[difficulty] = ai is not None
            
            if ai:
                print(f"   ✅ {difficulty} 级AI创建成功")
                
                # 测试基本功能
                try:
                    from game.board import ChessBoard
                    test_board = ChessBoard()
                    move = ai.get_best_move(test_board, PieceColor.WHITE)
                    if move:
                        print(f"   ✅ AI能够生成移动: {move}")
                    else:
                        print(f"   ⚠️ AI未能生成移动")
                except Exception as e:
                    print(f"   ❌ AI测试失败: {e}")
            else:
                print(f"   ❌ {difficulty} 级AI创建失败")
        
        return results

# 全局AI工厂实例
ai_factory = AIFactory()

def get_ai(difficulty: str, **kwargs):
    """便捷函数：获取AI实例"""
    return ai_factory.create_ai(difficulty, **kwargs)

def test_all_ais():
    """便捷函数：测试所有AI"""
    return ai_factory.test_ai_creation()

if __name__ == "__main__":
    # 测试AI工厂
    print("🏭 AI工厂测试")
    print("=" * 50)
    
    factory = AIFactory()
    results = factory.test_ai_creation()
    
    print(f"\n📊 测试结果:")
    for difficulty, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {difficulty}: {status}")
    
    print(f"\n📋 可用难度等级: {factory.get_available_difficulties()}")
    
    # 显示AI信息
    print(f"\n📖 AI详细信息:")
    for difficulty in factory.get_available_difficulties():
        info = factory.get_ai_info(difficulty)
        print(f"\n{difficulty}:")
        print(f"  描述: {info.get('description', 'N/A')}")
        print(f"  类名: {info.get('class_name', 'N/A')}")
        print(f"  参数: {info.get('default_params', {})}")
