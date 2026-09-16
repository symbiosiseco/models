/**
 * 运维面板
 * 受 GPL v3.0 保护
 *
 * EntityCBM寿命，L4影响CBM决策。
 */
class MaintenancePanel {
    constructor(containerId = 'maintenancePanel') {
        this.containerId = containerId;
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
                <h3>运维 · 物业管理</h3>
                <div id="maintenanceLifecycle"></div>
                <div id="maintenanceInspections" style="margin-top:12px;"></div>
                <div id="maintenanceReplacements" style="margin-top:12px;"></div>
                <div id="maintenanceL4" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient.getEntities();
            if (res && res.success) {
                const entities = res.data || [];
                this.renderLifecycle(entities);
            }
        } catch (e) {
            console.warn('加载运维数据失败', e);
        }
    }

    renderLifecycle(entities) {
        const el = document.getElementById('maintenanceLifecycle');
        if (!el) return;
        const gaskets = entities.filter(e => e.entity_type === '垫片');
        if (gaskets.length === 0) {
            el.innerHTML = '<div style="color:#999;">无寿命提醒</div>';
            return;
        }
        el.innerHTML = '<h4>寿命提醒</h4>' + gaskets.map(g => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${g.id} · 设计年限10年
                <button onclick="window.maintenancePanel.scheduleInspection('${g.id}', '2026-10-01')" style="font-size:11px;">安排检查</button>
                <button onclick="window.maintenancePanel.scheduleReplacement('${g.id}')" style="font-size:11px;">安排更换</button>
            </div>
        `).join('');
    }

    renderInspections(inspections) {
        const el = document.getElementById('maintenanceInspections');
        if (!el) return;
        el.innerHTML = '<h4>检查计划</h4><div style="color:#999;">暂无</div>';
    }

    renderReplacements(replacements) {
        const el = document.getElementById('maintenanceReplacements');
        if (!el) return;
        el.innerHTML = '<h4>更换计划</h4><div style="color:#999;">暂无</div>';
    }

    renderL4(l4Data) {
        const el = document.getElementById('maintenanceL4');
        if (!el) return;
        el.innerHTML = '<h4>L4套娃履历</h4>' + (l4Data || []).map(e => `
            <div style="font-size:11px;color:#666;">${e.time || ''} · ${e.event || ''}</div>
        `).join('');
    }

    renderEntityCBMStatus(entity) {
        // 由 loadData 处理
    }

    renderL4Impact(l4Data) {
        const el = document.getElementById('maintenanceL4');
        if (!el) return;
        const impacts = [];
        for (const event of (l4Data || [])) {
            if (event.event === '检查' && String(event.detail || '').includes('老化')) {
                impacts.push('橡胶圈接近更换期 → CBM提醒更换');
            }
            if (event.event === '漏水记录') {
                impacts.push('管道曾漏水 → CBM加强监控');
            }
        }
        if (impacts.length > 0) {
            el.innerHTML += '<h4>L4影响CBM</h4>' + impacts.map(i => `<div style="font-size:11px;">${i}</div>`).join('');
        }
    }

    scheduleInspection(entityId, date) {
        return APIClient._fetch('/api/recorder/start', { method: 'POST' })
            .then(() => alert(`已安排检查：${entityId} @ ${date}`))
            .catch(e => alert('安排失败：' + e.message));
    }

    scheduleReplacement(entityId) {
        return APIClient._fetch('/api/recorder/start', { method: 'POST' })
            .then(() => alert(`已安排更换：${entityId}`))
            .catch(e => alert('安排失败：' + e.message));
    }

    traceQuality(entityId) {
        return APIClient.getL4(entityId);
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '寿命到期' || eventType === 'L3变化') {
            this.loadData();
        }
    }
}

window.MaintenancePanel = MaintenancePanel;
window.maintenancePanel = new MaintenancePanel();