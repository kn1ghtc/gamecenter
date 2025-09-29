import pygame
from .settings import *
from .tetromino import Tetromino
from .board import Board

class TetrisGame:
    """
    俄罗斯方块主游戏类

    管理游戏主循环、渲染和用户输入
    """

    def __init__(self):
        """初始化游戏"""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("俄罗斯方块")

        self.clock = pygame.time.Clock()
        self.board = Board()
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.level = 'EASY'
        self.game_over = False

    def start_game(self):
        """开始新游戏"""
        self.board = Board()
        self.current_piece = Tetromino()
        self.next_piece = Tetromino()
        self.score = 0
        self.game_over = False

    def handle_input(self):
        """处理用户输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.move_piece(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_piece(1, 0)
                elif event.key == pygame.K_DOWN:
                    self.move_piece(0, 1)
                elif event.key == pygame.K_UP:
                    self.rotate_piece()

        return True

    def move_piece(self, dx, dy):
        """
        移动当前方块

        参数:
            dx: x方向移动距离
            dy: y方向移动距离
        """
        if self.board.is_valid_move(self.current_piece,
                                  self.current_piece.x + dx,
                                  self.current_piece.y + dy):
            self.current_piece.x += dx
            self.current_piece.y += dy

    def rotate_piece(self):
        """旋转当前方块"""
        rotated_shape = self.current_piece.rotate()
        # TODO: 检查旋转是否有效并执行

    def update(self):
        """更新游戏状态"""
        # 方块自动下落
        self.move_piece(0, 1)

        # 检查是否需要固定方块
        if not self.board.is_valid_move(self.current_piece,
                                      self.current_piece.x,
                                      self.current_piece.y + 1):
            # 固定当前方块前检查位置是否有效
            positions = self.current_piece.get_positions()
            for x, y in positions:
                if 0 <= x < self.board.width and 0 <= y < self.board.height:
                    self.board.grid[y][x] = self.current_piece.color

            # 清除完整行并更新分数
            lines_cleared = self.board.clear_lines()
            self.score += lines_cleared * SCORE_PER_LINE * \
                         DIFFICULTY_LEVELS[self.level]['score_multiplier']

            # 生成新方块并将其放置在顶部中间
            self.current_piece = self.next_piece
            self.current_piece.x = self.board.width // 2 - len(self.current_piece.shape[0]) // 2
            self.current_piece.y = 0
            self.next_piece = Tetromino()

            # 检查游戏是否结束
            if not self.board.is_valid_move(self.current_piece,
                                          self.current_piece.x,
                                          self.current_piece.y):
                self.game_over = True
    def draw(self):
        """渲染游戏画面"""
        self.screen.fill(COLORS['BLACK'])

        # 绘制游戏板边框
        board_rect = pygame.Rect(
            BOARD_OFFSET_X - 2,
            BOARD_OFFSET_Y - 2,
            self.board.width * BLOCK_SIZE + 4,
            self.board.height * BLOCK_SIZE + 4
        )
        pygame.draw.rect(self.screen, COLORS['WHITE'], board_rect, 2)

        # 绘制游戏板上的方块
        for y in range(self.board.height):
            for x in range(self.board.width):
                if self.board.grid[y][x]:
                    color = self.board.grid[y][x]
                    pygame.draw.rect(
                        self.screen,
                        COLORS[color],
                        (
                            BOARD_OFFSET_X + x * BLOCK_SIZE,
                            BOARD_OFFSET_Y + y * BLOCK_SIZE,
                            BLOCK_SIZE,
                            BLOCK_SIZE
                        )
                    )

        # 绘制当前方块
        if self.current_piece:
            positions = self.current_piece.get_positions()
            for x, y in positions:
                pygame.draw.rect(
                    self.screen,
                    COLORS[self.current_piece.color],
                    (
                        BOARD_OFFSET_X + x * BLOCK_SIZE,
                        BOARD_OFFSET_Y + y * BLOCK_SIZE,
                        BLOCK_SIZE,
                        BLOCK_SIZE
                    )
                )

        # 绘制下一个方块预览
        preview_x = BOARD_OFFSET_X + (self.board.width + 2) * BLOCK_SIZE
        preview_y = BOARD_OFFSET_Y

        # 预览区域边框
        preview_rect = pygame.Rect(
            preview_x - 2,
            preview_y - 2,
            6 * BLOCK_SIZE + 4,
            6 * BLOCK_SIZE + 4
        )
        pygame.draw.rect(self.screen, COLORS['WHITE'], preview_rect, 2)

        # 绘制预览方块
        if self.next_piece:
            for y, row in enumerate(self.next_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(
                            self.screen,
                            COLORS[self.next_piece.color],
                            (
                                preview_x + x * BLOCK_SIZE,
                                preview_y + y * BLOCK_SIZE,
                                BLOCK_SIZE,
                                BLOCK_SIZE
                            )
                        )

        # 绘制分数和等级
        font = pygame.font.Font(None, 36)

        # 分数显示
        score_text = font.render(f'Score: {self.score}', True, COLORS['WHITE'])
        self.screen.blit(
            score_text,
            (preview_x, preview_y + 8 * BLOCK_SIZE)
        )

        # 等级显示
        level_text = font.render(f'Level: {self.level}', True, COLORS['WHITE'])
        self.screen.blit(
            level_text,
            (preview_x, preview_y + 9.5 * BLOCK_SIZE)
        )

        # 游戏结束显示
        if self.game_over:
            game_over_font = pygame.font.Font(None, 48)
            game_over_text = game_over_font.render('GAME OVER', True, COLORS['RED'])
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(game_over_text, text_rect)

        pygame.display.flip()

    def run(self):
        """运行游戏主循环"""
        self.start_game()
        running = True

        while running:
            running = self.handle_input()

            if not self.game_over:
                self.update()

            self.draw()
            self.clock.tick(60)

        pygame.quit()
