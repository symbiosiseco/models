# -*- coding: utf-8 -*-
"""
阀门实体
受 GPL v3.0 保护

仅阀体。手轮/阀杆/法兰/垫片/螺栓为独立实体。
含受力点+接触面。

V2.0（阶段1）：VALVE_SPECS 从 valves.json 读，消除硬编码。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import valve_cbm, valve_force_points, valve_contact_faces
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON加载阀门规格 ====================

_DEFAULT_VALVE_SPECS = {
    '闸阀': {
        'DN50':  {'outer': 165, 'length': 200, 'weight': 10},
        'DN80':  {'outer': 200, 'length': 240, 'weight': 12},
        'DN100': {'outer': 220, 'length': 280, 'weight': 15},
        'DN150': {'outer': 285, 'length': 360, 'weight': 25},
        'DN200': {'outer': 340, 'length': 420, 'weight': 38},
    },
    '蝶阀': {
        'DN50':  {'outer': 165, 'length': 43,  'weight': 5},
        'DN80':  {'outer': 200, 'length': 46,  'weight': 6},
        'DN100': {'outer': 230, 'length': 52,  'weight': 8},
        'DN150': {'outer': 285, 'length': 60,  'weight': 12},
        'DN200': {'outer': 340, 'length': 70,  'weight': 18},
    },
    '止回阀': {
        'DN50':  {'outer': 165, 'length': 200, 'weight': 9},
        'DN80':  {'outer': 200, 'length': 240, 'weight': 11},
        'DN100': {'outer': 220, 'length': 280, 'weight': 14},
        'DN150': {'outer': 285, 'length': 360, 'weight': 23},
        'DN200': {'outer': 340, 'length': 420, 'weight': 35},
    },
}


def _load_valve_specs() -> Dict[str, Dict[str, Dict[str, float]]]:
    """从 valves.json 加载阀门规格（双层：类型→DN→参数）。"""
    specs = {}
    for valve_type, dn_map in _DEFAULT_VALVE_SPECS.items():
        specs[valve_type] = {}
        for dn, default in dn_map.items():
            s = read_standard('valves', dn, valve_type)
            specs[valve_type][dn] = {
                'outer': s.get('外径', default['outer']),
                'length': s.get('长度', default['length']),
                'weight': s.get('重量', default['weight']),
            }
    return specs


class ValveEntity(BaseEntity):
    """阀门实体（仅阀体）"""

    # ★ V2.0：从 JSON 加载
    VALVE_SPECS = _load_valve_specs()

    def __init__(self, valve_type: str = '闸阀', dn: str = 'DN100',
                 manufacturer: str = 'A厂', position: Optional[Dict] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        if valve_type not in self.VALVE_SPECS:
            valve_type = '闸阀'
        if dn not in self.VALVE_SPECS[valve_type]:
            dn = 'DN100'
        spec = self.VALVE_SPECS[valve_type][dn]

        position = position or {'x': 4000, 'y': -150, 'z': 2500}

        force_points = valve_force_points(dn, spec['outer'], spec['length'])
        contact_faces = valve_contact_faces(dn, spec['outer'], spec['length'])

        l2 = {
            '阀门类型': valve_type,
            '规格': dn,
            '厂家': manufacturer,
            '外径': f'{spec["outer"]}mm',
            '长度': f'{spec["length"]}mm',
            '重量': f'{spec["weight"]}kg',
            '材质': '铸钢',
            '连接方式': '法兰',
            '工作压力': '1.6MPa',
            '适用温度': '-20℃ ~ 150℃',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['length'], 'y': spec['outer'], 'z': spec['outer']},
        }

        l3 = {
            '绝对坐标': position,
            '旋转角度': 0,
            '工作压力': '1.6MPa',
            '受力点实时坐标': [],
        }

        cbm = valve_cbm(dn, spec['outer'], spec['length'])

        super().__init__(
            entity_type='阀门',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.valve_type = valve_type
        self.dn = dn
        self.system = system
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = dn
        self.layer['r_layer']['子类型'] = valve_type
        self.layer['r_layer']['系统'] = system

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def get_flange_positions(self):
        """获取两端法兰位置（用于装配）"""
        length = self._parse_mm(self.layer['l2_static_attributes']['长度'])
        pos = self.layer['l3_dynamic_state']['绝对坐标']
        return {
            'left': {'x': pos['x'] - length / 2, 'y': pos['y'], 'z': pos['z']},
            'right': {'x': pos['x'] + length / 2, 'y': pos['y'], 'z': pos['z']},
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '阀门',
            'valve_type': self.valve_type,
            'dn': self.dn,
            'layer': self.layer,
        }

    @staticmethod
    def _parse_mm(val) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val.replace('mm', '').strip())
        return 0.0