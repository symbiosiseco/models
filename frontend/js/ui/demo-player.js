/**
 * 动画播放器
 * 受 GPL v3.0 保护
 *
 * 含事件订阅 + 操作捕捉回放。
 */
class DemoPlayer {
    constructor(renderer) {
        this.renderer = renderer;
        this.tasks = [];
        this.currentIndex = -1;
        this.speed = 1.0;
        this.records = [];
        this.recording = false;
        this.currentRecord = null;
        this.createControlBar();
        this._subscribe_events();
    }

    init() { this.createControlBar(); }

    _subscribe_events() {
        if (window.state && window.state.websocket) {
            // 由 test-main 统一处理
        }
    }

    _on_event(data) {
        if (data.event_type === '任务完成') {
            const triggered = data.triggered_tasks || [];
            if (triggered.length > 0) this.autoPlayNext(triggered);
        } else if (data.event_type === '装配失败') {
            this.animateAssemblyFailure(data.entity_id);
        }
    }

    createControlBar() {
        let el = document.getElementById('demoControlBar');
        if (!el) {
            el = document.createElement('div');
            el.id = 'demoControlBar';
            el.style.cssText = 'position:fixed;bottom:48px;left:50%;transform:translateX(-50%);background:#001529;color:#fff;padding:6px 12px;border-radius:6px;z-index:999;display:flex;gap:8px;align-items:center;font-size:12px;';
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <button onclick="window.demoPlayer.start()">▶️</button>
            <button onclick="window.demoPlayer.pause()">⏸️</button>
            <button onclick="window.demoPlayer.next()">⏭️</button>
            <button onclick="window.demoPlayer.prev()">⏮️</button>
            <button onclick="window.demoPlayer.reset()">🔄</button>
            <select onchange="window.demoPlayer.setSpeed(parseFloat(this.value))">
                <option value="0.5">0.5x</option>
                <option value="1" selected>1x</option>
                <option value="1.5">1.5x</option>
                <option value="2">2x</option>
            </select>
            <button onclick="window.demoPlayer.startRecord()">⏺️</button>
            <button onclick="window.demoPlayer.stopRecord()">⏹️</button>
            <span id="demoProgress">0/0</span>
        `;
    }

    loadTasks(tasks) {
        this.tasks = tasks || [];
        this.currentIndex = -1;
        this.renderFrame();
    }

    start() {
        if (this.tasks.length === 0) return;
        this.currentIndex = 0;
        this.renderFrame();
    }

    pause() { /* 暂停 */ }
    next() {
        if (this.currentIndex < this.tasks.length - 1) this.currentIndex++;
        this.renderFrame();
    }
    prev() {
        if (this.currentIndex > 0) this.currentIndex--;
        this.renderFrame();
    }
    reset() {
        this.currentIndex = -1;
        this.renderFrame();
    }
    setSpeed(speed) { this.speed = speed; }

    renderFrame() {
        const el = document.getElementById('demoProgress');
        if (el) el.textContent = `${this.currentIndex + 1}/${this.tasks.length}`;
    }

    animateWorker(actor, startPos, endPos, duration) {
        if (window.AnimationEngine && this.renderer) {
            const engine = new AnimationEngine(this.renderer.scene);
            return engine.moveObject(actor, startPos, endPos, duration);
        }
        return Promise.resolve();
    }

    animatePayload(payload, startPos, endPos) {
        return this.animateWorker(payload, startPos, endPos, 1.0);
    }

    animateInstall(entity, targetPos) {
        if (window.AnimationEngine && this.renderer) {
            const engine = new AnimationEngine(this.renderer.scene);
            return engine.animateAssemblyFlow(entity, targetPos, []);
        }
        return Promise.resolve();
    }

    animateAssemblyFailure(entity) {
        if (window.AnimationEngine && this.renderer) {
            const engine = new AnimationEngine(this.renderer.scene);
            return engine.animateAssemblyFailure(entity);
        }
        return Promise.resolve();
    }

    updateTaskStatus(taskId, status) { console.log('任务状态', taskId, status); }
    updateWorkerPanel(workerId) { console.log('工人面板', workerId); }

    startRecord() {
        this.recording = true;
        this.currentRecord = { id: `REC-${Date.now()}`, actions: [], startTime: Date.now() };
        alert('开始录制');
    }

    stopRecord() {
        this.recording = false;
        if (this.currentRecord) {
            this.records.push(this.currentRecord);
            alert('录制完成');
        }
        return this.currentRecord ? this.currentRecord.id : null;
    }

    replayRecord(recordId) {
        const record = this.records.find(r => r.id === recordId);
        if (!record) return;
        alert(`回放 ${record.actions.length} 个操作`);
    }

    renderRecordList() { return this.records; }
}

window.DemoPlayer = DemoPlayer;
document.addEventListener('DOMContentLoaded', () => {
    if (window.state && window.state.renderer) {
        window.demoPlayer = new DemoPlayer(window.state.renderer);
    }
});