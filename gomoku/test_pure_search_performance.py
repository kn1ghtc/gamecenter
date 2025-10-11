"""纯搜索性能测试 - 禁用killer moves检测
测试Python AI引擎的实际搜索性能，不依赖快速胜利检测
"""

import time
from gamecenter.gomoku.game_logic import Board, Player
from gamecenter.gomoku.ai_engine import OptimizedAIController as Phase1AI
from gamecenter.gomoku.ai_engine_phase2 import Phase2AIController


def create_complex_midgame_board():
    """创建复杂中局，无即时胜利可能"""
    board = Board()
    # 分散分布，制造多个威胁方向
    moves = [
        # 区域1: 中心
        (7, 7, Player.BLACK), (7, 9, Player.WHITE),
        (9, 7, Player.BLACK), (9, 9, Player.WHITE),
        # 区域2: 左上
        (5, 5, Player.BLACK), (5, 6, Player.WHITE),
        (4, 5, Player.BLACK), (6, 6, Player.WHITE),
        # 区域3: 右下
        (10, 10, Player.BLACK), (10, 11, Player.WHITE),
        (11, 10, Player.BLACK), (11, 11, Player.WHITE),
        # 区域4: 左下
        (11, 5, Player.BLACK), (11, 6, Player.WHITE),
        (10, 5, Player.BLACK), (12, 6, Player.WHITE),
        # 区域5: 右上
        (5, 11, Player.BLACK), (5, 12, Player.WHITE),
        (4, 11, Player.BLACK), (6, 12, Player.WHITE),
    ]
    for row, col, player in moves:
        board.place_stone(row, col, player)
    return board


def test_pure_search_phase1():
    """测试Phase 1纯搜索性能"""
    print("\n" + "="*70)
    print(" Phase 1 纯搜索性能测试 (禁用Killer Moves)")
    print("="*70)
    
    board = create_complex_midgame_board()
    ai = Phase1AI(difficulty="medium", time_limit=3.0)
    
    # 初始化搜索状态
    ai.nodes_searched = 0
    ai.search_start_time = time.time()
    ai.current_hash = ai.zobrist.compute_hash(board)
    
    # 直接调用迭代加深搜索，跳过killer move检测
    start = time.time()
    best_move = ai._iterative_deepening_search(board, Player.BLACK)
    elapsed = time.time() - start
    
    # 设置search_time以便统计计算
    ai.search_time = elapsed
    stats = ai.get_stats()
    print(f"  最佳着法: {best_move}")
    print(f"  搜索时间: {elapsed:.3f}秒")
    print(f"  搜索节点: {stats.get('nodes_searched', 0)}")
    print(f"  搜索速度: {stats.get('nodes_per_second', 0):.0f} nps")
    print(f"  TT命中率: {stats.get('tt_hit_rate', 0):.1%}")
    
    nps = stats.get('nodes_per_second', 0)
    if nps >= 3000:
        print(f"  ✅ 达到目标 (3000+ nps): {(nps/3000)*100:.1f}%")
    else:
        print(f"  ❌ 未达目标 (3000 nps): {(nps/3000)*100:.1f}%")
    
    return nps


def test_pure_search_phase2():
    """测试Phase 2纯搜索性能"""
    print("\n" + "="*70)
    print(" Phase 2 纯搜索性能测试 (禁用Killer Moves)")
    print("="*70)
    
    board = create_complex_midgame_board()
    ai = Phase2AIController(difficulty="medium", time_limit=3.0)
    
    # 初始化搜索状态
    ai.nodes_searched = 0
    ai.search_start_time = time.time()
    ai.current_hash = ai.zobrist.compute_hash(board)
    
    # 直接调用迭代加深搜索，跳过killer move检测
    start = time.time()
    best_move = ai._iterative_deepening_search(board, Player.BLACK)
    elapsed = time.time() - start
    
    # 设置search_time以便统计计算
    ai.search_time = elapsed
    stats = ai.get_stats()
    print(f"  最佳着法: {best_move}")
    print(f"  搜索时间: {elapsed:.3f}秒")
    print(f"  搜索节点: {stats.get('nodes_searched', 0)}")
    print(f"  搜索速度: {stats.get('nodes_per_second', 0):.0f} nps")
    print(f"  TT命中率: {stats.get('tt_hit_rate', 0):.1%}")
    
    nps = stats.get('nodes_per_second', 0)
    if nps >= 3000:
        print(f"  ✅ 达到目标 (3000+ nps): {(nps/3000)*100:.1f}%")
    else:
        print(f"  ❌ 未达目标 (3000 nps): {(nps/3000)*100:.1f}%")
    
    return nps


def main():
    print("\n" + "="*70)
    print(" 五子棋AI引擎纯搜索性能测试")
    print(" 禁用Killer Moves，专注测试搜索算法性能")
    print("="*70)
    
    # 测试Phase 1
    nps1 = test_pure_search_phase1()
    
    # 测试Phase 2
    nps2 = test_pure_search_phase2()
    
    # 总结
    print("\n" + "="*70)
    print(" 测试总结")
    print("="*70)
    print(f"\nPhase 1 性能: {nps1:.0f} nps")
    print(f"Phase 2 性能: {nps2:.0f} nps")
    
    if nps1 > 0 and nps2 > 0:
        if nps2 > nps1:
            improvement = (nps2 / nps1 - 1) * 100
            print(f"\n✅ Phase 2 提升: +{improvement:.1f}%")
        else:
            degradation = (1 - nps2 / nps1) * 100
            print(f"\n⚠️  Phase 2 退化: -{degradation:.1f}%")
    elif nps1 == 0 and nps2 == 0:
        print(f"\n⚠️  两个引擎都未进行搜索 (可能因为立即找到解决方案)")
    
    if nps2 >= 3000:
        print(f"\n🎉 Phase 2 达到3000+ NPS目标！")
    else:
        shortfall = 3000 - nps2
        print(f"\n❌ Phase 2 未达标，差距: {shortfall:.0f} nps ({(nps2/3000)*100:.1f}%)")
    
    print("="*70)


if __name__ == "__main__":
    main()
