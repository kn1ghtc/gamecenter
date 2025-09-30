"""
高性能启动和热加载系统
High-Performance Startup and Hot Reload System

实现按需加载、控制加载时间、支持配置热重载，避免程序卡死
Implements lazy loading, controlled load times, configuration hot reloading, prevents freezing
"""

import json
import os
import time
import threading
import weakref
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from queue import Queue, Empty
from dataclasses import dataclass
from direct.showbase.ShowBase import ShowBase
from direct.task import Task


@dataclass
class LoadingTask:
    """加载任务定义"""
    name: str
    priority: int  # 数字越小优先级越高
    load_func: Callable
    dependencies: List[str]  # 依赖的其他任务名称
    loaded: bool = False
    loading: bool = False
    error: Optional[str] = None
    load_time: float = 0.0


class LazyLoadManager:
    """按需加载管理器"""
    
    def __init__(self, base_app: ShowBase):
        self.base_app = weakref.ref(base_app)
        self.tasks = {}
        self.load_queue = Queue()
        self.loading_thread = None
        self.is_loading = False
        self.load_progress = 0.0
        self.total_tasks = 0
        self.completed_tasks = 0
        self.loading_callbacks = []
        self.max_concurrent_loads = 3
        self.current_loads = 0
        
        print("✅ 按需加载管理器初始化完成")
    
    def register_task(self, name: str, load_func: Callable, priority: int = 5, 
                     dependencies: List[str] = None):
        """注册加载任务"""
        dependencies = dependencies or []
        task = LoadingTask(name, priority, load_func, dependencies)
        self.tasks[name] = task
        self.total_tasks += 1
        print(f"📋 注册加载任务: {name} (优先级: {priority})")
    
    def load_task(self, name: str, force: bool = False) -> bool:
        """加载指定任务"""
        if name not in self.tasks:
            print(f"⚠️  任务不存在: {name}")
            return False
        
        task = self.tasks[name]
        
        if task.loaded and not force:
            print(f"✅ 任务已加载: {name}")
            return True
        
        if task.loading:
            print(f"⏳ 任务正在加载: {name}")
            return False
        
        # 检查依赖
        for dep in task.dependencies:
            if not self._is_dependency_loaded(dep):
                print(f"⚠️  依赖未满足: {name} 需要 {dep}")
                # 自动加载依赖
                if not self.load_task(dep):
                    return False
        
        # 执行加载
        return self._execute_load(task)
    
    def _is_dependency_loaded(self, dep_name: str) -> bool:
        """检查依赖是否已加载"""
        if dep_name not in self.tasks:
            return True  # 不存在的依赖视为已满足
        return self.tasks[dep_name].loaded
    
    def _execute_load(self, task: LoadingTask) -> bool:
        """执行加载任务"""
        try:
            task.loading = True
            start_time = time.time()
            
            print(f"🔄 开始加载: {task.name}")
            
            # 执行加载函数
            result = task.load_func()
            
            task.load_time = time.time() - start_time
            task.loaded = True
            task.loading = False
            self.completed_tasks += 1
            
            print(f"✅ 加载完成: {task.name} ({task.load_time:.2f}s)")
            
            # 更新进度
            self.load_progress = self.completed_tasks / self.total_tasks
            
            # 触发加载回调
            for callback in self.loading_callbacks:
                try:
                    callback(task.name, self.load_progress)
                except Exception as e:
                    print(f"⚠️  加载回调失败: {e}")
            
            return True
            
        except Exception as e:
            task.error = str(e)
            task.loading = False
            print(f"❌ 加载失败: {task.name} - {e}")
            return False
    
    def load_by_priority(self, max_tasks: int = None):
        """按优先级批量加载"""
        if max_tasks is None:
            max_tasks = self.total_tasks
        
        # 按优先级排序未加载的任务
        pending_tasks = [
            task for task in self.tasks.values() 
            if not task.loaded and not task.loading
        ]
        pending_tasks.sort(key=lambda t: t.priority)
        
        loaded_count = 0
        for task in pending_tasks:
            if loaded_count >= max_tasks:
                break
            
            if self.load_task(task.name):
                loaded_count += 1
            
            # 防止阻塞主线程
            if loaded_count % 3 == 0:
                time.sleep(0.01)
        
        print(f"📦 批量加载完成: {loaded_count}/{len(pending_tasks)} 个任务")
    
    def register_progress_callback(self, callback: Callable[[str, float], None]):
        """注册加载进度回调"""
        self.loading_callbacks.append(callback)
    
    def get_loading_status(self) -> Dict[str, Any]:
        """获取加载状态"""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'progress': self.load_progress,
            'is_loading': self.is_loading,
            'failed_tasks': [
                name for name, task in self.tasks.items() 
                if task.error is not None
            ]
        }


