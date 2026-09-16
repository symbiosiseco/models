/**
 * L4套娃履历展示
 * 受 GPL v3.0 保护
 */
class L4Viewer {
    constructor(containerId = 'l4Panel') {
        this.containerId = containerId;
    }

    async show(entityId) {
        try {
            const res = await APIClient.getL4(entityId);
            if (res && res.success) {
                this.renderEvents(res.data || []);
            } else {
                this.renderEvents([]);
            }
        } catch (e) {
            this.renderEvents([]);
        }
    }

    renderEvents(events) {
        const el = document.getElementById(this.containerId);
        if (!el) return;
        if (!events || events.length === 0) {
            el.innerHTML = '<div class="empty-hint">暂无履历</div>';
            return;
        }
        el.innerHTML = `
            <h4>📜 L4 · 套娃式履历</h4>
            <div>${this.renderTimeline(events)}</div>
            ${this.renderNested(events)}
        `;
    }

    renderTimeline(events) {
        return events.map(e => `
            <div class="l4-item">
                <span style="color:#999;">${this.formatTime(e.time)}</span>
                <strong>${e.event || ''}</strong>
                <span style="color:#666;">${e.detail || ''}</span>
            </div>
        `).join('');
    }

    renderNested(events) {
        const nested = events.filter(e => e.nested);
        if (nested.length === 0) return '';
        return '<h4>内部零件履历</h4>' + nested.map(n => `
            <div style="margin-bottom:4px;">
                <div onclick="window.L4Viewer.expandNested('${n.part}')" style="cursor:pointer;">▶ ${n.part}</div>
            </div>
        `).join('');
    }

    expandNested(partName) { console.log('展开零件', partName); }
    collapseNested(partName) { console.log('折叠零件', partName); }

    formatTime(time) {
        if (!time) return '';
        return String(time).slice(0, 16);
    }

    exportL4(entityId) {
        return APIClient._fetch('/api/export/l4', {
            method: 'POST',
            body: JSON.stringify({ entity_id: entityId }),
        });
    }
}

window.L4Viewer = new L4Viewer();