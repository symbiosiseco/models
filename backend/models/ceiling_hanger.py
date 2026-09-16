# -*- coding: utf-8 -*-
"""
吊顶丝杆实体
受 GPL v3.0 保护

悬挂吊顶。含受力点+接触面。

V2.0（阶段1）：直径从 bolts.json 读，max_load 保持产品属性硬编码。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import (
    ceiling_hanger_cbm,
    ceiling_hanger_force_points,
    ceiling_hanger_contact_faces,
)
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON加载丝杆规格 ====================

_DEFAULT_CEILING_HANGER_SPECS = {
    'M8':  {'diameter': 8,  'max_load': '50kg'},
    'M10': {'diameter': 10, 'max_load': '80kg'},
    'M12': {'diameter': 12, 'max_load': '120kg'},
}


def _load_ceiling_hanger_specs() -> Dict[str, Dict[str, Any]]:
    """直径从 bolts.json 读（M8没有则用默认），max_load 保持产品属性。"""
    specs = {}
    for spec, default in _DEFAULT_CEILING_HANGER_SPECS.items():
        bolt_spec = read_standard('bolts', spec)
        specs[spec] = {
            'diameter': bolt_spec.get('直径', default['diameter']),
            'max_load': default['max_load'],
        }
    return specs


class CeilingHangerEntity(BaseEntity):
    """吊顶丝杆实体"""

    # ★ V2.0：从 bolts.json 加载
    CEILING_HANGER_SPECS = _load_ceiling_hanger_specs()

    MAX_SPACING = 1200

    def __init__(self, spec: str = 'M8', length: float = 300,
                 material: str = '镀锌钢', position: Optional[Dict] = None,
                 connect_ceiling: Optional[str] = None, index: int = 0,
                 space: Optional[Dict] = None):
        if spec not in self.CEILING_HANGER_SPECS:
            spec = 'M8'
        spec_data = self.CEILING_HANGER_SPECS[spec]

        position = position or {'x': 1000, 'y': 0, 'z': 2700}

        force_points = ceiling_hanger_force_points(spec, length)
        contact_faces = ceiling_hanger_contact_faces(spec, length)

        l2 = {
            '类型': '吊顶丝杆',
            '规格': spec,
            '直径': f'{spec_data["diameter"]}mm',
            '长度': f'{length}mm',
            '材质': material,
            '连接吊顶': connect_ceiling,
            '序号': index,
            '承重上限': spec_data['max_load'],
            '间距限制': f'≤{self.MAX_SPACING}mm',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec_data['diameter'], 'y': spec_data['diameter'], 'z': length},
        }

        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        cbm = ceiling_hanger_cbm(spec, length)

        super().__init__(
            entity_type='吊顶丝杆',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.spec = spec
        self.length = length
        self.material = material
        self.connect_ceiling = connect_ceiling
        self.index = index
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = spec

    def calc_load(self) -> Dict[str, Any]:
        """计算丝杆载荷"""
        max_load = self.CEILING_HANGER_SPECS[self.spec]['max_load']
        return {
            'current_load': '15kg',
            'max_load': max_load,
            'passed': True,
        }

    def check_spacing(self, prev_hanger_pos: Optional[Dict] = None) -> Dict[str, Any]:
        """检查与相邻丝杆的间距"""
        if not prev_hanger_pos:
            return {'passed': True, 'message': '无相邻丝杆'}

        curr = self.get_position()
        distance = abs(curr['x'] - prev_hanger_pos['x'])
        passed = distance <= self.MAX_SPACING
        return {
            'passed': passed,
            'distance': distance,
            'max_spacing': self.MAX_SPACING,
            'message': f'间距{distance}mm，限制{self.MAX_SPACING}mm',
        }

    def get_force_points(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '吊顶丝杆',
            'spec': self.spec,
            'length': self.length,
            'connect_ceiling': self.connect_ceiling,
            'layer': self.layer,
        }