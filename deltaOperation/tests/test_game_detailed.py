"""游戏主循环详细测试"""
import os
import sys

# 强制UTF-8编码
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import subprocess
import time

print("="*70)
print("游戏主循环详细测试")
print("="*70)

try:
    # 启动游戏进程
    proc = subprocess.Popen(
        [sys.executable, "gamecenter/deltaOperation/main.py", "--headless"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
        cwd=os.path.abspath(".")
    )
    
    print("\n[测试] 游戏启动中...")
    print("[提示] 将运行10秒后自动终止\n")
    
    # 监控输出
    start_time = time.time()
    line_count = 0
    max_lines = 200
    
    while time.time() - start_time < 10:
        line = proc.stdout.readline()
        if line and line_count < max_lines:
            print(line.rstrip())
            line_count += 1
        
        # 检查进程是否结束
        if proc.poll() is not None:
            print(f"\n[!] 进程提前退出,返回码: {proc.returncode}")
            break
        
        time.sleep(0.1)
    
    # 终止进程
    if proc.poll() is None:
        print("\n\n[测试] 10秒到,终止进程...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()
            proc.wait()
    
    print(f"\n{'='*70}")
    print(f"测试完成! 共{line_count}行输出")
    print(f"{'='*70}")
    
except KeyboardInterrupt:
    print("\n\n[!] 测试被中断")
    if proc:
        proc.terminate()
except Exception as e:
    print(f"\n[✗] 测试失败: {e}")
    import traceback
    traceback.print_exc()
