# -*- coding: utf-8 -*-
"""
实测实量实体
受 GPL v3.0 保护

定义现场测量记录。写L4影响CBM。
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .entity import BaseEntity
from .physics_rules import measurement_cbm
from config import config


class MeasurementEntity(BaseEntity):
    """实测实量实体"""

    # 测量类型
    MEASURE_TYPES = ['楼板高度', '支架高度', '管道坡度', '垂直度']

    # 阈值（mm）
    THRESHOLD = 5.0

    def __init__(self, measure_type: str = '楼板高度', location: str = '',
                 design_value: float = 0, actual_value: float = 0,
                 measured_by: str = '', measured_time: str = '',
                 space: Optional[Dict] = None):
        if measure_type not in self.MEASURE_TYPES:
            measure_type = '楼板高度'
        measured_time = measured_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 计算偏差
        deviation = round(actual_value - design_value, 2)

        # L2层
        l2 = {
            '测量类型': measure_type,
            '测量位置': location,
            '设计值': design_value,
            '实际值': actual_value,
            '偏差': deviation,
            '测量人': measured_by,
            '测量时间': measured_time,
        }

        # L3层
        l3 = {
            '状态': '已测量',
            '合格': abs(deviation) <= self.THRESHOLD,
        }

        # CBM层
        cbm = measurement_cbm(measure_type)

        super().__init__(
            entity_type='实测实量',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.measure_type = measure_type
        self.location = location
        self.design_value = design_value
        self.actual_value = actual_value
        self.deviation = deviation
        self.measured_by = measured_by
        self.space = space or config.SPACE_UNITS

    def calc_deviation(self) -> float:
        """计算偏差"""
        return self.deviation

    def check_threshold(self) -> bool:
        """检查是否超阈值"""
        return abs(self.deviation) <= self.THRESHOLD

    def get_deviation(self) -> float:
        """获取偏差"""
        return self.deviation

    def adjust_support(self, support_id: str) -> Dict[str, Any]:
        """根据偏差调节支架"""
        return {
            'success': True,
            'support_id': support_id,
            'adjust_value': -self.deviation,
            'message': f'支架调节 {-self.deviation:+}mm',
        }

    def write_to_l4(self) -> Dict[str, Any]:
        """写L4影响CBM"""
        self.add_event(
            '实测记录',
            f'{self.measure_type} 偏差{self.deviation:+}mm'
        )
        return {'success': True, 'message': '已写入L4'}

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '实测实量',
            'measure_type': self.measure_type,
            'design_value': self.design_value,
            'actual_value': self.actual_value,
            'deviation': self.deviation,
            'qualified': self.check_threshold(),
            'layer': self.layer,
        }