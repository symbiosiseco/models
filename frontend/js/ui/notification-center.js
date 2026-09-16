/**
 * 通知中心
 * 受 GPL v3.0 保护
 *
 * 源事件，事件驱动。
 */
class NotificationCenter {
    constructor(containerId = 'notificationCenter') {
        this.containerId = containerId;
        this.notifications = [];
    }

    init() { this.render(); this.loadNotifications(); this._subscribe_events(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>通知中心</h3>
                <div id="notifyList"></div>
            </div>
        `;
    }

    loadNotifications() { this.renderNotifications(this.notifications); }

    renderNotifications(list) {
        const el = document.getElementById('notifyList');
        if (!el) return;
        if (!list || list.length === 0) {
            el.innerHTML = '<div style="color:#999;">无通知</div>';
            return;
        }
        el.innerHTML = list.map(n => this.renderNotificationItem(n)).join('');
    }

    renderNotificationItem(n) {
        return `
            <div style="padding:6px;margin-bottom:4px;background:${n.read ? '#fafafa' : '#e6f7ff'};border-radius:4px;font-size:12px;">
                <strong>${n.notify_type || ''}</strong>
                <div>${n.content || ''}</div>
                <div style="font-size:11px;color:#999;">源事件：${n.source_event || ''}</div>
                <button onclick="window.notificationCenter.markRead('${n.notify_id}')" style="font-size:11px;">标记已读</button>
            </div>
        `;
    }

    renderSourceEvent(n) { return n.source_event || ''; }

    markRead(notifyId) {
        const n = this.notifications.find(x => x.notify_id === notifyId);
        if (n) n.read = true;
        this.renderNotifications(this.notifications);
    }

    markAllRead() {
        for (const n of this.notifications) n.read = true;
        this.renderNotifications(this.notifications);
    }

    onNotificationClick(n) { console.log('通知点击', n); }
    filterByType(type) { return this.notifications.filter(n => n.notify_type === type); }

    _subscribe_events() {}
    _on_event(eventType, data) {
        if (eventType === '通知') {
            this.notifications.unshift({
                notify_id: data.notify_id,
                notify_type: data.notify_type,
                content: data.content,
                source_event: data.source_event,
                read: false,
            });
            this.renderNotifications(this.notifications);
        }
    }
}

window.NotificationCenter = NotificationCenter;
window.notificationCenter = new NotificationCenter();