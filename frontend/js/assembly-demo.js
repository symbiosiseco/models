/**
 * 装配演示面板
 * 受 GPL v3.0 保护
 */
class AssemblyDemo {
    constructor() {
        this.panel = null;
        this.data = null;
        this.createFloatingButton();
        this.createPanel();
    }

    createFloatingButton() {
        const btn = document.createElement('button');
        btn.id = 'assemblyDemoBtn';
        btn.textContent = '🔧 装配测试';
        btn.style.cssText = `
            position: fixed; top: 60px; right: 16px; z-index: 999;
            background: #1677ff; color: #fff; border: none;
            padding: 8px 12px; border-radius: 4px; cursor: pointer;
            font-size: 12px;
        `;
        btn.onclick = () => this.openPanel();
        document.body.appendChild(btn);
    }

    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'assemblyDemoPanel';
        panel.style.cssText = `
            position: fixed; top: 100px; right: 16px; z-index: 1000;
            width: 360px; max-height: 70vh; overflow-y: auto;
            background: #fff; border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            display: none; padding: 12px;
        `;
        panel.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <strong>🔧 装配测试</strong>
                <button onclick="window.assemblyDemo.closePanel()" style="border:none;background:transparent;cursor:pointer;font-size:16px;">×</button>
            </div>
            <div id="assemblyDemoContent">加载中...</div>
        `;
        document.body.appendChild(panel);
        this.panel = panel;
    }

    openPanel() {
        this.panel.style.display = 'block';
        this.loadData();
    }

    closePanel() {
        this.panel.style.display = 'none';
    }

    async loadData() {
        try {
            const res = await APIClient.getEntities();
            if (!res || !res.success) {
                this.showError('加载失败');
                return;
            }
            const entities = res.data || [];
            // 找目标法兰和待装配螺栓
            const flange = entities.find(e => e.entity_type === '法兰');
            const bolts = entities.filter(e => e.entity_type === '螺栓');

            this.data = { flange, bolts };
            this.renderContent();
        } catch (e) {
            this.showError('加载失败：' + e.message);
        }
    }

    renderContent() {
        const el = document.getElementById('assemblyDemoContent');
        if (!el) return;
        const { flange, bolts } = this.data || {};
        if (!flange) {
            el.innerHTML = '<div style="color:#999;">未找到目标法兰</div>';
            return;
        }

        let html = `
            <div style="margin-bottom:8px;">
                <strong>目标：</strong>${flange.id} (${flange.entity_type})
            </div>
            <div style="margin-bottom:8px;">
                <strong>待装配零件：</strong>
            </div>
        `;
        for (const b of bolts) {
            const spec = b.layer && b.layer.l2_static_attributes ? b.layer.l2_static_attributes['规格'] : '';
            html += `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;">
                    <span>${b.id} · ${spec}</span>
                    <button onclick="window.assemblyDemo.doAssemble('${b.id}','${flange.id}',this)"
                        style="padding:2px 8px;border:1px solid #1677ff;color:#1677ff;background:#fff;border-radius:3px;cursor:pointer;font-size:11px;">
                        装配
                    </button>
                </div>
            `;
        }
        el.innerHTML = html;
    }

    async doAssemble(partId, targetId, btn) {
        btn.disabled = true;
        btn.textContent = '装配中...';
        try {
            const res = await APIClient.assemble(partId, targetId);
            if (res && res.success) {
                btn.textContent = '✅ 已装配';
                btn.style.background = '#52c41a';
                btn.style.color = '#fff';
            } else {
                btn.textContent = '❌ 失败';
                btn.style.background = '#ff4d4f';
                btn.style.color = '#fff';
                this.showError(res && res.message ? res.message : '装配失败');
            }
        } catch (e) {
            btn.textContent = '❌ 失败';
            btn.style.background = '#ff4d4f';
            btn.style.color = '#fff';
            this.showError('装配失败：' + e.message);
        }
    }

    refreshScene() {
        if (window.refreshAll) window.refreshAll();
    }

    showError(message) {
        alert(message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.assemblyDemo = new AssemblyDemo();
});