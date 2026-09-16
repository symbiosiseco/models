# -*- coding: utf-8 -*-
"""
风管实体
受 GPL v3.0 保护

镀锌钢板风管。含受力点+接触面。
风管优先级2，与其他管道间距≥150mm。

V2.0（阶段1）：DUCT_SPECS 从 ducts.json 读，消除硬编码。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import duct_cbm, duct_force_points, duct_contact_faces
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON加载风管规格 ====================

_DEFAULT_DUCT_SPECS = {
    '800×400': {'width': 800, 'height': 400, 'weight_per_m': 18.5, 'thickness': 1.0},
    '400×200': {'width': 400, 'height': 200, 'weight_per_m': 15,   'thickness': 0.8},
    '500×250': {'width': 500, 'height': 250, 'weight_per_m': 20,   'thickness': 1.0},
    '320×160': {'width': 320, 'height': 160, 'weight_per_m': 12,   'thickness': 0.8},
}


def _load_duct_specs() -> Dict[str, Dict[str, float]]:
    """从 ducts.json 加载风管规格。JSON没有的用默认值。"""
    specs = {}
    for spec, default in _DEFAULT_DUCT_SPECS.items():
        s = read_standard('ducts', spec)
        specs[spec] = {
            'width': s.get('宽度', default['width']),
            'height': s.get('高度', default['height']),
            'weight_per_m': s.get('单位重量', default['weight_per_m']),
            'thickness': s.get('壁厚', default['thickness']),
        }
    return specs


class DuctEntity(BaseEntity):
    """风管实体"""

    # ★ V2.0：从 ducts.json 加载
    DUCT_SPECS = _load_duct_specs()

    MIN_CLEARANCE = 150

    def __init__(self, spec: str = '800×400', material: str = '镀锌钢板',
                 thickness: Optional[float] = None, start: Optional[Dict] = None,
                 end: Optional[Dict] = None, manufacturer: str = '风管厂',
                 system: str = '通风系统', space: Optional[Dict] = None):
        if spec not in self.DUCT_SPECS:
            spec = '800×400'
        spec_data = self.DUCT_SPECS[spec]

        if thickness is None:
            thickness = spec_data.get('thickness', 1.0)

        start = start or {'x': 0, 'y': -600, 'z': 2800}
        end = end or {'x': 10000, 'y': -600, 'z': 2800}

        length = abs(end['x'] - start['x']) or 10000
        center = {
            'x': (start['x'] + end['x']) / 2,
            'y': (start['y'] + end['y']) / 2,
            'z': (start['z'] + end['z']) / 2,
        }

        total_weight = round(spec_data['weight_per_m'] * length / 1000, 2)

        force_points = duct_force_points(spec, thickness)
        contact_faces = duct_contact_faces(spec, thickness)

        l2 = {
            '规格': spec,
            '宽度': f'{spec_data["width"]}mm',
            '高度': f'{spec_data["height"]}mm',
            '材质': material,
            '壁厚': f'{thickness}mm',
            '连接方式': '法兰连接',
            '单位重量': f'{spec_data["weight_per_m"]}kg/m',
            '总重量': f'{total_weight}kg',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': spec_data['width'], 'z': spec_data['height']},
        }

        l3 = {
            '起点坐标': start,
            '终点坐标': end,
            '中心坐标': center,
            '长度': length,
            '受力点实时坐标': [],
        }

        cbm = duct_cbm(spec, thickness)

        super().__init__(
            entity_type='风管',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=center,
        )

        self.spec = spec
        self.length = length
        self.start = start
        self.end = end
        self.system = system
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = spec
        self.layer['r_layer']['系统'] = system

    def calc_weight(self) -> float:
        return float(str(self.layer['l2_static_attributes']['总重量']).replace('kg', ''))

    def check_clearance(self, entities: List[Any]) -> Dict[str, Any]:
        """检查与其他管道的间距"""
        violations = []
        my_pos = self.get_position()

        for e in entities:
            if e is self:
                continue
            e_type = getattr(e, 'entity_type', '')
            if e_type not in ('管道', '桥架', '阀门', '卡箍'):
                continue

            e_pos = e.layer.get('l3_dynamic_state', {}).get('绝对坐标', {})
            dy = abs(my_pos['y'] - e_pos.get('y', 0))
            dz = abs(my_pos['z'] - e_pos.get('z', 0))

            min_dist = min(dy, dz)
            if min_dist < self.MIN_CLEARANCE:
                violations.append({
                    'entity_id': getattr(e, 'id', None),
                    'entity_type': e_type,
                    'distance': min_dist,
                    'required': self.MIN_CLEARANCE,
                })

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'message': f'间距检查完成，{"通过" if not violations else f"发现{len(violations)}个违规"}',
        }

    def get_force_points(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '风管',
            'spec': self.spec,
            'length': self.length,
            'start': self.start,
            'end': self.end,
            'layer': self.layer,
        }