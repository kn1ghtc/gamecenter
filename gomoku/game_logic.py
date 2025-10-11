"""五子棋核心游戏逻辑模块
Core game logic for Gomoku (Five in a Row).

包含棋盘表示、规则判定、胜负检测、悔棋系统等核心功能。
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple
import json


class Player(Enum):
    """玩家枚举"""
    EMPTY = 0
    BLACK = 1
    WHITE = 2
    
    def opponent(self) -> Player:
        """返回对手"""
        if self == Player.BLACK:
            return Player.WHITE
        elif self == Player.WHITE:
            return Player.BLACK
        return Player.EMPTY
    
    def __str__(self) -> str:
        return self.name


class GameState(Enum):
    """游戏状态枚举"""
    ONGOING = "ongoing"        # 游戏进行中
    BLACK_WIN = "black_win"    # 黑棋胜利
    WHITE_WIN = "white_win"    # 白棋胜利
    DRAW = "draw"              # 平局（棋盘满）
    
    def __str__(self) -> str:
        return self.value


class Move:
    """着法表示"""
    def __init__(self, row: int, col: int, player: Player):
        self.row = row
        self.col = col
        self.player = player
    
    def to_tuple(self) -> Tuple[int, int]:
        """转换为坐标元组"""
        return (self.row, self.col)
    
    def __repr__(self) -> str:
        return f"Move({self.row}, {self.col}, {self.player})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Move):
            return False
        return (self.row == other.row and 
                self.col == other.col and 
                self.player == other.player)


class Board:
    """五子棋棋盘类
    
    15×15标准棋盘，支持落子、悔棋、胜负判定等操作。
    """
    
    # 标准棋盘大小
    SIZE = 15
    
    # 八个方向：水平、垂直、两个对角线
    DIRECTIONS = [
        (0, 1),   # 水平右
        (1, 0),   # 垂直下
        (1, 1),   # 对角右下
        (1, -1),  # 对角左下
    ]
    
    def __init__(self, size: int = SIZE):
        """初始化棋盘
        
        Args:
            size: 棋盘大小（默认15×15）
        """
        self.size = size
        self.board: List[List[Player]] = [
            [Player.EMPTY for _ in range(size)] for _ in range(size)
        ]
        self.history: List[Move] = []
        self.current_player = Player.BLACK
        self._state = GameState.ONGOING
        self._winning_line: Optional[List[Tuple[int, int]]] = None
    
    @property
    def empty_count(self) -> int:
        """返回空位数量"""
        count = 0
        for row in self.board:
            count += row.count(Player.EMPTY)
        return count
    
    @property
    def state(self) -> GameState:
        """返回当前游戏状态"""
        return self._state
    
    @property
    def winning_line(self) -> Optional[List[Tuple[int, int]]]:
        """返回获胜的五子连线"""
        return self._winning_line
    
    def is_valid_pos(self, row: int, col: int) -> bool:
        """检查坐标是否合法"""
        return 0 <= row < self.size and 0 <= col < self.size
    
    def is_empty(self, row: int, col: int) -> bool:
        """检查位置是否为空"""
        return (self.is_valid_pos(row, col) and 
                self.board[row][col] == Player.EMPTY)
    
    def get_stone(self, row: int, col: int) -> Player:
        """获取指定位置的棋子"""
        if not self.is_valid_pos(row, col):
            return Player.EMPTY
        return self.board[row][col]
    
    def place_stone(self, row: int, col: int, player: Optional[Player] = None) -> bool:
        """放置棋子
        
        Args:
            row: 行坐标
            col: 列坐标
            player: 玩家（None时使用当前玩家）
        
        Returns:
            是否成功放置
        """
        if not self.is_empty(row, col):
            return False
        
        if self._state != GameState.ONGOING:
            return False
        
        if player is None:
            player = self.current_player
        
        # 放置棋子
        self.board[row][col] = player
        move = Move(row, col, player)
        self.history.append(move)
        
        # 检查胜负
        if self._check_win(row, col, player):
            self._state = (GameState.BLACK_WIN if player == Player.BLACK 
                          else GameState.WHITE_WIN)
        elif self.empty_count == 0:
            self._state = GameState.DRAW
        else:
            # 切换玩家
            self.current_player = self.current_player.opponent()
        
        return True
    
    def undo_move(self) -> bool:
        """悔棋（撤销最后一步）
        
        Returns:
            是否成功悔棋
        """
        if not self.history:
            return False
        
        last_move = self.history.pop()
        self.board[last_move.row][last_move.col] = Player.EMPTY
        
        # 恢复游戏状态
        self._state = GameState.ONGOING
        self._winning_line = None
        self.current_player = last_move.player
        
        return True
    
    def _check_win(self, row: int, col: int, player: Player) -> bool:
        """检查是否形成五子连珠
        
        Args:
            row: 最后落子的行
            col: 最后落子的列
            player: 落子玩家
        
        Returns:
            是否获胜
        """
        # 检查四个方向
        for dr, dc in self.DIRECTIONS:
            line = self._count_line(row, col, dr, dc, player)
            if line >= 5:
                # 记录获胜线
                self._winning_line = self._get_winning_line(row, col, dr, dc, player)
                return True
        
        return False
    
    def _count_line(self, row: int, col: int, dr: int, dc: int, player: Player) -> int:
        """计算指定方向的连续棋子数
        
        Args:
            row, col: 起始位置
            dr, dc: 方向增量
            player: 玩家
        
        Returns:
            连续棋子数
        """
        count = 1  # 包含起始位置
        
        # 正向搜索
        r, c = row + dr, col + dc
        while self.is_valid_pos(r, c) and self.board[r][c] == player:
            count += 1
            r += dr
            c += dc
        
        # 反向搜索
        r, c = row - dr, col - dc
        while self.is_valid_pos(r, c) and self.board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        
        return count
    
    def _get_winning_line(self, row: int, col: int, dr: int, dc: int, 
                          player: Player) -> List[Tuple[int, int]]:
        """获取获胜线的所有坐标
        
        Args:
            row, col: 中心位置
            dr, dc: 方向增量
            player: 玩家
        
        Returns:
            获胜线坐标列表
        """
        line = [(row, col)]
        
        # 正向
        r, c = row + dr, col + dc
        while self.is_valid_pos(r, c) and self.board[r][c] == player:
            line.append((r, c))
            r += dr
            c += dc
        
        # 反向
        r, c = row - dr, col - dc
        while self.is_valid_pos(r, c) and self.board[r][c] == player:
            line.insert(0, (r, c))
            r -= dr
            c -= dc
        
        return line[:5]  # 只返回前5个
    
    def get_empty_neighbors(self, distance: int = 2) -> List[Tuple[int, int]]:
        """获取所有已落子位置周围的空位
        
        Args:
            distance: 搜索距离（默认2格）
        
        Returns:
            空位坐标列表
        """
        if not self.history:
            # 第一步，返回中心位置
            center = self.size // 2
            return [(center, center)]
        
        neighbors = set()
        
        for move in self.history:
            for dr in range(-distance, distance + 1):
                for dc in range(-distance, distance + 1):
                    if dr == 0 and dc == 0:
                        continue
                    r, c = move.row + dr, move.col + dc
                    if self.is_empty(r, c):
                        neighbors.add((r, c))
        
        return list(neighbors)
    
    def copy(self) -> Board:
        """创建棋盘副本"""
        new_board = Board(self.size)
        new_board.board = [row[:] for row in self.board]
        new_board.history = self.history[:]
        new_board.current_player = self.current_player
        new_board._state = self._state
        new_board._winning_line = self._winning_line[:] if self._winning_line else None
        return new_board
    
    def to_dict(self) -> dict:
        """转换为字典（用于保存）"""
        return {
            'size': self.size,
            'board': [[p.value for p in row] for row in self.board],
            'history': [
                {'row': m.row, 'col': m.col, 'player': m.player.value}
                for m in self.history
            ],
            'current_player': self.current_player.value,
            'state': self._state.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Board:
        """从字典创建棋盘"""
        board = cls(data['size'])
        
        # 重放历史
        for move_data in data['history']:
            player = Player(move_data['player'])
            board.place_stone(move_data['row'], move_data['col'], player)
        
        return board
    
    def save_to_file(self, filepath: str) -> None:
        """保存棋局到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Board:
        """从文件加载棋局"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """字符串表示（用于调试）"""
        lines = []
        lines.append("  " + " ".join(f"{i:2}" for i in range(self.size)))
        for i, row in enumerate(self.board):
            symbols = []
            for cell in row:
                if cell == Player.BLACK:
                    symbols.append("●")
                elif cell == Player.WHITE:
                    symbols.append("○")
                else:
                    symbols.append("·")
            lines.append(f"{i:2} " + " ".join(symbols))
        return "\n".join(lines)


class GameManager:
    """游戏管理器
    
    管理游戏流程、悔棋次数限制等高层逻辑。
    """
    
    def __init__(self, board: Optional[Board] = None, max_undo: int = 3):
        """初始化游戏管理器
        
        Args:
            board: 棋盘实例（None时创建新棋盘）
            max_undo: 最大悔棋次数
        """
        self.board = board if board else Board()
        self.max_undo = max_undo
        self.undo_count = 0
    
    def reset(self) -> None:
        """重置游戏"""
        self.board = Board(self.board.size)
        self.undo_count = 0
    
    def place_stone(self, row: int, col: int) -> bool:
        """放置棋子"""
        return self.board.place_stone(row, col)
    
    def undo(self, count: int = 1) -> bool:
        """悔棋
        
        Args:
            count: 悔棋步数（人机对战时悔棋2步）
        
        Returns:
            是否成功
        """
        if self.undo_count >= self.max_undo:
            return False
        
        success = True
        for _ in range(count):
            if not self.board.undo_move():
                success = False
                break
        
        if success:
            self.undo_count += 1
        
        return success
    
    def can_undo(self) -> bool:
        """是否可以悔棋"""
        return (self.undo_count < self.max_undo and 
                len(self.board.history) > 0)
    
    def get_undo_remaining(self) -> int:
        """返回剩余悔棋次数"""
        return max(0, self.max_undo - self.undo_count)


def create_game(size: int = 15, max_undo: int = 3) -> GameManager:
    """创建新游戏（工厂函数）"""
    return GameManager(Board(size), max_undo)
