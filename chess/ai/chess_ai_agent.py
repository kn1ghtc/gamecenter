"""
超级智能国际象棋陪伴助理 v2.0 - 使用ChromaDB记忆系统
基于OpenAI Agents SDK和ChromaDB的专家级象棋AI助理

核心能力：
- Memory: ChromaDB/LanceDB持久记忆系统（RAG向量数据库）
- Planning: 自主规划执行
- Tools: 工具调用（MCP、网络搜索、下棋决策等）
- Execution: 实时执行反馈
- Voice: OpenAI语音陪伴聊天功能
"""
import asyncio
import json
import os
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# 首先导入OpenAI Agents SDK（在添加本地路径之前）
try:
    from agents import Agent, Runner, Tool
    from agents.models import get_default_model
    from agents.tracing import trace
    OPENAI_AGENTS_AVAILABLE = True
    print("✅ OpenAI Agents SDK 导入成功")
except ImportError as e:
    print(f"⚠️ OpenAI Agents SDK not available: {e}")
    OPENAI_AGENTS_AVAILABLE = False

# 本地导入
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.board import ChessBoard
from game.pieces import PieceColor, PieceType, ChessPiece
from ai.evaluation import ChessEvaluator
from ai.gpt_ai import GPTChessAI
from data.database import ChessDatabase

# 导入系统组件
from .memory_system import ChessMemorySystem, create_chess_memory_system
from .tool_system import ChessToolSystem, create_tool_system
from .voice_system import ChessVoiceSystem, VoiceSettings, VoiceProvider, EmotionType
from .planning_engine import ChessPlanningEngine, Task, TaskStatus

class AgentPersonality(Enum):
    """Agent个性类型"""
    FRIENDLY_MENTOR = "friendly_mentor"      # 友好导师
    COMPETITIVE_EXPERT = "competitive_expert" # 竞技专家
    PATIENT_TEACHER = "patient_teacher"      # 耐心教师
    CASUAL_FRIEND = "casual_friend"          # 休闲朋友

class InteractionMode(Enum):
    """交互模式"""
    GAME_ONLY = "game_only"          # 仅下棋
    CHAT_ONLY = "chat_only"          # 仅聊天
    COMPANION = "companion"          # 陪伴模式（游戏+聊天）
    TEACHING = "teaching"            # 教学模式
    ANALYSIS = "analysis"            # 分析模式

@dataclass
class AgentState:
    """Agent状态"""
    current_game_id: Optional[str] = None
    interaction_mode: InteractionMode = InteractionMode.COMPANION
    thinking_depth: int = 3
    confidence_level: float = 0.8
    last_move_time: Optional[datetime] = None
    conversation_context: List[str] = None
    current_emotion: EmotionType = EmotionType.FRIENDLY
    session_start_time: datetime = None
    
    def __post_init__(self):
        if self.conversation_context is None:
            self.conversation_context = []
        if self.session_start_time is None:
            self.session_start_time = datetime.now()

