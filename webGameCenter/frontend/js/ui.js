/**
 * UI 工具函数
 */

// 显示通知
function showNotification(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertElement = document.createElement('div');
    alertElement.innerHTML = alertHTML;
    document.body.appendChild(alertElement);
    
    // 5秒后自动移除
    setTimeout(() => {
        alertElement.remove();
    }, 5000);
}

// 显示错误
function showError(message) {
    showNotification(message, 'danger');
}

// 显示成功
function showSuccess(message) {
    showNotification(message, 'success');
}

// 显示信息
function showInfo(message) {
    showNotification(message, 'info');
}

// 格式化数字
function formatNumber(num) {
    return new Intl.NumberFormat('zh-CN').format(num);
}

// 格式化时间
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}小时${minutes}分钟${secs}秒`;
    } else if (minutes > 0) {
        return `${minutes}分钟${secs}秒`;
    } else {
        return `${secs}秒`;
    }
}

// 获取难度徽章 HTML
function getDifficultyBadgeHTML(difficulty) {
    const badges = {
        'easy': '<span class="difficulty-badge difficulty-easy">简单</span>',
        'medium': '<span class="difficulty-badge difficulty-medium">中等</span>',
        'hard': '<span class="difficulty-badge difficulty-hard">困难</span>'
    };
    return badges[difficulty] || badges['medium'];
}

// 获取排名徽章
function getRankBadgeHTML(rank) {
    let badgeClass = 'rank-other';
    if (rank === 1) badgeClass = 'rank-1';
    else if (rank === 2) badgeClass = 'rank-2';
    else if (rank === 3) badgeClass = 'rank-3';
    
    return `<span class="rank-badge ${badgeClass}">#${rank}</span>`;
}

// 验证邮箱
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 验证用户名
function validateUsername(username) {
    return username.length >= 3 && username.length <= 20;
}

// 验证密码
function validatePassword(password) {
    return password.length >= 6;
}

// 生成随机颜色
function getRandomColor() {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b', '#fa709a', '#fee140'];
    return colors[Math.floor(Math.random() * colors.length)];
}

// 创建加载状态按钮
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span> 加载中...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || '确定';
    }
}

// 复制到剪贴板
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showSuccess('已复制到剪贴板');
    } catch (err) {
        showError('复制失败');
    }
}

// 数据表格渲染
function renderTable(containerId, headers, data, actions = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let html = '<table class="table table-hover"><thead><tr>';
    
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    
    if (actions) {
        html += '<th>操作</th>';
    }
    
    html += '</tr></thead><tbody>';
    
    data.forEach((row, index) => {
        html += '<tr>';
        headers.forEach(header => {
            const key = header.toLowerCase().replace(/\s+/g, '_');
            html += `<td>${row[key] || '-'}</td>`;
        });
        
        if (actions) {
            html += '<td>';
            actions.forEach(action => {
                html += action(row, index);
            });
            html += '</td>';
        }
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// 创建分页按钮
function createPaginationHTML(currentPage, totalPages, onPageChange) {
    let html = '<nav aria-label="Page navigation"><ul class="pagination">';
    
    // 上一页
    if (currentPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="event.preventDefault(); ${onPageChange}(${currentPage - 1})">上一页</a></li>`;
    } else {
        html += '<li class="page-item disabled"><span class="page-link">上一页</span></li>';
    }
    
    // 页码
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        if (i === currentPage) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="event.preventDefault(); ${onPageChange}(${i})">${i}</a></li>`;
        }
    }
    
    // 下一页
    if (currentPage < totalPages) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="event.preventDefault(); ${onPageChange}(${currentPage + 1})">下一页</a></li>`;
    } else {
        html += '<li class="page-item disabled"><span class="page-link">下一页</span></li>';
    }
    
    html += '</ul></nav>';
    return html;
}
