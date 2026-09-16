/**
 * 任务看板
 * 受 GPL v3.0 保护
 *
 * TaskCBM驱动动画。
 */
class TaskBoard {
    constructor(containerId = 'taskBoard') {
        this.containerId = containerId;
        this.tasks = [];
    }

    init() { this.render(); this.loadTasks(); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>任务看板</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
                    <div><h4>待执行</h4><div id="taskPending"></div></div>
                    <div><h4>执行中</h4><div id="taskRunning"></div></div>
                    <div><h4>已完成</h4><div id="taskDone"></div></div>
                </div>
            </div>
        `;
    }

    async loadTasks() {
        try {
            const res = await APIClient._fetch('/api/task_generator/tasks/');
            if (res && res.success) {
                this.tasks = res.data || [];
                this.render();
            }
        } catch (e) {
            console.warn('加载任务失败', e);
        }
    }

    render() {
        const pending = this.tasks.filter(t => t.status === '待执行');
        const running = this.tasks.filter(t => t.status === '执行中');
        const done = this.tasks.filter(t => t.status === '已完成');
        this._renderCol('taskPending', pending);
        this._renderCol('taskRunning', running);
        this._renderCol('taskDone', done);
    }

    _renderCol(id, list) {
        const el = document.getElementById(id);
        if (!el) return;
        if (list.length === 0) {
            el.innerHTML = '<div style="color:#999;font-size:12px;">无</div>';
            return;
        }
        el.innerHTML = list.map(t => this.renderTaskCard(t)).join('');
    }

    renderTaskCard(task) {
        return `
            <div onclick="window.taskBoard.onTaskClick('${task.id}')"
                style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;cursor:pointer;">
                <strong>${task.id}</strong>
                <div>${task.name || ''}</div>
                <div style="color:#666;">${task.actor || ''}</div>
                <button onclick="event.stopPropagation();window.taskBoard.completeTask('${task.id}')" style="font-size:11px;">完成</button>
            </div>
        `;
    }

    renderTaskStatus(task) { return task.status || ''; }
    renderTriggerChain(task) { return ''; }
    onTaskClick(taskId) { console.log('任务点击', taskId); }

    startTask(taskId) {
        return APIClient._fetch(`/api/tasks/${taskId}/start`, { method: 'POST' })
            .then(() => this.loadTasks());
    }

    completeTask(taskId) {
        return APIClient._fetch(`/api/tasks/${taskId}/complete`, { method: 'POST' })
            .then(() => this.loadTasks());
    }

    animateTaskMove(taskId, fromCol, toCol) {
        const el = document.getElementById(taskId);
        if (el) {
            el.style.transition = 'all 0.5s ease';
        }
    }

    animateTriggerChain(taskId, triggeredTasks) {
        console.log('触发链动画', taskId, triggeredTasks);
    }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '任务完成' || eventType === '任务派发') {
            this.loadTasks();
        }
    }
}

window.TaskBoard = TaskBoard;
window.taskBoard = new TaskBoard();