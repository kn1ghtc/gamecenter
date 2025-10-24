/**
 * 2048 游戏
 */

class Game2048 {
    constructor() {
        this.grid = [];
        this.score = 0;
        this.gameOver = false;
        this.won = false;

        this.init();
        this.bindEvents();
        this.render();
    }

    init() {
        // 初始化4x4网格
        for (let i = 0; i < 4; i++) {
            this.grid[i] = [];
            for (let j = 0; j < 4; j++) {
                this.grid[i][j] = 0;
            }
        }
        // 添加两个初始方块
        this.addNewTile();
        this.addNewTile();
    }

    addNewTile() {
        const empty = [];
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                if (this.grid[i][j] === 0) {
                    empty.push({ x: i, y: j });
                }
            }
        }

        if (empty.length > 0) {
            const pos = empty[Math.floor(Math.random() * empty.length)];
            this.grid[pos.x][pos.y] = Math.random() < 0.9 ? 2 : 4;
        }
    }

    bindEvents() {
        window.addEventListener('keydown', (e) => {
            const keyMap = {
                'ArrowUp': 'up',
                'ArrowDown': 'down',
                'ArrowLeft': 'left',
                'ArrowRight': 'right',
                'w': 'up',
                's': 'down',
                'a': 'left',
                'd': 'right'
            };

            if (keyMap[e.key]) {
                e.preventDefault();
                this.move(keyMap[e.key]);
            }
        });
    }

    move(direction) {
        if (this.gameOver) return;

        let changed = false;

        if (direction === 'left') {
            changed = this.moveLeft();
        } else if (direction === 'right') {
            changed = this.moveRight();
        } else if (direction === 'up') {
            changed = this.moveUp();
        } else if (direction === 'down') {
            changed = this.moveDown();
        }

        if (changed) {
            this.addNewTile();
            this.render();
            this.checkGameState();
        }
    }

    moveLeft() {
        let changed = false;
        for (let i = 0; i < 4; i++) {
            this.grid[i] = this.slideAndMerge(this.grid[i]);
        }
        return changed;
    }

    moveRight() {
        let changed = false;
        for (let i = 0; i < 4; i++) {
            this.grid[i] = this.slideAndMerge(this.grid[i].reverse()).reverse();
        }
        return changed;
    }

    moveUp() {
        let changed = false;
        for (let j = 0; j < 4; j++) {
            let column = [];
            for (let i = 0; i < 4; i++) {
                column.push(this.grid[i][j]);
            }
            column = this.slideAndMerge(column);
            for (let i = 0; i < 4; i++) {
                this.grid[i][j] = column[i];
            }
        }
        return changed;
    }

    moveDown() {
        let changed = false;
        for (let j = 0; j < 4; j++) {
            let column = [];
            for (let i = 0; i < 4; i++) {
                column.push(this.grid[i][j]);
            }
            column = this.slideAndMerge(column.reverse()).reverse();
            for (let i = 0; i < 4; i++) {
                this.grid[i][j] = column[i];
            }
        }
        return changed;
    }

    slideAndMerge(row) {
        // 移除零
        row = row.filter(val => val !== 0);

        // 合并相同的值
        for (let i = 0; i < row.length - 1; i++) {
            if (row[i] === row[i + 1]) {
                row[i] *= 2;
                this.score += row[i];
                row.splice(i + 1, 1);
            }
        }

        // 补充零
        while (row.length < 4) {
            row.push(0);
        }

        return row;
    }

    checkGameState() {
        // 检查是否赢了
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                if (this.grid[i][j] === 2048 && !this.won) {
                    this.won = true;
                    alert('恭喜！你赢了！');
                }
            }
        }

        // 检查是否游戏结束
        let hasEmpty = false;
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                if (this.grid[i][j] === 0) {
                    hasEmpty = true;
                    break;
                }
            }
        }

        if (!hasEmpty) {
            let canMove = false;
            for (let i = 0; i < 4; i++) {
                for (let j = 0; j < 4; j++) {
                    if ((j > 0 && this.grid[i][j] === this.grid[i][j - 1]) ||
                        (i > 0 && this.grid[i][j] === this.grid[i - 1][j])) {
                        canMove = true;
                        break;
                    }
                }
            }
            if (!canMove) {
                this.gameOver = true;
                alert(`游戏结束！最终分数: ${this.score}`);
                if (window.parent && window.parent.gameFinished) {
                    window.parent.gameFinished(this.score, 1);
                }
            }
        }
    }

    render() {
        const gameGrid = document.getElementById('gameGrid');
        const scoreDisplay = document.getElementById('score');
        const bestScoreDisplay = document.getElementById('bestScore');

        gameGrid.innerHTML = '';

        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 4; j++) {
                const value = this.grid[i][j];
                const tile = document.createElement('div');
                tile.className = 'tile';
                if (value !== 0) {
                    tile.setAttribute('data-value', value);
                    tile.textContent = value;
                }
                gameGrid.appendChild(tile);
            }
        }

        scoreDisplay.textContent = this.score;
        const bestScore = parseInt(localStorage.getItem('bestScore2048') || '0');
        if (this.score > bestScore) {
            localStorage.setItem('bestScore2048', this.score);
        }
        bestScoreDisplay.textContent = Math.max(this.score, bestScore);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new Game2048();
});
