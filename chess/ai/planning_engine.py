"""
Chess AI Agent 规划执行引擎 (Planning & Execution Engine)
实现AI自主规划能力，根据游戏状态和玩家需求自动规划使用工具或更新记忆

核心功能：
- 自主任务规划与分解
- 智能工具选择与组合
- 动态执行计划调整
- 目标导向的决策制定
- 多步骤任务协调
- 执行状态监控与错误恢复
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import copy

class TaskType(Enum):
    """任务类型"""
    CHESS_ANALYSIS = "chess_analysis"
    PLAYER_INTERACTION = "player_interaction" 
    KNOWLEDGE_SEARCH = "knowledge_search"
    MEMORY_OPERATION = "memory_operation"
    TEACHING_GUIDANCE = "teaching_guidance"
    GAME_MANAGEMENT = "game_management"
    VOICE_COMMUNICATION = "voice_communication"
    STRATEGIC_PLANNING = "strategic_planning"

class TaskPriority(Enum):
    """任务优先级"""
    URGENT = 1      # 紧急任务（如回应玩家问题）
    HIGH = 2        # 高优先级（如关键决策分析）
    MEDIUM = 3      # 中等优先级（如常规分析）
    LOW = 4         # 低优先级（如背景学习）

class TaskStatus(Enum):
    """任务状态"""
    PLANNED = "planned"           # 已规划
    READY = "ready"              # 准备执行
    RUNNING = "running"          # 执行中
    WAITING = "waiting"          # 等待依赖
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消

class PlanningStrategy(Enum):
    """规划策略"""
    REACTIVE = "reactive"        # 被动响应
    PROACTIVE = "proactive"      # 主动预测
    ADAPTIVE = "adaptive"        # 自适应调整
    COLLABORATIVE = "collaborative"  # 协作式

@dataclass
class Task:
    """任务定义"""
    id: str
    type: TaskType
    priority: TaskPriority
    name: str
    description: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    expected_duration: float = 10.0
    max_retries: int = 2
    
    # 执行状态
    status: TaskStatus = TaskStatus.PLANNED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    
    # 执行结果
    result: Any = None
    error_message: str = ""
    execution_log: List[str] = field(default_factory=list)
    
    def add_log(self, message: str):
        """添加执行日志"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.execution_log.append(f"[{timestamp}] {message}")

@dataclass 
class ExecutionPlan:
    """执行计划"""
    id: str
    name: str
    goal: str
    strategy: PlanningStrategy
    tasks: List[Task]
    created_at: datetime = field(default_factory=datetime.now)
    
    # 执行状态
    status: TaskStatus = TaskStatus.PLANNED
    progress: float = 0.0  # 0.0 - 1.0
    estimated_completion: Optional[datetime] = None
    
    # 性能指标
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    def update_progress(self):
        """更新执行进度"""
        if not self.tasks:
            self.progress = 1.0
            return
        
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        failed = sum(1 for task in self.tasks if task.status == TaskStatus.FAILED)
        
        self.completed_tasks = completed
        self.failed_tasks = failed
        self.total_tasks = len(self.tasks)
        self.progress = completed / len(self.tasks) if self.tasks else 1.0
        
        # 更新状态
        if self.progress >= 1.0:
            self.status = TaskStatus.COMPLETED
        elif any(task.status == TaskStatus.RUNNING for task in self.tasks):
            self.status = TaskStatus.RUNNING
        elif failed > 0 and completed + failed == len(self.tasks):
            self.status = TaskStatus.FAILED

