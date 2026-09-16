# -*- coding: utf-8 -*-
"""
变更实体
受 GPL v3.0 保护

定义工程变更记录。含L4影响CBM决策。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import change_cbm
from config import config


class ChangeEntity(BaseEntity):
    """变更实体"""

    # 变更类型
    CHANGE_TYPES = ['设计变更', '现场变更', '甲方变更']

    # 状态
    STATUSES = ['待确认', '已确认', '已执行', '已拒绝']

    def __init__(self, change_type: str = '设计变更', reason: str = '',
                 target_id: Optional[str] = None,
                 before: Optional[Dict] = None,
                 after: Optional[Dict] = None,
                 added_cost: float = 0,
                 space: Optional[Dict] = None):
        if change_type not in self.CHANGE_TYPES:
            change_type = '设计变更'

        # L2层
        l2 = {
            '变更类型': change_type,
            '变更原因': reason,
            '关联构件': target_id,
            '变更前状态': before,
            '变更后状态': after,
            '增加造价': f'¥{added_cost}',
        }

        # L3层
        l3 = {
            '状态': '待确认',
            '审批日期': None,
            '执行日期': None,
        }

        # CBM层
        cbm = change_cbm(change_type)

        super().__init__(
            entity_type='变更',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.change_type = change_type
        self.reason = reason
        self.target_id = target_id
        self.before = before
        self.after = after
        self.added_cost = added_cost
        self.space = space or config.SPACE_UNITS

    def approve(self, date: str = '') -> Dict[str, Any]:
        """审批通过"""
        self.layer['l3_dynamic_state']['状态'] = '已确认'
        self.layer['l3_dynamic_state']['审批日期'] = date
        self.add_event('变更审批通过', date)
        self.record_to_l4()
        return {'success': True, 'change_id': self.id, 'status': '已确认'}

    def reject(self, reason: str = '') -> Dict[str, Any]:
        """审批不通过"""
        self.layer['l3_dynamic_state']['状态'] = '已拒绝'
        self.add_event('变更拒绝', reason)
        return {'success': True, 'change_id': self.id, 'status': '已拒绝', 'reason': reason}

    def execute(self) -> Dict[str, Any]:
        """执行变更"""
        self.layer['l3_dynamic_state']['状态'] = '已执行'
        self.add_event('变更执行', '')
        return {'success': True, 'change_id': self.id, 'status': '已执行'}

    def calc_cost_difference(self) -> Dict[str, Any]:
        """计算变更费用差异"""
        return {
            'change_id': self.id,
            'added_cost': self.added_cost,
            'difference': self.added_cost,
        }

    def record_to_l4(self) -> Dict[str, Any]:
        """记录到L4影响CBM"""
        self.add_event('L4变更记录', f'{self.change_type}：{self.reason}')
        return {'success': True, 'message': '已记录到L4'}

    def get_status(self) -> str:
        """获取变更状态"""
        return self.layer['l3_dynamic_state'].get('状态', '待确认')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '变更',
            'change_type': self.change_type,
            'reason': self.reason,
            'target_id': self.target_id,
            'added_cost': self.added_cost,
            'status': self.get_status(),
            'layer': self.layer,
        }