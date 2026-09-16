# -*- coding: utf-8 -*-
"""
穿墙套管实体
受 GPL v3.0 保护

含受力点+接触面。
套管是穿过墙体的管道保护件。

V2.0（阶段1）：SLEEVE_SPECS 从 pipes.json 推算（套管外径 = 对应管道外径 × 1.2）。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON推算套管规格 ====================

# 套管规格 → 对应管道 DN
_SLEEVE_TO_PIPE = {
    'DN100': 'DN80',
    'DN150': 'DN100',
    'DN200': 'DN150',
}

_DEFAULT_SLEEVE_SPECS = {
    'DN100': {'outer': 114.3, 'wall': 4.0, 'applicable_pipe': 'DN80'},
    'DN150': {'outer': 168.3, 'wall': 4.5, 'applicable_pipe': 'DN100'},
    'DN200': {'outer': 219.1, 'wall': 6.0, 'applicable_pipe': 'DN150'},
}


def _load_sleeve_specs() -> Dict[str, Dict[str, Any]]:
    """套管规格：外径从 pipes.json 对应管道读，加套管壁厚与间隙。"""
    specs = {}
    for sleeve_dn, default in _DEFAULT_SLEEVE_SPECS.items():
        pipe_dn = _SLEEVE_TO_PIPE[sleeve_dn]
        pipe_spec = read_standard('pipes', pipe_dn)
        # 套管外径 = 管道外径 + 2×(壁厚+间隙) = 管道外径 × 1.2（简化）
        pipe_outer = pipe_spec.get('外径', default['outer'] / 1.2)
        specs[sleeve_dn] = {
            'outer': round(pipe_outer * 1.2, 1),
            'wall': default['wall'],
            'applicable_pipe': pipe_dn,
        }
    return specs


class SleeveEntity(BaseEntity):
    """穿墙套管实体"""

    # ★ V2.0：从 pipes.json 推算
    SLEEVE_SPECS = _load_sleeve_specs()

    SLEEVE_TYPES = ['普通套管', '防水套管', '柔性防水套管', '刚性防水套管']

    def __init__(self, sleeve_type: str = '普通套管', dn: str = 'DN150',
                 wall_thickness: float = 240, position: Optional[Dict] = None,
                 space: Optional[Dict] = None):
        if sleeve_type not in self.SLEEVE_TYPES:
            sleeve_type = '普通套管'
        if dn not in self.SLEEVE_SPECS:
            dn = 'DN150'
        spec = self.SLEEVE_SPECS[dn]

        position = position or {'x': 5000, 'y': -150, 'z': 2500}

        # 计算套管长度 = 墙厚 + 100mm
        length = wall_thickness + 100

        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '套管中心',
                '方向': 'Z-',
                '传力对象': '墙体',
                '承重上限': '500kg',
            }
        ]

        contact_faces = [
            {
                'id': 'cf_inner_wall',
                '类型': '套管内壁',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '法线方向': 'X+',
                '接触对象类型': ['管道'],
                '允许偏差': '0mm',
                '必须包含': ['填充料'],
                '违反后果': '漏水',
                '装配顺序': 2,
            },
            {
                'id': 'cf_outer_wall',
                '类型': '套管外壁',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '法线方向': 'X+',
                '接触对象类型': ['墙体'],
                '允许偏差': '0mm',
                '必须包含': ['封堵料'],
                '违反后果': '渗漏',
                '装配顺序': 1,
            },
        ]

        l2 = {
            '类型': sleeve_type,
            '规格': dn,
            '外径': f'{spec["outer"]}mm',
            '壁厚': f'{spec["wall"]}mm',
            '材质': 'Q235B',
            '长度': f'{length}mm',
            '墙厚': f'{wall_thickness}mm',
            '两侧出墙': '50mm',
            '适用管道': spec['applicable_pipe'],
            '间隙填充': '20-30mm 柔性防火填料',
            '封堵要求': '防火封堵',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': spec['outer'], 'z': spec['outer']},
        }

        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        cbm = {
            '物理规则': {
                '包围盒': {'x': length, 'y': spec['outer'], 'z': spec['outer']},
                '最小间距': 20,
                '允许接触': ['墙体', '管道'],
                '禁止穿透': True,
                '接触方式': '内外壁接触',
            },
            '受力规则': {
                '自重': '3kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['套管自重 → 墙体'],
                '承重上限': '500kg',
            },
            '装配规则': {
                '连接对象': ['墙体', '管道'],
                '拧紧力矩': '无',
                '装配顺序': ['预留洞口', '套管就位', '填充封堵'],
                '密封等级': '柔性防火填料',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '间隙要求': '20-30mm',
                '维护空间': 0,
                '检查周期': '每年1次',
            },
        }

        super().__init__(
            entity_type='套管',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.sleeve_type = sleeve_type
        self.dn = dn
        self.wall_thickness = wall_thickness
        self.length = length
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = dn
        self.layer['r_layer']['子类型'] = sleeve_type

    def calc_length(self) -> float:
        return self.length

    def check_clearance(self, pipe_dn: str) -> Dict[str, Any]:
        """检查管道与套管的间隙"""
        pipe_spec = read_standard('pipes', pipe_dn)
        pipe_outer = pipe_spec.get('外径', 114.3)

        sleeve_outer = self.SLEEVE_SPECS[self.dn]['outer']
        sleeve_wall = self.SLEEVE_SPECS[self.dn]['wall']
        sleeve_inner = sleeve_outer - 2 * sleeve_wall
        clearance = (sleeve_inner - pipe_outer) / 2

        passed = 20 <= clearance <= 30
        return {
            'passed': passed,
            'clearance': round(clearance, 2),
            'message': f'间隙{round(clearance, 2)}mm（要求20-30mm）',
        }

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '套管',
            'sleeve_type': self.sleeve_type,
            'dn': self.dn,
            'wall_thickness': self.wall_thickness,
            'length': self.length,
            'layer': self.layer,
        }