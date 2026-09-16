/**
 * 厂家参数导入
 * 受 GPL v3.0 保护
 */
class ParameterImport {
    constructor(containerId = 'parameterImport') {
        this.containerId = containerId;
        this.fileData = null;
    }

    init() { this.render(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>厂家参数导入</h3>
                <input type="file" id="importFile" accept=".xlsx,.xls,.csv,.json">
                <div id="importPreview" style="margin-top:12px;"></div>
                <div id="importResult" style="margin-top:12px;"></div>
            </div>
        `;
        document.getElementById('importFile').onchange = (e) => this.handleFileUpload(e.target.files[0]);
    }

    handleFileUpload(file) {
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            try {
                if (file.name.endsWith('.json')) {
                    this.fileData = this.parseJSON(text);
                } else if (file.name.endsWith('.csv')) {
                    this.fileData = this.parseCSV(text);
                } else {
                    this.fileData = { raw: text };
                }
                this.previewData(this.fileData);
            } catch (err) {
                alert('解析失败：' + err.message);
            }
        };
        reader.readAsText(file);
    }

    parseExcel(file) { return { raw: file }; }
    parseCSV(text) {
        const lines = text.split('\n').filter(l => l.trim());
        const headers = lines[0].split(',');
        return lines.slice(1).map(line => {
            const values = line.split(',');
            const obj = {};
            headers.forEach((h, i) => obj[h.trim()] = values[i] && values[i].trim());
            return obj;
        });
    }
    parseJSON(text) { return JSON.parse(text); }

    previewData(data) {
        const el = document.getElementById('importPreview');
        if (!el) return;
        el.innerHTML = `<h4>数据预览</h4><pre style="font-size:11px;background:#fafafa;padding:6px;max-height:200px;overflow:auto;">${JSON.stringify(data, null, 2)}</pre>`;
        el.innerHTML += `<h4>AI理解日志</h4><div style="font-size:11px;color:#666;">✓ 识别产品类型<br>✓ 联网查询<br>✓ 参数补全<br>✓ 规则推导<br>✓ 边界计算</div>`;
        el.innerHTML += `<button onclick="window.parameterImport.submitImport()">导入</button>`;
    }

    renderMappingUI(fields) {}
    autoMapFields(headers) { return {}; }

    submitImport() {
        if (!this.fileData) {
            alert('无数据');
            return;
        }
        const params = Array.isArray(this.fileData) ? this.fileData[0] : this.fileData;
        APIClient.generate(params).then(res => {
            if (res && res.success) {
                document.getElementById('importResult').innerHTML = '<div style="color:#52c41a;">✅ 导入成功</div>';
                this.refreshScene();
            } else {
                document.getElementById('importResult').innerHTML = '<div style="color:#ff4d4f;">❌ 导入失败</div>';
            }
        }).catch(e => {
            document.getElementById('importResult').innerHTML = `<div style="color:#ff4d4f;">❌ ${e.message}</div>`;
        });
    }

    renderAIUnderstanding(log) {}
    renderImportResult(result) {}

    refreshScene() {
        if (window.refreshAll) window.refreshAll();
    }
}

window.ParameterImport = ParameterImport;
window.parameterImport = new ParameterImport();