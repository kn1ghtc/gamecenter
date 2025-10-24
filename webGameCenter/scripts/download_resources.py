#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
游戏资源下载脚本
下载并集成高质量的游戏资源
"""

import os
import requests
from pathlib import Path
from urllib.parse import urlparse

# 游戏资源配置 - 资源来自 CC0/CC-BY licensed 来源
GAMES_RESOURCES = {
    'flappybird': {
        'name': '飞翔的鸟',
        'assets': {
            'bird.png': 'https://cdn-icons-png.flaticon.com/512/1721/1721220.png',
        }
    },
    'dinosaur': {
        'name': '小恐龙',
        'assets': {
            'dino.png': 'https://cdn-icons-png.flaticon.com/512/1721/1721201.png',
        }
    },
    'pacman': {
        'name': '吃豆人',
        'assets': {
            'pacman.png': 'https://cdn-icons-png.flaticon.com/512/1721/1721291.png',
        }
    },
    'snake': {
        'name': '贪吃蛇',
        'assets': {
            'segment.png': 'https://cdn-icons-png.flaticon.com/512/1721/1721282.png',
        }
    },
    '2048': {
        'name': '2048',
        'assets': {}
    },
    'tetris': {
        'name': '俄罗斯方块',
        'assets': {}
    },
    'minesweeper': {
        'name': '扫雷',
        'assets': {}
    },
    'sokoban': {
        'name': '推箱子',
        'assets': {}
    },
    'breakout': {
        'name': '打砖块',
        'assets': {}
    },
    'space_shooter': {
        'name': '太空射击',
        'assets': {}
    },
    'tankbattle': {
        'name': '坦克大战',
        'assets': {}
    },
    'contra': {
        'name': '魂斗罗',
        'assets': {}
    },
    'kof': {
        'name': '拳皇',
        'assets': {}
    }
}

def ensure_assets_directory():
    """确保资源目录存在"""
    assets_base = Path(__file__).parent.parent / 'frontend' / 'assets'
    assets_base.mkdir(parents=True, exist_ok=True)
    return assets_base

def download_resource(url, save_path):
    """下载单个资源文件"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        pass
    return False

def main():
    """主函数 - 下载游戏资源"""
    print("=" * 70)
    print("🎮 游戏资源下载管理器")
    print("=" * 70)
    
    assets_base = ensure_assets_directory()
    print(f"\n📁 资源目录: {assets_base}\n")
    
    total_games = len(GAMES_RESOURCES)
    downloaded = 0
    skipped = 0
    
    for game_id, game_config in GAMES_RESOURCES.items():
        game_name = game_config['name']
        assets_count = len(game_config.get('assets', {}))
        
        if assets_count == 0:
            print(f"⊘ {game_name}: 暂无资源下载")
            skipped += 1
            continue
        
        print(f"📥 {game_name}:")
        game_assets_dir = assets_base / game_id
        
        for asset_name, asset_url in game_config['assets'].items():
            save_path = game_assets_dir / asset_name
            
            if save_path.exists():
                print(f"   ✓ {asset_name} (已存在)")
                continue
            
            if download_resource(asset_url, save_path):
                print(f"   ✓ {asset_name} (已下载)")
                downloaded += 1
            else:
                print(f"   ✗ {asset_name} (下载失败)")
    
    print("\n" + "=" * 70)
    print(f"📊 统计: {downloaded} 已下载, {skipped} 无资源, {total_games} 总计")
    print("=" * 70)

if __name__ == '__main__':
    main()
