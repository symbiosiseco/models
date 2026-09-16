/**
 * 供应商面板
 * 受 GPL v3.0 保护
 */
class SupplierPanel {
    constructor(containerId = 'supplierPanel') {
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
                <h3>供应商 · 材料供应</h3>
                <div id="supplierOrders"></div>
                <div id="supplierInventory" style="margin-top:12px;"></div>
                <div id="supplierReplacements" style="margin-top:12px;"></div>
            </div>
        `;
    }

    async loadData() {
        try {
            const res = await APIClient.getEntities();
            if (res && res.success) {
                const entities = res.data || [];
                this.renderOrders(entities.filter(e => e.entity_type === '订单'));
                this.renderInventory({ 'DN100管道': 100, 'DN100阀门': 10 });
                this.renderReplacements([]);
            }
        } catch (e) {
            console.warn('加载供应商数据失败', e);
        }
    }

    renderOrders(orders) {
        const el = document.getElementById('supplierOrders');
        if (!el) return;
        if (!orders || orders.length === 0) {
            el.innerHTML = '<div style="color:#999;">无订单</div>';
            return;
        }
        el.innerHTML = '<h4>订单列表</h4>' + orders.map(o => `
            <div style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;font-size:12px;">
                ${o.id}
                <button onclick="window.supplierPanel.receiveOrder('${o.id}')" style="font-size:11px;">接单</button>
                <button onclick="window.supplierPanel.shipOrder('${o.id}', 'LOG-001')" style="font-size:11px;">发货</button>
            </div>
        `).join('');
    }

    renderInventory(inventory) {
        const el = document.getElementById('supplierInventory');
        if (!el) return;
        let html = '<h4>库存</h4>';
        for (const k in inventory) {
            html += `<div style="font-size:12px;">${k}：${inventory[k]}</div>`;
        }
        el.innerHTML = html;
    }

    async receiveOrder(orderId) {
        try {
            await APIClient._fetch('/api/templates/', { method: 'POST', body: JSON.stringify({ order_id: orderId }) });
            this.loadData();
        } catch (e) {
            alert('接单失败：' + e.message);
        }
    }

    checkStock(materialId) {
        return { material_id: materialId, stock: 100, available: true };
    }

    async shipOrder(orderId, logisticsId) {
        try {
            await APIClient._fetch('/api/templates/', { method: 'POST', body: JSON.stringify({ order_id: orderId, logistics_id: logisticsId }) });
            this.loadData();
        } catch (e) {
            alert('发货失败：' + e.message);
        }
    }

    async handleReplacement(orderId) {
        try {
            await APIClient._fetch('/api/recorder/start', { method: 'POST' });
            alert('已处理换货单：' + orderId);
        } catch (e) {
            alert('处理失败：' + e.message);
        }
    }

    _subscribe_events() {
        // WebSocket 已在 test-main 中统一处理
    }

    _on_event(eventType, data) {
        if (eventType === '换货触发' || eventType === '订单生成') {
            this.loadData();
        }
    }
}

window.SupplierPanel = SupplierPanel;
window.supplierPanel = new SupplierPanel();