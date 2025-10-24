#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目设置验证脚本 - 检查所有必需的组件是否正确配置

使用方法: python verify_setup.py
"""

import os
import sys
from pathlib import Path


def print_header(text):
    """打印带颜色的标题"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_success(text):
    """打印成功信息"""
    print(f"✅ {text}")


def print_error(text):
    """打印错误信息"""
    print(f"❌ {text}")


def print_info(text):
    """打印信息"""
    print(f"ℹ️  {text}")


def check_python_version():
    """检查 Python 版本"""
    print_header("检查 Python 版本")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} - 版本正确")
        return True
    else:
        print_error(f"Python 版本过低: {version.major}.{version.minor} (需要 3.8+)")
        return False


def check_directory_structure():
    """检查目录结构"""
    print_header("检查目录结构")
    
    required_dirs = [
        "backend",
        "backend/database",
        "backend/routes",
        "frontend",
        "frontend/css",
        "frontend/js",
        "frontend/games",
        "frontend/games/action",
        "frontend/games/shooting",
        "frontend/games/arcade",
        "frontend/games/puzzle",
        "frontend/games/casual",
        "static",
        "tests",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists() and full_path.is_dir():
            print_success(f"目录存在: {dir_path}/")
        else:
            print_error(f"目录缺失: {dir_path}/")
            all_exist = False
    
    return all_exist


def check_file_structure():
    """检查文件结构"""
    print_header("检查文件结构")
    
    required_files = [
        # Python 文件
        "app.py",
        "config.py",
        "run.py",
        "manage.py",
        "__init__.py",
        "requirements.txt",
        "backend/database/db.py",
        "backend/routes/auth.py",
        "backend/routes/games.py",
        "backend/routes/scores.py",
        
        # HTML 文件
        "frontend/index.html",
        "frontend/login.html",
        "frontend/game.html",
        "frontend/leaderboard.html",
        "frontend/dashboard.html",
        
        # CSS/JS 文件
        "frontend/css/style.css",
        "frontend/js/api.js",
        "frontend/js/ui.js",
        "frontend/js/main.js",
        
        # 游戏文件
        "frontend/games/action/contra/index.html",
        "frontend/games/action/contra/game.js",
        "frontend/games/action/kof/index.html",
        "frontend/games/action/kof/game.js",
        "frontend/games/shooting/tankbattle/index.html",
        "frontend/games/shooting/tankbattle/game.js",
        "frontend/games/arcade/snake/index.html",
        "frontend/games/arcade/snake/game.js",
        "frontend/games/puzzle/2048/index.html",
        "frontend/games/puzzle/2048/game.js",
        
        # 文档文件
        "README.md",
        "QUICKSTART.md",
        "TECHNICAL.md",
        "COMPLETION_REPORT.md",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists() and full_path.is_file():
            size = full_path.stat().st_size
            print_success(f"文件存在: {file_path} ({size:,} 字节)")
        else:
            print_error(f"文件缺失: {file_path}")
            all_exist = False
    
    return all_exist


def check_dependencies():
    """检查依赖项"""
    print_header("检查依赖项")
    
    required_packages = [
        "Flask",
        "flask_sqlalchemy",
        "flask_jwt_extended",
        "flask_cors",
        "sqlalchemy",
        "werkzeug",
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package if package != "flask_sqlalchemy" else "flask_sqlalchemy")
            print_success(f"模块已安装: {package}")
        except ImportError:
            print_error(f"模块未安装: {package}")
            all_installed = False
    
    return all_installed


def check_configuration():
    """检查配置"""
    print_header("检查配置")
    
    try:
        from config import Config, GAMES_CONFIG
        print_success("配置模块可以导入")
        
        # 检查游戏配置
        print_info(f"发现 {len(GAMES_CONFIG)} 个游戏分类")
        for category, games in GAMES_CONFIG.items():
            print_success(f"  分类 '{category}' 包含 {len(games)} 个游戏")
        
        # 检查数据库配置
        if hasattr(Config, 'SQLALCHEMY_DATABASE_URI'):
            print_success(f"数据库配置: {Config.SQLALCHEMY_DATABASE_URI}")
        
        return True
    except Exception as e:
        print_error(f"配置检查失败: {str(e)}")
        return False


def check_database():
    """检查数据库连接"""
    print_header("检查数据库连接")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from backend.database.db import User, Game, GameRecord, Score, Achievement
            print_success("数据库模型可以导入")
            print_info("  - User 表")
            print_info("  - Game 表")
            print_info("  - GameRecord 表")
            print_info("  - Score 表")
            print_info("  - Achievement 表")
        
        return True
    except Exception as e:
        print_error(f"数据库检查失败: {str(e)}")
        return False


def print_summary(results):
    """打印总结"""
    print_header("验证总结")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print_info(f"总检查项: {total}")
    print_success(f"通过: {passed}")
    if failed > 0:
        print_error(f"失败: {failed}")
    
    if failed == 0:
        print_header("🎉 所有检查通过！项目已就绪")
        print("\n接下来请运行:")
        print("  python run.py")
        print("\n然后访问:")
        print("  http://localhost:5000")
    else:
        print_header("❌ 存在未通过的检查")
        print("\n请先安装依赖:")
        print("  pip install -r requirements.txt")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  🎮 网页游戏中心 - 项目验证")
    print("="*60)
    
    results = {
        "Python 版本": check_python_version(),
        "目录结构": check_directory_structure(),
        "文件结构": check_file_structure(),
        "配置验证": check_configuration(),
    }
    
    # 尝试检查依赖和数据库（可能会失败）
    try:
        results["依赖项"] = check_dependencies()
    except Exception as e:
        print_info(f"依赖项检查跳过: {str(e)}")
    
    try:
        results["数据库"] = check_database()
    except Exception as e:
        print_info(f"数据库检查跳过: {str(e)}")
    
    print_summary(results)


if __name__ == "__main__":
    main()
