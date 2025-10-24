"""任务系统 - 管理12个关卡任务,目标追踪,胜利/失败条件"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class ObjectiveType(Enum):
    """任务目标类型"""
    ELIMINATE_ALL = "eliminate_all"          # 消灭所有敌人
    ELIMINATE_COUNT = "eliminate_count"      # 消灭指定数量敌人
    RESCUE_HOSTAGE = "rescue_hostage"        # 营救人质
    REACH_EXTRACTION = "reach_extraction"    # 到达撤离点
    DESTROY_TARGET = "destroy_target"        # 摧毁目标物体
    SURVIVE_TIME = "survive_time"            # 存活指定时间
    COLLECT_INTEL = "collect_intel"          # 收集情报


class MissionStatus(Enum):
    """任务状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Objective:
    """任务目标"""
    obj_type: ObjectiveType
    description: str
    target_value: int = 0       # 目标值(如击杀数量)
    current_value: int = 0      # 当前进度
    completed: bool = False
    optional: bool = False      # 可选目标
    
    def update_progress(self, value: int = 1):
        """更新目标进度"""
        self.current_value += value
        if self.current_value >= self.target_value:
            self.completed = True
            
    def check_completion(self) -> bool:
        """检查目标是否完成"""
        return self.completed
        
    def get_progress_text(self) -> str:
        """获取进度文本"""
        if self.obj_type in [ObjectiveType.ELIMINATE_COUNT, ObjectiveType.COLLECT_INTEL]:
            return f"{self.current_value}/{self.target_value}"
        elif self.obj_type == ObjectiveType.SURVIVE_TIME:
            return f"{self.current_value}s/{self.target_value}s"
        return "已完成" if self.completed else "进行中"


@dataclass
class MissionConfig:
    """任务配置数据"""
    mission_id: int
    name: str
    description: str
    briefing: str                      # 任务简报
    level_id: int                      # 关卡ID
    difficulty: str                    # 难度: easy/normal/hard
    time_limit: Optional[int] = None   # 时间限制(秒), None表示无限制
    objectives: List[Objective] = field(default_factory=list)
    
    # 失败条件
    fail_on_player_death: bool = True
    fail_on_hostage_death: bool = False
    fail_on_time_limit: bool = False


