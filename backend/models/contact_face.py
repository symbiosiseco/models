# -*- coding: utf-8 -*-
"""
接触面实体
受 GPL v3.0 保护

接触面 = 成品装配的绝对锚点。
不符合物理规则的，哪怕一点点都装配不上。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity


class ContactFaceEntity(BaseEntity):
    """接触面实体"""

    def __init__(self, cf_id: str = '', cf_type: str = '法兰面',
                 position: Optional[Dict] = None, normal: str = 'X-',
                 contact_types: Optional[List[str]] = None,
                 tolerance: str = '0mm',
                 must_contain: Optional[List[str]] = None,
                 violation: str = '', assembly_order: int = 1,
                 space: Optional[Dict] = None):
        # L2层：接触面定义
        l2 = {
            '接触面ID': cf_id,
            '类型': cf_type,
            '位置': position or {'x': 0, 'y': 0, 'z': 0},
            '法线方向': normal,
            '接触对象类型': contact_types or [],
            '允许偏差': tolerance,
            '必须包含': must_contain or [],
            '违反后果': violation,
            '装配顺序': assembly_order,
        }

        super().__init__(
            entity_type='接触面',
            l2=l2,
            position=position or {'x': 0, 'y': 0, 'z': 0},
        )

        self.cf_id = cf_id
        self.cf_type = cf_type
        self.normal = normal
        self.tolerance = tolerance
        self.must_contain = must_contain or []
        self.violation = violation
        self.assembly_order = assembly_order

    def get_position(self) -> Dict[str, float]:
        """获取接触面位置"""
        return self.layer.get('l2_static_attributes', {}).get('位置', {'x': 0, 'y': 0, 'z': 0})

    def check_contact(self, other_face: 'ContactFaceEntity') -> Dict[str, Any]:
        """
        检查与另一个接触面是否匹配。

        匹配条件：
            1. 法线相反
            2. 位置对齐（偏差 ≤ tolerance）
            3. 类型兼容
        """
        # 1. 法线相反
        normal_match = self._normal_opposite(self.normal, other_face.normal)

        # 2. 位置对齐
        pos_a = self.get_position()
        pos_b = other_face.get_position()
        distance = (
            (pos_a['x'] - pos_b['x']) ** 2 +
            (pos_a['y'] - pos_b['y']) ** 2 +
            (pos_a['z'] - pos_b['z']) ** 2
        ) ** 0.5
        tolerance = self._parse_mm(self.tolerance)
        position_match = distance <= tolerance

        # 3. 类型兼容
        type_match = (
            other_face.cf_type in self.layer['l2_static_attributes'].get('接触对象类型', []) or
            self.cf_type in other_face.layer['l2_static_attributes'].get('接触对象类型', [])
        )

        passed = normal_match and position_match

        return {
            'passed': passed,
            'checks': {
                'normal_match': normal_match,
                'position_match': position_match,
                'type_match': type_match,
                'distance': distance,
                'tolerance': tolerance,
            },
            'message': '接触面匹配' if passed else '接触面不匹配',
        }

    def is_paired(self) -> bool:
        """检查接触面是否成对出现（通过cf_id的left/right后缀判断）"""
        return 'left' in self.cf_id or 'right' in self.cf_id

    def check_must_contain(self, entities: List[Any]) -> Dict[str, Any]:
        """检查必须包含的实体是否到位"""
        if not self.must_contain:
            return {'passed': True, 'missing': []}

        present_types = set()
        for e in entities:
            if hasattr(e, 'entity_type'):
                present_types.add(e.entity_type)

        missing = [t for t in self.must_contain if t not in present_types]
        passed = len(missing) == 0

        return {
            'passed': passed,
            'missing': missing,
            'violation': self.violation if not passed else None,
            'message': '必须包含的实体已到位' if passed else f'缺少：{missing}',
        }

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '接触面',
            'cf_id': self.cf_id,
            'cf_type': self.cf_type,
            'position': self.get_position(),
            'normal': self.normal,
            'tolerance': self.tolerance,
            'must_contain': self.must_contain,
            'violation': self.violation,
            'layer': self.layer,
        }

    @staticmethod
    def _normal_opposite(n1: str, n2: str) -> bool:
        """判断两个法线是否相反"""
        if not n1 or not n2:
            return False
        opposite_pairs = [
            ('X+', 'X-'), ('X-', 'X+'),
            ('Y+', 'Y-'), ('Y-', 'Y+'),
            ('Z+', 'Z-'), ('Z-', 'Z+'),
        ]
        return (n1, n2) in opposite_pairs

    @staticmethod
    def _parse_mm(val) -> float:
        """解析 "0mm" → 0.0"""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val.replace('mm', '').strip())
        return 0.0