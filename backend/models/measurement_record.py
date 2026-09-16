# -*- coding: utf-8 -*-
"""
实测记录实体
受 GPL v3.0 保护

定义单条实测记录。含与设计值对比。
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .entity import BaseEntity
from .physics_rules import measurement_record_cbm
from config import config


class MeasurementRecordEntity(BaseEntity):
    """实测记录实体"""

    # 记录类型
    RECORD_TYPES = ['支架高度', '楼板高度', '管道位置']

    # 阈值（mm）
    THRESHOLD = 5.0

    def __init__(self, record_type: str = '支架高度',
                 target_id: Optional[str] = None,
                 value: float = 0,
                 recorded_by: str = '',
                 recorded_time: str = '',
                 space: Optional[Dict] = None):
        if record_type not in self.RECORD_TYPES:
            record_type = '支架高度'
        recorded_time = recorded_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # L2层
        l2 = {
            '记录类型': record_type,
            '关联构件': target_id,
            '记录值': value,
            '记录人': recorded_by,
            '记录时间': recorded_time,
        }

        # L3层
        l3 = {
            '状态': '已记录',
        }

        # CBM层
        cbm = measurement_record_cbm(record_type)

        super().__init__(
            entity_type='实测记录',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.record_type = record_type
        self.target_id = target_id
        self.value = value
        self.recorded_by = recorded_by
        self.recorded_time = recorded_time
        self.space = space or config.SPACE_UNITS

    def get_value(self) -> float:
        """获取记录值"""
        return self.value

    def compare_design(self, design_value: float) -> Dict[str, Any]:
        """与设计值对比"""
        deviation = round(self.value - design_value, 2)
        qualified = abs(deviation) <= self.THRESHOLD
        return {
            'deviation': deviation,
            'qualified': qualified,
            'design_value': design_value,
            'actual_value': self.value,
        }

    def check_qualified(self, design_value: float = 0) -> bool:
        """检查是否合格"""
        return self.compare_design(design_value).get('qualified', False)

    def get_record(self) -> Dict[str, Any]:
        """获取记录"""
        return {
            'id': self.id,
            'record_type': self.record_type,
            'target_id': self.target_id,
            'value': self.value,
            'recorded_by': self.recorded_by,
            'recorded_time': self.recorded_time,
        }

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '实测记录',
            'record_type': self.record_type,
            'target_id': self.target_id,
            'value': self.value,
            'layer': self.layer,
        }