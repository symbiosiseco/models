# -*- coding: utf-8 -*-
"""
螺栓实体
受 GPL v3.0 保护

支持多种规格。含受力点+接触面。
M16拧紧力矩40N·m，M20为80N·m。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import bolt_cbm, bolt_force_points, bolt_contact_faces
from config import config


class BoltEntity(BaseEntity):
    """螺栓实体"""

    # 螺栓国标（GB/T 5782）
    BOLT_SPECS = {
        'M10': {'diameter': 10, 'length': 65,  'torque': 15, 'preload': 10000, 'tensile': 300},
        'M12': {'diameter': 12, 'length': 100, 'torque': 20, 'preload': 15000, 'tensile': 400},
        'M16': {'diameter': 16, 'length': 80,  'torque': 40, 'preload': 25000, 'tensile': 500},
        'M20': {'diameter': 20, 'length': 100, 'torque': 80, 'preload': 40000, 'tensile': 600},
    }

    # 螺栓类型
    BOLT_TYPES = ['膨胀螺栓', '法兰螺栓', '六角螺栓', '螺母', '垫圈']

    # 公差
    FIT_TOLERANCE = 0.5

    def __init__(self, spec: str = 'M12', bolt_type: str = '膨胀螺栓',
                 length: Optional[float] = None, position: Optional[Dict] = None,
                 connect_support: Optional[str] = None,
                 connect_flange: Optional[str] = None,
                 index: int = 0, space: Optional[Dict] = None):
        if spec not in self.BOLT_SPECS:
            spec = 'M12'
        if bolt_type not in self.BOLT_TYPES:
            bolt_type = '膨胀螺栓'
        bolt_spec = self.BOLT_SPECS[spec]

        if length is None:
            length = bolt_spec['length']

        position = position or {'x': 1000, 'y': -800, 'z': 100}

        # 受力点
        force_points = bolt_force_points(spec, length)

        # 接触面
        contact_faces = bolt_contact_faces(spec, length)

        # L2层
        l2 = {
            '类型': bolt_type,
            '规格': spec,
            '直径': f'{bolt_spec["diameter"]}mm',
            '长度': f'{length}mm',
            '材质': 'Q235B',
            '拧紧力矩': f'{bolt_spec["torque"]}N·m',
            '预紧力': f'{bolt_spec["preload"]}N',
            '允许拉力': f'{bolt_spec["tensile"]}kg',
            '连接支架': connect_support,
            '连接法兰': connect_flange,
            '序号': index,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': bolt_spec['diameter'], 'z': bolt_spec['diameter']},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = bolt_cbm(spec, length)
        cbm['装配规则']['公差'] = self.FIT_TOLERANCE

        super().__init__(
            entity_type='螺栓',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.spec = spec
        self.bolt_type = bolt_type
        self.length = length
        self.connect_support = connect_support
        self.connect_flange = connect_flange
        self.index = index
        self.space = space or config.SPACE_UNITS
        self.diameter = bolt_spec['diameter']

        # 更新R层
        self.layer['r_layer']['规格'] = spec
        self.layer['r_layer']['子类型'] = bolt_type

    # ==================== 孔径检查 ====================

    def check_hole_fit(self, hole_diameter: float) -> Dict[str, Any]:
        """
        检查螺栓能否穿过孔。

        规则：螺栓直径 + 公差（0.5mm） ≤ 孔径
        - M16 (16) + 0.5 = 16.5 ≤ 18 ✅
        - M20 (20) + 0.5 = 20.5 > 18 ❌
        """
        passed = (self.diameter + self.FIT_TOLERANCE) <= hole_diameter
        return {
            'success': passed,
            'bolt_spec': self.spec,
            'bolt_diameter': self.diameter,
            'tolerance': self.FIT_TOLERANCE,
            'hole_diameter': hole_diameter,
            'message': (
                f'{self.diameter}+{self.FIT_TOLERANCE}<={hole_diameter}'
                if passed else
                f'{self.diameter}+{self.FIT_TOLERANCE}>{hole_diameter}'
            ),
        }

    def calc_preload(self) -> Dict[str, Any]:
        """计算预紧力"""
        bolt_spec = self.BOLT_SPECS[self.spec]
        return {
            'preload': bolt_spec['preload'],
            'torque': bolt_spec['torque'],
            'tensile_capacity': bolt_spec['tensile'],
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
            'entity_type': '螺栓',
            'spec': self.spec,
            'bolt_type': self.bolt_type,
            'length': self.length,
            'connect_support': self.connect_support,
            'connect_flange': self.connect_flange,
            'layer': self.layer,
        }