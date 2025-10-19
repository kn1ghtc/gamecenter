#!/usr/bin/env python3
"""测试 macOS C++ 引擎"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gamecenter.gomoku.cpp_engine.cpp_ai_wrapper import CppAIEngine
from gamecenter.gomoku.game_logic import Board, Player


def main():
    print('🔧 测试 C++ 引擎加载...')
    try:
        engine = CppAIEngine()
        print('✅ C++ 引擎加载成功！')

        print('\n🎮 测试基本功能...')
        board = Board()
        board.place_stone(7, 7, Player.BLACK)

        move = engine.find_best_move(board, Player.WHITE, max_depth=5, time_limit=2.0)
        print(f'✅ AI 找到最佳落子: {move}')

        stats = engine.get_stats()
        print(f'\n📊 搜索统计:')
        print(f'  - 搜索节点: {stats["nodes_searched"]:,}')
        print(f'  - 搜索时间: {stats["search_time"]:.3f}s')
        print(f'  - NPS: {stats["nodes_per_second"]:,.0f}')
        print(f'  - 引擎类型: {stats["engine"]}')

        print('\n🎉 所有测试通过！macOS C++ 引擎工作正常！')
        return 0

    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
