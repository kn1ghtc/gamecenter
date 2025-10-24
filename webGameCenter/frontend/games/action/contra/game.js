/**
 * 魂斗罗游戏 - 横版射击游戏
 */

class ContraGame {
    constructor() {
        this.container = document.getElementById('gameContainer');
        this.player = document.getElementById('player');
        this.scoreDisplay = document.getElementById('score');
        this.livesDisplay = document.getElementById('lives');
        this.levelDisplay = document.getElementById('level');
        this.gameOverScreen = document.getElementById('gameOver');

        this.score = 0;
        this.lives = 3;
        this.level = 1;
        this.gameOver = false;

        // 玩家状态
        this.playerX = 50;
        this.playerY = this.container.offsetHeight - 140;
        this.playerVelY = 0;
        this.playerJumping = false;
        this.playerDirection = 1; // 1 = right, -1 = left
        this.shooting = false;

        // 输入状态
        this.keys = {};

        // 敌人列表
        this.enemies = [];

        // 子弹列表
        this.bullets = [];

        // 平台列表
        this.platforms = [];

        this.initPlatforms();
        this.bindEvents();
        this.startGame();
    }

    initPlatforms() {
        // 创建游戏场景的平台
        const platformData = [
            { x: 0, y: this.container.offsetHeight - 50, w: this.container.offsetWidth, h: 50 }, // 地面
            { x: 150, y: 400, w: 200, h: 20 },
            { x: 500, y: 350, w: 200, h: 20 },
            { x: 100, y: 250, w: 150, h: 20 },
            { x: 550, y: 200, w: 150, h: 20 }
        ];

        platformData.forEach(data => {
            const platform = document.createElement('div');
            platform.className = 'platform';
            platform.style.left = data.x + 'px';
            platform.style.top = data.y + 'px';
            platform.style.width = data.w + 'px';
            platform.style.height = data.h + 'px';
            this.container.appendChild(platform);

            this.platforms.push(data);
        });
    }

