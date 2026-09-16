# -*- coding: utf-8 -*-
"""
法兰实体
受 GPL v3.0 保护

独立成品，用于阀门/管道连接。含受力点+接触面。
DN100法兰孔径18mm（装配检查关键）。
"""

import math
from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import flange_cbm, flange_force_points, flange_contact_faces
from config import config


class FlangeEntity(BaseEntity):
    """法兰实体"""

    # 法兰国标尺寸（GB/T 9119 PN16）
    FLANGE_SPECS = {
        'DN50':  {'outer': 165, 'thickness': 20, 'bolts': 4,  'bolt_spec': 'M16', 'hole': 18},
        'DN80':  {'outer': 200, 'thickness': 22, 'bolts': 4,  'bolt_spec': 'M16', 'hole': 18},
        'DN100': {'outer': 220, 'thickness': 24, 'bolts': 8,  'bolt_spec': 'M16', 'hole': 18},
        'DN150': {'outer': 285, 'thickness': 26, 'bolts': 8,  'bolt_spec': 'M20', 'hole': 22},
        'DN200': {'outer': 340, 'thickness': 30, 'bolts': 12, 'bolt_spec': 'M20', 'hole': 22},
    }

    # 法兰类型
    FLANGE_TYPES = ['沟槽法兰', '平焊法兰', '对焊法兰']

    # 压力等级
    PRESSURE_LEVELS = ['PN10', 'PN16', 'PN25']

    def __init__(self, dn: str = 'DN100', flange_type: str = '沟槽法兰',
                 pressure: str = 'PN16', manufacturer: str = 'D厂',
                 position: Optional[Dict] = None, system: str = '消防给水系统',
                 space: Optional[Dict] = None):
        # 参数校验
        if dn not in self.FLANGE_SPECS:
            dn = 'DN100'
        if flange_type not in self.FLANGE_TYPES:
            flange_type = '沟槽法兰'
        if pressure not in self.PRESSURE_LEVELS:
            pressure = 'PN16'
        spec = self.FLANGE_SPECS[dn]

        position = position or {'x': 4000, 'y': -150, 'z': 2500}

        # 受力点
        force_points = flange_force_points(dn, spec['outer'], spec['thickness'])

        # 接触面
        contact_faces = flange_contact_faces(dn, spec['outer'], spec['thickness'])

        # L2层
        l2 = {
            '类型': flange_type,
            '规格': dn,
            '厂家': manufacturer,
            '外径': f'{spec["outer"]}mm',
            '厚度': f'{spec["thickness"]}mm',
            '螺栓数量': spec['bolts'],
            '螺栓规格': spec['bolt_spec'],
            '螺栓孔径': f'{spec["hole"]}mm',
            '材质': '铸钢',
            '密封面': 'RF凸面',
            '压力等级': pressure,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['thickness'], 'y': spec['outer'], 'z': spec['outer']},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = flange_cbm(dn, spec['outer'], spec['thickness'])
        # 增加孔径信息到CBM（装配检查用）
        cbm['装配规则']['孔径'] = spec['hole']
        cbm['装配规则']['螺栓数量'] = spec['bolts']
        cbm['装配规则']['螺栓规格'] = spec['bolt_spec']

        super().__init__(
            entity_type='法兰',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.flange_type = flange_type
        self.pressure = pressure
        self.system = system
        self.space = space or config.SPACE_UNITS
        self.bolt_hole_diameter = spec['hole']

        # 更新R层
        self.layer['r_layer']['规格'] = dn
        self.layer['r_layer']['子类型'] = flange_type
        self.layer['r_layer']['压力等级'] = pressure
        self.layer['r_layer']['系统'] = system

    # ==================== 螺栓孔 ====================

    def get_bolt_holes(self) -> List[Dict[str, Any]]:
        """
        获取螺栓孔位置。

        DN100 → 8个孔
        DN150 → 8个孔
        DN200 → 12个孔
        """
        spec = self.FLANGE_SPECS[self.dn]
        count = spec['bolts']
        hole_d = spec['hole']
        # 分布圆直径 = 外径 × 0.85
        pcd = spec['outer'] * 0.85

        holes = []
        for i in range(count):
            angle = 2 * math.pi * i / count
            holes.append({
                'id': f'bolt_hole_{i + 1}',
                '类型': '螺栓孔',
                '孔径': hole_d,
                '位置': {
                    'x': 0,
                    'y': round(pcd / 2 * math.cos(angle), 2),
                    'z': round(pcd / 2 * math.sin(angle), 2),
                },
                '用途': f'穿{spec["bolt_spec"]}螺栓',
            })
        return holes

    def check_bolt_fit(self, bolt_spec: str) -> Dict[str, Any]:
        """
        检查螺栓能否穿过法兰孔。

        规则：螺栓直径 + 公差（0.5mm） ≤ 孔径
        - M16 + 0.5 = 16.5 ≤ 18 ✅
        - M20 + 0.5 = 20.5 > 18 ❌
        """
        try:
            diameter = float(bolt_spec.replace('M', ''))
        except ValueError:
            return {'success': False, 'message': f'无效螺栓规格：{bolt_spec}'}

        tolerance = config.CBM_CONFIG.get('bolt_fit_tolerance', 0.5)
        hole = self.bolt_hole_diameter

        passed = (diameter + tolerance) <= hole
        return {
            'success': passed,
            'bolt_spec': bolt_spec,
            'bolt_diameter': diameter,
            'tolerance': tolerance,
            'hole_diameter': hole,
            'message': (
                f'{diameter}+{tolerance}<={hole}，可以穿过'
                if passed else
                f'{diameter}+{tolerance}>{hole}，无法穿过'
            ),
        }

    # ==================== 受力点/接触面 ====================

    def get_force_points(self) -> List[Dict[str, Any]]:
        """获取受力点"""
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        """获取接触面"""
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '法兰',
            'dn': self.dn,
            'flange_type': self.flange_type,
            'pressure': self.pressure,
            'bolt_holes': self.get_bolt_holes(),
            'layer': self.layer,
        }