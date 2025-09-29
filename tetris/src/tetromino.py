import random

class Tetromino:
    """
    俄罗斯方块形状类

    属性:
        shape: 方块形状矩阵
        color: 方块颜色
        x: 当前x坐标
        y: 当前y坐标
    """

    def __init__(self):
        # Define shapes and their corresponding colors using color names
        self.SHAPES = {
            'I': ([[1, 1, 1, 1]], 'CYAN'),
            'O': ([[1, 1],
                  [1, 1]], 'YELLOW'),
            'T': ([[0, 1, 0],
                  [1, 1, 1]], 'PURPLE'),
            'L': ([[1, 0, 0],
                  [1, 1, 1]], 'ORANGE'),
            'J': ([[0, 0, 1],
                  [1, 1, 1]], 'BLUE'),
            'S': ([[0, 1, 1],
                  [1, 1, 0]], 'GREEN'),
            'Z': ([[1, 1, 0],
                  [0, 1, 1]], 'RED')
        }

        # Randomly select a shape and its color
        shape_name = random.choice(list(self.SHAPES.keys()))
        self.shape = self.SHAPES[shape_name][0]
        self.color = self.SHAPES[shape_name][1]  # Now storing color name instead of RGB

        # Initial position
        self.x = 0
        self.y = 0
    def rotate(self):
        """
        顺时针旋转方块

        返回:
            rotated_shape: 旋转后的形状矩阵
        """
        return list(zip(*self.shape[::-1]))

    def get_positions(self):
        """
        获取方块所有格子的位置

        返回:
            list: 包含所有格子坐标的列表 [(x1,y1), (x2,y2),...]
        """
        positions = []
        for i in range(len(self.shape)):
            for j in range(len(self.shape[i])):
                if self.shape[i][j]:
                    positions.append((self.x + j, self.y + i))
        return positions
