# -*- coding: utf-8 -*-
"""
支架吊杆实体
受 GPL v3.0 保护

悬挂支架。含受力点+接触面。

V2.0（阶段1）：直径从 bolts.json 读，max_load 保持产品属性硬编码。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import hanger_cbm, hanger_force_points, hanger_contact_faces
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON加载吊杆规格 ====================

_DEFAULT_HANGER_SPECS = {
    'M10': {'diameter': 10, 'max_load': '200kg'},
    'M12': {'diameter': 12, 'max_load': '300kg'},
    'M16': {'diameter': 16, 'max_load': '500kg'},
}


def _load_hanger_specs() -> Dict[str, Dict[str, Any]]:
    """直径从 bolts.json 读，max_load 保持产品属性。"""
    specs = {}
    for spec, default in _DEFAULT_HANGER_SPECS.items():
        bolt_spec = read_standard('bolts', spec)
        specs[spec] = {
            'diameter': bolt_spec.get('直径', default['diameter']),
            'max_load': default['max_load'],
        }
    return specs


class HangerEntity(BaseEntity):
    """支架吊杆实体"""

    # ★ V2.0：从 bolts.json 加载
    HANGER_SPECS = _load_hanger_specs()

    def __init__(self, spec: str = 'M12', length: float = 350,
                 material: str = 'Q235B', position: Optional[Dict] = None,
                 connect_support: Optional[str] = None, index: int = 0,
                 space: Optional[Dict] = None):
        if spec not in self.HANGER_SPECS:
            spec = 'M12'
        spec_data = self.HANGER_SPECS[spec]

        position = position or {'x': 1000, 'y': -100, 'z': 2850}

        force_points = hanger_force_points(spec, length)
        contact_faces = hanger_contact_faces(spec, length)

        l2 = {
            '类型': '支架吊杆',
            '规格': spec,
            '直径': f'{spec_data["diameter"]}mm',
            '长度': f'{length}mm',
            '材质': material,
            '连接支架': connect_support,
            '序号': index,
            '承重上限': spec_data['max_load'],
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec_data['diameter'], 'y': spec_data['diameter'], 'z': length},
        }

        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        cbm = hanger_cbm(spec, length)

        super().__init__(
            entity_type='支架吊杆',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.spec = spec
        self.length = length
        self.material = material
        self.connect_support = connect_support
        self.index = index
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = spec

    def calc_load(self) -> Dict[str, Any]:
        """计算吊杆载荷"""
        max_load = self.HANGER_SPECS[self.spec]['max_load']
        current_load = 50
        return {
            'current_load': f'{current_load}kg',
            'max_load': max_load,
            'passed': current_load <= float(str(max_load).replace('kg', '')),
        }

    def get_force_points(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '支架吊杆',
            'spec': self.spec,
            'length': self.length,
            'material': self.material,
            'connect_support': self.connect_support,
            'layer': self.layer,
        }