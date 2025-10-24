#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
游戏可玩性验证脚本
检查每个游戏文件的完整性和基本功能
"""

import os
from pathlib import Path
import json

class GameValidator:
    """游戏验证器"""
    
    def __init__(self):
        self.games_base = Path(__file__).parent.parent / 'frontend' / 'games'
        self.results = []
    
    def check_game_files(self, game_path, game_name):
        """检查游戏文件完整性 - 支持 Canvas 和 DOM-based 两种实现"""
        issues = []
        
        # 检查index.html
        index_html = game_path / 'index.html'
        if not index_html.exists():
            issues.append("缺少 index.html")
        else:
            with open(index_html, 'r', encoding='utf-8') as f:
                content = f.read()
                # 支持 Canvas 或 DOM 两种实现方式
                has_canvas = 'gameCanvas' in content or '<canvas' in content
                has_dom_structure = 'gameContainer' in content or 'gameBoard' in content or 'game-container' in content
                
                if not has_canvas and not has_dom_structure:
                    issues.append("缺少游戏画布或 DOM 结构")
                    
                if 'game.js' not in content:
                    issues.append("未引入 game.js")
        
        # 检查game.js
        game_js = game_path / 'game.js'
        if not game_js.exists():
            issues.append("缺少 game.js")
        else:
            # 检查game.js的基本结构
            with open(game_js, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查是否有初始化逻辑
                has_init = any(keyword in content for keyword in [
                    'constructor', 'function', 'class ',
                    'new Game', 'addEventListener'
                ])
                if not has_init:
                    issues.append("缺少初始化逻辑")
                
                # 检查是否有游戏逻辑 - Canvas 或 DOM 方式
                has_game_logic = any(keyword in content for keyword in [
                    'gameLoop', 'update', 'draw', 'render',
                    'move', 'keydown', 'init', 'requestAnimationFrame'
                ])
                if not has_game_logic:
                    issues.append("缺少游戏逻辑")
        
        return issues
    
    def validate_all_games(self):
        """验证所有游戏"""
        print("=" * 70)
        print("🎮 游戏可玩性验证")
        print("=" * 70 + "\n")
        
        categories = {
            'casual': {'name': '休闲游戏', 'games': []},
            'arcade': {'name': '街机游戏', 'games': []},
            'puzzle': {'name': '益智游戏', 'games': []},
            'shooting': {'name': '射击游戏', 'games': []},
            'action': {'name': '动作游戏', 'games': []},
        }
        
        # 遍历所有游戏目录
        for category in self.games_base.iterdir():
            if not category.is_dir():
                continue
            
            category_name = category.name
            if category_name not in categories:
                continue
            
            print(f"\n📁 {categories[category_name]['name']}:")
            
            for game_dir in category.iterdir():
                if not game_dir.is_dir():
                    continue
                
                game_name = game_dir.name
                issues = self.check_game_files(game_dir, game_name)
                
                status = "✓" if not issues else "⚠"
                print(f"  {status} {game_name}")
                
                if issues:
                    for issue in issues:
                        print(f"      → {issue}")
                
                result = {
                    'category': category_name,
                    'game': game_name,
                    'status': 'OK' if not issues else 'WARNING',
                    'issues': issues
                }
                self.results.append(result)
                categories[category_name]['games'].append(result)
        
        # 输出总结
        print("\n" + "=" * 70)
        self.print_summary()
        print("=" * 70)
        
        return self.results
    
    def print_summary(self):
        """输出验证总结"""
        total = len(self.results)
        ok = sum(1 for r in self.results if r['status'] == 'OK')
        warning = sum(1 for r in self.results if r['status'] == 'WARNING')
        
        print(f"📊 验证结果: {ok}/{total} 完整 ({warning} 个警告)")
        
        if warning > 0:
            print(f"\n⚠️  有问题的游戏:")
            for result in self.results:
                if result['status'] == 'WARNING':
                    print(f"  • {result['game']}")
                    for issue in result['issues']:
                        print(f"    - {issue}")

def main():
    validator = GameValidator()
    validator.validate_all_games()

if __name__ == '__main__':
    main()
