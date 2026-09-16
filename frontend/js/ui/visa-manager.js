/**
 * 签证管理
 * 受 GPL v3.0 保护
 *
 * 从差异自动生成。
 */
class VisaManager {
    constructor(containerId = 'visaManager') {
        this.containerId = containerId;
        this.visas = [];
    }

    init() { this.render(); this.loadVisas(); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>签证管理</h3>
                <div id="visaList"></div>
                <div id="visaDetail" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadVisas() {
        try {
            const res = await APIClient._fetch('/api/cost/visa');
            if (res && res.success) {
                this.visas = res.data || [];
                this.renderVisaList(this.visas);
            }
        } catch (e) {
            console.warn('加载签证失败', e);
        }
    }

    renderVisaList(list) {
        const el = document.getElementById('visaList');
        if (!el) return;
        if (!list || list.length === 0) {
            el.innerHTML = '<div style="color:#999;">无签证</div>';
            return;
        }
        el.innerHTML = list.map(v => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                <strong>${v.entity_id || v.id}</strong> · ¥${v.difference_amount || v.amount || 0}
                <button onclick="window.visaManager.showVisaDetail('${v.entity_id || v.id}')" style="font-size:11px;">详情</button>
                <button onclick="window.visaManager.approveVisa('${v.entity_id || v.id}')" style="font-size:11px;">审批</button>
            </div>
        `).join('');
    }

    showVisaDetail(visaId) {
        const v = this.visas.find(x => (x.entity_id || x.id) === visaId);
        if (!v) return;
        const el = document.getElementById('visaDetail');
        if (!el) return;
        el.innerHTML = `
            <h4>签证详情</h4>
            <div>金额：¥${v.difference_amount || v.amount || 0}</div>
            <div>原因：${v.reason || ''}</div>
            <h4>证据</h4>
            <div style="font-size:11px;">照片×3 · 坐标 · 时间戳</div>
        `;
    }

    renderEvidence(evidence) { return ''; }
    renderAutoGenerate(diff) {
        if (Math.abs(diff) > 5) {
            return `<div style="color:#faad14;">⚠️ 差异超阈值，将自动生成签证</div>`;
        }
        return '';
    }

    approveVisa(visaId) {
        return APIClient._fetch('/api/workflow/start', {
            method: 'POST',
            body: JSON.stringify({ workflow_type: '签证', instance_data: { visa_id: visaId } }),
        }).then(() => this.loadVisas());
    }

    rejectVisa(visaId, reason) {
        return APIClient._fetch('/api/workflow/reject', {
            method: 'POST',
            body: JSON.stringify({ instance_id: visaId, role: '甲方', reason }),
        });
    }

    markPaid(visaId) {
        return APIClient._fetch('/api/workflow/approve', {
            method: 'POST',
            body: JSON.stringify({ instance_id: visaId, role: '甲方财务', comment: '已支付' }),
        });
    }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '签证生成' || eventType === '签证支付') this.loadVisas();
    }
}

window.VisaManager = VisaManager;
window.visaManager = new VisaManager();