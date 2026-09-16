# -*- coding: utf-8 -*-
"""
工序实体
受 GPL v3.0 保护

定义施工工序。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import process_cbm
from config import config


class ProcessEntity(BaseEntity):
    """工序实体"""

    # 工序类型（含标准时长，单位：分钟）
    PROCESS_TYPES = {
        '打码': {'duration': 30,  'required_worker': '管道工', 'required_equipment': '打码机'},
        '预制': {'duration': 120, 'required_worker': '焊工',   'required_equipment': '电焊机'},
        '安装': {'duration': 240, 'required_worker': '管道工', 'required_equipment': '电锤'},
        '试压': {'duration': 60,  'required_worker': '质检员', 'required_equipment': '试压泵'},
    }

    def __init__(self, process_name: str = '', process_type: str = '打码',
                 duration: int = 0, required_worker: Optional[str] = None,
                 required_equipment: Optional[str] = None,
                 quality_standard: str = '', space: Optional[Dict] = None):
        if process_type not in self.PROCESS_TYPES:
            process_type = '打码'
        spec = self.PROCESS_TYPES[process_type]
        duration = duration or spec['duration']
        required_worker = required_worker or spec['required_worker']
        required_equipment = required_equipment or spec['required_equipment']

        # L2层
        l2 = {
            '工序名': process_name,
            '工序类型': process_type,
            '标准时长': duration,
            '需要工种': required_worker,
            '需要设备': required_equipment,
            '质量标准': quality_standard,
        }

        # L3层
        l3 = {
            '状态': '待执行',
        }

        # CBM层
        cbm = process_cbm(process_name, process_type)

        super().__init__(
            entity_type='工序',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.process_name = process_name
        self.process_type = process_type
        self.duration = duration
        self.required_worker = required_worker
        self.required_equipment = required_equipment
        self.quality_standard = quality_standard
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['工序类型'] = process_type

    def check_duration(self, actual_duration: int) -> bool:
        """检查实际时长是否超标"""
        return actual_duration <= self.duration

    def get_quality_standard(self) -> str:
        """获取质量标准"""
        return self.layer['l2_static_attributes'].get('质量标准', '')

    def get_status(self) -> str:
        """获取状态"""
        return self.layer['l3_dynamic_state'].get('状态', '待执行')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '工序',
            'process_name': self.process_name,
            'process_type': self.process_type,
            'duration': self.duration,
            'layer': self.layer,
        }