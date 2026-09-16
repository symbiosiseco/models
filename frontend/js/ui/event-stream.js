/**
 * 事件流面板
 * 受 GPL v3.0 保护
 */
class EventStream {
    constructor(containerId = 'eventStreamBody') {
        this.containerId = containerId;
        this.events = [];
        this.filter = 'all';
        this.paused = false;
        this.maxEvents = 100;
        this.render();
    }

    init() {
        this.render();
    }

    addEvent(event) {
        if (this.paused) return;
        this.events.unshift(event);
        if (this.events.length > this.maxEvents) {
            this.events = this.events.slice(0, this.maxEvents);
        }
        this.render();
    }

    render() {
        const el = document.getElementById(this.containerId);
        if (!el) return;
        let list = this.events;
        if (this.filter !== 'all') {
            list = list.filter(e => this._matchFilter(e, this.filter));
        }
        if (list.length === 0) {
            el.innerHTML = '<div style="color:#888;padding:8px;">暂无事件</div>';
            return;
        }
        el.innerHTML = list.map(e => this.renderEvent(e)).join('');
    }

    renderEvent(e) {
        const icon = this._getEventIcon(e.event_type);
        const time = this._formatTime(e.timestamp || e.time);
        return `
            <div class="event-item">
                <span class="event-time">${time}</span>
                <span>${icon} ${e.event_type || ''}</span>
                <div style="color:#aaa;font-size:10px;">${e.data ? JSON.stringify(e.data).slice(0, 80) : ''}</div>
            </div>
        `;
    }

    filterByType(type) {
        this.filter = type;
        this.render();
    }

    clear() {
        this.events = [];
        this.render();
    }

    pause() { this.paused = true; }
    resume() { this.paused = false; }

    _matchFilter(event, filter) {
        const t = event.event_type || '';
        if (filter === 'L3变化') return t === 'L3变化';
        if (filter === '任务') return t.includes('任务') || t.includes('产物');
        if (filter === '通知') return t === '通知';
        if (filter === '错误') return t.includes('失败') || t.includes('错误');
        return true;
    }

    _formatTime(timestamp) {
        if (!timestamp) return '';
        if (typeof timestamp === 'string' && timestamp.includes(':')) {
            return timestamp.slice(-8);
        }
        const d = new Date(timestamp);
        if (isNaN(d.getTime())) return '';
        const pad = n => n < 10 ? '0' + n : n;
        return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    }

    _getEventIcon(type) {
        const map = {
            'L3变化': '🔄',
            '任务派发': '📋',
            '任务完成': '✅',
            '装配失败': '⚠️',
            '接触面错误': '❌',
            '通知': '📢',
            '换货触发': '🔁',
            '签字': '✍️',
        };
        return map[type] || '⚡';
    }
}

window.EventStream = new EventStream();