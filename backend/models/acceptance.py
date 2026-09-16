# -*- coding: utf-8 -*-
"""
验收实体
受 GPL v3.0 保护

定义工程验收记录。含CBM状态检查。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import acceptance_cbm
from config import config


class AcceptanceEntity(BaseEntity):
    """验收实体"""

    # 验收类型
    ACCEPTANCE_TYPES = ['初验', '复验', '抽检']

    # 状态
    STATUSES = ['待验收', '已验收', '不合格', '整改中']

    def __init__(self, acceptance_type: str = '初验',
                 target_id: Optional[str] = None,
                 inspector: str = '', result: str = '',
                 standard: str = '', acceptance_date: str = '',
                 space: Optional[Dict] = None):
        if acceptance_type not in self.ACCEPTANCE_TYPES:
            acceptance_type = '初验'

        # L2层
        l2 = {
            '验收类型': acceptance_type,
            '验收对象': target_id,
            '验收人': inspector,
            '验收标准': standard,
            '验收日期': acceptance_date,
            'CBM状态': None,
        }

        # L3层
        l3 = {
            '状态': '待验收',
        }

        # CBM层
        cbm = acceptance_cbm(acceptance_type)

        super().__init__(
            entity_type='验收',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.acceptance_type = acceptance_type
        self.target_id = target_id
        self.inspector = inspector
        self.result = result
        self.standard = standard
        self.acceptance_date = acceptance_date
        self.space = space or config.SPACE_UNITS

    def pass_acceptance(self) -> Dict[str, Any]:
        """验收通过"""
        self.layer['l3_dynamic_state']['状态'] = '已验收'
        self.add_event('验收通过', f'验收人：{self.inspector}')
        return {'success': True, 'acceptance_id': self.id, 'status': '已验收'}

    def reject_acceptance(self, reason: str = '') -> Dict[str, Any]:
        """验收不通过"""
        self.layer['l3_dynamic_state']['状态'] = '不合格'
        self.add_event('验收不通过', f'原因：{reason}')
        return {'success': True, 'acceptance_id': self.id, 'status': '不合格', 'reason': reason}

    def check_cbm_status(self, cbm_status: str = 'stable') -> Dict[str, Any]:
        """检查CBM状态"""
        self.layer['l2_static_attributes']['CBM状态'] = cbm_status
        passed = cbm_status == 'stable'
        return {
            'passed': passed,
            'cbm_status': cbm_status,
            'message': 'CBM状态正常' if passed else f'CBM状态异常：{cbm_status}',
        }

    def get_status(self) -> str:
        """获取验收状态"""
        return self.layer['l3_dynamic_state'].get('状态', '待验收')

    def get_records(self) -> list:
        """获取验收记录"""
        return self.layer['l4_event_chain']

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '验收',
            'acceptance_type': self.acceptance_type,
            'target_id': self.target_id,
            'inspector': self.inspector,
            'status': self.get_status(),
            'layer': self.layer,
        }