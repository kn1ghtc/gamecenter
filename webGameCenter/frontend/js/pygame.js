/**
 * Pygame 本地游戏交互模块 — 负责 Pygame 游戏列表加载、启动、状态轮询和停止
 *
 * 依赖: api.js (全局 api 对象)
 */

/* ── 状态 ── */
let pygameStatusTimer = null;
let pygameGames = [];

/**
 * 加载 Pygame 游戏列表并渲染到 #pygameGamesContainer
 */
async function loadPygameGames() {
    const container = document.getElementById('pygameGamesContainer');
    if (!container) return;

    try {
        container.innerHTML = '<div class="text-center py-3"><div class="spinner"></div> 加载中...</div>';
        const resp = await fetch('/api/pygame/games');
        const data = await resp.json();
        pygameGames = data.games || [];
        renderPygameGames(container, pygameGames);
    } catch (err) {
        container.innerHTML = '<div class="text-center text-danger py-3">加载本地游戏失败</div>';
        console.error('loadPygameGames error:', err);
    }
}

/**
 * 渲染 Pygame 游戏卡片列表
 * @param {HTMLElement} container - 渲染目标容器
 * @param {Array} games - 游戏元数据数组
 */
function renderPygameGames(container, games) {
    if (!games.length) {
        container.innerHTML = '<div class="text-center text-muted py-3">暂未发现本地 Pygame 游戏</div>';
        return;
    }

    const categoryMap = {};
    games.forEach(g => {
        const cat = g.category || 'other';
        if (!categoryMap[cat]) categoryMap[cat] = [];
        categoryMap[cat].push(g);
    });

    const categoryNames = {
        strategy: '策略游戏', shooting: '射击游戏', puzzle: '益智游戏',
        action: '动作游戏', simulation: '模拟经营', other: '其他游戏'
    };

    let html = '';
    for (const [cat, catGames] of Object.entries(categoryMap)) {
        html += `<div class="col-12 mt-3"><h6 class="text-primary fw-bold">${categoryNames[cat] || cat}</h6></div>`;
        for (const game of catGames) {
            html += `
                <div class="col-md-6 col-lg-4">
                    <div class="pygame-card">
                        <div class="pygame-card-header">
                            <div class="pygame-card-icon"><i class="${game.icon || 'fas fa-gamepad'}"></i></div>
                            <div>
                                <div class="pygame-card-title">${escapeHtml(game.name)}</div>
                                <span class="badge bg-info">本地游戏</span>
                                <span class="badge bg-secondary">${escapeHtml(game.category || '')}</span>
                            </div>
                        </div>
                        <div class="pygame-card-desc">${escapeHtml(game.description || '')}</div>
                        <button class="btn btn-launch w-100" onclick="launchPygame('${escapeHtml(game.id)}')">
                            <i class="fas fa-rocket"></i> 启动游戏
                        </button>
                    </div>
                </div>`;
        }
    }
    container.innerHTML = `<div class="row g-3">${html}</div>`;
}

/**
 * 启动 Pygame 游戏
 * @param {string} gameId - 游戏 ID
 */
async function launchPygame(gameId) {
    try {
        showToast('正在启动游戏...', 'info');
        const resp = await fetch(`/api/pygame/launch/${encodeURIComponent(gameId)}`, {method: 'POST'});
        const data = await resp.json();

        if (resp.ok && data.status === 'launched') {
            showToast(`${data.game_name || gameId} 已启动`, 'success');
            startStatusPolling();
            updateRunningStatusBar(data);
        } else {
            showToast(data.message || data.error || '启动失败', 'error');
        }
    } catch (err) {
        showToast('启动游戏失败', 'error');
        console.error('launchPygame error:', err);
    }
}

/**
 * 检查 Pygame 运行状态
 */
async function checkPygameStatus() {
    try {
        const resp = await fetch('/api/pygame/status');
        const data = await resp.json();

        updateRunningStatusBar(data);

        if (!data.running) {
            stopStatusPolling();
        }
    } catch (err) {
        console.error('checkPygameStatus error:', err);
    }
}

/**
 * 停止当前运行的 Pygame 游戏
 */
async function stopPygame() {
    try {
        const resp = await fetch('/api/pygame/stop', {method: 'POST'});
        const data = await resp.json();

        if (data.status === 'stopped') {
            showToast('游戏已停止', 'success');
        } else {
            showToast(data.message || '没有运行中的游戏', 'info');
        }
        stopStatusPolling();
        updateRunningStatusBar({running: false});
    } catch (err) {
        showToast('停止游戏失败', 'error');
        console.error('stopPygame error:', err);
    }
}

/* ── 状态轮询 ── */

/**
 * 开始状态轮询（每 3 秒）
 */
function startStatusPolling() {
    stopStatusPolling();
    pygameStatusTimer = setInterval(checkPygameStatus, 3000);
}

/**
 * 停止状态轮询
 */
function stopStatusPolling() {
    if (pygameStatusTimer) {
        clearInterval(pygameStatusTimer);
        pygameStatusTimer = null;
    }
}

/* ── UI 辅助 ── */

/**
 * 更新顶部运行状态栏
 * @param {Object} status - 状态对象
 */
function updateRunningStatusBar(status) {
    const bar = document.getElementById('runningStatusBar');
    if (!bar) return;

    if (status && status.running) {
        const elapsed = status.elapsed_seconds ? Math.round(status.elapsed_seconds) : 0;
        bar.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <span>
                    <i class="fas fa-play-circle text-success"></i>
                    <strong>${escapeHtml(status.game_name || status.game_id)}</strong> 运行中
                    <span class="text-muted ms-2">${elapsed}s</span>
                </span>
                <button class="btn btn-sm btn-danger" onclick="stopPygame()">
                    <i class="fas fa-stop"></i> 停止
                </button>
            </div>`;
        bar.style.display = 'block';
    } else {
        bar.style.display = 'none';
        bar.innerHTML = '';
    }
}

/**
 * 显示 Toast 通知
 * @param {string} message - 消息文本
 * @param {string} type - 类型: 'success' | 'error' | 'info'
 */
function showToast(message, type) {
    // 移除已有 toast
    const old = document.getElementById('pygameToast');
    if (old) old.remove();

    const colorClass = type === 'success' ? 'toast-success' :
                       type === 'error' ? 'toast-error' : 'toast-info';

    const toast = document.createElement('div');
    toast.id = 'pygameToast';
    toast.className = `toast-notification ${colorClass}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

/**
 * HTML 转义
 * @param {string} str - 原始字符串
 * @returns {string} 转义后的安全字符串
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

/**
 * 页面加载时检查是否有游戏正在运行
 */
async function initPygameStatus() {
    try {
        const resp = await fetch('/api/pygame/status');
        const data = await resp.json();
        if (data.running) {
            updateRunningStatusBar(data);
            startStatusPolling();
        }
    } catch (_) {
        // 静默忽略
    }
}
