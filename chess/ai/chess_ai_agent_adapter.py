"""
Chess AI Agent v2.0 游戏接口适配器
使用ChromaDB记忆系统的新版本适配器

主要功能：
- 提供标准的get_best_move接口
- 使用ChromaDB记忆系统
- OpenAI语音支持
- 完整的陪伴模式功能
"""

import asyncio
import time
import logging
from typing import Optional, Tuple, Any, Dict

# 导入现有系统组件
from game.board import ChessBoard
from game.pieces import PieceColor, ChessPiece

# 导入AI Agent
try:
    from ai.chess_ai_agent import ChessAIAgentV2, AgentPersonality, InteractionMode, create_chess_ai_agent_v2
    AI_AGENT_V2_AVAILABLE = True
    print("✅ Chess AI Agent v2.0 可用")
except ImportError as e:
    print(f"⚠️ Chess AI Agent v2.0 不可用: {e}")
    AI_AGENT_V2_AVAILABLE = False

class ChessAIAgentAdapter:
    """Chess AI Agent 适配器 - 连接新Agent与游戏系统"""
    
    def __init__(self,
                 difficulty: str = "companion",
                 personality: str = "friendly_mentor",
                 voice_enabled: bool = True,
                 api_key: str = None):
        """
        初始化适配器
        
        Args:
            difficulty: 难度级别 ("companion" 为陪伴模式)
            personality: 个性类型
            voice_enabled: 是否启用语音
            api_key: OpenAI API密钥
        """
        self.difficulty = difficulty
        self.voice_enabled = voice_enabled
        self.api_key = api_key
        
        # 日志设置
        self.logger = logging.getLogger("ChessAIAgentAdapter")
        self.logger.setLevel(logging.INFO)
        
        # 映射个性类型
        personality_mapping = {
            "friendly_mentor": AgentPersonality.FRIENDLY_MENTOR,
            "competitive_expert": AgentPersonality.COMPETITIVE_EXPERT,
            "patient_teacher": AgentPersonality.PATIENT_TEACHER,
            "casual_friend": AgentPersonality.CASUAL_FRIEND
        }
        
        self.personality_enum = personality_mapping.get(
            personality, 
            AgentPersonality.FRIENDLY_MENTOR
        )
        
        # 初始化Agent
        self.agent = None
        self._init_agent()
        
        # 运行时状态
        self.current_game_id = None
        self.move_count = 0
        self.last_interaction_time = time.time()
        
        self.logger.info(f"Chess AI Agent适配器初始化完成 (难度: {difficulty})")
    
    def _init_agent(self):
        """初始化AI Agent"""
        try:
            if not AI_AGENT_V2_AVAILABLE:
                self.logger.warning("AI Agent v2.0 不可用，使用备用模式")
                return
            
            # 创建Agent实例
            self.agent = create_chess_ai_agent_v2(
                name=f"ChessCompanion_{self.difficulty}",
                personality=self.personality_enum,
                api_key=self.api_key,
                memory_dir=f"chess_memory_{self.difficulty}",
                voice_enabled=self.voice_enabled
            )
            
            self.logger.info("✅ AI Agent v2.0 初始化成功")
            
        except Exception as e:
            self.logger.error(f"AI Agent初始化失败: {e}")
            self.agent = None
    
    def get_best_move(self, board: ChessBoard, color: PieceColor, time_limit: int = 5) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        获取最佳移动（同步接口，兼容现有系统）
        
        Args:
            board: 棋盘状态
            color: 要移动的颜色
            time_limit: 时间限制
            
        Returns:
            最佳移动或None
        """
        try:
            if not self.agent:
                return self._fallback_move(board, color)
            
            # 异步转同步执行
            loop = None
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已有运行的事件循环，创建新的线程执行
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._async_get_move, board, color, time_limit)
                        return future.result(timeout=time_limit + 2)
                else:
                    return loop.run_until_complete(self._async_get_move(board, color, time_limit))
            except RuntimeError:
                # 没有事件循环，创建新的
                return asyncio.run(self._async_get_move(board, color, time_limit))
            
        except Exception as e:
            self.logger.error(f"获取移动失败: {e}")
            return self._fallback_move(board, color)
    
    async def _async_get_move(self, board: ChessBoard, color: PieceColor, time_limit: int) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """异步获取移动"""
        try:
            self.move_count += 1
            self.last_interaction_time = time.time()
            
            # 如果是新游戏，初始化游戏ID
            if self.current_game_id is None:
                self.current_game_id = f"game_{int(time.time())}"
                self.agent.start_new_game(self.current_game_id)
            
            # 调用Agent获取移动
            move = await self.agent.get_best_move(board, color, time_limit)
            
            if move:
                self.logger.info(f"Agent返回移动: {move}")
            else:
                self.logger.warning("Agent未返回有效移动，使用备用策略")
                move = self._fallback_move(board, color)
            
            return move
            
        except asyncio.TimeoutError:
            self.logger.warning(f"移动计算超时 ({time_limit}s)")
            return self._fallback_move(board, color)
        except Exception as e:
            self.logger.error(f"异步移动计算失败: {e}")
            return self._fallback_move(board, color)
    
    def _fallback_move(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """备用移动策略"""
        try:
            legal_moves = board.get_legal_moves_for_player(color)
            if not legal_moves:
                return None
            
            # 简单启发式选择
            best_move = None
            best_score = -1000
            
            for move in legal_moves:
                from_pos, to_pos = move
                score = 0
                
                # 吃子优先
                target_piece = board.get_piece_at(to_pos)
                if target_piece and target_piece.color != color:
                    piece_values = {
                        'pawn': 1, 'knight': 3, 'bishop': 3, 
                        'rook': 5, 'queen': 9, 'king': 100
                    }
                    score += piece_values.get(target_piece.piece_type.value, 0) * 10
                
                # 中心控制
                center_distance = abs(3.5 - to_pos[0]) + abs(3.5 - to_pos[1])
                score += (7 - center_distance) * 2
                
                # 随机因子
                import random
                score += random.random() * 5
                
                if score > best_score:
                    best_score = score
                    best_move = move
            
            self.logger.info(f"备用策略选择移动: {best_move} (得分: {best_score})")
            return best_move
            
        except Exception as e:
            self.logger.error(f"备用移动策略失败: {e}")
            return None
    
    def process_user_message(self, message: str) -> str:
        """处理用户消息（聊天功能）"""
        try:
            if not self.agent:
                return "抱歉，陪伴功能暂时不可用。让我们专注于下棋吧！"
            
            # 异步转同步
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._async_chat, message)
                        return future.result(timeout=10)
                else:
                    return loop.run_until_complete(self._async_chat(message))
            except RuntimeError:
                return asyncio.run(self._async_chat(message))
                
        except Exception as e:
            self.logger.error(f"处理用户消息失败: {e}")
            return "我现在有点困惑，让我们继续下棋吧！"
    
    async def _async_chat(self, message: str) -> str:
        """异步聊天"""
        try:
            response = await self.agent.chat(message)
            return response
        except Exception as e:
            self.logger.error(f"异步聊天失败: {e}")
            return "抱歉，我现在无法正常聊天。"
    
    def get_companion_greeting(self) -> str:
        """获取陪伴模式问候语"""
        greetings = [
            "你好！我是你的象棋陪伴助理。准备开始一场有趣的对弈吗？",
            "欢迎！我会陪你下棋，还可以聊天哦。有什么想问的吗？",
            "很高兴见到你！让我们一起享受象棋的乐趣吧！",
            "嗨！我是专业的象棋AI助理，也是你的好朋友。开始游戏吧！"
        ]
        
        import random
        return random.choice(greetings)

    # 供UI调用的事件处理（避免"不支持语音/问答"提示）
    def handle_player_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        try:
            # 直接记录到记忆系统，避免依赖颜色/棋盘上下文
            if self.agent and hasattr(self.agent, "memory_system") and self.agent.memory_system:
                move_text = f"玩家移动: {from_pos} -> {to_pos}"
                try:
                    self.agent.memory_system.store_memory(
                        content=move_text,
                        memory_type="game",
                        importance=0.5,
                        context={"event": "player_move"}
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def handle_player_question(self, question: str) -> str:
        try:
            if not self.agent:
                return "抱歉，陪伴功能暂不可用。"
            # 同步调用聊天接口
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(lambda: asyncio.run(self.agent.chat(question)))
                        return future.result(timeout=10)
                else:
                    return loop.run_until_complete(self.agent.chat(question))
            except RuntimeError:
                return asyncio.run(self.agent.chat(question))
        except Exception:
            return "我正在思考中，我们继续下棋吧。"

    # 语音聊天流程：播报提示 -> 监听一次 -> 将识别文本发给agent -> 播报AI回复
    def start_voice_chat_interaction(self) -> str:
        try:
            if not self.agent or not getattr(self.agent, 'voice_system', None):
                return "语音系统不可用，请检查麦克风或API配置。"
            vs = self.agent.voice_system

            # 播报开始提示
            vs.speak("语音聊天开始。请在提示音后说话，三秒内结束。", blocking=True)

            # 监听一次（尽量短，避免卡顿）
            result = vs.listen(timeout=4.0, phrase_timeout=2.0)
            user_text = (result.text if result else "") if result else ""
            if not user_text.strip():
                vs.speak("没有听清楚，请再试一次。", blocking=True)
                return "未识别到有效语音。"

            # 调用聊天
            reply = self.process_user_message(user_text)

            # 播报回复
            vs.speak(reply, blocking=False)
            return reply
        except Exception as e:
            self.logger.error(f"语音聊天交互失败: {e}")
            return "语音聊天出错，请稍后重试。"
    
    def get_move_explanation(self, move: Tuple[Tuple[int, int], Tuple[int, int]], board: ChessBoard) -> str:
        """获取移动解释"""
        if not move:
            return "我找不到合适的移动。"
        
        from_pos, to_pos = move
        from_notation = self._pos_to_notation(from_pos)
        to_notation = self._pos_to_notation(to_pos)
        
        # 基本移动描述
        explanation = f"我将棋子从{from_notation}移动到{to_notation}"
        
        # 检查是否吃子
        target_piece = board.get_piece_at(to_pos)
        if target_piece:
            explanation += f"，吃掉你的{target_piece.piece_type.value}"
        
        # 添加策略说明
        strategies = [
            "这样可以更好地控制中心",
            "这是一个不错的进攻位置", 
            "这样可以保护我的重要棋子",
            "这个移动有助于我的整体布局"
        ]
        
        import random
        explanation += f"。{random.choice(strategies)}。"
        
        return explanation
    
    def _pos_to_notation(self, pos: Tuple[int, int]) -> str:
        """位置转换为代数记号"""
        row, col = pos
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
        return f"{files[col]}{ranks[row]}"
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        base_stats = {
            'difficulty': self.difficulty,
            'personality': self.personality_enum.value if hasattr(self.personality_enum, 'value') else str(self.personality_enum),
            'voice_enabled': self.voice_enabled,
            'current_game_id': self.current_game_id,
            'move_count': self.move_count,
            'last_interaction': self.last_interaction_time,
            'agent_available': self.agent is not None
        }
        
        # 如果Agent可用，获取详细统计
        if self.agent:
            try:
                agent_stats = self.agent.get_agent_stats()
                base_stats.update(agent_stats)
            except Exception as e:
                self.logger.error(f"获取Agent统计失败: {e}")
        
        return base_stats
    
    def start_new_game(self):
        """开始新游戏"""
        self.current_game_id = None
        self.move_count = 0
        self.last_interaction_time = time.time()
        self.logger.info("开始新游戏")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.agent:
                # 如果Agent有cleanup方法，调用它
                if hasattr(self.agent, 'cleanup'):
                    # 异步转同步
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(self._async_cleanup)
                                future.result(timeout=5)
                        else:
                            loop.run_until_complete(self._async_cleanup())
                    except RuntimeError:
                        asyncio.run(self._async_cleanup())
            
            self.logger.info("适配器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")
    
    async def _async_cleanup(self):
        """异步清理"""
        try:
            await self.agent.cleanup()
        except Exception as e:
            self.logger.error(f"Agent清理失败: {e}")

# 兼容性函数，供现有游戏系统调用
def create_companion_ai(api_key: str = None, voice_enabled: bool = True) -> ChessAIAgentAdapter:
    """创建陪伴模式AI"""
    return ChessAIAgentAdapter(
        difficulty="companion",
        personality="friendly_mentor",
        voice_enabled=voice_enabled,
        api_key=api_key
    )

def create_teaching_ai(api_key: str = None, voice_enabled: bool = True) -> ChessAIAgentAdapter:
    """创建教学模式AI"""
    return ChessAIAgentAdapter(
        difficulty="teaching",
        personality="patient_teacher",
        voice_enabled=voice_enabled,
        api_key=api_key
    )

def create_competitive_ai(api_key: str = None, voice_enabled: bool = False) -> ChessAIAgentAdapter:
    """创建竞技模式AI"""
    return ChessAIAgentAdapter(
        difficulty="expert",
        personality="competitive_expert",
        voice_enabled=voice_enabled,
        api_key=api_key
    )

# 测试代码
if __name__ == "__main__":
    print("🧪 测试Chess AI Agent适配器...")
    
    # 创建适配器
    adapter = create_companion_ai(voice_enabled=False)  # 测试时禁用语音
    print("✅ 适配器创建成功")
    
    # 测试聊天
    response = adapter.process_user_message("你好！")
    print(f"💬 聊天测试: {response}")
    
    # 获取问候语
    greeting = adapter.get_companion_greeting()
    print(f"👋 问候语: {greeting}")
    
    # 获取统计信息
    stats = adapter.get_agent_stats()
    print(f"📊 统计信息:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}: {dict(value)}")
        else:
            print(f"  {key}: {value}")
    
    # 清理
    adapter.cleanup()
    print("🎉 适配器测试完成!")