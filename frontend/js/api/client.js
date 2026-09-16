/**
 * API 客户端
 * 受 GPL v3.0 保护
 *
 * 封装所有后端请求（含 WebSocket 订阅）。
 */
const APIClient = {
    baseURL: 'http://localhost:5000',
    wsURL: 'ws://localhost:5000/ws',
    timeout: 10000,
    _ws: null,
    _wsReconnectTimer: null,

    /**
     * 封装 fetch
     */
    async _fetch(url, options = {}) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.timeout);
        try {
            const res = await fetch(this.baseURL + url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...(options.headers || {}),
                },
            });
            clearTimeout(timer);
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return await res.json();
        } catch (e) {
            clearTimeout(timer);
            throw e;
        }
    },

    // ==================== 健康检查 ====================

    health() {
        return this._fetch('/api/health');
    },

    // ==================== 实体 ====================

    getEntities() {
        return this._fetch('/api/entities/');
    },

    getEntity(entityId) {
        return this._fetch(`/api/entities/${entityId}`);
    },

    getScene() {
        return this._fetch('/api/scene/');
    },

    getForcePoints(entityId) {
        return this._fetch(`/api/entities/${entityId}/force_points`);
    },

    getContactFaces(entityId) {
        return this._fetch(`/api/entities/${entityId}/contact_faces`);
    },

    getCBMStatus(entityId) {
        return this._fetch(`/api/entities/${entityId}/cbm`);
    },

    getL4(entityId) {
        return this._fetch(`/api/entities/${entityId}/l4`);
    },

    // ==================== 碰撞 ====================

    getCollisions() {
        return this._fetch('/api/collisions/');
    },

    getCollisionSummary() {
        return this._fetch('/api/collision/summary');
    },

    // ==================== 造价 ====================

    getCostSummary() {
        return this._fetch('/api/cost/summary');
    },

    getCostDetails() {
        return this._fetch('/api/cost/details');
    },

    // ==================== 装配 ====================

    getAssemblyTest() {
        return this._fetch('/api/entities/?type=装配测试');
    },

    assemble(partId, targetId) {
        return this._fetch('/api/assembly/assemble', {
            method: 'POST',
            body: JSON.stringify({ part_id: partId, target_id: targetId }),
        });
    },

    // ==================== 生成器 ====================

    generate(params) {
        return this._fetch('/api/generate', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    },

    generateBatch(paramsList) {
        return this._fetch('/api/generate_batch', {
            method: 'POST',
            body: JSON.stringify({ params_list: paramsList }),
        });
    },

    generateExample() {
        return this._fetch('/api/generate_example/');
    },

    // ==================== 模板 ====================

    getTemplates() {
        return this._fetch('/api/templates/');
    },

    getTemplate(templateId) {
        return this._fetch(`/api/templates/${templateId}`);
    },

    instantiateTemplate(templateId, position) {
        return this._fetch(`/api/templates/${templateId}/instantiate`, {
            method: 'POST',
            body: JSON.stringify({ position }),
        });
    },

    getTemplatesStats() {
        return this._fetch('/api/templates/stats/');
    },

    // ==================== 事件 ====================

    getEvents(filter = {}) {
        const params = new URLSearchParams(filter).toString();
        return this._fetch(`/api/events/?${params}`);
    },

    // ==================== CBM ====================

    getCBMStats() {
        return this._fetch('/api/cbm/stats');
    },

    // ==================== WebSocket ====================

    /**
     * 连接 WebSocket（使用 socket.io 客户端）。
     * @param {Function} onEvent - 事件回调
     * @returns {Socket}
     */
    connectWebSocket(onEvent) {
        if (this._ws && this._ws.connected) {
            return this._ws;
        }

        try {
            const socket = io('http://localhost:5000', {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: 5000,
            });
            this._ws = socket;

            socket.on('connect', () => {
                console.log('[WS] 连接成功');
                this._updateWSStatus(true);
                socket.emit('subscribe_events', {
                    event_types: [
                        'L3变化', '任务派发', '任务完成', '装配失败',
                        '接触面错误', '通知', '验收通过', '验收不通过',
                    ],
                });
            });

            socket.on('disconnect', () => {
                console.warn('[WS] 连接断开');
                this._updateWSStatus(false);
            });

            const eventTypes = [
                'L3变化', '任务派发', '任务完成', '装配失败',
                '接触面错误', '通知', '验收通过', '验收不通过',
                '签字', '签字完成', '流程完成', '换货触发',
            ];
            eventTypes.forEach(evt => {
                socket.on(evt, (data) => {
                    if (onEvent) onEvent({ event_type: evt, data });
                });
            });

            return socket;
        } catch (e) {
            console.error('[WS] 连接失败', e);
            this._updateWSStatus(false);
            return null;
        }
    },

    /**
     * 订阅事件类型。
     * @param {Array<string>} eventTypes
     */
    subscribeEvents(eventTypes) {
        if (!this._ws || !this._ws.connected) {
            console.warn('[WS] 未连接，无法订阅');
            return;
        }
        this._ws.emit('subscribe_events', { event_types: eventTypes });
    },

    /**
     * 订阅实体。
     */
    subscribeEntities(entityIds) {
        if (!this._ws || !this._ws.connected) return;
        this._ws.emit('subscribe', { entity_ids: entityIds });
    },

    _updateWSStatus(connected) {
        const el = document.getElementById('wsStatus');
        if (el) {
            el.textContent = connected ? '● 已连接' : '● 未连接';
            el.classList.toggle('connected', connected);
        }
    },
};

window.APIClient = APIClient;