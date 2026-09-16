/**
 * 签字面板
 * 受 GPL v3.0 保护
 *
 * 7步流程可视化。
 */
class SignaturePanel {
    constructor(containerId = 'signaturePanel') {
        this.containerId = containerId;
        this.flowId = '';
        this.steps = [];
    }

    init() { this.render(); this.loadPendingSignatures(); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>签字面板</h3>
                <div id="signaturePending"></div>
                <div id="signatureFlow" style="margin-top:12px;"></div>
                <div id="signatureHistory" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadPendingSignatures() {
        try {
            const res = await APIClient._fetch('/api/workflow/templates');
            if (res && res.success) {
                this.renderPending([]);
            }
        } catch (e) {
            console.warn('加载签字失败', e);
        }
    }

    renderPending(list) {
        const el = document.getElementById('signaturePending');
        if (!el) return;
        if (!list || list.length === 0) {
            el.innerHTML = '<div style="color:#999;">无待签字</div>';
            return;
        }
        el.innerHTML = list.map(p => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${p.flow_id}
                <button onclick="window.signaturePanel.onSign('${p.flow_id}', '同意')" style="font-size:11px;">签字</button>
                <button onclick="window.signaturePanel.onReject('${p.flow_id}', '驳回')" style="font-size:11px;">驳回</button>
            </div>
        `).join('');
    }

    renderFlow(flowId) {
        const el = document.getElementById('signatureFlow');
        if (!el) return;
        const steps = ['施工员', '项目经理', '公司经理', '甲方工程师', '甲方项目负责人', '甲方成本', '甲方财务'];
        el.innerHTML = '<h4>7步签字流程</h4>' + steps.map((s, i) =>
            `<div style="font-size:12px;padding:2px 0;">${i + 1}. ${s} ${i === 0 ? '✅' : '⏸️'}</div>`
        ).join('');
    }

    renderStep(step, status) {
        const icon = status === 'done' ? '✅' : status === 'current' ? '⏳' : '⏸️';
        return `<div>${icon} ${step}</div>`;
    }

    renderSignatureHistory(flowId) {
        const el = document.getElementById('signatureHistory');
        if (!el) return;
        el.innerHTML = '<h4>签字历史</h4><div style="color:#999;">暂无</div>';
    }

    onSign(flowId, comment) {
        return APIClient._fetch('/api/workflow/approve', {
            method: 'POST',
            body: JSON.stringify({ instance_id: flowId, role: '施工员', comment }),
        }).then(() => this.loadPendingSignatures());
    }

    onReject(flowId, reason) {
        return APIClient._fetch('/api/workflow/reject', {
            method: 'POST',
            body: JSON.stringify({ instance_id: flowId, role: '施工员', reason }),
        }).then(() => this.loadPendingSignatures());
    }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '签字' || eventType === '签字完成' || eventType === '签字驳回') {
            this.loadPendingSignatures();
        }
    }
}

window.SignaturePanel = SignaturePanel;
window.signaturePanel = new SignaturePanel();