class HotReloadManager:
    """热重载管理器"""
    
    def __init__(self, base_app: ShowBase):
        self.base_app = weakref.ref(base_app)
        self.watched_files = {}  # filepath -> (callback, last_mtime)
        self.reload_callbacks = {}  # config_name -> callback
        self.config_cache = {}
        self.check_interval = 1.0  # 检查间隔（秒）
        self.monitoring = False
        self.monitor_task = None
        
        print("✅ 热重载管理器初始化完成")
    
    def watch_config_file(self, config_name: str, filepath: str, 
                         reload_callback: Callable[[Dict], None]):
        """监视配置文件变化"""
        if not os.path.exists(filepath):
            print(f"⚠️  配置文件不存在: {filepath}")
            return
        
        # 初始加载
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            self.config_cache[config_name] = config_data
            
            # 注册监视
            mtime = os.path.getmtime(filepath)
            self.watched_files[filepath] = (reload_callback, mtime, config_name)
            self.reload_callbacks[config_name] = reload_callback
            
            print(f"👁️  开始监视配置: {config_name} -> {filepath}")
            
            # 启动监控任务
            if not self.monitoring:
                self.start_monitoring()
                
        except Exception as e:
            print(f"❌ 配置文件监视失败: {e}")
    
    def start_monitoring(self):
        """启动文件监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        base_app = self.base_app()
        if base_app:
            self.monitor_task = base_app.taskMgr.add(
                self._check_file_changes, 'hot-reload-monitor'
            )
            print("🔍 启动热重载监控")
    
    def stop_monitoring(self):
        """停止文件监控"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_task:
            base_app = self.base_app()
            if base_app:
                base_app.taskMgr.remove(self.monitor_task)
        print("🛑 停止热重载监控")
    
    def _check_file_changes(self, task):
        """检查文件变化"""
        try:
            for filepath, (callback, last_mtime, config_name) in list(self.watched_files.items()):
                if not os.path.exists(filepath):
                    continue
                
                current_mtime = os.path.getmtime(filepath)
                if current_mtime > last_mtime:
                    print(f"🔥 检测到文件变化: {config_name}")
                    self._reload_config(filepath, callback, config_name)
                    # 更新时间戳
                    self.watched_files[filepath] = (callback, current_mtime, config_name)
            
            # 继续下次检查
            return task.again
            
        except Exception as e:
            print(f"❌ 文件变化检查失败: {e}")
            return task.again
    
    def _reload_config(self, filepath: str, callback: Callable, config_name: str):
        """重新加载配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                new_config = json.load(f)
            
            # 更新缓存
            old_config = self.config_cache.get(config_name, {})
            self.config_cache[config_name] = new_config
            
            # 执行回调
            callback(new_config, old_config)
            print(f"✅ 配置热重载成功: {config_name}")
            
        except Exception as e:
            print(f"❌ 配置重载失败: {config_name} - {e}")
    
    def get_config(self, config_name: str) -> Optional[Dict]:
        """获取缓存的配置"""
        return self.config_cache.get(config_name)
    
    def force_reload(self, config_name: str):
        """强制重新加载配置"""
        for filepath, (callback, _, name) in self.watched_files.items():
            if name == config_name:
                self._reload_config(filepath, callback, config_name)
                break


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, base_app: ShowBase):
        self.base_app = weakref.ref(base_app)
        self.optimization_enabled = True
        self.frame_time_history = []
        self.max_history = 60  # 保留60帧的历史
        self.target_fps = 60
        self.auto_adjust = True
        
        print("✅ 性能优化器初始化完成")
    
    def optimize_startup(self):
        """启动时性能优化"""
        try:
            base_app = self.base_app()
            if not base_app:
                return
            
            # 禁用不必要的渲染特性
            if hasattr(base_app, 'render'):
                # 优化背面裁剪
                from panda3d.core import CullFaceAttrib
                base_app.render.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))
            
            # 优化音频设置
            if hasattr(base_app, 'sfxManagerList'):
                for mgr in base_app.sfxManagerList:
                    if hasattr(mgr, 'setConcurrentSoundLimit'):
                        mgr.setConcurrentSoundLimit(8)  # 限制同时播放音效数量
            
            # 设置合理的帧率限制
            base_app.globalClock.setMode(base_app.globalClock.MLimited)
            base_app.globalClock.setFrameRate(self.target_fps)
            
            print("⚡ 启动性能优化完成")
            
        except Exception as e:
            print(f"❌ 启动性能优化失败: {e}")
    
    def monitor_performance(self, task):
        """监控性能指标"""
        try:
            base_app = self.base_app()
            if not base_app:
                return task.done
            
            # 记录帧时间
            dt = base_app.globalClock.getDt()
            self.frame_time_history.append(dt)
            
            # 限制历史记录长度
            if len(self.frame_time_history) > self.max_history:
                self.frame_time_history.pop(0)
            
            # 计算平均FPS
            if len(self.frame_time_history) >= 10:
                avg_frame_time = sum(self.frame_time_history[-10:]) / 10
                current_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
                
                # 自动调整性能设置
                if self.auto_adjust and current_fps < self.target_fps * 0.8:
                    self._apply_performance_reduction()
                elif self.auto_adjust and current_fps > self.target_fps * 1.1:
                    self._apply_performance_increase()
            
            return task.again
            
        except Exception as e:
            print(f"❌ 性能监控失败: {e}")
            return task.again
    
    def _apply_performance_reduction(self):
        """降低性能设置"""
        # 这里可以添加自动降低质量的逻辑
        pass
    
    def _apply_performance_increase(self):
        """提高性能设置"""
        # 这里可以添加自动提高质量的逻辑
        pass
    
    def start_monitoring(self):
        """开始性能监控"""
        base_app = self.base_app()
        if base_app:
            base_app.taskMgr.add(self.monitor_performance, 'performance-monitor')
            print("📊 启动性能监控")


class SmartLoadingSystem:
    """智能加载系统 - 集成所有优化功能"""
    
    def __init__(self, base_app: ShowBase):
        self.base_app = weakref.ref(base_app)
        self.lazy_loader = LazyLoadManager(base_app)
        self.hot_reload = HotReloadManager(base_app)
        self.optimizer = PerformanceOptimizer(base_app)
        
        # 配置默认加载任务
        self._setup_default_tasks()
        
        print("🚀 智能加载系统初始化完成")
    
    def _setup_default_tasks(self):
        """设置默认加载任务"""
        # 核心系统 - 最高优先级
        self.lazy_loader.register_task(
            "audio_system", self._load_audio_system, priority=1
        )
        
        # 图形系统
        self.lazy_loader.register_task(
            "graphics_shaders", self._load_graphics_shaders, priority=2
        )
        
        # 角色模型 - 中等优先级
        self.lazy_loader.register_task(
            "character_models", self._load_character_models, 
            priority=3, dependencies=["graphics_shaders"]
        )
        
        # UI系统
        self.lazy_loader.register_task(
            "ui_system", self._load_ui_system, priority=4
        )
        
        # 特效系统 - 较低优先级
        self.lazy_loader.register_task(
            "vfx_system", self._load_vfx_system, 
            priority=5, dependencies=["graphics_shaders"]
        )
    
    def _load_audio_system(self):
        """加载音频系统"""
        try:
            base_app = self.base_app()
            if base_app and hasattr(base_app, 'audio'):
                # 音频系统可能已经初始化
                return True
            return True
        except Exception as e:
            print(f"音频系统加载失败: {e}")
            return False
    
    def _load_graphics_shaders(self):
        """加载图形着色器"""
        try:
            # 这里可以加载自定义着色器
            return True
        except Exception as e:
            print(f"图形着色器加载失败: {e}")
            return False
    
    def _load_character_models(self):
        """加载角色模型"""
        try:
            # 这里可以预加载角色模型
            return True
        except Exception as e:
            print(f"角色模型加载失败: {e}")
            return False
    
    def _load_ui_system(self):
        """加载UI系统"""
        try:
            # 这里可以加载UI资源
            return True
        except Exception as e:
            print(f"UI系统加载失败: {e}")
            return False
    
    def _load_vfx_system(self):
        """加载特效系统"""
        try:
            # 这里可以加载特效资源
            return True
        except Exception as e:
            print(f"特效系统加载失败: {e}")
            return False
    
    def start_optimized_loading(self):
        """启动优化加载流程"""
        print("🚀 开始优化加载流程...")
        
        # 1. 启动性能优化
        self.optimizer.optimize_startup()
        
        # 2. 按优先级加载核心系统
        self.lazy_loader.load_by_priority(max_tasks=3)
        
        # 3. 启动性能监控
        self.optimizer.start_monitoring()
        
        # 4. 启动热重载监控
        self.hot_reload.start_monitoring()
        
        print("✅ 优化加载流程完成")
    
    def setup_config_watching(self, config_dir: str):
        """设置配置文件监视"""
        config_path = Path(config_dir)
        if not config_path.exists():
            print(f"⚠️  配置目录不存在: {config_dir}")
            return
        
        # 监视主要配置文件
        main_config = config_path / "game_config.json"
        if main_config.exists():
            self.hot_reload.watch_config_file(
                "main_config", str(main_config), self._on_main_config_reload
            )
        
        # 监视角色配置
        char_config = config_path / "characters" / "manifest.json"
        if char_config.exists():
            self.hot_reload.watch_config_file(
                "characters", str(char_config), self._on_character_config_reload
            )
    
    def _on_main_config_reload(self, new_config: Dict, old_config: Dict):
        """主配置重载回调"""
        print("🔄 重新加载主配置")
        # 这里可以应用新的配置设置
    
    def _on_character_config_reload(self, new_config: Dict, old_config: Dict):
        """角色配置重载回调"""
        print("🔄 重新加载角色配置")
        # 这里可以重新加载角色数据
    
    def cleanup(self):
        """清理资源"""
        self.hot_reload.stop_monitoring()
        print("✅ 智能加载系统清理完成")