/**
 * 设计院面板
 * 受 GPL v3.0 保护
 */
class DesignerPanel {
    constructor(containerId = 'designerPanel') {
        this.containerId = containerId;
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
                <h3>设计院 · 图纸管理</h3>
                <div id="designerDrawings"></div>
                <div id="designerChanges" style="margin-top:12px;"></div>
                <div id="designerFeedback" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient.getEntities();
            if (res && res.success) {
                const entities = res.data || [];
                this.renderDrawings(entities.filter(e => e.entity_type === '图纸'));
                this.renderChanges(entities.filter(e => e.entity_type === '变更'));
                this.renderSiteFeedback([]);
            }
        } catch (e) {
            console.warn('加载设计数据失败', e);
        }
    }

    renderDrawings(drawings) {
        const el = document.getElementById('designerDrawings');
        if (!el) return;
        if (!drawings || drawings.length === 0) {
            el.innerHTML = '<div style="color:#999;">无图纸</div>';
            return;
        }
        el.innerHTML = '<h4>我的图纸</h4>' + drawings.map(d => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${d.id} · ${d.entity_type}
                <button onclick="window.designerPanel.reviewDrawing('${d.id}')" style="font-size:11px;">会审</button>
            </div>
        `).join('');
    }

    renderChanges(changes) {
        const el = document.getElementById('designerChanges');
        if (!el) return;
        if (!changes || changes.length === 0) {
            el.innerHTML = '<div style="color:#999;">无变更</div>';
            return;
        }
        el.innerHTML = '<h4>设计变更</h4>' + changes.map(c => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${c.id}
                <button onclick="window.designerPanel.modifyDrawing('${c.id}', {})" style="font-size:11px;">修改设计</button>
            </div>
        `).join('');
    }

    renderSiteFeedback(feedback) {
        const el = document.getElementById('designerFeedback');
        if (!el) return;
        if (!feedback || feedback.length === 0) {
            el.innerHTML = '<h4>现场反馈</h4><div style="color:#999;">暂无</div>';
            return;
        }
        el.innerHTML = '<h4>现场反馈</h4>' + feedback.map(f => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${f.content || ''}
            </div>
        `).join('');
    }

    uploadDrawing(drawingData) {
        return APIClient._fetch('/api/templates/', {
            method: 'POST',
            body: JSON.stringify(drawingData),
        });
    }

    modifyDrawing(drawingId, changes) {
        return APIClient._fetch('/api/templates/', {
            method: 'POST',
            body: JSON.stringify({ drawing_id: drawingId, changes }),
        });
    }

    reviewDrawing(drawingId, comments) {
        return APIClient._fetch('/api/templates/', {
            method: 'POST',
            body: JSON.stringify({ drawing_id: drawingId, comments }),
        }).then(() => this.loadData());
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '现场反馈') {
            this.loadData();
        }
    }
}

window.DesignerPanel = DesignerPanel;
window.designerPanel = new DesignerPanel();