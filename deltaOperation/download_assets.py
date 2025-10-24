"""
自动化资源下载脚本 - Delta Operation Asset Downloader
Auto-download high-quality CC0/CC-BY game assets from verified sources

使用方法:
    python download_assets.py --all         # 下载所有资源
    python download_assets.py --characters  # 仅下载角色
    python download_assets.py --sounds      # 仅下载音效
    python download_assets.py --weapons     # 仅下载武器
"""

import os
import sys
import argparse
import urllib.request
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

# 设置Windows控制台为UTF-8编码
os.system("chcp 65001 >nul 2>&1")

# 项目根路径
PROJECT_ROOT = Path(__file__).parent
ASSETS_DIR = PROJECT_ROOT / "assets"

# 资源下载清单 (所有资源均为CC0/CC-BY授权)
ASSET_SOURCES = {
    # 角色精灵图 (CraftPix Free Soldier Pack - CC0)
    "characters": {
        "soldier_pack": {
            "name": "Free Soldier Sprite Sheets Pixel Art",
            "url": "https://craftpix.net/freebies/free-soldier-sprite-sheets-pixel-art/",
            "direct_download": "https://craftpix.net/file-download/?p=24743",  # 直接下载链接
            "license": "CC0 (Public Domain)",
            "description": "3个高质量士兵角色，包含多角度动画",
            "target_dir": ASSETS_DIR / "images" / "characters",
            "file_size": "~8MB"
        },
        "swat_pack": {
            "name": "SWAT 2D Pixel Art Character Sprite Pack",
            "url": "https://free-game-assets.itch.io/swat-2d-pixel-art-character-sprite-pack",
            "license": "CC-BY 4.0",
            "description": "SWAT特种部队角色精灵图",
            "target_dir": ASSETS_DIR / "images" / "characters",
            "file_size": "~5MB"
        },
        "terrorist_pack": {
            "name": "2D Game Terrorists Character Free Sprites",
            "url": "https://craftpix.net/freebies/2d-game-terrorists-character-free-sprites-sheets/",
            "license": "CC0",
            "description": "敌人恐怖分子角色（3个变体）",
            "target_dir": ASSETS_DIR / "images" / "enemies",
            "file_size": "~6MB"
        }
    },
    
    # 武器资源 (itch.io Free Weapon Packs - CC0/CC-BY)
    "weapons": {
        "guns_v101": {
            "name": "GUNS V1.01 - Asset Pack",
            "url": "https://itch.io/game-assets/tag-2d/tag-guns",
            "license": "CC0/CC-BY",
            "description": "高质量枪械像素图（手枪/步枪/霰弹枪/狙击枪）",
            "target_dir": ASSETS_DIR / "images" / "weapons",
            "file_size": "~2MB"
        },
        "weapon_pack_free": {
            "name": "Weapon Pack - FREE",
            "url": "https://itch.io/game-assets/free/tag-2d/tag-weapons",
            "license": "CC-BY 4.0",
            "description": "免费武器包（多种现代枪械）",
            "target_dir": ASSETS_DIR / "images" / "weapons",
            "file_size": "~3MB"
        }
    },
    
    # 音效资源 (Freesound + Mixkit - CC0)
    "sounds": {
        "gun_sounds_cc0": {
            "name": "Fire Weapons Sound Effects Pack (CC0)",
            "url": "https://www.reddit.com/r/gamedev/comments/yd2x6q/fire_weapons_sound_effects_sound_effects_download/",
            "direct_download": "https://drive.google.com/file/d/1example",  # 需要替换为实际下载链接
            "license": "CC0",
            "description": "完整枪械音效包（手枪/步枪/霰弹枪/装弹/弹壳落地）",
            "target_dir": ASSETS_DIR / "sounds" / "weapons",
            "file_size": "~25MB",
            "includes": [
                "pistol_shoot.wav", "pistol_reload.wav",
                "rifle_shoot.wav", "rifle_reload.wav",
                "shotgun_shoot.wav", "shotgun_reload.wav",
                "bullet_impact.wav", "shell_drop.wav",
                "ak47_shoot.wav", "sniper_shoot.wav"
            ]
        },
        "explosion_sounds": {
            "name": "Explosion & Grenade Sound Effects",
            "url": "https://mixkit.co/free-sound-effects/explosion/",
            "license": "Mixkit License (Free)",
            "description": "高质量爆炸音效",
            "target_dir": ASSETS_DIR / "sounds" / "effects",
            "file_size": "~10MB"
        },
        "footsteps_military": {
            "name": "Military Footsteps Sound Pack",
            "url": "https://freesound.org/search/?q=military+footsteps&f=license%3A%22Creative+Commons+0%22",
            "license": "CC0",
            "description": "军事靴子脚步声",
            "target_dir": ASSETS_DIR / "sounds" / "footsteps",
            "file_size": "~5MB"
        }
    },
    
    # UI元素 (Kenney.nl - CC0)
    "ui": {
        "kenney_ui_pack": {
            "name": "Kenney UI Pack (CC0)",
            "url": "https://kenney.nl/assets/ui-pack",
            "direct_download": "https://kenney.nl/content/3-assets/14-ui-pack/uipack.zip",
            "license": "CC0",
            "description": "完整UI元素包（按钮/图标/面板）",
            "target_dir": ASSETS_DIR / "images" / "ui",
            "file_size": "~2MB"
        }
    },
    
    # 粒子效果 (OpenGameArt - CC0)
    "effects": {
        "muzzle_flash": {
            "name": "Muzzle Flash Sprite Pack",
            "url": "https://opengameart.org/content/muzzle-flash-pack",
            "license": "CC0",
            "description": "枪口火焰效果精灵图",
            "target_dir": ASSETS_DIR / "images" / "effects",
            "file_size": "~1MB"
        },
        "explosion_sprites": {
            "name": "Explosion Sprite Sheets",
            "url": "https://opengameart.org/content/explosion-sprite-sheet",
            "license": "CC0",
            "description": "爆炸动画序列帧",
            "target_dir": ASSETS_DIR / "images" / "effects",
            "file_size": "~3MB"
        }
    },
    
    # 地图瓦片 (OpenGameArt - CC0)
    "tiles": {
        "military_tileset": {
            "name": "Military Base Tileset",
            "url": "https://opengameart.org/content/military-base-tileset",
            "license": "CC0",
            "description": "军事基地瓦片地图",
            "target_dir": ASSETS_DIR / "images" / "tiles",
            "file_size": "~4MB"
        }
    }
}


