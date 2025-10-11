"""AI性能测试脚本
测试优化前后的AI性能对比。
"""

import time
from gamecenter.gomoku.game_logic import Board, Player
from gamecenter.gomoku.ai_engine import create_ai
from gamecenter.gomoku.ai_engine_optimized import create_optimized_ai


def test_ai_performance():
    """测试AI性能"""
    print("=" * 60)
    print("五子棋AI性能测试")
    print("=" * 60)
    
    # 创建测试棋盘（中局复杂局面，无杀棋）
    board = Board()
    test_moves = [
        (7, 7), (7, 9),   # 黑白相距较远
        (8, 6), (6, 9),
        (6, 6), (8, 9),
        (5, 8), (9, 7),
        (9, 5), (5, 10),
        (10, 6), (4, 10),
    ]
    
    for i, (row, col) in enumerate(test_moves):
        player = Player.BLACK if i % 2 == 0 else Player.WHITE
        board.place_stone(row, col, player)
    
    print(f"\n测试局面：已落子{len(board.history)}步")
    print(f"当前玩家：{board.current_player.value}")
    print()
    
    # 测试不同难度
    difficulties = ['easy', 'medium', 'hard']
    
    for difficulty in difficulties:
        print(f"\n{'='*60}")
        print(f"难度: {difficulty.upper()}")
        print(f"{'='*60}")
        
        # 旧版AI
        print("\n【旧版AI】")
        old_ai = create_ai(difficulty)
        start = time.time()
        try:
            move = old_ai.find_best_move(board, Player.BLACK)
            elapsed = time.time() - start
            stats = old_ai.get_stats()
            print(f"  着法: {move}")
            print(f"  耗时: {elapsed:.3f}秒")
            print(f"  节点: {stats['nodes_searched']}")
            print(f"  速度: {stats['nodes_per_second']:.0f} nps")
        except Exception as e:
            print(f"  错误: {e}")
        
        # 新版AI
        print("\n【优化AI】")
        new_ai = create_optimized_ai(difficulty, time_limit=5.0)
        start = time.time()
        try:
            move = new_ai.find_best_move(board, Player.BLACK)
            elapsed = time.time() - start
            stats = new_ai.get_stats()
            print(f"  着法: {move}")
            print(f"  耗时: {elapsed:.3f}秒")
            print(f"  节点: {stats['nodes_searched']}")
            print(f"  速度: {stats['nodes_per_second']:.0f} nps")
            print(f"  TT命中率: {stats['tt_hit_rate']:.1%}")
            print(f"  TT大小: {stats['tt_size']}")
        except Exception as e:
            import traceback
            print(f"  错误: {e}")
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("测试完成！")
    print(f"{'='*60}")


if __name__ == '__main__':
    test_ai_performance()
