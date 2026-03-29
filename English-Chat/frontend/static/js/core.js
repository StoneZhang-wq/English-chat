// LocalCache - 本地缓存管理类
class LocalCache {
    constructor(ttlMinutes = 5) {
        this.ttl = ttlMinutes * 60 * 1000; // 转换为毫秒
        this.prefix = 'voice_chat_cache_';
    }

    // 生成缓存键
    _makeKey(key) {
        return `${this.prefix}${key}`;
    }

    // 获取缓存
    get(key) {
        try {
            const fullKey = this._makeKey(key);
            const item = localStorage.getItem(fullKey);
            if (!item) return null;

            const data = JSON.parse(item);

            // 检查是否过期
            if (Date.now() > data.expiresAt) {
                localStorage.removeItem(fullKey);
                return null;
            }

            return data.value;
        } catch (e) {
            console.warn('Cache get error:', e);
            return null;
        }
    }

    // 设置缓存
    set(key, value, customTTL = null) {
        try {
            const fullKey = this._makeKey(key);
            const ttl = customTTL || this.ttl;
            const data = {
                value,
                expiresAt: Date.now() + ttl
            };
            localStorage.setItem(fullKey, JSON.stringify(data));
        } catch (e) {
            console.warn('Cache set error:', e);
        }
    }

    // 删除缓存
    delete(key) {
        try {
            const fullKey = this._makeKey(key);
            localStorage.removeItem(fullKey);
        } catch (e) {
            console.warn('Cache delete error:', e);
        }
    }

    // 按前缀删除缓存
    deletePattern(pattern) {
        try {
            const prefix = this._makeKey(pattern);
            const keys = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith(prefix)) {
                    keys.push(key);
                }
            }
            keys.forEach(key => localStorage.removeItem(key));
        } catch (e) {
            console.warn('Cache deletePattern error:', e);
        }
    }

    // 清空所有缓存
    clear() {
        try {
            const keys = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith(this.prefix)) {
                    keys.push(key);
                }
            }
            keys.forEach(key => localStorage.removeItem(key));
        } catch (e) {
            console.warn('Cache clear error:', e);
        }
    }

    // 清理过期缓存
    cleanup() {
        try {
            const now = Date.now();
            const keys = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith(this.prefix)) {
                    keys.push(key);
                }
            }
            keys.forEach(key => {
                try {
                    const item = localStorage.getItem(key);
                    if (item) {
                        const data = JSON.parse(item);
                        if (now > data.expiresAt) {
                            localStorage.removeItem(key);
                        }
                    }
                } catch (e) {
                    // 忽略解析错误，删除无效条目
                    localStorage.removeItem(key);
                }
            });
        } catch (e) {
            console.warn('Cache cleanup error:', e);
        }
    }
}

class BaseMethod {
    constructor(baseURL = '') {
        this.apiBase = baseURL;

        // Auth state（使用 sessionStorage：关闭标签/浏览器后失效，需重新登录）
        this.token = typeof sessionStorage !== 'undefined' && sessionStorage.getItem('token');
        this.currentUser = typeof sessionStorage !== 'undefined' && sessionStorage.getItem('current_account');

        // Sync token from sessionStorage to cookie for image loading
        if (this.token) {
            document.cookie = `token=${this.token}; path=/; SameSite=Lax`;
        }

        // 初始化本地缓存 (5分钟TTL)
        this.cache = new LocalCache(5);
    }

    SetToken(token) {
        this.token = token
    }

     // API 方法
    async api(endpoint, options = {}) {
        const timeout = options.timeout || 300000; // 默认 300 秒
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);

        // 构建基础请求配置
        const defaults = {
            cache: 'no-store',
            signal: controller.signal
        };

        // 设置 Content-Type（对于 FormData 让浏览器自动处理）
        if (!(options.body instanceof FormData)) {
            defaults.headers = {
                'Content-Type': 'application/json',
            };
        } else {
            defaults.headers = {};
        }

        // 添加认证头
        if (this.token) {
            defaults.headers['Authorization'] = `Bearer ${this.token}`;
        }

        // 构造 URL，为 GET 请求添加时间戳避免缓存
        let url = `${this.apiBase}${endpoint}`;
        if (!options.method || options.method === 'GET') {
            const separator = url.includes('?') ? '&' : '?';
            url += `${separator}_t=${Date.now()}`;
        }

        try {
            const merged = { ...defaults, ...options };
            if (options.headers && defaults.headers) {
                merged.headers = { ...defaults.headers, ...options.headers };
            }
            const response = await fetch(url, merged);
            clearTimeout(id);

            // 处理 204 No Content
            if (response.status === 204) {
                return null;
            }
            if (!response.ok) {
                let errorMsg = '请求失败';
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorData.message || errorMsg;
                } catch {
                    // 如果 JSON 解析失败，尝试读取文本
                    try {
                        errorMsg = await response.text() || errorMsg;
                    } catch {
                        // 忽略，使用默认错误信息
                    }
                }
                throw new Error(errorMsg);
            }

            // 响应成功，解析 JSON 并返回数据部分
            const result = await response.json();
            return result.data; // 假设 API 返回的数据在 data 字段中

        } catch (error) {
            clearTimeout(id); // 确保超时定时器被清除
            if (error.name === 'AbortError') {
                throw new Error('请求超时，请稍后重试');
            }
            throw error; // 重新抛出其他错误
        }
    }

    /**
     * 使用认证头拉取音频并返回 Blob Object URL，用于 TTS 等需要登录的音频播放。
     * 调用方在播放结束后应调用 URL.revokeObjectURL(url) 释放内存。
     * @param {string} audioPath - 相对路径，如 "/audio/tts/xxx.wav"
     * @returns {Promise<string>} 可传给 Audio 的 object URL
     */
    async fetchAudioAsObjectUrl(audioPath) {
        if (!audioPath) return Promise.reject(new Error('audio path is required'));
        const url = audioPath.startsWith('http') ? audioPath : (window.location.origin + audioPath);
        const headers = {};
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        const response = await fetch(url, { method: 'GET', headers, cache: 'no-store' });
        if (!response.ok) {
            const err = new Error(response.statusText || 'Failed to load audio');
            err.status = response.status;
            throw err;
        }
        const blob = await response.blob();
        return URL.createObjectURL(blob);
    }
}

// 创建全局 BaseApi 实例
const BaseApi = new BaseMethod('');
