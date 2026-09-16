/**
 * 主逻辑
 * 受 GPL v3.0 保护
 *
 * 初始化渲染器、加载实体、组织UI、处理交互。
 * 含事件总线订阅 + CBM 状态管理。
 */

// ==================== 全局状态 ====================
const state = {
    entities: [],
    entityMap: {},
    collisions: [],
    forcePoints: [],
    cbmStatusMap: {},
    events: [],
    renderer: null,
    websocket: null,
    currentOrg: '',
    currentRole: '',
    currentTab: 'overview',
    selectedEntity: null,
    showForcePoints: true,
    showCBMStatus: true,
};

// 8 单位 24 岗位
const ORGS = {
    owner: { name: '建设单位', color: '#1677ff', roles: ['项目负责人', '专业工程师', '成本工程师', '资料管理员'] },
    design: { name: '设计单位', color: '#722ed1', roles: ['项目负责人', '管道设计师', 'BIM工程师'] },
    supervision: { name: '监理单位', color: '#13c2c2', roles: ['总监理工程师', '专业监理工程师', '监理员'] },
    contractor: { name: '施工单位', color: '#52c41a', roles: ['项目经理', '施工员', '技术员', '商务员', '资料员', 'BIM工程师', '材料员'] },
    subcontractor: { name: '分包单位', color: '#fa8c16', roles: ['分包负责人', '班组长', '管道工'] },
    supplier: { name: '材料供应商', color: '#eb2f96', roles: ['销售经理', '库管员'] },
    logistics: { name: '运输单位', color: '#a0d911', roles: ['司机', '搬运工'] },
    regulator: { name: '监管部门', color: '#f5222d', roles: ['质监站', '安监站'] },
};

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
    init();
});

async function init() {
    // 1. 创建渲染器
    try {
        state.renderer = new Renderer3D('canvas3d');
    } catch (e) {
        console.error('渲染器初始化失败', e);
    }

    // 2. 渲染左侧栏
    renderOrgList();
    renderRoleList('');
    renderActions();

    // 3. 初始化 Tab
    initTabs();

    // 4. 加载数据
    try {
        const res = await APIClient.getEntities();
        if (res && res.success) {
            state.entities = res.data || [];
            state.entityMap = {};
            for (const e of state.entities) {
                state.entityMap[e.id] = e;
            }
            if (state.renderer) {
                state.renderer.setEntities(state.entities);
            }
            renderCurrentTab();
            updateStats();
        }
    } catch (e) {
        console.warn('加载实体失败', e);
    }

    // 5. 加载碰撞
    try {
        const res = await APIClient.getCollisions();
        if (res && res.success) {
            state.collisions = res.data || [];
            if (state.renderer) {
                state.renderer.setCollisions(state.collisions);
            }
        }
    } catch (e) {
        console.warn('加载碰撞失败', e);
    }

    // 6. 加载 CBM 统计
    try {
        const res = await APIClient.getCBMStats();
        if (res && res.success) {
            state.cbmStatusMap = res.data || {};
        }
    } catch (e) {
        console.warn('加载CBM统计失败', e);
    }

    // 7. 初始化拖动条
    initSplitters();

    // 8. 初始化 WebSocket
    initWebSocket();
}

// ==================== 左侧栏 ====================

function renderOrgList() {
    const el = document.getElementById('orgList');
    if (!el) return;
    el.innerHTML = '';
    for (const code in ORGS) {
        const org = ORGS[code];
        const div = document.createElement('div');
        div.className = 'org-item';
        div.textContent = org.name;
        div.style.borderLeft = `3px solid ${org.color}`;
        div.onclick = () => {
            state.currentOrg = code;
            renderOrgList();
            renderRoleList(code);
        };
        if (state.currentOrg === code) div.classList.add('active');
        el.appendChild(div);
    }
}

