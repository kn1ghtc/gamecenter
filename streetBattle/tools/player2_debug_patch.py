#!/usr/bin/env python3
"""
Player2 Loading Debug Patch
Player2加载调试补丁
"""

import os
from pathlib import Path

def debug_player2_loading():
    """调试Player2加载问题"""
    
    def enhanced_load_player2_model(self, character_name):
        """增强的Player2模型加载方法"""
        print(f"🎭 开始加载Player2模型: {character_name}")
        
        # 多种模型文件路径尝试
        models_dir = Path(self.assets_dir) / "3d_models"
        
        model_candidates = [
            models_dir / f"{character_name}.bam",
            models_dir / f"{character_name}_player2.bam", 
            models_dir / f"{character_name}_p2.bam",
            models_dir / "characters" / f"{character_name}.bam",
            models_dir / "players" / f"{character_name}_p2.bam"
        ]
        
        print(f"🔍 搜索Player2模型文件:")
        for candidate in model_candidates:
            if candidate.exists():
                print(f"    ✓ 找到: {candidate}")
                try:
                    # 尝试加载模型
                    model = self.base_app.loader.loadModel(str(candidate))
                    if model:
                        print(f"    ✅ 成功加载: {candidate.name}")
                        
                        # 设置Player2位置和属性
                        model.setPos(3, 0, 0)  # Player2位置
                        model.setScale(1.0)
                        model.reparentTo(self.base_app.render)
                        
                        # 如果是Actor，设置动画
                        if hasattr(model, 'setPlayRate'):
                            model.loop('idle')  # 播放idle动画
                        
                        print(f"    📍 Player2已设置到位置 (3, 0, 0)")
                        return model
                    else:
                        print(f"    ❌ 加载失败: {candidate.name}")
                except Exception as e:
                    print(f"    ❌ 加载异常 {candidate.name}: {e}")
            else:
                print(f"    ❌ 不存在: {candidate}")
        
        print(f"⚠️ 无法找到Player2模型文件，使用回退方案")
        
        # 回退方案：使用Player1模型的副本
        try:
            player1_model = getattr(self, 'player1_model', None)
            if player1_model:
                player2_model = player1_model.copyTo(self.base_app.render)
                player2_model.setPos(3, 0, 0)
                player2_model.setColorScale(0.8, 0.8, 1.0, 1.0)  # 略微改变颜色
                print(f"    ✅ 使用Player1模型副本作为Player2")
                return player2_model
        except Exception as e:
            print(f"    ❌ 回退方案失败: {e}")
        
        return None
    
    def enhanced_setup_player2_lighting(self):
        """增强的Player2光照设置"""
        print(f"💡 设置Player2光照")
        
        try:
            # 为Player2创建专用光照
            from panda3d.core import DirectionalLight, AmbientLight, VBase4
            
            # 方向光
            player2_dlight = DirectionalLight('player2_dlight')
            player2_dlight.setDirection(VBase4(-1, -1, -1, 0))
            player2_dlight.setColor(VBase4(0.8, 0.8, 1.0, 1))
            
            player2_dlnp = self.base_app.render.attachNewNode(player2_dlight)
            player2_dlnp.setPos(3, 5, 5)
            
            # 环境光
            player2_alight = AmbientLight('player2_alight')
            player2_alight.setColor(VBase4(0.3, 0.3, 0.4, 1))
            player2_alnp = self.base_app.render.attachNewNode(player2_alight)
            
            # 应用光照到Player2区域
            if hasattr(self, 'player2_model') and self.player2_model:
                self.player2_model.setLight(player2_dlnp)
                self.player2_model.setLight(player2_alnp)
                print(f"    ✅ Player2光照设置完成")
            
        except Exception as e:
            print(f"    ❌ Player2光照设置失败: {e}")
    
    # 应用补丁的辅助函数
    def apply_player2_patch(game_instance):
        """应用Player2补丁到游戏实例"""
        if hasattr(game_instance, 'load_player2_model'):
            game_instance.load_player2_model = enhanced_load_player2_model.__get__(game_instance)
            print("✅ Player2加载补丁已应用")
        
        if hasattr(game_instance, 'setup_player2_lighting'):
            game_instance.setup_player2_lighting = enhanced_setup_player2_lighting.__get__(game_instance)
            print("✅ Player2光照补丁已应用")
    
    return {
        'load_player2_model': enhanced_load_player2_model,
        'setup_player2_lighting': enhanced_setup_player2_lighting,
        'apply_patch': apply_player2_patch
    }

if __name__ == "__main__":
    debug_functions = debug_player2_loading()
    print("Player2调试补丁已准备就绪")
