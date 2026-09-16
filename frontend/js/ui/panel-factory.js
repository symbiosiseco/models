/**
 * 工厂面板
 * 受 GPL v3.0 保护
 */
class FactoryPanel {
    constructor(containerId = 'factoryPanel') {
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
                <h3>工厂 · 生产制造</h3>
                <div id="factoryOrders"></div>
                <div id="factoryProduction" style="margin-top:12px;"></div>
                <div id="factoryInventory" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient.getEntities();
            if (res && res.success) {
                const entities = res.data || [];
                this.renderOrders(entities.filter(e => e.entity_type === '订单'));
                this.renderProduction([]);
                this.renderInventory({});
            }
        } catch (e) {
            console.warn('加载工厂数据失败', e);
        }
    }

    renderOrders(orders) {
        const el = document.getElementById('factoryOrders');
        if (!el) return;
        if (!orders || orders.length === 0) {
            el.innerHTML = '<div style="color:#999;">无订单</div>';
            return;
        }
        el.innerHTML = '<h4>订单列表</h4>' + orders.map(o => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${o.id}
                <button onclick="window.factoryPanel.receiveOrder('${o.id}')" style="font-size:11px;">接单</button>
                <button onclick="window.factoryPanel.planProduction('${o.id}')" style="font-size:11px;">排产</button>
            </div>
        `).join('');
    }

    renderProduction(production) {
        const el = document.getElementById('factoryProduction');
        if (!el) return;
        if (!production || production.length === 0) {
            el.innerHTML = '<h4>生产任务</h4><div style="color:#999;">暂无</div>';
            return;
        }
        el.innerHTML = '<h4>生产任务</h4>' + production.map(p => `
            <div style="font-size:12px;">${p.id}</div>
        `).join('');
    }

    renderInventory(inventory) {
        const el = document.getElementById('factoryInventory');
        if (!el) return;
        el.innerHTML = '<h4>库存</h4><div style="color:#999;">暂无</div>';
    }

    receiveOrder(orderData) {
        return APIClient._fetch('/api/templates/', {
            method: 'POST',
            body: JSON.stringify({ order: orderData }),
        }).then(() => this.loadData());
    }

    planProduction(orderId) {
        return APIClient._fetch('/api/task_generator/decompose', {
            method: 'POST',
            body: JSON.stringify({ order_id: orderId }),
        }).then(() => this.loadData());
    }

    produce(materialId) {
        return APIClient._fetch('/api/templates/', {
            method: 'POST',
            body: JSON.stringify({ produce: materialId }),
        });
    }

    qualityCheck(materialId) {
        return { success: true, material_id: materialId, passed: true };
    }

    ship(materialId, logisticsId) {
        return APIClient._fetch('/api/templates/', {
            method: 'POST',
            body: JSON.stringify({ ship: materialId, logistics_id: logisticsId }),
        });
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '订单生成' || eventType === '换货触发') {
            this.loadData();
        }
    }
}

window.FactoryPanel = FactoryPanel;
window.factoryPanel = new FactoryPanel();