    bindEvents() {
        window.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;

            if (e.key === ' ') {
                e.preventDefault();
                this.shoot();
            }
            if (e.key === 'w' || e.key === 'W') {
                e.preventDefault();
                this.jump();
            }
        });

        window.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });
    }

    startGame() {
        this.spawnEnemies();
        this.gameLoop();
    }

    spawnEnemies() {
        if (this.enemies.length < 2 + this.level) {
            const enemy = {
                x: Math.random() * 700,
                y: 100,
                velX: (Math.random() - 0.5) * 3,
                width: 30,
                height: 35
            };
            this.enemies.push(enemy);
        }
    }

    shoot() {
        const bullet = {
            x: this.playerX + (this.playerDirection > 0 ? 30 : 0),
            y: this.playerY + 15,
            velX: this.playerDirection * 5
        };
        this.bullets.push(bullet);
    }

    jump() {
        if (!this.playerJumping) {
            this.playerVelY = -12;
            this.playerJumping = true;
        }
    }

    update() {
        // 更新玩家位置
        if (this.keys['ArrowLeft'] || this.keys['a'] || this.keys['A']) {
            this.playerX -= 5;
            this.playerDirection = -1;
        }
        if (this.keys['ArrowRight'] || this.keys['d'] || this.keys['D']) {
            this.playerX += 5;
            this.playerDirection = 1;
        }

        // 重力
        this.playerVelY += 0.5;
        this.playerY += this.playerVelY;

        // 碰撞检测
        let onGround = false;
        this.platforms.forEach(platform => {
            if (this.playerX < platform.x + platform.w &&
                this.playerX + 30 > platform.x &&
                this.playerY + 40 >= platform.y &&
                this.playerY + 40 <= platform.y + platform.h + 5 &&
                this.playerVelY >= 0) {
                this.playerY = platform.y - 40;
                this.playerVelY = 0;
                this.playerJumping = false;
                onGround = true;
            }
        });

        // 边界检测
        if (this.playerX < 0) this.playerX = 0;
        if (this.playerX + 30 > this.container.offsetWidth) this.playerX = this.container.offsetWidth - 30;
        if (this.playerY > this.container.offsetHeight) {
            this.lives--;
            this.playerX = 50;
            this.playerY = this.container.offsetHeight - 140;
        }

        // 更新玩家显示
        this.player.style.left = this.playerX + 'px';
        this.player.style.top = this.playerY + 'px';
        if (this.playerDirection < 0) {
            this.player.style.transform = 'scaleX(-1)';
        } else {
            this.player.style.transform = 'scaleX(1)';
        }

        // 更新敌人
        this.enemies = this.enemies.filter(enemy => {
            enemy.x += enemy.velX;
            enemy.y += 2;

            if (enemy.x < 0 || enemy.x > this.container.offsetWidth || enemy.y > this.container.offsetHeight) {
                return false;
            }

            // 从DOM中查找敌人元素
            let enemyElement = document.querySelector(`[data-enemy-id="${enemy.id}"]`);
            if (enemyElement) {
                enemyElement.style.left = enemy.x + 'px';
                enemyElement.style.top = enemy.y + 'px';
            }

            // 与玩家碰撞
            if (this.playerX < enemy.x + enemy.width &&
                this.playerX + 30 > enemy.x &&
                this.playerY < enemy.y + enemy.height &&
                this.playerY + 40 > enemy.y) {
                this.lives--;
                return false;
            }

            return true;
        });

        // 更新子弹
        this.bullets = this.bullets.filter(bullet => {
            bullet.x += bullet.velX;

            // 从DOM中查找子弹元素
            let bulletElement = document.querySelector(`[data-bullet-id="${bullet.id}"]`);
            if (bulletElement) {
                bulletElement.style.left = bullet.x + 'px';
                bulletElement.style.top = bullet.y + 'px';
            }

            // 检查与敌人碰撞
            let hit = false;
            this.enemies.forEach(enemy => {
                if (bullet.x > enemy.x &&
                    bullet.x < enemy.x + enemy.width &&
                    bullet.y > enemy.y &&
                    bullet.y < enemy.y + enemy.height) {
                    this.score += 100;
                    hit = true;
                }
            });

            return !(bullet.x < 0 || bullet.x > this.container.offsetWidth || hit);
        });

        // 更新显示
        this.scoreDisplay.textContent = `分数: ${this.score}`;
        this.livesDisplay.textContent = `生命: ${this.lives}`;
        this.levelDisplay.textContent = `关卡: ${this.level}`;

        // 检查游戏结束
        if (this.lives <= 0) {
            this.endGame();
        }

        // 升级条件
        if (this.enemies.length === 0 && this.score > this.level * 1000) {
            this.level++;
        }

        this.spawnEnemies();
    }

    render() {
        // 创建或更新敌人DOM元素
        this.enemies.forEach(enemy => {
            if (!enemy.id) {
                enemy.id = Math.random();
                const enemyEl = document.createElement('div');
                enemyEl.className = 'enemy';
                enemyEl.setAttribute('data-enemy-id', enemy.id);
                this.container.appendChild(enemyEl);
            }
        });

        // 创建或更新子弹DOM元素
        this.bullets.forEach(bullet => {
            if (!bullet.id) {
                bullet.id = Math.random();
                const bulletEl = document.createElement('div');
                bulletEl.className = 'bullet';
                bulletEl.setAttribute('data-bullet-id', bullet.id);
                this.container.appendChild(bulletEl);
            }
        });
    }

    endGame() {
        this.gameOver = true;
        this.gameOverScreen.style.display = 'flex';
        this.gameOverScreen.innerHTML = `
            <h1>游戏结束</h1>
            <p>最终分数: ${this.score}</p>
            <p>达到关卡: ${this.level}</p>
        `;

        // 上报分数到后端
        if (window.parent && window.parent.gameFinished) {
            window.parent.gameFinished(this.score, this.level);
        }
    }

    gameLoop() {
        if (!this.gameOver) {
            this.update();
            this.render();
            requestAnimationFrame(() => this.gameLoop());
        }
    }
}

// 初始化游戏
window.addEventListener('DOMContentLoaded', () => {
    new ContraGame();
});
