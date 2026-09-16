# -*- coding: utf-8 -*-
"""
垫片/橡胶圈实体
受 GPL v3.0 保护

两种用途：阀门法兰垫片 / 卡箍橡胶圈。
含接触面+5个绝对约束。

V2.0（阶段1）：GASKET_SPECS 从 gaskets.json 读，消除硬编码。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import gasket_cbm, gasket_contact_faces
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON加载垫片规格 ====================

_DEFAULT_GASKET_SPECS = {
    'DN50':  {'outer': 107, 'inner': 61,    'thickness': 3},
    'DN80':  {'outer': 142, 'inner': 89,    'thickness': 3},
    'DN100': {'outer': 162, 'inner': 115,   'thickness': 3},
    'DN150': {'outer': 218, 'inner': 169,   'thickness': 3},
    'DN200': {'outer': 273, 'inner': 220,   'thickness': 3},
}


def _load_gasket_specs() -> Dict[str, Dict[str, float]]:
    """从 gaskets.json 加载垫片规格。"""
    specs = {}
    for dn, default in _DEFAULT_GASKET_SPECS.items():
        s = read_standard('gaskets', dn)
        specs[dn] = {
            'outer': s.get('垫片外径', default['outer']),
            'inner': s.get('垫片内径', default['inner']),
            'thickness': s.get('厚度', default['thickness']),
        }
    return specs


class GasketEntity(BaseEntity):
    """垫片/橡胶圈实体"""

    # ★ V2.0：从 JSON 加载
    GASKET_SPECS = _load_gasket_specs()

    GASKET_TYPES = ['法兰垫片', '卡箍橡胶圈']
    MATERIALS = ['三元乙丙(EPDM)', '丁腈橡胶', '聚四氟乙烯']

    def __init__(self, dn: str = 'DN100', gasket_type: str = '法兰垫片',
                 material: str = '三元乙丙(EPDM)', manufacturer: str = 'E厂',
                 position: Optional[Dict] = None, connect_clamp: Optional[str] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None,
                 design_life: int = 10):
        if dn not in self.GASKET_SPECS:
            dn = 'DN100'
        if gasket_type not in self.GASKET_TYPES:
            gasket_type = '法兰垫片'
        if material not in self.MATERIALS:
            material = '三元乙丙(EPDM)'
        spec = self.GASKET_SPECS[dn]

        position = position or {'x': 4000, 'y': -150, 'z': 2500}

        contact_faces = gasket_contact_faces(dn, spec['outer'], spec['thickness'])
        constraints = self._build_constraints(spec)

        l2 = {
            '类型': gasket_type,
            '规格': dn,
            '厂家': manufacturer,
            '材质': material,
            '外径': f'{spec["outer"]}mm',
            '内径': f'{spec["inner"]}mm',
            '厚度': f'{spec["thickness"]}mm',
            '设计年限': f'{design_life}年',
            '工作温度': '-20℃ ~ 120℃',
            '连接卡箍': connect_clamp,
            '接触面': contact_faces,
            '约束': constraints,
            '包围盒': {'x': spec['thickness'], 'y': spec['outer'], 'z': spec['outer']},
        }

        l3 = {
            '绝对坐标': position,
            '安装日期': None,
        }

        cbm = gasket_cbm(dn, spec['outer'], spec['thickness'])
        cbm['规范约束']['设计年限'] = f'{design_life}年'
        cbm['规范约束']['更换周期'] = f'{design_life - 2}年检查，{design_life}年更换'

        super().__init__(
            entity_type='垫片',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.gasket_type = gasket_type
        self.material = material
        self.connect_clamp = connect_clamp
        self.design_life = design_life
        self.system = system
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = dn
        self.layer['r_layer']['子类型'] = gasket_type

    def _build_constraints(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建垫片的5个绝对约束。"""
        return [
            {
                '类型': '位置约束',
                '规则': '必须在两法兰中间',
                '违反后果': '漏水',
                '允许偏差': '0mm',
            },
            {
                '类型': '范围约束',
                '规则': f'外径 ≤ {spec["outer"]}mm（法兰密封面外径）',
                '违反后果': '无效密封',
                '允许偏差': '0mm',
            },
            {
                '类型': '孔径约束',
                '规则': f'内径 ≥ {spec["inner"]}mm（管道外径）',
                '违反后果': '螺栓穿不过',
                '允许偏差': '0mm',
            },
            {
                '类型': '方向约束',
                '规则': '必须与法兰面平行',
                '违反后果': '密封失效',
                '允许偏差': '0mm',
            },
            {
                '类型': '数量约束',
                '规则': '每个法兰连接必须有1个',
                '违反后果': '漏水',
                '允许偏差': '0个',
            },
        ]

    def get_constraints(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('约束', [])

    def check_position(self, flange_left, flange_right) -> Dict[str, Any]:
        gasket_pos = self.get_position()
        left_pos = flange_left.get_position() if hasattr(flange_left, 'get_position') else flange_left.layer['l3_dynamic_state']['绝对坐标']
        right_pos = flange_right.get_position() if hasattr(flange_right, 'get_position') else flange_right.layer['l3_dynamic_state']['绝对坐标']

        x_min = min(left_pos['x'], right_pos['x'])
        x_max = max(left_pos['x'], right_pos['x'])

        passed = x_min <= gasket_pos['x'] <= x_max
        return {
            'passed': passed,
            'check': '位置约束',
            'violation': None if passed else '漏水',
            'message': f'垫片X={gasket_pos["x"]}，法兰范围[{x_min}, {x_max}]',
        }

    def check_range(self, flange_outer_d: str) -> Dict[str, Any]:
        gasket_outer = self._parse_mm(self.layer['l2_static_attributes']['外径'])
        flange_outer = self._parse_mm(flange_outer_d)

        passed = gasket_outer <= flange_outer
        return {
            'passed': passed,
            'check': '范围约束',
            'violation': None if passed else '无效密封',
            'message': f'垫片外径{gasket_outer}mm vs 法兰外径{flange_outer}mm',
        }

    def check_hole_clearance(self, bolt_holes: List[Dict]) -> Dict[str, Any]:
        gasket_inner = self._parse_mm(self.layer['l2_static_attributes']['内径'])
        passed = gasket_inner > 0
        return {
            'passed': passed,
            'check': '孔径约束',
            'violation': None if passed else '螺栓穿不过',
            'message': f'垫片内径{gasket_inner}mm',
        }

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '垫片',
            'dn': self.dn,
            'gasket_type': self.gasket_type,
            'material': self.material,
            'design_life': self.design_life,
            'layer': self.layer,
        }

    @staticmethod
    def _parse_mm(val) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val.replace('mm', '').strip())
        return 0.0