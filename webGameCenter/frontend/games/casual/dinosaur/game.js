// 恐龙跳跃游戏逻辑
class DinosaurGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // 恐龙
        this.dinosaur = {
            x: 50,
            y: this.canvas.height - 100,
            width: 40,
            height: 50,
            velocityY: 0,
            jumping: false,
            jumpPower: 15,
            gravity: 0.6
        };
        
        this.groundY = this.canvas.height - 50;
        this.obstacles = [];
        this.clouds = [];
        this.score = 0;
        this.bestScore = localStorage.getItem('dino_best_score') || 0;
        this.gameOver = false;
        this.gameSpeed = 1;
        this.spawnRate = 150;
        this.spawnCounter = 0;
        
        // 创建云
        for (let i = 0; i < 3; i++) {
            this.clouds.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * 100 + 20,
                width: 80,
                height: 30,
                speed: Math.random() * 0.5 + 0.5
            });
        }
        
        // 事件监听
        document.addEventListener('keydown', (e) => {
            if ((e.key === ' ' || e.key === 'ArrowUp') && !this.gameOver) {
                e.preventDefault();
                this.jump();
            }
            if (e.key === 'r' || e.key === 'R') {
                location.reload();
            }
        });
        
        this.canvas.addEventListener('click', () => {
            if (!this.gameOver) this.jump();
        });
        
        document.getElementById('bestScore').textContent = this.bestScore;
        this.gameLoop();
    }
    
    jump() {
        if (!this.dinosaur.jumping) {
            this.dinosaur.velocityY = this.dinosaur.jumpPower;
            this.dinosaur.jumping = true;
        }
    }
    
    update() {
        if (this.gameOver) return;
        
        // 更新恐龙
        this.dinosaur.velocityY -= this.dinosaur.gravity;
        this.dinosaur.y -= this.dinosaur.velocityY;
        
        if (this.dinosaur.y >= this.groundY) {
            this.dinosaur.y = this.groundY;
            this.dinosaur.jumping = false;
            this.dinosaur.velocityY = 0;
        }
        
        // 生成障碍物
        this.spawnCounter++;
        if (this.spawnCounter > this.spawnRate - this.score / 100) {
            this.spawnObstacle();
            this.spawnCounter = 0;
        }
        
        // 更新障碍物
        for (let i = this.obstacles.length - 1; i >= 0; i--) {
            this.obstacles[i].x -= 6 * this.gameSpeed;
            
            // 碰撞检测
            if (this.checkCollision(this.dinosaur, this.obstacles[i])) {
                this.gameOver = true;
                if (this.score > this.bestScore) {
                    this.bestScore = this.score;
                    localStorage.setItem('dino_best_score', this.bestScore);
                    document.getElementById('bestScore').textContent = this.bestScore;
                }
            }
            
            // 加分
            if (!this.obstacles[i].scored && this.obstacles[i].x + this.obstacles[i].width < this.dinosaur.x) {
                this.obstacles[i].scored = true;
                this.score += 10;
                document.getElementById('score').textContent = this.score;
                
                // 增加难度
                this.gameSpeed = 1 + this.score / 500;
                document.getElementById('speed').textContent = this.gameSpeed.toFixed(1) + 'x';
            }
            
            // 删除离屏障碍物
            if (this.obstacles[i].x + this.obstacles[i].width < 0) {
                this.obstacles.splice(i, 1);
            }
        }
        
        // 更新云
        for (let cloud of this.clouds) {
            cloud.x -= cloud.speed * 0.5;
            if (cloud.x + cloud.width < 0) {
                cloud.x = this.canvas.width;
            }
        }
    }
    
    spawnObstacle() {
        const types = ['cactus1', 'cactus2', 'pterodactyl'];
        const type = types[Math.floor(Math.random() * types.length)];
        
        let width, height, y;
        if (type === 'pterodactyl') {
            width = 35;
            height = 25;
            y = this.groundY - 80;
        } else {
            width = 25;
            height = 50;
            y = this.groundY;
        }
        
        this.obstacles.push({
            x: this.canvas.width,
            y: y,
            width: width,
            height: height,
            type: type,
            scored: false
        });
    }
    
    checkCollision(a, b) {
        return a.x < b.x + b.width &&
               a.x + a.width > b.x &&
               a.y < b.y + b.height &&
               a.y + a.height > b.y;
    }
    
    draw() {
        // 背景
        this.ctx.fillStyle = '#87CEEB';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制云
        this.ctx.fillStyle = '#fff';
        for (let cloud of this.clouds) {
            this.ctx.beginPath();
            this.ctx.arc(cloud.x + 10, cloud.y + 15, 15, 0, Math.PI * 2);
            this.ctx.arc(cloud.x + 30, cloud.y, 20, 0, Math.PI * 2);
            this.ctx.arc(cloud.x + 50, cloud.y + 15, 15, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // 地面
        this.ctx.fillStyle = '#90EE90';
        this.ctx.fillRect(0, this.groundY + this.dinosaur.height, this.canvas.width, this.canvas.height - this.groundY - this.dinosaur.height);
        
        // 绘制地面线条
        this.ctx.strokeStyle = '#8B4513';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(0, this.groundY + this.dinosaur.height);
        this.ctx.lineTo(this.canvas.width, this.groundY + this.dinosaur.height);
        this.ctx.stroke();
        
        // 绘制恐龙
        this.ctx.fillStyle = '#228B22';
        this.ctx.fillRect(this.dinosaur.x, this.dinosaur.y, this.dinosaur.width, this.dinosaur.height);
        
        // 恐龙头
        this.ctx.fillStyle = '#1a6b1a';
        this.ctx.fillRect(this.dinosaur.x + 25, this.dinosaur.y, 15, 20);
        
        // 恐龙眼睛
        this.ctx.fillStyle = '#fff';
        this.ctx.fillRect(this.dinosaur.x + 32, this.dinosaur.y + 3, 5, 5);
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(this.dinosaur.x + 34, this.dinosaur.y + 4, 2, 2);
        
        // 绘制障碍物
        for (let obstacle of this.obstacles) {
            if (obstacle.type === 'pterodactyl') {
                // 飞龙
                this.ctx.fillStyle = '#FF6347';
                this.ctx.fillRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height);
                this.ctx.fillRect(obstacle.x - 15, obstacle.y + 5, 15, 3);
                this.ctx.fillRect(obstacle.x + obstacle.width, obstacle.y + 5, 15, 3);
            } else {
                // 仙人掌
                this.ctx.fillStyle = '#228B22';
                this.ctx.fillRect(obstacle.x + 8, obstacle.y, 9, obstacle.height);
                if (obstacle.type === 'cactus2') {
                    this.ctx.fillRect(obstacle.x, obstacle.y + 20, 25, 6);
                }
            }
        }
        
        // 游戏结束
        if (this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#FF0000';
            this.ctx.font = 'bold 40px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏结束', this.canvas.width / 2, this.canvas.height / 2 - 40);
            
            this.ctx.fillStyle = '#fff';
            this.ctx.font = 'bold 24px Arial';
            this.ctx.fillText('得分: ' + this.score, this.canvas.width / 2, this.canvas.height / 2 + 20);
            
            this.gameFinished(this.score, 1);
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
    new DinosaurGame();
});