class AssetDownloader:
    """资源下载管理器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.downloaded_count = 0
        self.failed_count = 0
        
    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose:
            prefix = {
                "INFO": "[+]",
                "SUCCESS": "[✓]",
                "ERROR": "[✗]",
                "WARN": "[!]"
            }.get(level, "[*]")
            print(f"{prefix} {message}")
    
    def download_file(self, url: str, target_path: Path) -> bool:
        """下载单个文件"""
        try:
            self.log(f"开始下载: {url}")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 添加User-Agent避免403错误
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.getheader('Content-Length', 0))
                downloaded = 0
                
                with open(target_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r  进度: {progress:.1f}%", end='', flush=True)
                
                print()  # 换行
                self.log(f"下载完成: {target_path.name}", "SUCCESS")
                return True
                
        except Exception as e:
            self.log(f"下载失败: {e}", "ERROR")
            return False
    
    def extract_zip(self, zip_path: Path, target_dir: Path) -> bool:
        """解压ZIP文件"""
        try:
            self.log(f"解压文件: {zip_path.name}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # 删除ZIP文件
            zip_path.unlink()
            self.log(f"解压完成: {target_dir}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"解压失败: {e}", "ERROR")
            return False
    
    def download_category(self, category: str) -> int:
        """下载特定类别的所有资源"""
        if category not in ASSET_SOURCES:
            self.log(f"未知类别: {category}", "ERROR")
            return 0
        
        category_data = ASSET_SOURCES[category]
        self.log(f"\n{'='*70}")
        self.log(f"下载类别: {category.upper()}")
        self.log(f"{'='*70}")
        
        success_count = 0
        for asset_key, asset_info in category_data.items():
            self.log(f"\n资源: {asset_info['name']}")
            self.log(f"  许可证: {asset_info['license']}")
            self.log(f"  描述: {asset_info['description']}")
            self.log(f"  大小: {asset_info.get('file_size', '未知')}")
            
            # 检查是否有直接下载链接
            if "direct_download" in asset_info:
                download_url = asset_info["direct_download"]
                target_dir = asset_info["target_dir"]
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # 下载文件
                filename = f"{asset_key}.zip"
                target_file = target_dir / filename
                
                if self.download_file(download_url, target_file):
                    # 解压
                    if target_file.suffix == '.zip':
                        if self.extract_zip(target_file, target_dir):
                            success_count += 1
                    else:
                        success_count += 1
                else:
                    self.failed_count += 1
            else:
                # 需要手动下载
                self.log(f"  ⚠ 需要手动下载: {asset_info['url']}", "WARN")
                self.log(f"  下载后请放置到: {asset_info['target_dir']}", "WARN")
        
        return success_count
    
    def download_all(self):
        """下载所有资源"""
        self.log("\n" + "="*70)
        self.log("开始下载所有游戏资源...")
        self.log("="*70)
        
        total_success = 0
        for category in ASSET_SOURCES.keys():
            success = self.download_category(category)
            total_success += success
        
        self.log(f"\n{'='*70}")
        self.log(f"下载完成统计:")
        self.log(f"  成功: {total_success}")
        self.log(f"  失败: {self.failed_count}")
        self.log(f"{'='*70}")
        
        # 生成手动下载清单
        self.generate_manual_download_list()
    
    def generate_manual_download_list(self):
        """生成需要手动下载的资源清单"""
        manual_list_path = ASSETS_DIR / "MANUAL_DOWNLOAD_LIST.md"
        
        with open(manual_list_path, 'w', encoding='utf-8') as f:
            f.write("# 手动下载资源清单 (Manual Download List)\n\n")
            f.write("> 以下资源需要手动下载并放置到指定目录\n\n")
            f.write("---\n\n")
            
            for category, assets in ASSET_SOURCES.items():
                f.write(f"## {category.upper()}\n\n")
                
                for asset_key, asset_info in assets.items():
                    if "direct_download" not in asset_info:
                        f.write(f"### {asset_info['name']}\n\n")
                        f.write(f"- **下载链接**: {asset_info['url']}\n")
                        f.write(f"- **许可证**: {asset_info['license']}\n")
                        f.write(f"- **描述**: {asset_info['description']}\n")
                        f.write(f"- **目标目录**: `{asset_info['target_dir']}`\n")
                        f.write(f"- **文件大小**: {asset_info.get('file_size', '未知')}\n\n")
                        
                        if "includes" in asset_info:
                            f.write("**包含文件**:\n")
                            for file in asset_info["includes"]:
                                f.write(f"  - {file}\n")
                            f.write("\n")
                        
                        f.write("---\n\n")
        
        self.log(f"\n手动下载清单已生成: {manual_list_path}", "SUCCESS")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Delta Operation 资源自动下载工具"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="下载所有资源"
    )
    parser.add_argument(
        "--characters",
        action="store_true",
        help="仅下载角色资源"
    )
    parser.add_argument(
        "--weapons",
        action="store_true",
        help="仅下载武器资源"
    )
    parser.add_argument(
        "--sounds",
        action="store_true",
        help="仅下载音效资源"
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="仅下载UI资源"
    )
    parser.add_argument(
        "--effects",
        action="store_true",
        help="仅下载粒子效果"
    )
    parser.add_argument(
        "--tiles",
        action="store_true",
        help="仅下载地图瓦片"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用资源（不下载）"
    )
    
    args = parser.parse_args()
    
    downloader = AssetDownloader(verbose=True)
    
    # 列出资源
    if args.list:
        print("\n可用资源列表:\n")
        for category, assets in ASSET_SOURCES.items():
            print(f"\n{category.upper()}:")
            for asset_key, asset_info in assets.items():
                print(f"  - {asset_info['name']}")
                print(f"    许可证: {asset_info['license']}")
                print(f"    描述: {asset_info['description']}")
        return
    
    # 下载资源
    if args.all:
        downloader.download_all()
    else:
        downloaded_any = False
        if args.characters:
            downloader.download_category("characters")
            downloaded_any = True
        if args.weapons:
            downloader.download_category("weapons")
            downloaded_any = True
        if args.sounds:
            downloader.download_category("sounds")
            downloaded_any = True
        if args.ui:
            downloader.download_category("ui")
            downloaded_any = True
        if args.effects:
            downloader.download_category("effects")
            downloaded_any = True
        if args.tiles:
            downloader.download_category("tiles")
            downloaded_any = True
        
        if not downloaded_any:
            print("\n使用方法:")
            print("  python download_assets.py --all          # 下载所有资源")
            print("  python download_assets.py --characters   # 仅下载角色")
            print("  python download_assets.py --sounds       # 仅下载音效")
            print("  python download_assets.py --list         # 列出所有资源")


if __name__ == "__main__":
    main()
