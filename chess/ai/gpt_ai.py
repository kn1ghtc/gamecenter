"""
GPT-4o-mini专家级AI
使用OpenAI API的智能象棋代理
"""
import openai
import json
import sys
import os
from typing import List, Tuple, Optional, Dict
import time
import random

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.board import ChessBoard
from game.pieces import PieceColor, PieceType
from ai.evaluation import ChessEvaluator

class GPTChessAI:
    """GPT-4o-mini专家级国际象棋AI"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        初始化GPT象棋AI
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
        """
        # 获取API密钥
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("⚠️ 未找到OpenAI API密钥，GPT AI将使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False
            openai.api_key = self.api_key
        
        self.model = model
        self.evaluator = ChessEvaluator()
        
        # 对话历史（保持上下文）
        self.conversation_history = []
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'average_response_time': 0.0
        }
        
        # 初始化系统提示词
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """创建系统提示词"""
        return """你是专家级国际象棋AI，具备深度战术分析和战略规划能力。

响应格式：
```json
{
    "analysis": "位置分析",
    "best_move": {
        "from": [x, y],
        "to": [x, y],
        "reasoning": "移动理由"
    },
    "evaluation": "位置评估",
    "confidence": "高/中/低"
}
```

重要：
- 坐标为[x, y]格式，x和y都是0-7的整数
- 只选择提供的合法移动
- 响应必须是有效JSON格式，不要添加markdown标记
- 优先考虑战术机会和位置改善"""
    
    def get_best_move(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """获取最佳移动"""
        if self.mock_mode:
            return self._get_mock_move(board, color)
        
        try:
            # 获取棋盘状态和合法移动
            board_state = self._analyze_board_state(board, color)
            legal_moves = self._get_legal_moves_list(board, color)
            
            if not legal_moves:
                return None
            
            # 构建提示词
            prompt = self._create_move_prompt(board_state, legal_moves, color)
            
            # 调用GPT API
            start_time = time.time()
            response = self._call_gpt_api(prompt)
            response_time = time.time() - start_time
            
            # 更新统计
            self._update_stats(response_time, success=True)
            
            # 解析响应
            move = self._parse_gpt_response(response, legal_moves)
            
            if move:
                return move
            else:
                # 尝试备用解析方法
                backup_move = self._parse_fallback_formats(response, legal_moves)
                if backup_move:
                    return backup_move
                else:
                    # 尝试智能解析
                    smart_move = self._parse_smart_fallback(response, legal_moves)
                    if smart_move:
                        return smart_move
                    else:
                        # 使用备用移动
                        return self._get_fallback_move(board, color, legal_moves)
                
        except Exception as e:
            print(f"❌ GPT AI出错: {e}")
            self._update_stats(0, success=False)
            return self._get_fallback_move(board, color, legal_moves)
    
    def _analyze_board_state(self, board: ChessBoard, color: PieceColor) -> Dict:
        """分析棋盘状态"""
        analysis = {
            'current_player': 'white' if color == PieceColor.WHITE else 'black',
            'position_evaluation': self.evaluator.evaluate_position(board),
            'material_balance': self._calculate_material_balance(board),
            'king_safety': self._analyze_king_safety(board, color),
            'piece_activity': self._analyze_piece_activity(board, color),
            'pawn_structure': self._analyze_pawn_structure(board),
            'tactical_threats': self._find_tactical_threats(board, color),
            'game_phase': self._determine_game_phase(board),
            'castling_rights': self._get_castling_status(board),
            'special_situations': self._check_special_situations(board)
        }
        
        return analysis
    
    def _get_legal_moves_list(self, board: ChessBoard, color: PieceColor) -> List[Dict]:
        """获取格式化的合法移动列表"""
        legal_moves = []
        
        for position, piece in board.pieces.items():
            if piece.color == color:
                moves = board.get_legal_moves(position)
                for to_pos in moves:
                    move_info = {
                        'from': list(position),
                        'to': list(to_pos),
                        'piece': piece.piece_type.name.lower(),
                        'capture': to_pos in board.pieces,
                        'notation': self._to_chess_notation(position, to_pos)
                    }
                    legal_moves.append(move_info)
        
        return legal_moves
    
    def _create_move_prompt(self, board_state: Dict, legal_moves: List[Dict], color: PieceColor) -> str:
        """创建移动选择提示词"""
        color_str = 'white' if color == PieceColor.WHITE else 'black'
        
        prompt = f"""当前轮到{color_str}行棋。

棋盘状态：
- 材质平衡: {board_state['material_balance']['status']}
- 游戏阶段: {board_state['game_phase']}
- 特殊情况: {board_state['special_situations']}

合法移动 (共{len(legal_moves)}个):
"""
        
        # 显示合法移动
        for i, move in enumerate(legal_moves[:20]):
            capture = " (吃子)" if move['capture'] else ""
            prompt += f"{i+1}. [{move['from'][0]}, {move['from'][1]}] -> [{move['to'][0]}, {move['to'][1]}] {move['piece']}{capture}\n"
        
        if len(legal_moves) > 20:
            prompt += f"... 还有{len(legal_moves) - 20}个移动\n"
        
        prompt += "\n请分析并选择最佳移动。只返回JSON格式响应。"
        
        return prompt
    
    def _call_gpt_api(self, prompt: str) -> str:
        """调用GPT API"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 添加对话历史（最近3轮）
        if self.conversation_history:
            recent_history = self.conversation_history[-6:]  # 最近3轮对话
            for msg in recent_history:
                messages.insert(-1, msg)
        
        response = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=500,
            temperature=0.3,  # 低温度保证一致性
            top_p=0.9,
            frequency_penalty=0.1
        )
        
        response_text = response.choices[0].message.content
        
        # 更新对话历史
        self.conversation_history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response_text}
        ])
        
        # 限制历史长度
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return response_text
    
    def _clean_json_response(self, response: str) -> str:
        """清理GPT响应，提取JSON部分"""
        try:
            # 移除markdown代码块标记
            response = response.replace('```json', '').replace('```', '').strip()
            
            # 提取JSON部分
            if not response.startswith('{'):
                first_brace = response.find('{')
                if first_brace != -1:
                    response = response[first_brace:]
            
            if not response.endswith('}'):
                last_brace = response.rfind('}')
                if last_brace != -1:
                    response = response[:last_brace+1]
            
            return response
        except Exception:
            return response
    
    def _parse_gpt_response(self, response: str, legal_moves: List[Dict]) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """解析GPT响应"""
        try:
            # 清理响应
            clean_response = self._clean_json_response(response)
            
            # 尝试直接解析清理后的JSON
            try:
                data = json.loads(clean_response)
                return self._extract_move_from_json(data, legal_moves)
            except json.JSONDecodeError:
                pass
            
            # 如果直接解析失败，尝试分块解析
            json_candidates = self._extract_json_blocks(response)
            
            for json_str in json_candidates:
                try:
                    data = json.loads(json_str)
                    move = self._extract_move_from_json(data, legal_moves)
                    if move:
                        return move
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ GPT响应解析异常: {e}")
            return None

    def _extract_json_blocks(self, response: str) -> List[str]:
        """提取响应中的JSON块"""
        json_candidates = []
        brace_count = 0
        start_pos = -1
        
        for i, char in enumerate(response):
            if char == '{':
                if brace_count == 0:
                    start_pos = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_pos != -1:
                    json_str = response[start_pos:i+1]
                    json_candidates.append(json_str)
                    start_pos = -1
        
        return json_candidates
    
    def _extract_move_from_json(self, data: Dict, legal_moves: List[Dict]) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """从解析的JSON中提取移动"""
        if not isinstance(data, dict) or 'best_move' not in data:
            return None
        
        best_move = data['best_move']
        if not isinstance(best_move, dict):
            return None
        
        from_pos = best_move.get('from')
        to_pos = best_move.get('to')
        
        # 验证坐标格式
        if (not isinstance(from_pos, list) or len(from_pos) != 2 or
            not isinstance(to_pos, list) or len(to_pos) != 2 or
            not all(isinstance(x, int) for x in from_pos + to_pos) or
            not (0 <= from_pos[0] <= 7 and 0 <= from_pos[1] <= 7) or
            not (0 <= to_pos[0] <= 7 and 0 <= to_pos[1] <= 7)):
            return None
        
        from_pos_tuple = tuple(from_pos)
        to_pos_tuple = tuple(to_pos)
        
        # 验证移动合法性
        for move in legal_moves:
            if (tuple(move['from']) == from_pos_tuple and 
                tuple(move['to']) == to_pos_tuple):
                return (from_pos_tuple, to_pos_tuple)
        
        return None

    def _parse_smart_fallback(self, response: str, legal_moves: List[Dict]) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """智能备用解析（从响应中提取坐标）"""
        try:
            import re
            
            # 寻找坐标对
            coord_patterns = [
                r'(\d)\s*[,，]\s*(\d)',      # 数字,数字
                r'\[(\d)\s*[,，]\s*(\d)\]',  # [数字,数字]
                r'\((\d)\s*[,，]\s*(\d)\)',  # (数字,数字)
            ]
            
            all_coords = []
            for pattern in coord_patterns:
                matches = re.finditer(pattern, response)
                for match in matches:
                    try:
                        x, y = int(match.group(1)), int(match.group(2))
                        if 0 <= x <= 7 and 0 <= y <= 7:
                            all_coords.append((x, y))
                    except ValueError:
                        continue
            
            # 尝试坐标对组合
            if len(all_coords) >= 2:
                for i in range(len(all_coords)):
                    for j in range(i+1, len(all_coords)):
                        # 正向和反向都试试
                        for from_pos, to_pos in [(all_coords[i], all_coords[j]), 
                                                 (all_coords[j], all_coords[i])]:
                            for move in legal_moves:
                                if (tuple(move['from']) == from_pos and 
                                    tuple(move['to']) == to_pos):
                                    return (from_pos, to_pos)
            
            # 尝试棋谱记号
            notation_matches = re.findall(r'\b([a-h][1-8])\b', response.lower())
            if len(notation_matches) >= 2:
                for i in range(len(notation_matches)):
                    for j in range(i+1, len(notation_matches)):
                        from_notation = notation_matches[i]
                        to_notation = notation_matches[j]
                        
                        from_pos = self._notation_to_pos(from_notation)
                        to_pos = self._notation_to_pos(to_notation)
                        
                        if from_pos and to_pos:
                            for move in legal_moves:
                                if (tuple(move['from']) == from_pos and 
                                    tuple(move['to']) == to_pos):
                                    return (from_pos, to_pos)
            
            return None
            
        except Exception:
            return None
    
    def _parse_fallback_formats(self, response: str, legal_moves: List[Dict]) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """解析备用格式（棋谱记号和坐标格式）"""
        try:
            import re
            
            # 棋谱记号格式
            notation_patterns = [
                r'([a-h][1-8])\s*[-→]\s*([a-h][1-8])',
                r'([a-h][1-8])\s+to\s+([a-h][1-8])',
                r'move:?\s*([a-h][1-8])\s*[-→]\s*([a-h][1-8])',
            ]
            
            for pattern in notation_patterns:
                matches = re.finditer(pattern, response, re.IGNORECASE)
                for match in matches:
                    from_pos = self._notation_to_pos(match.group(1).lower())
                    to_pos = self._notation_to_pos(match.group(2).lower())
                    
                    if from_pos and to_pos:
                        for move in legal_moves:
                            if (tuple(move['from']) == from_pos and 
                                tuple(move['to']) == to_pos):
                                return (from_pos, to_pos)
            
            # 坐标格式
            coord_patterns = [
                r'\((\d),\s*(\d)\)\s*[-→到至]\s*\((\d),\s*(\d)\)',
                r'\[(\d),\s*(\d)\]\s*[-→到至]\s*\[(\d),\s*(\d)\]',
                r'(\d),\s*(\d)\s+(?:to|到|至)\s+(\d),\s*(\d)',
            ]
            
            for pattern in coord_patterns:
                matches = re.finditer(pattern, response)
                for match in matches:
                    try:
                        from_x, from_y = int(match.group(1)), int(match.group(2))
                        to_x, to_y = int(match.group(3)), int(match.group(4))
                        
                        if (0 <= from_x <= 7 and 0 <= from_y <= 7 and
                            0 <= to_x <= 7 and 0 <= to_y <= 7):
                            
                            from_pos = (from_x, from_y)
                            to_pos = (to_x, to_y)
                            
                            for move in legal_moves:
                                if (tuple(move['from']) == from_pos and 
                                    tuple(move['to']) == to_pos):
                                    return (from_pos, to_pos)
                    except ValueError:
                        continue
            
            return None
        except Exception:
            return None

    def _notation_to_pos(self, notation: str) -> Optional[Tuple[int, int]]:
        """将棋谱记号转换为坐标"""
        try:
            if len(notation) != 2:
                return None
            
            file_char = notation[0].lower()
            rank_char = notation[1]
            
            if file_char < 'a' or file_char > 'h':
                return None
            if rank_char < '1' or rank_char > '8':
                return None
            
            x = ord(file_char) - ord('a')  # a=0, b=1, ..., h=7
            y = int(rank_char) - 1         # 1=0, 2=1, ..., 8=7（与棋盘坐标一致）
            
            return (x, y)
            
        except Exception:
            return None
    
    def _get_mock_move(self, board: ChessBoard, color: PieceColor) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """模拟模式下的移动选择"""
        legal_moves = []
        
        for position, piece in board.pieces.items():
            if piece.color == color:
                moves = board.get_legal_moves(position)
                for to_pos in moves:
                    legal_moves.append((position, to_pos))
        
        if not legal_moves:
            return None
        
        # 简单的启发式选择（优先吃子、中心控制）
        scored_moves = []
        
        for move in legal_moves:
            from_pos, to_pos = move
            score = 0
            
            # 吃子加分
            if to_pos in board.pieces:
                captured_piece = board.pieces[to_pos]
                piece_values = {
                    PieceType.PAWN: 1,
                    PieceType.KNIGHT: 3,
                    PieceType.BISHOP: 3,
                    PieceType.ROOK: 5,
                    PieceType.QUEEN: 9,
                    PieceType.KING: 0
                }
                score += piece_values.get(captured_piece.piece_type, 0) * 10
            
            # 中心控制加分
            center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
            if to_pos in center_squares:
                score += 5
            
            # 随机因子
            score += random.uniform(-2, 2)
            
            scored_moves.append((move, score))
        
        # 选择得分最高的移动
        best_move = max(scored_moves, key=lambda x: x[1])[0]
        return best_move
    
    def _get_fallback_move(self, board: ChessBoard, color: PieceColor, legal_moves: List[Dict]) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """备用移动选择"""
        if not legal_moves:
            return None
        
        # 使用评估函数选择最佳移动
        best_move = None
        best_score = float('-inf') if color == PieceColor.WHITE else float('inf')
        
        for move_info in legal_moves[:10]:  # 限制搜索范围
            from_pos = tuple(move_info['from'])
            to_pos = tuple(move_info['to'])
            
            # 简单评估
            score = random.uniform(-10, 10)  # 基础随机分数
            
            if move_info['capture']:
                score += 50  # 吃子加分
            
            center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
            if to_pos in center_squares:
                score += 20  # 中心控制加分
            
            if color == PieceColor.WHITE:
                if score > best_score:
                    best_score = score
                    best_move = (from_pos, to_pos)
            else:
                if score < best_score:
                    best_score = score
                    best_move = (from_pos, to_pos)
        
        return best_move or (tuple(legal_moves[0]['from']), tuple(legal_moves[0]['to']))
    
    def _calculate_material_balance(self, board: ChessBoard) -> Dict:
        """计算材质平衡"""
        piece_values = {
            PieceType.PAWN: 1,
            PieceType.KNIGHT: 3,
            PieceType.BISHOP: 3,
            PieceType.ROOK: 5,
            PieceType.QUEEN: 9,
            PieceType.KING: 0
        }
        
        white_material = 0
        black_material = 0
        
        for piece in board.pieces.values():
            value = piece_values.get(piece.piece_type, 0)
            if piece.color == PieceColor.WHITE:
                white_material += value
            else:
                black_material += value
        
        return {
            'white': white_material,
            'black': black_material,
            'difference': white_material - black_material,
            'status': '平衡' if abs(white_material - black_material) <= 1 else 
                     ('白方优势' if white_material > black_material else '黑方优势')
        }
    
    def _analyze_king_safety(self, board: ChessBoard, color: PieceColor) -> str:
        """分析王的安全"""
        # 简化版本
        king_positions = [(pos, piece) for pos, piece in board.pieces.items() 
                         if piece.piece_type == PieceType.KING and piece.color == color]
        
        if not king_positions:
            return "王不在棋盘上"
        
        king_pos = king_positions[0][0]
        x, y = king_pos
        
        # 检查王是否在后排
        back_rank = 0 if color == PieceColor.WHITE else 7
        if y == back_rank:
            return "王在后排，相对安全"
        else:
            return "王已离开后排，需要注意安全"
    
    def _analyze_piece_activity(self, board: ChessBoard, color: PieceColor) -> str:
        """分析棋子活跃度"""
        own_pieces = [piece for piece in board.pieces.values() if piece.color == color]
        
        if len(own_pieces) > 12:
            return "开局阶段，需要开发棋子"
        elif len(own_pieces) > 8:
            return "中局阶段，棋子协调重要"
        else:
            return "残局阶段，王和兵的作用增强"
    
    def _analyze_pawn_structure(self, board: ChessBoard) -> str:
        """分析兵形结构"""
        # 简化版本
        return "兵形结构分析需要更详细的实现"
    
    def _find_tactical_threats(self, board: ChessBoard, color: PieceColor) -> str:
        """寻找战术威胁"""
        # 简化版本 - 检查是否有将军
        if board.board.is_check():
            return "当前处于将军状态"
        return "未发现直接战术威胁"
    
    def _determine_game_phase(self, board: ChessBoard) -> str:
        """确定游戏阶段"""
        total_pieces = len(board.pieces)
        
        if total_pieces > 24:
            return "开局"
        elif total_pieces > 12:
            return "中局"
        else:
            return "残局"
    
    def _get_castling_status(self, board: ChessBoard) -> Dict:
        """获取易位状态"""
        return {
            'white_kingside': board.board.has_kingside_castling_rights(True),
            'white_queenside': board.board.has_queenside_castling_rights(True),
            'black_kingside': board.board.has_kingside_castling_rights(False),
            'black_queenside': board.board.has_queenside_castling_rights(False)
        }
    
    def _check_special_situations(self, board: ChessBoard) -> str:
        """检查特殊情况"""
        # 检查特殊情况
        if board.board.is_checkmate():
            return "将死"
        elif board.board.is_stalemate():
            return "逼和"
        elif board.board.is_check():
            return "将军"
        else:
            return "正常"
    
    def _to_chess_notation(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
        """转换为象棋记谱法"""
        def pos_to_notation(pos):
            x, y = pos
            return f"{chr(ord('a') + x)}{8 - y}"
        
        return f"{pos_to_notation(from_pos)}-{pos_to_notation(to_pos)}"
    
    def _update_stats(self, response_time: float, success: bool):
        """更新性能统计"""
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
            self.stats['total_response_time'] += response_time
            self.stats['average_response_time'] = (
                self.stats['total_response_time'] / self.stats['successful_requests']
            )
        else:
            self.stats['failed_requests'] += 1
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        success_rate = (
            self.stats['successful_requests'] / self.stats['total_requests'] * 100
            if self.stats['total_requests'] > 0 else 0
        )
        
        return {
            **self.stats,
            'success_rate': f"{success_rate:.1f}%",
            'mock_mode': self.mock_mode,
            'model': self.model
        }
    
    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []

def main():
    """测试GPT AI"""
    print("🤖 GPT Chess AI 测试")
    
    # 创建AI实例
    api_key = os.getenv('OPENAI_API_KEY')
    gpt_ai = GPTChessAI(api_key)
    
    # 创建测试棋盘
    board = ChessBoard()
    
    # 测试移动
    move = gpt_ai.get_best_move(board, PieceColor.WHITE)
    
    if move:
        print(f"✅ GPT选择移动: {move[0]} -> {move[1]}")
    else:
        print("❌ GPT未能选择移动")
    
    # 显示统计信息
    stats = gpt_ai.get_stats()
    print(f"📊 成功率: {stats['success_rate']}, 平均响应时间: {stats.get('average_response_time', 0):.2f}s")

if __name__ == "__main__":
    main()
