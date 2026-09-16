# -*- coding: utf-8 -*-
"""
受力点实体
受 GPL v3.0 保护

受力点 = 一个绝对空间中的精确点，所有力从这里传导。
受力点是L2的"锚"，L2从受力点长出来。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity


class ForcePointEntity(BaseEntity):
    """受力点实体"""

    def __init__(self, fp_id: str = '', fp_type: str = '法兰面承压',
                 position: Optional[Dict] = None, direction: str = 'Z-',
                 capacity: str = '500kg', safety_factor: str = '',
                 transfer_target: str = '', space: Optional[Dict] = None):
        # L2层：受力点定义
        l2 = {
            '受力点ID': fp_id,
            '类型': fp_type,
            '位置': position or {'x': 0, 'y': 0, 'z': 0},
            '方向': direction,
            '承重上限': capacity,
            '安全系数': safety_factor,
            '传力对象': transfer_target,
        }

        # L3层：受力点实时状态
        l3 = {
            '受力点实时坐标': [],
            '当前受力': '0kg',
            '受力状态': '稳定',
        }

        super().__init__(
            entity_type='受力点',
            l2=l2,
            l3=l3,
            position=position or {'x': 0, 'y': 0, 'z': 0},
        )

        # 记录私有字段
        self.fp_id = fp_id
        self.fp_type = fp_type
        self.direction = direction
        self.capacity = capacity

    def get_relative_position(self) -> Dict[str, float]:
        """获取L2的相对坐标"""
        return self.layer.get('l2_static_attributes', {}).get('位置', {'x': 0, 'y': 0, 'z': 0})

    def get_absolute_position(self) -> Dict[str, float]:
        """从L3取受力点绝对坐标"""
        l3 = self.layer.get('l3_dynamic_state', {})
        for fp in l3.get('受力点实时坐标', []):
            if fp.get('id') == self.fp_id:
                return fp.get('绝对坐标', {'x': 0, 'y': 0, 'z': 0})
        return {'x': 0, 'y': 0, 'z': 0}

    def update_force(self, force_value: str, force_direction: str = '') -> Dict[str, Any]:
        """更新L3的受力数据"""
        l3 = self.layer['l3_dynamic_state']
        if '受力点实时坐标' not in l3:
            l3['受力点实时坐标'] = []

        for fp in l3['受力点实时坐标']:
            if fp.get('id') == self.fp_id:
                fp['当前受力'] = force_value
                fp['受力方向'] = force_direction or self.direction
                fp['受力状态'] = '稳定' if self.check_capacity(force_value) else '超载'
                return {'success': True}

        # 不存在则新增
        l3['受力点实时坐标'].append({
            'id': self.fp_id,
            '绝对坐标': self.get_relative_position(),
            '当前受力': force_value,
            '受力方向': force_direction or self.direction,
            '受力状态': '稳定' if self.check_capacity(force_value) else '超载',
        })
        return {'success': True}

    def check_capacity(self, force_value: str) -> bool:
        """检查受力是否在承重范围内"""
        try:
            current = self._parse_kg(force_value)
            capacity = self._parse_kg(self.capacity)
            return current <= capacity
        except Exception:
            return True

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '受力点',
            'fp_id': self.fp_id,
            'fp_type': self.fp_type,
            'relative_position': self.get_relative_position(),
            'absolute_position': self.get_absolute_position(),
            'direction': self.direction,
            'capacity': self.capacity,
            'layer': self.layer,
        }

    @staticmethod
    def _parse_kg(val) -> float:
        """解析 "15kg" → 15.0"""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val.replace('kg', '').strip())
        return 0.0