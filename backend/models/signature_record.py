# -*- coding: utf-8 -*-
"""
签字记录实体
受 GPL v3.0 保护

定义审批签字流程中的单条记录。含流程步骤。
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .entity import BaseEntity
from .physics_rules import signature_record_cbm
from config import config


class SignatureRecordEntity(BaseEntity):
    """签字记录实体"""

    # 签字类型
    SIGNATURE_TYPES = ['进度款', '变更', '验收']

    # 状态
    STATUSES = ['待签', '已签', '退回']

    def __init__(self, signature_type: str = '进度款',
                 signer: str = '', role: str = '',
                 sign_time: str = '', comment: str = '',
                 step: int = 0,
                 space: Optional[Dict] = None):
        if signature_type not in self.SIGNATURE_TYPES:
            signature_type = '进度款'
        sign_time = sign_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # L2层
        l2 = {
            '签字类型': signature_type,
            '签字人': signer,
            '角色': role,
            '签字时间': sign_time,
            '意见': comment,
            '步骤': step,
        }

        # L3层
        l3 = {
            '状态': '待签',
        }

        # CBM层
        cbm = signature_record_cbm(signature_type)

        super().__init__(
            entity_type='签字记录',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.signature_type = signature_type
        self.signer = signer
        self.role = role
        self.sign_time = sign_time
        self.comment = comment
        self.step = step
        self.space = space or config.SPACE_UNITS

    def sign(self, comment: str = '') -> Dict[str, Any]:
        """签字"""
        self.layer['l3_dynamic_state']['状态'] = '已签'
        self.layer['l2_static_attributes']['意见'] = comment
        self.layer['l2_static_attributes']['签字时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.add_event('签字', f'{self.signer}（{self.role}）：{comment}')
        return {'success': True, 'signature_id': self.id, 'status': '已签'}

    def reject(self, reason: str = '') -> Dict[str, Any]:
        """拒绝签字"""
        self.layer['l3_dynamic_state']['状态'] = '退回'
        self.layer['l2_static_attributes']['意见'] = reason
        self.add_event('驳回', f'{self.signer}（{self.role}）：{reason}')
        return {'success': True, 'signature_id': self.id, 'status': '退回', 'reason': reason}

    def get_status(self) -> str:
        """获取签字状态"""
        return self.layer['l3_dynamic_state'].get('状态', '待签')

    def get_history(self) -> list:
        """获取签字历史"""
        return self.layer['l4_event_chain']

    def get_step_info(self) -> Dict[str, Any]:
        """获取步骤信息"""
        return {
            'step': self.step,
            'role': self.role,
            'signer': self.signer,
            'status': self.get_status(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '签字记录',
            'signature_type': self.signature_type,
            'signer': self.signer,
            'role': self.role,
            'step': self.step,
            'status': self.get_status(),
            'layer': self.layer,
        }