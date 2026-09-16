# -*- coding: utf-8 -*-
"""
手轮实体
受 GPL v3.0 保护

阀门顶部的手轮。

V2.0（阶段1）：尺寸从 pipes.json 推算（手轮外径 ≈ 阀门DN对应管道外径 × 1.75）。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON推算手轮规格 ====================

_DEFAULT_WHEEL_SPECS = {
    'DN50':  {'outer': 120, 'weight': 1.0, 'spokes': 4},
    'DN80':  {'outer': 160, 'weight': 1.4, 'spokes': 4},
    'DN100': {'outer': 200, 'weight': 1.8, 'spokes': 4},
    'DN150': {'outer': 280, 'weight': 3.2, 'spokes': 5},
    'DN200': {'outer': 360, 'weight': 5.0, 'spokes': 5},
}


def _load_wheel_specs() -> Dict[str, Dict[str, Any]]:
    """手轮外径 ≈ 管道外径 × 1.75"""
    specs = {}
    for dn, default in _DEFAULT_WHEEL_SPECS.items():
        pipe_spec = read_standard('pipes', dn)
        outer = pipe_spec.get('外径', default['outer'] / 1.75)
        specs[dn] = {
            'outer': round(outer * 1.75, 1),
            'weight': default['weight'],
            'spokes': default['spokes'],
        }
    return specs


class WheelEntity(BaseEntity):
    """手轮实体"""

    # ★ V2.0：从 pipes.json 推算
    WHEEL_SPECS = _load_wheel_specs()

    def __init__(self, dn: str = 'DN100', manufacturer: str = 'A厂',
                 position: Optional[Dict] = None, connect_valve: Optional[str] = None,
                 space: Optional[Dict] = None):
        if dn not in self.WHEEL_SPECS:
            dn = 'DN100'
        spec = self.WHEEL_SPECS[dn]

        position = position or {'x': 4000, 'y': -150, 'z': 2700}

        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '手轮中心',
                '方向': 'Z-',
                '传力对象': '阀杆',
                '承重上限': '150N·m',
            }
        ]

        contact_faces = [
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

        l2 = {
            '类型': '手轮',
            '规格': dn,
            '厂家': manufacturer,
            '外径': f'{spec["outer"]}mm',
            '重量': f'{spec["weight"]}kg',
            '材质': '铸铁',
            '辐条数量': spec['spokes'],
            '连接阀门': connect_valve,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': 20, 'y': spec['outer'], 'z': spec['outer']},
        }

        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        cbm = {
            '物理规则': {
                '包围盒': {'x': 20, 'y': spec['outer'], 'z': spec['outer']},
                '最小间距': 100,
                '允许接触': ['阀杆'],
                '禁止穿透': True,
                '接触方式': '键槽连接',
            },
            '受力规则': {
                '自重': f'{spec["weight"]}kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['操作力矩 → 手轮 → 阀杆 → 阀体'],
                '承重上限': '150N·m',
            },
            '装配规则': {
                '连接对象': ['阀杆'],
                '拧紧力矩': '10N·m',
                '装配顺序': ['键槽对齐', '手轮套入', '紧固螺母'],
                '密封等级': '无',
            },
            '规范约束': {
                '安装规范': 'GB/T 12224',
                '操作力矩': '≤150N·m',
                '维护空间': 100,
                '检查周期': '每年1次',
            },
        }

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

        self.layer['r_layer']['规格'] = dn

    def calc_operation_torque(self) -> Dict[str, Any]:
        """计算操作力矩"""
        return {'torque': 150, 'unit': 'N·m', 'max_allowed': 150}

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '手轮',
            'dn': self.dn,
            'connect_valve': self.connect_valve,
            'layer': self.layer,
        }