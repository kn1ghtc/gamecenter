class Minesweeper {
    constructor(rows = 10, cols = 10, mines = 10) {
        this.rows = rows;
        this.cols = cols;
        this.mineCount = mines;
        this.board = [];
        this.revealed = [];
        this.flags = [];
        this.gameOver = false;
        this.gameWon = false;
        this.flagCount = 0;
        this.revealedCount = 0;
        this.startTime = Date.now();
        this.elapsedTime = 0;
        
        this.initBoard();
        this.placeMines();
        this.calculateNumbers();
        this.renderBoard();
        this.startTimer();
    }
    
    initBoard() {
        // Initialize empty board
        for (let i = 0; i < this.rows; i++) {
            this.board[i] = [];
            this.revealed[i] = [];
            this.flags[i] = [];
            for (let j = 0; j < this.cols; j++) {
                this.board[i][j] = 0;
                this.revealed[i][j] = false;
                this.flags[i][j] = false;
            }
        }
    }
    
    placeMines() {
        let placed = 0;
        while (placed < this.mineCount) {
            const row = Math.floor(Math.random() * this.rows);
            const col = Math.floor(Math.random() * this.cols);
            
            if (this.board[row][col] !== 'M') {
                this.board[row][col] = 'M';
                placed++;
            }
        }
    }
    
    calculateNumbers() {
        const directions = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],           [0, 1],
            [1, -1],  [1, 0],  [1, 1]
        ];
        
        for (let i = 0; i < this.rows; i++) {
            for (let j = 0; j < this.cols; j++) {
                if (this.board[i][j] !== 'M') {
                    let count = 0;
                    for (const [di, dj] of directions) {
                        const ni = i + di;
                        const nj = j + dj;
                        if (ni >= 0 && ni < this.rows && nj >= 0 && nj < this.cols) {
                            if (this.board[ni][nj] === 'M') count++;
                        }
                    }
                    this.board[i][j] = count;
                }
            }
        }
    }
    
    revealCell(row, col) {
        if (this.gameOver || this.gameWon) return;
        if (this.revealed[row][col] || this.flags[row][col]) return;
        
        this.revealed[row][col] = true;
        this.revealedCount++;
        
        if (this.board[row][col] === 'M') {
            this.gameOver = true;
            this.revealAllMines();
            this.showGameOver();
            return;
        }
        
        if (this.board[row][col] === 0) {
            this.revealAdjacent(row, col);
        }
        
        this.checkWin();
        this.renderBoard();
    }
    
    revealAdjacent(row, col) {
        const directions = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],           [0, 1],
            [1, -1],  [1, 0],  [1, 1]
        ];
        
        for (const [di, dj] of directions) {
            const ni = row + di;
            const nj = col + dj;
            if (ni >= 0 && ni < this.rows && nj >= 0 && nj < this.cols) {
                if (!this.revealed[ni][nj] && !this.flags[ni][nj]) {
                    this.revealed[ni][nj] = true;
                    this.revealedCount++;
                    
                    if (this.board[ni][nj] === 0) {
                        this.revealAdjacent(ni, nj);
                    }
                }
            }
        }
    }
    
    toggleFlag(row, col) {
        if (this.gameOver || this.gameWon) return;
        if (this.revealed[row][col]) return;
        
        if (this.flags[row][col]) {
            this.flags[row][col] = false;
            this.flagCount--;
        } else if (this.flagCount < this.mineCount) {
            this.flags[row][col] = true;
            this.flagCount++;
        }
        
        this.updateUI();
        this.renderBoard();
    }
    
    revealAllMines() {
        for (let i = 0; i < this.rows; i++) {
            for (let j = 0; j < this.cols; j++) {
                if (this.board[i][j] === 'M') {
                    this.revealed[i][j] = true;
                }
            }
        }
        this.renderBoard();
    }
    
    checkWin() {
        const totalNonMines = this.rows * this.cols - this.mineCount;
        if (this.revealedCount === totalNonMines) {
            this.gameWon = true;
            this.showGameWon();
        }
    }
    
    renderBoard() {
        const gameBoard = document.getElementById('gameBoard');
        gameBoard.innerHTML = '';
        gameBoard.style.gridTemplateColumns = `repeat(${this.cols}, 30px)`;
        
        for (let i = 0; i < this.rows; i++) {
            for (let j = 0; j < this.cols; j++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                
                if (this.revealed[i][j]) {
                    cell.classList.add('revealed');
                    if (this.board[i][j] === 'M') {
                        cell.classList.add('mine');
                    } else if (this.board[i][j] > 0) {
                        cell.classList.add('number');
                        cell.textContent = this.board[i][j];
                    } else {
                        cell.classList.add('empty');
                    }
                } else if (this.flags[i][j]) {
                    cell.classList.add('flag');
                }
                
                cell.addEventListener('click', () => this.revealCell(i, j));
                cell.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    this.toggleFlag(i, j);
                });
                
                gameBoard.appendChild(cell);
            }
        }
    }
    
    updateUI() {
        document.getElementById('mines').textContent = this.mineCount;
        document.getElementById('flags').textContent = this.flagCount;
    }
    
    startTimer() {
        setInterval(() => {
            if (!this.gameOver && !this.gameWon) {
                this.elapsedTime = Math.floor((Date.now() - this.startTime) / 1000);
                document.getElementById('timer').textContent = this.elapsedTime;
            }
        }, 1000);
    }
    
    showGameOver() {
        setTimeout(() => {
            alert('💥 游戏失败！您踩到了地雷！\n用时: ' + this.elapsedTime + '秒');
        }, 300);
    }
    
    showGameWon() {
        setTimeout(() => {
            alert('🎉 恭喜胜利！\n用时: ' + this.elapsedTime + '秒\n标记地雷: ' + this.flagCount + '/' + this.mineCount);
        }, 300);
    }
}

// Initialize game
let game;

window.addEventListener('DOMContentLoaded', () => {
    game = new Minesweeper(10, 10, 10);
    document.getElementById('mines').textContent = game.mineCount;
});