function renderRoleList(orgCode) {
    const el = document.getElementById('roleList');
    if (!el) return;
    el.innerHTML = '';
    const org = ORGS[orgCode];
    if (!org) return;
    for (const role of org.roles) {
        const div = document.createElement('div');
        div.className = 'role-item';
        div.textContent = role;
        div.onclick = () => {
            state.currentRole = role;
            renderRoleList(orgCode);
            renderCurrentTab();
        };
        if (state.currentRole === role) div.classList.add('active');
        el.appendChild(div);
    }
}

function renderActions() {
    const el = document.getElementById('actionList');
    if (!el) return;
    const actions = [
        { label: '刷新数据', fn: () => window.refreshAll() },
        { label: '全屏画布', fn: () => window.toggleFullscreen() },
        { label: '收起左栏', fn: () => window.collapseLeft() },
        { label: '收起右栏', fn: () => window.collapseRight() },
    ];
    el.innerHTML = '';
    for (const a of actions) {
        const div = document.createElement('div');
        div.className = 'action-item';
        div.textContent = a.label;
        div.onclick = a.fn;
        el.appendChild(div);
    }
}

// ==================== Tab ====================

function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.onclick = () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            state.currentTab = tab.dataset.tab;
            renderCurrentTab();
        };
    });
}

function renderCurrentTab() {
    const el = document.getElementById('tabContent');
    if (!el) return;
    switch (state.currentTab) {
        case 'overview': renderOverviewPanel(el); break;
        case 'cost': renderCostPanel(el); break;
        case 'task': renderTaskPanel(el); break;
        case 'workflow': renderWorkflowPanel(el); break;
        case 'maintenance': renderMaintenancePanel(el); break;
    }
}

function renderOverviewPanel(el) {
    const total = state.entities.length;
    const installed = state.entities.filter(e => {
        const st = e.layer && e.layer.l3_dynamic_state && e.layer.l3_dynamic_state['状态'];
        return st === '已安装' || st === '已验收';
    }).length;
    el.innerHTML = `
        <div style="padding:12px;">
            <h3>项目概览</h3>
            <p>实体总数：${total}</p>
            <p>已安装：${installed}</p>
            <p>碰撞：${state.collisions.length}</p>
            <p>当前角色：${state.currentRole || '未选择'}</p>
        </div>
    `;
}

function renderCostPanel(el) {
    APIClient.getCostSummary().then(res => {
        if (res && res.success) {
            const d = res.data || {};
            el.innerHTML = `
                <div style="padding:12px;">
                    <h3>造价概览</h3>
                    <p>总额：¥${d.total || 0}</p>
                    <p>签证数：${d.visaCount || 0}</p>
                </div>
            `;
        }
    }).catch(() => {
        el.innerHTML = '<div style="padding:12px;color:#999;">造价数据加载失败</div>';
    });
}

function renderTaskPanel(el) {
    el.innerHTML = '<div style="padding:12px;color:#999;">任务看板（点击"更多功能 → 任务看板"查看完整）</div>';
}

function renderWorkflowPanel(el) {
    el.innerHTML = '<div style="padding:12px;color:#999;">流程看板（点击"更多功能 → 签字面板"查看完整）</div>';
}

function renderMaintenancePanel(el) {
    el.innerHTML = '<div style="padding:12px;color:#999;">运维面板（点击"更多功能 → L4套娃履历"查看完整）</div>';
}

// ==================== 显示实体 ====================

window.showEntity = function (id) {
    const entity = state.entityMap[id];
    if (!entity) return;
    state.selectedEntity = entity;

    // 渲染六层
    renderLayers(entity);
    // 渲染受力点
    renderForcePointsPanel(entity);
    // 渲染 CBM
    renderCBMStatusPanel(entity);
    // 渲染接触面
    renderContactFacesPanel(entity);
    // 渲染 L4
    renderL4Panel(entity);
};

