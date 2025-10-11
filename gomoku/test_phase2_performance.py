"""测试Phase 2优化AI的性能
Test Phase 2 optimized AI performance
"""

import time
from gamecenter.gomoku.game_logic import Board, Player
from gamecenter.gomoku.ai_engine_phase2 import Phase2AIController, DifficultyLevel

def create_test_board():
    """创建测试局面"""
    board = Board()
    # 添加一些棋子创建中局局面
    moves = [
        (7, 7, Player.BLACK),
        (7, 8, Player.WHITE),
        (8, 7, Player.BLACK),
        (8, 8, Player.WHITE),
        (6, 7, Player.BLACK),
        (6, 8, Player.WHITE),
        (9, 7, Player.BLACK),
        (9, 8, Player.WHITE),
        (7, 6, Player.BLACK),
        (7, 9, Player.WHITE),
        (8, 6, Player.BLACK),
        (8, 9, Player.WHITE),
    ]
    
    for row, col, player in moves:
        board.place_stone(row, col, player)
    
    return board

def test_ai_performance(difficulty_name: str, depth: int):
    """测试AI性能"""
    difficulty_map = {
        'easy': DifficultyLevel.EASY,
        'medium': DifficultyLevel.MEDIUM,
        'hard': DifficultyLevel.HARD
    }
    
    difficulty = difficulty_map[difficulty_name]
    ai = Phase2AIController(difficulty, time_limit=5.0)
    board = create_test_board()
    
    print(f"\n{'='*60}")
    print(f"测试配置: {difficulty_name.upper()} (深度={depth})")
    print(f"{'='*60}")
    
    # 运行AI搜索
    start = time.time()
    best_move = ai.find_best_move(board, Player.BLACK)
    elapsed = time.time() - start
    
    # 获取统计信息
    stats = ai.get_stats()
    
    print(f"最佳着法: {best_move}")
    print(f"搜索节点: {stats['nodes_searched']}")
    print(f"搜索时间: {elapsed:.3f}秒")
    print(f"搜索速度: {stats['nodes_per_second']:.0f} nps")
    print(f"TT命中率: {stats['tt_hit_rate']:.1%}")
    print(f"TT大小: {stats['tt_size']}")
    
    return stats['nodes_per_second']

def main():
    print("="*60)
    print(" Phase 2 AI性能测试")
    print(" 目标: 3000+ NPS")
    print("="*60)
    
    results = {}
    
    # 测试三个难度
    for difficulty, depth in [('easy', 3), ('medium', 5), ('hard', 7)]:
        nps = test_ai_performance(difficulty, depth)
        results[difficulty] = nps
    
    # 总结
    print(f"\n{'='*60}")
    print(" 性能测试总结")
    print(f"{'='*60}")
    
    avg_nps = sum(results.values()) / len(results)
    
    print(f"\n难度       NPS        目标达成")
    print(f"{'-'*60}")
    for difficulty, nps in results.items():
        status = "✅" if nps >= 3000 else "❌"
        percentage = (nps / 3000) * 100
        print(f"{difficulty:8}  {nps:8.0f}   {status} {percentage:.1f}%")
    
    print(f"{'-'*60}")
    print(f"平均     {avg_nps:8.0f}   {'✅' if avg_nps >= 3000 else '❌'} {(avg_nps/3000)*100:.1f}%")
    print(f"\n{'='*60}")
    
    if avg_nps >= 3000:
        print("🎉 Phase 2优化成功！已达到3000+ NPS目标")
    else:
        print(f"⚠️  还需提升 {3000 - avg_nps:.0f} NPS 才能达标")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
