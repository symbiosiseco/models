/**
 * CBM状态面板
 * 受 GPL v3.0 保护
 */
class CBMStatusPanel {
    constructor(containerId = 'cbmStatusPanel') {
        this.containerId = containerId;
    }

    init() {
        this.render({});
    }

    async load(entityId) {
        try {
            const res = await APIClient.getCBMStatus(entityId);
            if (res && res.success) {
                this.render(res.data || {});
            } else {
                this.render({});
            }
        } catch (e) {
            this.render({});
        }
    }

    render(cbm) {
        const el = document.getElementById(this.containerId);
        if (!el) return;
        const rules = cbm.rules || {};
        const status = cbm.status || 'stable';

        el.innerHTML = `
            <div style="font-size:12px;">
                <div style="margin-bottom:8px;">
                    <span class="cbm-tag ${status}">${this._statusName(status)}</span>
                </div>
                ${this.renderPhysicalRules(rules['物理规则'])}
                ${this.renderForceRules(rules['受力规则'])}
                ${this.renderAssemblyRules(rules['装配规则'])}
                ${this.renderSpecRules(rules['规范约束'])}
                ${this.renderChecks(cbm.checks || [])}
            </div>
        `;
    }

    renderPhysicalRules(rules) {
        if (!rules) return '';
        return `
            <div style="margin-bottom:6px;">
                <strong>物理规则</strong>
                <div style="color:#666;">包围盒：${JSON.stringify(rules['包围盒'] || {})}</div>
                <div style="color:#666;">最小间距：${rules['最小间距'] || '—'}</div>
                <div style="color:#666;">允许接触：${(rules['允许接触'] || []).join(', ')}</div>
                <div style="color:#666;">禁止穿透：${rules['禁止穿透'] ? '是' : '否'}</div>
            </div>
        `;
    }

    renderForceRules(rules) {
        if (!rules) return '';
        return `
            <div style="margin-bottom:6px;">
                <strong>受力规则</strong>
                <div style="color:#666;">自重：${rules['自重'] || '—'}</div>
                <div style="color:#666;">承重上限：${rules['承重上限'] || '—'}</div>
                <div style="color:#666;">传力路径：${(rules['传力路径'] || []).join(' → ')}</div>
            </div>
        `;
    }

    renderAssemblyRules(rules) {
        if (!rules) return '';
        return `
            <div style="margin-bottom:6px;">
                <strong>装配规则</strong>
                <div style="color:#666;">拧紧力矩：${rules['拧紧力矩'] || '—'}</div>
                <div style="color:#666;">装配顺序：${(rules['装配顺序'] || []).join(' → ')}</div>
            </div>
        `;
    }

    renderSpecRules(rules) {
        if (!rules) return '';
        return `
            <div style="margin-bottom:6px;">
                <strong>规范约束</strong>
                <div style="color:#666;">安装规范：${rules['安装规范'] || '—'}</div>
                <div style="color:#666;">维护空间：${rules['维护空间'] || '—'}</div>
                <div style="color:#666;">检查周期：${rules['检查周期'] || '—'}</div>
            </div>
        `;
    }

    renderStatus(status) {
        return `<span class="cbm-tag ${status}">${this._statusName(status)}</span>`;
    }

    renderChecks(checks) {
        if (!checks || checks.length === 0) return '';
        return `
            <div style="margin-top:6px;">
                <strong>检查结果</strong>
                ${checks.map(c => `<div style="color:#666;">· ${c.check || ''} ${c.passed ? '✅' : '❌'}</div>`).join('')}
            </div>
        `;
    }

    _statusName(status) {
        const map = {
            stable: '稳定',
            warning: '预警',
            overload: '超载',
            collision: '碰撞',
            unbuilt: '未施工',
        };
        return map[status] || '稳定';
    }
}

window.CBMStatusPanel = new CBMStatusPanel();