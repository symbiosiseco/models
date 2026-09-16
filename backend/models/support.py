# -*- coding: utf-8 -*-
"""
支架实体
受 GPL v3.0 保护

单支角钢支架。含受力点+接触面。

V2.0（阶段1）：SUPPORT_SPECS 从 angles.json 读，消除硬编码。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import support_cbm, support_force_points, support_contact_faces, support_anchors
from data.standard_reader import read_standard
from config import config


# ==================== 从JSON加载支架规格 ====================

# 角钢规格 → angles.json 的 key
_SUPPORT_ANGLE_KEY = 'L50×50×6'

_DEFAULT_SUPPORT_SPECS = {
    '单支角钢支架': {
        '规格': 'L50×50×6',
        '材质': 'Q235B',
        '横担长度': '400mm',
        '立杆长度': '300mm',
        '底板尺寸': '100×100×8',
        '膨胀螺栓': 'M12×100',
        '膨胀螺栓数量': 2,
        '总重量': '4.9kg',
        '承重能力': '500kg',
        '安全系数': '1.5',
    },
}


def _load_support_specs() -> Dict[str, Dict[str, Any]]:
    """从 angles.json 读角钢规格，其他字段（底板/螺栓）保持默认。"""
    angle = read_standard('angles', _SUPPORT_ANGLE_KEY)
    default = _DEFAULT_SUPPORT_SPECS['单支角钢支架']

    # 角钢理论重量（kg/m）× 约3米 = 支架总重
    angle_weight_per_m = angle.get('理论重量', 1.72)
    total_weight = round(angle_weight_per_m * 3, 2)

    return {
        '单支角钢支架': {
            '规格': angle.get('规格', default['规格']),
            '材质': angle.get('材质', default['材质']),
            '横担长度': default['横担长度'],
            '立杆长度': default['立杆长度'],
            '底板尺寸': default['底板尺寸'],
            '膨胀螺栓': default['膨胀螺栓'],
            '膨胀螺栓数量': default['膨胀螺栓数量'],
            '总重量': f'{total_weight}kg',
            '承重能力': default['承重能力'],
            '安全系数': default['安全系数'],
        },
    }


class SupportEntity(BaseEntity):
    """支架实体"""

    # ★ V2.0：从 angles.json 加载
    SUPPORT_SPECS = _load_support_specs()

    def __init__(self, index: int = 0, support_type: str = '单支角钢支架',
                 x_pos: Optional[float] = None, space: Optional[Dict] = None):
        if x_pos is None:
            x_pos = 1000 + index * 2000

        spec = self.SUPPORT_SPECS.get(support_type, self.SUPPORT_SPECS['单支角钢支架'])

        # 单个螺栓承重
        weight = float(str(spec['总重量']).replace('kg', ''))
        single_bolt_load = round((32.7 + weight) * 1.5 / 2, 2)

        force_points = support_force_points(x_pos, support_type)
        contact_faces = support_contact_faces(x_pos, support_type)

        l2 = {
            '类型': support_type,
            '规格': spec['规格'],
            '材质': spec['材质'],
            '横担长度': spec['横担长度'],
            '立杆长度': spec['立杆长度'],
            '底板尺寸': spec['底板尺寸'],
            '膨胀螺栓': spec['膨胀螺栓'],
            '膨胀螺栓数量': spec['膨胀螺栓数量'],
            '单个螺栓承重': f'{single_bolt_load}kg',
            '总重量': spec['总重量'],
            '承重能力': spec['承重能力'],
            '安全系数': spec['安全系数'],
            '防腐': '热浸镀锌',
            '受力点': force_points,
            '接触面': contact_faces,
            '锚点': support_anchors(support_type),
            '包围盒': {'x': 50, 'y': 400, 'z': 300},
        }

        l3 = {
            '绝对坐标': {'x': x_pos, 'y': -100, 'z': 2500},
            '旋转角度': 0,
            '受力': '0kg',
            '实际安装高度': 2500,
            '实测数据': [],
            '受力点实时坐标': [],
        }

        cbm = support_cbm(x_pos, support_type)

        super().__init__(
            entity_type='支架',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position={'x': x_pos, 'y': -100, 'z': 2500},
        )

        self.index = index
        self.support_type = support_type
        self.x_pos = x_pos
        self.space = space or config.SPACE_UNITS

        self.layer['r_layer']['规格'] = spec['规格']
        self.layer['r_layer']['序号'] = index

    def calc_load(self, pipe_weight: str = '50kg') -> Dict[str, Any]:
        """计算支架载荷"""
        try:
            pipe_kg = float(str(pipe_weight).replace('kg', ''))
        except (ValueError, TypeError):
            pipe_kg = 50.0

        weight = float(str(self.layer['l2_static_attributes']['总重量']).replace('kg', ''))
        total = pipe_kg + weight
        single_bolt = total * 1.5 / 2

        return {
            'pipe_weight': pipe_kg,
            'support_weight': weight,
            'total_weight': total,
            'safety_factor': 1.5,
            'single_bolt_load': round(single_bolt, 2),
        }

    def get_force_points(self):
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '支架',
            'index': self.index,
            'support_type': self.support_type,
            'x_pos': self.x_pos,
            'layer': self.layer,
        }