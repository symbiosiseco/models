/**
 * 模板库面板
 * 受 GPL v3.0 保护
 */
class TemplatePanel {
    constructor() {
        this.panel = null;
        this.templates = [];
        this.currentCategory = '全部';
        this.createPanel();
    }

    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'templatePanel';
        panel.style.cssText = `
            position: fixed; top: 140px; right: 16px; z-index: 1000;
            width: 460px; max-height: 75vh; overflow-y: auto;
            background: #fff; border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            display: none; padding: 12px;
        `;
        panel.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <strong>📚 模板库</strong>
                <button onclick="window.templatePanel.close()" style="border:none;background:transparent;cursor:pointer;font-size:16px;">×</button>
            </div>
            <div id="templateTabs" style="display:flex;gap:4px;margin-bottom:8px;"></div>
            <div id="templateList"></div>
            <div id="templateDetail" style="margin-top:12px;"></div>
        `;
        document.body.appendChild(panel);
        this.panel = panel;
    }

    open() {
        this.panel.style.display = 'block';
        this.renderTabs();
        this.loadTemplates();
    }

    close() {
        this.panel.style.display = 'none';
    }

    renderTabs() {
        const el = document.getElementById('templateTabs');
        if (!el) return;
        const cats = ['全部', '物品', '人员', '设备', '任务'];
        el.innerHTML = cats.map(c =>
            `<button onclick="window.templatePanel.switchCategory('${c}')"
                style="padding:4px 10px;border:1px solid ${c === this.currentCategory ? '#1677ff' : '#d9d9d9'};
                background:${c === this.currentCategory ? '#e6f7ff' : '#fff'};
                color:${c === this.currentCategory ? '#1677ff' : '#333'};
                border-radius:4px;cursor:pointer;font-size:12px;">${c}</button>`
        ).join('');
    }

    switchCategory(cat) {
        this.currentCategory = cat;
        this.renderTabs();
        this.renderList();
    }

    async loadTemplates() {
        try {
            const res = await APIClient.getTemplates();
            if (res && res.success) {
                this.templates = res.data || [];
                this.renderList();
            }
        } catch (e) {
            const el = document.getElementById('templateList');
            if (el) el.innerHTML = '<div style="color:#999;">加载失败</div>';
        }
    }

    renderList() {
        const el = document.getElementById('templateList');
        if (!el) return;
        let list = this.templates;
        if (this.currentCategory !== '全部') {
            list = list.filter(t => t.category === this.currentCategory);
        }
        if (list.length === 0) {
            el.innerHTML = '<div style="color:#999;">无模板</div>';
            return;
        }
        el.innerHTML = list.map(t => `
            <div onclick="window.templatePanel.renderTemplateDetail('${t.template_id}')"
                style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;cursor:pointer;">
                <strong>${t.name || t.template_id}</strong>
                <span style="color:#999;font-size:11px;margin-left:8px;">${t.category} · ${t.entity_type} · ${t.spec}</span>
            </div>
        `).join('');
    }

    async renderTemplateDetail(templateId) {
        try {
            const res = await APIClient.getTemplate(templateId);
            if (!res || !res.success) return;
            const t = res.data;
            const el = document.getElementById('templateDetail');
            if (!el) return;

            let html = `<h4>${t.name}</h4>`;
            html += `<div><strong>模板ID：</strong>${t.template_id}</div>`;
            html += `<div><strong>类别：</strong>${t.category}</div>`;
            html += `<div><strong>实体类型：</strong>${t.entity_type}</div>`;
            html += `<div><strong>厂家：</strong>${t.manufacturer || ''}</div>`;
            html += `<div><strong>规格：</strong>${t.spec || ''}</div>`;

            // 受力点
            const fps = t.force_points || [];
            html += `<div style="margin-top:8px;"><strong>受力点：</strong>${fps.length}个</div>`;
            for (const fp of fps) {
                html += `<div style="font-size:11px;color:#666;">· ${fp.id} · ${fp['类型'] || ''} · ${fp['承重上限'] || ''}</div>`;
            }

            // 接触面
            const cfs = t.contact_faces || [];
            html += `<div style="margin-top:8px;"><strong>接触面：</strong>${cfs.length}个</div>`;
            for (const cf of cfs) {
                html += `<div style="font-size:11px;color:#666;">· ${cf.id} · ${cf['类型'] || ''} · 必须包含：${(cf['必须包含'] || []).join(',')}</div>`;
            }

            // 硬性要求
            const req = t['硬性要求'] || {};
            html += `<div style="margin-top:8px;"><strong>硬性要求：</strong></div>`;
            html += `<div style="font-size:11px;color:#666;">必须包含：${(req['必须包含'] || []).join(', ')}</div>`;

            html += `<button onclick="window.templatePanel.instantiate('${templateId}', this)"
                style="margin-top:8px;padding:6px 12px;border:none;background:#1677ff;color:#fff;border-radius:4px;cursor:pointer;">
                生成实例</button>`;

            el.innerHTML = html;
        } catch (e) {
            alert('加载模板详情失败：' + e.message);
        }
    }

    async instantiate(templateId, btn) {
        btn.disabled = true;
        btn.textContent = '生成中...';
        try {
            const position = {
                x: 1000 + Math.random() * 9000,
                y: -800,
                z: 100,
            };
            const res = await APIClient.instantiateTemplate(templateId, position);
            if (res && res.success) {
                btn.textContent = '✅ 已生成';
                if (window.refreshAll) window.refreshAll();
            } else {
                btn.textContent = '❌ 失败';
            }
        } catch (e) {
            btn.textContent = '❌ 失败';
            alert('生成失败：' + e.message);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.templatePanel = new TemplatePanel();
});