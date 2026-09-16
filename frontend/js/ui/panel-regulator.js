/**
 * 监管面板
 * 受 GPL v3.0 保护
 *
 * 只读，事件驱动自动刷新。
 */
class RegulatorPanel {
    constructor(containerId = 'regulatorPanel') {
        this.containerId = containerId;
        this.warnings = [];
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
                <h3>监管 · 政府监督</h3>
                <div id="regulatorQuality"></div>
                <div id="regulatorSafety" style="margin-top:12px;"></div>
                <div id="regulatorCompliance" style="margin-top:12px;"></div>
                <div id="regulatorWarnings" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient.getCollisions();
            const collisions = (res && res.data) || [];
            const red = collisions.filter(c => c.severity === 'red').length;
            const yellow = collisions.filter(c => c.severity === 'yellow').length;
            this.renderQuality({ score: 92, issues: 3 });
            this.renderSafety({ score: 88, hazards: red });
            this.renderCompliance({ compliance: yellow === 0, violations: yellow });
            this.renderWarningHistory(this.warnings);
        } catch (e) {
            console.warn('加载监管数据失败', e);
        }
    }

    renderQuality(quality) {
        const el = document.getElementById('regulatorQuality');
        if (!el) return;
        el.innerHTML = `<h4>质量监督</h4><p>质量得分：${quality.score}分</p><p>问题：${quality.issues}个</p>`;
    }

    renderSafety(safety) {
        const el = document.getElementById('regulatorSafety');
        if (!el) return;
        el.innerHTML = `<h4>安全监督</h4><p>安全得分：${safety.score}分</p><p>隐患：${safety.hazards}个</p>`;
    }

    renderCompliance(compliance) {
        const el = document.getElementById('regulatorCompliance');
        if (!el) return;
        el.innerHTML = `<h4>合规检查</h4><p>合规：${compliance.compliance ? '是' : '否'}</p><p>违规：${compliance.violations}个</p>`;
    }

    renderWarningHistory(warnings) {
        const el = document.getElementById('regulatorWarnings');
        if (!el) return;
        if (!warnings || warnings.length === 0) {
            el.innerHTML = '<h4>警告历史</h4><div style="color:#999;">暂无</div>';
            return;
        }
        el.innerHTML = '<h4>警告历史</h4>' + warnings.map(w => `
            <div style="font-size:11px;color:#666;">${w.time || ''} · ${w.content || ''}</div>
        `).join('');
    }

    async issueWarning(warning) {
        try {
            const res = await APIClient._fetch('/api/collision/check_all', { method: 'POST' });
            this.warnings.push({ content: warning, time: new Date().toLocaleString() });
            this.renderWarningHistory(this.warnings);
        } catch (e) {
            alert('下发警告失败：' + e.message);
        }
    }

    viewEntityDetail(entityId) {
        return APIClient.getEntity(entityId);
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === 'L3变化' || eventType === '验收通过' || eventType === '验收不通过') {
            this.loadData();
        }
    }
}

window.RegulatorPanel = RegulatorPanel;
window.regulatorPanel = new RegulatorPanel();