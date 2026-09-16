# -*- coding: utf-8 -*-
"""
联轴器实体
受 GPL v3.0 保护

连接两段同管径的管道。含受力点+接触面。

V2.0（阶段1）：尺寸从 pipes.json 推算。
"""

from typing import Dict, Any, Optional, List
from .entity import BaseEntity
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON推算联轴器规格 ====================

_DEFAULT_COUPLING_SPECS = {
    'DN50':  {'outer': 88,  'length': 90},
    'DN80':  {'outer': 120, 'length': 130},
    'DN100': {'outer': 140, 'length': 170},
    'DN150': {'outer': 200, 'length': 250},
    'DN200': {'outer': 260, 'length': 330},
}


def _load_coupling_specs() -> Dict[str, Dict[str, float]]:
    """联轴器外径 ≈ 管道外径 × 1.22，长度 ≈ 管道外径 × 1.5"""
    specs = {}
    for dn, default in _DEFAULT_COUPLING_SPECS.items():
        pipe_spec = read_standard('pipes', dn)
        outer = pipe_spec.get('外径', default['outer'] / 1.22)
        specs[dn] = {
            'outer': round(outer * 1.22, 1),
            'length': round(outer * 1.5, 1),
        }
    return specs


class CouplingEntity(BaseEntity):
    """联轴器实体"""

    # ★ V2.0：从 pipes.json 推算
    COUPLING_SPECS = _load_coupling_specs()

    def __init__(self, dn: str = 'DN100', material: str = '镀锌铸铁',
                 position: Optional[Dict] = None, connect_pipes: Optional[List] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        if dn not in self.COUPLING_SPECS:
            dn = 'DN100'
        spec = self.COUPLING_SPECS[dn]

        position = position or {'x': 6000, 'y': -150, 'z': 2500}
        connect_pipes = connect_pipes or []

        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '联轴器中心',
                '方向': 'X+',
                '传力对象': '管道',
                '承重上限': '500kg',
            }
        ]

        contact_faces = [
            {
                'id': 'cf_groove_left',
                '类型': '沟槽',
                '位置': {'x': -spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X-',
                '接触对象类型': ['管道'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
            {
                'id': 'cf_groove_right',
                '类型': '沟槽',
                '位置': {'x': spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X+',
                '接触对象类型': ['管道'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
        ]

        l2 = {
            '规格': dn,
            '材质': material,
            '外径': f'{spec["outer"]}mm',
            '长度': f'{spec["length"]}mm',
            '连接管道': connect_pipes,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['length'], 'y': spec['outer'], 'z': spec['outer']},
        }

        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        cbm = {
            '物理规则': {
                '包围盒': {'x': spec['length'], 'y': spec['outer'], 'z': spec['outer']},
                '最小间距': 50,
                '允许接触': ['管道'],
                '禁止穿透': True,
                '接触方式': '沟槽卡接',
            },
            '受力规则': {
                '自重': '1.5kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['管道轴向力 → 联轴器 → 两段管道连接'],
                '承重上限': '500kg',
            },
            '装配规则': {
                '连接对象': ['管道'],
                '拧紧力矩': '2.5-3.5N·m',
                '装配顺序': ['橡胶圈放入', '两段管道对齐', '联轴器扣合', '螺栓拧紧'],
                '密封等级': 'PN16',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '维护空间': 100,
                '检查周期': '每年1次',
                '管径要求': '两端必须同管径',
            },
        }

        super().__init__(
            entity_type='联轴器',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.material = material
        self.system = system
        self.connect_pipes = list(connect_pipes)
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = dn

    def check_dn_match(self, pipe1_dn: str, pipe2_dn: str) -> bool:
        """检查两段管道管径是否一致"""
        return pipe1_dn == pipe2_dn

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '联轴器',
            'dn': self.dn,
            'connect_pipes': self.connect_pipes,
            'layer': self.layer,
        }