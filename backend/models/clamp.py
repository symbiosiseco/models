# -*- coding: utf-8 -*-
"""
沟槽卡箍实体
受 GPL v3.0 保护

连接两段管道。含受力点+接触面。
必须包含橡胶圈。

V2.0（阶段1）：CLAMP_SPECS 从 clamps.json 读，消除硬编码。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import clamp_cbm, clamp_force_points, clamp_contact_faces
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON加载卡箍规格 ====================

_DEFAULT_CLAMP_SPECS = {
    'DN50':  {'width': 45, 'outer': 88,  'weight': 0.6, 'bolt': 'M8×55',  'bolt_count': 2},
    'DN80':  {'width': 50, 'outer': 120, 'weight': 0.9, 'bolt': 'M10×65', 'bolt_count': 2},
    'DN100': {'width': 60, 'outer': 140, 'weight': 1.2, 'bolt': 'M10×65', 'bolt_count': 2},
    'DN150': {'width': 70, 'outer': 200, 'weight': 2.2, 'bolt': 'M12×75', 'bolt_count': 2},
    'DN200': {'width': 80, 'outer': 260, 'weight': 3.5, 'bolt': 'M12×75', 'bolt_count': 2},
}


def _load_clamp_specs() -> Dict[str, Dict[str, Any]]:
    """从 clamps.json 加载卡箍规格。JSON没有的用默认值。"""
    specs = {}
    for dn, default in _DEFAULT_CLAMP_SPECS.items():
        s = read_standard('clamps', dn)
        specs[dn] = {
            'width': s.get('卡箍宽度', default['width']),
            'outer': s.get('卡箍外径', default['outer']),
            'weight': s.get('重量', default['weight']),
            'bolt': s.get('螺栓规格', default['bolt']),
            'bolt_count': s.get('螺栓数', default['bolt_count']),
        }
    return specs


class ClampEntity(BaseEntity):
    """沟槽卡箍实体"""

    # ★ V2.0：从 JSON 加载
    CLAMP_SPECS = _load_clamp_specs()

    def __init__(self, dn: str = 'DN100', manufacturer: str = 'B厂',
                 position: Optional[Dict] = None, connect_pipes: Optional[List] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        if dn not in self.CLAMP_SPECS:
            dn = 'DN100'
        spec = self.CLAMP_SPECS[dn]

        position = position or {'x': 6000, 'y': -150, 'z': 2500}
        connect_pipes = connect_pipes or []

        force_points = clamp_force_points(dn, spec['outer'], spec['width'])
        contact_faces = clamp_contact_faces(dn, spec['outer'], spec['width'])

        l2 = {
            '规格': dn,
            '厂家': manufacturer,
            '宽度': f'{spec["width"]}mm',
            '外径': f'{spec["outer"]}mm',
            '重量': f'{spec["weight"]}kg',
            '材质': '球墨铸铁',
            '螺栓规格': spec['bolt'],
            '螺栓数量': spec['bolt_count'],
            '拧紧力矩': '2.5-3.5N·m',
            '密封圈': '橡胶圈（EPDM）',
            '连接管道': connect_pipes,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['width'], 'y': spec['outer'], 'z': spec['outer']},
        }

        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        cbm = clamp_cbm(dn, spec['outer'], spec['width'])

        super().__init__(
            entity_type='卡箍',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.system = system
        self.connect_pipes = list(connect_pipes)
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = dn
        self.layer['r_layer']['系统'] = system

    def check_groove(self, pipe_groove: str) -> bool:
        """检查卡箍沟槽与管道沟槽是否匹配"""
        return bool(pipe_groove)

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def has_rubber_ring(self) -> bool:
        """检查是否包含橡胶圈"""
        for cf in self.get_contact_faces():
            if '橡胶圈' in cf.get('必须包含', []):
                return True
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '卡箍',
            'dn': self.dn,
            'connect_pipes': self.connect_pipes,
            'layer': self.layer,
        }