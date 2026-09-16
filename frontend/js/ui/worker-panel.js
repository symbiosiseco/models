/**
 * 人员任务面板
 * 受 GPL v3.0 保护
 *
 * L3多维度动画。
 */
class WorkerPanel {
    constructor(containerId = 'workerPanelFull') {
        this.containerId = containerId;
        this.workerId = 'WORKER-001';
        this.currentStamina = '100%';
        this.currentMentality = '正常';
    }

    init() { this.render(); this.showWorker(this.workerId); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>人员任务面板</h3>
                <div id="wpStatus"></div>
                <div id="wpTasks" style="margin-top:12px;"></div>
                <div id="wpHhistory" style="margin-top:12px;"></div>
            </div>
        `;
    }

    showWorker(workerId) {
        this.workerId = workerId;
        APIClient._fetch(`/api/users/${workerId}/state`).then(res => {
            if (res && res.success) this.renderWorkerStatus(res.data);
        }).catch(() => {});
        this.renderTasks([]);
        this.renderHistory([]);
    }

    renderTasks(tasks) {
        const el = document.getElementById('wpTasks');
        if (!el) return;
        if (!tasks || tasks.length === 0) {
            el.innerHTML = '<div style="color:#999;">今日无任务</div>';
            return;
        }
        el.innerHTML = tasks.map(t => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${t.id} · ${t.name || ''}
            </div>
        `).join('');
    }

    renderHistory(events) {
        const el = document.getElementById('wpHhistory');
        if (!el) return;
        if (!events || events.length === 0) {
            el.innerHTML = '<div style="color:#999;">暂无履历</div>';
            return;
        }
        el.innerHTML = events.slice(0, 10).map(e => `
            <div style="font-size:11px;color:#666;">${e.time || ''} · ${e.event || ''}</div>
        `).join('');
    }

    renderWorkerStatus(worker) {
        const el = document.getElementById('wpStatus');
        if (!el) return;
        const state = worker || {};
        el.innerHTML = `
            <div>状态：${state.status || '空闲'}</div>
            <div>体力：${this.renderStaminaBar(state['体力'] || '100%')}</div>
            <div>心态：${this.renderMentality(state['心态'] || '正常')}</div>
            <div>情绪：${this.renderEmotion(state['情绪'] || '平静')}</div>
            <div>活动范围：${this.renderActivityArea(state['活动范围'])}</div>
        `;
    }

    renderStaminaBar(stamina) {
        const pct = parseInt(String(stamina).replace('%', '')) || 100;
        const cls = pct >= 80 ? '' : pct >= 60 ? 'warning' : 'danger';
        return `<div class="fp-gauge"><div class="fp-gauge-bar ${cls}" style="width:${pct}%"></div></div>${stamina}`;
    }

    renderMentality(m) { return m; }
    renderEmotion(e) { return e; }
    renderActivityArea(a) { return (a && a['区域']) || '全区域'; }

    animateStaminaChange(oldS, newS) {
        const el = document.getElementById('wpStatus');
        if (el) {
            const bar = el.querySelector('.fp-gauge-bar');
            if (bar) bar.style.transition = 'width 0.5s ease';
        }
    }

    animateMentalityChange(oldM, newM) {
        console.log(`心态变化：${oldM} → ${newM}`);
    }

    onTaskAction(taskId, action) { console.log('任务操作', taskId, action); }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '任务派发' && data.worker_id === this.workerId) {
            this.showWorker(this.workerId);
        }
        if (eventType === 'L3变化' && data.entity_id === this.workerId) {
            if (data.stamina) {
                this.animateStaminaChange(this.currentStamina, data.stamina);
                this.currentStamina = data.stamina;
            }
            if (data.mentality) {
                this.animateMentalityChange(this.currentMentality, data.mentality);
                this.currentMentality = data.mentality;
            }
        }
    }
}

window.WorkerPanelFull = WorkerPanel;
window.workerPanelFull = new WorkerPanel();