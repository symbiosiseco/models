# -*- coding: utf-8 -*-
"""
支架实体
受 GPL v3.0 保护

单支角钢支架。含受力点+接触面。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import support_cbm, support_force_points, support_contact_faces
from config import config


class SupportEntity(BaseEntity):
    """支架实体"""

    # 支架规格
    SUPPORT_SPECS = {
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

    def __init__(self, index: int = 0, support_type: str = '单支角钢支架',
                 x_pos: Optional[float] = None, space: Optional[Dict] = None):
        # 默认x坐标
        if x_pos is None:
            x_pos = 1000 + index * 2000

        # 规格
        spec = self.SUPPORT_SPECS.get(support_type, self.SUPPORT_SPECS['单支角钢支架'])

        # 单个螺栓承重（(管道载荷 + 支架自重) / 2）
        # 管道载荷约 32.7kg，支架自重 4.9kg，安全系数 1.5
        single_bolt_load = round((32.7 + 4.9) * 1.5 / 2, 2)

        # 受力点
        force_points = support_force_points(x_pos, support_type)

        # 接触面
        contact_faces = support_contact_faces(x_pos, support_type)

        # L2层
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
            '包围盒': {'x': 50, 'y': 400, 'z': 300},
        }

        # L3层
        l3 = {
            '绝对坐标': {'x': x_pos, 'y': -100, 'z': 2500},
            '旋转角度': 0,
            '受力': '0kg',
            '实际安装高度': 2500,
            '实测数据': [],
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = support_cbm(x_pos, support_type)

        super().__init__(
            entity_type='支架',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position={'x': x_pos, 'y': -100, 'z': 2500},
        )

        # 附加字段
        self.index = index
        self.support_type = support_type
        self.x_pos = x_pos
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = spec['规格']
        self.layer['r_layer']['序号'] = index

    def calc_load(self, pipe_weight: str = '50kg') -> Dict[str, Any]:
        """计算支架载荷"""
        try:
            pipe_kg = float(str(pipe_weight).replace('kg', ''))
        except (ValueError, TypeError):
            pipe_kg = 50.0

        support_kg = 4.9
        total = pipe_kg + support_kg
        single_bolt = total * 1.5 / 2

        return {
            'pipe_weight': pipe_kg,
            'support_weight': support_kg,
            'total_weight': total,
            'safety_factor': 1.5,
            'single_bolt_load': round(single_bolt, 2),
        }

    def get_force_points(self):
        """获取受力点"""
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self):
        """获取接触面"""
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '支架',
            'index': self.index,
            'support_type': self.support_type,
            'x_pos': self.x_pos,
            'layer': self.layer,
        }