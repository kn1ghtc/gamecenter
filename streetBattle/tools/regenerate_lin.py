#!/usr/bin/env python3
"""
Lin Character Image Regeneration
为Lin角色重新生成图片（使用更安全的提示词）
"""

import os
import sys
import openai
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def regenerate_lin_character():
    """重新生成Lin角色图片"""
    print("🎭 重新生成Lin角色图片")
    print("=" * 30)
    
    # 更安全的Lin角色描述
    lin_prompt = "A skilled martial artist with short dark hair in traditional fighting stance, wearing dark clothing with gold accents, ready for combat pose, full body view, single person only, anime style character design, King of Fighters game style, detailed artwork suitable for game sprites"
    
    try:
        # 检查API密钥
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ 未找到OPENAI_API_KEY环境变量")
            return False
        
        client = openai.OpenAI(api_key=api_key)
        portraits_dir = project_root / "assets" / "images" / "portraits"
        
        print("🎨 正在为Lin生成新的全身动作图片...")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=lin_prompt,
            size="1024x1024",
            quality="hd",
            style="vivid",
            n=1
        )
        
        if response.data:
            image_url = response.data[0].url
            print("  ✓ 图像生成成功: Lin")
            
            # 下载图像
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            # 保存图像
            output_path = portraits_dir / "lin.png"
            with open(output_path, 'wb') as f:
                f.write(img_response.content)
            
            print(f"  ✅ 保存成功: {output_path}")
            return True
        else:
            print("  ❌ 图像生成失败: Lin")
            return False
            
    except Exception as e:
        print(f"  ❌ 生成异常: {e}")
        return False

if __name__ == "__main__":
    regenerate_lin_character()