"""AI性能对比测试
Compare Python-optimized AI vs C++-integrated AI
"""

import time
from gamecenter.gomoku.game_logic import Board, Player
from gamecenter.gomoku.ai_engine import create_optimized_ai

# Try to import C++ engine
try:
    from gamecenter.gomoku.cpp_engine.cpp_ai_wrapper import create_cpp_ai
    CPP_AVAILABLE = True
except (ImportError, FileNotFoundError) as e:
    print(f"⚠️  C++ engine not available: {e}")
    print("   Please compile C++ engine first!")
    print("   See cpp_engine/BUILD.md for instructions")
    CPP_AVAILABLE = False


def create_test_board():
    """Create complex mid-game position"""
    board = Board()
    test_moves = [
        (7, 7), (7, 9),
        (8, 6), (6, 9),
        (6, 6), (8, 9),
        (5, 8), (9, 7),
        (9, 5), (5, 10),
        (10, 6), (4, 10),
    ]
    
    for i, (row, col) in enumerate(test_moves):
        player = Player.BLACK if i % 2 == 0 else Player.WHITE
        board.place_stone(row, col, player)
    
    return board


def test_ai_performance(ai_engine, name: str, board: Board, difficulty: str):
    """Test AI performance"""
    print(f"\n{'='*60}")
    print(f"{name} - {difficulty.upper()}")
    print(f"{'='*60}")
    
    start = time.time()
    try:
        move = ai_engine.find_best_move(board, Player.BLACK)
        elapsed = time.time() - start
        
        stats = ai_engine.get_stats()
        
        print(f"  着法: {move}")
        print(f"  耗时: {elapsed:.3f}秒")
        print(f"  节点: {stats['nodes_searched']}")
        print(f"  速度: {stats['nodes_per_second']:.0f} nps")
        
        if 'tt_hit_rate' in stats:
            print(f"  TT命中率: {stats['tt_hit_rate']:.1%}")
        
        if 'engine' in stats:
            print(f"  引擎: {stats['engine']}")
        
        return stats['nodes_per_second'], elapsed
        
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0


def main():
    """Main comparison test"""
    print("=" * 70)
    print(" 五子棋AI性能对比测试")
    print(" Python优化版 vs C++集成版")
    print("=" * 70)
    
    # Create test board
    board = create_test_board()
    print(f"\n测试局面：已落子{len(board.history)}步")
    print(f"当前玩家：{board.current_player.value}\n")
    
    # Test difficulties
    difficulties = {
        'easy': {'depth': 3, 'time': 2.0},
        'medium': {'depth': 5, 'time': 3.0},
        'hard': {'depth': 7, 'time': 5.0}
    }
    
    results = {}
    
    for diff_name, params in difficulties.items():
        results[diff_name] = {}
        
        print(f"\n{'#' * 70}")
        print(f"# 难度: {diff_name.upper()} (深度={params['depth']}, 时限={params['time']}s)")
        print(f"{'#' * 70}")
        
        # Test Python AI
        print("\n【Python优化AI】")
        python_ai = create_optimized_ai(diff_name, time_limit=params['time'])
        py_nps, py_time = test_ai_performance(python_ai, "Python优化AI", board, diff_name)
        results[diff_name]['python'] = {'nps': py_nps, 'time': py_time}
        
        # Test C++ AI (if available)
        if CPP_AVAILABLE:
            print("\n【C++集成AI】")
            try:
                cpp_ai = create_cpp_ai(max_depth=params['depth'], time_limit=params['time'])
                cpp_nps, cpp_time = test_ai_performance(cpp_ai, "C++集成AI", board, diff_name)
                results[diff_name]['cpp'] = {'nps': cpp_nps, 'time': cpp_time}
            except Exception as e:
                print(f"  C++引擎加载失败: {e}")
                results[diff_name]['cpp'] = {'nps': 0, 'time': 0}
        else:
            print("\n【C++集成AI】")
            print("  ⚠️  C++引擎未编译，跳过测试")
            results[diff_name]['cpp'] = {'nps': 0, 'time': 0}
    
    # Summary report
    print("\n" + "=" * 70)
    print(" 性能对比总结")
    print("=" * 70)
    
    print(f"\n{'难度':<10} {'Python NPS':<15} {'C++ NPS':<15} {'加速比':<10} {'时间比'}")
    print("-" * 70)
    
    for diff_name in difficulties.keys():
        py = results[diff_name]['python']
        cpp = results[diff_name]['cpp']
        
        if cpp['nps'] > 0:
            speedup = cpp['nps'] / py['nps'] if py['nps'] > 0 else 0
            time_ratio = py['time'] / cpp['time'] if cpp['time'] > 0 else 0
            
            print(f"{diff_name:<10} {py['nps']:<15.0f} {cpp['nps']:<15.0f} {speedup:<10.2f}x {time_ratio:<.2f}x")
        else:
            print(f"{diff_name:<10} {py['nps']:<15.0f} {'N/A':<15} {'N/A':<10} {'N/A'}")
    
    print("\n" + "=" * 70)
    
    # Conclusion
    if CPP_AVAILABLE and any(results[d]['cpp']['nps'] > 0 for d in difficulties.keys()):
        avg_speedup = sum(
            results[d]['cpp']['nps'] / results[d]['python']['nps'] 
            for d in difficulties.keys() 
            if results[d]['cpp']['nps'] > 0 and results[d]['python']['nps'] > 0
        ) / len([d for d in difficulties.keys() if results[d]['cpp']['nps'] > 0])
        
        print(f"\n✅ C++引擎平均加速: {avg_speedup:.2f}x")
        
        if avg_speedup >= 3.0:
            print(f"🎉 性能目标达成！C++引擎显著提升搜索速度")
        elif avg_speedup >= 2.0:
            print(f"👍 C++引擎有明显提升，但还有优化空间")
        else:
            print(f"⚠️  C++引擎提升有限，建议检查编译优化选项")
    else:
        print("\n⚠️  请编译C++引擎以进行完整对比测试")
        print("   编译命令见 cpp_engine/BUILD.md")
    
    print("=" * 70)


if __name__ == '__main__':
    main()
