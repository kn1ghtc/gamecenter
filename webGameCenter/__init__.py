# -*- coding: utf-8 -*-
"""
webGameCenter 包初始化文件
"""

__version__ = '1.0.0'
__author__ = 'Honor Security Team'

from app import create_app

def get_app():
    """获取 Flask 应用实例"""
    return create_app()
