/**
 * 坦克大战游戏
 */

class TankBattleGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.container = document.getElementById('gameContainer');

        this.score = 0;
        this.lives = 3;
        this.level = 1;
        this.gameOver = false;

        // 玩家坦克
        this.player = {
            x: this.canvas.width / 2 - 15,
            y: this.canvas.height - 40,
            width: 30,
            height: 30,
            angle: 0,
            speed: 2,
            velX: 0,
            velY: 0
        };

        // 敌人坦克
        this.enemies = [];
        this.spawnEnemies(2);

        // 子弹
        this.bullets = [];
        this.enemyBullets = [];

        // 输入
        this.keys = {};

        this.bindEvents();
        this.startGame();
    }

    bindEvents() {
        window.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;
            if (e.key === ' ') {
                e.preventDefault();
                this.shoot();
            }
        });

        window.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });
    }

    spawnEnemies(count) {
        for (let i = 0; i < count; i++) {
            this.enemies.push({
                x: Math.random() * (this.canvas.width - 30),
                y: Math.random() * 100,
                width: 30,
                height: 30,
                angle: Math.random() * Math.PI * 2,
                speed: 1.5,
                velX: Math.cos(this.player.angle) * 1.5,
                velY: Math.sin(this.player.angle) * 1.5,
                shootTimer: 0
            });
        }
    }

    shoot() {
        this.bullets.push({
            x: this.player.x + 15,
            y: this.player.y + 15,
            velX: Math.cos(this.player.angle) * 5,
            velY: Math.sin(this.player.angle) * 5
        });
    }

    update() {
        // 更新玩家
        this.player.velX = 0;
        this.player.velY = 0;

        if (this.keys['ArrowUp'] || this.keys['w']) {
            this.player.angle = -Math.PI / 2;
            this.player.velY = -this.player.speed;
        }
        if (this.keys['ArrowDown'] || this.keys['s']) {
            this.player.angle = Math.PI / 2;
            this.player.velY = this.player.speed;
        }
        if (this.keys['ArrowLeft'] || this.keys['a']) {
            this.player.angle = Math.PI;
            this.player.velX = -this.player.speed;
        }
        if (this.keys['ArrowRight'] || this.keys['d']) {
            this.player.angle = 0;
            this.player.velX = this.player.speed;
        }

        this.player.x += this.player.velX;
        this.player.y += this.player.velY;

        // 边界
        if (this.player.x < 0) this.player.x = 0;
        if (this.player.x + this.player.width > this.canvas.width) 
            this.player.x = this.canvas.width - this.player.width;
        if (this.player.y < 0) this.player.y = 0;
        if (this.player.y + this.player.height > this.canvas.height) 
            this.player.y = this.canvas.height - this.player.height;

        // 更新敌人
        this.enemies = this.enemies.filter(enemy => {
            // 移动
            if (Math.random() < 0.02) {
                enemy.angle = Math.random() * Math.PI * 2;
            }
            enemy.velX = Math.cos(enemy.angle) * enemy.speed;
            enemy.velY = Math.sin(enemy.angle) * enemy.speed;
            enemy.x += enemy.velX;
            enemy.y += enemy.velY;

            // 边界反弹
            if (enemy.x < 0 || enemy.x + enemy.width > this.canvas.width) {
                enemy.angle = Math.PI - enemy.angle;
            }
            if (enemy.y < 0 || enemy.y + enemy.height > this.canvas.height) {
                enemy.angle = -enemy.angle;
            }

            // 敌人射击
            enemy.shootTimer++;
            if (enemy.shootTimer > 60) {
                const angleToPlayer = Math.atan2(
                    this.player.y - enemy.y,
                    this.player.x - enemy.x
                );
                this.enemyBullets.push({
                    x: enemy.x + 15,
                    y: enemy.y + 15,
                    velX: Math.cos(angleToPlayer) * 3,
                    velY: Math.sin(angleToPlayer) * 3
                });
                enemy.shootTimer = 0;
            }

            // 与玩家碰撞
            if (this.checkCollision(this.player, enemy)) {
                this.lives--;
                if (this.lives <= 0) this.endGame();
                return false;
            }

            return true;
        });

        // 更新子弹
        this.bullets = this.bullets.filter(bullet => {
            bullet.x += bullet.velX;
            bullet.y += bullet.velY;

            // 敌人碰撞
            for (let i = this.enemies.length - 1; i >= 0; i--) {
                if (this.checkCollision(bullet, this.enemies[i])) {
                    this.enemies.splice(i, 1);
                    this.score += 100;
                    return false;
                }
            }

            return bullet.x > -10 && bullet.x < this.canvas.width + 10 &&
                   bullet.y > -10 && bullet.y < this.canvas.height + 10;
        });

        // 更新敌人子弹
        this.enemyBullets = this.enemyBullets.filter(bullet => {
            bullet.x += bullet.velX;
            bullet.y += bullet.velY;

            // 与玩家碰撞
            if (this.checkCollision(bullet, this.player)) {
                this.lives--;
                if (this.lives <= 0) this.endGame();
                return false;
            }

            return bullet.x > -10 && bullet.x < this.canvas.width + 10 &&
                   bullet.y > -10 && bullet.y < this.canvas.height + 10;
        });

        // 生成敌人
        if (this.enemies.length < 2 + Math.floor(this.score / 500)) {
            this.spawnEnemies(1);
        }

        // 更新UI
        document.getElementById('score').textContent = this.score;
        document.getElementById('lives').textContent = this.lives;
        document.getElementById('enemies').textContent = this.enemies.length;
    }

    checkCollision(obj1, obj2) {
        return obj1.x < obj2.x + obj2.width &&
               obj1.x + obj1.width > obj2.x &&
               obj1.y < obj2.y + obj2.height &&
               obj1.y + obj1.height > obj2.y;
    }

    draw() {
        // 清空画布
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制玩家
        this.drawTank(this.player, '#00FF00');

        // 绘制敌人
        this.enemies.forEach(enemy => {
            this.drawTank(enemy, '#FF0000');
        });

        // 绘制子弹
        this.ctx.fillStyle = '#FFFF00';
        this.bullets.forEach(bullet => {
            this.ctx.fillRect(bullet.x - 2, bullet.y - 2, 4, 4);
        });

        // 绘制敌人子弹
        this.ctx.fillStyle = '#FF6600';
        this.enemyBullets.forEach(bullet => {
            this.ctx.fillRect(bullet.x - 2, bullet.y - 2, 4, 4);
        });
    }

    drawTank(tank, color) {
        this.ctx.save();
        this.ctx.translate(tank.x + tank.width / 2, tank.y + tank.height / 2);
        this.ctx.rotate(tank.angle);

        // 坦克身体
        this.ctx.fillStyle = color;
        this.ctx.fillRect(-tank.width / 2, -tank.height / 2, tank.width, tank.height);

        // 坦克炮塔
        this.ctx.fillStyle = '#FFD700';
        this.ctx.fillRect(-4, -tank.height / 4, 8, tank.height / 2);

        this.ctx.restore();
    }

    endGame() {
        this.gameOver = true;
        if (window.parent && window.parent.gameFinished) {
            window.parent.gameFinished(this.score, this.level);
        }
    }

    gameLoop() {
        if (!this.gameOver) {
            this.update();
            this.draw();
            requestAnimationFrame(() => this.gameLoop());
        }
    }

    startGame() {
        this.gameLoop();
    }
}

// 初始化游戏
window.addEventListener('DOMContentLoaded', () => {
    new TankBattleGame();
});
