// Pac-Man 游戏逻辑
class PacManGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // 游戏参数
        this.tileSize = 16;
        this.cols = this.canvas.width / this.tileSize;
        this.rows = this.canvas.height / this.tileSize;
        
        // 迷宫
        this.maze = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,2,1,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,2,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,2,1,1,1,2,1],
            [1,2,2,2,2,1,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1,2,2,2,2,2,1],
            [1,1,1,1,2,1,1,1,1,1,1,1,0,1,1,0,1,1,1,1,1,1,2,1,1,1,1,1],
            [1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1],
            [1,1,1,1,2,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,1,1,1,1,1],
            [1,1,1,1,2,1,1,0,1,1,1,1,0,1,1,0,1,1,1,1,0,1,2,1,1,1,1,1],
            [1,2,2,2,2,2,2,0,1,0,0,0,0,0,0,0,0,0,0,1,0,2,2,2,2,2,2,1],
            [1,2,1,1,1,1,2,0,1,0,1,1,1,1,1,1,1,1,0,1,0,2,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,0,0,0,1,0,0,0,0,0,0,0,0,1,0,2,2,2,2,2,2,1],
            [1,2,1,1,1,1,2,1,1,0,1,1,1,1,1,1,1,1,1,1,0,2,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,1,0,0,0,0,0,1,1,0,0,0,0,0,0,2,2,2,2,2,2,1],
            [1,2,1,1,1,1,2,1,0,1,1,1,1,1,1,1,1,1,1,1,0,2,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ];
        
        // 初始化游戏状态
        this.pacman = { x: 1, y: 1, dx: 0, dy: 0, nextDx: 0, nextDy: 0 };
        this.ghosts = [
            { x: 13, y: 9, dx: -1, dy: 0, color: '#FF0000' },
            { x: 14, y: 10, dx: 0, dy: -1, color: '#FFB6C1' },
            { x: 13, y: 10, dx: 1, dy: 0, color: '#00FFFF' },
            { x: 14, y: 9, dx: 0, dy: 1, color: '#FFB347' }
        ];
        
        this.score = 0;
        this.pelletsLeft = this.countPellets();
        this.gameOver = false;
        this.level = 1;
        this.paused = false;
        
        // 绑定事件
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // 游戏循环
        this.gameLoop();
    }
    
    countPellets() {
        let count = 0;
        for (let row of this.maze) {
            for (let cell of row) {
                if (cell === 2) count++;
            }
        }
        return count;
    }
    
    handleKeyDown(e) {
        const directions = {
            'ArrowUp': [0, -1],
            'ArrowDown': [0, 1],
            'ArrowLeft': [-1, 0],
            'ArrowRight': [1, 0],
            'w': [0, -1],
            's': [0, 1],
            'a': [-1, 0],
            'd': [1, 0]
        };
        
        if (directions[e.key]) {
            e.preventDefault();
            [this.pacman.nextDx, this.pacman.nextDy] = directions[e.key];
        } else if (e.key === ' ') {
            e.preventDefault();
            this.paused = !this.paused;
        }
    }
    
    update() {
        if (this.gameOver || this.paused) return;
        
        // 尝试移动pacman到下一个方向
        if (this.canMove(this.pacman.x + this.pacman.nextDx, this.pacman.y + this.pacman.nextDy)) {
            this.pacman.dx = this.pacman.nextDx;
            this.pacman.dy = this.pacman.nextDy;
        }
        
        // 移动pacman
        if (this.canMove(this.pacman.x + this.pacman.dx, this.pacman.y + this.pacman.dy)) {
            this.pacman.x += this.pacman.dx;
            this.pacman.y += this.pacman.dy;
        }
        
        // 吃豆子
        if (this.maze[this.pacman.y][this.pacman.x] === 2) {
            this.maze[this.pacman.y][this.pacman.x] = 0;
            this.score += 10;
            this.pelletsLeft--;
            
            if (this.pelletsLeft === 0) {
                this.levelUp();
            }
        }
        
        // 移动鬼怪
        for (let ghost of this.ghosts) {
            this.moveGhost(ghost);
        }
        
        // 检查碰撞
        for (let ghost of this.ghosts) {
            if (this.pacman.x === ghost.x && this.pacman.y === ghost.y) {
                this.gameOver = true;
            }
        }
        
        // 更新分数显示
        document.getElementById('score').textContent = this.score;
        document.getElementById('level').textContent = this.level;
    }
    
    canMove(x, y) {
        if (x < 0 || x >= this.cols || y < 0 || y >= this.rows) return false;
        return this.maze[y][x] !== 1;
    }
    
    moveGhost(ghost) {
        const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
        let validMoves = [];
        
        for (let [dx, dy] of directions) {
            if (this.canMove(ghost.x + dx, ghost.y + dy)) {
                validMoves.push([dx, dy]);
            }
        }
        
        if (validMoves.length > 0) {
            [ghost.dx, ghost.dy] = validMoves[Math.floor(Math.random() * validMoves.length)];
            ghost.x += ghost.dx;
            ghost.y += ghost.dy;
        }
    }
    
    levelUp() {
        this.level++;
        this.score += 500;
        
        // 重新开始
        this.pacman = { x: 1, y: 1, dx: 0, dy: 0, nextDx: 0, nextDy: 0 };
        this.ghosts = [
            { x: 13, y: 9, dx: -1, dy: 0, color: '#FF0000' },
            { x: 14, y: 10, dx: 0, dy: -1, color: '#FFB6C1' },
            { x: 13, y: 10, dx: 1, dy: 0, color: '#00FFFF' },
            { x: 14, y: 9, dx: 0, dy: 1, color: '#FFB347' }
        ];
        
        this.maze = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,2,1,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,2,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,2,1,1,1,2,1],
            [1,2,2,2,2,1,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1,2,2,2,2,2,1],
            [1,1,1,1,2,1,1,1,1,1,1,1,0,1,1,0,1,1,1,1,1,1,2,1,1,1,1,1],
            [1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1],
            [1,1,1,1,2,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,1,1,1,1,1],
            [1,1,1,1,2,1,1,0,1,1,1,1,0,1,1,0,1,1,1,1,0,1,2,1,1,1,1,1],
            [1,2,2,2,2,2,2,0,1,0,0,0,0,0,0,0,0,0,0,1,0,2,2,2,2,2,2,1],
            [1,2,1,1,1,1,2,0,1,0,1,1,1,1,1,1,1,1,0,1,0,2,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,0,0,0,1,0,0,0,0,0,0,0,0,1,0,2,2,2,2,2,2,1],
            [1,2,1,1,1,1,2,1,1,0,1,1,1,1,1,1,1,1,1,1,0,2,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,1,0,0,0,0,0,1,1,0,0,0,0,0,0,2,2,2,2,2,2,1],
            [1,2,1,1,1,1,2,1,0,1,1,1,1,1,1,1,1,1,1,1,0,2,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ];
        
        this.pelletsLeft = this.countPellets();
    }
    
    draw() {
        // 清空画布
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 画迷宫
        for (let y = 0; y < this.rows; y++) {
            for (let x = 0; x < this.cols; x++) {
                const cell = this.maze[y][x];
                const px = x * this.tileSize;
                const py = y * this.tileSize;
                
                if (cell === 1) {
                    // 墙
                    this.ctx.fillStyle = '#0066FF';
                    this.ctx.fillRect(px, py, this.tileSize, this.tileSize);
                } else if (cell === 2) {
                    // 豆子
                    this.ctx.fillStyle = '#FFB6C1';
                    this.ctx.beginPath();
                    this.ctx.arc(px + this.tileSize/2, py + this.tileSize/2, 2, 0, Math.PI*2);
                    this.ctx.fill();
                }
            }
        }
        
        // 画Pacman
        this.ctx.fillStyle = '#FFD700';
        this.ctx.beginPath();
        const pacX = this.pacman.x * this.tileSize + this.tileSize/2;
        const pacY = this.pacman.y * this.tileSize + this.tileSize/2;
        this.ctx.arc(pacX, pacY, 7, 0, Math.PI*2);
        this.ctx.fill();
        
        // 画鬼怪
        for (let ghost of this.ghosts) {
            this.ctx.fillStyle = ghost.color;
            const ghostX = ghost.x * this.tileSize + 2;
            const ghostY = ghost.y * this.tileSize + 2;
            
            // 身体
            this.ctx.fillRect(ghostX, ghostY, this.tileSize-4, this.tileSize-4);
            
            // 眼睛
            this.ctx.fillStyle = '#FFF';
            this.ctx.fillRect(ghostX+2, ghostY+2, 3, 3);
            this.ctx.fillRect(ghostX+8, ghostY+2, 3, 3);
        }
        
        // 游戏结束
        if (this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.fillStyle = '#FF0000';
            this.ctx.font = 'bold 40px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏结束', this.canvas.width/2, this.canvas.height/2);
            
            // 上报分数
            this.gameFinished(this.score, this.level);
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

// 启动游戏
window.addEventListener('DOMContentLoaded', () => {
    new PacManGame();
});
