/**
 * 导出面板
 * 受 GPL v3.0 保护
 *
 * 任务完成刷新。
 */
class ExportPanel {
    constructor(containerId = 'exportPanel') {
        this.containerId = containerId;
    }

    init() { this.render(); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>导出</h3>
                <div>报表类型：
                    <select id="exportReportType">
                        <option value="quantity">工程量清单</option>
                        <option value="payment">进度款</option>
                        <option value="acceptance">验收记录</option>
                        <option value="change">变更台账</option>
                        <option value="material">材料台账</option>
                        <option value="quality">质量记录</option>
                        <option value="asbuilt">竣工图</option>
                        <option value="visa">签证单</option>
                    </select>
                </div>
                <div style="margin-top:8px;">格式：
                    <select id="exportFormat">
                        <option value="excel">Excel</option>
                        <option value="pdf">PDF</option>
                        <option value="json">JSON</option>
                    </select>
                </div>
                <button onclick="window.exportPanel.exportExcel()" style="margin-top:8px;">导出</button>
                <div id="exportProgress" style="margin-top:8px;"></div>
            </div>
        `;
    }

    renderExportOptions() {}

    exportExcel() { this._doExport('excel'); }
    exportPDF() { this._doExport('pdf'); }
    exportJSON() { this._doExport('json'); }

    _doExport(format) {
        const reportType = document.getElementById('exportReportType').value;
        const el = document.getElementById('exportProgress');
        if (el) el.innerHTML = '导出中...';
        APIClient._fetch(`/api/export/report/${reportType}`, {
            method: 'POST',
            body: JSON.stringify({ format }),
        }).then(() => {
            if (el) el.innerHTML = '<div style="color:#52c41a;">✅ 导出成功</div>';
        }).catch(e => {
            if (el) el.innerHTML = `<div style="color:#ff4d4f;">❌ ${e.message}</div>`;
        });
    }

    exportEntityList(entities, format) {
        return APIClient._fetch('/api/export/entity_list', {
            method: 'POST',
            body: JSON.stringify({ format }),
        });
    }

    renderExportProgress(progress) {}
    downloadFile(filePath) { window.open(filePath); }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '任务完成') {
            this.renderExportOptions();
        }
    }
}

window.ExportPanel = ExportPanel;
window.exportPanel = new ExportPanel();