class ChessPlanningEngine:
    """Chess AI Agent 规划执行引擎"""
    
    def __init__(self,
                 tool_system = None,
                 memory_system = None,
                 voice_system = None,
                 max_concurrent_tasks: int = 3,
                 planning_horizon: int = 10,
                 enable_proactive_planning: bool = True):
        """
        初始化规划执行引擎
        
        Args:
            tool_system: 工具系统
            memory_system: 记忆系统
            voice_system: 语音系统
            max_concurrent_tasks: 最大并发任务数
            planning_horizon: 规划时间范围（分钟）
            enable_proactive_planning: 启用主动规划
        """
        self.tool_system = tool_system
        self.memory_system = memory_system
        self.voice_system = voice_system
        self.max_concurrent_tasks = max_concurrent_tasks
        self.planning_horizon = planning_horizon
        self.enable_proactive_planning = enable_proactive_planning
        
        # 执行状态
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        
        # 规划知识库
        self.task_templates = self._init_task_templates()
        self.planning_rules = self._init_planning_rules()
        
        # 上下文状态
        self.game_context: Dict[str, Any] = {}
        self.player_context: Dict[str, Any] = {}
        self.conversation_context: List[Dict] = []
        
        # 统计信息
        self.stats = {
            'plans_created': 0,
            'tasks_executed': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_execution_time': 0.0,
            'proactive_actions': 0
        }
        
        # 日志设置
        self.logger = logging.getLogger(f"PlanningEngine_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # 启动执行循环
        self.running = True
        self.execution_task = None
        
        self.logger.info("规划执行引擎初始化完成")
    
    def _init_task_templates(self) -> Dict[str, Dict]:
        """初始化任务模板"""
        return {
            "analyze_position": {
                "type": TaskType.CHESS_ANALYSIS,
                "priority": TaskPriority.HIGH,
                "tools": ["analyze_position", "find_tactics"],
                "duration": 5.0,
                "description": "分析当前棋局位置"
            },
            "provide_hint": {
                "type": TaskType.PLAYER_INTERACTION,
                "priority": TaskPriority.HIGH,
                "tools": ["analyze_position", "explain_move"],
                "duration": 8.0,
                "description": "为玩家提供移动提示"
            },
            "search_opening_theory": {
                "type": TaskType.KNOWLEDGE_SEARCH,
                "priority": TaskPriority.MEDIUM,
                "tools": ["search_chess_theory", "get_opening_info"],
                "duration": 10.0,
                "description": "搜索开局理论"
            },
            "remember_game_state": {
                "type": TaskType.MEMORY_OPERATION,
                "priority": TaskPriority.LOW,
                "tools": ["store_game"],
                "duration": 2.0,
                "description": "记住当前游戏状态"
            },
            "create_teaching_moment": {
                "type": TaskType.TEACHING_GUIDANCE,
                "priority": TaskPriority.MEDIUM,
                "tools": ["create_lesson", "explain_move"],
                "duration": 15.0,
                "description": "创建教学时刻"
            },
            "voice_response": {
                "type": TaskType.VOICE_COMMUNICATION,
                "priority": TaskPriority.URGENT,
                "tools": [],
                "duration": 3.0,
                "description": "语音回应玩家"
            },
            "strategic_assessment": {
                "type": TaskType.STRATEGIC_PLANNING,
                "priority": TaskPriority.MEDIUM,
                "tools": ["analyze_position", "recall_similar"],
                "duration": 12.0,
                "description": "战略评估和规划"
            }
        }
    
    def _init_planning_rules(self) -> List[Dict]:
        """初始化规划规则"""
        return [
            {
                "name": "respond_to_questions",
                "condition": lambda ctx: ctx.get('player_asked_question', False),
                "action": "create_response_plan",
                "priority": TaskPriority.URGENT
            },
            {
                "name": "analyze_critical_positions", 
                "condition": lambda ctx: ctx.get('position_complexity', 0) > 0.7,
                "action": "create_analysis_plan",
                "priority": TaskPriority.HIGH
            },
            {
                "name": "provide_guidance",
                "condition": lambda ctx: ctx.get('player_needs_help', False),
                "action": "create_teaching_plan",
                "priority": TaskPriority.MEDIUM
            },
            {
                "name": "memory_consolidation",
                "condition": lambda ctx: ctx.get('significant_moves', 0) > 5,
                "action": "create_memory_plan",
                "priority": TaskPriority.LOW
            },
            {
                "name": "proactive_commentary",
                "condition": lambda ctx: ctx.get('silent_time', 0) > 60,
                "action": "create_commentary_plan",
                "priority": TaskPriority.LOW
            }
        ]
    
    async def start_execution_loop(self):
        """启动执行循环"""
        if self.execution_task is None:
            self.execution_task = asyncio.create_task(self._execution_loop())
            self.logger.info("执行循环已启动")
    
    async def _execution_loop(self):
        """主执行循环"""
        while self.running:
            try:
                # 更新上下文
                await self._update_context()
                
                # 主动规划
                if self.enable_proactive_planning:
                    await self._proactive_planning()
                
                # 执行就绪的任务
                await self._execute_ready_tasks()
                
                # 清理完成的计划
                self._cleanup_completed_plans()
                
                # 短暂休息
                await asyncio.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"执行循环错误: {e}")
                await asyncio.sleep(2.0)
    
    async def _update_context(self):
        """更新上下文信息"""
        try:
            # 更新游戏上下文
            current_time = time.time()
            self.game_context.update({
                'current_time': current_time,
                'last_update': getattr(self, '_last_context_update', current_time),
                'silent_time': current_time - self.game_context.get('last_interaction', current_time)
            })
            
            self._last_context_update = current_time
            
        except Exception as e:
            self.logger.warning(f"更新上下文失败: {e}")
    
    async def _proactive_planning(self):
        """主动规划"""
        try:
            # 检查规划规则
            for rule in self.planning_rules:
                try:
                    if rule['condition'](self.game_context):
                        plan = await self._create_plan_by_rule(rule)
                        if plan:
                            self.stats['proactive_actions'] += 1
                            self.logger.info(f"主动创建计划: {plan.name}")
                except Exception as e:
                    self.logger.warning(f"规则 {rule['name']} 检查失败: {e}")
        
        except Exception as e:
            self.logger.error(f"主动规划失败: {e}")
    
    async def _create_plan_by_rule(self, rule: Dict) -> Optional[ExecutionPlan]:
        """根据规则创建计划"""
        action = rule['action']
        
        if action == "create_response_plan":
            return await self.create_response_plan(
                self.game_context.get('player_question', ''),
                priority=rule['priority']
            )
        elif action == "create_analysis_plan":
            return await self.create_analysis_plan(
                self.game_context.get('current_position', ''),
                priority=rule['priority']
            )
        elif action == "create_teaching_plan":
            return await self.create_teaching_plan(
                self.game_context.get('teaching_topic', ''),
                priority=rule['priority']
            )
        elif action == "create_memory_plan":
            return await self.create_memory_plan(
                self.game_context.get('game_state', {}),
                priority=rule['priority']
            )
        elif action == "create_commentary_plan":
            return await self.create_commentary_plan(
                self.game_context.get('current_position', ''),
                priority=rule['priority']
            )
        
        return None
    
    async def create_response_plan(self, 
                                 question: str,
                                 priority: TaskPriority = TaskPriority.HIGH) -> ExecutionPlan:
        """创建响应计划"""
        plan_id = str(uuid.uuid4())[:8]
        
        # 分析问题类型
        question_type = self._classify_question(question)
        
        tasks = []
        
        # 根据问题类型创建不同任务
        if question_type == "position_analysis":
            tasks.extend([
                self._create_task("analyze_position", priority, {
                    'board_fen': self.game_context.get('current_position', ''),
                    'depth': 4
                }),
                self._create_task("voice_response", priority, {
                    'response_type': 'analysis',
                    'question': question
                })
            ])
        elif question_type == "move_suggestion":
            tasks.extend([
                self._create_task("provide_hint", priority, {
                    'position': self.game_context.get('current_position', ''),
                    'player_level': self.player_context.get('skill_level', 'intermediate')
                }),
                self._create_task("voice_response", priority, {
                    'response_type': 'suggestion',
                    'question': question
                })
            ])
        elif question_type == "theory_question":
            tasks.extend([
                self._create_task("search_opening_theory", priority, {
                    'query': question,
                    'context': self.game_context.get('current_position', '')
                }),
                self._create_task("voice_response", priority, {
                    'response_type': 'theory',
                    'question': question
                })
            ])
        else:
            # 通用响应
            tasks.append(self._create_task("voice_response", priority, {
                'response_type': 'general',
                'question': question
            }))
        
        plan = ExecutionPlan(
            id=plan_id,
            name=f"Response Plan: {question[:30]}...",
            goal=f"回应玩家问题: {question}",
            strategy=PlanningStrategy.REACTIVE,
            tasks=tasks
        )
        
        await self._register_plan(plan)
        return plan
    
    async def create_analysis_plan(self,
                                 position: str,
                                 priority: TaskPriority = TaskPriority.HIGH) -> ExecutionPlan:
        """创建分析计划"""
        plan_id = str(uuid.uuid4())[:8]
        
        tasks = [
            self._create_task("analyze_position", priority, {
                'board_fen': position,
                'depth': 5,
                'analysis_type': 'comprehensive'
            }),
            self._create_task("strategic_assessment", priority, {
                'position': position,
                'game_phase': self.game_context.get('game_phase', 'middlegame')
            }),
            self._create_task("remember_game_state", TaskPriority.LOW, {
                'position': position,
                'analysis_result': None,  # 将由前面的任务提供
                'importance': 0.7
            })
        ]
        
        # 设置任务依赖关系
        tasks[1].dependencies = [tasks[0].id]
        tasks[2].dependencies = [tasks[0].id, tasks[1].id]
        
        plan = ExecutionPlan(
            id=plan_id,
            name="深度位置分析",
            goal=f"全面分析位置: {position[:20]}...",
            strategy=PlanningStrategy.PROACTIVE,
            tasks=tasks
        )
        
        await self._register_plan(plan)
        return plan
    
    async def create_teaching_plan(self,
                                  topic: str,
                                  priority: TaskPriority = TaskPriority.MEDIUM) -> ExecutionPlan:
        """创建教学计划"""
        plan_id = str(uuid.uuid4())[:8]
        
        tasks = [
            self._create_task("create_teaching_moment", priority, {
                'topic': topic,
                'player_level': self.player_context.get('skill_level', 'intermediate'),
                'context': self.game_context.get('current_position', '')
            }),
            self._create_task("voice_response", priority, {
                'response_type': 'teaching',
                'topic': topic
            })
        ]
        
        tasks[1].dependencies = [tasks[0].id]
        
        plan = ExecutionPlan(
            id=plan_id,
            name=f"教学计划: {topic}",
            goal=f"为玩家提供关于{topic}的教学指导",
            strategy=PlanningStrategy.COLLABORATIVE,
            tasks=tasks
        )
        
        await self._register_plan(plan)
        return plan
    
    async def create_memory_plan(self,
                               game_state: Dict,
                               priority: TaskPriority = TaskPriority.LOW) -> ExecutionPlan:
        """创建记忆计划"""
        plan_id = str(uuid.uuid4())[:8]
        
        tasks = [
            self._create_task("remember_game_state", priority, {
                'game_state': game_state,
                'memory_type': 'game',
                'importance': 0.6
            })
        ]
        
        # 如果有重要的战术或策略发现，也要记住
        if game_state.get('tactical_themes'):
            tasks.append(self._create_task("remember_game_state", priority, {
                'content': json.dumps(game_state.get('tactical_themes')),
                'memory_type': 'strategy',
                'importance': 0.8
            }))
        
        plan = ExecutionPlan(
            id=plan_id,
            name="记忆巩固计划",
            goal="将重要信息存储到长期记忆",
            strategy=PlanningStrategy.ADAPTIVE,
            tasks=tasks
        )
        
        await self._register_plan(plan)
        return plan
    
    async def create_commentary_plan(self,
                                   position: str,
                                   priority: TaskPriority = TaskPriority.LOW) -> ExecutionPlan:
        """创建主动评论计划"""
        plan_id = str(uuid.uuid4())[:8]
        
        tasks = [
            self._create_task("analyze_position", priority, {
                'board_fen': position,
                'analysis_type': 'quick'
            }),
            self._create_task("voice_response", priority, {
                'response_type': 'commentary',
                'proactive': True
            })
        ]
        
        tasks[1].dependencies = [tasks[0].id]
        
        plan = ExecutionPlan(
            id=plan_id,
            name="主动评论计划",
            goal="提供主动的棋局评论和见解",
            strategy=PlanningStrategy.PROACTIVE,
            tasks=tasks
        )
        
        await self._register_plan(plan)
        return plan
    
    def _create_task(self, 
                    template_name: str,
                    priority: TaskPriority,
                    parameters: Dict[str, Any]) -> Task:
        """基于模板创建任务"""
        template = self.task_templates.get(template_name, {})
        
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            id=task_id,
            type=template.get('type', TaskType.CHESS_ANALYSIS),
            priority=priority,
            name=template_name,
            description=template.get('description', ''),
            parameters=parameters,
            tools_required=template.get('tools', []),
            expected_duration=template.get('duration', 10.0)
        )
        
        task.add_log(f"任务创建: {template_name}")
        return task
    
    async def _register_plan(self, plan: ExecutionPlan):
        """注册执行计划"""
        self.active_plans[plan.id] = plan
        
        # 将任务添加到队列
        for task in plan.tasks:
            task.status = TaskStatus.READY if not task.dependencies else TaskStatus.WAITING
            self.task_queue.append(task)
        
        self.stats['plans_created'] += 1
        self.logger.info(f"注册执行计划: {plan.name} (任务数: {len(plan.tasks)})")
    
    async def _execute_ready_tasks(self):
        """执行就绪的任务"""
        # 获取就绪任务（按优先级排序）
        ready_tasks = [
            task for task in self.task_queue 
            if task.status == TaskStatus.READY and self._check_dependencies(task)
        ]
        
        ready_tasks.sort(key=lambda t: t.priority.value)
        
        # 限制并发数量
        available_slots = self.max_concurrent_tasks - len(self.running_tasks)
        
        for task in ready_tasks[:available_slots]:
            await self._execute_task(task)
    
    def _check_dependencies(self, task: Task) -> bool:
        """检查任务依赖是否满足"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            # 查找依赖任务
            dep_task = None
            for t in self.task_queue:
                if t.id == dep_id:
                    dep_task = t
                    break
            
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _execute_task(self, task: Task):
        """执行单个任务"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.running_tasks[task.id] = task
            
            task.add_log(f"开始执行任务: {task.name}")
            self.logger.info(f"执行任务: {task.name} [{task.priority.value}]")
            
            # 根据任务类型选择执行方法
            if task.type == TaskType.CHESS_ANALYSIS:
                result = await self._execute_analysis_task(task)
            elif task.type == TaskType.PLAYER_INTERACTION:
                result = await self._execute_interaction_task(task)
            elif task.type == TaskType.KNOWLEDGE_SEARCH:
                result = await self._execute_search_task(task)
            elif task.type == TaskType.MEMORY_OPERATION:
                result = await self._execute_memory_task(task)
            elif task.type == TaskType.TEACHING_GUIDANCE:
                result = await self._execute_teaching_task(task)
            elif task.type == TaskType.VOICE_COMMUNICATION:
                result = await self._execute_voice_task(task)
            elif task.type == TaskType.STRATEGIC_PLANNING:
                result = await self._execute_strategic_task(task)
            else:
                result = await self._execute_generic_task(task)
            
            # 处理任务完成
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.add_log("任务执行完成")
            
            self.stats['tasks_completed'] += 1
            
        except Exception as e:
            # 处理任务失败
            task.error_message = str(e)
            task.status = TaskStatus.FAILED
            task.add_log(f"任务执行失败: {e}")
            
            # 尝试重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.READY
                task.add_log(f"准备重试 ({task.retry_count}/{task.max_retries})")
            else:
                self.stats['tasks_failed'] += 1
                self.logger.error(f"任务执行失败: {task.name} - {e}")
        
        finally:
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            
            self.stats['tasks_executed'] += 1
            
            # 更新相关计划的进度
            self._update_plan_progress(task)
    
    async def _execute_analysis_task(self, task: Task) -> Any:
        """执行分析类任务"""
        if not self.tool_system:
            return {"error": "工具系统不可用"}
        
        results = {}
        
        for tool_name in task.tools_required:
            if tool_name == "analyze_position":
                result = await self.tool_system.execute_tool(
                    'analyze_position',
                    task.parameters
                )
                results[tool_name] = result.result if result.success else result.error_message
            elif tool_name == "find_tactics":
                result = await self.tool_system.execute_tool(
                    'find_tactics',
                    {'board_fen': task.parameters.get('board_fen', '')}
                )
                results[tool_name] = result.result if result.success else result.error_message
        
        return results
    
    async def _execute_interaction_task(self, task: Task) -> Any:
        """执行玩家交互类任务"""
        if not self.tool_system:
            return {"error": "工具系统不可用"}
        
        results = {}
        
        if "provide_hint" in task.tools_required:
            # 提供移动提示
            analysis_result = await self.tool_system.execute_tool(
                'analyze_position',
                {
                    'board_fen': task.parameters.get('position', ''),
                    'depth': 3
                }
            )
            
            if analysis_result.success:
                explanation_result = await self.tool_system.execute_tool(
                    'explain_move',
                    {
                        'move': analysis_result.result.get('best_moves', [{}])[0].get('move', ''),
                        'position': task.parameters.get('position', ''),
                        'audience': task.parameters.get('player_level', 'intermediate')
                    }
                )
                
                results = {
                    'hint': analysis_result.result,
                    'explanation': explanation_result.result if explanation_result.success else "无法生成解释"
                }
        
        return results
    
    async def _execute_search_task(self, task: Task) -> Any:
        """执行知识搜索类任务"""
        if not self.tool_system:
            return {"error": "工具系统不可用"}
        
        results = {}
        
        for tool_name in task.tools_required:
            if tool_name == "search_chess_theory":
                result = await self.tool_system.execute_tool(
                    'search_chess_theory',
                    {
                        'query': task.parameters.get('query', ''),
                        'max_results': 5
                    }
                )
                results[tool_name] = result.result if result.success else result.error_message
            elif tool_name == "get_opening_info":
                result = await self.tool_system.execute_tool(
                    'get_opening_info',
                    {
                        'opening_name': task.parameters.get('opening_name', '')
                    }
                )
                results[tool_name] = result.result if result.success else result.error_message
        
        return results
    
    async def _execute_memory_task(self, task: Task) -> Any:
        """执行记忆操作类任务"""
        if not self.memory_system:
            return {"error": "记忆系统不可用"}
        
        try:
            memory_id = self.memory_system.store_memory(
                content=task.parameters.get('content', json.dumps(task.parameters.get('game_state', {}))),
                memory_type=task.parameters.get('memory_type', 'game'),
                importance=task.parameters.get('importance', 0.5)
            )
            
            return {"memory_id": memory_id, "success": True}
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _execute_teaching_task(self, task: Task) -> Any:
        """执行教学指导类任务"""
        if not self.tool_system:
            return {"error": "工具系统不可用"}
        
        # 创建教学内容
        lesson_result = await self.tool_system.execute_tool(
            'create_lesson',
            {
                'situation': {
                    'topic': task.parameters.get('topic', ''),
                    'difficulty': task.parameters.get('player_level', 'intermediate'),
                    'context': task.parameters.get('context', '')
                }
            }
        )
        
        return lesson_result.result if lesson_result.success else lesson_result.error_message
    
    async def _execute_voice_task(self, task: Task) -> Any:
        """执行语音通信类任务"""
        if not self.voice_system:
            return {"message": "语音系统不可用", "spoken": False}
        
        try:
            response_type = task.parameters.get('response_type', 'general')
            
            # 根据响应类型生成不同的语音内容
            if response_type == 'analysis':
                message = "让我分析一下这个位置..."
            elif response_type == 'suggestion':
                message = "我建议你考虑以下移动..."
            elif response_type == 'theory':
                message = "关于这个理论问题..."
            elif response_type == 'teaching':
                message = f"让我来教你关于{task.parameters.get('topic', '象棋')}的知识..."
            elif response_type == 'commentary':
                message = "从当前局面来看..."
            else:
                message = "好的，让我来帮助你..."
            
            # 执行语音合成
            success = await self.voice_system.speak_async(
                message,
                emotion=self.voice_system.EmotionType.FRIENDLY
            )
            
            return {"message": message, "spoken": success}
            
        except Exception as e:
            return {"error": str(e), "spoken": False}
    
    async def _execute_strategic_task(self, task: Task) -> Any:
        """执行战略规划类任务"""
        if not self.tool_system:
            return {"error": "工具系统不可用"}
        
        results = {}
        
        # 分析当前位置
        analysis_result = await self.tool_system.execute_tool(
            'analyze_position',
            {
                'board_fen': task.parameters.get('position', ''),
                'analysis_type': 'comprehensive'
            }
        )
        
        if analysis_result.success:
            results['current_analysis'] = analysis_result.result
            
            # 回忆相似局面
            recall_result = await self.tool_system.execute_tool(
                'recall_similar',
                {
                    'position_fen': task.parameters.get('position', ''),
                    'limit': 3
                }
            )
            
            if recall_result.success:
                results['similar_positions'] = recall_result.result
        
        return results
    
    async def _execute_generic_task(self, task: Task) -> Any:
        """执行通用任务"""
        # 简单执行所有需要的工具
        if not self.tool_system or not task.tools_required:
            return {"message": "任务执行完成"}
        
        results = {}
        
        for tool_name in task.tools_required:
            result = await self.tool_system.execute_tool(tool_name, task.parameters)
            results[tool_name] = result.result if result.success else result.error_message
        
        return results
    
    def _update_plan_progress(self, task: Task):
        """更新计划进度"""
        for plan in self.active_plans.values():
            if task in plan.tasks:
                plan.update_progress()
                
                if plan.status == TaskStatus.COMPLETED:
                    self.logger.info(f"执行计划完成: {plan.name}")
                elif plan.status == TaskStatus.FAILED:
                    self.logger.warning(f"执行计划失败: {plan.name}")
    
    def _cleanup_completed_plans(self):
        """清理已完成的计划"""
        completed_plans = [
            plan_id for plan_id, plan in self.active_plans.items()
            if plan.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]
        
        for plan_id in completed_plans:
            plan = self.active_plans[plan_id]
            
            # 从任务队列中移除已完成的任务
            plan_tasks = {task.id for task in plan.tasks}
            self.task_queue = [
                task for task in self.task_queue 
                if task.id not in plan_tasks
            ]
            
            # 移除计划
            del self.active_plans[plan_id]
            
            self.logger.debug(f"清理计划: {plan.name}")
    
    def _classify_question(self, question: str) -> str:
        """分类用户问题"""
        question_lower = question.lower()
        
        analysis_keywords = ['分析', '评估', '局面', '位置', 'analyze', 'evaluation']
        if any(keyword in question_lower for keyword in analysis_keywords):
            return "position_analysis"
        
        move_keywords = ['建议', '提示', '走法', '移动', 'suggest', 'hint', 'move']
        if any(keyword in question_lower for keyword in move_keywords):
            return "move_suggestion"
        
        theory_keywords = ['开局', '理论', '战术', '策略', 'opening', 'theory', 'tactic']
        if any(keyword in question_lower for keyword in theory_keywords):
            return "theory_question"
        
        return "general"
    
    # 公共接口方法
    
    def update_game_context(self, context: Dict[str, Any]):
        """更新游戏上下文"""
        self.game_context.update(context)
        self.game_context['last_interaction'] = time.time()
    
    def update_player_context(self, context: Dict[str, Any]):
        """更新玩家上下文"""
        self.player_context.update(context)
    
    async def handle_player_question(self, question: str) -> str:
        """处理玩家问题"""
        # 更新上下文
        self.game_context.update({
            'player_asked_question': True,
            'player_question': question,
            'last_interaction': time.time()
        })
        
        # 创建响应计划
        plan = await self.create_response_plan(question, TaskPriority.URGENT)
        
        return f"我正在思考你的问题：{question}。计划ID: {plan.id}"
    
    async def handle_move_made(self, move: str, position: str):
        """处理棋步制作"""
        # 更新游戏上下文
        self.game_context.update({
            'last_move': move,
            'current_position': position,
            'significant_moves': self.game_context.get('significant_moves', 0) + 1,
            'position_complexity': self._estimate_position_complexity(position)
        })
        
        # 可能触发主动分析
        if self.game_context.get('position_complexity', 0) > 0.7:
            await self.create_analysis_plan(position, TaskPriority.MEDIUM)
    
    def _estimate_position_complexity(self, position: str) -> float:
        """估算位置复杂度"""
        # 简化实现：基于位置字符串的复杂度估算
        # 实际实现应该分析棋子数量、攻击关系等
        return min(1.0, len(position.replace(' ', '')) / 100.0)
    
    def get_active_plans(self) -> List[Dict[str, Any]]:
        """获取活动计划列表"""
        return [
            {
                'id': plan.id,
                'name': plan.name,
                'status': plan.status.value,
                'progress': plan.progress,
                'tasks_total': plan.total_tasks,
                'tasks_completed': plan.completed_tasks,
                'created_at': plan.created_at.isoformat()
            }
            for plan in self.active_plans.values()
        ]
    
    def get_task_queue_status(self) -> Dict[str, Any]:
        """获取任务队列状态"""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(
                1 for task in self.task_queue if task.status == status
            )
        
        return {
            'total_tasks': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'status_breakdown': status_counts,
            'average_task_duration': sum(
                task.expected_duration for task in self.task_queue
            ) / len(self.task_queue) if self.task_queue else 0
        }
    
    def get_planning_stats(self) -> Dict[str, Any]:
        """获取规划统计信息"""
        total_execution_time = sum(
            (task.completed_at - task.started_at).total_seconds()
            for task in self.task_queue
            if task.completed_at and task.started_at
        )
        
        completed_tasks = self.stats['tasks_completed']
        
        return {
            **self.stats,
            'average_execution_time': (
                total_execution_time / completed_tasks if completed_tasks > 0 else 0
            ),
            'active_plans': len(self.active_plans),
            'queued_tasks': len(self.task_queue),
            'success_rate': (
                completed_tasks / self.stats['tasks_executed'] 
                if self.stats['tasks_executed'] > 0 else 0
            )
        }
    
    async def shutdown(self):
        """关闭规划引擎"""
        self.running = False
        
        # 等待执行循环结束
        if self.execution_task:
            self.execution_task.cancel()
            try:
                await self.execution_task
            except asyncio.CancelledError:
                pass
        
        # 清理资源
        self.active_plans.clear()
        self.task_queue.clear()
        self.running_tasks.clear()
        
        self.logger.info("规划执行引擎已关闭")

