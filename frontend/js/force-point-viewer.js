/**
 * 受力点查看器
 * 受 GPL v3.0 保护
 */
class ForcePointViewer {
    constructor(containerId = 'forcePointsPanel') {
        this.containerId = containerId;
    }

    init() {
        this.render([]);
    }

    async load(entityId) {
        try {
            const res = await APIClient.getForcePoints(entityId);
            if (res && res.success) {
                this.render(res.data || []);
            } else {
                this.render([]);
            }
        } catch (e) {
            this.render([]);
        }
    }

    render(fpList) {
        const el = document.getElementById(this.containerId);
        if (!el) return;
        if (!fpList || fpList.length === 0) {
            el.innerHTML = '<div class="empty-hint">无受力点</div>';
            return;
        }
        el.innerHTML = fpList.map(fp => this.renderForcePoint(fp)).join('');
    }

    renderForcePoint(fp) {
        const capacity = this._parse(fp['承重上限'] || '500kg');
        const current = this._parse(fp['当前受力'] || '0kg');
        const pct = capacity > 0 ? Math.min(100, current / capacity * 100) : 0;

        let gaugeClass = '';
        if (pct >= 90) gaugeClass = 'danger';
        else if (pct >= 60) gaugeClass = 'warning';

        return `
            <div class="fp-item">
                <div><strong>${fp.id || '受力点'}</strong></div>
                <div style="font-size:11px;color:#666;">类型：${fp['类型'] || '—'}</div>
                <div style="font-size:11px;color:#666;">方向：${this.renderForceDirection(fp['方向'])}</div>
                <div style="font-size:11px;color:#666;">承重上限：${fp['承重上限'] || '—'}</div>
                <div style="font-size:11px;color:#666;">当前受力：${fp['当前受力'] || '待检测'}</div>
                <div class="fp-gauge">
                    <div class="fp-gauge-bar ${gaugeClass}" style="width:${pct}%"></div>
                </div>
                <div style="font-size:10px;color:#999;">${pct.toFixed(1)}%</div>
            </div>
        `;
    }

    renderForceGauge(force, capacity) {
        const pct = capacity > 0 ? Math.min(100, force / capacity * 100) : 0;
        return `<div class="fp-gauge"><div class="fp-gauge-bar" style="width:${pct}%"></div></div>`;
    }

    renderForceDirection(direction) {
        const map = {
            'Z-': '↓ Z-',
            'Z+': '↑ Z+',
            'X+': '→ X+',
            'X-': '← X-',
            'Y+': '↗ Y+',
            'Y-': '↙ Y-',
        };
        return map[direction] || direction || '—';
    }

    showHistory(fpId) {
        // 简化：从 L4 中提取
        console.log('受力历史：', fpId);
    }

    _formatCapacity(cap) {
        return cap || '—';
    }

    _parse(val) {
        if (typeof val === 'number') return val;
        if (typeof val === 'string') {
            const n = parseFloat(val.replace('kg', '').replace('N·m', '').trim());
            return isNaN(n) ? 0 : n;
        }
        return 0;
    }
}

window.ForcePointViewer = new ForcePointViewer();