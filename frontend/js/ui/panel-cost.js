/**
 * 造价员面板
 * 受 GPL v3.0 保护
 *
 * 事件驱动，L3变化自动更新。
 */
class CostPanel {
    constructor(containerId = 'costPanel') {
        this.containerId = containerId;
        this.visas = [];
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
                <h3>造价明细</h3>
                <div id="costTable"></div>
                <div id="visaList" style="margin-top:12px;"></div>
                <div style="margin-top:12px;">
                    <button onclick="window.costPanel.exportCost('excel')">导出Excel</button>
                    <button onclick="window.costPanel.checkDifferences()">检查差异</button>
                </div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient.getCostDetails();
            if (res && res.success) {
                this.renderCostTable(res.data || []);
            }
            const visaRes = await APIClient._fetch('/api/cost/visa');
            if (visaRes && visaRes.success) {
                this.visas = visaRes.data || [];
                this.renderVisaList(this.visas);
            }
        } catch (e) {
            console.warn('加载造价失败', e);
        }
    }

    renderCostTable(items) {
        const el = document.getElementById('costTable');
        if (!el) return;
        if (!items || items.length === 0) {
            el.innerHTML = '<div style="color:#999;">无数据</div>';
            return;
        }
        let html = '<table style="width:100%;font-size:12px;border-collapse:collapse;">';
        html += '<tr style="background:#fafafa;"><th>类别</th><th>数量</th><th>单价</th><th>金额</th></tr>';
        let total = 0;
        for (const item of items) {
            total += item.amount || 0;
            html += `<tr><td>${item.category}</td><td>${item.quantity}</td><td>¥${item.unit_price}</td><td>${this.renderDiffHighlight(item.difference)}¥${item.amount}</td></tr>`;
        }
        html += `<tr style="font-weight:600;"><td>合计</td><td></td><td></td><td>¥${total.toFixed(2)}</td></tr>`;
        html += '</table>';
        el.innerHTML = html;
    }

    renderVisaList(visas) {
        const el = document.getElementById('visaList');
        if (!el) return;
        if (!visas || visas.length === 0) {
            el.innerHTML = '<div style="color:#999;">无签证</div>';
            return;
        }
        el.innerHTML = '<h4>签证列表</h4>' + visas.map(v => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                <strong>${v.entity_id}</strong> · ${v.category} · 差异 ${v.difference} · ¥${v.difference_amount}
            </div>
        `).join('');
    }

    renderDiffHighlight(diff) {
        if (diff === undefined || diff === null) return '';
        if (Math.abs(diff) > 5) {
            return '<span style="color:#ff4d4f;">';
        }
        return '';
    }

    renderCostChart(costData) {
        // 简化：不实现图表
    }

    async checkDifferences() {
        try {
            const res = await APIClient._fetch('/api/cost/check_differences', { method: 'POST' });
            if (res && res.success) {
                this.loadData();
            }
        } catch (e) {
            alert('检查差异失败：' + e.message);
        }
    }

    exportCost(format) {
        APIClient._fetch('/api/export/excel', {
            method: 'POST',
            body: JSON.stringify({ report_type: 'cost' }),
        }).then(() => alert('导出成功')).catch(e => alert('导出失败：' + e.message));
    }

    onVisaClick(visaId) {
        console.log('签证点击：', visaId);
    }

    refresh() {
        this.loadData();
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === 'L3变化' || eventType === '签证生成') {
            this.loadData();
        }
    }
}

window.CostPanel = CostPanel;
window.costPanel = new CostPanel();