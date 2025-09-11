"""
数据库管理模块
管理游戏数据存储和检索
"""
import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.pieces import PieceColor

class ChessDatabase:
    """国际象棋数据库管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用当前模块目录下的数据库路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, 'chess_games.db')
        
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 游戏记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    white_player TEXT,
                    black_player TEXT,
                    white_type TEXT,  -- 'human' or 'ai'
                    black_type TEXT,
                    ai_level TEXT,
                    result TEXT,  -- 'white_wins', 'black_wins', 'draw'
                    total_moves INTEGER,
                    game_duration REAL,
                    pgn TEXT,
                    final_position TEXT  -- FEN notation
                )
            ''')
            
            # 移动记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    move_number INTEGER,
                    player_color TEXT,
                    from_square TEXT,
                    to_square TEXT,
                    piece_type TEXT,
                    captured_piece TEXT,
                    special_move TEXT,  -- 'castle', 'en_passant', 'promotion'
                    notation TEXT,
                    evaluation REAL,
                    think_time REAL,
                    position_after TEXT,  -- FEN after move
                    FOREIGN KEY (game_id) REFERENCES games (id)
                )
            ''')
            
            # AI训练数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position TEXT,  -- FEN notation
                    evaluation REAL,
                    best_move TEXT,
                    depth INTEGER,
                    nodes_searched INTEGER,
                    game_id INTEGER,
                    FOREIGN KEY (game_id) REFERENCES games (id)
                )
            ''')
            
            # 统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT UNIQUE,
                    games_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    total_time REAL DEFAULT 0,
                    avg_moves REAL DEFAULT 0,
                    elo_rating INTEGER DEFAULT 1200,
                    last_played TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_game(self, game_data: Dict) -> int:
        """保存游戏记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO games (
                    start_time, end_time, white_player, black_player,
                    white_type, black_type, ai_level, result,
                    total_moves, game_duration, pgn, final_position
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_data['start_time'],
                game_data['end_time'],
                game_data['white_player'],
                game_data['black_player'],
                game_data['white_type'],
                game_data['black_type'],
                game_data.get('ai_level'),
                game_data['result'],
                game_data['total_moves'],
                game_data['game_duration'],
                game_data['pgn'],
                game_data['final_position']
            ))
            
            game_id = cursor.lastrowid
            conn.commit()
            
            return game_id
    
    def save_move(self, game_id: int, move_data: Dict):
        """保存移动记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO moves (
                    game_id, move_number, player_color, from_square, to_square,
                    piece_type, captured_piece, special_move, notation,
                    evaluation, think_time, position_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_id,
                move_data['move_number'],
                move_data['player_color'],
                move_data['from_square'],
                move_data['to_square'],
                move_data['piece_type'],
                move_data.get('captured_piece'),
                move_data.get('special_move'),
                move_data['notation'],
                move_data.get('evaluation'),
                move_data.get('think_time'),
                move_data['position_after']
            ))
            
            conn.commit()
    
    def save_training_position(self, position_data: Dict):
        """保存训练位置数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO training_positions (
                    position, evaluation, best_move, depth,
                    nodes_searched, game_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                position_data['position'],
                position_data['evaluation'],
                position_data['best_move'],
                position_data['depth'],
                position_data['nodes_searched'],
                position_data.get('game_id')
            ))
            
            conn.commit()
    
    def get_games(self, limit: int = 50, player_name: str = None) -> List[Dict]:
        """获取游戏记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if player_name:
                cursor.execute('''
                    SELECT * FROM games 
                    WHERE white_player = ? OR black_player = ?
                    ORDER BY start_time DESC LIMIT ?
                ''', (player_name, player_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM games 
                    ORDER BY start_time DESC LIMIT ?
                ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            games = []
            
            for row in cursor.fetchall():
                game_dict = dict(zip(columns, row))
                games.append(game_dict)
            
            return games
    
    def get_game_moves(self, game_id: int) -> List[Dict]:
        """获取游戏的所有移动"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM moves 
                WHERE game_id = ? 
                ORDER BY move_number
            ''', (game_id,))
            
            columns = [desc[0] for desc in cursor.description]
            moves = []
            
            for row in cursor.fetchall():
                move_dict = dict(zip(columns, row))
                moves.append(move_dict)
            
            return moves
    
    def get_training_data(self, limit: int = 1000) -> List[Dict]:
        """获取训练数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM training_positions 
                ORDER BY id DESC LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            positions = []
            
            for row in cursor.fetchall():
                position_dict = dict(zip(columns, row))
                positions.append(position_dict)
            
            return positions
    
    def update_player_stats(self, player_name: str, result: str, game_duration: float, move_count: int):
        """更新玩家统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查玩家是否存在
            cursor.execute('SELECT * FROM player_stats WHERE player_name = ?', (player_name,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                wins = existing[2] + (1 if result == 'win' else 0)
                losses = existing[3] + (1 if result == 'loss' else 0)
                draws = existing[4] + (1 if result == 'draw' else 0)
                games_played = existing[1] + 1
                total_time = existing[5] + game_duration
                avg_moves = (existing[6] * existing[1] + move_count) / games_played
                
                cursor.execute('''
                    UPDATE player_stats 
                    SET games_played = ?, wins = ?, losses = ?, draws = ?,
                        total_time = ?, avg_moves = ?, last_played = ?
                    WHERE player_name = ?
                ''', (games_played, wins, losses, draws, total_time, avg_moves, datetime.now(), player_name))
            else:
                # 创建新记录
                wins = 1 if result == 'win' else 0
                losses = 1 if result == 'loss' else 0
                draws = 1 if result == 'draw' else 0
                
                cursor.execute('''
                    INSERT INTO player_stats (
                        player_name, games_played, wins, losses, draws,
                        total_time, avg_moves, last_played
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (player_name, 1, wins, losses, draws, game_duration, move_count, datetime.now()))
            
            conn.commit()
    
    def get_player_stats(self, player_name: str) -> Optional[Dict]:
        """获取玩家统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM player_stats WHERE player_name = ?', (player_name,))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            
            return None
    
    def export_games_to_pgn(self, output_file: str, limit: int = None):
        """导出游戏为PGN格式"""
        games = self.get_games(limit or 1000)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for game in games:
                # PGN头部信息
                f.write(f'[Event "Chess Game"]\n')
                f.write(f'[Site "Local"]\n')
                f.write(f'[Date "{game["start_time"][:10]}"]\n')
                f.write(f'[Round "?"]\n')
                f.write(f'[White "{game["white_player"]}"]\n')
                f.write(f'[Black "{game["black_player"]}"]\n')
                
                if game['result'] == 'white_wins':
                    result = '1-0'
                elif game['result'] == 'black_wins':
                    result = '0-1'
                else:
                    result = '1/2-1/2'
                
                f.write(f'[Result "{result}"]\n')
                f.write(f'[TimeControl "?"]\n')
                f.write(f'[Termination "Normal"]\n\n')
                
                # 移动记录
                if game['pgn']:
                    f.write(game['pgn'])
                    f.write(f' {result}\n\n')
                else:
                    f.write(f'{result}\n\n')
    
    def get_statistics(self) -> Dict:
        """获取总体统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 总游戏数
            cursor.execute('SELECT COUNT(*) FROM games')
            stats['total_games'] = cursor.fetchone()[0]
            
            # 结果统计
            cursor.execute('SELECT result, COUNT(*) FROM games GROUP BY result')
            results = dict(cursor.fetchall())
            stats['results'] = results
            
            # 平均游戏时长
            cursor.execute('SELECT AVG(game_duration) FROM games WHERE game_duration IS NOT NULL')
            avg_duration = cursor.fetchone()[0]
            stats['avg_game_duration'] = avg_duration or 0
            
            # 平均移动数
            cursor.execute('SELECT AVG(total_moves) FROM games WHERE total_moves IS NOT NULL')
            avg_moves = cursor.fetchone()[0]
            stats['avg_moves'] = avg_moves or 0
            
            # AI vs Human 统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN white_type = 'ai' OR black_type = 'ai' THEN 1 ELSE 0 END) as ai_games,
                    SUM(CASE WHEN white_type = 'human' AND black_type = 'human' THEN 1 ELSE 0 END) as human_games
                FROM games
            ''')
            game_types = cursor.fetchone()
            stats['ai_games'] = game_types[1] if game_types else 0
            stats['human_games'] = game_types[2] if game_types else 0
            
            return stats
