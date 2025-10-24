/**
 * 贪吃蛇游戏
 */

class SnakeGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.scoreDisplay = document.getElementById('score');

        this.gridSize = 20;
        this.score = 0;
        this.gameOver = false;
        this.paused = false;

        // 蛇
        this.snake = [
            { x: 10, y: 10 }
        ];
        this.direction = { x: 1, y: 0 };
        this.nextDirection = { x: 1, y: 0 };

        // 食物
        this.food = this.generateFood();

        // 输入
        this.keys = {};

        this.bindEvents();
        this.gameLoop();
    }

    bindEvents() {
        window.addEventListener('keydown', (e) => {
            if (e.key === ' ') {
                e.preventDefault();
                this.paused = !this.paused;
                return;
            }

            const keyMap = {
                'ArrowUp': { x: 0, y: -1 },
                'ArrowDown': { x: 0, y: 1 },
                'ArrowLeft': { x: -1, y: 0 },
                'ArrowRight': { x: 1, y: 0 },
                'w': { x: 0, y: -1 },
                's': { x: 0, y: 1 },
                'a': { x: -1, y: 0 },
                'd': { x: 1, y: 0 }
            };

            if (keyMap[e.key]) {
                const newDir = keyMap[e.key];
                // 防止蛇向相反方向移动
                if (!(this.direction.x === -newDir.x && this.direction.y === -newDir.y)) {
                    this.nextDirection = newDir;
                }
            }
        });
    }

    generateFood() {
        let food;
        let collision;
        do {
            collision = false;
            food = {
                x: Math.floor(Math.random() * (this.canvas.width / this.gridSize)),
                y: Math.floor(Math.random() * (this.canvas.height / this.gridSize))
            };
            for (let segment of this.snake) {
                if (segment.x === food.x && segment.y === food.y) {
                    collision = true;
                    break;
                }
            }
        } while (collision);
        return food;
    }

    update() {
        if (this.paused || this.gameOver) return;

        this.direction = this.nextDirection;

        // 新的蛇头
        const head = {
            x: this.snake[0].x + this.direction.x,
            y: this.snake[0].y + this.direction.y
        };

        // 检查边界碰撞
        if (head.x < 0 || head.x >= this.canvas.width / this.gridSize ||
            head.y < 0 || head.y >= this.canvas.height / this.gridSize) {
            this.endGame();
            return;
        }

        // 检查自身碰撞
        for (let segment of this.snake) {
            if (head.x === segment.x && head.y === segment.y) {
                this.endGame();
                return;
            }
        }

        this.snake.unshift(head);

        // 检查是否吃到食物
        if (head.x === this.food.x && head.y === this.food.y) {
            this.score += 10;
            this.scoreDisplay.textContent = `分数: ${this.score}`;
            this.food = this.generateFood();
        } else {
            this.snake.pop();
        }
    }

    draw() {
        // 清空画布
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制蛇
        this.ctx.fillStyle = '#0F0';
        for (let i = 0; i < this.snake.length; i++) {
            const segment = this.snake[i];
            if (i === 0) {
                this.ctx.fillStyle = '#FFF';
            } else {
                this.ctx.fillStyle = '#0F0';
            }
            this.ctx.fillRect(
                segment.x * this.gridSize + 1,
                segment.y * this.gridSize + 1,
                this.gridSize - 2,
                this.gridSize - 2
            );
        }

        // 绘制食物
        this.ctx.fillStyle = '#F00';
        this.ctx.fillRect(
            this.food.x * this.gridSize + 1,
            this.food.y * this.gridSize + 1,
            this.gridSize - 2,
            this.gridSize - 2
        );

        // 绘制网格（可选）
        this.ctx.strokeStyle = '#222';
        this.ctx.lineWidth = 0.5;
        for (let i = 0; i <= this.canvas.width; i += this.gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(i, 0);
            this.ctx.lineTo(i, this.canvas.height);
            this.ctx.stroke();
        }
        for (let i = 0; i <= this.canvas.height; i += this.gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, i);
            this.ctx.lineTo(this.canvas.width, i);
            this.ctx.stroke();
        }
    }

    endGame() {
        this.gameOver = true;
        if (window.parent && window.parent.gameFinished) {
            window.parent.gameFinished(this.score, 1);
        }
    }

    gameLoop() {
        this.update();
        this.draw();
        setTimeout(() => this.gameLoop(), 100);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new SnakeGame();
});