class Mission:
    """任务管理器
    
    职责:
    - 加载任务配置
    - 追踪目标完成情况
    - 检查胜利/失败条件
    - 提供任务简报和提示
    """
    
    # 12个预设任务配置
    MISSION_PRESETS = {
        1: {
            "name": "黎明突袭",
            "description": "消灭武装分子基地的所有敌人",
            "briefing": "情报显示敌方在沙漠基地集结。你的任务是清除所有敌对武装,确保区域安全。",
            "level_id": 1,
            "difficulty": "easy",
            "objectives": [
                {"type": "eliminate_all", "desc": "消灭所有敌人", "value": 0},
                {"type": "reach_extraction", "desc": "到达撤离点", "value": 1}
            ]
        },
        2: {
            "name": "城市渗透",
            "description": "潜入城市区域,消灭15名敌人",
            "briefing": "目标区域有大量敌军巡逻。保持隐蔽,逐个击破,避免引起大规模警报。",
            "level_id": 2,
            "difficulty": "easy",
            "objectives": [
                {"type": "eliminate_count", "desc": "击杀15名敌人", "value": 15},
                {"type": "reach_extraction", "desc": "安全撤离", "value": 1}
            ]
        },
        3: {
            "name": "人质营救",
            "description": "营救被困人质并安全撤离",
            "briefing": "恐怖分子劫持了我方人员。你必须在5分钟内完成营救,不得让人质受到伤害。",
            "level_id": 3,
            "difficulty": "normal",
            "time_limit": 300,
            "objectives": [
                {"type": "rescue_hostage", "desc": "营救人质", "value": 3},
                {"type": "eliminate_all", "desc": "清除威胁", "value": 0},
                {"type": "reach_extraction", "desc": "护送撤离", "value": 1}
            ],
            "fail_on_hostage_death": True
        },
        4: {
            "name": "工业破坏",
            "description": "摧毁敌方武器工厂",
            "briefing": "目标是敌方的武器生产设施。摧毁3个关键目标,阻止其军事生产。",
            "level_id": 4,
            "difficulty": "normal",
            "objectives": [
                {"type": "destroy_target", "desc": "摧毁武器库", "value": 3},
                {"type": "eliminate_count", "desc": "击杀20名守卫", "value": 20},
                {"type": "reach_extraction", "desc": "撤离", "value": 1}
            ]
        },
        5: {
            "name": "情报收集",
            "description": "收集敌方情报文件",
            "briefing": "我们需要敌方的作战计划。潜入总部,收集5份机密文件,避免被发现。",
            "level_id": 5,
            "difficulty": "normal",
            "objectives": [
                {"type": "collect_intel", "desc": "收集情报", "value": 5},
                {"type": "reach_extraction", "desc": "安全撤离", "value": 1}
            ]
        },
        6: {
            "name": "防御战",
            "description": "守住阵地10分钟",
            "briefing": "敌军即将发起进攻。你必须在此坚守10分钟,直到增援到达。",
            "level_id": 6,
            "difficulty": "hard",
            "time_limit": 600,
            "objectives": [
                {"type": "survive_time", "desc": "存活10分钟", "value": 600},
                {"type": "eliminate_count", "desc": "击杀30名敌人", "value": 30, "optional": True}
            ]
        },
        7: {
            "name": "夜间突袭",
            "description": "夜间渗透敌军指挥部",
            "briefing": "利用夜幕掩护,潜入敌方指挥部。消灭高级指挥官并摧毁通讯设备。",
            "level_id": 7,
            "difficulty": "hard",
            "objectives": [
                {"type": "eliminate_count", "desc": "击杀指挥官", "value": 1},
                {"type": "destroy_target", "desc": "摧毁通讯塔", "value": 2},
                {"type": "reach_extraction", "desc": "撤离", "value": 1}
            ]
        },
        8: {
            "name": "护卫任务",
            "description": "护送VIP安全通过危险区域",
            "briefing": "要员需要穿越战区。你的任务是确保其安全,消灭沿途所有威胁。",
            "level_id": 8,
            "difficulty": "hard",
            "objectives": [
                {"type": "reach_extraction", "desc": "护送VIP到撤离点", "value": 1},
                {"type": "eliminate_all", "desc": "清除所有威胁", "value": 0}
            ],
            "fail_on_hostage_death": True
        },
        9: {
            "name": "狙击行动",
            "description": "远程消灭高价值目标",
            "briefing": "你将在制高点就位。目标是3名高级军官,使用狙击步枪完成任务。",
            "level_id": 9,
            "difficulty": "normal",
            "objectives": [
                {"type": "eliminate_count", "desc": "狙击目标", "value": 3},
                {"type": "reach_extraction", "desc": "撤离", "value": 1}
            ]
        },
        10: {
            "name": "最后防线",
            "description": "抵御敌军最后的反攻",
            "briefing": "敌军发起最后的疯狂进攻。坚守阵地,消灭所有来犯之敌!",
            "level_id": 10,
            "difficulty": "hard",
            "time_limit": 480,
            "objectives": [
                {"type": "eliminate_all", "desc": "击退进攻", "value": 0},
                {"type": "survive_time", "desc": "坚守8分钟", "value": 480}
            ]
        },
        11: {
            "name": "深入敌后",
            "description": "深入敌后执行破坏任务",
            "briefing": "这是一次危险的深入行动。摧毁5个补给站,击杀25名敌军,然后快速撤离。",
            "level_id": 11,
            "difficulty": "hard",
            "time_limit": 420,
            "objectives": [
                {"type": "destroy_target", "desc": "摧毁补给站", "value": 5},
                {"type": "eliminate_count", "desc": "击杀25名敌人", "value": 25},
                {"type": "reach_extraction", "desc": "撤离", "value": 1}
            ]
        },
        12: {
            "name": "最终对决",
            "description": "突袭敌军司令部,消灭BOSS",
            "briefing": "这是最后一战!突入敌军司令部,消灭所有抵抗,击败敌方统帅!",
            "level_id": 12,
            "difficulty": "hard",
            "objectives": [
                {"type": "eliminate_count", "desc": "击败BOSS", "value": 1},
                {"type": "eliminate_all", "desc": "清除所有敌人", "value": 0},
                {"type": "reach_extraction", "desc": "胜利撤离", "value": 1}
            ]
        }
    }
    
    def __init__(self, mission_id: int):
        self.mission_id = mission_id
        self.status = MissionStatus.NOT_STARTED
        self.elapsed_time = 0.0
        
        # 加载任务配置
        self.config = self._load_mission_config(mission_id)
        
        # 统计数据
        self.enemies_killed = 0
        self.hostages_rescued = 0
        self.intel_collected = 0
        self.targets_destroyed = 0
        
    def _load_mission_config(self, mission_id: int) -> MissionConfig:
        """加载任务配置"""
        if mission_id not in self.MISSION_PRESETS:
            raise ValueError(f"任务ID {mission_id} 不存在")
            
        preset = self.MISSION_PRESETS[mission_id]
        
        # 创建目标对象
        objectives = []
        for obj_data in preset["objectives"]:
            obj_type = ObjectiveType(obj_data["type"])
            objectives.append(Objective(
                obj_type=obj_type,
                description=obj_data["desc"],
                target_value=obj_data["value"],
                optional=obj_data.get("optional", False)
            ))
            
        return MissionConfig(
            mission_id=mission_id,
            name=preset["name"],
            description=preset["description"],
            briefing=preset["briefing"],
            level_id=preset["level_id"],
            difficulty=preset["difficulty"],
            time_limit=preset.get("time_limit"),
            objectives=objectives,
            fail_on_hostage_death=preset.get("fail_on_hostage_death", False)
        )
        
    def start_mission(self):
        """开始任务"""
        self.status = MissionStatus.IN_PROGRESS
        self.elapsed_time = 0.0
        
    def update(self, delta_time: float, level_manager, player):
        """更新任务状态
        
        Args:
            delta_time: 时间步长
            level_manager: 关卡管理器
            player: 玩家对象
        """
        if self.status != MissionStatus.IN_PROGRESS:
            return
            
        self.elapsed_time += delta_time
        
        # 检查时间限制
        if self.config.time_limit:
            if self.elapsed_time >= self.config.time_limit:
                if self.config.fail_on_time_limit:
                    self.fail_mission("时间到!")
                    return
                    
        # 自动更新消灭敌人目标
        alive_enemies = len(level_manager.get_alive_enemies())
        total_enemies = len(level_manager.enemies)
        self.enemies_killed = total_enemies - alive_enemies
        
        for obj in self.config.objectives:
            if obj.obj_type == ObjectiveType.ELIMINATE_ALL:
                obj.current_value = self.enemies_killed
                obj.target_value = total_enemies
                obj.completed = (alive_enemies == 0)
                
            elif obj.obj_type == ObjectiveType.ELIMINATE_COUNT:
                obj.current_value = self.enemies_killed
                obj.completed = (self.enemies_killed >= obj.target_value)
                
            elif obj.obj_type == ObjectiveType.SURVIVE_TIME:
                obj.current_value = int(self.elapsed_time)
                obj.completed = (self.elapsed_time >= obj.target_value)
                
            elif obj.obj_type == ObjectiveType.REACH_EXTRACTION:
                reached = level_manager.check_extraction(
                    (player.position.x, player.position.y)
                )
                if reached:
                    obj.completed = True
                    
        # 检查胜利条件
        self._check_victory()
        
    def on_enemy_killed(self):
        """敌人被击杀事件"""
        self.enemies_killed += 1
        
        for obj in self.config.objectives:
            if obj.obj_type == ObjectiveType.ELIMINATE_COUNT:
                obj.update_progress()
                
    def on_hostage_rescued(self):
        """人质被营救事件"""
        self.hostages_rescued += 1
        
        for obj in self.config.objectives:
            if obj.obj_type == ObjectiveType.RESCUE_HOSTAGE:
                obj.update_progress()
                
    def on_intel_collected(self):
        """情报被收集事件"""
        self.intel_collected += 1
        
        for obj in self.config.objectives:
            if obj.obj_type == ObjectiveType.COLLECT_INTEL:
                obj.update_progress()
                
    def on_target_destroyed(self):
        """目标被摧毁事件"""
        self.targets_destroyed += 1
        
        for obj in self.config.objectives:
            if obj.obj_type == ObjectiveType.DESTROY_TARGET:
                obj.update_progress()
                
    def on_player_death(self):
        """玩家死亡事件"""
        if self.config.fail_on_player_death:
            self.fail_mission("玩家阵亡")
            
    def on_hostage_death(self):
        """人质死亡事件"""
        if self.config.fail_on_hostage_death:
            self.fail_mission("人质死亡")
            
    def _check_victory(self):
        """检查胜利条件"""
        # 所有必需目标完成
        required_objectives = [obj for obj in self.config.objectives if not obj.optional]
        
        if all(obj.completed for obj in required_objectives):
            self.complete_mission()
            
    def complete_mission(self):
        """完成任务"""
        self.status = MissionStatus.COMPLETED
        
    def fail_mission(self, reason: str = "任务失败"):
        """任务失败"""
        self.status = MissionStatus.FAILED
        self.failure_reason = reason
        
    def is_completed(self) -> bool:
        """任务是否完成"""
        return self.status == MissionStatus.COMPLETED
        
    def is_failed(self) -> bool:
        """任务是否失败"""
        return self.status == MissionStatus.FAILED
        
    def get_completion_percentage(self) -> float:
        """获取完成百分比"""
        total = len(self.config.objectives)
        if total == 0:
            return 0.0
            
        completed = sum(1 for obj in self.config.objectives if obj.completed)
        return (completed / total) * 100
        
    def get_time_remaining(self) -> Optional[int]:
        """获取剩余时间(秒)"""
        if not self.config.time_limit:
            return None
        return max(0, int(self.config.time_limit - self.elapsed_time))
        
    def get_objectives_text(self) -> List[str]:
        """获取目标文本列表"""
        texts = []
        for i, obj in enumerate(self.config.objectives, 1):
            status = "✓" if obj.completed else "○"
            optional = " [可选]" if obj.optional else ""
            progress = obj.get_progress_text()
            texts.append(f"{status} {obj.description}{optional}: {progress}")
        return texts
