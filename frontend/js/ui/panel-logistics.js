/**
 * 物流面板
 * 受 GPL v3.0 保护
 */
class LogisticsPanel {
    constructor(containerId = 'logisticsPanel') {
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
                <h3>物流 · 运输配送</h3>
                <div id="logisticsTasks"></div>
                <div id="logisticsVehicles" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            this.renderTasks([]);
            this.renderVehicles([
                { vehicle_id: 'VEH-001', plate: '粤C·12345', type: '货车', capacity: 3, status: '空闲' },
                { vehicle_id: 'VEH-002', plate: '粤C·67890', type: '叉车', capacity: 1, status: '运输中' },
            ]);
        } catch (e) {
            console.warn('加载物流数据失败', e);
        }
    }

    renderTasks(tasks) {
        const el = document.getElementById('logisticsTasks');
        if (!el) return;
        if (!tasks || tasks.length === 0) {
            el.innerHTML = '<div style="color:#999;">无配送任务</div>';
            return;
        }
        el.innerHTML = '<h4>配送任务</h4>' + tasks.map(t => `
            <div style="font-size:12px;">${t.id}</div>
        `).join('');
    }

    renderVehicles(vehicles) {
        const el = document.getElementById('logisticsVehicles');
        if (!el) return;
        el.innerHTML = '<h4>车辆列表</h4>' + vehicles.map(v => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${v.plate} · ${v.type} · ${v.capacity}吨 · ${v.status}
                <button onclick="window.logisticsPanel.trackVehicle('${v.vehicle_id}')" style="font-size:11px;">跟踪</button>
            </div>
        `).join('');
    }

    matchVehicle(materials, destination) {
        return { success: true, vehicle_id: 'VEH-001', plate: '粤C·12345' };
    }

    dispatchTask(driverId, task) {
        return APIClient._fetch('/api/tasks/', {
            method: 'POST',
            body: JSON.stringify({ driver_id: driverId, task }),
        });
    }

    trackVehicle(vehicleId) {
        return { vehicle_id: vehicleId, position: { x: 15000, y: 8000 }, eta: '15:30' };
    }

    confirmDelivery(taskId) {
        return APIClient._fetch(`/api/tasks/${taskId}/complete`, { method: 'POST' });
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '发货' || eventType === '换货触发') {
            this.loadData();
        }
    }
}

window.LogisticsPanel = LogisticsPanel;
window.logisticsPanel = new LogisticsPanel();