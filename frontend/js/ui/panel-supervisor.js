/**
 * 监理面板
 * 受 GPL v3.0 保护
 *
 * EntityCBM检查，L3变化待验收+1。
 */
class SupervisorPanel {
    constructor(containerId = 'supervisorPanel') {
        this.containerId = containerId;
        this.pending = [];
    }

    init() {
        this.render();
        this.loadData();
        this._subscribe_events();
    }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>监理 · 质量验收</h3>
                <div id="supervisorPending"></div>
                <div id="supervisorRecords" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient.getEntities();
            if (res && res.success) {
                const entities = res.data || [];
                this.pending = entities.filter(e => {
                    const st = e.layer && e.layer.l3_dynamic_state && e.layer.l3_dynamic_state['状态'];
                    return st === '已安装';
                });
                this.renderPendingInspections(this.pending);
            }
        } catch (e) {
            console.warn('加载监理数据失败', e);
        }
    }

    renderPendingInspections(list) {
        const el = document.getElementById('supervisorPending');
        if (!el) return;
        if (!list || list.length === 0) {
            el.innerHTML = '<div style="color:#999;">无待验收</div>';
            return;
        }
        el.innerHTML = '<h4>待验收</h4>' + list.map(e => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${e.id} · ${e.entity_type}
                <button onclick="window.supervisorPanel.accept('${e.id}', '合格')" style="font-size:11px;">验收</button>
                <button onclick="window.supervisorPanel.reject('${e.id}', '不合格')" style="font-size:11px;">整改</button>
            </div>
        `).join('');
    }

    renderInspectionRecords(records) {
        const el = document.getElementById('supervisorRecords');
        if (!el) return;
        el.innerHTML = '<h4>验收记录</h4><div style="color:#999;">暂无</div>';
    }

    renderEntityCBMStatus(entity) {
        // 由 loadData 处理
    }

    async accept(entityId, result) {
        try {
            const res = await APIClient._fetch('/api/workflow/start', {
                method: 'POST',
                body: JSON.stringify({ workflow_type: '验收', instance_data: { entity_id: entityId, result } }),
            });
            if (res && res.success) {
                this.loadData();
            }
        } catch (e) {
            alert('验收失败：' + e.message);
        }
    }

    async reject(entityId, reason) {
        try {
            await APIClient._fetch('/api/workflow/reject', {
                method: 'POST',
                body: JSON.stringify({ instance_id: entityId, role: '监理', reason }),
            });
            this.loadData();
        } catch (e) {
            alert('整改失败：' + e.message);
        }
    }

    signAcceptance(acceptanceId) {
        return APIClient._fetch('/api/workflow/approve', {
            method: 'POST',
            body: JSON.stringify({ instance_id: acceptanceId, role: '监理', comment: '同意' }),
        });
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === 'L3变化' && data.new_status === '已安装') {
            this.loadData();
        }
    }
}

window.SupervisorPanel = SupervisorPanel;
window.supervisorPanel = new SupervisorPanel();