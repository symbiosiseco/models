# -*- coding: utf-8 -*-
"""
手轮实体
受 GPL v3.0 保护

阀门顶部的手轮。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import wheel_cbm
from config import config


class WheelEntity(BaseEntity):
    """手轮实体"""

    # 手轮规格
    WHEEL_SPECS = {
        'DN50':  {'outer': 120, 'weight': 0.8},
        'DN80':  {'outer': 160, 'weight': 1.2},
        'DN100': {'outer': 200, 'weight': 1.8},
        'DN150': {'outer': 240, 'weight': 2.5},
        'DN200': {'outer': 280, 'weight': 3.2},
    }

    def __init__(self, dn: str = 'DN100', manufacturer: str = 'A厂',
                 position: Optional[Dict] = None,
                 connect_valve: Optional[str] = None,
                 space: Optional[Dict] = None):
        if dn not in self.WHEEL_SPECS:
            dn = 'DN100'
        spec = self.WHEEL_SPECS[dn]

        position = position or {'x': 4000, 'y': -150, 'z': 2800}

        # L2层
        l2 = {
            '类型': '手轮',
            '规格': dn,
            '厂家': manufacturer,
            '外径': f'{spec["outer"]}mm',
            '重量': f'{spec["weight"]}kg',
            '材质': '铸铁',
            '辐条数量': 4,
            '连接阀门': connect_valve,
            '包围盒': {'x': 20, 'y': spec['outer'], 'z': spec['outer']},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
        }

        # CBM层
        cbm = wheel_cbm(dn, spec['outer'])

        super().__init__(
            entity_type='手轮',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.connect_valve = connect_valve
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = dn

    def calc_operation_torque(self) -> Dict[str, Any]:
        """计算操作力矩"""
        return {
            'operation_torque': '≤150N·m',
            'max_torque': 150,
            'message': '操作力矩≤150N·m',
        }

    def get_force_points(self):
        """获取受力点（可选）"""
        return [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '手轮中心',
                '方向': 'Z-',
                '传力对象': '阀杆',
                '承重上限': '150N·m',
            }
        ]

    def get_contact_faces(self):
        """获取接触面（可选）"""
        return [
            {
                'id': 'cf_hub',
                '类型': '轮毂',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '法线方向': 'Z-',
                '接触对象类型': ['阀杆'],
                '允许偏差': '0mm',
                '必须包含': [],
                '违反后果': '打滑',
                '装配顺序': 1,
            }
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '手轮',
            'dn': self.dn,
            'connect_valve': self.connect_valve,
            'layer': self.layer,
        }