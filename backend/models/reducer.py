# -*- coding: utf-8 -*-
"""
变径管实体
受 GPL v3.0 保护

连接两段不同管径的管道。含受力点+接触面。

V2.0（阶段1）：尺寸从 pipes.json 推算（两端外径分别读对应DN）。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON推算变径管规格 ====================

_DEFAULT_REDUCER_SPECS = {
    'DN100/DN80': {'length': 300},
    'DN80/DN50':  {'length': 200},
    'DN150/DN100': {'length': 380},
    'DN200/DN150': {'length': 520},
}


def _load_reducer_specs() -> Dict[str, Dict[str, float]]:
    """变径管外径从两端管道DN读，长度 = (大径 + 小径) × 1.5"""
    specs = {}
    for key, default in _DEFAULT_REDUCER_SPECS.items():
        dn_in, dn_out = key.split('/')
        s_in = read_standard('pipes', dn_in)
        s_out = read_standard('pipes', dn_out)
        outer_in = s_in.get('外径', 114.3)
        outer_out = s_out.get('外径', 88.9)
        length = round((outer_in + outer_out) * 1.5, 1)
        specs[key] = {
            'outer_in': outer_in,
            'outer_out': outer_out,
            'length': length,
        }
    return specs


class ReducerEntity(BaseEntity):
    """变径管实体"""

    # ★ V2.0：从 pipes.json 推算
    REDUCER_SPECS = _load_reducer_specs()

    def __init__(self, dn_in: str = 'DN100', dn_out: str = 'DN80',
                 material: str = '镀锌铸铁', position: Optional[Dict] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        if dn_in == dn_out:
            raise ValueError('变径管两端管径必须不同')

        # 组装 key
        key = f'{dn_in}/{dn_out}'
        if key not in self.REDUCER_SPECS:
            # 动态推算
            s_in = read_standard('pipes', dn_in)
            s_out = read_standard('pipes', dn_out)
            outer_in = s_in.get('外径', 114.3)
            outer_out = s_out.get('外径', 88.9)
            spec = {
                'outer_in': outer_in,
                'outer_out': outer_out,
                'length': round((outer_in + outer_out) * 1.5, 1),
            }
        else:
            spec = self.REDUCER_SPECS[key]

        position = position or {'x': 5000, 'y': -150, 'z': 2500}
        max_outer = max(spec['outer_in'], spec['outer_out'])

        # 受力点：变径管中心
        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '变径管中心',
                '方向': 'X+',
                '传力对象': '管道',
                '承重上限': '500kg',
            }
        ]

        # 接触面：两端沟槽
        contact_faces = [
            {
                'id': 'cf_groove_in',
                '类型': '沟槽',
                '位置': {'x': -spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X-',
                '接触对象类型': ['卡箍'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
            {
                'id': 'cf_groove_out',
                '类型': '沟槽',
                '位置': {'x': spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X+',
                '接触对象类型': ['卡箍'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
        ]

        # L2层
        l2 = {
            '进口规格': dn_in,
            '出口规格': dn_out,
            '材质': material,
            '进口外径': f'{spec["outer_in"]}mm',
            '出口外径': f'{spec["outer_out"]}mm',
            '长度': f'{spec["length"]}mm',
            '变径方式': '同心变径',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['length'], 'y': max_outer, 'z': max_outer},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '进口端坐标': {'x': position['x'] - spec['length'] / 2, 'y': position['y'], 'z': position['z']},
            '出口端坐标': {'x': position['x'] + spec['length'] / 2, 'y': position['y'], 'z': position['z']},
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = {
            '物理规则': {
                '包围盒': {'x': spec['length'], 'y': max_outer, 'z': max_outer},
                '最小间距': 100,
                '允许接触': ['卡箍', '管道'],
                '禁止穿透': True,
                '接触方式': '沟槽卡接',
            },
            '受力规则': {
                '自重': '2kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['变径管自重 → 两端沟槽 → 卡箍 → 管道'],
                '承重上限': '500kg',
            },
            '装配规则': {
                '连接对象': ['卡箍', '管道'],
                '拧紧力矩': '2.5-3.5N·m',
                '装配顺序': ['橡胶圈放入', '两端对齐', '卡箍扣合', '螺栓拧紧'],
                '密封等级': 'PN16',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '维护空间': 100,
                '检查周期': '每年1次',
                '禁止场景': '重力排水管（坡度要求）',
            },
        }

        super().__init__(
            entity_type='变径管',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn_in = dn_in
        self.dn_out = dn_out
        self.material = material
        self.system = system
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = f'{dn_in}/{dn_out}'

    def calc_length(self) -> float:
        """计算变径管长度"""
        key = f'{self.dn_in}/{self.dn_out}'
        if key in self.REDUCER_SPECS:
            return self.REDUCER_SPECS[key]['length']
        return 300.0

    def get_end_positions(self) -> Dict[str, Any]:
        return {
            'in': self.layer['l3_dynamic_state']['进口端坐标'],
            'out': self.layer['l3_dynamic_state']['出口端坐标'],
        }

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '变径管',
            'dn_in': self.dn_in,
            'dn_out': self.dn_out,
            'length': self.calc_length(),
            'layer': self.layer,
        }