function renderLayers(entity) {
    const el = document.getElementById('entityLayers');
    if (!el) return;
    const layer = entity.layer || {};
    const layers = [
        ['R层', layer.r_layer],
        ['L1层', layer.l1_identity],
        ['L2层', layer.l2_static_attributes],
        ['L3层', layer.l3_dynamic_state],
        ['L4层', layer.l4_event_chain],
        ['CBM层', layer.cbm_abilities],
    ];
    let html = `<div style="margin-bottom:8px;font-weight:600;">${entity.id} · ${entity.entity_type}</div>`;
    for (const [name, val] of layers) {
        html += `
            <div class="layer-block">
                <div class="layer-block-header">${name}</div>
                <div class="layer-block-body">${JSON.stringify(val, null, 2)}</div>
            </div>
        `;
    }
    el.innerHTML = html;
}

function renderForcePointsPanel(entity) {
    const el = document.getElementById('forcePointsPanel');
    if (!el) return;
    if (window.ForcePointViewer && state.selectedEntity) {
        window.ForcePointViewer.load(entity.id);
    } else {
        const l2 = entity.layer ? entity.layer.l2_static_attributes : {};
        const fps = (l2 && l2['受力点']) || [];
        el.innerHTML = fps.length === 0
            ? '<div class="empty-hint">无受力点</div>'
            : fps.map(fp => `<div class="fp-item">${fp.id || '受力点'} · ${fp['类型'] || ''} · ${fp['承重上限'] || ''}</div>`).join('');
    }
}

function renderCBMStatusPanel(entity) {
    const el = document.getElementById('cbmStatusPanel');
    if (!el) return;
    if (window.CBMStatusPanel && state.selectedEntity) {
        window.CBMStatusPanel.load(entity.id);
    } else {
        const cbm = entity.layer ? entity.layer.cbm_abilities : {};
        const status = (entity.layer && entity.layer.l3_dynamic_state && entity.layer.l3_dynamic_state.cbm_status) || 'stable';
        el.innerHTML = `<div class="cbm-tag ${status}">${status}</div>`;
    }
}

function renderContactFacesPanel(entity) {
    const el = document.getElementById('contactFacesPanel');
    if (!el) return;
    const l2 = entity.layer ? entity.layer.l2_static_attributes : {};
    const cfs = (l2 && l2['接触面']) || [];
    el.innerHTML = cfs.length === 0
        ? '<div class="empty-hint">无接触面</div>'
        : cfs.map(cf => `<div class="cf-item">${cf.id || '接触面'} · ${cf['类型'] || ''} · 偏差${cf['允许偏差'] || ''}</div>`).join('');
}

function renderL4Panel(entity) {
    const el = document.getElementById('l4Panel');
    if (!el) return;
    if (window.L4Viewer && state.selectedEntity) {
        window.L4Viewer.show(entity.id);
    } else {
        const l4 = (entity.layer && entity.layer.l4_event_chain) || [];
        el.innerHTML = l4.length === 0
            ? '<div class="empty-hint">暂无履历</div>'
            : l4.map(e => `<div class="l4-item">${e.time || ''} · ${e.event || ''} · ${e.detail || ''}</div>`).join('');
    }
}

// ==================== 全屏/收起 ====================

window.toggleFullscreen = function () {
    document.body.classList.toggle('fullscreen');
    setTimeout(() => {
        if (state.renderer) {
            const canvas = document.getElementById('canvas3d');
            if (canvas) {
                state.renderer.camera.aspect = canvas.clientWidth / canvas.clientHeight;
                state.renderer.camera.updateProjectionMatrix();
                state.renderer.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
            }
        }
    }, 100);
};

window.collapseLeft = function () {
    document.body.classList.toggle('collapse-left');
};
window.collapseRight = function () {
    document.body.classList.toggle('collapse-right');
};

// ==================== 刷新 ====================

