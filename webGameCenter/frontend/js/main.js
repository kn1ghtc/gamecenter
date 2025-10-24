/**
 * 主应用逻辑
 */

// 页面初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 检查用户登录状态
    await checkUserStatus();
    
    // 加载游戏分类
    await loadGameCategories();
    
    // 绑定事件
    bindEvents();
});

// 检查用户登录状态
async function checkUserStatus() {
    const token = api.getToken();
    const loginLink = document.getElementById('loginLink');
    const logoutBtn = document.getElementById('logoutBtn');
    const dashboardLink = document.getElementById('dashboardLink');
    const userStatsSection = document.getElementById('userStatsSection');
    
    if (token) {
        try {
            const profile = await api.getProfile();
            
            // 显示用户信息
            if (loginLink) loginLink.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = 'block';
            if (dashboardLink) dashboardLink.style.display = 'block';
            if (userStatsSection) userStatsSection.style.display = 'block';
            
            // 加载用户统计
            await loadUserStats(profile.id);
            
        } catch (error) {
            console.error('获取用户信息失败:', error);
            api.clearToken();
        }
    } else {
        if (loginLink) loginLink.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (dashboardLink) dashboardLink.style.display = 'none';
        if (userStatsSection) userStatsSection.style.display = 'none';
    }
}

// 加载用户统计
async function loadUserStats(userId) {
    try {
        const stats = await api.getUserStats(userId);
        
        document.getElementById('totalScore').textContent = formatNumber(stats.stats.total_score);
        document.getElementById('gamesPlayed').textContent = stats.stats.total_games;
        document.getElementById('maxScore').textContent = formatNumber(stats.stats.max_score);
        
        // 加载排名
        const rankData = await api.getUserRank();
        document.getElementById('userRank').textContent = `#${rankData.rank}`;
        
    } catch (error) {
        console.error('加载用户统计失败:', error);
    }
}

// 加载游戏分类
async function loadGameCategories() {
    try {
        const categories = await api.getCategories();
        const container = document.getElementById('categoriesContainer');
        
        let html = '';
        
        for (const category of categories) {
            html += `
                <div class="col-md-6 col-lg-4">
                    <div class="category-card" onclick="selectCategory('${category.id}', '${category.name}')">
                        <div class="category-card-header">
                            <div class="category-card-icon">
                                <i class="${category.icon}"></i>
                            </div>
                            <div class="category-card-title">${category.name}</div>
                            <div class="category-card-description">${category.description}</div>
                        </div>
                        <div class="category-card-footer">
                            <div class="game-count">${category.game_count}个游戏</div>
                            <button class="btn btn-primary btn-sm">选择分类</button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('加载游戏分类失败:', error);
        showError('加载游戏分类失败');
    }
}

// 加载所有游戏供选择
async function loadAllGamesForSelection() {
    try {
        const categories = await api.getCategories();
        const modal = new bootstrap.Modal(document.getElementById('gameSelectionModal'));
        document.getElementById('modalTitle').textContent = '选择游戏';
        
        let html = '';
        
        for (const category of categories) {
            const categoryGames = await api.getCategoryGames(category.id);
            
            // 添加分类标题
            html += `<div class="col-12 mt-3"><h6 class="text-primary fw-bold">${category.name}</h6></div>`;
            
            for (const game of categoryGames.games) {
                html += `
                    <div class="col-12">
                        <div class="game-item">
                            <div class="game-item-header">
                                <div class="game-item-icon">
                                    <i class="${game.icon}"></i>
                                </div>
                                <div>
                                    <div class="game-item-title">${game.name}</div>
                                    <div>${getDifficultyBadgeHTML(game.difficulty)}</div>
                                </div>
                            </div>
                            <div class="game-item-description">${game.description}</div>
                            <div class="game-item-stats">
                                <div class="game-item-stat">
                                    <i class="fas fa-play"></i>
                                    <span>${formatNumber(game.total_plays)}次游玩</span>
                                </div>
                                <div class="game-item-stat">
                                    <i class="fas fa-star"></i>
                                    <span>平均分: ${formatNumber(Math.round(game.average_score))}</span>
                                </div>
                            </div>
                            <button class="btn btn-play" onclick="launchGame('${game.game_id}')">
                                <i class="fas fa-play"></i> 开始游戏
                            </button>
                        </div>
                    </div>
                `;
            }
        }
        
        document.getElementById('gamesListContainer').innerHTML = html;
        modal.show();
        
    } catch (error) {
        console.error('加载游戏列表失败:', error);
        showError('加载游戏列表失败');
    }
}

// 选择分类
async function selectCategory(categoryId, categoryName) {
    if (!api.getToken()) {
        showError('请先登录');
        window.location.href = '/login.html';
        return;
    }
    
    try {
        const categoryGames = await api.getCategoryGames(categoryId);
        
        const modal = new bootstrap.Modal(document.getElementById('gameSelectionModal'));
        document.getElementById('modalTitle').textContent = `选择${categoryName}`;
        
        let html = '';
        for (const game of categoryGames.games) {
            html += `
                <div class="col-12">
                    <div class="game-item">
                        <div class="game-item-header">
                            <div class="game-item-icon">
                                <i class="${game.icon}"></i>
                            </div>
                            <div>
                                <div class="game-item-title">${game.name}</div>
                                <div>${getDifficultyBadgeHTML(game.difficulty)}</div>
                            </div>
                        </div>
                        <div class="game-item-description">${game.description}</div>
                        <div class="game-item-stats">
                            <div class="game-item-stat">
                                <i class="fas fa-play"></i>
                                <span>${formatNumber(game.total_plays)}次游玩</span>
                            </div>
                            <div class="game-item-stat">
                                <i class="fas fa-star"></i>
                                <span>平均分: ${formatNumber(Math.round(game.average_score))}</span>
                            </div>
                        </div>
                        <button class="btn btn-play" onclick="launchGame('${game.game_id}')">
                            <i class="fas fa-play"></i> 开始游戏
                        </button>
                    </div>
                </div>
            `;
        }
        
        document.getElementById('gamesListContainer').innerHTML = html;
        modal.show();
        
    } catch (error) {
        console.error('加载分类游戏失败:', error);
        showError('加载游戏失败');
    }
}

// 启动游戏
function launchGame(gameId) {
    window.location.href = `/game.html?id=${gameId}`;
}

// 绑定事件
function bindEvents() {
    // 开始游戏按钮
    const startPlayingBtn = document.getElementById('startPlayingBtn');
    if (startPlayingBtn) {
        startPlayingBtn.addEventListener('click', () => {
            const token = api.getToken();
            if (!token) {
                showError('请先登录');
                window.location.href = '/login.html';
            } else {
                // 显示游戏分类选择器
                const modal = new bootstrap.Modal(document.getElementById('gameSelectionModal'));
                const categories = Array.from(document.querySelectorAll('.category-card'));
                if (categories.length > 0) {
                    // 显示所有分类的游戏列表，用户可以选择
                    loadAllGamesForSelection();
                    modal.show();
                } else {
                    showError('暂无可用游戏');
                }
            }
        });
    }
    
    // 登出按钮
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            api.clearToken();
            window.location.href = '/';
        });
    }
}
