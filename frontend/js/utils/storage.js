/**
 * 本地存储工具
 * 受 GPL v3.0 保护
 */
const StorageUtils = {

    _memory: {},  // 降级内存

    _available() {
        try {
            const k = '__test__';
            localStorage.setItem(k, '1');
            localStorage.removeItem(k);
            return true;
        } catch (e) {
            return false;
        }
    },

    set(key, value) {
        const val = JSON.stringify(value);
        if (this._available()) {
            try {
                localStorage.setItem(key, val);
                return true;
            } catch (e) {
                console.warn('localStorage 写入失败', e);
            }
        }
        this._memory[key] = val;
        return true;
    },

    get(key, defaultVal = null) {
        let val;
        if (this._available()) {
            val = localStorage.getItem(key);
        }
        if (val === null || val === undefined) {
            val = this._memory[key];
        }
        if (val === null || val === undefined) return defaultVal;
        try {
            return JSON.parse(val);
        } catch (e) {
            return defaultVal;
        }
    },

    remove(key) {
        if (this._available()) {
            localStorage.removeItem(key);
        }
        delete this._memory[key];
        return true;
    },

    clear() {
        if (this._available()) {
            localStorage.clear();
        }
        this._memory = {};
        return true;
    },

    has(key) {
        return this.get(key, undefined) !== undefined;
    },

    setJSON(key, obj) {
        return this.set(key, obj);
    },

    getJSON(key, defaultVal = null) {
        return this.get(key, defaultVal);
    },

    // ==================== Token ====================

    setToken(token) {
        return this.set('token', token);
    },

    getToken() {
        return this.get('token', '');
    },

    clearToken() {
        return this.remove('token');
    },

    // ==================== User ====================

    setUser(user) {
        return this.set('user', user);
    },

    getUser() {
        return this.get('user', null);
    },

    // ==================== Preference ====================

    setPreference(key, value) {
        return this.set('pref_' + key, value);
    },

    getPreference(key, defaultVal = null) {
        return this.get('pref_' + key, defaultVal);
    },

    // ==================== Cache ====================

    setCache(key, value, ttl = 300) {
        const expireAt = Date.now() + ttl * 1000;
        return this.set('cache_' + key, { value, expireAt });
    },

    getCache(key) {
        const item = this.get('cache_' + key, null);
        if (!item) return null;
        if (item.expireAt && Date.now() > item.expireAt) {
            this.remove('cache_' + key);
            return null;
        }
        return item.value;
    },
};

window.StorageUtils = StorageUtils;