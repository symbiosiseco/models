/**
 * 施工员面板
 * 受 GPL v3.0 保护
 */
class WorkerPanel {
    constructor(containerId = 'workerPanel') {
        this.containerId = containerId;
        this.workerId = 'WORKER-001';
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
                <h3>施工员面板</h3>
                <div id="workerStatus"></div>
                <div id="workerTasks" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient._fetch(`/api/users/${this.workerId}/state`);
            if (res && res.success) {
                this.renderWorkerStatus(res.data);
            }
        } catch (e) {
            console.warn('加载工人状态失败', e);
        }
        this.renderTasks([]);
    }

    renderWorkerStatus(worker) {
        const el = document.getElementById('workerStatus');
        if (!el) return;
        const state = worker || {};
        el.innerHTML = `
            <div>状态：${state.status || '空闲'}</div>
            <div>体力：${this.renderStaminaBar(state['体力'] || '100%')}</div>
            <div>心态：${this.renderMentality(state['心态'] || '正常')}</div>
            <div>活动范围：${this.renderActivityArea(state['活动范围'])}</div>
        `;
    }

    renderStaminaBar(stamina) {
        const pct = parseInt(String(stamina).replace('%', '')) || 100;
        const cls = pct >= 80 ? '' : pct >= 60 ? 'warning' : 'danger';
        return `<div class="fp-gauge"><div class="fp-gauge-bar ${cls}" style="width:${pct}%"></div></div>${stamina}`;
    }

    renderMentality(mentality) {
        return mentality;
    }

    renderActivityArea(area) {
        if (!area) return '全区域';
        return area['区域'] || '全区域';
    }

    renderTasks(tasks) {
        const el = document.getElementById('workerTasks');
        if (!el) return;
        if (!tasks || tasks.length === 0) {
            el.innerHTML = '<div style="color:#999;">今日无任务</div>';
            return;
        }
        el.innerHTML = tasks.map(t => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;">
                <strong>${t.id}</strong> · ${t.name || ''}
                <div style="font-size:11px;color:#666;">状态：${t.status || '待执行'}</div>
                <button onclick="window.workerPanel.startTask('${t.id}')" style="font-size:11px;margin-top:4px;">开始</button>
                <button onclick="window.workerPanel.completeTask('${t.id}')" style="font-size:11px;margin-top:4px;">完成</button>
            </div>
        `).join('');
    }

    async startTask(taskId) {
        try {
            const res = await APIClient._fetch(`/api/tasks/${taskId}/start`, {
                method: 'POST',
                body: JSON.stringify({ worker_id: this.workerId }),
            });
            if (res && res.success) {
                this.loadData();
            }
        } catch (e) {
            alert('开始任务失败：' + e.message);
        }
    }

    async completeTask(taskId) {
        try {
            const res = await APIClient._fetch(`/api/tasks/${taskId}/complete`, {
                method: 'POST',
                body: JSON.stringify({ photos: [] }),
            });
            if (res && res.success) {
                this.loadData();
                if (res.data && res.data.triggered_tasks) {
                    alert('已触发下游任务：' + res.data.triggered_tasks.join(', '));
                }
            }
        } catch (e) {
            alert('完成任务失败：' + e.message);
        }
    }

    reportProblem(taskId, problem) {
        return APIClient._fetch('/api/construction/problem', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, problem }),
        });
    }

    _subscribe_events() {
        if (window.state && window.state.websocket) {
            // WebSocket 已在 test-main 中统一处理
        }
    }

    _on_event(eventType, data) {
        if (eventType === '任务派发' && data.worker_id === this.workerId) {
            this.loadData();
        }
    }
}

window.WorkerPanel = WorkerPanel;
window.workerPanel = new WorkerPanel();