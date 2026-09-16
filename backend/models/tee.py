# -*- coding: utf-8 -*-
"""
三通实体
受 GPL v3.0 保护

连接三个方向的管道。含受力点+接触面。

V2.0（阶段1）：TEE_SPECS 从 pipes.json 推算（三通外径 = 主管外径）。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON推算三通规格 ====================

_DEFAULT_TEE_SPECS = {
    'DN50':  {'outer': 60.3,  'length': 120},
    'DN80':  {'outer': 88.9,  'length': 160},
    'DN100': {'outer': 114.3, 'length': 200},
    'DN150': {'outer': 168.3, 'length': 280},
    'DN200': {'outer': 219.1, 'length': 360},
}


def _load_tee_specs() -> Dict[str, Dict[str, float]]:
    """从 pipes.json 加载对应管道外径，三通中心长度按 1.75D 计算。"""
    specs = {}
    for dn, default in _DEFAULT_TEE_SPECS.items():
        pipe_spec = read_standard('pipes', dn)
        outer = pipe_spec.get('外径', default['outer'])
        length = round(outer * 1.75, 1)
        specs[dn] = {'outer': outer, 'length': length}
    return specs


class TeeEntity(BaseEntity):
    """三通实体"""

    # ★ V2.0：从 pipes.json 推算
    TEE_SPECS = _load_tee_specs()

    def __init__(self, dn: str = 'DN100', branch_dn: str = 'DN80',
                 material: str = '镀锌铸铁', position: Optional[Dict] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        if dn not in self.TEE_SPECS:
            dn = 'DN100'
        if branch_dn not in self.TEE_SPECS:
            branch_dn = 'DN80'
        spec = self.TEE_SPECS[dn]

        position = position or {'x': 6000, 'y': -150, 'z': 2500}

        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '三通中心',
                '方向': 'Z-',
                '传力对象': '管道',
                '承重上限': '500kg',
            }
        ]

        contact_faces = [
            {
                'id': 'cf_groove_main_in',
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
                'id': 'cf_groove_main_out',
                '类型': '沟槽',
                '位置': {'x': spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X+',
                '接触对象类型': ['卡箍'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
            {
                'id': 'cf_groove_branch',
                '类型': '沟槽',
                '位置': {'x': 0, 'y': -spec['length'] / 2, 'z': 0},
                '法线方向': 'Y-',
                '接触对象类型': ['卡箍'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
        ]

        l2 = {
            '主管规格': dn,
            '支管规格': branch_dn,
            '材质': material,
            '外径': f'{spec["outer"]}mm',
            '支管角度': '90°',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['length'], 'y': spec['length'], 'z': spec['outer']},
        }

        l3 = {
            '绝对坐标': position,
            '三个端口坐标': {
                'main_in':  {'x': position['x'] - spec['length'] / 2, 'y': position['y'], 'z': position['z']},
                'main_out': {'x': position['x'] + spec['length'] / 2, 'y': position['y'], 'z': position['z']},
                'branch':   {'x': position['x'], 'y': position['y'] - spec['length'] / 2, 'z': position['z']},
            },
            '受力点实时坐标': [],
        }

        cbm = {
            '物理规则': {
                '包围盒': {'x': spec['length'], 'y': spec['length'], 'z': spec['outer']},
                '最小间距': 100,
                '允许接触': ['卡箍', '管道'],
                '禁止穿透': True,
                '接触方式': '沟槽卡接',
            },
            '受力规则': {
                '自重': '3kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['三通自重 → 三个端口 → 卡箍 → 管道'],
                '承重上限': '500kg',
            },
            '装配规则': {
                '连接对象': ['卡箍', '管道'],
                '拧紧力矩': '2.5-3.5N·m',
                '装配顺序': ['橡胶圈放入', '端口对齐', '卡箍扣合', '螺栓拧紧'],
                '密封等级': 'PN16',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '维护空间': 100,
                '检查周期': '每年1次',
            },
        }

        super().__init__(
            entity_type='三通',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.branch_dn = branch_dn
        self.system = system
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = f'{dn}/{branch_dn}'

    def get_branch_angle(self) -> float:
        return 90.0

    def get_three_end_positions(self) -> Dict[str, Any]:
        return self.layer['l3_dynamic_state']['三个端口坐标']

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '三通',
            'dn': self.dn,
            'branch_dn': self.branch_dn,
            'branch_angle': self.get_branch_angle(),
            'layer': self.layer,
        }