"""游戏主循环快速测试"""
import subprocess
import time

print("="*70)
print("游戏主循环测试")
print("="*70)

print("\n[测试] 运行游戏5秒...")
print("(按Ctrl+C提前退出)")

try:
    # 启动游戏
    proc = subprocess.Popen(
        ["python", "gamecenter/deltaOperation/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # 监控输出5秒
    start_time = time.time()
    while time.time() - start_time < 5:
        line = proc.stdout.readline()
        if line:
            print(line.rstrip())
        if proc.poll() is not None:
            break
        time.sleep(0.1)
    
    # 终止进程
    proc.terminate()
    proc.wait(timeout=2)
    
    print("\n✓ 游戏运行测试完成")
    
except KeyboardInterrupt:
    print("\n\n✓ 测试被中断")
    proc.terminate()
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
