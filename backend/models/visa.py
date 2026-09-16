# -*- coding: utf-8 -*-
"""
签证实体
受 GPL v3.0 保护

定义工程量/费用签证。支持从差异自动生成。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .entity import BaseEntity
from .physics_rules import visa_cbm
from config import config


class VisaEntity(BaseEntity):
    """签证实体"""

    # 签证类型
    VISA_TYPES = ['工程量签证', '费用签证']

    # 状态
    STATUSES = ['待确认', '已确认', '已支付', '已拒绝']

    def __init__(self, visa_type: str = '工程量签证', reason: str = '',
                 amount: float = 0,
                 evidence: Optional[List[Dict]] = None,
                 target_id: Optional[str] = None,
                 space: Optional[Dict] = None):
        if visa_type not in self.VISA_TYPES:
            visa_type = '工程量签证'
        evidence = evidence or []

        # L2层
        l2 = {
            '签证类型': visa_type,
            '签证原因': reason,
            '金额': f'¥{amount}',
            '证据': evidence,
            '关联构件': target_id,
        }

        # L3层
        l3 = {
            '状态': '待确认',
            '提交日期': None,
            '审批日期': None,
            '支付日期': None,
        }

        # CBM层
        cbm = visa_cbm(visa_type)

        super().__init__(
            entity_type='签证',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.visa_type = visa_type
        self.reason = reason
        self.amount = amount
        self.evidence = list(evidence)
        self.target_id = target_id
        self.space = space or config.SPACE_UNITS

    def submit(self) -> Dict[str, Any]:
        """提交签证"""
        self.layer['l3_dynamic_state']['状态'] = '待确认'
        self.layer['l3_dynamic_state']['提交日期'] = datetime.now().strftime('%Y-%m-%d')
        self.add_event('提交签证', '')
        return {'success': True, 'visa_id': self.id, 'status': '待确认'}

    def approve(self, date: str = '') -> Dict[str, Any]:
        """审批通过"""
        self.layer['l3_dynamic_state']['状态'] = '已确认'
        self.layer['l3_dynamic_state']['审批日期'] = date
        self.add_event('签证审批通过', date)
        return {'success': True, 'visa_id': self.id, 'status': '已确认'}

    def reject(self, reason: str = '') -> Dict[str, Any]:
        """审批不通过"""
        self.layer['l3_dynamic_state']['状态'] = '已拒绝'
        self.add_event('签证拒绝', reason)
        return {'success': True, 'visa_id': self.id, 'status': '已拒绝', 'reason': reason}

    def mark_paid(self, date: str = '') -> Dict[str, Any]:
        """标记已支付"""
        self.layer['l3_dynamic_state']['状态'] = '已支付'
        self.layer['l3_dynamic_state']['支付日期'] = date
        self.add_event('签证已支付', date)
        return {'success': True, 'visa_id': self.id, 'status': '已支付'}

    def get_evidence(self) -> List[Dict[str, Any]]:
        """获取证据"""
        return self.layer['l2_static_attributes'].get('证据', [])

    def get_status(self) -> str:
        """获取签证状态"""
        return self.layer['l3_dynamic_state'].get('状态', '待确认')

    @classmethod
    def auto_generate_from_difference(cls, entity_id: str, difference: float,
                                       unit_price: float = 850,
                                       reason: str = '实际量超清单量',
                                       space: Optional[Dict] = None) -> 'VisaEntity':
        """
        从差异自动生成签证。

        参数：
            entity_id: 构件ID
            difference: 差异量
            unit_price: 单价
            reason: 原因
        """
        amount = abs(difference) * unit_price
        evidence = [
            {
                'type': '照片',
                'count': 3,
                'description': '现场照片',
            },
            {
                'type': '坐标',
                'value': space or {'x': 0, 'y': 0, 'z': 0},
            },
            {
                'type': '时间戳',
                'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            },
        ]

        visa = cls(
            visa_type='工程量签证',
            reason=reason,
            amount=amount,
            evidence=evidence,
            target_id=entity_id,
            space=space,
        )
        visa.submit()
        visa.add_event('自动生成', f'差异{difference}，单价{unit_price}')
        return visa

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '签证',
            'visa_type': self.visa_type,
            'reason': self.reason,
            'amount': self.amount,
            'target_id': self.target_id,
            'status': self.get_status(),
            'layer': self.layer,
        }