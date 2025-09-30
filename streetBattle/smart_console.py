"""
智能控制台输出管理器
Smart Console Output Manager

优化和管理控制台输出，支持日志等级、频率控制、格式化输出
Optimizes and manages console output with log levels, frequency control, formatted output
"""

import time
import threading
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime


class LogLevel(Enum):
    """日志等级"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class LogMessage:
    """日志消息"""
    timestamp: float
    level: LogLevel
    category: str
    message: str
    count: int = 1


class SmartConsoleManager:
    """智能控制台管理器"""
    
    def __init__(self, min_level: LogLevel = LogLevel.INFO):
        self.min_level = min_level
        self.message_history = deque(maxlen=1000)
        self.category_counters = defaultdict(int)
        self.frequency_limits = {}  # category -> (max_per_second, last_reset_time, current_count)
        self.duplicate_suppression = {}  # message_hash -> (count, last_time)
        self.output_formatters = {}
        self.output_enabled = True
        self.lock = threading.Lock()
        
        # 默认频率限制
        self._setup_default_frequency_limits()
        
        # 默认格式器
        self._setup_default_formatters()
        
        print("✅ 智能控制台管理器初始化完成")
    
    def _setup_default_frequency_limits(self):
        """设置默认频率限制"""
        # 位置更新信息：每秒最多2条
        self.set_frequency_limit("position", max_per_second=2)
        
        # 调试信息：每秒最多5条
        self.set_frequency_limit("debug", max_per_second=5)
        
        # 动画信息：每秒最多3条
        self.set_frequency_limit("animation", max_per_second=3)
        
        # 音频信息：每秒最多1条
        self.set_frequency_limit("audio", max_per_second=1)
        
        # 网络信息：每秒最多10条
        self.set_frequency_limit("network", max_per_second=10)
        
        # 错误信息：不限制
        self.set_frequency_limit("error", max_per_second=100)
    
    def _setup_default_formatters(self):
        """设置默认输出格式器"""
        self.output_formatters = {
            LogLevel.DEBUG: lambda msg: f"🔍 [DEBUG] {msg}",
            LogLevel.INFO: lambda msg: f"ℹ️  [INFO] {msg}",
            LogLevel.WARNING: lambda msg: f"⚠️  [WARN] {msg}",
            LogLevel.ERROR: lambda msg: f"❌ [ERROR] {msg}",
            LogLevel.CRITICAL: lambda msg: f"🚨 [CRITICAL] {msg}"
        }
    
    def set_frequency_limit(self, category: str, max_per_second: int):
        """设置分类的频率限制"""
        self.frequency_limits[category] = [max_per_second, time.time(), 0]
    
    def set_min_level(self, level: LogLevel):
        """设置最小日志等级"""
        self.min_level = level
        print(f"📊 设置最小日志等级: {level.name}")
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO, 
            category: str = "general", suppress_duplicates: bool = True):
        """记录日志消息"""
        with self.lock:
            # 检查日志等级
            if level.value < self.min_level.value:
                return
            
            # 检查频率限制
            if not self._check_frequency_limit(category):
                return
            
            # 检查重复抑制
            if suppress_duplicates:
                message_hash = hash(f"{category}:{message}")
                if message_hash in self.duplicate_suppression:
                    count, last_time = self.duplicate_suppression[message_hash]
                    if time.time() - last_time < 1.0:  # 1秒内的重复消息
                        self.duplicate_suppression[message_hash] = (count + 1, time.time())
                        return
                self.duplicate_suppression[message_hash] = (1, time.time())
            
            # 创建日志消息
            log_msg = LogMessage(time.time(), level, category, message)
            self.message_history.append(log_msg)
            self.category_counters[category] += 1
            
            # 输出消息
            if self.output_enabled:
                self._output_message(log_msg)
    
    def _check_frequency_limit(self, category: str) -> bool:
        """检查频率限制"""
        if category not in self.frequency_limits:
            return True
        
        max_per_second, last_reset_time, current_count = self.frequency_limits[category]
        current_time = time.time()
        
        # 重置计数器（每秒）
        if current_time - last_reset_time >= 1.0:
            self.frequency_limits[category] = [max_per_second, current_time, 0]
            current_count = 0
        
        # 检查是否超过限制
        if current_count >= max_per_second:
            return False
        
        # 增加计数
        self.frequency_limits[category][2] += 1
        return True
    
    def _output_message(self, log_msg: LogMessage):
        """输出消息到控制台"""
        formatter = self.output_formatters.get(log_msg.level)
        if formatter:
            formatted_msg = formatter(log_msg.message)
        else:
            formatted_msg = log_msg.message
        
        # 添加分类信息（如果不是一般分类）
        if log_msg.category != "general":
            formatted_msg = f"[{log_msg.category.upper()}] {formatted_msg}"
        
        print(formatted_msg)
    
    def debug(self, message: str, category: str = "debug"):
        """调试消息"""
        self.log(message, LogLevel.DEBUG, category)
    
    def info(self, message: str, category: str = "general"):
        """信息消息"""
        self.log(message, LogLevel.INFO, category)
    
    def warning(self, message: str, category: str = "general"):
        """警告消息"""
        self.log(message, LogLevel.WARNING, category)
    
    def error(self, message: str, category: str = "error"):
        """错误消息"""
        self.log(message, LogLevel.ERROR, category)
    
    def critical(self, message: str, category: str = "error"):
        """严重错误消息"""
        self.log(message, LogLevel.CRITICAL, category)
    
    def position_update(self, player_name: str, position):
        """位置更新消息（特殊处理）"""
        if hasattr(position, 'x'):
            msg = f"{player_name} 位置: ({position.x:.1f}, {position.y:.1f}, {position.z:.1f})"
        else:
            msg = f"{player_name} 位置: {position}"
        self.log(msg, LogLevel.DEBUG, "position")
    
    def animation_state(self, character: str, state: str):
        """动画状态消息"""
        self.log(f"{character} 动画状态: {state}", LogLevel.DEBUG, "animation")
    
    def audio_event(self, event: str, details: str = ""):
        """音频事件消息"""
        msg = f"音频事件: {event}"
        if details:
            msg += f" - {details}"
        self.log(msg, LogLevel.INFO, "audio")
    
    def network_event(self, event: str, details: str = ""):
        """网络事件消息"""
        msg = f"网络: {event}"
        if details:
            msg += f" - {details}"
        self.log(msg, LogLevel.INFO, "network")
    
    def combat_event(self, event: str, details: str = ""):
        """战斗事件消息"""
        msg = f"战斗: {event}"
        if details:
            msg += f" - {details}"
        self.log(msg, LogLevel.INFO, "combat")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            total_messages = sum(self.category_counters.values())
            return {
                "total_messages": total_messages,
                "category_counts": dict(self.category_counters),
                "duplicate_suppressions": len(self.duplicate_suppression),
                "frequency_limits": {
                    cat: {"max_per_second": limit[0], "current_count": limit[2]}
                    for cat, limit in self.frequency_limits.items()
                }
            }
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        print(f"\n📊 控制台输出统计:")
        print(f"   总消息数: {stats['total_messages']}")
        print(f"   抑制重复: {stats['duplicate_suppressions']}")
        print(f"   分类统计:")
        for category, count in stats['category_counts'].items():
            print(f"     {category}: {count}")
    
    def set_quiet_mode(self, quiet: bool = True):
        """设置安静模式"""
        if quiet:
            self.set_min_level(LogLevel.WARNING)
            print("🤫 启用安静模式 - 只显示警告和错误")
        else:
            self.set_min_level(LogLevel.INFO)
            print("🔊 禁用安静模式 - 显示所有信息")
    
    def enable_debug_mode(self, enable: bool = True):
        """启用/禁用调试模式"""
        if enable:
            self.set_min_level(LogLevel.DEBUG)
            print("🔍 启用调试模式 - 显示所有日志")
        else:
            self.set_min_level(LogLevel.INFO)
            print("📋 禁用调试模式 - 隐藏调试信息")
    
    def clear_history(self):
        """清除历史记录"""
        with self.lock:
            self.message_history.clear()
            self.category_counters.clear()
            self.duplicate_suppression.clear()
            print("🗑️  清除控制台历史记录")
    
    def disable_output(self):
        """禁用输出"""
        self.output_enabled = False
        print("🔇 禁用控制台输出")
    
    def enable_output(self):
        """启用输出"""
        self.output_enabled = True
        print("🔊 启用控制台输出")


# 全局控制台管理器实例
_console_manager = None


def get_console_manager() -> SmartConsoleManager:
    """获取全局控制台管理器"""
    global _console_manager
    if _console_manager is None:
        _console_manager = SmartConsoleManager()
    return _console_manager


def setup_optimized_console(min_level: LogLevel = LogLevel.INFO, quiet_mode: bool = False):
    """设置优化的控制台输出"""
    global _console_manager
    _console_manager = SmartConsoleManager(min_level)
    
    if quiet_mode:
        _console_manager.set_quiet_mode(True)
    
    print("✅ 优化控制台输出系统已设置")
    return _console_manager


# 便捷函数
def console_debug(message: str, category: str = "debug"):
    """调试日志"""
    get_console_manager().debug(message, category)


def console_info(message: str, category: str = "general"):
    """信息日志"""
    get_console_manager().info(message, category)


def console_warning(message: str, category: str = "general"):
    """警告日志"""
    get_console_manager().warning(message, category)


def console_error(message: str, category: str = "error"):
    """错误日志"""
    get_console_manager().error(message, category)


def console_position(player_name: str, position):
    """位置更新日志"""
    get_console_manager().position_update(player_name, position)


def console_animation(character: str, state: str):
    """动画状态日志"""
    get_console_manager().animation_state(character, state)


def console_audio(event: str, details: str = ""):
    """音频事件日志"""
    get_console_manager().audio_event(event, details)


def console_combat(event: str, details: str = ""):
    """战斗事件日志"""
    get_console_manager().combat_event(event, details)