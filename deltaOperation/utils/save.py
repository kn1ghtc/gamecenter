"""存档系统 - 保存和读取游戏进度"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from gamecenter.deltaOperation import config


class SaveSystem:
    """存档管理系统
    
    功能:
    - 保存/读取任务进度
    - 检查点自动保存
    - 玩家数据持久化
    - 游戏设置保存
    """
    
    def __init__(self):
        self.saves_dir = config.SAVES_DIR
        self.saves_dir.mkdir(exist_ok=True)
        
        self.current_save_slot = 1
        self.max_save_slots = 5
        
    def save_game(self, slot: int, game_data: Dict[str, Any]) -> bool:
        """保存游戏
        
        Args:
            slot: 存档槽位 (1-5)
            game_data: 游戏数据字典
            
        Returns:
            是否保存成功
        """
        if not 1 <= slot <= self.max_save_slots:
            print(f"[SaveSystem] 无效的存档槽位: {slot}")
            return False
            
        try:
            save_file = self.saves_dir / f"save_{slot}.json"
            
            # 添加元数据
            save_data = {
                "slot": slot,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0-alpha",
                "data": game_data
            }
            
            # 写入文件
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            print(f"[SaveSystem] 游戏已保存到槽位 {slot}")
            return True
            
        except Exception as e:
            print(f"[SaveSystem] 保存失败: {e}")
            return False
            
    def load_game(self, slot: int) -> Optional[Dict[str, Any]]:
        """读取游戏
        
        Args:
            slot: 存档槽位 (1-5)
            
        Returns:
            游戏数据字典,失败返回None
        """
        if not 1 <= slot <= self.max_save_slots:
            print(f"[SaveSystem] 无效的存档槽位: {slot}")
            return None
            
        try:
            save_file = self.saves_dir / f"save_{slot}.json"
            
            if not save_file.exists():
                print(f"[SaveSystem] 存档槽位 {slot} 为空")
                return None
                
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
                
            print(f"[SaveSystem] 加载存档槽位 {slot}")
            print(f"  保存时间: {save_data.get('timestamp', 'unknown')}")
            
            return save_data.get('data')
            
        except Exception as e:
            print(f"[SaveSystem] 读取失败: {e}")
            return None
            
    def delete_save(self, slot: int) -> bool:
        """删除存档
        
        Args:
            slot: 存档槽位 (1-5)
            
        Returns:
            是否删除成功
        """
        if not 1 <= slot <= self.max_save_slots:
            return False
            
        try:
            save_file = self.saves_dir / f"save_{slot}.json"
            if save_file.exists():
                save_file.unlink()
                print(f"[SaveSystem] 删除存档槽位 {slot}")
                return True
            return False
        except Exception as e:
            print(f"[SaveSystem] 删除失败: {e}")
            return False
            
    def list_saves(self) -> Dict[int, Dict[str, Any]]:
        """列出所有存档
        
        Returns:
            {slot: {timestamp, mission_id, ...}}
        """
        saves = {}
        
        for slot in range(1, self.max_save_slots + 1):
            save_file = self.saves_dir / f"save_{slot}.json"
            
            if save_file.exists():
                try:
                    with open(save_file, 'r', encoding='utf-8') as f:
                        save_data = json.load(f)
                        
                    saves[slot] = {
                        "timestamp": save_data.get("timestamp"),
                        "mission_id": save_data.get("data", {}).get("mission_id"),
                        "player_health": save_data.get("data", {}).get("player", {}).get("health"),
                        "progress": save_data.get("data", {}).get("progress", 0)
                    }
                except:
                    pass
                    
        return saves
        
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """保存设置
        
        Args:
            settings: 设置字典
            
        Returns:
            是否保存成功
        """
        try:
            settings_file = self.saves_dir / "settings.json"
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
                
            print("[SaveSystem] 设置已保存")
            return True
        except Exception as e:
            print(f"[SaveSystem] 设置保存失败: {e}")
            return False
            
    def load_settings(self) -> Dict[str, Any]:
        """读取设置
        
        Returns:
            设置字典,失败返回默认值
        """
        try:
            settings_file = self.saves_dir / "settings.json"
            
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[SaveSystem] 设置读取失败: {e}")
            
        # 返回默认设置
        return {
            "volume_master": 0.8,
            "volume_music": 0.6,
            "volume_sfx": 0.8,
            "fullscreen": False,
            "difficulty": "normal",
            "controls": "default"
        }
        
    def quick_save(self, game_data: Dict[str, Any]) -> bool:
        """快速保存(使用当前槽位)
        
        Args:
            game_data: 游戏数据
            
        Returns:
            是否保存成功
        """
        return self.save_game(self.current_save_slot, game_data)
        
    def quick_load(self) -> Optional[Dict[str, Any]]:
        """快速读取(使用当前槽位)
        
        Returns:
            游戏数据或None
        """
        return self.load_game(self.current_save_slot)
        
    def auto_save(self, game_data: Dict[str, Any]) -> bool:
        """自动保存(槽位0)
        
        Args:
            game_data: 游戏数据
            
        Returns:
            是否保存成功
        """
        try:
            auto_save_file = self.saves_dir / "autosave.json"
            
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0-alpha",
                "data": game_data
            }
            
            with open(auto_save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            print("[SaveSystem] 自动保存完成")
            return True
        except Exception as e:
            print(f"[SaveSystem] 自动保存失败: {e}")
            return False


def create_save_data(player, mission, level) -> Dict[str, Any]:
    """创建存档数据
    
    Args:
        player: 玩家对象
        mission: 任务对象
        level: 关卡对象
        
    Returns:
        存档数据字典
    """
    return {
        "mission_id": mission.mission_id if mission else 1,
        "progress": 0,  # TODO: 计算进度百分比
        "player": {
            "health": player.health if player else 100,
            "position": {
                "x": player.position.x if player else 0,
                "y": player.position.y if player else 0
            },
            "weapons": ["pistol"],  # TODO: 从player获取
            "ammo": {}  # TODO: 从player获取
        },
        "mission": {
            "completed_objectives": 0,  # TODO: 从mission获取
            "enemies_killed": mission.enemies_killed if mission else 0,
            "time_elapsed": mission.time_elapsed if mission else 0
        },
        "level": {
            "checkpoints_reached": 0,  # TODO: 从level获取
            "enemies_remaining": len(level.get_alive_enemies()) if level else 0
        }
    }
