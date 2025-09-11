"""
PGN格式处理模块
用于导入和导出国际象棋游戏记录
"""
import re
import sys
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

class PGNParser:
    """PGN格式解析器"""
    
    def __init__(self):
        self.current_game = {}
        self.games = []
    
    def parse_file(self, file_path: str) -> List[Dict]:
        """解析PGN文件"""
        games = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                games = self.parse_content(content)
        except FileNotFoundError:
            print(f"文件未找到: {file_path}")
        except Exception as e:
            print(f"解析PGN文件时出错: {e}")
        
        return games
    
    def parse_content(self, content: str) -> List[Dict]:
        """解析PGN内容"""
        games = []
        current_game = {}
        in_moves = False
        moves_text = ""
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if current_game and in_moves:
                    # 游戏结束
                    current_game['moves'] = self._parse_moves(moves_text)
                    games.append(current_game)
                    current_game = {}
                    in_moves = False
                    moves_text = ""
                continue
            
            if line.startswith('[') and line.endswith(']'):
                # 解析头部标签
                tag_match = re.match(r'\[(\w+)\s+"([^"]*)"\]', line)
                if tag_match:
                    tag_name = tag_match.group(1)
                    tag_value = tag_match.group(2)
                    current_game[tag_name.lower()] = tag_value
            else:
                # 移动记录
                in_moves = True
                moves_text += line + " "
        
        # 处理最后一个游戏
        if current_game and in_moves:
            current_game['moves'] = self._parse_moves(moves_text)
            games.append(current_game)
        
        return games
    
    def _parse_moves(self, moves_text: str) -> List[Dict]:
        """解析移动记录"""
        moves = []
        
        # 移除注释
        moves_text = re.sub(r'\{[^}]*\}', '', moves_text)
        moves_text = re.sub(r';[^\n]*', '', moves_text)
        
        # 移除游戏结果
        moves_text = re.sub(r'\s+(1-0|0-1|1/2-1/2|\*)\s*$', '', moves_text)
        
        # 分割移动
        tokens = moves_text.split()
        move_number = 1
        white_move = None
        
        for token in tokens:
            # 跳过移动编号
            if re.match(r'^\d+\.\.\.?$', token):
                continue
            
            # 跳过注释符号
            if token.startswith('(') or token.endswith(')'):
                continue
            
            # 跳过NAG（数字注释符号）
            if re.match(r'^\$\d+$', token):
                continue
            
            # 处理移动
            if self._is_valid_move(token):
                if white_move is None:
                    # 白方移动
                    white_move = token
                else:
                    # 黑方移动
                    moves.append({
                        'move_number': move_number,
                        'white': white_move,
                        'black': token
                    })
                    white_move = None
                    move_number += 1
        
        # 处理最后一个白方移动（如果游戏以白方移动结束）
        if white_move is not None:
            moves.append({
                'move_number': move_number,
                'white': white_move,
                'black': None
            })
        
        return moves
    
    def _is_valid_move(self, token: str) -> bool:
        """检查是否是有效的移动记录"""
        # 基本移动模式
        move_patterns = [
            r'^[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](\=[QRBN])?[\+#]?$',  # 普通移动
            r'^O-O(-O)?[\+#]?$',  # 王车易位
            r'^[a-h][1-8](\=[QRBN])?[\+#]?$',  # 兵移动
        ]
        
        return any(re.match(pattern, token) for pattern in move_patterns)
    
    def create_pgn(self, game_data: Dict) -> str:
        """创建PGN格式字符串"""
        pgn_lines = []
        
        # 头部标签
        headers = {
            'Event': game_data.get('event', 'Casual Game'),
            'Site': game_data.get('site', 'Local'),
            'Date': game_data.get('date', datetime.now().strftime('%Y.%m.%d')),
            'Round': game_data.get('round', '?'),
            'White': game_data.get('white_player', 'Player 1'),
            'Black': game_data.get('black_player', 'Player 2'),
            'Result': game_data.get('result', '*')
        }
        
        for key, value in headers.items():
            pgn_lines.append(f'[{key} "{value}"]')
        
        pgn_lines.append('')  # 空行分隔头部和移动
        
        # 移动记录
        moves_line = ""
        moves = game_data.get('moves', [])
        
        for i, move in enumerate(moves):
            if i % 2 == 0:  # 白方移动
                move_number = (i // 2) + 1
                moves_line += f"{move_number}. {move} "
            else:  # 黑方移动
                moves_line += f"{move} "
            
            # 每20个移动换行
            if (i + 1) % 20 == 0:
                moves_line += "\n"
        
        # 添加游戏结果
        moves_line += game_data.get('result', '*')
        pgn_lines.append(moves_line)
        
        return '\n'.join(pgn_lines)
    
    def export_games_to_file(self, games: List[Dict], output_path: str):
        """导出多个游戏到PGN文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, game in enumerate(games):
                    if i > 0:
                        f.write('\n\n')  # 游戏之间空行分隔
                    
                    pgn_content = self.create_pgn(game)
                    f.write(pgn_content)
            
            print(f"成功导出 {len(games)} 个游戏到 {output_path}")
            
        except Exception as e:
            print(f"导出PGN文件时出错: {e}")

class GameRecorder:
    """游戏记录器"""
    
    def __init__(self):
        self.moves = []
        self.headers = {}
        self.start_time = None
        
    def start_recording(self, white_player: str, black_player: str, event: str = "Casual Game"):
        """开始记录游戏"""
        self.moves = []
        self.start_time = datetime.now()
        
        self.headers = {
            'event': event,
            'site': 'Local',
            'date': self.start_time.strftime('%Y.%m.%d'),
            'round': '?',
            'white_player': white_player,
            'black_player': black_player,
            'result': '*'
        }
    
    def record_move(self, move_notation: str, move_number: int = None, color: str = 'white'):
        """记录移动"""
        if move_number is None:
            move_number = len(self.moves) // 2 + 1
        
        self.moves.append({
            'notation': move_notation,
            'move_number': move_number,
            'color': color,
            'timestamp': datetime.now()
        })
    
    def end_recording(self, result: str):
        """结束记录"""
        self.headers['result'] = result
        
        if self.start_time:
            duration = datetime.now() - self.start_time
            self.headers['time_control'] = f"{duration.total_seconds():.0f}s"
    
    def get_pgn_moves(self) -> List[str]:
        """获取PGN格式的移动列表"""
        pgn_moves = []
        
        for move in self.moves:
            pgn_moves.append(move['notation'])
        
        return pgn_moves
    
    def get_game_data(self) -> Dict:
        """获取完整游戏数据"""
        return {
            **self.headers,
            'moves': self.get_pgn_moves(),
            'move_count': len(self.moves),
            'duration': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
    
    def save_to_file(self, file_path: str):
        """保存到PGN文件"""
        parser = PGNParser()
        game_data = self.get_game_data()
        pgn_content = parser.create_pgn(game_data)
        
        try:
            # 追加模式，允许多个游戏记录在同一文件中
            with open(file_path, 'a', encoding='utf-8') as f:
                if os.path.getsize(file_path) > 0:
                    f.write('\n\n')  # 如果文件不为空，先添加空行
                f.write(pgn_content)
            
            print(f"游戏记录已保存到: {file_path}")
            
        except Exception as e:
            print(f"保存游戏记录时出错: {e}")

def convert_algebraic_to_pgn(from_square: str, to_square: str, piece_type: str, 
                           captured: bool = False, check: bool = False, 
                           checkmate: bool = False, promotion: str = None) -> str:
    """将移动转换为PGN记谱法"""
    notation = ""
    
    # 特殊移动：王车易位
    if piece_type.lower() == 'king':
        if from_square == 'e1' and to_square == 'g1':
            return 'O-O'
        elif from_square == 'e1' and to_square == 'c1':
            return 'O-O-O'
        elif from_square == 'e8' and to_square == 'g8':
            return 'O-O'
        elif from_square == 'e8' and to_square == 'c8':
            return 'O-O-O'
    
    # 棋子符号
    if piece_type.lower() != 'pawn':
        notation += piece_type.upper()
    
    # 吃子标记
    if captured:
        if piece_type.lower() == 'pawn':
            notation += from_square[0]  # 兵吃子时需要起始列
        notation += 'x'
    
    # 目标格子
    notation += to_square
    
    # 兵的升变
    if promotion:
        notation += f'={promotion.upper()}'
    
    # 将军和将死标记
    if checkmate:
        notation += '#'
    elif check:
        notation += '+'
    
    return notation
