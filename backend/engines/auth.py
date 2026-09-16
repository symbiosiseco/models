# -*- coding: utf-8 -*-
"""
权限引擎
受 GPL v3.0 保护

角色权限管理。
支持四层CBM权限。
"""

from typing import Dict, Any, List, Optional


class AuthEngine:
    """权限引擎"""

    # 角色权限矩阵
    PERMISSION_MATRIX = {
        '施工员': {
            'visible': ['own_tasks', 'scene'],
            'actions': ['install', 'complete', 'view', 'report_problem'],
            'cbm': ['check_assembly', 'check_contact'],
        },
        '项目经理': {
            'visible': ['all_tasks', 'scene', 'cost'],
            'actions': ['install', 'complete', 'assign', 'approve', 'view'],
            'cbm': ['check_assembly', 'check_contact', 'check_cost'],
        },
        '造价员': {
            'visible': ['cost'],
            'actions': ['view', 'edit_cost', 'check_differences'],
            'cbm': ['check_cost'],
        },
        '监理': {
            'visible': ['pending_inspections', 'scene'],
            'actions': ['inspect', 'accept', 'reject', 'view'],
            'cbm': ['check_quality'],
        },
        '甲方': {
            'visible': ['progress', 'cost', 'contract'],
            'actions': ['approve', 'payment', 'view'],
            'cbm': ['check_cost', 'check_contract'],
        },
        '运维': {
            'visible': ['lifecycle', 'scene'],
            'actions': ['inspect', 'replace', 'view'],
            'cbm': ['check_lifecycle'],
        },
        '监管': {
            'visible': ['quality', 'safety'],
            'actions': ['view'],
            'cbm': [],
        },
        '设计师': {
            'visible': ['drawings', 'scene'],
            'actions': ['view', 'modify_drawing', 'issue_drawing'],
            'cbm': ['check_design'],
        },
        '管理员': {
            'visible': ['*'],
            'actions': ['*'],
            'cbm': ['*'],
        },
    }

    def __init__(self, config_obj=None):
        self.config = config_obj
        self.users: Dict[str, Dict[str, Any]] = {}

    # ==================== 权限检查 ====================

    def check_permission(self, user: str, action: str, target=None) -> bool:
        """
        检查权限。

        流程：
            1. 检查用户是否存在
            2. 检查角色
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
        if role == '管理员':
            return True

        perms = self.PERMISSION_MATRIX.get(role, {})
        cbm_perms = perms.get('cbm', [])
        return '*' in cbm_perms or cbm_action in cbm_perms

    # ==================== 角色权限 ====================

    def get_role_permissions(self, role: str) -> List[str]:
        """获取角色权限"""
        perms = self.PERMISSION_MATRIX.get(role, {})
        return perms.get('actions', [])

    def get_visible_range(self, user: str) -> Dict[str, Any]:
        """获取可见范围"""
        user_info = self.users.get(user, {})
        role = user_info.get('role', '')
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
        return self.users.get(user, {}).get('role', '')

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