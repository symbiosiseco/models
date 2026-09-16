/**
 * 甲方面板
 * 受 GPL v3.0 保护
 *
 * ProjectCBM进度，任务完成自动更新。
 */
class OwnerPanel {
    constructor(containerId = 'ownerPanel') {
        this.containerId = containerId;
        this.projectId = 'PROJ-001';
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
                <h3>甲方 · 项目管理</h3>
                <div id="ownerProgress"></div>
                <div id="ownerContract" style="margin-top:12px;"></div>
                <div id="ownerApprovals" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient._fetch(`/api/workflow/status/${this.projectId}`).catch(() => ({}));
            this.renderProgress(res.data || {});
            this.renderContract({});
            this.renderApprovals([]);
        } catch (e) {
            console.warn('加载甲方数据失败', e);
        }
    }

    renderProgress(progress) {
        const el = document.getElementById('ownerProgress');
        if (!el) return;
        el.innerHTML = `
            <h4>项目进度</h4>
            <div class="fp-gauge"><div class="fp-gauge-bar" style="width:${progress.percentage || 0}%"></div></div>
            <div>${progress.percentage || 0}%</div>
        `;
    }

    renderApprovals(approvals) {
        const el = document.getElementById('ownerApprovals');
        if (!el) return;
        if (!approvals || approvals.length === 0) {
            el.innerHTML = '<div style="color:#999;">无待审批</div>';
            return;
        }
        el.innerHTML = approvals.map(a => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;">
                ${a.id} · ${a.type}
                <button onclick="window.ownerPanel.approvePayment('${a.id}')">审批</button>
            </div>
        `).join('');
    }

    renderContract(contract) {
        const el = document.getElementById('ownerContract');
        if (!el) return;
        el.innerHTML = `<h4>合同总览</h4><p>合同金额：¥${contract.amount || 0}</p><p>已付：¥${contract.paid || 0}</p>`;
    }

    renderProjectCBM(projectCbm) {
        // 由 renderProgress 处理
    }

    async approvePayment(paymentId) {
        try {
            const res = await APIClient._fetch('/api/workflow/start', {
                method: 'POST',
                body: JSON.stringify({ workflow_type: '进度款', instance_data: { payment_id: paymentId } }),
            });
            if (res && res.success) {
                alert('已提交审批流程');
                this.loadData();
            }
        } catch (e) {
            alert('审批失败：' + e.message);
        }
    }

    async approveChange(changeId) {
        try {
            const res = await APIClient._fetch('/api/workflow/start', {
                method: 'POST',
                body: JSON.stringify({ workflow_type: '变更', instance_data: { change_id: changeId } }),
            });
            if (res && res.success) {
                alert('已提交变更审批');
                this.loadData();
            }
        } catch (e) {
            alert('审批失败：' + e.message);
        }
    }

    rejectApproval(id, reason) {
        return APIClient._fetch('/api/workflow/reject', {
            method: 'POST',
            body: JSON.stringify({ instance_id: id, role: '甲方', reason }),
        });
    }

    viewSignatureFlow(flowId) {
        return APIClient._fetch(`/api/workflow/${flowId}/steps`);
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '任务完成' || eventType === '流程完成' || eventType === '签证生成') {
            this.loadData();
        }
    }
}

window.OwnerPanel = OwnerPanel;
window.ownerPanel = new OwnerPanel();