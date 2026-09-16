/**
 * 报表查看器
 * 受 GPL v3.0 保护
 *
 * 任务完成自动更新。
 */
class ReportViewer {
    constructor(containerId = 'reportViewer') {
        this.containerId = containerId;
        this.currentReportType = 'quantity';
        this.types = [
            { id: 'quantity', name: '工程量清单' },
            { id: 'payment', name: '进度款' },
            { id: 'acceptance', name: '验收记录' },
            { id: 'change', name: '变更台账' },
            { id: 'material', name: '材料台账' },
            { id: 'quality', name: '质量记录' },
            { id: 'asbuilt', name: '竣工图' },
            { id: 'visa', name: '签证单' },
        ];
    }

    init() {
        this.render();
        this._subscribe_events();
        this.show('quantity');
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
                <h3>报表查看器</h3>
                <div id="reportTabs" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;"></div>
                <div id="reportContent"></div>
                <div style="margin-top:12px;">
                    <button onclick="window.reportViewer.exportReport('excel')">导出Excel</button>
                    <button onclick="window.reportViewer.exportReport('pdf')">导出PDF</button>
                    <button onclick="window.reportViewer.exportReport('json')">导出JSON</button>
                </div>
            </div>
        `;
        const tabs = document.getElementById('reportTabs');
        tabs.innerHTML = this.types.map(t =>
            `<button onclick="window.reportViewer.show('${t.id}')"
                style="padding:4px 10px;border:1px solid ${t.id === this.currentReportType ? '#1677ff' : '#d9d9d9'};
                background:${t.id === this.currentReportType ? '#e6f7ff' : '#fff'};
                color:${t.id === this.currentReportType ? '#1677ff' : '#333'};
                border-radius:4px;cursor:pointer;font-size:12px;">${t.name}</button>`
        ).join('');
    }

    async show(reportType) {
        this.currentReportType = reportType;
        this.render();
        const el = document.getElementById('reportContent');
        if (!el) return;
        el.innerHTML = '加载中...';
        try {
            const res = await APIClient._fetch(`/api/report/${reportType}`);
            if (res && res.success) {
                this.renderTable(res.data || {});
            } else {
                el.innerHTML = '<div style="color:#999;">无数据</div>';
            }
        } catch (e) {
            el.innerHTML = `<div style="color:#ff4d4f;">加载失败：${e.message}</div>`;
        }
    }

    renderQuantityReport(data) { this.renderTable(data); }
    renderPaymentReport(data) { this.renderTable(data); }
    renderAcceptanceReport(data) { this.renderTable(data); }
    renderChangeReport(data) { this.renderTable(data); }
    renderMaterialReport(data) { this.renderTable(data); }
    renderQualityReport(data) { this.renderTable(data); }
    renderAsbuiltReport(data) { this.renderTable(data); }
    renderVisaReport(data) { this.renderTable(data); }

    renderTable(data) {
        const el = document.getElementById('reportContent');
        if (!el) return;
        if (!data || Object.keys(data).length === 0) {
            el.innerHTML = '<div style="color:#999;">无数据</div>';
            return;
        }
        el.innerHTML = `<pre style="font-size:11px;background:#fafafa;padding:8px;border-radius:4px;max-height:400px;overflow:auto;">${JSON.stringify(data, null, 2)}</pre>`;
    }

    exportReport(format) {
        APIClient._fetch(`/api/export/report/${this.currentReportType}`, {
            method: 'POST',
            body: JSON.stringify({ format }),
        }).then(() => alert('导出成功')).catch(e => alert('导出失败：' + e.message));
    }

    refresh() {
        this.show(this.currentReportType);
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '任务完成') {
            this.refresh();
        } else if (eventType === '签证生成' && this.currentReportType === 'visa') {
            this.refresh();
        }
    }
}

window.ReportViewer = ReportViewer;
window.reportViewer = new ReportViewer();