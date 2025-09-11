"""
国际象棋游戏状态管理
管理游戏流程、状态转换和事件处理
"""
import time
import sys
import os
from datetime import datetime
from typing import Optional, Dict, List, Callable
from enum import Enum

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.board import ChessBoard
from game.pieces import PieceColor

# 延迟导入数据库模块，避免循环导入
try:
    from data.database import ChessDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ 数据库模块不可用，游戏记录将不会保存")

class GameState(Enum):
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'game_over'
    SETTINGS = 'settings'

class GameMode(Enum):
    HUMAN_VS_HUMAN = 'human_vs_human'
    HUMAN_VS_AI = 'human_vs_ai'
    AI_VS_AI = 'ai_vs_ai'

class ChessGameState:
    """国际象棋游戏状态管理器"""
    
    def __init__(self, enable_database: bool = True):
        self.board = ChessBoard()
        self.state = GameState.MENU
        self.mode = GameMode.HUMAN_VS_HUMAN
        self.ai_level = 'EASY'
        self.selected_square = None
        self.highlighted_squares = []
        self.move_hints = []
        self.game_start_time = None
        self.move_times = []
        self.observers = []  # 观察者模式用于UI更新
        
        # 数据库支持
        self.database = None
        self.current_game_id = None
        if enable_database and DATABASE_AVAILABLE:
            try:
                self.database = ChessDatabase()
                print("✅ 数据库初始化成功")
            except Exception as e:
                print(f"❌ 数据库初始化失败: {e}")
                self.database = None
        
        # 玩家设置
        self.players = {
            PieceColor.WHITE: {'type': 'human', 'name': 'Player 1'},
            PieceColor.BLACK: {'type': 'human', 'name': 'Player 2'}
        }
        
        # 游戏统计
        self.stats = {
            'games_played': 0,
            'wins': {'white': 0, 'black': 0, 'draw': 0},
            'total_moves': 0,
            'average_game_time': 0
        }
    
    def add_observer(self, observer: Callable):
        """添加状态观察者"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, data: Dict = None):
        """通知所有观察者状态变化"""
        for observer in self.observers:
            observer(event, data or {})
    
    def start_new_game(self, mode: GameMode = GameMode.HUMAN_VS_HUMAN, ai_level: str = 'EASY'):
        """开始新游戏"""
        self.board = ChessBoard()
        self.state = GameState.PLAYING
        self.mode = mode
        self.ai_level = ai_level
        self.selected_square = None
        self.highlighted_squares = []
        self.move_hints = []
        self.game_start_time = time.time()
        self.move_times = []
        
        # 设置玩家类型
        if mode == GameMode.HUMAN_VS_AI:
            self.players[PieceColor.WHITE] = {'type': 'human', 'name': 'Player'}
            self.players[PieceColor.BLACK] = {'type': 'ai', 'name': f'AI ({ai_level})'}
        elif mode == GameMode.AI_VS_AI:
            self.players[PieceColor.WHITE] = {'type': 'ai', 'name': f'AI White ({ai_level})'}
            self.players[PieceColor.BLACK] = {'type': 'ai', 'name': f'AI Black ({ai_level})'}
        else:
            self.players[PieceColor.WHITE] = {'type': 'human', 'name': 'Player 1'}
            self.players[PieceColor.BLACK] = {'type': 'human', 'name': 'Player 2'}
        
        self.notify_observers('game_started', {
            'mode': mode.value,
            'ai_level': ai_level,
            'players': self.players
        })
    
    def select_square(self, position: tuple):
        """选择棋盘上的方格"""
        if self.state != GameState.PLAYING:
            return
        
        current_player = self.board.current_player
        
        # 如果当前是AI回合，不允许人类操作
        if self.players[current_player]['type'] == 'ai':
            return
        
        piece = self.board.get_piece_at(position)
        
        # 如果没有选中的方格
        if self.selected_square is None:
            if piece and piece.color == current_player:
                self.selected_square = position
                self.move_hints = self.board.get_legal_moves(position)
                self.highlighted_squares = [position] + self.move_hints
                self.notify_observers('square_selected', {
                    'position': position,
                    'legal_moves': self.move_hints
                })
        else:
            # 如果点击的是同色棋子，切换选择
            if piece and piece.color == current_player:
                self.selected_square = position
                self.move_hints = self.board.get_legal_moves(position)
                self.highlighted_squares = [position] + self.move_hints
                self.notify_observers('square_selected', {
                    'position': position,
                    'legal_moves': self.move_hints
                })
            # 尝试移动棋子
            else:
                if self.attempt_move(self.selected_square, position):
                    self.selected_square = None
                    self.highlighted_squares = []
                    self.move_hints = []
                else:
                    # 移动失败，取消选择
                    self.selected_square = None
                    self.highlighted_squares = []
                    self.move_hints = []
    
    def attempt_move(self, from_pos: tuple, to_pos: tuple, promotion_piece: str = None) -> bool:
        """尝试执行移动
        
        Args:
            from_pos: 起始位置
            to_pos: 目标位置
            promotion_piece: 升变棋子类型 ('queen', 'rook', 'bishop', 'knight')
        """
        move_start_time = time.time()
        
        # 检查是否是兵升变
        piece = self.board.get_piece_at(from_pos)
        needs_promotion = (piece and piece.piece_type.name.lower() == 'pawn' and 
                          ((piece.color.name.lower() == 'white' and to_pos[1] == 7) or
                           (piece.color.name.lower() == 'black' and to_pos[1] == 0)))
        
        if needs_promotion and promotion_piece is None:
            # 默认升变为皇后
            promotion_piece = 'queen'
        
        move_result = self.board.make_move(from_pos, to_pos, promotion_piece)
        
        if move_result:
            move_time = time.time() - move_start_time
            self.move_times.append(move_time)
            
            self.notify_observers('move_made', {
                'from': from_pos,
                'to': to_pos,
                'board_state': self.board.get_board_state(),
                'move_time': move_time,
                'promotion': promotion_piece if needs_promotion else None
            })
            
            # 检查游戏是否结束
            if self.board.game_over:
                self.end_game()
            
            return True
        
        return False
    
    def undo_move(self):
        """撤销移动"""
        if self.state == GameState.PLAYING and self.board.undo_move():
            self.selected_square = None
            self.highlighted_squares = []
            self.move_hints = []
            
            self.notify_observers('move_undone', {
                'board_state': self.board.get_board_state()
            })
    
    def end_game(self):
        """结束游戏"""
        self.state = GameState.GAME_OVER
        game_time = time.time() - self.game_start_time if self.game_start_time else 0
        
        # 更新统计数据
        self.stats['games_played'] += 1
        self.stats['total_moves'] += len(self.board.move_history)
        
        if self.board.winner:
            if self.board.winner == PieceColor.WHITE:
                self.stats['wins']['white'] += 1
            else:
                self.stats['wins']['black'] += 1
        else:
            self.stats['wins']['draw'] += 1
        
        if self.stats['games_played'] > 0:
            self.stats['average_game_time'] = (
                self.stats['average_game_time'] * (self.stats['games_played'] - 1) + game_time
            ) / self.stats['games_played']
        
        # 保存游戏到数据库
        self._save_game_to_database(game_time)
        
        self.notify_observers('game_ended', {
            'winner': self.board.winner.value if self.board.winner else 'draw',
            'game_time': game_time,
            'total_moves': len(self.board.move_history),
            'stats': self.stats
        })
    
    def _save_game_to_database(self, game_time: float):
        """保存游戏到数据库"""
        if not self.database:
            return
        
        try:
            # 准备游戏数据
            game_data = {
                'start_time': datetime.fromtimestamp(self.game_start_time).isoformat() if self.game_start_time else None,
                'end_time': datetime.now().isoformat(),
                'white_player': self.players[PieceColor.WHITE]['name'],
                'black_player': self.players[PieceColor.BLACK]['name'],
                'white_type': self.players[PieceColor.WHITE]['type'],
                'black_type': self.players[PieceColor.BLACK]['type'],
                'ai_level': self.ai_level if self.mode != GameMode.HUMAN_VS_HUMAN else None,
                'result': self.board.winner.value if self.board.winner else 'draw',
                'total_moves': len(self.board.move_history),
                'game_duration': game_time,
                'pgn': self._generate_pgn(),
                'final_position': self.board.board.fen()
            }
            
            # 保存到数据库
            game_id = self.database.save_game(game_data)
            print(f"✅ 游戏记录已保存，ID: {game_id}")
            
        except Exception as e:
            print(f"❌ 保存游戏记录失败: {e}")
    
    def _generate_pgn(self) -> str:
        """生成PGN格式的游戏记录"""
        try:
            # 如果使用python-chess库，尝试直接获取PGN
            return str(self.board.board)
        except:
            # 否则，从move_history构建简单的PGN
            moves = []
            for i, move in enumerate(self.board.move_history):
                if isinstance(move, dict) and 'notation' in move:
                    move_str = move['notation']
                    if i % 2 == 0:
                        moves.append(f"{i//2 + 1}. {move_str}")
                    else:
                        moves.append(move_str)
                else:
                    # 如果没有记谱法，使用位置信息
                    if isinstance(move, dict):
                        from_pos = move.get('from', (0,0))
                        to_pos = move.get('to', (0,0))
                        move_str = f"{chr(ord('a') + from_pos[0])}{from_pos[1]+1}-{chr(ord('a') + to_pos[0])}{to_pos[1]+1}"
                        if i % 2 == 0:
                            moves.append(f"{i//2 + 1}. {move_str}")
                        else:
                            moves.append(move_str)
            return " ".join(moves)
    
    def pause_game(self):
        """暂停游戏"""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            self.notify_observers('game_paused', {})
    
    def resume_game(self):
        """恢复游戏"""
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            self.notify_observers('game_resumed', {})
    
    def go_to_menu(self):
        """返回主菜单"""
        self.state = GameState.MENU
        self.selected_square = None
        self.highlighted_squares = []
        self.move_hints = []
        self.notify_observers('menu_opened', {})
    
    def get_current_player_info(self) -> Dict:
        """获取当前玩家信息"""
        current_player = self.board.current_player
        return {
            'color': current_player.value,
            'type': self.players[current_player]['type'],
            'name': self.players[current_player]['name'],
            'in_check': self.board.is_in_check(current_player)
        }
    
    def is_human_turn(self) -> bool:
        """检查是否是人类玩家回合"""
        current_player = self.board.current_player
        return self.players[current_player]['type'] == 'human'
    
    def get_game_info(self) -> Dict:
        """获取游戏信息"""
        return {
            'state': self.state.value,
            'mode': self.mode.value,
            'ai_level': self.ai_level,
            'current_player': self.get_current_player_info(),
            'move_count': len(self.board.move_history),
            'game_time': time.time() - self.game_start_time if self.game_start_time else 0,
            'captured_pieces': self.board.captured_pieces,
            'last_moves': self.board.move_history[-5:] if self.board.move_history else []
        }
