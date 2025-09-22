"""
Chess AI Agent 工具系统 (Tools System)
实现MCP工具集成、互联网搜索、象棋决策分析等工具调用能力

核心功能：
- MCP工具集成（深度研究、网络搜索、代码分析等）
- 象棋专业分析工具
- 互联网实时信息检索
- 自动工具选择和组合
- 工具执行状态跟踪
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os
import traceback

# 本地导入
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.board import ChessBoard
from game.pieces import PieceColor, PieceType

class ToolCategory(Enum):
    """工具分类"""
    CHESS_ANALYSIS = "chess_analysis"
    WEB_SEARCH = "web_search"
    KNOWLEDGE_BASE = "knowledge_base"
    MEMORY_OPERATION = "memory_operation"
    COMMUNICATION = "communication"
    UTILITY = "utility"

class ToolPriority(Enum):
    """工具优先级"""
    CRITICAL = 1    # 关键工具，必须成功
    HIGH = 2        # 高优先级
    MEDIUM = 3      # 中等优先级
    LOW = 4         # 低优先级

@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Any
    error_message: str = ""
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    category: ToolCategory
    priority: ToolPriority
    description: str
    parameters: Dict[str, Any]
    function: Callable
    timeout: float = 30.0
    retry_count: int = 2

class ChessToolSystem:
    """Chess AI Agent 工具系统"""
    
    def __init__(self, 
                 api_key: str = None,
                 enable_mcp: bool = True,
                 enable_web_search: bool = True,
                 enable_chess_engines: bool = True,
                 timeout_default: float = 30.0):
        """
        初始化工具系统
        
        Args:
            api_key: OpenAI API密钥（用于某些工具）
            enable_mcp: 启用MCP工具
            enable_web_search: 启用网络搜索
            enable_chess_engines: 启用象棋引擎
            timeout_default: 默认超时时间
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.enable_mcp = enable_mcp
        self.enable_web_search = enable_web_search
        self.enable_chess_engines = enable_chess_engines
        self.timeout_default = timeout_default
        
        # 工具注册表
        self.tools: Dict[str, ToolDefinition] = {}
        self.tool_usage_stats: Dict[str, Dict] = {}
        
        # MCP工具可用性
        self.mcp_available = self._check_mcp_availability()
        
        # 执行状态
        self.active_executions: Dict[str, Dict] = {}
        
        # 日志设置
        self.logger = logging.getLogger(f"ChessToolSystem_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # 初始化工具
        self._register_all_tools()
        
        self.logger.info(f"工具系统初始化完成，注册了 {len(self.tools)} 个工具")
    
    def _check_mcp_availability(self) -> Dict[str, bool]:
        """检查MCP工具可用性"""
        availability = {}
        
        if not self.enable_mcp:
            return availability
        
        # 尝试导入MCP相关模块（这里模拟检查过程）
        try:
            # 模拟检查各种MCP工具的可用性
            mcp_tools = [
                'deep_research',
                'brave_search', 
                'context7',
                'code_security_audit',
                'aihacker_penetration',
                'playwright_browser'
            ]
            
            for tool in mcp_tools:
                # 这里应该实际检查MCP工具是否可用
                # 暂时假设都可用
                availability[tool] = True
                
        except Exception as e:
            self.logger.warning(f"MCP工具检查失败: {e}")
        
        return availability
    
    def _register_all_tools(self):
        """注册所有工具"""
        # 象棋分析工具
        self._register_chess_tools()
        
        # 网络搜索工具
        if self.enable_web_search:
            self._register_web_search_tools()
        
        # MCP工具
        if self.enable_mcp:
            self._register_mcp_tools()
        
        # 内存和通信工具
        self._register_memory_tools()
        self._register_communication_tools()
        
        # 实用工具
        self._register_utility_tools()
    
    def _register_chess_tools(self):
        """注册象棋专业工具"""
        
        def analyze_chess_position(board_fen: str, depth: int = 3, analysis_type: str = "full") -> Dict:
            """深度分析象棋位置"""
            try:
                # 这里实现实际的象棋位置分析
                # 可以调用象棋引擎如Stockfish
                
                analysis = {
                    'position_evaluation': self._evaluate_position_from_fen(board_fen),
                    'best_moves': self._get_candidate_moves(board_fen, depth),
                    'tactical_themes': self._identify_tactics(board_fen),
                    'strategic_assessment': self._assess_strategy(board_fen),
                    'king_safety': self._evaluate_king_safety(board_fen),
                    'pawn_structure': self._analyze_pawn_structure(board_fen),
                    'piece_activity': self._analyze_piece_activity(board_fen)
                }
                
                if analysis_type == "quick":
                    # 快速分析，只返回核心信息
                    return {
                        'evaluation': analysis['position_evaluation'],
                        'best_move': analysis['best_moves'][0] if analysis['best_moves'] else None
                    }
                
                return analysis
                
            except Exception as e:
                return {'error': str(e), 'evaluation': 0.0}
        
        def find_tactical_motifs(board_fen: str) -> List[Dict]:
            """寻找战术主题"""
            try:
                motifs = []
                
                # 实现战术主题识别
                patterns = [
                    {'name': 'pin', 'description': '牵制'},
                    {'name': 'fork', 'description': '双重攻击'},
                    {'name': 'discovery', 'description': '发现攻击'},
                    {'name': 'deflection', 'description': '引开'},
                    {'name': 'decoy', 'description': '引诱'},
                    {'name': 'clearance', 'description': '清道'}
                ]
                
                # 简化实现：随机返回一些战术主题
                import random
                found_motifs = random.sample(patterns, random.randint(1, 3))
                
                for motif in found_motifs:
                    motifs.append({
                        'motif': motif['name'],
                        'description': motif['description'],
                        'confidence': random.uniform(0.6, 0.9),
                        'target_squares': []  # 实际实现需要计算具体格子
                    })
                
                return motifs
                
            except Exception as e:
                return [{'error': str(e)}]
        
        def calculate_time_management(game_context: Dict) -> Dict:
            """计算时间管理建议"""
            try:
                move_number = game_context.get('move_number', 1)
                remaining_time = game_context.get('remaining_time', 600)  # 10分钟
                game_phase = game_context.get('game_phase', 'middlegame')
                
                # 时间分配策略
                time_allocation = {
                    'opening': 0.1,    # 开局用10%时间
                    'middlegame': 0.6, # 中局用60%时间  
                    'endgame': 0.3     # 残局用30%时间
                }
                
                recommended_time = remaining_time * time_allocation.get(game_phase, 0.3) / 20
                
                return {
                    'recommended_thinking_time': max(5, min(60, recommended_time)),
                    'time_pressure': remaining_time < 60,
                    'should_play_quickly': remaining_time < 30,
                    'phase_time_budget': remaining_time * time_allocation.get(game_phase, 0.3)
                }
                
            except Exception as e:
                return {'error': str(e)}
        
        # 注册象棋工具
        self.register_tool(
            name="analyze_position",
            category=ToolCategory.CHESS_ANALYSIS,
            priority=ToolPriority.HIGH,
            description="深度分析象棋位置",
            parameters={'board_fen': str, 'depth': int, 'analysis_type': str},
            function=analyze_chess_position
        )
        
        self.register_tool(
            name="find_tactics",
            category=ToolCategory.CHESS_ANALYSIS,
            priority=ToolPriority.MEDIUM,
            description="寻找战术机会",
            parameters={'board_fen': str},
            function=find_tactical_motifs
        )
        
        self.register_tool(
            name="time_management",
            category=ToolCategory.CHESS_ANALYSIS,
            priority=ToolPriority.LOW,
            description="计算时间管理策略",
            parameters={'game_context': dict},
            function=calculate_time_management
        )
    
    def _register_web_search_tools(self):
        """注册网络搜索工具"""
        
        async def search_chess_theory(query: str, max_results: int = 5) -> Dict:
            """搜索象棋理论和开局"""
            try:
                # 构造专业的象棋搜索查询
                chess_query = f"chess theory {query} opening strategy tactics"
                
                # 这里应该调用实际的搜索API
                # 模拟搜索结果
                results = {
                    'query': chess_query,
                    'results': [
                        {
                            'title': f"Chess Theory: {query}",
                            'url': "https://example.com/chess-theory",
                            'description': f"Comprehensive analysis of {query} in chess",
                            'relevance': 0.9
                        },
                        {
                            'title': f"Master Games with {query}",
                            'url': "https://example.com/master-games", 
                            'description': f"Famous games featuring {query}",
                            'relevance': 0.8
                        }
                    ],
                    'search_time': time.time()
                }
                
                return results
                
            except Exception as e:
                return {'error': str(e), 'results': []}
        
        async def get_opening_database(opening_name: str) -> Dict:
            """获取开局数据库信息"""
            try:
                # 模拟开局数据库查询
                opening_data = {
                    'opening_name': opening_name,
                    'eco_code': 'B00',  # 实际需要查询ECO编码
                    'main_moves': ['e2-e4', 'e7-e5', 'g1-f3'],
                    'statistics': {
                        'white_wins': 0.45,
                        'draws': 0.30,
                        'black_wins': 0.25
                    },
                    'famous_games': [
                        {'white': 'Kasparov', 'black': 'Karpov', 'year': 1984},
                        {'white': 'Fischer', 'black': 'Spassky', 'year': 1972}
                    ],
                    'theory_depth': 15,
                    'popularity': 0.8
                }
                
                return opening_data
                
            except Exception as e:
                return {'error': str(e)}
        
        # 注册网络搜索工具
        self.register_tool(
            name="search_chess_theory",
            category=ToolCategory.WEB_SEARCH,
            priority=ToolPriority.MEDIUM,
            description="搜索象棋理论和策略",
            parameters={'query': str, 'max_results': int},
            function=search_chess_theory
        )
        
        self.register_tool(
            name="get_opening_info",
            category=ToolCategory.KNOWLEDGE_BASE,
            priority=ToolPriority.MEDIUM,
            description="获取开局理论信息",
            parameters={'opening_name': str},
            function=get_opening_database
        )
    
    def _register_mcp_tools(self):
        """注册MCP工具"""
        
        async def deep_research_chess(topic: str, max_papers: int = 5) -> Dict:
            """使用Deep Research服务搜索象棋学术资料"""
            try:
                if not self.mcp_available.get('deep_research', False):
                    return {'error': 'Deep Research MCP tool not available'}
                
                # 这里应该调用实际的MCP Deep Research工具
                # 由于MCP工具在外层环境中，这里模拟调用过程
                
                research_result = {
                    'topic': topic,
                    'papers_found': [
                        {
                            'title': f"AI and Chess: {topic} Analysis",
                            'authors': ["AI Researcher", "Chess Master"],
                            'abstract': f"This paper analyzes {topic} in chess using AI methods...",
                            'year': 2023,
                            'citations': 25
                        }
                    ],
                    'knowledge_graph': {
                        'concepts': [topic, 'chess AI', 'game theory'],
                        'relationships': []
                    },
                    'summary': f"Research summary for {topic} in chess context"
                }
                
                return research_result
                
            except Exception as e:
                return {'error': str(e)}
        
        async def web_search_realtime(query: str, search_type: str = "web") -> Dict:
            """实时网络搜索"""
            try:
                if not self.mcp_available.get('brave_search', False):
                    return {'error': 'Brave Search MCP tool not available'}
                
                # 模拟调用Brave Search MCP工具
                search_result = {
                    'query': query,
                    'search_type': search_type,
                    'results': [
                        {
                            'title': f"Latest info about {query}",
                            'url': "https://example.com",
                            'description': f"Current information about {query}...",
                            'timestamp': datetime.now().isoformat()
                        }
                    ],
                    'total_results': 100
                }
                
                return search_result
                
            except Exception as e:
                return {'error': str(e)}
        
        async def analyze_chess_code(code_snippet: str) -> Dict:
            """分析象棋相关代码"""
            try:
                if not self.mcp_available.get('code_security_audit', False):
                    return {'error': 'Code Security Audit MCP tool not available'}
                
                # 模拟代码分析
                analysis_result = {
                    'code_quality': 'good',
                    'security_issues': [],
                    'performance_suggestions': [
                        'Consider using bitboards for position representation',
                        'Implement alpha-beta pruning for search optimization'
                    ],
                    'chess_specific_advice': [
                        'Use standard chess notation for moves',
                        'Implement proper castling and en passant rules'
                    ]
                }
                
                return analysis_result
                
            except Exception as e:
                return {'error': str(e)}
        
        # 注册MCP工具
        self.register_tool(
            name="deep_research",
            category=ToolCategory.KNOWLEDGE_BASE,
            priority=ToolPriority.HIGH,
            description="深度学术研究",
            parameters={'topic': str, 'max_papers': int},
            function=deep_research_chess
        )
        
        self.register_tool(
            name="web_search_live",
            category=ToolCategory.WEB_SEARCH,
            priority=ToolPriority.MEDIUM,
            description="实时网络搜索",
            parameters={'query': str, 'search_type': str},
            function=web_search_realtime
        )
        
        self.register_tool(
            name="code_analysis", 
            category=ToolCategory.UTILITY,
            priority=ToolPriority.LOW,
            description="分析象棋代码",
            parameters={'code_snippet': str},
            function=analyze_chess_code
        )
    
    def _register_memory_tools(self):
        """注册记忆操作工具"""
        
        def store_game_memory(game_data: Dict, importance: float = 0.5) -> str:
            """存储游戏记忆"""
            try:
                # 这里应该集成实际的记忆系统
                memory_id = f"game_{int(time.time())}"
                
                # 模拟存储过程
                stored_data = {
                    'memory_id': memory_id,
                    'content': json.dumps(game_data),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'game',
                    'importance': importance
                }
                
                return memory_id
                
            except Exception as e:
                return f"Error storing memory: {e}"
        
        def recall_similar_games(position_fen: str, limit: int = 5) -> List[Dict]:
            """回忆相似的游戏局面"""
            try:
                # 模拟相似局面搜索
                similar_games = [
                    {
                        'game_id': 'game_001',
                        'position': position_fen,
                        'result': 'white_wins',
                        'best_move': 'Qh5',
                        'similarity': 0.87,
                        'notes': 'Similar pawn structure'
                    }
                ]
                
                return similar_games[:limit]
                
            except Exception as e:
                return [{'error': str(e)}]
        
        # 注册记忆工具
        self.register_tool(
            name="store_game",
            category=ToolCategory.MEMORY_OPERATION,
            priority=ToolPriority.MEDIUM,
            description="存储游戏记忆",
            parameters={'game_data': dict, 'importance': float},
            function=store_game_memory
        )
        
        self.register_tool(
            name="recall_similar",
            category=ToolCategory.MEMORY_OPERATION,
            priority=ToolPriority.HIGH,
            description="回忆相似局面",
            parameters={'position_fen': str, 'limit': int},
            function=recall_similar_games
        )
    
    def _register_communication_tools(self):
        """注册通信工具"""
        
        def generate_explanation(move: str, position: str, audience: str = "intermediate") -> str:
            """生成移动解释"""
            try:
                explanations = {
                    'beginner': f"The move {move} is played to improve the position. This is a common strategy in this type of position.",
                    'intermediate': f"Move {move} serves multiple purposes: it develops a piece, controls key squares, and prepares for the next phase of the game.",
                    'advanced': f"The move {move} is based on deep positional understanding, considering pawn structure dynamics and long-term strategic goals."
                }
                
                return explanations.get(audience, explanations['intermediate'])
                
            except Exception as e:
                return f"Error generating explanation: {e}"
        
        def create_teaching_moment(situation: Dict) -> Dict:
            """创建教学时刻"""
            try:
                teaching_content = {
                    'concept': situation.get('concept', 'General Chess Principle'),
                    'explanation': "This is a great opportunity to learn about chess strategy...",
                    'examples': ["Example 1: ...", "Example 2: ..."],
                    'exercises': ["Try to find the best move in this position"],
                    'difficulty': situation.get('difficulty', 'medium')
                }
                
                return teaching_content
                
            except Exception as e:
                return {'error': str(e)}
        
        # 注册通信工具
        self.register_tool(
            name="explain_move",
            category=ToolCategory.COMMUNICATION,
            priority=ToolPriority.HIGH,
            description="解释棋步",
            parameters={'move': str, 'position': str, 'audience': str},
            function=generate_explanation
        )
        
        self.register_tool(
            name="create_lesson",
            category=ToolCategory.COMMUNICATION,
            priority=ToolPriority.MEDIUM,
            description="创建教学内容",
            parameters={'situation': dict},
            function=create_teaching_moment
        )
    
    def _register_utility_tools(self):
        """注册实用工具"""
        
        def format_chess_notation(moves: List[str], format_type: str = "algebraic") -> str:
            """格式化象棋记谱"""
            try:
                if format_type == "algebraic":
                    formatted = " ".join(f"{i//2 + 1}.{' ' if i%2==0 else '.. '}{move}" 
                                       for i, move in enumerate(moves))
                elif format_type == "pgn":
                    formatted = " ".join(moves)
                else:
                    formatted = str(moves)
                
                return formatted
                
            except Exception as e:
                return f"Error formatting notation: {e}"
        
        def calculate_statistics(game_history: List[Dict]) -> Dict:
            """计算游戏统计"""
            try:
                if not game_history:
                    return {'error': 'No game history provided'}
                
                stats = {
                    'total_games': len(game_history),
                    'wins': sum(1 for g in game_history if g.get('result') == 'win'),
                    'losses': sum(1 for g in game_history if g.get('result') == 'loss'),
                    'draws': sum(1 for g in game_history if g.get('result') == 'draw'),
                    'average_game_length': sum(g.get('moves', 0) for g in game_history) / len(game_history),
                    'favorite_opening': 'e2-e4'  # 简化计算
                }
                
                stats['win_rate'] = stats['wins'] / stats['total_games'] if stats['total_games'] > 0 else 0
                
                return stats
                
            except Exception as e:
                return {'error': str(e)}
        
        # 注册实用工具
        self.register_tool(
            name="format_notation",
            category=ToolCategory.UTILITY,
            priority=ToolPriority.LOW,
            description="格式化棋谱记号",
            parameters={'moves': list, 'format_type': str},
            function=format_chess_notation
        )
        
        self.register_tool(
            name="game_statistics",
            category=ToolCategory.UTILITY,
            priority=ToolPriority.LOW,
            description="计算游戏统计",
            parameters={'game_history': list},
            function=calculate_statistics
        )
    
    def register_tool(self,
                     name: str,
                     category: ToolCategory,
                     priority: ToolPriority,
                     description: str,
                     parameters: Dict[str, Any],
                     function: Callable,
                     timeout: float = None) -> bool:
        """
        注册新工具
        
        Args:
            name: 工具名称
            category: 工具分类
            priority: 优先级
            description: 描述
            parameters: 参数定义
            function: 执行函数
            timeout: 超时时间
            
        Returns:
            注册是否成功
        """
        try:
            if name in self.tools:
                self.logger.warning(f"工具 {name} 已存在，将被覆盖")
            
            tool_def = ToolDefinition(
                name=name,
                category=category,
                priority=priority,
                description=description,
                parameters=parameters,
                function=function,
                timeout=timeout or self.timeout_default
            )
            
            self.tools[name] = tool_def
            
            # 初始化使用统计
            self.tool_usage_stats[name] = {
                'call_count': 0,
                'success_count': 0,
                'total_execution_time': 0.0,
                'last_used': None,
                'error_count': 0
            }
            
            self.logger.debug(f"注册工具: {name} [{category.value}]")
            return True
            
        except Exception as e:
            self.logger.error(f"注册工具 {name} 失败: {e}")
            return False
    
    def list_available_tools(self, category: ToolCategory = None) -> List[Dict[str, Any]]:
        """
        列出可用工具
        
        Args:
            category: 过滤工具分类
            
        Returns:
            工具信息列表
        """
        tools_info = []
        
        for name, tool_def in self.tools.items():
            if category is None or tool_def.category == category:
                tool_info = {
                    'name': name,
                    'category': tool_def.category.value,
                    'priority': tool_def.priority.value,
                    'description': tool_def.description,
                    'timeout': tool_def.timeout,
                    'parameters': tool_def.parameters
                }
                
                # 添加使用统计
                if name in self.tool_usage_stats:
                    tool_info['usage_stats'] = self.tool_usage_stats[name]
                
                tools_info.append(tool_info)
        
        return tools_info
    
    async def execute_tool(self, 
                          tool_name: str, 
                          parameters: Dict[str, Any] = None,
                          timeout: float = None) -> ToolResult:
        """
        执行指定工具
        
        Args:
            tool_name: 工具名称
            parameters: 参数
            timeout: 超时时间
            
        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=f"工具 {tool_name} 未找到"
            )
        
        tool_def = self.tools[tool_name]
        execution_id = f"{tool_name}_{int(time.time() * 1000)}"
        
        # 记录执行开始
        self.active_executions[execution_id] = {
            'tool_name': tool_name,
            'start_time': time.time(),
            'parameters': parameters or {}
        }
        
        try:
            # 更新统计
            self.tool_usage_stats[tool_name]['call_count'] += 1
            self.tool_usage_stats[tool_name]['last_used'] = datetime.now()
            
            start_time = time.time()
            
            # 执行工具（支持异步和同步函数）
            if asyncio.iscoroutinefunction(tool_def.function):
                result = await asyncio.wait_for(
                    tool_def.function(**(parameters or {})),
                    timeout=timeout or tool_def.timeout
                )
            else:
                result = tool_def.function(**(parameters or {}))
            
            execution_time = time.time() - start_time
            
            # 更新统计
            self.tool_usage_stats[tool_name]['success_count'] += 1
            self.tool_usage_stats[tool_name]['total_execution_time'] += execution_time
            
            # 清理执行记录
            del self.active_executions[execution_id]
            
            self.logger.debug(f"工具 {tool_name} 执行成功，耗时 {execution_time:.2f}s")
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={
                    'category': tool_def.category.value,
                    'priority': tool_def.priority.value
                }
            )
            
        except asyncio.TimeoutError:
            self.tool_usage_stats[tool_name]['error_count'] += 1
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            error_msg = f"工具 {tool_name} 执行超时"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=error_msg,
                execution_time=timeout or tool_def.timeout
            )
            
        except Exception as e:
            self.tool_usage_stats[tool_name]['error_count'] += 1
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            error_msg = f"工具 {tool_name} 执行异常: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=error_msg,
                execution_time=time.time() - start_time if 'start_time' in locals() else 0
            )
    
    async def execute_tool_chain(self, 
                                tool_chain: List[Dict[str, Any]],
                                stop_on_error: bool = False) -> List[ToolResult]:
        """
        执行工具链
        
        Args:
            tool_chain: 工具链定义，每个元素包含tool_name和parameters
            stop_on_error: 遇到错误时是否停止
            
        Returns:
            工具执行结果列表
        """
        results = []
        
        for i, tool_spec in enumerate(tool_chain):
            tool_name = tool_spec.get('tool_name')
            parameters = tool_spec.get('parameters', {})
            
            if not tool_name:
                results.append(ToolResult(
                    tool_name="unknown",
                    success=False,
                    result=None,
                    error_message=f"工具链第 {i+1} 步缺少tool_name"
                ))
                if stop_on_error:
                    break
                continue
            
            # 从前面的结果中获取参数（支持链式传递）
            if i > 0 and 'use_previous_result' in tool_spec:
                previous_result = results[i-1]
                if previous_result.success:
                    if isinstance(previous_result.result, dict):
                        parameters.update(previous_result.result)
            
            result = await self.execute_tool(tool_name, parameters)
            results.append(result)
            
            if not result.success and stop_on_error:
                self.logger.error(f"工具链在第 {i+1} 步失败，停止执行")
                break
        
        return results
    
    def suggest_tools_for_context(self, context: Dict[str, Any]) -> List[str]:
        """
        根据上下文建议合适的工具
        
        Args:
            context: 上下文信息
            
        Returns:
            建议的工具名称列表
        """
        suggestions = []
        
        # 分析上下文
        needs_analysis = context.get('needs_position_analysis', False)
        needs_research = context.get('needs_research', False) 
        needs_explanation = context.get('needs_explanation', False)
        game_phase = context.get('game_phase', 'middlegame')
        player_level = context.get('player_level', 'intermediate')
        
        # 根据需求建议工具
        if needs_analysis:
            suggestions.extend(['analyze_position', 'find_tactics'])
        
        if needs_research:
            suggestions.extend(['deep_research', 'search_chess_theory'])
        
        if needs_explanation:
            suggestions.append('explain_move')
            if player_level == 'beginner':
                suggestions.append('create_lesson')
        
        # 根据游戏阶段建议工具
        if game_phase == 'opening':
            suggestions.append('get_opening_info')
        elif game_phase == 'endgame':
            suggestions.append('recall_similar')
        
        # 移除重复并按优先级排序
        unique_suggestions = list(dict.fromkeys(suggestions))  # 保持顺序去重
        
        # 按工具优先级排序
        prioritized_suggestions = sorted(
            unique_suggestions,
            key=lambda name: self.tools[name].priority.value if name in self.tools else 99
        )
        
        return prioritized_suggestions[:5]  # 最多返回5个建议
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        if tool_name not in self.tools:
            return None
        
        tool_def = self.tools[tool_name]
        stats = self.tool_usage_stats[tool_name]
        
        return {
            'name': tool_def.name,
            'category': tool_def.category.value,
            'priority': tool_def.priority.value,
            'description': tool_def.description,
            'parameters': tool_def.parameters,
            'timeout': tool_def.timeout,
            'usage_stats': {
                **stats,
                'last_used': stats['last_used'].isoformat() if stats['last_used'] else None,
                'average_execution_time': (
                    stats['total_execution_time'] / stats['success_count'] 
                    if stats['success_count'] > 0 else 0
                ),
                'success_rate': (
                    stats['success_count'] / stats['call_count'] 
                    if stats['call_count'] > 0 else 0
                )
            }
        }
    
    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """获取指定分类的工具"""
        return [
            name for name, tool_def in self.tools.items() 
            if tool_def.category == category
        ]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取工具系统统计信息"""
        total_calls = sum(stats['call_count'] for stats in self.tool_usage_stats.values())
        total_successes = sum(stats['success_count'] for stats in self.tool_usage_stats.values())
        
        return {
            'total_tools': len(self.tools),
            'tools_by_category': {
                category.value: len(self.get_tools_by_category(category))
                for category in ToolCategory
            },
            'mcp_available': self.mcp_available,
            'total_tool_calls': total_calls,
            'overall_success_rate': total_successes / total_calls if total_calls > 0 else 0,
            'active_executions': len(self.active_executions),
            'most_used_tools': sorted(
                self.tool_usage_stats.items(),
                key=lambda x: x[1]['call_count'],
                reverse=True
            )[:5]
        }
    
    def cleanup(self):
        """清理资源"""
        try:
            # 取消活动执行
            for execution_id in list(self.active_executions.keys()):
                del self.active_executions[execution_id]
            
            # 清理统计
            self.tool_usage_stats.clear()
            
            self.logger.info("工具系统清理完成")
            
        except Exception as e:
            self.logger.error(f"清理工具系统失败: {e}")
    
    # 简化的象棋分析实现（这些方法在实际应用中需要更复杂的实现）
    
    def _evaluate_position_from_fen(self, fen: str) -> float:
        """从FEN评估位置"""
        # 简化实现：返回随机评分
        import random
        return random.uniform(-2.0, 2.0)
    
    def _get_candidate_moves(self, fen: str, depth: int) -> List[Dict]:
        """获取候选移动"""
        # 简化实现
        moves = [
            {'move': 'e2e4', 'evaluation': 0.3, 'depth': depth},
            {'move': 'd2d4', 'evaluation': 0.2, 'depth': depth},
            {'move': 'g1f3', 'evaluation': 0.15, 'depth': depth}
        ]
        return moves
    
    def _identify_tactics(self, fen: str) -> List[str]:
        """识别战术"""
        return ['pin', 'fork', 'discovery']
    
    def _assess_strategy(self, fen: str) -> str:
        """评估策略"""
        return "控制中心，发展子力"
    
    def _evaluate_king_safety(self, fen: str) -> Dict:
        """评估王安全"""
        return {'white_king_safety': 0.7, 'black_king_safety': 0.6}
    
    def _analyze_pawn_structure(self, fen: str) -> Dict:
        """分析兵型"""
        return {'isolated_pawns': 1, 'doubled_pawns': 0, 'passed_pawns': 2}
    
    def _analyze_piece_activity(self, fen: str) -> Dict:
        """分析子力活跃度"""
        return {'white_activity': 0.6, 'black_activity': 0.5}

# 工厂函数
def create_tool_system(**kwargs) -> ChessToolSystem:
    """创建工具系统实例"""
    return ChessToolSystem(**kwargs)

# 测试和演示
if __name__ == "__main__":
    print("🛠️ 测试Chess AI Agent工具系统...")
    
    async def test_tool_system():
        # 创建工具系统
        tool_system = create_tool_system(
            enable_mcp=True,
            enable_web_search=True,
            enable_chess_engines=True
        )
        
        print(f"✅ 工具系统创建成功，包含 {len(tool_system.tools)} 个工具")
        
        # 显示工具分类统计
        stats = tool_system.get_system_stats()
        print(f"📊 工具统计: {stats['tools_by_category']}")
        
        # 测试单个工具执行
        print("\n🔍 测试位置分析工具...")
        result = await tool_system.execute_tool(
            'analyze_position',
            {'board_fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 'depth': 3}
        )
        
        if result.success:
            print(f"✅ 分析成功: {result.result}")
        else:
            print(f"❌ 分析失败: {result.error_message}")
        
        # 测试工具链执行
        print("\n⛓️ 测试工具链执行...")
        tool_chain = [
            {'tool_name': 'analyze_position', 'parameters': {'board_fen': 'test_fen'}},
            {'tool_name': 'find_tactics', 'parameters': {'board_fen': 'test_fen'}},
            {'tool_name': 'explain_move', 'parameters': {'move': 'e2-e4', 'position': 'opening'}}
        ]
        
        chain_results = await tool_system.execute_tool_chain(tool_chain)
        print(f"📋 工具链执行完成，{len(chain_results)} 个步骤:")
        
        for i, result in enumerate(chain_results):
            status = "✅" if result.success else "❌"
            print(f"  {i+1}. {status} {result.tool_name} - {result.execution_time:.2f}s")
        
        # 测试上下文建议
        print("\n💡 测试工具建议...")
        context = {
            'needs_position_analysis': True,
            'needs_explanation': True,
            'game_phase': 'opening',
            'player_level': 'beginner'
        }
        
        suggestions = tool_system.suggest_tools_for_context(context)
        print(f"建议工具: {suggestions}")
        
        # 显示工具信息
        print("\n📋 工具详细信息:")
        for tool_name in suggestions[:3]:  # 显示前3个
            info = tool_system.get_tool_info(tool_name)
            if info:
                print(f"  🔧 {tool_name}: {info['description']}")
                print(f"     分类: {info['category']}, 优先级: {info['priority']}")
        
        # 清理
        tool_system.cleanup()
        print("\n🎉 工具系统测试完成!")
    
    # 运行测试
    asyncio.run(test_tool_system())