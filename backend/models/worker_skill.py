# -*- coding: utf-8 -*-
"""
工人技能实体
受 GPL v3.0 保护

定义工人技能等级和证书。
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .entity import BaseEntity
from config import config


class WorkerSkillEntity(BaseEntity):
    """工人技能实体"""

    # 等级范围
    MIN_LEVEL = 1
    MAX_LEVEL = 5

    def __init__(self, skill_name: str = '', level: int = 1,
                 cert_number: str = '', expire_date: str = '',
                 worker_id: Optional[str] = None,
                 space: Optional[Dict] = None):
        if level < self.MIN_LEVEL:
            level = self.MIN_LEVEL
        if level > self.MAX_LEVEL:
            level = self.MAX_LEVEL

        # L2层
        l2 = {
            '技能名': skill_name,
            '等级': level,
            '证书编号': cert_number,
            '有效期': expire_date,
            '关联工人': worker_id,
        }

        # L3层
        l3 = {
            '状态': '有效',
        }

        # CBM层（引用physics_rules）
        from .physics_rules import worker_skill_cbm
        cbm = worker_skill_cbm(skill_name, level)

        super().__init__(
            entity_type='工人技能',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.skill_name = skill_name
        self.level = level
        self.cert_number = cert_number
        self.expire_date = expire_date
        self.worker_id = worker_id
        self.space = space or config.SPACE_UNITS

    def check_level(self, required_level: int) -> bool:
        """检查技能等级是否满足"""
        return self.level >= required_level

    def check_certificate(self) -> bool:
        """检查证书是否有效"""
        if not self.cert_number:
            return False
        return not self.is_expired()

    def is_expired(self) -> bool:
        """检查证书是否过期"""
        if not self.expire_date:
            return False
        try:
            exp = datetime.strptime(self.expire_date, '%Y-%m-%d')
            return datetime.now() > exp
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '工人技能',
            'skill_name': self.skill_name,
            'level': self.level,
            'cert_number': self.cert_number,
            'expire_date': self.expire_date,
            'worker_id': self.worker_id,
            'layer': self.layer,
        }