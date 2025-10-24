/**
 * API 客户端 - 处理所有后端 API 调用
 */

const API_BASE_URL = '/api';

class APIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    getToken() {
        return this.token;
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('access_token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            ...options,
            headers: this.getHeaders()
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '请求失败');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // 认证相关
    async register(username, email, password, avatar = '') {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password, avatar })
        });
    }

    async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    }

    async getProfile() {
        return this.request('/auth/profile', {
            method: 'GET'
        });
    }

    async updateProfile(avatar, email) {
        return this.request('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify({ avatar, email })
        });
    }

    // 游戏相关
    async getCategories() {
        return this.request('/games/categories', {
            method: 'GET'
        });
    }

    async getCategoryGames(categoryId) {
        return this.request(`/games/category/${categoryId}`, {
            method: 'GET'
        });
    }

    async getGameList(page = 1, perPage = 20) {
        return this.request(`/games/list?page=${page}&per_page=${perPage}`, {
            method: 'GET'
        });
    }

    async getGame(gameId) {
        return this.request(`/games/${gameId}`, {
            method: 'GET'
        });
    }

    async saveGameRecord(gameId, score, timePlayed, level, status, progress, gameState) {
        return this.request('/games/record', {
            method: 'POST',
            body: JSON.stringify({
                game_id: gameId,
                score,
                time_played: timePlayed,
                level,
                status,
                progress,
                game_state: gameState
            })
        });
    }

    async getGameRecords(page = 1, perPage = 20, gameId = null) {
        let url = `/games/records?page=${page}&per_page=${perPage}`;
        if (gameId) {
            url += `&game_id=${gameId}`;
        }
        return this.request(url, {
            method: 'GET'
        });
    }

    // 积分相关
    async getLeaderboard(limit = 100) {
        return this.request(`/scores/leaderboard?limit=${limit}`, {
            method: 'GET'
        });
    }

    async getGameLeaderboard(gameId, limit = 50) {
        return this.request(`/scores/game/${gameId}?limit=${limit}`, {
            method: 'GET'
        });
    }

    async getUserStats(userId) {
        return this.request(`/scores/user/${userId}`, {
            method: 'GET'
        });
    }

    async getUserRank() {
        return this.request('/scores/user/rank', {
            method: 'GET'
        });
    }
}

// 创建全局 API 客户端实例
const api = new APIClient();
