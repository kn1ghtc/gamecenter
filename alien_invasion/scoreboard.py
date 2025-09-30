import pygame.font
from pygame.sprite import Group
from ship import Ship

class Scoreboard:
    """显示得分信息的类"""

    def __init__(self, ai_game):
        """初始化得分涉及的属性"""
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = ai_game.screen.get_rect()
        self.settings = ai_game.settings
        self.stats = ai_game.stats

        # 显示得分信息时使用的字体设置
        self.text_color = (30, 30, 30)
        self.font = pygame.font.SysFont("simhei", 48)

        # 准备初始得分图像
        self.prep_score()
        self.prep_high_score()
        self.prep_level()
        self.prep_ships()

    def prep_score(self):
        """将得分转换为渲染的图像"""
        rounded_score_1 = round(self.stats.score[0], -1)
        score_str_1 = f"P1 score: {rounded_score_1:,}"
        self.score_image_1 = self.font.render(score_str_1, True, self.text_color, self.settings.bg_color)
        rounded_score_2 = round(self.stats.score[1], -1)
        score_str_2 = f"P2 score: {rounded_score_2:,}"
        self.score_image_2 = self.font.render(score_str_2, True, self.text_color, self.settings.bg_color)

        # Display the score at the top right of the screen.
        self.score_rect_1 = self.score_image_1.get_rect()
        self.score_rect_1.right = self.screen_rect.right - 20
        self.score_rect_1.top = 20
        self.score_rect_2 = self.score_image_2.get_rect()
        self.score_rect_2.right = self.screen_rect.right - 20
        self.score_rect_2.top = self.score_rect_1.bottom + 10

    def prep_high_score(self):
        """将最高得分转换为渲染的图像"""
        high_score = round(self.stats.high_score, -1)
        high_score_str = f"high score: {high_score:,}"
        self.high_score_image = self.font.render(high_score_str, True, self.text_color, self.settings.bg_color)

        # 将最高得分放在屏幕顶部中央
        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.centerx = self.screen_rect.centerx
        self.high_score_rect.top = self.score_rect_1.top

    def check_high_score(self):
        """检查是否诞生了新的最高得分"""
        if max(self.stats.score) > self.stats.high_score:
            self.stats.high_score = max(self.stats.score)
            self.prep_high_score()

    def prep_level(self):
        level_str = f" level : {self.stats.level}"
        self.level_image = self.font.render(level_str, True, self.text_color, self.settings.bg_color)

        # Position the level below the score.
        self.level_rect = self.level_image.get_rect()
        self.level_rect.right = self.score_rect_1.right
        self.level_rect.top = self.score_rect_2.bottom + 10

    def prep_ships(self):
        """Show how many ships are left."""
        self.ships = [Group(), Group()]
        for player in range(2):
            for ship_number in range(self.stats.ships_left[player]):
                ship = Ship(self.ai_game, player + 1)
                ship.rect.x = 10 + ship_number * ship.rect.width
                ship.rect.y = 10 + player * (ship.rect.height + 10)
                self.ships[player].add(ship)

    def show_score(self):
        """在屏幕上显示得分"""
        self.screen.blit(self.score_image_1, self.score_rect_1)
        self.screen.blit(self.score_image_2, self.score_rect_2)
        self.screen.blit(self.high_score_image, self.high_score_rect)
        self.screen.blit(self.level_image, self.level_rect)
        for ship in self.ships:
            ship.draw(self.screen)
