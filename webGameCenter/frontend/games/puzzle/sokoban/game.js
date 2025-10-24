// 推箱子游戏逻辑
class SokobanGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.tileSize = 60;
        this.gridWidth = 8;
        this.gridHeight = 8;
        
        this.currentLevel = 1;
        this.moves = 0;
        this.levels = [
            {
                map: [
                    [1,1,1,1,1,1,1,1],
                    [1,0,0,0,0,0,0,1],
                    [1,0,2,0,0,0,0,1],
                    [1,0,0,0,3,0,0,1],
                    [1,0,0,0,0,0,0,1],
                    [1,0,0,0,4,0,0,1],
                    [1,0,0,0,0,0,0,1],
                    [1,1,1,1,1,1,1,1]
                ],
                player: {x: 1, y: 1},
                boxes: [{x: 3, y: 2}, {x: 4, y: 4}],
                goals: [{x: 5, y: 2}, {x: 6, y: 4}]
            },
            {
                map: [
                    [1,1,1,1,1,1,1,1],
                    [1,0,0,0,0,0,0,1],
                    [1,0,2,0,3,0,0,1],
                    [1,0,0,0,0,0,0,1],
                    [1,0,4,0,5,0,0,1],
                    [1,0,0,0,0,0,0,1],
                    [1,0,6,0,0,0,0,1],
                    [1,1,1,1,1,1,1,1]
                ],
                player: {x: 1, y: 1},
                boxes: [{x: 2, y: 2}, {x: 4, y: 2}, {x: 2, y: 4}, {x: 4, y: 4}],
                goals: [{x: 5, y: 2}, {x: 6, y: 2}, {x: 5, y: 4}, {x: 6, y: 4}]
            }
        ];
        
        this.loadLevel();
        
        document.addEventListener('keydown', (e) => this.handleInput(e));
        this.gameLoop();
    }
    
    loadLevel() {
        if (this.currentLevel > this.levels.length) {
            this.currentLevel = this.levels.length;
        }
        
        const level = this.levels[this.currentLevel - 1];
        this.map = JSON.parse(JSON.stringify(level.map));
        this.player = {...level.player};
        this.boxes = level.boxes.map(b => ({...b}));
        this.goals = level.goals;
        this.moves = 0;
        
        document.getElementById('level').textContent = this.currentLevel;
        document.getElementById('moves').textContent = this.moves;
        document.getElementById('total').textContent = this.boxes.length;
        this.updateProgress();
    }
    
    handleInput(e) {
        let dx = 0, dy = 0;
        
        switch(e.key) {
            case 'ArrowLeft':
                dx = -1;
                e.preventDefault();
                break;
            case 'ArrowRight':
                dx = 1;
                e.preventDefault();
                break;
            case 'ArrowUp':
                dy = -1;
                e.preventDefault();
                break;
            case 'ArrowDown':
                dy = 1;
                e.preventDefault();
                break;
            case ' ':
                this.loadLevel();
                e.preventDefault();
                return;
            case 'r':
            case 'R':
                this.nextLevel();
                e.preventDefault();
                return;
        }
        
        if (dx !== 0 || dy !== 0) {
            this.movePlayer(dx, dy);
        }
    }
    
    movePlayer(dx, dy) {
        const newX = this.player.x + dx;
        const newY = this.player.y + dy;
        
        // 检查是否可以移动到墙
        if (this.map[newY][newX] === 1) return;
        
        // 检查是否有箱子
        const boxIndex = this.boxes.findIndex(b => b.x === newX && b.y === newY);
        
        if (boxIndex !== -1) {
            // 尝试推动箱子
            const boxNewX = this.boxes[boxIndex].x + dx;
            const boxNewY = this.boxes[boxIndex].y + dy;
            
            // 检查箱子是否能移动
            if (this.map[boxNewY][boxNewX] === 1) return;
            if (this.boxes.some(b => b.x === boxNewX && b.y === boxNewY)) return;
            
            this.boxes[boxIndex].x = boxNewX;
            this.boxes[boxIndex].y = boxNewY;
        }
        
        this.player.x = newX;
        this.player.y = newY;
        this.moves++;
        document.getElementById('moves').textContent = this.moves;
        
        this.updateProgress();
        
        if (this.isLevelComplete()) {
            setTimeout(() => {
                alert('恭喜！关卡 ' + this.currentLevel + ' 完成！移动数: ' + this.moves);
                this.nextLevel();
            }, 200);
        }
    }
    
    updateProgress() {
        let count = 0;
        for (let box of this.boxes) {
            if (this.goals.some(g => g.x === box.x && g.y === box.y)) {
                count++;
            }
        }
        document.getElementById('progress').textContent = count;
    }
    
    isLevelComplete() {
        return this.boxes.every(box => 
            this.goals.some(goal => goal.x === box.x && goal.y === box.y)
        );
    }
    
    nextLevel() {
        this.currentLevel++;
        if (this.currentLevel > this.levels.length) {
            this.currentLevel = 1;
            alert('所有关卡完成！游戏重新开始。');
        }
        this.loadLevel();
    }
    
    draw() {
        // 背景
        this.ctx.fillStyle = '#D2B48C';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制地图
        for (let y = 0; y < this.gridHeight; y++) {
            for (let x = 0; x < this.gridWidth; x++) {
                if (this.map[y][x] === 1) {
                    this.ctx.fillStyle = '#8B4513';
                    this.ctx.fillRect(x * this.tileSize, y * this.tileSize, this.tileSize, this.tileSize);
                }
            }
        }
        
        // 绘制目标
        for (let goal of this.goals) {
            this.ctx.fillStyle = '#FFD700';
            this.ctx.beginPath();
            this.ctx.arc((goal.x + 0.5) * this.tileSize, (goal.y + 0.5) * this.tileSize, 15, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.ctx.strokeStyle = '#FF6347';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
        }
        
        // 绘制箱子
        for (let box of this.boxes) {
            const isOnGoal = this.goals.some(g => g.x === box.x && g.y === box.y);
            this.ctx.fillStyle = isOnGoal ? '#00AA00' : '#FF8C00';
            this.ctx.fillRect(box.x * this.tileSize + 5, box.y * this.tileSize + 5, this.tileSize - 10, this.tileSize - 10);
            
            this.ctx.strokeStyle = '#000';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(box.x * this.tileSize + 5, box.y * this.tileSize + 5, this.tileSize - 10, this.tileSize - 10);
        }
        
        // 绘制玩家
        this.ctx.fillStyle = '#FF1493';
        this.ctx.fillRect(this.player.x * this.tileSize + 15, this.player.y * this.tileSize + 15, this.tileSize - 30, this.tileSize - 30);
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(this.player.x * this.tileSize + 15, this.player.y * this.tileSize + 15, this.tileSize - 30, this.tileSize - 30);
    }
    
    gameLoop() {
        this.draw();
        requestAnimationFrame(() => this.gameLoop());
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new SokobanGame();
});
