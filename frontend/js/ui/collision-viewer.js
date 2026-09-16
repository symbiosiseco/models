/**
 * 碰撞查看器
 * 受 GPL v3.0 保护
 */
class CollisionViewer {
    constructor(containerId = 'collisionViewer') {
        this.containerId = containerId;
        this.collisions = [];
        this.filter = 'all';
    }

    init() { this.render(); this.loadCollisions(); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>碰撞检测</h3>
                <div id="collisionSummary"></div>
                <div id="collisionFilter" style="margin:8px 0;"></div>
                <div id="collisionList"></div>
            </div>
        `;
    }

    async loadCollisions() {
        try {
            const res = await APIClient.getCollisions();
            if (res && res.success) {
                this.collisions = res.data || [];
                this.renderSummary();
                this.renderFilter();
                this.render();
            }
        } catch (e) {
            console.warn('加载碰撞失败', e);
        }
    }

    renderSummary() {
        const el = document.getElementById('collisionSummary');
        if (!el) return;
        const red = this.collisions.filter(c => c.severity === 'red').length;
        const yellow = this.collisions.filter(c => c.severity === 'yellow').length;
        el.innerHTML = `<div>🔴 物理穿透：${red}个</div><div>🟡 规范预警：${yellow}个</div>`;
    }

    renderFilter() {
        const el = document.getElementById('collisionFilter');
        if (!el) return;
        const filters = [
            { id: 'all', label: '全部' },
            { id: 'red', label: '红色' },
            { id: 'yellow', label: '黄色' },
        ];
        el.innerHTML = filters.map(f =>
            `<button onclick="window.collisionViewer.filterBySeverity('${f.id}')"
                style="padding:2px 8px;margin-right:4px;font-size:11px;
                background:${this.filter === f.id ? '#e6f7ff' : '#fff'};
                border:1px solid ${this.filter === f.id ? '#1677ff' : '#d9d9d9'};border-radius:3px;cursor:pointer;">
                ${f.label}</button>`
        ).join('');
    }

    render() {
        const el = document.getElementById('collisionList');
        if (!el) return;
        let list = this.collisions;
        if (this.filter !== 'all') list = list.filter(c => c.severity === this.filter);
        if (list.length === 0) {
            el.innerHTML = '<div style="color:#999;">无碰撞</div>';
            return;
        }
        el.innerHTML = list.map(c => this.renderCollision(c)).join('');
    }

    renderCollision(c) {
        const color = c.severity === 'red' ? '#ff4d4f' : '#faad14';
        return `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;border-left:3px solid ${color};font-size:12px;">
                <strong>${c.entity1} ↔ ${c.entity2}</strong>
                <div style="color:#666;">${c.type} · ${c.detail || ''}</div>
                <button onclick="window.collisionViewer.highlightIn3D('${c.entity1}','${c.entity2}')" style="font-size:11px;">3D高亮</button>
            </div>
        `;
    }

    filterBySeverity(severity) {
        this.filter = severity;
        this.renderFilter();
        this.render();
    }

    highlightIn3D(e1, e2) {
        if (window.state && window.state.renderer) {
            window.state.renderer.select(e1);
        }
    }

    resolveCollision(collisionId) {
        return APIClient._fetch(`/api/collision/${collisionId}/resolve`, {
            method: 'POST',
            body: JSON.stringify({ resolution: 'auto' }),
        }).then(() => this.loadCollisions());
    }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '碰撞解决') this.loadCollisions();
    }
}

window.CollisionViewer = CollisionViewer;
window.collisionViewer = new CollisionViewer();