/**
 * 拳皇格斗游戏
 */

class KOFGame {
    constructor() {
        this.container = document.getElementById('gameContainer');
        this.player = document.getElementById('player');
        this.opponent = document.getElementById('opponent');
        this.playerHealthFill = document.querySelector('#playerHealth .health-fill');
        this.opponentHealthFill = document.querySelector('#opponentHealth .health-fill');

        this.playerHealth = 100;
        this.opponentHealth = 100;
        this.playerScore = 0;
        this.opponentScore = 0;
        this.gameOver = false;

        // 玩家状态
        this.playerX = 100;
        this.playerY = 400;
        this.playerVelX = 0;
        this.playerVelY = 0;
        this.playerJumping = false;
        this.playerAttacking = false;
        this.playerDirection = 1;

        // 对手状态
        this.opponentX = 700;
        this.opponentY = 400;
        this.opponentVelX = 0;
        this.opponentVelY = 0;
        this.opponentJumping = false;
        this.opponentAttacking = false;
        this.opponentAttackTimer = 0;

        // 输入
        this.keys = {};

        this.bindEvents();
        this.gameLoop();
    }

    bindEvents() {
        window.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;
            if (e.key === ' ') {
                e.preventDefault();
                this.playerAttack();
            }
            if (e.key === 'w' || e.key === 'W') {
                e.preventDefault();
                this.playerJump();
            }
        });

        window.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });
    }

    playerAttack() {
        if (!this.playerAttacking) {
            this.playerAttacking = true;
            this.checkHit(true);
            setTimeout(() => {
                this.playerAttacking = false;
            }, 300);
        }
    }

    playerJump() {
        if (!this.playerJumping) {
            this.playerVelY = -15;
            this.playerJumping = true;
        }
    }

    checkHit(isPlayer) {
        const dist = Math.abs(this.playerX - this.opponentX);
        if (dist < 150 && isPlayer) {
            this.opponentHealth -= 15;
            this.playerScore += 50;
            if (this.opponentHealth <= 0) this.endGame(true);
        } else if (dist < 150 && !isPlayer) {
            this.playerHealth -= 15;
            this.opponentScore += 50;
            if (this.playerHealth <= 0) this.endGame(false);
        }
    }

    update() {
        // 玩家移动
        this.playerVelX = 0;
        if (this.keys['a'] || this.keys['A'] || this.keys['ArrowLeft']) {
            this.playerVelX = -5;
            this.playerDirection = -1;
        }
        if (this.keys['d'] || this.keys['D'] || this.keys['ArrowRight']) {
            this.playerVelX = 5;
            this.playerDirection = 1;
        }

        // 重力
        this.playerVelY += 0.6;
        this.playerX += this.playerVelX;
        this.playerY += this.playerVelY;

        // 地面碰撞
        if (this.playerY >= 400) {
            this.playerY = 400;
            this.playerVelY = 0;
            this.playerJumping = false;
        }

        // 边界
        if (this.playerX < 50) this.playerX = 50;
        if (this.playerX > 400) this.playerX = 400;

        // 对手AI
        this.opponentAttackTimer++;
        const dist = Math.abs(this.playerX - this.opponentX);

        if (dist > 200) {
            this.opponentVelX = this.playerX > this.opponentX ? -3 : 3;
        } else {
            this.opponentVelX = 0;
            if (Math.random() < 0.02) {
                this.opponentAttacking = true;
                this.checkHit(false);
                setTimeout(() => {
                    this.opponentAttacking = false;
                }, 300);
            }
        }

        // 对手重力
        this.opponentVelY += 0.6;
        this.opponentX += this.opponentVelX;
        this.opponentY += this.opponentVelY;

        if (this.opponentY >= 400) {
            this.opponentY = 400;
            this.opponentVelY = 0;
        }

        // 边界
        if (this.opponentX < 400) this.opponentX = 400;
        if (this.opponentX > 750) this.opponentX = 750;

        // 更新显示
        this.player.style.left = this.playerX + 'px';
        this.player.style.top = this.playerY + 'px';
        if (this.playerDirection < 0) {
            this.player.style.transform = 'scaleX(-1)';
        } else {
            this.player.style.transform = 'scaleX(1)';
        }

        this.opponent.style.right = (800 - this.opponentX - 40) + 'px';
        this.opponent.style.top = this.opponentY + 'px';

        // 健康条
        this.playerHealthFill.style.width = Math.max(0, this.playerHealth) + '%';
        this.opponentHealthFill.style.width = Math.max(0, this.opponentHealth) + '%';
    }

    endGame(playerWon) {
        this.gameOver = true;
        if (window.parent && window.parent.gameFinished) {
            window.parent.gameFinished(playerWon ? this.playerScore : 0, 1);
        }
    }

    gameLoop() {
        if (!this.gameOver) {
            this.update();
            requestAnimationFrame(() => this.gameLoop());
        }
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new KOFGame();
});
