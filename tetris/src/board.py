from .settings import BOARD_WIDTH, BOARD_HEIGHT

class Board:
    """
    游戏板类

    属性:
        grid: 游戏板网格
        width: 宽度
        height: 高度
    """

    def __init__(self):
        """初始化空游戏板"""
        self.width = BOARD_WIDTH
        self.height = BOARD_HEIGHT
        self.grid = [[None for x in range(self.width)] for y in range(self.height)]

    def is_valid_move(self, tetromino, x, y):
        """
        检查移动是否有效

        参数:
            tetromino: Tetromino对象
            x: 目标x坐标
            y: 目标y坐标

        返回:
            bool: 移动是否有效
        """
        positions = tetromino.get_positions()
        for px, py in positions:
            if (px < 0 or px >= self.width or
                py < 0 or py >= self.height or
                self.grid[py][px] is not None):
                return False
        return True

    def clear_lines(self):
        """
        清除已填满的行并计算分数

        返回:
            int: 清除的行数
        """
        lines_cleared = 0
        y = self.height - 1
        while y >= 0:
            if all(cell is not None for cell in self.grid[y]):
                lines_cleared += 1
                # 将上方所有行下移
                for y2 in range(y, 0, -1):
                    self.grid[y2] = self.grid[y2-1][:]
                self.grid[0] = [None] * self.width
            else:
                y -= 1
        return lines_cleared
