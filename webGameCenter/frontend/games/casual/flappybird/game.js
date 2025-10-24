// Flappy Bird 游戏逻辑
class FlappyBirdGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // 游戏参数
        this.bird = {
            x: 100,
            y: 300,
            width: 30,
            height: 24,
            velocity: 0,
            gravity: 0.5,
            jump: -10
        };
        
        this.pipes = [];
        this.pipeWidth = 60;
        this.pipeGap = 120;
        this.pipeDistance = 200;
        this.score = 0;
        this.gameOver = false;
        this.hasReported = false;  // 标志：是否已报告游戏结束
        
        // 创建第一根管道
        this.createPipe();
        
        // 事件监听
        document.addEventListener('click', () => this.jump());
        document.addEventListener('keydown', (e) => {
            if (e.key === ' ') {
                e.preventDefault();
                this.jump();
            }
        });
        
        this.gameLoop();
    }
    
    jump() {
        if (!this.gameOver) {
            this.bird.velocity = this.bird.jump;
        }
    }
    
    createPipe() {
        const minY = 50;
        const maxY = this.canvas.height - this.pipeGap - 100;
        const randomY = Math.random() * (maxY - minY) + minY;
        
        this.pipes.push({
            x: this.canvas.width,
            y: randomY,
            scored: false
        });
    }
    
    update() {
        if (this.gameOver) return;
        
        // 更新鸟的位置
        this.bird.velocity += this.bird.gravity;
        this.bird.y += this.bird.velocity;
        
        // 检查碰撞边界
        if (this.bird.y + this.bird.height > this.canvas.height || this.bird.y < 0) {
            this.gameOver = true;
        }
        
        // 更新管道
        for (let i = this.pipes.length - 1; i >= 0; i--) {
            this.pipes[i].x -= 4;
            
            // 检查是否通过管道（加分）
            if (!this.pipes[i].scored && this.pipes[i].x + this.pipeWidth < this.bird.x) {
                this.pipes[i].scored = true;
                this.score++;
                document.getElementById('score').textContent = this.score;
            }
            
            // 检查碰撞
            if (this.checkPipeCollision(this.pipes[i])) {
                this.gameOver = true;
            }
            
            // 删除离屏管道
            if (this.pipes[i].x + this.pipeWidth < 0) {
                this.pipes.splice(i, 1);
            }
        }
        
        // 创建新管道
        if (this.pipes.length === 0 || this.pipes[this.pipes.length - 1].x < this.canvas.width - this.pipeDistance) {
            this.createPipe();
        }
    }
    
    checkPipeCollision(pipe) {
        // 检查与上管道碰撞
        if (this.bird.x < pipe.x + this.pipeWidth && 
            this.bird.x + this.bird.width > pipe.x &&
            this.bird.y < pipe.y) {
            return true;
        }
        
        // 检查与下管道碰撞
        if (this.bird.x < pipe.x + this.pipeWidth && 
            this.bird.x + this.bird.width > pipe.x &&
            this.bird.y + this.bird.height > pipe.y + this.pipeGap) {
            return true;
        }
        
        return false;
    }
    
    draw() {
        // 背景
        this.ctx.fillStyle = '#87CEEB';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 地面
        this.ctx.fillStyle = '#228B22';
        this.ctx.fillRect(0, this.canvas.height - 40, this.canvas.width, 40);
        
        // 鸟
        this.ctx.fillStyle = '#FFD700';
        this.ctx.beginPath();
        this.ctx.arc(this.bird.x + this.bird.width/2, this.bird.y + this.bird.height/2, this.bird.width/2, 0, Math.PI*2);
        this.ctx.fill();
        
        // 鸟的眼睛
        this.ctx.fillStyle = '#000';
        this.ctx.beginPath();
        this.ctx.arc(this.bird.x + 20, this.bird.y + 8, 3, 0, Math.PI*2);
        this.ctx.fill();
        
        // 管道
        this.ctx.fillStyle = '#228B22';
        for (let pipe of this.pipes) {
            // 上管道
            this.ctx.fillRect(pipe.x, 0, this.pipeWidth, pipe.y);
            // 下管道
            this.ctx.fillRect(pipe.x, pipe.y + this.pipeGap, this.pipeWidth, this.canvas.height - pipe.y - this.pipeGap);
        }
        
        // 游戏结束
        if (this.gameOver && !this.hasReported) {
            this.hasReported = true;
            
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#FFF';
            this.ctx.font = 'bold 30px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏结束', this.canvas.width/2, this.canvas.height/2 - 20);
            this.ctx.font = 'bold 20px Arial';
            this.ctx.fillText('得分: ' + this.score, this.canvas.width/2, this.canvas.height/2 + 20);
            
            // 延迟报告结果，避免重复调用
            setTimeout(() => this.gameFinished(this.score, 1), 500);
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
    new FlappyBirdGame();
});
