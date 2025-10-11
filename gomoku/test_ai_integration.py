"""完整的AI引擎集成测试
Test all AI engines (Python Phase 1, Phase 2, C++) with automatic fallback.
"""

import time
from gamecenter.gomoku.game_logic import Board, Player
from gamecenter.gomoku.ai_engine_manager import create_ai_engine, EngineType

def create_test_board():
    """创建复杂测试局面 - 避免killer moves，强制深度搜索"""
    board = Board()
    # 制造复杂的中局对抗，多个威胁方向，无明显获胜
    moves = [
        # 中心区域对抗
        (7, 7, Player.BLACK), (7, 8, Player.WHITE),
        (8, 7, Player.BLACK), (6, 8, Player.WHITE),
        (6, 7, Player.BLACK), (8, 8, Player.WHITE),
        # 左侧分支威胁
        (7, 5, Player.BLACK), (6, 5, Player.WHITE),
        (8, 5, Player.BLACK), (7, 4, Player.WHITE),
        # 右侧分支威胁
        (7, 10, Player.BLACK), (6, 10, Player.WHITE),
        (8, 10, Player.BLACK), (7, 11, Player.WHITE),
        # 上方分支威胁
        (4, 7, Player.BLACK), (4, 8, Player.WHITE),
        (3, 7, Player.BLACK), (4, 6, Player.WHITE),
        # 下方分支威胁
        (10, 7, Player.BLACK), (10, 8, Player.WHITE),
        (11, 7, Player.BLACK), (10, 6, Player.WHITE),
    ]
    for row, col, player in moves:
        board.place_stone(row, col, player)
    return board

def test_engine(engine_type_str: str, difficulty: str):
    """测试单个引擎"""
    print(f"\n{'='*70}")
    print(f" 测试引擎: {engine_type_str.upper()} | 难度: {difficulty.upper()}")
    print(f"{'='*70}")
    
    try:
        # 创建引擎
        ai = create_ai_engine(engine_type_str, difficulty, time_limit=3.0)
        print(f"✅ 引擎创建成功: {ai.get_engine_name()}")
        
        # 创建测试局面
        board = create_test_board()
        
        # 运行AI
        start = time.time()
        best_move = ai.find_best_move(board, Player.BLACK)
        elapsed = time.time() - start
        
        # 获取统计
        stats = ai.get_stats()
        
        print(f"  最佳着法: {best_move}")
        print(f"  搜索时间: {elapsed:.3f}秒")
        
        if 'nodes_searched' in stats:
            print(f"  搜索节点: {stats['nodes_searched']}")
        if 'nodes_per_second' in stats:
            nps = stats['nodes_per_second']
            print(f"  搜索速度: {nps:.0f} nps")
            if nps >= 3000:
                print(f"  ✅ 达到目标 (3000+ nps): {(nps/3000)*100:.1f}%")
            else:
                print(f"  ⚠️  未达目标 (3000 nps): {(nps/3000)*100:.1f}%")
        if 'tt_hit_rate' in stats:
            print(f"  TT命中率: {stats['tt_hit_rate']:.1%}")
        if 'cpp_failures' in stats and stats['cpp_failures'] > 0:
            print(f"  ⚠️  C++失败次数: {stats['cpp_failures']}")
        if 'fallback_count' in stats and stats['fallback_count'] > 0:
            print(f"  ℹ️  回退次数: {stats['fallback_count']}")
        
        return True, elapsed, stats.get('nodes_per_second', 0)
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0

def main():
    print("="*70)
    print(" 五子棋AI引擎完整集成测试")
    print(" 测试项目:")
    print("   1. Python Phase 1引擎 (基础优化)")
    print("   2. Python Phase 2引擎 (高级优化)")
    print("   3. C++引擎 (原生性能)")
    print("   4. 自动模式 (优先C++，自动回退)")
    print("="*70)
    
    test_cases = [
        ('python_phase1', 'medium'),
        ('python_phase2', 'medium'),
        ('cpp', 'medium'),
        ('auto', 'medium'),
    ]
    
    results = []
    
    for engine_type, difficulty in test_cases:
        success, elapsed, nps = test_engine(engine_type, difficulty)
        results.append({
            'engine': engine_type,
            'success': success,
            'time': elapsed,
            'nps': nps
        })
        time.sleep(0.5)  # 短暂暂停
    
    # 总结
    print(f"\n{'='*70}")
    print(" 测试总结")
    print(f"{'='*70}\n")
    
    print(f"{'引擎类型':<20} {'状态':<8} {'时间(s)':<10} {'NPS':<12} {'达标'}")
    print(f"{'-'*70}")
    
    for r in results:
        status = "✅ 成功" if r['success'] else "❌ 失败"
        nps_str = f"{r['nps']:.0f}" if r['nps'] > 0 else "N/A"
        达标 = "✅" if r['nps'] >= 3000 else ("⚠️" if r['nps'] > 0 else "❌")
        print(f"{r['engine']:<20} {status:<8} {r['time']:<10.3f} {nps_str:<12} {达标}")
    
    print(f"{'-'*70}")
    
    # 检查是否有任何引擎达标
    max_nps = max([r['nps'] for r in results])
    successful = sum([1 for r in results if r['success']])
    达标_count = sum([1 for r in results if r['nps'] >= 3000])
    
    print(f"\n统计:")
    print(f"  成功引擎: {successful}/{len(results)}")
    print(f"  达标引擎 (3000+ nps): {达标_count}/{len(results)}")
    print(f"  最高性能: {max_nps:.0f} nps")
    
    if 达标_count > 0:
        print(f"\n🎉 测试通过！至少有{达标_count}个引擎达到3000+ NPS目标")
    else:
        print(f"\n⚠️  警告：没有引擎达到3000 NPS目标")
    
    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()
