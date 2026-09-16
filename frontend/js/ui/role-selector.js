/**
 * 角色选择器
 * 受 GPL v3.0 保护
 */
class RoleSelector {
    constructor(containerId = 'roleSelectorContainer') {
        this.containerId = containerId;
        this.currentOrg = '';
        this.currentRole = '';
    }

    init() {
        this.render();
    }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:8px;">
                <div id="roleOrgList"></div>
                <div id="roleRoleList" style="margin-top:8px;"></div>
            </div>
        `;
        this.renderOrgList();
    }

    renderOrgList() {
        const el = document.getElementById('roleOrgList');
        if (!el) return;
        el.innerHTML = Object.keys(ORGS).map(code =>
            `<div onclick="window.roleSelector.selectOrg('${code}')"
                style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;cursor:pointer;
                border-left:3px solid ${ORGS[code].color};">
                ${ORGS[code].name}
            </div>`
        ).join('');
    }

    renderRoleList(orgCode) {
        const el = document.getElementById('roleRoleList');
        if (!el) return;
        const org = ORGS[orgCode];
        if (!org) {
            el.innerHTML = '';
            return;
        }
        el.innerHTML = org.roles.map(role =>
            `<div onclick="window.roleSelector.selectRole('${role}')"
                style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;cursor:pointer;">
                ${role}
            </div>`
        ).join('');
    }

    selectOrg(orgCode) {
        this.currentOrg = orgCode;
        this.renderRoleList(orgCode);
    }

    selectRole(roleId) {
        this.currentRole = roleId;
        if (window.state) window.state.currentRole = roleId;
        this.onRoleChange(roleId);
    }

    getCurrentRole() {
        return this.currentRole;
    }

    onRoleChange(role) {
        console.log('角色切换：', role);
        if (window.renderCurrentTab) window.renderCurrentTab();
    }

    getRolePermissions(role) {
        return APIClient._fetch(`/api/auth/permissions/${role}`);
    }
}

window.RoleSelector = RoleSelector;
window.roleSelector = new RoleSelector();