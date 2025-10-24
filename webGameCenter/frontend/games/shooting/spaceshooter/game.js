// 太空射击游戏逻辑
class SpaceShooterGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // 玩家飞船
        this.player = {
            x: this.canvas.width / 2 - 15,
            y: this.canvas.height - 50,
            width: 30,
            height: 40,
            speed: 6
        };
        
        // 游戏状态
        this.bullets = [];
        this.enemies = [];
        this.explosions = [];
        this.keys = {};
        this.score = 0;
        this.lives = 3;
        this.level = 1;
        this.gameOver = false;
        this.paused = false;
        this.enemySpawnTimer = 0;
        
        // 事件监听
        document.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;
            if (e.key === ' ') {
                e.preventDefault();
                this.shoot();
            }
            if (e.key === 'r' || e.key === 'R') {
                location.reload();
            }
            if (e.key === 'p' || e.key === 'P') {
                this.paused = !this.paused;
            }
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });
        
        this.canvas.addEventListener('click', () => this.shoot());
        
        this.gameLoop();
    }
    
    shoot() {
        if (!this.gameOver && !this.paused) {
            this.bullets.push({
                x: this.player.x + this.player.width / 2 - 3,
                y: this.player.y,
                width: 6,
                height: 15,
                speed: 7
            });
        }
    }
    
    spawnEnemy() {
        const enemyWidth = 30;
        const x = Math.random() * (this.canvas.width - enemyWidth);
        this.enemies.push({
            x: x,
            y: -40,
            width: 30,
            height: 40,
            speed: 2 + this.level * 0.5,
            health: 1
        });
    }
    
    update() {
        if (this.gameOver || this.paused) return;
        
        // 移动玩家
        if (this.keys['ArrowLeft'] || this.keys['a']) {
            this.player.x = Math.max(0, this.player.x - this.player.speed);
        }
        if (this.keys['ArrowRight'] || this.keys['d']) {
            this.player.x = Math.min(this.canvas.width - this.player.width, this.player.x + this.player.speed);
        }
        
        // 生成敌人
        this.enemySpawnTimer++;
        if (this.enemySpawnTimer > 60 - this.level * 5) {
            this.spawnEnemy();
            this.enemySpawnTimer = 0;
        }
        
        // 更新子弹
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            this.bullets[i].y -= this.bullets[i].speed;
            if (this.bullets[i].y < 0) {
                this.bullets.splice(i, 1);
            }
        }
        
        // 更新敌人
        for (let i = this.enemies.length - 1; i >= 0; i--) {
            this.enemies[i].y += this.enemies[i].speed;
            
            // 敌人离屏
            if (this.enemies[i].y > this.canvas.height) {
                this.enemies.splice(i, 1);
                this.lives--;
                document.getElementById('lives').textContent = this.lives;
                if (this.lives <= 0) {
                    this.gameOver = true;
                }
            }
        }
        
        // 碰撞检测
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            for (let j = this.enemies.length - 1; j >= 0; j--) {
                if (this.checkCollision(this.bullets[i], this.enemies[j])) {
                    this.bullets.splice(i, 1);
                    this.enemies[j].health--;
                    
                    if (this.enemies[j].health <= 0) {
                        this.explosions.push({
                            x: this.enemies[j].x + this.enemies[j].width / 2,
                            y: this.enemies[j].y + this.enemies[j].height / 2,
                            radius: 0,
                            maxRadius: 30
                        });
                        this.enemies.splice(j, 1);
                        this.score += 100;
                        document.getElementById('score').textContent = this.score;
                        
                        // 升级
                        if (this.score % 1000 === 0) {
                            this.level++;
                            document.getElementById('level').textContent = this.level;
                        }
                    }
                    break;
                }
            }
        }
        
        // 玩家碰撞
        for (let i = this.enemies.length - 1; i >= 0; i--) {
            if (this.checkCollision(this.player, this.enemies[i])) {
                this.explosions.push({
                    x: this.player.x + this.player.width / 2,
                    y: this.player.y + this.player.height / 2,
                    radius: 0,
                    maxRadius: 40
                });
                this.enemies.splice(i, 1);
                this.lives--;
                document.getElementById('lives').textContent = this.lives;
                if (this.lives <= 0) {
                    this.gameOver = true;
                }
            }
        }
        
        // 更新爆炸
        for (let i = this.explosions.length - 1; i >= 0; i--) {
            this.explosions[i].radius += 2;
            if (this.explosions[i].radius > this.explosions[i].maxRadius) {
                this.explosions.splice(i, 1);
            }
        }
    }
    
    checkCollision(a, b) {
        return a.x < b.x + b.width &&
               a.x + a.width > b.x &&
               a.y < b.y + b.height &&
               a.y + a.height > b.y;
    }
    
    draw() {
        // 背景星空
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制星星
        this.ctx.fillStyle = '#fff';
        for (let i = 0; i < 100; i++) {
            const x = (i * 23) % this.canvas.width;
            const y = (i * 47 + Date.now() * 0.05) % this.canvas.height;
            this.ctx.fillRect(x, y, 1, 1);
        }
        
        // 绘制玩家飞船
        this.ctx.fillStyle = '#00ff00';
        this.ctx.fillRect(this.player.x, this.player.y, this.player.width, this.player.height);
        this.ctx.fillStyle = '#ffff00';
        this.ctx.fillRect(this.player.x + 8, this.player.y - 10, 14, 10);
        
        // 绘制子弹
        this.ctx.fillStyle = '#ffff00';
        for (let bullet of this.bullets) {
            this.ctx.fillRect(bullet.x, bullet.y, bullet.width, bullet.height);
        }
        
        // 绘制敌人
        this.ctx.fillStyle = '#ff0000';
        for (let enemy of this.enemies) {
            this.ctx.fillRect(enemy.x, enemy.y, enemy.width, enemy.height);
            this.ctx.fillStyle = '#ffff00';
            this.ctx.fillRect(enemy.x + 5, enemy.y + 5, 20, 10);
            this.ctx.fillStyle = '#ff0000';
        }
        
        // 绘制爆炸
        for (let explosion of this.explosions) {
            this.ctx.strokeStyle = '#ff6600';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.arc(explosion.x, explosion.y, explosion.radius, 0, Math.PI * 2);
            this.ctx.stroke();
            
            this.ctx.fillStyle = 'rgba(255, 102, 0, 0.5)';
            this.ctx.beginPath();
            this.ctx.arc(explosion.x, explosion.y, explosion.radius * 0.7, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // 绘制游戏结束
        if (this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#ff0000';
            this.ctx.font = 'bold 40px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏结束', this.canvas.width / 2, this.canvas.height / 2 - 30);
            
            this.ctx.fillStyle = '#ffff00';
            this.ctx.font = 'bold 24px Arial';
            this.ctx.fillText('最终得分: ' + this.score, this.canvas.width / 2, this.canvas.height / 2 + 20);
            
            this.gameFinished(this.score, this.level);
        }
        
        // 绘制暂停
        if (this.paused) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.fillStyle = '#ffff00';
            this.ctx.font = 'bold 30px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('暂停中', this.canvas.width / 2, this.canvas.height / 2);
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
    new SpaceShooterGame();
});
