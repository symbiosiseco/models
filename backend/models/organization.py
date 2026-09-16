# -*- coding: utf-8 -*-
"""
组织实体
受 GPL v3.0 保护

定义8个参建单位。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import organization_cbm
from config import config


class OrganizationEntity(BaseEntity):
    """组织实体"""

    # 8个单位
    ORG_SPECS = {
        'owner': {
            'name': '建设单位', 'type': '甲方',
            'roles': ['项目负责人', '专业工程师', '成本工程师', '资料管理员'],
            'permissions': ['view_progress', 'approve_payment', 'approve_change'],
        },
        'design': {
            'name': '设计单位', 'type': '设计',
            'roles': ['项目负责人', '管道设计师', 'BIM工程师'],
            'permissions': ['view_site', 'modify_drawing', 'issue_drawing'],
        },
        'supervision': {
            'name': '监理单位', 'type': '监理',
            'roles': ['总监理工程师', '专业监理工程师', '监理员'],
            'permissions': ['inspect', 'accept', 'reject'],
        },
        'contractor': {
            'name': '施工单位', 'type': '总包',
            'roles': ['项目经理', '施工员', '技术员', '商务员', '资料员', 'BIM工程师', '材料员'],
            'permissions': ['install', 'complete', 'report'],
        },
        'subcontractor': {
            'name': '分包单位', 'type': '分包',
            'roles': ['分包负责人', '班组长', '管道工'],
            'permissions': ['accept_task', 'assign_worker', 'report_progress'],
        },
        'supplier': {
            'name': '材料供应商', 'type': '供应商',
            'roles': ['销售经理', '库管员'],
            'permissions': ['receive_order', 'ship', 'handle_replacement'],
        },
        'logistics': {
            'name': '运输单位', 'type': '物流',
            'roles': ['司机', '搬运工'],
            'permissions': ['deliver', 'track'],
        },
        'regulator': {
            'name': '监管部门', 'type': '政府',
            'roles': ['质监站', '安监站'],
            'permissions': ['check_quality', 'check_safety', 'issue_warning'],
        },
    }

    def __init__(self, org_code: str = '', org_name: str = '',
                 org_type: str = '', contact: str = '',
                 phone: str = '', address: str = '',
                 space: Optional[Dict] = None):
        spec = self.ORG_SPECS.get(org_code, {})
        org_name = org_name or spec.get('name', org_code)
        org_type = org_type or spec.get('type', '')

        # L2层
        l2 = {
            '单位编码': org_code,
            '单位名称': org_name,
            '单位类型': org_type,
            '联系人': contact,
            '电话': phone,
            '地址': address,
            '岗位列表': spec.get('roles', []),
            '权限列表': spec.get('permissions', []),
        }

        # L3层
        l3 = {
            '状态': '正常',
        }

        # CBM层
        cbm = organization_cbm(org_code, org_type)

        super().__init__(
            entity_type='组织',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.org_code = org_code
        self.org_name = org_name
        self.org_type = org_type
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['单位编码'] = org_code
        self.layer['r_layer']['单位类型'] = org_type

    def get_roles(self) -> List[str]:
        """获取该单位的岗位列表"""
        return self.layer['l2_static_attributes'].get('岗位列表', [])

    def get_permissions(self) -> List[str]:
        """获取该单位的权限列表"""
        return self.layer['l2_static_attributes'].get('权限列表', [])

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '组织',
            'org_code': self.org_code,
            'org_name': self.org_name,
            'org_type': self.org_type,
            'layer': self.layer,
        }