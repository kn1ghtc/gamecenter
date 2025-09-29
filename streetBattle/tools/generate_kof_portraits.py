#!/usr/bin/env python3
"""
使用OpenAI DALL-E 3生成缺失的KOF角色肖像图片
"""
import os
import json
import requests
import urllib3
from pathlib import Path
from openai import OpenAI
from PIL import Image
import time

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KOFPortraitGenerator:
    def __init__(self):
        self.client = OpenAI()
        self.output_dir = Path("assets/images/portraits")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # KOF角色描述信息，用于生成更准确的图像
        self.character_descriptions = {
            'angel': "Angel from King of Fighters, female NESTS agent with silver/white hair, black leather outfit, combat boots, confident pose, fighting stance",
            'choi_bounge': "Choi Bounge from King of Fighters, small Korean fighter with claws, orange/yellow uniform, spiky hair, evil grin, martial arts pose",
            'goro_daimon': "Goro Daimon from King of Fighters, large Japanese judoka, white judo gi, black belt, muscular build, serious expression, grappling stance",
            'igniz': "Igniz from King of Fighters, NESTS final boss, white/silver armor, cape, godlike appearance, floating pose, divine aura",
            'lin': "Lin from King of Fighters, Chinese assassin, dark outfit, mysterious appearance, martial arts stance, serious expression",
            'magaki': "Magaki from King of Fighters, pale otherworldly being, long dark hair, mysterious robes, supernatural aura, boss character",
            'mr_big': "Mr. Big from King of Fighters, tall crime boss, suit and tie, sunglasses, cane/stick weapon, confident pose, mafia style",
            'orochi': "Orochi from King of Fighters, legendary serpent entity, pale skin, long silver/white hair, dark robes, mystical aura, godlike presence",
            'ramon': "Ramon from King of Fighters, Mexican luchador wrestler, colorful wrestling mask, muscular build, wrestling pose, energetic stance",
            'saisyu_kusanagi': "Saisyu Kusanagi from King of Fighters, Kyo's father, older Japanese martial artist, traditional outfit, flame powers, wise expression",
            'sie_kensou': "Sie Kensou from King of Fighters, young Chinese psychic fighter, casual clothes, energetic pose, psychic powers effect",
            'wolfgang_krauser': "Wolfgang Krauser from King of Fighters/Fatal Fury, tall German nobleman, blue military uniform, blonde hair, imposing presence, aristocratic pose"
        }
    
    def load_valid_characters(self):
        """从resource_catalog.json加载有效角色列表"""
        catalog_path = Path("assets/resource_catalog.json")
        if not catalog_path.exists():
            print(f"Error: {catalog_path} not found!")
            return set()
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return set(data.keys())
    
    def get_missing_characters(self):
        """获取缺失肖像的角色列表"""
        valid_chars = self.load_valid_characters()
        existing_portraits = set()
        
        for f in self.output_dir.glob('*.png'):
            name = f.stem.replace('_official', '')
            existing_portraits.add(name)
        
        missing = valid_chars - existing_portraits
        return sorted(missing)
    
    def generate_character_portrait(self, character_name, max_retries=3):
        """为指定角色生成肖像"""
        print(f"正在生成角色肖像: {character_name}")
        
        # 构建提示词
        base_prompt = f"High quality official artwork portrait of {self.character_descriptions.get(character_name, character_name)} from King of Fighters video game series"
        style_prompt = ", professional game character art, clean background, detailed illustration, fighting game style, SNK art style, high resolution"
        full_prompt = base_prompt + style_prompt
        
        for attempt in range(max_retries):
            try:
                print(f"  尝试 {attempt + 1}/{max_retries}: 调用DALL-E 3...")
                
                # 调用OpenAI DALL-E 3
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=full_prompt,
                    n=1,
                    size="1024x1024",
                    quality="hd",
                    style="vivid"
                )
                
                image_url = response.data[0].url
                print(f"  生成图像URL: {image_url}")
                
                # 下载图像
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                
                # 保存图像
                output_path = self.output_dir / f"{character_name}_official.png"
                
                # 使用PIL处理图像以确保格式正确
                img = Image.open(requests.get(image_url, stream=True).raw)
                img = img.convert('RGBA')  # 确保支持透明度
                img.save(output_path, "PNG", optimize=True)
                
                print(f"  ✓ 成功保存: {output_path}")
                return True
                
            except Exception as e:
                print(f"  ✗ 生成失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"  等待3秒后重试...")
                    time.sleep(3)
                continue
        
        print(f"  ✗ 角色 {character_name} 生成失败，已达到最大重试次数")
        return False
    
    def generate_all_missing_portraits(self):
        """生成所有缺失的角色肖像"""
        print("=== KOF角色肖像生成器 ===")
        print(f"输出目录: {self.output_dir.absolute()}")
        
        # 检查API密钥
        if not os.environ.get('OPENAI_API_KEY'):
            print("错误: 未找到OPENAI_API_KEY环境变量")
            return False
        
        missing_characters = self.get_missing_characters()
        
        if not missing_characters:
            print("所有角色肖像已存在，无需生成")
            return True
        
        print(f"发现 {len(missing_characters)} 个缺失的角色肖像:")
        for char in missing_characters:
            print(f"  - {char}")
        
        print("\n开始生成角色肖像...")
        
        success_count = 0
        total_count = len(missing_characters)
        
        for i, character in enumerate(missing_characters, 1):
            print(f"\n[{i}/{total_count}] 处理角色: {character}")
            
            if self.generate_character_portrait(character):
                success_count += 1
            
            # 避免API速率限制，每次请求间隔
            if i < total_count:
                print("  等待5秒避免API限制...")
                time.sleep(5)
        
        print(f"\n=== 生成完成 ===")
        print(f"成功生成: {success_count}/{total_count} 个角色肖像")
        
        if success_count == total_count:
            print("🎉 所有缺失的角色肖像已成功生成!")
            return True
        else:
            print(f"⚠️  {total_count - success_count} 个角色生成失败，请检查错误信息")
            return False
    
    def verify_generated_portraits(self):
        """验证生成的肖像图片"""
        print("\n=== 验证生成的肖像图片 ===")
        
        valid_chars = self.load_valid_characters()
        verified_count = 0
        
        for character in valid_chars:
            portrait_path = self.output_dir / f"{character}_official.png"
            if portrait_path.exists():
                try:
                    # 验证图片可以正常加载
                    img = Image.open(portrait_path)
                    width, height = img.size
                    print(f"✓ {character}: {width}x{height} pixels")
                    verified_count += 1
                except Exception as e:
                    print(f"✗ {character}: 图片损坏 - {e}")
            else:
                print(f"✗ {character}: 文件不存在")
        
        print(f"\n验证结果: {verified_count}/{len(valid_chars)} 个角色肖像有效")
        return verified_count == len(valid_chars)

def main():
    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"工作目录: {os.getcwd()}")
    
    generator = KOFPortraitGenerator()
    
    # 生成缺失的肖像
    success = generator.generate_all_missing_portraits()
    
    if success:
        # 验证生成的肖像
        generator.verify_generated_portraits()
        print("\n🎉 所有任务完成!")
    else:
        print("\n⚠️  部分任务失败，请检查错误信息")

if __name__ == "__main__":
    main()