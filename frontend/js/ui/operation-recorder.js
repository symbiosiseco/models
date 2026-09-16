/**
 * 操作捕捉回放器
 * 受 GPL v3.0 保护
 */
class OperationRecorder {
    constructor(demoPlayer) {
        this.demoPlayer = demoPlayer;
        this.recording = false;
        this.replaying = false;
        this.records = [];
        this.currentRecord = null;
    }

    init() { this._loadFromStorage(); }

    startRecord() {
        this.recording = true;
        this.currentRecord = {
            id: `REC-${Date.now()}`,
            actions: [],
            startTime: Date.now(),
        };
        document.addEventListener('click', this._captureAction.bind(this));
        document.addEventListener('input', this._captureAction.bind(this));
        document.addEventListener('change', this._captureAction.bind(this));
        alert('开始录制');
    }

    stopRecord() {
        this.recording = false;
        document.removeEventListener('click', this._captureAction.bind(this));
        document.removeEventListener('input', this._captureAction.bind(this));
        document.removeEventListener('change', this._captureAction.bind(this));
        if (this.currentRecord && this.currentRecord.actions.length > 0) {
            this.records.push(this.currentRecord);
            this._saveToStorage();
        }
        alert('录制完成');
        return this.currentRecord ? this.currentRecord.id : null;
    }

    recordAction(action) {
        if (!this.currentRecord) return;
        this.currentRecord.actions.push({
            timestamp: Date.now(),
            action,
        });
    }

    saveRecord(recordId) { this._saveToStorage(); return { success: true, record_id: recordId }; }
    getRecords() { return this.records; }
    loadRecord(recordId) { return this.records.find(r => r.id === recordId); }

    async replay(recordId, speed = 1.0) {
        const record = this.loadRecord(recordId);
        if (!record) return;
        this.replaying = true;
        const startTime = record.startTime;
        for (const action of record.actions) {
            if (!this.replaying) break;
            const delay = (action.timestamp - startTime) / speed;
            await this._wait(delay);
            this._executeAction(action);
        }
        this.replaying = false;
    }

    pause() { this.replaying = false; }
    resume() { this.replaying = true; }
    stop() { this.replaying = false; }

    deleteRecord(recordId) {
        this.records = this.records.filter(r => r.id !== recordId);
        this._saveToStorage();
    }

    exportRecord(recordId) {
        const record = this.loadRecord(recordId);
        if (!record) return;
        const blob = new Blob([JSON.stringify(record)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${recordId}.json`;
        a.click();
    }

    importRecord(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const record = JSON.parse(e.target.result);
                this.records.push(record);
                this._saveToStorage();
            } catch (err) {
                alert('导入失败：' + err.message);
            }
        };
        reader.readAsText(file);
    }

    _captureAction(event) {
        if (!this.recording) return;
        this.recordAction({
            type: event.type,
            target: event.target.id || event.target.tagName,
            data: {
                x: event.clientX,
                y: event.clientY,
                value: event.target.value,
            },
        });
    }

    _executeAction(action) {
        const a = action.action;
        switch (a.type) {
            case 'click': {
                const el = document.getElementById(a.target);
                if (el) el.click();
                break;
            }
            case 'input': {
                const el = document.getElementById(a.target);
                if (el) {
                    el.value = a.data.value;
                    el.dispatchEvent(new Event('input'));
                }
                break;
            }
        }
    }

    _wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
    _saveToStorage() { StorageUtils.set('operation_records', this.records); }
    _loadFromStorage() { this.records = StorageUtils.get('operation_records', []); }
}

window.OperationRecorder = OperationRecorder;
document.addEventListener('DOMContentLoaded', () => {
    if (window.demoPlayer) {
        window.operationRecorder = new OperationRecorder(window.demoPlayer);
    }
});