class ChessAIAgentV2:
    """Chess AI Agent v2.0 - 超级智能象棋陪伴助理"""
    
    def __init__(self,
                 name: str = "ChessCompanion",
                 personality: AgentPersonality = AgentPersonality.FRIENDLY_MENTOR,
                 api_key: str = None,
                 memory_dir: str = "chess_agent_memory",
                 voice_enabled: bool = True,
                 auto_planning: bool = True,
                 thinking_time: int = 3):
        """
        初始化Chess AI Agent v2.0
        
        Args:
            name: Agent名字
            personality: 个性类型
            api_key: OpenAI API密钥
            memory_dir: 记忆系统存储目录
            voice_enabled: 是否启用语音功能
            auto_planning: 是否启用自动规划
            thinking_time: 思考时间（秒）
        """
        self.name = name
        self.personality = personality
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.voice_enabled = voice_enabled
        self.auto_planning = auto_planning
        self.thinking_time = thinking_time
        
        # 初始化状态
        self.state = AgentState()
        
        # 日志设置
        self.logger = logging.getLogger(f"ChessAIAgentV2_{name}")
        self.logger.setLevel(logging.INFO)
        
        # 统计信息
        self.stats = {
            'games_played': 0,
            'moves_made': 0,
            'conversations': 0,
            'memory_interactions': 0,
            'tool_calls': 0,
            'planning_tasks': 0,
            'session_start': datetime.now()
        }
        
        # 初始化子系统
        self._init_systems(memory_dir)
        
        self.logger.info(f"Chess AI Agent v2.0 '{name}' 初始化完成")
    
    def _init_systems(self, memory_dir: str):
        """初始化各个子系统"""
        try:
            # 1. 记忆系统 - ChromaDB
            self.memory_system = create_chess_memory_system(
                memory_dir=memory_dir,
                embedding_model="openai" if self.api_key else "huggingface",
                fast_start=True,
                strict_vector=True
            )
            self.logger.info("✅ ChromaDB记忆系统已初始化")
            
            # 2. 工具系统 - MCP集成
            self.tool_system = create_tool_system(
                api_key=self.api_key
            )
            self.logger.info("✅ MCP工具系统已初始化")
            
            # 3. 语音系统 - OpenAI语音
            if self.voice_enabled:
                voice_settings = VoiceSettings(
                    provider=VoiceProvider.OPENAI if self.api_key else VoiceProvider.LOCAL,
                    emotion=EmotionType.FRIENDLY,
                    language="zh-CN"
                )
                
                # 使用配置中的语音缓存目录，避免C盘临时目录权限问题
                try:
                    from config.settings import PATHS
                    voice_cache_dir = PATHS['voice_cache']
                except ImportError:
                    # 回退到项目内部目录
                    import os
                    chess_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    voice_cache_dir = os.path.join(chess_dir, "test_data", "chess_voice_cache")
                    os.makedirs(voice_cache_dir, exist_ok=True)
                
                self.voice_system = ChessVoiceSystem(
                    api_key=self.api_key,
                    voice_settings=voice_settings,
                    audio_cache_dir=voice_cache_dir  # 显式传递缓存目录
                )
                self.logger.info("✅ 语音系统已初始化")
            else:
                self.voice_system = None
                self.logger.info("⚪ 语音系统已禁用")
            
            # 4. 规划引擎 - 自主任务规划
            if self.auto_planning:
                self.planning_engine = ChessPlanningEngine(
                    tool_system=self.tool_system,
                    memory_system=self.memory_system,
                    voice_system=self.voice_system
                )
                self.logger.info("✅ 规划引擎已初始化")
            else:
                self.planning_engine = None
                self.logger.info("⚪ 规划引擎已禁用")
            
            # 5. 传统AI组件
            self.evaluator = ChessEvaluator()
            self.gpt_ai = GPTChessAI(api_key=self.api_key) if self.api_key else None
            self.database = ChessDatabase()
            
        except Exception as e:
            self.logger.error(f"子系统初始化失败: {e}")
            raise
    
    async def get_best_move(self, 
                          board: ChessBoard, 
                          color: PieceColor,
                          time_limit: int = None) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        获取最佳移动（主要接口）
        
        Args:
            board: 棋盘状态
            color: 要移动的颜色
            time_limit: 时间限制（秒）
            
        Returns:
            最佳移动 (from_pos, to_pos) 或 None
        """
        start_time = time.time()
        self.stats['moves_made'] += 1
        
        try:
            # 记录游戏状态到记忆
            await self._record_game_state(board, color, "move_request")
            
            # 执行思考过程
            thinking_tasks = []
            
            # 1. 基础棋局分析
            if self.gpt_ai:
                thinking_tasks.append(self._analyze_position_with_ai(board, color))
            
            # 2. 记忆中寻找相似局面
            thinking_tasks.append(self._search_similar_positions(board))
            
            # 3. 工具辅助分析（仅在分析/教学模式启用，陪伴模式默认关闭以减少开销）
            if self.tool_system and self.state.interaction_mode in (
                InteractionMode.ANALYSIS, InteractionMode.TEACHING
            ):
                thinking_tasks.append(self._analyze_with_tools(board, color))
            
            # 并行执行思考任务
            results = await asyncio.gather(*thinking_tasks, return_exceptions=True)
            
            # 综合分析结果
            move = await self._synthesize_move_decision(board, color, results)
            
            # 记录移动决策过程
            decision_time = time.time() - start_time
            await self._record_move_decision(board, color, move, decision_time, results)
            
            # 语音反馈
            if self.voice_system and move:
                await self._provide_voice_feedback(move, board, decision_time)
            
            # 更新状态
            self.state.last_move_time = datetime.now()
            
            self.logger.info(f"移动决策完成: {move} (用时: {decision_time:.2f}s)")
            return move
            
        except Exception as e:
            self.logger.error(f"移动决策失败: {e}")
            return await self._fallback_move(board, color)
    
    async def _analyze_position_with_ai(self, board: ChessBoard, color: PieceColor) -> Dict[str, Any]:
        """使用AI分析局面"""
        try:
            if not self.gpt_ai:
                return {'error': 'AI不可用'}
            
            # 获取传统AI分析
            move = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.gpt_ai.get_best_move(board, color)
            )
            
            # 获取局面评估
            evaluation = self.evaluator.evaluate_position(board, color)
            
            return {
                'type': 'ai_analysis',
                'recommended_move': move,
                'position_score': evaluation,
                'analysis': f"AI推荐移动: {move}, 局面评分: {evaluation}"
            }
            
        except Exception as e:
            return {'type': 'ai_analysis', 'error': str(e)}
    
    async def _search_similar_positions(self, board: ChessBoard) -> Dict[str, Any]:
        """搜索记忆中的相似局面"""
        try:
            # 将棋盘状态转换为文本描述
            position_description = self._board_to_description(board)
            
            # 在记忆中搜索相似局面
            memories = self.memory_system.search_memories(
                query=position_description,
                memory_type="game",
                limit=3,
                similarity_threshold=0.75
            )
            
            similar_positions = []
            for memory in memories:
                similar_positions.append({
                    'content': memory.content,
                    'importance': memory.importance,
                    'context': memory.context
                })
            
            return {
                'type': 'memory_search',
                'similar_positions': similar_positions,
                'count': len(similar_positions)
            }
            
        except Exception as e:
            return {'type': 'memory_search', 'error': str(e)}
    
    async def _analyze_with_tools(self, board: ChessBoard, color: PieceColor) -> Dict[str, Any]:
        """使用工具进行分析"""
        try:
            if not self.tool_system:
                return {'error': '工具系统不可用'}
            
            # 使用象棋分析工具
            analysis_result = await self.tool_system.analyze_chess_position(
                board_state=self._board_to_fen(board),
                color=color.value
            )
            
            return {
                'type': 'tool_analysis',
                'analysis': analysis_result,
                'tool_used': 'chess_analyzer'
            }
            
        except Exception as e:
            return {'type': 'tool_analysis', 'error': str(e)}
    
    async def _synthesize_move_decision(self, 
                                      board: ChessBoard, 
                                      color: PieceColor, 
                                      analysis_results: List[Dict[str, Any]]) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """综合分析结果做出移动决策"""
        try:
            # 收集所有有效的移动建议
            move_candidates = []
            
            for result in analysis_results:
                if isinstance(result, dict) and 'recommended_move' in result:
                    move = result['recommended_move']
                    if move:
                        move_candidates.append(move)
            
            if not move_candidates:
                return await self._fallback_move(board, color)
            
            # 如果只有一个候选，直接返回
            if len(move_candidates) == 1:
                return move_candidates[0]
            
            # 多个候选时，使用评估函数选择最佳
            best_move = None
            best_score = float('-inf')
            
            for move in move_candidates:
                # 简单评估（实际实现中可以更复杂）
                score = self._evaluate_move(board, move, color)
                if score > best_score:
                    best_score = score
                    best_move = move
            
            return best_move
            
        except Exception as e:
            self.logger.error(f"移动决策综合失败: {e}")
            return await self._fallback_move(board, color)
    
    async def _fallback_move(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """备用移动策略"""
        try:
            # 获取所有合法移动（按玩家）
            legal_moves = board.get_legal_moves_for_player(color)
            if not legal_moves:
                return None
            
            # 简单启发式：优先吃子，其次占中心
            scored_moves = []
            for move in legal_moves:
                from_pos, to_pos = move
                score = 0
                
                # 吃子奖励
                target_piece = board.get_piece_at(to_pos)
                if target_piece and target_piece.color != color:
                    score += 10
                
                # 中心控制奖励
                if 2 <= to_pos[0] <= 5 and 2 <= to_pos[1] <= 5:
                    score += 5
                
                scored_moves.append((score, move))
            
            # 选择得分最高的移动
            scored_moves.sort(reverse=True)
            return scored_moves[0][1]
            
        except Exception as e:
            self.logger.error(f"备用移动策略失败: {e}")
            return None
    
    async def _record_game_state(self, board: ChessBoard, color: PieceColor, event_type: str):
        """记录游戏状态到记忆"""
        try:
            game_description = f"{event_type}: {self._board_to_description(board)}"
            
            self.memory_system.store_memory(
                content=game_description,
                memory_type="game",
                importance=0.6,
                context={
                    'color': color.value,
                    'event_type': event_type,
                    'game_id': self.state.current_game_id,
                    'fen': self._board_to_fen(board)
                }
            )
            
            self.stats['memory_interactions'] += 1
            
        except Exception as e:
            self.logger.error(f"记录游戏状态失败: {e}")
    
    async def _record_move_decision(self, 
                                  board: ChessBoard, 
                                  color: PieceColor, 
                                  move: Optional[Tuple[Tuple[int, int], Tuple[int, int]]],
                                  decision_time: float,
                                  analysis_results: List[Dict[str, Any]]):
        """记录移动决策过程"""
        try:
            decision_record = {
                'move': f"{move[0]} -> {move[1]}" if move else "无移动",
                'decision_time': decision_time,
                'analysis_count': len(analysis_results),
                'successful_analysis': len([r for r in analysis_results if isinstance(r, dict) and 'error' not in r])
            }
            
            self.memory_system.store_memory(
                content=f"移动决策: {json.dumps(decision_record, ensure_ascii=False)}",
                memory_type="strategy",
                importance=0.7,
                context={
                    'color': color.value,
                    'game_id': self.state.current_game_id,
                    'decision_data': decision_record
                }
            )
            
        except Exception as e:
            self.logger.error(f"记录移动决策失败: {e}")
    
    async def _provide_voice_feedback(self, 
                                    move: Tuple[Tuple[int, int], Tuple[int, int]], 
                                    board: ChessBoard, 
                                    decision_time: float):
        """提供语音反馈"""
        try:
            if not self.voice_system:
                return
            
            from_pos, to_pos = move
            piece = board.get_piece_at(from_pos)
            piece_name = piece.piece_type.value if piece else "棋子"
            feedback_text = f"我选择将{piece_name}从{self._pos_to_chess_notation(from_pos)}移动到{self._pos_to_chess_notation(to_pos)}。"

            # 给出简单理由
            reason_bits = []
            target_piece = board.get_piece_at(to_pos)
            if target_piece and (not piece or target_piece.color != piece.color):
                reason_bits.append(f"可以吃掉对方的{target_piece.piece_type.value}")
            center_squares = [(3,3), (3,4), (4,3), (4,4)]
            if to_pos in center_squares:
                reason_bits.append("加强对中心格的控制")
            if not reason_bits:
                reason_bits.append("优化我的棋子位置与协同")
            feedback_text += "原因是：" + "，".join(reason_bits)
            
            if decision_time > 3:
                feedback_text += f"。我思考了{decision_time:.1f}秒"
            
            await self.voice_system.speak_async(feedback_text, EmotionType.THINKING)
            
        except Exception as e:
            self.logger.error(f"语音反馈失败: {e}")
    
    async def chat(self, message: str, current_board: ChessBoard = None) -> str:
        """与Agent聊天 - 自动上下文感知版本"""
        try:
            self.stats['conversations'] += 1
            
            # 自动获取当前游戏状态上下文
            game_context = await self._gather_game_context(current_board)
            
            # 记录用户消息到记忆，包含游戏上下文
            self.memory_system.store_memory(
                content=f"用户说: {message}",
                memory_type="conversation",
                importance=0.5,
                context={
                    'speaker': 'user', 
                    'timestamp': datetime.now().isoformat(),
                    'game_context': game_context
                }
            )
            
            # 搜索相关记忆
            relevant_memories = self.memory_system.search_memories(
                query=message,
                limit=3,
                min_importance=0.3
            )
            
            # 生成回复，包含游戏上下文
            if self.gpt_ai:
                response = await self._generate_ai_response(message, relevant_memories, game_context)
            else:
                response = self._generate_fallback_response(message, relevant_memories, game_context)
            
            # 记录回复到记忆
            self.memory_system.store_memory(
                content=f"我回复: {response}",
                memory_type="conversation",
                importance=0.6,
                context={
                    'speaker': 'agent', 
                    'timestamp': datetime.now().isoformat(),
                    'game_context': game_context
                }
            )
            
            # 语音回复
            if self.voice_system:
                await self.voice_system.speak_async(response, self.state.current_emotion)
            
            self.logger.info(f"上下文感知对话回复: {response[:50]}... (游戏状态已自动获取)")
            return response
            
        except Exception as e:
            self.logger.error(f"聊天处理失败: {e}")
            return "抱歉，我现在无法正常回应。让我们继续下棋吧！"
    
    def chat_sync(self, message: str, current_board: ChessBoard = None) -> str:
        """同步chat方法，兼容旧代码"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已有事件循环在运行，创建新循环
                import threading
                result = None
                exception = None
                
                def run_chat():
                    nonlocal result, exception
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(self.chat(message, current_board))
                        new_loop.close()
                    except Exception as e:
                        exception = e
                
                thread = threading.Thread(target=run_chat)
                thread.start()
                thread.join(timeout=10)  # 最多等待10秒
                
                if exception:
                    raise exception
                return result or "对话超时，请重试。"
            else:
                # 直接在当前循环运行
                return loop.run_until_complete(self.chat(message, current_board))
        except Exception as e:
            self.logger.error(f"同步聊天调用失败: {e}")
            return "抱歉，我现在无法正常回应。让我们继续下棋吧！"
    
    async def _gather_game_context(self, current_board: ChessBoard = None) -> Dict[str, Any]:
        """自动收集游戏上下文信息"""
        try:
            context = {
                'timestamp': datetime.now().isoformat(),
                'has_board': current_board is not None
            }
            
            if current_board:
                # 棋盘基本状态
                context.update({
                    'current_player': str(current_board.current_player),
                    'move_count': len(current_board.move_history),
                    'is_in_check': current_board.is_in_check(current_board.current_player),
                    'pieces_count': len(current_board.pieces),
                })
                
                # 最近的移动历史
                if current_board.move_history:
                    recent_moves = []
                    for move in current_board.move_history[-3:]:  # 最近3步
                        move_desc = f"{move['from']}->{move['to']}"
                        if 'piece' in move:
                            move_desc = f"{move['piece']} {move_desc}"
                        if 'captured' in move and move['captured']:
                            move_desc += f" (吃掉{move['captured']})"
                        recent_moves.append(move_desc)
                    context['recent_moves'] = recent_moves
                    context['last_move'] = recent_moves[-1] if recent_moves else None
                
                # 棋局阶段判断
                piece_count = len(current_board.pieces)
                if piece_count > 20:
                    context['game_phase'] = 'opening'  # 开局
                elif piece_count > 10:
                    context['game_phase'] = 'middlegame'  # 中局
                else:
                    context['game_phase'] = 'endgame'  # 残局
                
                # 棋盘位置描述
                context['position_description'] = self._board_to_description(current_board)
                
            # 从记忆系统搜索相关的游戏状态
            if current_board:
                position_memories = self.memory_system.search_memories(
                    query=context.get('position_description', ''),
                    limit=2,
                    memory_type='position'
                )
                if position_memories:
                    context['similar_positions'] = [m.content for m in position_memories]
            
            # 获取对话历史
            conversation_memories = self.memory_system.search_memories(
                query="用户说",
                limit=2,
                memory_type='conversation'
            )
            if conversation_memories:
                context['recent_conversations'] = [m.content for m in conversation_memories]
                
            self.logger.debug(f"收集到游戏上下文: {len(context)} 项信息")
            return context
            
        except Exception as e:
            self.logger.error(f"收集游戏上下文失败: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def _generate_ai_response(self, message: str, memories: List, game_context: Dict = None) -> str:
        """使用AI生成回复 - 增强上下文版本"""
        # 构建更丰富的上下文提示
        memory_context = "\n".join([f"- {m.content}" for m in memories[:2]])
        
        # 构建游戏状态描述
        game_status = ""
        if game_context and game_context.get('has_board'):
            game_status = f"""
            当前游戏状态:
            - 当前轮到: {game_context.get('current_player', '未知')}
            - 移动次数: {game_context.get('move_count', 0)}
            - 游戏阶段: {game_context.get('game_phase', '未知')}
            - 是否被将军: {'是' if game_context.get('is_in_check') else '否'}
            """
            
            if game_context.get('recent_moves'):
                recent_moves_str = " -> ".join(game_context['recent_moves'])
                game_status += f"\n- 最近走法: {recent_moves_str}"
                
            if game_context.get('position_description'):
                game_status += f"\n- 局面描述: {game_context['position_description'][:100]}..."
        
        context_prompt = f"""
        你是一个友好的象棋AI助理，名字是{self.name}。你能看到当前的棋盘状态和游戏历史。
        用户说: {message}
        {game_status}
        
        相关记忆:
        {memory_context}
        
        请基于当前游戏状态用友好、专业的语气回复用户。如果用户询问棋局，要结合实际棋盘状态回答。
        回复要简洁明了，不超过100个字。
        """
        
        try:
            # 实际调用GPT API
            if not self.gpt_ai or not self.api_key:
                return self._generate_fallback_response(message, memories, game_context)

            # 使用openai官方库
            import openai
            openai.api_key = self.api_key
            messages = [
                {"role": "system", "content": "你是一个智能的象棋AI陪伴助理，能够感知当前棋局状态，提供专业建议。"},
                {"role": "user", "content": context_prompt.strip()}
            ]

            resp = openai.chat.completions.create(
                model=self.gpt_ai.model if hasattr(self.gpt_ai, 'model') and self.gpt_ai.model else "gpt-4o-mini",
                messages=messages,
                max_tokens=200,
                temperature=0.6
            )
            answer = resp.choices[0].message.content.strip()
            return answer or self._generate_fallback_response(message, memories, game_context)
        except Exception as e:
            self.logger.warning(f"GPT API调用失败: {e}")
            return self._generate_fallback_response(message, memories, game_context)
    
    def _generate_fallback_response(self, message: str, memories: List, game_context: Dict = None) -> str:
        """备用回复生成 - 支持游戏上下文"""
        message_lower = message.lower()
        
        # 如果有游戏上下文，优先回应游戏相关问题
        if game_context and game_context.get('has_board'):
            if any(word in message_lower for word in ['局面', '分析', '怎么走', '建议', '走法']):
                phase = game_context.get('game_phase', '中局')
                current_player = game_context.get('current_player', '未知')
                
                if game_context.get('is_in_check'):
                    return f"注意！{current_player}方正被将军，需要优先应将！"
                elif phase == 'opening':
                    return "现在是开局阶段，建议先发展子力，控制中心。"
                elif phase == 'endgame':
                    return "已进入残局，要注意王的活跃性和兵的推进。"
                else:
                    return "中局阶段要注重子力协调和战术机会。"
            
            elif any(word in message_lower for word in ['上一步', '刚才', '最后']):
                last_move = game_context.get('last_move')
                if last_move:
                    return f"刚才的走法是: {last_move}。这步棋{['不错', '很好', '有趣', '合理'][hash(last_move) % 4]}！"
                else:
                    return "这是游戏开始，还没有走过棋。"
        
        # 通用回复
        if any(word in message_lower for word in ['帮助', 'help', '怎么']):
            return "我可以分析当前棋局、给出走棋建议，或者和你聊天。有什么想了解的吗？"
        elif any(word in message_lower for word in ['谢谢', '感谢', 'thank']):
            return "不客气！我很高兴能帮助你。让我们继续下棋吧！"
        elif any(word in message_lower for word in ['再见', 'bye', '结束']):
            return "再见！期待下次和你一起下棋。记得多练习哦！"
        else:
            return "我明白了。我会根据当前棋局为你提供最好的建议！"
    
    # 工具方法
    def _board_to_description(self, board: ChessBoard) -> str:
        """将棋盘转换为文本描述"""
        # 简化版本，实际实现可以更详细
        pieces_count = {'white': 0, 'black': 0}
        for row in range(8):
            for col in range(8):
                piece = board.get_piece_at((row, col))
                if piece:
                    pieces_count[piece.color.value] += 1
        
        return f"棋盘状态: 白方{pieces_count['white']}子，黑方{pieces_count['black']}子"
    
    def _board_to_fen(self, board: ChessBoard) -> str:
        """将棋盘转换为FEN格式（简化版）"""
        # 实际实现需要完整的FEN生成逻辑
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    def _pos_to_chess_notation(self, pos: Tuple[int, int]) -> str:
        """将位置转换为象棋记号"""
        row, col = pos
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        return f"{files[col]}{8-row}"
    
    def _evaluate_move(self, board: ChessBoard, move: Tuple[Tuple[int, int], Tuple[int, int]], color: PieceColor) -> float:
        """评估移动的价值"""
        from_pos, to_pos = move
        score = 0.0
        
        # 基本评估逻辑
        target_piece = board.get_piece_at(to_pos)
        if target_piece and target_piece.color != color:
            # 吃子奖励
            piece_values = {
                PieceType.PAWN: 1,
                PieceType.KNIGHT: 3,
                PieceType.BISHOP: 3,
                PieceType.ROOK: 5,
                PieceType.QUEEN: 9,
                PieceType.KING: 100
            }
            score += piece_values.get(target_piece.piece_type, 0)
        
        # 位置价值
        center_squares = [(3,3), (3,4), (4,3), (4,4)]
        if to_pos in center_squares:
            score += 0.5
        
        return score
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        uptime = datetime.now() - self.stats['session_start']
        
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'current_state': {
                'interaction_mode': self.state.interaction_mode.value,
                'current_emotion': self.state.current_emotion.value,
                'thinking_depth': self.state.thinking_depth,
                'confidence_level': self.state.confidence_level
            },
            'systems_status': {
                'memory_available': self.memory_system is not None,
                'voice_available': self.voice_system is not None,
                'tools_available': self.tool_system is not None,
                'planning_available': self.planning_engine is not None,
                'ai_available': self.gpt_ai is not None
            }
        }
    
    def set_personality(self, personality: AgentPersonality):
        """设置Agent个性"""
        self.personality = personality
        
        # 更新情感状态
        emotion_mapping = {
            AgentPersonality.FRIENDLY_MENTOR: EmotionType.ENCOURAGING,
            AgentPersonality.COMPETITIVE_EXPERT: EmotionType.SERIOUS,
            AgentPersonality.PATIENT_TEACHER: EmotionType.FRIENDLY,
            AgentPersonality.CASUAL_FRIEND: EmotionType.NEUTRAL
        }
        
        self.state.current_emotion = emotion_mapping.get(personality, EmotionType.FRIENDLY)
        self.logger.info(f"个性已更新为: {personality.value}")
    
    def start_new_game(self, game_id: str = None):
        """开始新游戏"""
        self.state.current_game_id = game_id or f"game_{int(time.time())}"
        self.stats['games_played'] += 1
        self.logger.info(f"开始新游戏: {self.state.current_game_id}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.voice_system:
                self.voice_system.cleanup()
            
            if self.planning_engine:
                # planning_engine的cleanup是同步的
                self.planning_engine.cleanup()
            
            if self.memory_system:
                # 如果memory_system有清理方法也调用
                if hasattr(self.memory_system, 'cleanup'):
                    self.memory_system.cleanup()
            
            self.logger.info("Agent资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")
    
    def sync_cleanup(self):
        """同步清理方法，供非异步环境使用"""
        try:
            if self.voice_system and hasattr(self.voice_system, 'cleanup'):
                self.voice_system.cleanup()
            
            if self.planning_engine and hasattr(self.planning_engine, 'cleanup'):
                self.planning_engine.cleanup()
            
            if self.memory_system and hasattr(self.memory_system, 'cleanup'):
                self.memory_system.cleanup()
            
            self.logger.info("Agent资源同步清理完成")
            
        except Exception as e:
            self.logger.error(f"同步资源清理失败: {e}")

# 工厂函数
def create_chess_ai_agent_v2(
    name: str = "ChessCompanion",
    personality: AgentPersonality = AgentPersonality.FRIENDLY_MENTOR,
    api_key: str = None,
    memory_dir: str = "chess_agent_memory",
    voice_enabled: bool = True
) -> ChessAIAgentV2:
    """创建Chess AI Agent v2.0实例"""
    return ChessAIAgentV2(
        name=name,
        personality=personality,
        api_key=api_key,
        memory_dir=memory_dir,
        voice_enabled=voice_enabled
    )

# 测试和演示
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        print("🧪 测试Chess AI Agent v2.0...")
        
        # 创建Agent
        agent = create_chess_ai_agent_v2(
            name="测试陪伴者",
            personality=AgentPersonality.FRIENDLY_MENTOR,
            voice_enabled=False  # 测试时禁用语音
        )
        
        print("✅ Agent创建成功")
        
        # 测试聊天功能
        response = await agent.chat("你好，我想学习象棋")
        print(f"💬 聊天回复: {response}")
        
        # 测试记忆搜索
        memories = agent.memory_system.search_memories("象棋", limit=2)
        print(f"🧠 记忆搜索: 找到{len(memories)}条相关记忆")
        
        # 获取统计信息
        stats = agent.get_agent_stats()
        print(f"📊 统计信息:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}: {dict(value)}")
            else:
                print(f"  {key}: {value}")
        
        await agent.cleanup()
        print("🎉 Agent测试完成!")
    
    # 运行测试
    asyncio.run(test_agent())