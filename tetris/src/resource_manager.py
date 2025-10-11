"""
资源管理器模块

负责从互联网下载字体、音效、背景图片等资源，
实现自动下载和本地缓存机制
"""
import os
import sys
import urllib.request
import shutil
from typing import Optional, Dict
from .settings import FONTS_DIR, SOUNDS_DIR, IMAGES_DIR

class ResourceManager:
    """资源管理器类"""
    
    # CC0授权的免费资源URL
    RESOURCE_URLS = {
        # 字体资源
        'font_main': {
            'url': 'https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf',
            'path': os.path.join(FONTS_DIR, 'PressStart2P.ttf'),
            'type': 'font'
        },
        # 音效资源（使用freesound.org的CC0资源）
        'sound_rotate': {
            'url': 'https://freesound.org/data/previews/341/341695_5121236-lq.mp3',
            'path': os.path.join(SOUNDS_DIR, 'rotate.mp3'),
            'type': 'sound'
        },
        'sound_move': {
            'url': 'https://freesound.org/data/previews/341/341695_5121236-lq.mp3',
            'path': os.path.join(SOUNDS_DIR, 'move.mp3'),
            'type': 'sound'
        },
        'sound_clear': {
            'url': 'https://freesound.org/data/previews/270/270319_5123851-lq.mp3',
            'path': os.path.join(SOUNDS_DIR, 'clear.mp3'),
            'type': 'sound'
        },
        'sound_drop': {
            'url': 'https://freesound.org/data/previews/341/341695_5121236-lq.mp3',
            'path': os.path.join(SOUNDS_DIR, 'drop.mp3'),
            'type': 'sound'
        },
        'sound_level_up': {
            'url': 'https://freesound.org/data/previews/270/270404_5123851-lq.mp3',
            'path': os.path.join(SOUNDS_DIR, 'level_up.mp3'),
            'type': 'sound'
        },
        'sound_game_over': {
            'url': 'https://freesound.org/data/previews/277/277403_5123851-lq.mp3',
            'path': os.path.join(SOUNDS_DIR, 'game_over.mp3'),
            'type': 'sound'
        },
        # 背景音乐
        'music_bg': {
            'url': 'https://freesound.org/data/previews/198/198876_1648170-lq.mp3',
            'path': os.path.join(SOUNDS_DIR, 'background.mp3'),
            'type': 'sound'
        },
    }
    
    def __init__(self):
        """初始化资源管理器"""
        self.cached_resources: Dict[str, str] = {}
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有资源目录存在"""
        for dir_path in [FONTS_DIR, SOUNDS_DIR, IMAGES_DIR]:
            os.makedirs(dir_path, exist_ok=True)
    
    def download_resource(self, key: str, force: bool = False) -> Optional[str]:
        """
        下载指定资源
        
        参数:
            key: 资源键名
            force: 是否强制重新下载
            
        返回:
            资源本地路径，失败返回None
        """
        if key not in self.RESOURCE_URLS:
            print(f"警告: 未知的资源键 '{key}'")
            return None
        
        resource_info = self.RESOURCE_URLS[key]
        local_path = resource_info['path']
        
        # 如果文件已存在且不强制下载，直接返回路径
        if os.path.exists(local_path) and not force:
            self.cached_resources[key] = local_path
            return local_path
        
        # 下载资源
        try:
            print(f"正在下载资源: {key}...")
            
            # 设置User-Agent避免403错误
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            request = urllib.request.Request(resource_info['url'], headers=headers)
            
            with urllib.request.urlopen(request, timeout=30) as response:
                with open(local_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
            
            print(f"✓ 资源下载成功: {key}")
            self.cached_resources[key] = local_path
            return local_path
            
        except Exception as e:
            print(f"✗ 资源下载失败 {key}: {e}")
            return None
    
    def download_all_resources(self, progress_callback=None):
        """
        下载所有资源
        
        参数:
            progress_callback: 进度回调函数 (current, total)
        """
        total = len(self.RESOURCE_URLS)
        current = 0
        
        print(f"\n开始下载游戏资源 (共{total}个文件)...")
        print("=" * 50)
        
        for key in self.RESOURCE_URLS.keys():
            current += 1
            if progress_callback:
                progress_callback(current, total)
            
            self.download_resource(key)
        
        print("=" * 50)
        print(f"资源下载完成! 成功: {len(self.cached_resources)}/{total}\n")
    
    def get_resource_path(self, key: str) -> Optional[str]:
        """
        获取资源路径（如果不存在则尝试下载）
        
        参数:
            key: 资源键名
            
        返回:
            资源本地路径
        """
        if key in self.cached_resources:
            return self.cached_resources[key]
        
        return self.download_resource(key)
    
    def get_font_path(self, fallback: bool = True) -> str:
        """
        获取字体路径
        
        参数:
            fallback: 如果下载失败是否使用系统默认字体
            
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
        检查所有资源是否已下载
        
        返回:
            资源状态字典 {key: exists}
        """
        status = {}
        for key, info in self.RESOURCE_URLS.items():
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
    
    def cleanup_resources(self):
        """清理所有下载的资源"""
        for key, info in self.RESOURCE_URLS.items():
            path = info['path']
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"已删除: {path}")
                except Exception as e:
                    print(f"删除失败 {path}: {e}")
        
        self.cached_resources.clear()


# 全局资源管理器实例
_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """获取全局资源管理器实例"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


if __name__ == '__main__':
    # 测试资源下载
    print("测试资源管理器...")
    rm = ResourceManager()
    
    # 检查缺失资源
    missing = rm.get_missing_resources()
    if missing:
        print(f"\n缺失资源: {missing}")
        print("\n开始下载...")
        rm.download_all_resources()
    else:
        print("\n所有资源已就绪!")
    
    # 显示资源状态
    print("\n资源状态:")
    status = rm.check_all_resources()
    for key, exists in status.items():
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {key}")
