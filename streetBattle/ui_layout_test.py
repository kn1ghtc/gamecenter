#!/usr/bin/env python3
"""
UI Layout Test for Street Battle Character Selection
验证角色选择界面的UI布局优化
"""

from direct.showbase.ShowBase import ShowBase
from character_selector import CharacterSelector
from enhanced_character_manager import EnhancedCharacterManager
import os
import sys

class UILayoutTest(ShowBase):
    """UI布局测试应用"""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # 设置窗口
        self.win.setTitle("Street Battle - UI Layout Test")
        
        # 初始化角色管理器
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.char_manager = EnhancedCharacterManager(assets_dir)
        
        # 创建角色选择器
        self.char_selector = CharacterSelector(self, self.char_manager)
        
        # 显示角色选择界面
        self.char_selector.show(self.on_character_selected)
        
        print("=== UI Layout Test Started ===")
        print("测试角色选择界面的UI布局...")
        print("请检查以下项目:")
        print("1. 标题和副标题居中显示，不与右侧信息面板重叠")
        print("2. 左侧角色网格不超出边界，不与右侧面板重叠")
        print("3. 底部按钮对称分布，间距合理")
        print("4. 右侧信息面板内容布局合理，无重叠")
        print("5. 角色卡片尺寸适中，间距合理")
        print("按ESC键退出测试")
        
        # 键盘控制
        self.accept('escape', sys.exit)
        
    def on_character_selected(self, character_name):
        """角色选择回调"""
        print(f"测试选择了角色: {character_name}")
        print("UI布局测试完成！")
        sys.exit(0)

def main():
    """主函数"""
    try:
        app = UILayoutTest()
        app.run()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()