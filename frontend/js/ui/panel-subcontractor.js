/**
 * 分包面板
 * 受 GPL v3.0 保护
 */
class SubcontractorPanel {
    constructor(containerId = 'subcontractorPanel') {
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
                <h3>分包 · 专业作业</h3>
                <div id="subcontractorTasks"></div>
                <div id="subcontractorWorkers" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient._fetch('/api/task_generator/tasks/');
            if (res && res.success) {
                this.renderTasks(res.data || []);
            }
            this.renderWorkers([
                { id: 'WORKER-001', name: '王五', type: '管道工', status: '空闲' },
                { id: 'WORKER-002', name: '李四', type: '焊工', status: '忙碌' },
            ]);
        } catch (e) {
            console.warn('加载分包数据失败', e);
        }
    }

    renderTasks(tasks) {
        const el = document.getElementById('subcontractorTasks');
        if (!el) return;
        if (!tasks || tasks.length === 0) {
            el.innerHTML = '<div style="color:#999;">无任务</div>';
            return;
        }
        el.innerHTML = '<h4>我的任务</h4>' + tasks.map(t => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${t.id} · ${t.name || ''}
                <button onclick="window.subcontractorPanel.acceptTask('${t.id}')" style="font-size:11px;">接受</button>
                <button onclick="window.subcontractorPanel.assignWorker('${t.id}', 'WORKER-001')" style="font-size:11px;">派工</button>
            </div>
        `).join('');
    }

    renderWorkers(workers) {
        const el = document.getElementById('subcontractorWorkers');
        if (!el) return;
        el.innerHTML = '<h4>我的工人</h4>' + workers.map(w => `
            <div style="font-size:12px;">${w.name}（${w.type}）· ${w.status}</div>
        `).join('');
    }

    acceptTask(taskId) {
        return APIClient._fetch('/api/tasks/', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, status: '已接受' }),
        }).then(() => this.loadData());
    }

    assignWorker(taskId, workerId) {
        return APIClient._fetch('/api/tasks/', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, worker_id: workerId }),
        }).then(() => this.loadData());
    }

    requestMaterial(materialIds) {
        return APIClient._fetch('/api/tasks/', {
            method: 'POST',
            body: JSON.stringify({ materials: materialIds }),
        });
    }

    reportProgress(taskId, progress) {
        return APIClient._fetch('/api/tasks/', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, progress }),
        });
    }

    handleProblem(taskId, problem) {
        return APIClient._fetch('/api/tasks/', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, problem }),
        });
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '任务派发' || eventType === '产物完成') {
            this.loadData();
        }
    }
}

window.SubcontractorPanel = SubcontractorPanel;
window.subcontractorPanel = new SubcontractorPanel();