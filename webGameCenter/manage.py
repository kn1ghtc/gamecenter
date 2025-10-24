# -*- coding: utf-8 -*-
"""
网页游戏中心 - 辅助工具脚本
"""

import os
import sys
from app import create_app, db
from backend.database.db import User, Game, GameRecord, Score, Achievement

def init_db():
    """初始化数据库"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ 数据库初始化成功")

def reset_db():
    """重置数据库"""
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ 数据库重置成功")

def create_admin_user(username, email, password):
    """创建管理员账户"""
    app = create_app()
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"✗ 用户 {username} 已存在")
            return
        
        from werkzeug.security import generate_password_hash
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            total_score=0
        )
        db.session.add(user)
        db.session.commit()
        print(f"✓ 管理员账户创建成功: {username}")

def list_users():
    """列出所有用户"""
    app = create_app()
    with app.app_context():
        users = User.query.all()
        if not users:
            print("没有用户记录")
            return
        
        print("\n用户列表:")
        print(f"{'ID':<5} {'用户名':<15} {'邮箱':<25} {'积分':<10}")
        print("-" * 55)
        for user in users:
            print(f"{user.id:<5} {user.username:<15} {user.email:<25} {user.total_score:<10}")

def clear_records():
    """清除所有游戏记录"""
    app = create_app()
    with app.app_context():
        GameRecord.query.delete()
        db.session.commit()
        print("✓ 游戏记录已清除")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  python manage.py init_db          - 初始化数据库")
        print("  python manage.py reset_db         - 重置数据库")
        print("  python manage.py create_admin <username> <email> <password>")
        print("  python manage.py list_users       - 列出所有用户")
        print("  python manage.py clear_records    - 清除游戏记录")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init_db':
        init_db()
    elif command == 'reset_db':
        reset_db()
    elif command == 'create_admin' and len(sys.argv) >= 5:
        create_admin_user(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == 'list_users':
        list_users()
    elif command == 'clear_records':
        clear_records()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
