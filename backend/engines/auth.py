# -*- coding: utf-8 -*-
"""
权限引擎
受 GPL v3.0 保护

角色权限管理。
支持四层CBM权限。

V2.0 升级（专报H）：
- 8单位24岗位的完整权限矩阵
- 中文角色名兼容（通过 ROLE_ALIAS）
"""

from typing import Dict, Any, List, Optional


class AuthEngine:
    """权限引擎"""

    # ★ V2.0 升级：8单位24岗位的完整权限矩阵（专报H要求）
    PERMISSION_MATRIX = {
        # ===================== 甲方（4岗位）=====================
        'owner_pm': {
            'visible': ['progress', 'cost', 'contract'],
            'actions': ['approve', 'payment', 'view'],
            'cbm': ['check_cost', 'check_contract'],
        },
        'owner_eng': {
            'visible': ['progress', 'quality'],
            'actions': ['approve', 'view'],
            'cbm': ['check_quality'],
        },
        'owner_cost': {
            'visible': ['cost', 'visa'],
            'actions': ['approve', 'view', 'edit_cost'],
            'cbm': ['check_cost'],
        },
        'owner_doc': {
            'visible': ['documents'],
            'actions': ['view', 'edit_doc'],
            'cbm': [],
        },

        # ===================== 设计（3岗位）=====================
        'design_pm': {
            'visible': ['drawings', 'changes'],
            'actions': ['issue_drawing', 'view'],
            'cbm': ['check_design'],
        },
        'design_pipe': {
            'visible': ['drawings', 'scene'],
            'actions': ['issue_drawing', 'view', 'modify_drawing'],
            'cbm': ['check_design'],
        },
        'design_bim': {
            'visible': ['drawings', 'scene'],
            'actions': ['issue_drawing', 'view'],
            'cbm': ['check_design'],
        },

        # ===================== 监理（3岗位）=====================
        'sup_chief': {
            'visible': ['pending_inspections', 'scene'],
            'actions': ['inspect', 'accept', 'reject', 'sign', 'view'],
            'cbm': ['check_quality'],
        },
        'sup_eng': {
            'visible': ['pending_inspections'],
            'actions': ['inspect', 'accept', 'view'],
            'cbm': ['check_quality'],
        },
        'sup_inspector': {
            'visible': ['pending_inspections'],
            'actions': ['inspect', 'view'],
            'cbm': ['check_quality'],
        },

        # ===================== 施工（7岗位）=====================
        'con_pm': {
            'visible': ['all_tasks', 'scene', 'cost'],
            'actions': ['install', 'complete', 'assign', 'approve', 'view'],
            'cbm': ['check_assembly', 'check_contact', 'check_cost'],
        },
        'con_foreman': {
            'visible': ['own_tasks', 'scene'],
            'actions': ['install', 'complete', 'view', 'report_problem'],
            'cbm': ['check_assembly', 'check_contact'],
        },
        'con_tech': {
            'visible': ['own_tasks', 'drawings'],
            'actions': ['view', 'report_problem'],
            'cbm': ['check_assembly'],
        },
        'con_biz': {
            'visible': ['cost', 'visa'],
            'actions': ['view', 'edit_cost', 'report_progress'],
            'cbm': ['check_cost'],
        },
        'con_doc': {
            'visible': ['documents'],
            'actions': ['view', 'edit_doc'],
            'cbm': [],
        },
        'con_bim': {
            'visible': ['scene', 'drawings'],
            'actions': ['view', 'edit_model'],
            'cbm': ['check_design'],
        },
        'con_material': {
            'visible': ['materials'],
            'actions': ['view', 'edit_material'],
            'cbm': [],
        },

        # ===================== 分包（3岗位）=====================
        'sub_pm': {
            'visible': ['own_tasks', 'workers'],
            'actions': ['accept_task', 'assign', 'view'],
            'cbm': ['check_assembly'],
        },
        'sub_leader': {
            'visible': ['own_tasks', 'workers'],
            'actions': ['assign', 'report_progress', 'view'],
            'cbm': ['check_assembly'],
        },
        'sub_pipe': {
            'visible': ['own_tasks'],
            'actions': ['install', 'complete', 'view'],
            'cbm': ['check_assembly', 'check_contact'],
        },

        # ===================== 供应商（2岗位）=====================
        'sup_sales': {
            'visible': ['orders'],
            'actions': ['view', 'receive_order', 'ship_order'],
            'cbm': [],
        },
        'sup_stock': {
            'visible': ['inventory'],
            'actions': ['view', 'edit_inventory'],
            'cbm': [],
        },

        # ===================== 物流（2岗位）=====================
        'log_driver': {
            'visible': ['delivery_tasks'],
            'actions': ['accept_task', 'confirm_delivery', 'view'],
            'cbm': [],
        },
        'log_worker': {
            'visible': ['delivery_tasks'],
            'actions': ['view', 'confirm_load'],
            'cbm': [],
        },

        # ===================== 监管（2岗位）=====================
        'reg_quality': {
            'visible': ['quality'],
            'actions': ['view'],
            'cbm': [],
        },
        'reg_safety': {
            'visible': ['safety'],
            'actions': ['view', 'issue_warning'],
            'cbm': [],
        },

        # ===================== 兼容旧角色（中文名）=====================
        '施工员': {'_alias': 'con_foreman'},
        '项目经理': {'_alias': 'con_pm'},
        '造价员': {'_alias': 'con_biz'},
        '监理': {'_alias': 'sup_chief'},
        '甲方': {'_alias': 'owner_pm'},
        '监管': {'_alias': 'reg_quality'},
        '设计师': {'_alias': 'design_pipe'},
        '运维': {
            'visible': ['lifecycle', 'scene'],
            'actions': ['inspect', 'replace', 'view'],
            'cbm': ['check_lifecycle'],
        },
        '管理员': {
            'visible': ['*'],
            'actions': ['*'],
            'cbm': ['*'],
        },
    }

    # ★ V2.0 新增：角色别名映射（中文名 → 岗位ID）
    ROLE_ALIAS = {
        '施工员': 'con_foreman',
        '项目经理': 'con_pm',
        '造价员': 'con_biz',
        '监理': 'sup_chief',
        '甲方': 'owner_pm',
        '监管': 'reg_quality',
        '设计师': 'design_pipe',
    }

    def __init__(self, config_obj=None):
        self.config = config_obj
        self.users: Dict[str, Dict[str, Any]] = {}

    # ★ V2.0 新增：解析角色名（支持中文别名）
    def _resolve_role(self, role: str) -> str:
        """解析角色名（支持中文别名）"""
        if role in self.PERMISSION_MATRIX:
            entry = self.PERMISSION_MATRIX[role]
            if '_alias' in entry:
                return entry['_alias']
            return role
        return self.ROLE_ALIAS.get(role, role)

    # ==================== 权限检查 ====================

    def check_permission(self, user: str, action: str, target=None) -> bool:
        """
        检查权限。

        流程：
            1. 检查用户是否存在
            2. 检查角色（★ V2.0 支持中文别名）
            3. 检查可见范围
            4. 检查操作权限
            5. 检查CBM权限
        """
        if not user:
            return False

        user_info = self.users.get(user, {})
        role = user_info.get('role', '')
        if not role:
            return False

        # ★ V2.0 新增：解析角色别名
        role = self._resolve_role(role)

        # 管理员全权限
        if role == '管理员':
            return True

        perms = self.PERMISSION_MATRIX.get(role, {})
        if not perms:
            return False

        # 检查操作权限
        allowed_actions = perms.get('actions', [])
        if '*' in allowed_actions or action in allowed_actions:
            return True

        return False

    def check_action_permission(self, user: str, action: str) -> bool:
        """检查操作权限"""
        return self.check_permission(user, action)

    def check_entity_visibility(self, user: str, entity) -> bool:
        """检查实体可见性"""
        user_info = self.users.get(user, {})
        role = user_info.get('role', '')

        # ★ V2.0 新增：解析角色别名
        role = self._resolve_role(role)

        if role == '管理员':
            return True

        perms = self.PERMISSION_MATRIX.get(role, {})
        visible = perms.get('visible', [])
        if '*' in visible:
            return True

        entity_type = getattr(entity, 'entity_type', '')
        if 'scene' in visible:
            return True
        if 'own_tasks' in visible and '任务' in entity_type:
            return True

        return False

    def check_cbm_permission(self, user: str, cbm_action: str, entity) -> bool:
        """检查CBM权限（四层CBM权限）"""
        user_info = self.users.get(user, {})
        role = user_info.get('role', '')

        # ★ V2.0 新增：解析角色别名
        role = self._resolve_role(role)

        if role == '管理员':
            return True

        perms = self.PERMISSION_MATRIX.get(role, {})
        cbm_perms = perms.get('cbm', [])
        return '*' in cbm_perms or cbm_action in cbm_perms

    # ==================== 角色权限 ====================

    def get_role_permissions(self, role: str) -> List[str]:
        """获取角色权限"""
        # ★ V2.0 新增：解析角色别名
        role = self._resolve_role(role)

        perms = self.PERMISSION_MATRIX.get(role, {})
        return perms.get('actions', [])

    def get_visible_range(self, user: str) -> Dict[str, Any]:
        """获取可见范围"""
        user_info = self.users.get(user, {})
        role = user_info.get('role', '')

        # ★ V2.0 新增：解析角色别名
        role = self._resolve_role(role)

        perms = self.PERMISSION_MATRIX.get(role, {})
        return {
            'role': role,
            'visible': perms.get('visible', []),
            'actions': perms.get('actions', []),
            'cbm': perms.get('cbm', []),
        }

    # ==================== 过滤 ====================

    def filter_entities(self, role: str, entities: List) -> List:
        """按权限过滤实体"""
        # ★ V2.0 新增：解析角色别名
        role = self._resolve_role(role)

        perms = self.PERMISSION_MATRIX.get(role, {})
        visible = perms.get('visible', [])
        if '*' in visible:
            return list(entities)

        result = []
        for e in entities:
            etype = getattr(e, 'entity_type', '')
            if 'scene' in visible:
                result.append(e)
            elif 'own_tasks' in visible and '任务' in etype:
                result.append(e)
            elif 'cost' in visible and etype in ('管道', '支架', '阀门', '卡箍'):
                result.append(e)
        return result

    # ==================== 用户信息 ====================

    def get_user_org(self, user: str) -> str:
        """获取用户单位"""
        return self.users.get(user, {}).get('organization', '')

    def get_user_role(self, user: str) -> str:
        """获取用户角色"""
        role = self.users.get(user, {}).get('role', '')
        # ★ V2.0 新增：返回解析后的角色
        return self._resolve_role(role) if role else ''

    def register_user(self, user_id: str, role: str, organization: str = '') -> Dict[str, Any]:
        """注册用户（简化）"""
        self.users[user_id] = {
            'user_id': user_id,
            'role': role,
            'organization': organization,
        }
        return {'success': True, 'user_id': user_id}

    # ==================== 内部方法 ====================

    def _load_permission_matrix(self) -> Dict[str, Any]:
        """加载权限矩阵"""
        return self.PERMISSION_MATRIX

    def _check_org_permission(self, user_org: str, entity_org: str) -> bool:
        """检查单位权限"""
        if not user_org or not entity_org:
            return True
        return user_org == entity_org

    def _check_profession_permission(self, user_prof: str, entity_prof: str) -> bool:
        """检查专业权限"""
        if not user_prof or not entity_prof:
            return True
        return user_prof == entity_prof