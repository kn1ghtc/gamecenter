"""
资源管理器模块

所有资源已集成到assets目录，无需在线下载
音效来自OpenGameArt "512 Sound Effects (8-bit style)" by Juhani Junkala (CC0)
背景音乐来自FreePD "Bit Bit Loop" by Kevin MacLeod (CC0)
"""
import os
from typing import Optional, Dict
from .settings import FONTS_DIR, SOUNDS_DIR, IMAGES_DIR


class ResourceManager:
    """资源管理器类"""
    
    # 资源路径映射（所有资源已集成到assets目录）
    RESOURCE_PATHS = {
        # 字体资源 - 系统字体优先，无需下载
        'font_main': {
            'path': os.path.join(FONTS_DIR, 'PressStart2P.ttf'),
            'type': 'font'
        },
        # 音效资源 - 已集成到assets/sounds目录
        'sound_rotate': {
            'path': os.path.join(SOUNDS_DIR, 'rotate.wav'),
            'type': 'sound'
        },
        'sound_move': {
            'path': os.path.join(SOUNDS_DIR, 'move.wav'),
            'type': 'sound'
        },
        'sound_clear': {
            'path': os.path.join(SOUNDS_DIR, 'clear.wav'),
            'type': 'sound'
        },
        'sound_drop': {
            'path': os.path.join(SOUNDS_DIR, 'drop.wav'),
            'type': 'sound'
        },
        'sound_level_up': {
            'path': os.path.join(SOUNDS_DIR, 'level_up.wav'),
            'type': 'sound'
        },
        'sound_game_over': {
            'path': os.path.join(SOUNDS_DIR, 'game_over.wav'),
            'type': 'sound'
        },
        # 背景音乐 - 已集成
        'music_bg': {
            'path': os.path.join(SOUNDS_DIR, 'background.mp3'),
            'type': 'sound'
        },
    }
    
    def __init__(self, auto_download=False):
        """
        初始化资源管理器
        
        参数:
            auto_download: 兼容参数（已移除在线下载功能）
        """
        self.cached_resources: Dict[str, str] = {}
        self._ensure_directories()
        self._cache_existing_resources()
    
    def _ensure_directories(self):
        """确保所有资源目录存在"""
        for dir_path in [FONTS_DIR, SOUNDS_DIR, IMAGES_DIR]:
            os.makedirs(dir_path, exist_ok=True)
    
    def _cache_existing_resources(self):
        """缓存已存在的资源路径"""
        for key, info in self.RESOURCE_PATHS.items():
            path = info['path']
            if os.path.exists(path):
                self.cached_resources[key] = path
    
    def get_resource_path(self, key: str) -> Optional[str]:
        """
        获取资源路径
        
        参数:
            key: 资源键名
            
        返回:
            资源本地路径，如果不存在则返回None
        """
        if key in self.cached_resources:
            return self.cached_resources[key]
        
        # 检查资源是否存在
        if key in self.RESOURCE_PATHS:
            local_path = self.RESOURCE_PATHS[key]['path']
            if os.path.exists(local_path):
                self.cached_resources[key] = local_path
                return local_path
        
        return None
    
    def get_font_path(self, fallback: bool = True) -> Optional[str]:
        """
        获取字体路径
        
        参数:
            fallback: 如果资源字体不存在是否使用系统默认字体
            
        返回:
            字体路径或None（使用pygame默认字体）
        """
        font_path = self.get_resource_path('font_main')
        
        if font_path and os.path.exists(font_path):
            return font_path
        
        if fallback:
            # 尝试使用Windows系统字体
            system_fonts = [
                'C:\\Windows\\Fonts\\msyh.ttc',  # 微软雅黑
                'C:\\Windows\\Fonts\\simhei.ttf',  # 黑体
                'C:\\Windows\\Fonts\\arial.ttf',  # Arial
            ]
            for font in system_fonts:
                if os.path.exists(font):
                    return font
        
        return None  # 使用pygame默认字体
    
    def check_all_resources(self) -> Dict[str, bool]:
        """
        检查所有资源是否存在
        
        返回:
            资源状态字典 {key: exists}
        """
        status = {}
        for key, info in self.RESOURCE_PATHS.items():
            status[key] = os.path.exists(info['path'])
        return status
    
    def get_missing_resources(self) -> list:
        """
        获取缺失的资源列表
        
        返回:
            缺失资源的键名列表
        """
        status = self.check_all_resources()
        return [key for key, exists in status.items() if not exists]


# 全局资源管理器实例
_resource_manager = None


def get_resource_manager(auto_download=False) -> ResourceManager:
    """
    获取全局资源管理器实例
    
    参数:
        auto_download: 兼容参数（已移除在线下载功能）
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager(auto_download=auto_download)
    return _resource_manager


if __name__ == '__main__':
    # 测试资源管理器
    print("检查资源状态...")
    rm = ResourceManager()
    
    # 显示资源状态
    print("\n资源状态:")
    status = rm.check_all_resources()
    for key, exists in status.items():
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {key}")
    
    # 检查缺失资源
    missing = rm.get_missing_resources()
    if missing:
        print(f"\n⚠ 缺失资源: {missing}")
        print("游戏将在静音模式下运行")
    else:
        print("\n✓ 所有资源已就绪!")
