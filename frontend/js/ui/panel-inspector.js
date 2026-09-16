/**
 * 第三方检测面板
 * 受 GPL v3.0 保护
 */
class InspectorPanel {
    constructor(containerId = 'inspectorPanel') {
        this.containerId = containerId;
        this.tests = [];
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
                <h3>第三方检测 · 独立报告</h3>
                <div id="inspectorTests"></div>
                <div id="inspectorReports" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            this.renderTests(this.tests);
            this.renderReports([]);
        } catch (e) {
            console.warn('加载检测数据失败', e);
        }
    }

    renderTests(tests) {
        const el = document.getElementById('inspectorTests');
        if (!el) return;
        if (!tests || tests.length === 0) {
            el.innerHTML = '<div style="color:#999;">无检测</div>';
            return;
        }
        el.innerHTML = '<h4>检测列表</h4>' + tests.map(t => `
            <div style="font-size:12px;">${t.test_id} · ${t.test_type}</div>
        `).join('');
    }

    renderReports(reports) {
        const el = document.getElementById('inspectorReports');
        if (!el) return;
        el.innerHTML = '<h4>检测报告</h4><div style="color:#999;">暂无</div>';
    }

    testMaterial(materialId, testType) {
        const testId = 'TEST-' + Date.now();
        this.tests.push({ test_id: testId, material_id: materialId, test_type: testType || '材料检测' });
        this.renderTests(this.tests);
        return { success: true, test_id: testId, result: { passed: true } };
    }

    testQuality(entityId, testType) {
        const testId = 'TEST-' + Date.now();
        this.tests.push({ test_id: testId, entity_id: entityId, test_type: testType || '质量检测' });
        this.renderTests(this.tests);
        return { success: true, test_id: testId, result: { passed: true } };
    }

    testAssembly(entityId, testType) {
        const testId = 'TEST-' + Date.now();
        this.tests.push({ test_id: testId, entity_id: entityId, test_type: testType || '装配检测' });
        this.renderTests(this.tests);
        return { success: true, test_id: testId, checks: [] };
    }

    testContactFace(entityId, testType) {
        const testId = 'TEST-' + Date.now();
        this.tests.push({ test_id: testId, entity_id: entityId, test_type: testType || '接触面检测' });
        this.renderTests(this.tests);
        return { success: true, test_id: testId, checks: [] };
    }

    issueReport(testId, result) {
        const reportId = 'RPT-' + Date.now();
        this.renderReports([{ report_id: reportId, test_id: testId, result }]);
        return { success: true, report_id: reportId, file_path: `/tmp/${reportId}.pdf` };
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '检测请求' || eventType === '装配失败') {
            this.loadData();
        }
    }
}

window.InspectorPanel = InspectorPanel;
window.inspectorPanel = new InspectorPanel();