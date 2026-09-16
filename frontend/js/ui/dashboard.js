/**
 * 仪表盘
 * 受 GPL v3.0 保护
 */
class DashboardUI {
    constructor(containerId = 'dashboardContainer') {
        this.containerId = containerId;
        this.refreshTimer = null;
    }

    init() {
        this.render();
        this.loadData();
        this.refreshTimer = setInterval(() => this.loadData(), 30000);
    }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:16px;">
                <h2>仪表盘</h2>
                <div id="dashboardContent" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px;">
                    <div class="dash-card" id="dashProject"></div>
                    <div class="dash-card" id="dashCost"></div>
                    <div class="dash-card" id="dashTask"></div>
                    <div class="dash-card" id="dashCBM"></div>
                </div>
            </div>
        `;
    }

    async loadData() {
        try {
            const [scene, cost, cbmStats] = await Promise.all([
                APIClient.getScene().catch(() => ({})),
                APIClient.getCostSummary().catch(() => ({})),
                APIClient.getCBMStats().catch(() => ({})),
            ]);
            this.renderProjectCard(scene);
            this.renderCostCard(cost);
            this.renderTaskCard({});
            this.renderCBMStatusCard(cbmStats);
        } catch (e) {
            console.warn('仪表盘加载失败', e);
        }
    }

    renderProjectCard(scene) {
        const el = document.getElementById('dashProject');
        if (!el) return;
        const total = (scene && scene.data && scene.data.total) || 0;
        el.innerHTML = `<h4>项目概览</h4><p>实体总数：${total}</p>`;
    }

    renderProgressCard(progress) {
        const el = document.getElementById('dashProject');
        if (el && progress) el.innerHTML += `<p>进度：${progress.percentage || 0}%</p>`;
    }

    renderCostCard(cost) {
        const el = document.getElementById('dashCost');
        if (!el) return;
        const d = (cost && cost.data) || {};
        el.innerHTML = `<h4>造价概览</h4><p>总额：¥${d.total || 0}</p><p>签证数：${d.visaCount || 0}</p>`;
    }

    renderTaskCard(tasks) {
        const el = document.getElementById('dashTask');
        if (!el) return;
        el.innerHTML = `<h4>今日任务</h4><p>待执行：0</p><p>执行中：0</p><p>已完成：0</p>`;
    }

    renderCBMStatusCard(cbmStats) {
        const el = document.getElementById('dashCBM');
        if (!el) return;
        const d = (cbmStats && cbmStats.data) || {};
        el.innerHTML = `
            <h4>CBM状态</h4>
            <p>稳定：${d.stable || 0}</p>
            <p>预警：${d.warning || 0}</p>
            <p>超载：${d.overload || 0}</p>
            <p>碰撞：${d.collision || 0}</p>
        `;
    }

    renderEventStream(events) {
        // 由 EventStream 处理
    }

    renderNotifications(notifications) {
        // 由 NotificationCenter 处理
    }

    quickActions() {
        return [
            { label: '刷新', fn: () => this.loadData() },
        ];
    }

    onEntityClick(entityId) {
        if (window.showEntity) window.showEntity(entityId);
    }
}

window.DashboardUI = DashboardUI;
window.dashboard = new DashboardUI();