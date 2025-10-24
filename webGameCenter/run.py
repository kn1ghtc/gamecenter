#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网页游戏中心启动脚本

使用方法:
    python run.py                  # 开发环境 (http://localhost:5000)
    python run.py production       # 生产环境 (http://0.0.0.0:5000)
"""

import os
import sys
import warnings
from app import create_app

# 抑制某些警告信息
warnings.filterwarnings('ignore')

def main():
    """主启动函数"""
    env = sys.argv[1] if len(sys.argv) > 1 else 'development'
    
    # 设置环境变量
    os.environ['FLASK_ENV'] = env
    
    # 创建应用
    app = create_app(env)
    
    print("\n" + "="*70)
    print("  🎮 网页游戏中心")
    print("  Web Game Center")
    print("="*70 + "\n")
    
    if env == 'production':
        print(f"  ✅ 生产模式启动")
        print(f"  📍 访问地址: http://0.0.0.0:5000")
        print(f"  🔗 本机访问: http://localhost:5000")
        print(f"  ⚠️  生产环境请使用 Gunicorn + Nginx\n")
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
    else:
        print(f"  ✅ 开发模式启动")
        print(f"  🔗 访问地址: http://localhost:5000")
        print(f"  📝 日志模式: 详细")
        print(f"  🔄 自动重载: 启用\n")
        print("  💡 快速导航:")
        print("     • 首页: http://localhost:5000")
        print("     • 登录: http://localhost:5000/login.html")
        print("     • 游戏: http://localhost:5000/game.html")
        print("     • 排行: http://localhost:5000/leaderboard.html")
        print("     • API: http://localhost:5000/api/health")
        print("\n" + "="*70 + "\n")
        app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    main()
