#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NodePath错误处理器 - 全局处理Panda3D NodePath相关错误
NodePath Error Handler - Global handler for Panda3D NodePath related errors
"""

import sys
import traceback
from typing import Optional, Any
from panda3d.core import NodePath


class NodePathErrorHandler:
    """NodePath安全操作处理器"""
    
    @staticmethod
    def safe_is_empty(node_path: Optional[NodePath], context: str = "unknown") -> bool:
        """安全地检查NodePath是否为空"""
        if not node_path:
            return True
        
        try:
            return node_path.isEmpty()
        except Exception as e:
            print(f"[NodePath Warning] isEmpty() check failed in {context}: {e}")
            # 尝试备用检查方法
            try:
                return not node_path.getNode()
            except Exception:
                return True
    
    @staticmethod
    def safe_remove_node(node_path: Optional[NodePath], context: str = "unknown") -> bool:
        """安全地移除NodePath节点"""
        if not node_path:
            return True
        
        if NodePathErrorHandler.safe_is_empty(node_path, f"{context}_remove_check"):
            return True
        
        try:
            node_path.removeNode()
            return True
        except Exception as e:
            print(f"[NodePath Warning] removeNode() failed in {context}: {e}")
            return False
    
    @staticmethod
    def safe_get_node(node_path: Optional[NodePath], context: str = "unknown") -> Optional[Any]:
        """安全地获取NodePath的节点"""
        if not node_path:
            return None
        
        try:
            return node_path.getNode()
        except Exception as e:
            print(f"[NodePath Warning] getNode() failed in {context}: {e}")
            return None
    
    @staticmethod
    def install_global_handler():
        """安装全局NodePath错误处理器"""
        original_excepthook = sys.excepthook
        
        def enhanced_excepthook(exc_type, exc_value, exc_traceback):
            if "Assertion failed" in str(exc_value) and "is_empty()" in str(exc_value):
                print("=" * 60)
                print("🔧 检测到NodePath isEmpty()断言错误!")
                print("这通常是由于尝试在空NodePath上调用操作导致的。")
                print("建议使用NodePathErrorHandler中的安全方法。")
                print("=" * 60)
                traceback.print_exception(exc_type, exc_value, exc_traceback)
                print("=" * 60)
            else:
                original_excepthook(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = enhanced_excepthook
        print("✅ NodePath全局错误处理器已安装")


# 自动安装处理器
NodePathErrorHandler.install_global_handler()
