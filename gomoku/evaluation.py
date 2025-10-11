"""五子棋评估函数模块
Evaluation functions for Gomoku AI.

包含棋型识别、启发式评估、位置权重计算等功能。
"""

from __future__ import annotations

from typing import Dict, List, Tuple
from gamecenter.gomoku.game_logic import Board, Player
from gamecenter.gomoku.config.config_manager import get_config_manager


_CONFIG = get_config_manager()
PATTERN_SCORES = _CONFIG.get_pattern_scores()


class PatternRecognizer:
    """棋型识别器
    
    识别线性棋型：五连、活四、冲四、活三等。
    """
    
    @staticmethod
    def analyze_line(line: List[Player], player: Player) -> Dict[str, int]:
        """分析一条线上的棋型
        
        Args:
            line: 棋子序列（长度应>=5）
            player: 分析的玩家
        
        Returns:
            各种棋型的数量字典
        """
        patterns = {
            'FIVE': 0,
            'LIVE_FOUR': 0,
            'RUSH_FOUR': 0,
            'LIVE_THREE': 0,
            'SLEEP_THREE': 0,
            'LIVE_TWO': 0,
            'SLEEP_TWO': 0,
            'LIVE_ONE': 0,
        }
        
        if len(line) < 5:
            return patterns
        
        opponent = player.opponent()
        
        # 滑动窗口分析
        for i in range(len(line) - 4):
            window = line[i:i+5]
            pattern = PatternRecognizer._recognize_window(window, player, opponent)
            if pattern:
                patterns[pattern] += 1
        
        # 检查更长的窗口（6-9格，用于检测活四、活三等）
        for window_size in [6, 7, 8, 9]:
            if len(line) >= window_size:
                for i in range(len(line) - window_size + 1):
                    window = line[i:i+window_size]
                    pattern = PatternRecognizer._recognize_extended_window(
                        window, player, opponent
                    )
                    if pattern:
                        patterns[pattern] += 1
        
        return patterns
    
    @staticmethod
    def _recognize_window(window: List[Player], player: Player, 
                         opponent: Player) -> str:
        """识别5格窗口的棋型
        
        Args:
            window: 5个连续格子
            player: 当前玩家
            opponent: 对手
        
        Returns:
            棋型名称或空字符串
        """
        my_count = window.count(player)
        opp_count = window.count(opponent)
        empty_count = window.count(Player.EMPTY)
        
        # 五连
        if my_count == 5:
            return 'FIVE'
        
        # 有对手棋子，无法形成有效棋型
        if opp_count > 0:
            return ''
        
        # 四子
        if my_count == 4 and empty_count == 1:
            return 'RUSH_FOUR'
        
        # 三子
        if my_count == 3 and empty_count == 2:
            # 检查是否连续
            if PatternRecognizer._is_continuous(window, player, 3):
                return 'SLEEP_THREE'
        
        # 二子
        if my_count == 2 and empty_count == 3:
            if PatternRecognizer._is_continuous(window, player, 2):
                return 'SLEEP_TWO'
        
        return ''
    
    @staticmethod
    def _recognize_extended_window(window: List[Player], player: Player,
                                   opponent: Player) -> str:
        """识别扩展窗口的棋型（6-9格）
        
        主要用于识别活四、活三、活二等需要空格的棋型。
        """
        my_count = window.count(player)
        opp_count = window.count(opponent)
        empty_count = window.count(Player.EMPTY)
        
        # 有对手棋子，跳过
        if opp_count > 0:
            return ''
        
        # 活四：_XXXX_ 或 _XXX_X_
        if len(window) == 6 and my_count == 4 and empty_count == 2:
            if window[0] == Player.EMPTY and window[-1] == Player.EMPTY:
                return 'LIVE_FOUR'
        
        # 活三：_XXX_ 或 _XX_X_
        if len(window) in [5, 6] and my_count == 3 and empty_count >= 2:
            if window[0] == Player.EMPTY and window[-1] == Player.EMPTY:
                return 'LIVE_THREE'
        
        # 活二：_XX_
        if len(window) == 4 and my_count == 2 and empty_count == 2:
            if window[0] == Player.EMPTY and window[-1] == Player.EMPTY:
                return 'LIVE_TWO'
        
        return ''
    
    @staticmethod
    def _is_continuous(window: List[Player], player: Player, count: int) -> bool:
        """检查是否有连续的count个棋子"""
        continuous = 0
        max_continuous = 0
        
        for stone in window:
            if stone == player:
                continuous += 1
                max_continuous = max(max_continuous, continuous)
            else:
                continuous = 0
        
        return max_continuous >= count


class PositionEvaluator:
    """位置评估器
    
    为不同位置分配权重值。
    """
    
    def __init__(self, board_size: int = 15):
        """初始化位置评估器
        
        Args:
            board_size: 棋盘大小
        """
        self.board_size = board_size
        self.position_weights = self._generate_position_weights()
    
    def _generate_position_weights(self) -> List[List[float]]:
        """生成位置权重表
        
        中心区域权重高，边缘权重低。
        """
        weights = []
        center = self.board_size // 2
        
        for row in range(self.board_size):
            weight_row = []
            for col in range(self.board_size):
                # 计算到中心的曼哈顿距离
                distance = abs(row - center) + abs(col - center)
                
                # 距离越远权重越低
                weight = max(1.0, 10.0 - distance * 0.5)
                weight_row.append(weight)
            weights.append(weight_row)
        
        return weights
    
    def get_weight(self, row: int, col: int) -> float:
        """获取位置权重"""
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return self.position_weights[row][col]
        return 0.0