# 工厂函数
def create_planning_engine(**kwargs) -> ChessPlanningEngine:
    """创建规划执行引擎实例"""
    return ChessPlanningEngine(**kwargs)

# 测试和演示
if __name__ == "__main__":
    print("🧠 测试Chess AI Agent规划执行引擎...")
    
    async def test_planning_engine():
        # 创建规划引擎
        planning_engine = create_planning_engine(
            max_concurrent_tasks=2,
            planning_horizon=10,
            enable_proactive_planning=True
        )
        
        print("✅ 规划执行引擎创建成功")
        
        # 启动执行循环
        await planning_engine.start_execution_loop()
        
        # 更新游戏上下文
        planning_engine.update_game_context({
            'current_position': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'game_phase': 'opening',
            'position_complexity': 0.3
        })
        
        # 更新玩家上下文
        planning_engine.update_player_context({
            'skill_level': 'intermediate',
            'preferred_style': 'aggressive'
        })
        
        # 测试处理玩家问题
        print("\n🤔 测试问题处理...")
        response = await planning_engine.handle_player_question("分析一下当前局面")
        print(f"响应: {response}")
        
        # 等待一段时间让任务执行
        await asyncio.sleep(3)
        
        # 测试处理棋步
        print("\n♟️ 测试棋步处理...")
        await planning_engine.handle_move_made(
            "e2-e4", 
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        )
        
        # 等待更多任务执行
        await asyncio.sleep(3)
        
        # 显示活动计划
        print("\n📋 活动计划:")
        plans = planning_engine.get_active_plans()
        for plan in plans:
            print(f"  📊 {plan['name']}: {plan['status']} ({plan['progress']*100:.1f}%)")
        
        # 显示任务队列状态
        print("\n📈 任务队列状态:")
        queue_status = planning_engine.get_task_queue_status()
        for key, value in queue_status.items():
            print(f"  {key}: {value}")
        
        # 显示规划统计
        print("\n📊 规划统计:")
        stats = planning_engine.get_planning_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        # 等待更长时间让更多任务完成
        await asyncio.sleep(5)
        
        # 关闭规划引擎
        await planning_engine.shutdown()
        print("\n🎉 规划执行引擎测试完成!")
    
    def cleanup(self):
        """同步清理方法，供测试使用"""
        try:
            # 停止运行
            self.running = False
            
            # 如果有执行任务，尝试取消
            if self.execution_task and not self.execution_task.done():
                self.execution_task.cancel()
            
            # 清理任务队列
            if hasattr(self, 'task_queues'):
                for queue in self.task_queues.values():
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                        except:
                            break
            
            self.logger.info("规划引擎已清理")
            
        except Exception as e:
            self.logger.error(f"清理过程中发生错误: {e}")
    
    def sync_cleanup(self):
        """同步清理方法的别名，确保兼容性"""
        self.cleanup()
    
    # 运行测试
    asyncio.run(test_planning_engine())