// 打砖块游戏逻辑
class BreakoutGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // 游戏元素
        this.paddle = {
            x: this.canvas.width / 2 - 40,
            y: this.canvas.height - 30,
            width: 80,
            height: 15,
            speed: 7
        };
        
        this.ball = {
            x: this.canvas.width / 2,
            y: this.canvas.height - 50,
            radius: 6,
            velocityX: 0,
            velocityY: 0,
            speed: 4,
            launched: false
        };
        
        this.bricks = [];
        this.createBricks();
        
        this.score = 0;
        this.lives = 3;
        this.gameOver = false;
        this.won = false;
        
        this.keys = {};
        
        // 事件监听
        document.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;
            if (e.key === ' ') {
                e.preventDefault();
                this.launchBall();
            }
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });
        
        this.canvas.addEventListener('click', () => this.launchBall());
        
        this.gameLoop();
    }
    
    createBricks() {
        const brickWidth = 60;
        const brickHeight = 15;
        const padding = 10;
        const rows = 4;
        const cols = 9;
        const offsetTop = 30;
        const offsetLeft = (this.canvas.width - (cols * (brickWidth + padding))) / 2;
        
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'];
        
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                this.bricks.push({
                    x: offsetLeft + c * (brickWidth + padding),
                    y: offsetTop + r * (brickHeight + padding),
                    width: brickWidth,
                    height: brickHeight,
                    color: colors[r],
                    destroyed: false
                });
            }
        }
        
        document.getElementById('bricks').textContent = this.bricks.length;
    }
    
    launchBall() {
        if (!this.ball.launched && !this.gameOver && !this.won) {
            this.ball.launched = true;
            const angle = (Math.random() - 0.5) * Math.PI / 3;
            this.ball.velocityX = this.ball.speed * Math.sin(angle);
            this.ball.velocityY = -this.ball.speed * Math.cos(angle);
        }
    }
    
    update() {
        if (this.gameOver || this.won) return;
        
        // 移动挡板
        if (this.keys['ArrowLeft'] || this.keys['a']) {
            this.paddle.x = Math.max(0, this.paddle.x - this.paddle.speed);
        }
        if (this.keys['ArrowRight'] || this.keys['d']) {
            this.paddle.x = Math.min(this.canvas.width - this.paddle.width, this.paddle.x + this.paddle.speed);
        }
        
        // 移动球
        if (this.ball.launched) {
            this.ball.x += this.ball.velocityX;
            this.ball.y += this.ball.velocityY;
            
            // 边界碰撞
            if (this.ball.x - this.ball.radius < 0 || this.ball.x + this.ball.radius > this.canvas.width) {
                this.ball.velocityX *= -1;
                this.ball.x = Math.max(this.ball.radius, Math.min(this.canvas.width - this.ball.radius, this.ball.x));
            }
            
            if (this.ball.y - this.ball.radius < 0) {
                this.ball.velocityY *= -1;
            }
            
            // 游戏结束
            if (this.ball.y > this.canvas.height) {
                this.lives--;
                document.getElementById('lives').textContent = this.lives;
                if (this.lives <= 0) {
                    this.gameOver = true;
                } else {
                    this.resetBall();
                }
            }
            
            // 挡板碰撞
            if (this.checkPaddleCollision()) {
                this.ball.velocityY *= -1;
                this.ball.y = this.paddle.y - this.ball.radius;
                const paddleCenter = this.paddle.x + this.paddle.width / 2;
                const ballToCenter = (this.ball.x - paddleCenter) / (this.paddle.width / 2);
                this.ball.velocityX = ballToCenter * this.ball.speed;
            }
            
            // 砖块碰撞
            for (let brick of this.bricks) {
                if (!brick.destroyed && this.checkBrickCollision(brick)) {
                    brick.destroyed = true;
                    this.score += 10;
                    document.getElementById('score').textContent = this.score;
                    
                    // 计算碰撞面
                    const dx = (this.ball.x) - (brick.x + brick.width / 2);
                    const dy = (this.ball.y) - (brick.y + brick.height / 2);
                    
                    if (Math.abs(dx) > Math.abs(dy)) {
                        this.ball.velocityX *= -1;
                    } else {
                        this.ball.velocityY *= -1;
                    }
                    
                    // 检查是否赢了
                    if (this.bricks.every(b => b.destroyed)) {
                        this.won = true;
                        this.gameFinished(this.score, 1);
                    }
                    break;
                }
            }
        } else {
            // 球跟着挡板
            this.ball.x = this.paddle.x + this.paddle.width / 2;
            this.ball.y = this.paddle.y - this.ball.radius - 5;
        }
    }
    
    checkPaddleCollision() {
        return this.ball.x > this.paddle.x &&
               this.ball.x < this.paddle.x + this.paddle.width &&
               this.ball.y + this.ball.radius >= this.paddle.y &&
               this.ball.y - this.ball.radius <= this.paddle.y + this.paddle.height;
    }
    
    checkBrickCollision(brick) {
        return this.ball.x > brick.x &&
               this.ball.x < brick.x + brick.width &&
               this.ball.y > brick.y &&
               this.ball.y < brick.y + brick.height;
    }
    
    resetBall() {
        this.ball.launched = false;
        this.ball.velocityX = 0;
        this.ball.velocityY = 0;
    }
    
    draw() {
        // 背景
        this.ctx.fillStyle = '#0f3460';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制砖块
        for (let brick of this.bricks) {
            if (!brick.destroyed) {
                this.ctx.fillStyle = brick.color;
                this.ctx.fillRect(brick.x, brick.y, brick.width, brick.height);
                this.ctx.strokeStyle = '#fff';
                this.ctx.lineWidth = 1;
                this.ctx.strokeRect(brick.x, brick.y, brick.width, brick.height);
            }
        }
        
        // 绘制挡板
        this.ctx.fillStyle = '#00d4ff';
        this.ctx.fillRect(this.paddle.x, this.paddle.y, this.paddle.width, this.paddle.height);
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(this.paddle.x, this.paddle.y, this.paddle.width, this.paddle.height);
        
        // 绘制球
        this.ctx.fillStyle = '#FFD700';
        this.ctx.beginPath();
        this.ctx.arc(this.ball.x, this.ball.y, this.ball.radius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 提示信息
        if (!this.ball.launched) {
            this.ctx.fillStyle = '#FFD700';
            this.ctx.font = 'bold 16px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('按空格或点击发射', this.canvas.width / 2, 50);
        }
        
        // 游戏结束
        if (this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#FF0000';
            this.ctx.font = 'bold 40px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏结束', this.canvas.width / 2, this.canvas.height / 2 - 30);
            
            this.ctx.fillStyle = '#FFD700';
            this.ctx.font = 'bold 24px Arial';
            this.ctx.fillText('得分: ' + this.score, this.canvas.width / 2, this.canvas.height / 2 + 20);
            
            this.gameFinished(this.score, 1);
        }
        
        // 赢了
        if (this.won) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#00FF00';
            this.ctx.font = 'bold 40px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('恭喜！', this.canvas.width / 2, this.canvas.height / 2 - 30);
            
            this.ctx.fillStyle = '#FFD700';
            this.ctx.font = 'bold 24px Arial';
            this.ctx.fillText('最终得分: ' + this.score, this.canvas.width / 2, this.canvas.height / 2 + 20);
        }
    }
    
    gameFinished(score, level) {
        if (window.parent && window.parent.gameFinished) {
            window.parent.gameFinished(score, level);
        }
    }
    
    gameLoop() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.gameLoop());
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new BreakoutGame();
});
