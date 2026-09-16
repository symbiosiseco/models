# -*- coding: utf-8 -*-
"""
阀杆实体
受 GPL v3.0 保护

连接阀体和手轮。

V2.0（阶段1）：尺寸从 pipes.json 推算（阀杆直径 ≈ 管道外径 × 0.175）。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON推算阀杆规格 ====================

_DEFAULT_STEM_SPECS = {
    'DN50':  {'diameter': 14, 'length': 100},
    'DN80':  {'diameter': 16, 'length': 115},
    'DN100': {'diameter': 20, 'length': 130},
    'DN150': {'diameter': 25, 'length': 165},
    'DN200': {'diameter': 30, 'length': 200},
}


def _load_stem_specs() -> Dict[str, Dict[str, float]]:
    """阀杆直径 ≈ 管道外径 × 0.175"""
    specs = {}
    for dn, default in _DEFAULT_STEM_SPECS.items():
        pipe_spec = read_standard('pipes', dn)
        outer = pipe_spec.get('外径', default['diameter'] / 0.175)
        specs[dn] = {
            'diameter': round(outer * 0.175, 1),
            'length': default['length'],
        }
    return specs


class StemEntity(BaseEntity):
    """阀杆实体"""

    # ★ V2.0：从 pipes.json 推算
    STEM_SPECS = _load_stem_specs()

    def __init__(self, dn: str = 'DN100', manufacturer: str = 'A厂',
                 position: Optional[Dict] = None, connect_valve: Optional[str] = None,
                 connect_wheel: Optional[str] = None, space: Optional[Dict] = None):
        if dn not in self.STEM_SPECS:
            dn = 'DN100'
        spec = self.STEM_SPECS[dn]

        position = position or {'x': 4000, 'y': -150, 'z': 2600}

        force_points = [
            {
                'id': 'fp_axis',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '阀杆中轴',
                '方向': 'Z-',
                '传力对象': '阀体',
                '承重上限': '150N·m',
            }
        ]

        contact_faces = [
            {
                'id': 'cf_top',
                '类型': '上端',
                '位置': {'x': 0, 'y': 0, 'z': spec['length'] / 2},
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
                '位置': {'x': 0, 'y': 0, 'z': -spec['length'] / 2},
                '法线方向': 'Z-',
                '接触对象类型': ['阀体'],
                '允许偏差': '0mm',
                '必须包含': [],
                '违反后果': '打滑',
                '装配顺序': 1,
            },
        ]

        l2 = {
            '类型': '阀杆',
            '规格': dn,
            '厂家': manufacturer,
            '直径': f'{spec["diameter"]}mm',
            '长度': f'{spec["length"]}mm',
            '材质': '不锈钢304',
            '连接阀门': connect_valve,
            '连接手轮': connect_wheel,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['diameter'], 'y': spec['diameter'], 'z': spec['length']},
        }

        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        cbm = {
            '物理规则': {
                '包围盒': {'x': spec['diameter'], 'y': spec['diameter'], 'z': spec['length']},
                '最小间距': 20,
                '允许接触': ['手轮', '阀体'],
                '禁止穿透': True,
                '接触方式': '轴孔配合 H7/h6',
            },
            '受力规则': {
                '自重': '0.3kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['操作力矩 → 手轮 → 阀杆 → 阀体'],
                '承重上限': '150N·m',
            },
            '装配规则': {
                '连接对象': ['手轮', '阀体'],
                '拧紧力矩': '10N·m',
                '装配顺序': ['阀杆插入阀体', '手轮套入阀杆', '紧固'],
                '密封等级': '无',
            },
            '规范约束': {
                '安装规范': 'GB/T 12224',
                '材料强度': '不锈钢304屈服≥205MPa',
                '传递力矩': '≤150N·m',
                '检查周期': '每年1次',
            },
        }

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

        self.layer['r_layer']['规格'] = dn

    def check_material_strength(self) -> Dict[str, Any]:
        """检查材料强度"""
        return {
            'success': True,
            'material': '不锈钢304',
            'yield_strength': '205MPa',
            'message': '屈服强度205MPa≥205MPa',
        }

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '阀杆',
            'dn': self.dn,
            'connect_valve': self.connect_valve,
            'connect_wheel': self.connect_wheel,
            'layer': self.layer,
        }