class BoardEvaluator:
    """棋盘评估器
    
    评估整个棋盘局面的优劣。
    """
    
    def __init__(self, board_size: int = 15):
        """初始化评估器
        
        Args:
            board_size: 棋盘大小
        """
        self.board_size = board_size
        self.position_evaluator = PositionEvaluator(board_size)
        self._line_cache = {}  # 缓存提取的线
        self._cache_version = -1  # 缓存版本号
    
    def evaluate(self, board: Board, player: Player) -> float:
        """评估棋盘对指定玩家的分数
        
        Args:
            board: 棋盘实例
            player: 评估的玩家
        
        Returns:
            评估分数（正数表示对player有利）
        """
        # 检查胜负
        if board.state.value == 'black_win':
            return 100000 if player == Player.BLACK else -100000
        elif board.state.value == 'white_win':
            return 100000 if player == Player.WHITE else -100000
        elif board.state.value == 'draw':
            return 0
        
        my_score = self._evaluate_player(board, player)
        opp_score = self._evaluate_player(board, player.opponent())
        
        # 我方分数 - 对方分数
        return my_score - opp_score
    
    def _evaluate_player(self, board: Board, player: Player) -> float:
        """评估单个玩家的分数"""
        total_score = 0.0
        
        # 遍历所有方向的线（使用缓存）
        lines = self._get_lines_cached(board)
        
        for line, positions in lines:
            # 识别棋型
            patterns = PatternRecognizer.analyze_line(line, player)
            
            # 计算分数
            for pattern_name, count in patterns.items():
                if count > 0:
                    pattern_score = PATTERN_SCORES.get(pattern_name, 0)
                    
                    # 添加位置权重
                    position_bonus = self._get_line_position_bonus(positions)
                    
                    total_score += pattern_score * count * (1.0 + position_bonus * 0.1)
        
        return total_score
    
    def _get_lines_cached(self, board: Board) -> List[Tuple[List[Player], List[Tuple[int, int]]]]:
        """获取缓存的线数据
        
        使用棋盘的move_count作为缓存版本号，避免重复计算。
        """
        current_version = len(board.history)
        
        # 如果缓存有效，直接返回
        if current_version == self._cache_version and current_version in self._line_cache:
            return self._line_cache[current_version]
        
        # 重新提取线
        lines = self._extract_all_lines(board)
        
        # 更新缓存（只保留最近3个版本）
        self._line_cache[current_version] = lines
        self._cache_version = current_version
        
        # 清理旧缓存
        if len(self._line_cache) > 3:
            old_keys = sorted(self._line_cache.keys())[:-3]
            for key in old_keys:
                del self._line_cache[key]
        
        return lines
    
    def _extract_all_lines(self, board: Board) -> List[Tuple[List[Player], List[Tuple[int, int]]]]:
        """提取棋盘上所有的线（横、竖、斜）
        
        Returns:
            (棋子序列, 位置坐标列表) 的列表
        """
        lines = []
        size = board.size
        
        # 横线
        for row in range(size):
            line = []
            positions = []
            for col in range(size):
                line.append(board.get_stone(row, col))
                positions.append((row, col))
            lines.append((line, positions))
        
        # 竖线
        for col in range(size):
            line = []
            positions = []
            for row in range(size):
                line.append(board.get_stone(row, col))
                positions.append((row, col))
            lines.append((line, positions))
        
        # 主对角线（左上到右下）
        for start_col in range(size):
            line = []
            positions = []
            row, col = 0, start_col
            while row < size and col < size:
                line.append(board.get_stone(row, col))
                positions.append((row, col))
                row += 1
                col += 1
            if len(line) >= 5:
                lines.append((line, positions))
        
        for start_row in range(1, size):
            line = []
            positions = []
            row, col = start_row, 0
            while row < size and col < size:
                line.append(board.get_stone(row, col))
                positions.append((row, col))
                row += 1
                col += 1
            if len(line) >= 5:
                lines.append((line, positions))
        
        # 副对角线（右上到左下）
        for start_col in range(size):
            line = []
            positions = []
            row, col = 0, start_col
            while row < size and col >= 0:
                line.append(board.get_stone(row, col))
                positions.append((row, col))
                row += 1
                col -= 1
            if len(line) >= 5:
                lines.append((line, positions))
        
        for start_row in range(1, size):
            line = []
            positions = []
            row, col = start_row, size - 1
            while row < size and col >= 0:
                line.append(board.get_stone(row, col))
                positions.append((row, col))
                row += 1
                col -= 1
            if len(line) >= 5:
                lines.append((line, positions))
        
        return lines
    
    def _get_line_position_bonus(self, positions: List[Tuple[int, int]]) -> float:
        """计算线的位置加成"""
        if not positions:
            return 0.0
        
        total_weight = sum(
            self.position_evaluator.get_weight(r, c) 
            for r, c in positions
        )
        return total_weight / len(positions) / 10.0  # 归一化


def evaluate_move(board: Board, row: int, col: int, player: Player) -> float:
    """快速评估单个着法的价值
    
    Args:
        board: 棋盘实例
        row, col: 着法位置
        player: 玩家
    
    Returns:
        着法评估分数
    """
    # 创建临时棋盘
    temp_board = board.copy()
    temp_board.place_stone(row, col, player)
    
    # 评估
    evaluator = BoardEvaluator(board.size)
    return evaluator.evaluate(temp_board, player)