window.refreshAll = async function () {
    try {
        const res = await APIClient.getEntities();
        if (res && res.success) {
            state.entities = res.data || [];
            state.entityMap = {};
            for (const e of state.entities) state.entityMap[e.id] = e;
            if (state.renderer) state.renderer.setEntities(state.entities);
            updateStats();
        }
    } catch (e) {
        console.warn('刷新失败', e);
    }
};

function updateStats() {
    const el = document.getElementById('sceneStats');
    if (el) el.textContent = `实体：${state.entities.length}`;
    const footer = document.getElementById('footerStats');
    if (footer) footer.textContent = `实体：${state.entities.length} · 碰撞：${state.collisions.length}`;
}

// ==================== 拖动条 ====================

function initSplitters() {
    initSplitter('splitterLeft', 'left');
    initSplitter('splitterRight', 'right');
    initSplitterH('splitterH');
}

function initSplitter(id, side) {
    const el = document.getElementById(id);
    if (!el) return;
    let startX = 0;
    let startWidth = 0;

    el.addEventListener('mousedown', (e) => {
        startX = e.clientX;
        const root = document.documentElement;
        startWidth = parseInt(getComputedStyle(root).getPropertyValue(
            side === 'left' ? '--left-width' : '--right-width'
        )) || 220;

        const onMove = (ev) => {
            const delta = side === 'left' ? ev.clientX - startX : startX - ev.clientX;
            const newWidth = Math.max(100, Math.min(500, startWidth + delta));
            document.documentElement.style.setProperty(
                side === 'left' ? '--left-width' : '--right-width',
                newWidth + 'px'
            );
        };
        const onUp = () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
}

function initSplitterH(id) {
    const el = document.getElementById(id);
    if (!el) return;
    let startY = 0;
    let startHeight = 0;

    el.addEventListener('mousedown', (e) => {
        startY = e.clientY;
        const root = document.documentElement;
        startHeight = parseInt(getComputedStyle(root).getPropertyValue('--canvas-height')) || 60;

        const onMove = (ev) => {
            const delta = ev.clientY - startY;
            const newHeight = Math.max(20, Math.min(90, startHeight + delta / 5));
            document.documentElement.style.setProperty('--canvas-height', newHeight + '%');
        };
        const onUp = () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
}

// ==================== WebSocket ====================

function initWebSocket() {
    state.websocket = APIClient.connectWebSocket((data) => {
        onWebSocketEvent(data);
    });
}

function onWebSocketEvent(data) {
    // 1. 添加到事件流
    state.events.unshift(data);
    if (state.events.length > 100) state.events.pop();
    if (window.EventStream) {
        window.EventStream.addEvent(data);
    }

    // 2. 更新实体
    if (data.event_type === 'L3变化' && data.entity_id) {
        updateEntityFromEvent(data);
        if (state.renderer) state.renderer.setEntities(state.entities);
    }

    // 3. 更新 CBM 状态
    if (data.event_type === '装配失败' || data.event_type === '接触面错误') {
        state.cbmStatusMap[data.entity_id] = 'overload';
        if (state.renderer) state.renderer.setCBMStatus(state.cbmStatusMap);
    }
}

function updateEntityFromEvent(data) {
    const entity = state.entityMap[data.entity_id];
    if (!entity) return;
    if (data.new_status && entity.layer && entity.layer.l3_dynamic_state) {
        entity.layer.l3_dynamic_state['状态'] = data.new_status;
    }
    if (data.position && entity.layer && entity.layer.l3_dynamic_state) {
        entity.layer.l3_dynamic_state['绝对坐标'] = data.position;
    }
}

// ==================== 受力点/ CBM 切换 ====================

window.toggleForcePoints = function () {
    state.showForcePoints = !state.showForcePoints;
    if (state.renderer) state.renderer.toggleForcePoints();
};

window.toggleCBMStatus = function () {
    state.showCBMStatus = !state.showCBMStatus;
    if (state.renderer) state.renderer.toggleCBMStatus();
};

// 暴露全局
window.state = state;