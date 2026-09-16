/**
 * 更多功能菜单
 * 受 GPL v3.0 保护
 */
const FEATURES = [
    { id: 'template', icon: '📚', label: '模板库', panel: 'templatePanel' },
    { id: 'generator', icon: '✨', label: '数字生命体生成器', panel: 'generatorPanel' },
    { id: 'assembly', icon: '🔧', label: '装配测试', panel: 'assemblyDemo' },
    { id: 'task', icon: '📅', label: '任务看板', panel: 'taskBoard' },
    { id: 'animation', icon: '🎬', label: '动画演示', panel: 'demoPlayer' },
    { id: 'report', icon: '📊', label: '报表', panel: 'reportViewer' },
    { id: 'event', icon: '⚡', label: '事件流', panel: 'eventStream' },
    { id: 'force', icon: '🎯', label: '受力点查看器', panel: 'ForcePointViewer' },
    { id: 'cbm', icon: '📈', label: 'CBM状态面板', panel: 'cbmStatusPanel' },
    { id: 'l4', icon: '📜', label: 'L4套娃履历', panel: 'l4Viewer' },
    { id: 'settings', icon: '⚙️', label: '设置', panel: null },
];

class MoreMenu {
    constructor() {
        this.menu = null;
        this.createTopButton();
        this.createMenu();
    }

    createTopButton() {
        const btn = document.createElement('button');
        btn.id = 'moreMenuBtn';
        btn.textContent = '⋯ 更多功能';
        btn.style.cssText = `
            position: fixed; top: 140px; right: 16px; z-index: 999;
            background: #001529; color: #fff; border: none;
            padding: 8px 12px; border-radius: 4px; cursor: pointer;
            font-size: 12px;
        `;
        btn.onclick = () => this.toggleMenu();
        document.body.appendChild(btn);
    }

    createMenu() {
        const menu = document.createElement('div');
        menu.id = 'moreMenu';
        menu.style.cssText = `
            position: fixed; top: 180px; right: 16px; z-index: 1000;
            width: 200px; background: #fff; border-radius: 6px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2); display: none; padding: 4px;
        `;
        menu.innerHTML = FEATURES.map(f =>
            `<div onclick="window.moreMenu.handleFeature('${f.id}')"
                style="padding:6px 8px;border-radius:4px;cursor:pointer;font-size:12px;"
                onmouseover="this.style.background='#f0f0f0'"
                onmouseout="this.style.background='transparent'">
                ${f.icon} ${f.label}
            </div>`
        ).join('');
        document.body.appendChild(menu);
        this.menu = menu;
    }

    toggleMenu() {
        this.menu.style.display = this.menu.style.display === 'block' ? 'none' : 'block';
    }

    closeMenu() {
        this.menu.style.display = 'none';
    }

    handleFeature(id) {
        const feature = FEATURES.find(f => f.id === id);
        if (!feature) return;
        this.closeMenu();

        if (!feature.panel) {
            alert('开发中...');
            return;
        }

        const panel = window[feature.panel];
        if (panel && typeof panel.open === 'function') {
            panel.open();
        } else {
            alert('开发中...');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.moreMenu = new MoreMenu();
});