// 俄罗斯方块游戏
class TetrisGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.nextCanvas = document.getElementById('nextPieceCanvas');
        this.nextCtx = this.nextCanvas.getContext('2d');
        
        // 游戏配置
        this.blockSize = 20;
        this.cols = 12;
        this.rows = 20;
        
        // 游戏状态
        this.board = Array(this.rows).fill(null).map(() => Array(this.cols).fill(0));
        this.score = 0;
        this.level = 1;
        this.lines = 0;
        this.gameOver = false;
        this.paused = false;
        
        // 方块定义 (7种标准方块)
        this.pieces = [
            { name: 'I', color: '#00f0f0', blocks: [[1,1,1,1]] },
            { name: 'O', color: '#f0f000', blocks: [[1,1],[1,1]] },
            { name: 'T', color: '#a000f0', blocks: [[0,1,0],[1,1,1]] },
            { name: 'S', color: '#00f000', blocks: [[0,1,1],[1,1,0]] },
            { name: 'Z', color: '#f00000', blocks: [[1,1,0],[0,1,1]] },
            { name: 'J', color: '#0000f0', blocks: [[1,0,0],[1,1,1]] },
            { name: 'L', color: '#f0a000', blocks: [[0,0,1],[1,1,1]] }
        ];
        
        // 当前和下一个方块
        this.currentPiece = this.randomPiece();
        this.nextPiece = this.randomPiece();
        this.currentX = 4;
        this.currentY = 0;
        
        // 游戏速度
        this.speed = 1000;
        this.dropTime = 0;
        
        // 事件监听
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        this.gameLoop();
    }
    
    randomPiece() {
        return JSON.parse(JSON.stringify(this.pieces[Math.floor(Math.random() * this.pieces.length)]));
    }
    
    handleKeydown(e) {
        if (this.gameOver) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.movePiece(-1, 0);
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.movePiece(1, 0);
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.movePiece(0, 1);
                break;
            case ' ':
                e.preventDefault();
                while (this.canPlace(this.currentX, this.currentY + 1, this.currentPiece.blocks)) {
                    this.currentY++;
                }
                this.lockPiece();
                break;
            case 'z':
            case 'Z':
            case 'ArrowUp':
                e.preventDefault();
                this.rotatePiece();
                break;
            case 'p':
            case 'P':
                e.preventDefault();
                this.paused = !this.paused;
                break;
            case 'r':
            case 'R':
                location.reload();
                break;
        }
    }
    
    movePiece(dx, dy) {
        if (this.canPlace(this.currentX + dx, this.currentY + dy, this.currentPiece.blocks)) {
            this.currentX += dx;
            this.currentY += dy;
        } else if (dy > 0) {
            this.lockPiece();
        }
    }
    
    rotatePiece() {
        const rotated = this.rotate(this.currentPiece.blocks);
        if (this.canPlace(this.currentX, this.currentY, rotated)) {
            this.currentPiece.blocks = rotated;
        }
    }
    
    rotate(matrix) {
        const rotated = matrix[0].map((_, i) => matrix.map(row => row[i]).reverse());
        return rotated;
    }
    
    canPlace(x, y, blocks) {
        for (let row = 0; row < blocks.length; row++) {
            for (let col = 0; col < blocks[row].length; col++) {
                if (blocks[row][col]) {
                    const newX = x + col;
                    const newY = y + row;
                    
                    if (newX < 0 || newX >= this.cols || newY >= this.rows) return false;
                    if (newY >= 0 && this.board[newY][newX]) return false;
                }
            }
        }
        return true;
    }
    
    lockPiece() {
        // 放置方块到棋盘
        for (let row = 0; row < this.currentPiece.blocks.length; row++) {
            for (let col = 0; col < this.currentPiece.blocks[row].length; col++) {
                if (this.currentPiece.blocks[row][col]) {
                    const x = this.currentX + col;
                    const y = this.currentY + row;
                    if (y >= 0) {
                        this.board[y][x] = this.currentPiece.color;
                    }
                }
            }
        }
        
        // 清除完整行
        this.clearLines();
        
        // 生成新方块
        this.currentPiece = this.nextPiece;
        this.nextPiece = this.randomPiece();
        this.currentX = 4;
        this.currentY = 0;
        
        // 检查游戏结束
        if (!this.canPlace(this.currentX, this.currentY, this.currentPiece.blocks)) {
            this.gameOver = true;
        }
    }
    
    clearLines() {
        let linesCleared = 0;
        
        for (let row = this.rows - 1; row >= 0; row--) {
            if (this.board[row].every(cell => cell)) {
                this.board.splice(row, 1);
                this.board.unshift(Array(this.cols).fill(0));
                linesCleared++;
                row++;
            }
        }
        
        if (linesCleared) {
            this.lines += linesCleared;
            this.score += [0, 100, 300, 500, 800][linesCleared];
            this.level = Math.floor(this.lines / 10) + 1;
            this.speed = Math.max(100, 1000 - this.level * 50);
            
            document.getElementById('score').textContent = this.score;
            document.getElementById('level').textContent = this.level;
            document.getElementById('lines').textContent = this.lines;
        }
    }
    
    update() {
        if (this.gameOver || this.paused) return;
        
        this.dropTime += 16;
        if (this.dropTime > this.speed) {
            this.movePiece(0, 1);
            this.dropTime = 0;
        }
    }
    
    draw() {
        // 清除画布
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制网格线
        this.ctx.strokeStyle = '#222';
        this.ctx.lineWidth = 1;
        for (let i = 0; i <= this.cols; i++) {
            this.ctx.beginPath();
            this.ctx.moveTo(i * this.blockSize, 0);
            this.ctx.lineTo(i * this.blockSize, this.canvas.height);
            this.ctx.stroke();
        }
        
        // 绘制棋盘方块
        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                if (this.board[row][col]) {
                    this.ctx.fillStyle = this.board[row][col];
                    this.ctx.fillRect(col * this.blockSize + 1, row * this.blockSize + 1, 
                                    this.blockSize - 2, this.blockSize - 2);
                }
            }
        }
        
        // 绘制当前方块
        if (!this.gameOver) {
            for (let row = 0; row < this.currentPiece.blocks.length; row++) {
                for (let col = 0; col < this.currentPiece.blocks[row].length; col++) {
                    if (this.currentPiece.blocks[row][col]) {
                        this.ctx.fillStyle = this.currentPiece.color;
                        this.ctx.fillRect(
                            (this.currentX + col) * this.blockSize + 1,
                            (this.currentY + row) * this.blockSize + 1,
                            this.blockSize - 2, this.blockSize - 2
                        );
                    }
                }
            }
        }
        
        // 绘制游戏结束屏幕
        if (this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#fff';
            this.ctx.font = 'bold 20px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏结束', this.canvas.width / 2, this.canvas.height / 2);
            this.ctx.font = '16px Arial';
            this.ctx.fillText('得分: ' + this.score, this.canvas.width / 2, this.canvas.height / 2 + 30);
        }
        
        // 绘制暂停状态
        if (this.paused && !this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#fff';
            this.ctx.font = 'bold 16px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('暂停中', this.canvas.width / 2, this.canvas.height / 2);
        }
        
        // 绘制下一个方块
        this.drawNextPiece();
    }
    
    drawNextPiece() {
        this.nextCtx.fillStyle = '#000';
        this.nextCtx.fillRect(0, 0, this.nextCanvas.width, this.nextCanvas.height);
        
        this.nextCtx.fillStyle = this.nextPiece.color;
        const blockSize = 20;
        const offsetX = (this.nextCanvas.width - this.nextPiece.blocks[0].length * blockSize) / 2;
        const offsetY = (this.nextCanvas.height - this.nextPiece.blocks.length * blockSize) / 2;
        
        for (let row = 0; row < this.nextPiece.blocks.length; row++) {
            for (let col = 0; col < this.nextPiece.blocks[row].length; col++) {
                if (this.nextPiece.blocks[row][col]) {
                    this.nextCtx.fillRect(
                        offsetX + col * blockSize + 2,
                        offsetY + row * blockSize + 2,
                        blockSize - 4, blockSize - 4
                    );
                }
            }
        }
    }
    
    gameLoop() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.gameLoop());
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new TetrisGame();
});
