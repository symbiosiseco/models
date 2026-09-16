/**
 * 变更管理
 * 受 GPL v3.0 保护
 *
 * L4影响CBM。
 */
class ChangeManager {
    constructor(containerId = 'changeManager') {
        this.containerId = containerId;
        this.changes = [];
    }

    init() { this.render(); this.loadChanges(); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>变更管理</h3>
                <div id="changeList"></div>
                <div id="changeDetail" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadChanges() {
        try {
            const res = await APIClient.getEntities();
            if (res && res.success) {
                this.changes = (res.data || []).filter(e => e.entity_type === '变更');
                this.renderChangeList(this.changes);
            }
        } catch (e) {
            console.warn('加载变更失败', e);
        }
    }

    renderChangeList(list) {
        const el = document.getElementById('changeList');
        if (!el) return;
        if (!list || list.length === 0) {
            el.innerHTML = '<div style="color:#999;">无变更</div>';
            return;
        }
        el.innerHTML = list.map(c => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                <strong>${c.id}</strong>
                <button onclick="window.changeManager.showChangeDetail('${c.id}')" style="font-size:11px;">详情</button>
                <button onclick="window.changeManager.approveChange('${c.id}')" style="font-size:11px;">审批</button>
            </div>
        `).join('');
    }

    showChangeDetail(changeId) {
        const c = this.changes.find(x => x.id === changeId);
        if (!c) return;
        const el = document.getElementById('changeDetail');
        if (!el) return;
        const l2 = c.layer && c.layer.l2_static_attributes ? c.layer.l2_static_attributes : {};
        el.innerHTML = `
            <h4>变更详情</h4>
            <div>类型：${l2['变更类型'] || ''}</div>
            <div>原因：${l2['变更原因'] || ''}</div>
            <div>变更前：${JSON.stringify(l2['变更前状态'] || {})}</div>
            <div>变更后：${JSON.stringify(l2['变更后状态'] || {})}</div>
            <h4>L4影响CBM</h4>
            <div style="font-size:11px;">变更记录已写入L4，CBM将根据变更调整受力规则</div>
        `;
    }

    renderDiff(before, after) { return ''; }
    renderL4Impact(changeId) { return ''; }

    approveChange(changeId) {
        return APIClient._fetch('/api/workflow/start', {
            method: 'POST',
            body: JSON.stringify({ workflow_type: '变更', instance_data: { change_id: changeId } }),
        }).then(() => this.loadChanges());
    }

    rejectChange(changeId, reason) {
        return APIClient._fetch('/api/workflow/reject', {
            method: 'POST',
            body: JSON.stringify({ instance_id: changeId, role: '甲方', reason }),
        });
    }

    executeChange(changeId) {
        return APIClient._fetch('/api/workflow/approve', {
            method: 'POST',
            body: JSON.stringify({ instance_id: changeId, role: '施工员', comment: '执行' }),
        });
    }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '变更触发' || eventType === '变更审批') this.loadChanges();
    }
}

window.ChangeManager = ChangeManager;
window.changeManager = new ChangeManager();