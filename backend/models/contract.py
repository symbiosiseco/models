# -*- coding: utf-8 -*-
"""
合同实体
受 GPL v3.0 保护

定义工程合同。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import contract_cbm
from config import config


class ContractEntity(BaseEntity):
    """合同实体"""

    # 合同类型
    CONTRACT_TYPES = ['总包', '分包', '采购', '监理']

    # 合同状态
    STATUSES = ['草签', '已签', '执行中', '已完成']

    def __init__(self, contract_type: str = '总包', party_a: str = '',
                 party_b: str = '', amount: float = 0,
                 duration_days: int = 0, project_id: Optional[str] = None,
                 space: Optional[Dict] = None):
        # L2层
        l2 = {
            '合同类型': contract_type,
            '甲方': party_a,
            '乙方': party_b,
            '金额': f'¥{amount}',
            '工期': f'{duration_days}天',
            '关联项目': project_id,
        }

        # L3层
        l3 = {
            '状态': '草签',
            '签订日期': None,
        }

        # CBM层
        cbm = contract_cbm(contract_type, amount)

        super().__init__(
            entity_type='合同',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.contract_type = contract_type
        self.party_a = party_a
        self.party_b = party_b
        self.amount = amount
        self.project_id = project_id
        self.space = space or config.SPACE_UNITS

    def sign(self, date: str) -> Dict[str, Any]:
        """签订合同"""
        self.layer['l3_dynamic_state']['状态'] = '已签'
        self.layer['l3_dynamic_state']['签订日期'] = date
        self.add_event('签订合同', date)
        return {'success': True, 'date': date}

    def get_status(self) -> str:
        """获取合同状态"""
        return self.layer['l3_dynamic_state'].get('状态', '草签')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '合同',
            'contract_type': self.contract_type,
            'party_a': self.party_a,
            'party_b': self.party_b,
            'amount': self.amount,
            'status': self.get_status(),
            'layer': self.layer,
        }