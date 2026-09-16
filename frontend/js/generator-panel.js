/**
 * 数字生命体生成器面板
 * 受 GPL v3.0 保护
 */
class GeneratorPanel {
    constructor() {
        this.panel = null;
        this.createFloatingButton();
        this.createPanel();
    }

    createFloatingButton() {
        const btn = document.createElement('button');
        btn.id = 'generatorPanelBtn';
        btn.textContent = '✨ 数字生命体生成器';
        btn.style.cssText = `
            position: fixed; top: 100px; right: 16px; z-index: 999;
            background: #722ed1; color: #fff; border: none;
            padding: 8px 12px; border-radius: 4px; cursor: pointer;
            font-size: 12px;
        `;
        btn.onclick = () => this.openPanel();
        document.body.appendChild(btn);
    }

    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'generatorPanel';
        panel.style.cssText = `
            position: fixed; top: 140px; right: 16px; z-index: 1000;
            width: 420px; max-height: 75vh; overflow-y: auto;
            background: #fff; border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            display: none; padding: 12px;
        `;
        panel.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <strong>✨ 数字生命体生成器</strong>
                <button onclick="window.generatorPanel.closePanel()" style="border:none;background:transparent;cursor:pointer;font-size:16px;">×</button>
            </div>
            <textarea id="generatorInput" style="width:100%;height:150px;font-family:monospace;font-size:11px;padding:6px;border:1px solid #d9d9d9;border-radius:4px;" placeholder="输入厂家参数JSON..."></textarea>
            <div style="margin-top:8px;display:flex;gap:8px;">
                <button onclick="window.generatorPanel.loadExample()" style="flex:1;padding:6px;border:1px solid #d9d9d9;background:#fff;border-radius:4px;cursor:pointer;">加载示例</button>
                <button onclick="window.generatorPanel.doGenerate()" style="flex:1;padding:6px;border:none;background:#722ed1;color:#fff;border-radius:4px;cursor:pointer;">生成</button>
            </div>
            <div id="generatorResult" style="margin-top:12px;"></div>
        `;
        document.body.appendChild(panel);
        this.panel = panel;
    }

    openPanel() {
        this.panel.style.display = 'block';
    }

    closePanel() {
        this.panel.style.display = 'none';
    }

    async loadExample() {
        try {
            const res = await APIClient.generateExample();
            if (res && res.success) {
                const el = document.getElementById('generatorInput');
                if (el) el.value = JSON.stringify(res.data, null, 2);
            }
        } catch (e) {
            alert('加载示例失败：' + e.message);
        }
    }

    async doGenerate() {
        const input = document.getElementById('generatorInput');
        if (!input) return;
        let params;
        try {
            params = JSON.parse(input.value);
        } catch (e) {
            alert('JSON格式错误');
            return;
        }

        const resultEl = document.getElementById('generatorResult');
        resultEl.innerHTML = '生成中...';

        try {
            if (Array.isArray(params)) {
                await this.doGenerateBatch(params, resultEl);
            } else {
                await this.doGenerateSingle(params, resultEl);
            }
        } catch (e) {
            resultEl.innerHTML = `<div style="color:#ff4d4f;">生成失败：${e.message}</div>`;
        }
    }

    async doGenerateSingle(params, resultEl) {
        const res = await APIClient.generate(params);
        if (res && res.success) {
            this.renderGeneratedEntity(res.data, resultEl);
            this.refreshScene();
        } else {
            resultEl.innerHTML = `<div style="color:#ff4d4f;">生成失败：${res && res.message ? res.message : '未知错误'}</div>`;
        }
    }

    async doGenerateBatch(arr, resultEl) {
        const res = await APIClient.generateBatch(arr);
        if (res && res.success) {
            resultEl.innerHTML = `<div style="color:#52c41a;">批量生成成功：${(res.data || []).length}个实体</div>`;
            this.refreshScene();
        } else {
            resultEl.innerHTML = `<div style="color:#ff4d4f;">批量生成失败</div>`;
        }
    }

    renderGeneratedEntity(entity, resultEl) {
        const logs = entity['生成日志'] || {};
        let html = `<div style="color:#52c41a;margin-bottom:8px;">✅ 生成成功：${entity.id}</div>`;

        // AI理解日志
        if (logs['ai理解']) {
            html += `<div style="margin-bottom:8px;"><strong>AI理解：</strong><pre style="font-size:10px;background:#fafafa;padding:4px;border-radius:3px;">${JSON.stringify(logs['ai理解'], null, 2)}</pre></div>`;
        }
        // 参数补全
        if (logs['参数补全']) {
            html += `<div style="margin-bottom:8px;"><strong>参数补全：</strong><pre style="font-size:10px;background:#fafafa;padding:4px;border-radius:3px;">${JSON.stringify(logs['参数补全'], null, 2)}</pre></div>`;
        }
        // 完整性验证
        if (logs['完整性验证']) {
            html += `<div style="margin-bottom:8px;"><strong>完整性验证：</strong><pre style="font-size:10px;background:#fafafa;padding:4px;border-radius:3px;">${JSON.stringify(logs['完整性验证'], null, 2)}</pre></div>`;
        }

        resultEl.innerHTML = html;
    }

    renderAIUnderstanding(log) {
        return `<pre style="font-size:10px;">${JSON.stringify(log, null, 2)}</pre>`;
    }

    renderGenerationManual(manual) {
        return `<pre style="font-size:10px;">${JSON.stringify(manual, null, 2)}</pre>`;
    }

    refreshScene() {
        if (window.refreshAll) window.refreshAll();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.generatorPanel = new GeneratorPanel();
});