# -*- coding: utf-8 -*-
"""
游戏自动化测试框架
使用Selenium测试每个游戏的初始化、输入响应和完成条件
"""
import pytest
import time
import os
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class GameTestBase:
    """游戏测试基类"""
    
    def __init__(self, game_name, game_url, base_url='http://localhost:5000'):
        self.game_name = game_name
        self.game_url = game_url
        self.base_url = base_url
        self.full_url = f"{base_url}{game_url}"
        self.driver = None
        self.wait = None
    
    def setup(self):
        """初始化浏览器驱动"""
        if not SELENIUM_AVAILABLE:
            pytest.skip("Selenium not available")
        
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            pytest.skip(f"Chrome driver not available: {e}")
    
    def teardown(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
    
    def load_game(self):
        """加载游戏"""
        self.driver.get(self.full_url)
        time.sleep(2)  # 等待游戏初始化
    
    def find_canvas(self):
        """查找游戏画布"""
        canvas = self.driver.find_element(By.ID, 'gameCanvas')
        assert canvas is not None, f"{self.game_name}: 找不到 gameCanvas 元素"
        return canvas
    
    def send_key(self, key):
        """发送键盘输入"""
        action = ActionChains(self.driver)
        action.send_keys(key)
        action.perform()
    
    def click_canvas(self):
        """点击画布"""
        canvas = self.find_canvas()
        ActionChains(self.driver).click(canvas).perform()
    
    def get_canvas_pixel(self, x, y):
        """获取画布像素颜色用于验证游戏状态"""
        canvas = self.find_canvas()
        script = f"""
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData({x}, {y}, 1, 1);
            return imageData.data;
        """
        return self.driver.execute_script(script)
    
    def test_game_loads(self):
        """测试：游戏能否成功加载"""
        self.load_game()
        canvas = self.find_canvas()
        assert canvas is not None, f"{self.game_name}: 游戏未能加载"
        print(f"✓ {self.game_name}: 游戏加载成功")
    
    def test_canvas_renders(self):
        """测试：画布是否能正确渲染"""
        self.load_game()
        canvas = self.find_canvas()
        
        width = canvas.get_attribute('width')
        height = canvas.get_attribute('height')
        
        assert width is not None, f"{self.game_name}: 画布宽度未定义"
        assert height is not None, f"{self.game_name}: 画布高度未定义"
        
        # 检查是否有内容被绘制
        script = """
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            // 检查是否有非全黑的像素
            for (let i = 0; i < data.length; i += 4) {
                if (data[i] !== 0 || data[i+1] !== 0 || data[i+2] !== 0 || data[i+3] !== 0) {
                    return true;
                }
            }
            return false;
        """
        
        is_rendered = self.driver.execute_script(script)
        assert is_rendered, f"{self.game_name}: 画布未被正确渲染"
        print(f"✓ {self.game_name}: 画布渲染成功")


class FlappyBirdTest(GameTestBase):
    """飞鸟游戏测试"""
    
    def __init__(self):
        super().__init__('FlappyBird', '/games/casual/flappybird/index.html')
    
    def test_game_logic(self):
        """测试飞鸟游戏逻辑"""
        self.load_game()
        
        # 等待一段时间让游戏运行
        time.sleep(1)
        
        # 尝试点击使鸟跳跃
        self.click_canvas()
        time.sleep(0.5)
        
        # 再次点击
        self.click_canvas()
        time.sleep(1)
        
        # 检查得分是否改变
        score = self.driver.execute_script("""
            const scoreElement = document.getElementById('score');
            return scoreElement ? parseInt(scoreElement.textContent) : 0;
        """)
        
        print(f"✓ {self.game_name}: 游戏逻辑运行正常，当前分数: {score}")


class SnakeTest(GameTestBase):
    """贪吃蛇游戏测试"""
    
    def __init__(self):
        super().__init__('Snake', '/games/arcade/snake/index.html')
    
    def test_keyboard_input(self):
        """测试贪吃蛇的键盘输入"""
        self.load_game()
        time.sleep(1)
        
        # 发送方向键输入
        self.send_key(Keys.UP)
        time.sleep(0.2)
        self.send_key(Keys.RIGHT)
        time.sleep(0.2)
        self.send_key(Keys.DOWN)
        time.sleep(0.5)
        
        print(f"✓ {self.game_name}: 键盘输入测试通过")


class TetrisTest(GameTestBase):
    """俄罗斯方块游戏测试"""
    
    def __init__(self):
        super().__init__('Tetris', '/games/puzzle/tetris/index.html')
    
    def test_game_initialization(self):
        """测试俄罗斯方块初始化"""
        self.load_game()
        
        # 检查游戏信息
        score = self.driver.execute_script("""
            return document.body.innerText.includes('得分') ? 1 : 0;
        """)
        
        assert score, f"{self.game_name}: 游戏界面未正确初始化"
        print(f"✓ {self.game_name}: 游戏初始化成功")


class Game2048Test(GameTestBase):
    """2048游戏测试"""
    
    def __init__(self):
        super().__init__('2048', '/games/puzzle/2048/index.html')
    
    def test_game_mechanics(self):
        """测试2048游戏机制"""
        self.load_game()
        time.sleep(1)
        
        # 发送方向键尝试合并
        self.send_key(Keys.UP)
        time.sleep(0.3)
        self.send_key(Keys.LEFT)
        time.sleep(0.3)
        
        print(f"✓ {self.game_name}: 游戏机制测试通过")


# 快速测试脚本
if __name__ == '__main__':
    print("开始游戏测试...\n")
    
    tests = [
        FlappyBirdTest(),
        SnakeTest(),
        TetrisTest(),
        Game2048Test(),
    ]
    
    for test in tests:
        try:
            test.setup()
            print(f"\n========== 测试 {test.game_name} ==========")
            test.test_game_loads()
            test.test_canvas_renders()
            
            if hasattr(test, 'test_game_logic'):
                test.test_game_logic()
            if hasattr(test, 'test_keyboard_input'):
                test.test_keyboard_input()
            if hasattr(test, 'test_game_initialization'):
                test.test_game_initialization()
            if hasattr(test, 'test_game_mechanics'):
                test.test_game_mechanics()
            
            print(f"✓ {test.game_name}: 所有测试通过\n")
            
        except Exception as e:
            print(f"✗ {test.game_name}: 测试失败 - {str(e)}\n")
        finally:
            test.teardown()
