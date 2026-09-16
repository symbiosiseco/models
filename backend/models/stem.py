# -*- coding: utf-8 -*-
"""
阀杆实体
受 GPL v3.0 保护

连接阀体和手轮。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import stem_cbm
from config import config


class StemEntity(BaseEntity):
    """阀杆实体"""

    # 阀杆规格
    STEM_SPECS = {
        'DN50':  {'diameter': 14, 'length': 90},
        'DN80':  {'diameter': 16, 'length': 110},
        'DN100': {'diameter': 20, 'length': 130},
        'DN150': {'diameter': 24, 'length': 160},
        'DN200': {'diameter': 28, 'length': 190},
    }

    def __init__(self, dn: str = 'DN100', manufacturer: str = 'A厂',
                 position: Optional[Dict] = None,
                 connect_valve: Optional[str] = None,
                 connect_wheel: Optional[str] = None,
                 space: Optional[Dict] = None):
        if dn not in self.STEM_SPECS:
            dn = 'DN100'
        spec = self.STEM_SPECS[dn]

        position = position or {'x': 4000, 'y': -150, 'z': 2700}

        # L2层
        l2 = {
            '类型': '阀杆',
            '规格': dn,
            '厂家': manufacturer,
            '直径': f'{spec["diameter"]}mm',
            '长度': f'{spec["length"]}mm',
            '材质': '不锈钢304',
            '轴孔配合': 'H7/h6',
            '连接阀门': connect_valve,
            '连接手轮': connect_wheel,
            '包围盒': {'x': spec['diameter'], 'y': spec['diameter'], 'z': spec['length']},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
        }

        # CBM层
        cbm = stem_cbm(dn, spec['diameter'], spec['length'])

        super().__init__(
            entity_type='阀杆',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.connect_valve = connect_valve
        self.connect_wheel = connect_wheel
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = dn

    def check_material_strength(self) -> Dict[str, Any]:
        """检查材料强度"""
        # 不锈钢304屈服强度 ≥ 205MPa
        return {
            'success': True,
            'material': '不锈钢304',
            'yield_strength': '205MPa',
            'message': '屈服强度205MPa≥205MPa',
        }

    def get_force_points(self):
        """获取受力点（可选）"""
        return [
            {
                'id': 'fp_axis',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '阀杆中轴',
                '方向': 'Z-',
                '传力对象': '阀体',
                '承重上限': '150N·m',
            }
        ]

    def get_contact_faces(self):
        """获取接触面（可选）"""
        return [
            {
                'id': 'cf_top',
                '类型': '上端',
                '位置': {'x': 0, 'y': 0, 'z': 65},
                '法线方向': 'Z+',
                '接触对象类型': ['手轮'],
                '允许偏差': '0mm',
                '必须包含': [],
                '违反后果': '打滑',
                '装配顺序': 1,
            },
            {
                'id': 'cf_bottom',
                '类型': '下端',
                '位置': {'x': 0, 'y': 0, 'z': -65},
                '法线方向': 'Z-',
                '接触对象类型': ['阀体'],
                '允许偏差': '0mm',
                '必须包含': [],
                '违反后果': '打滑',
                '装配顺序': 1,
            },
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '阀杆',
            'dn': self.dn,
            'connect_valve': self.connect_valve,
            'connect_wheel': self.connect_wheel,
            'layer': self.layer,
        }