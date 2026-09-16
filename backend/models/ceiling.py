# -*- coding: utf-8 -*-
"""
吊顶实体
受 GPL v3.0 保护

轻钢龙骨石膏板吊顶。含受力点+接触面。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import ceiling_cbm, ceiling_force_points, ceiling_contact_faces
from config import config


class CeilingEntity(BaseEntity):
    """吊顶实体"""

    # 吊顶规格
    CEILING_SPECS = {
        '轻钢龙骨石膏板': {'thickness': 20, 'weight': 15, 'fire_rating': 'A级'},
        '矿棉板':         {'thickness': 15, 'weight': 8,  'fire_rating': 'A级'},
        '铝扣板':         {'thickness': 10, 'weight': 5,  'fire_rating': 'A级'},
    }

    def __init__(self, ceiling_type: str = '轻钢龙骨石膏板',
                 ceiling_height: float = 2700, length: float = 10000,
                 width: float = 3000, material: str = '石膏板',
                 space: Optional[Dict] = None):
        if ceiling_type not in self.CEILING_SPECS:
            ceiling_type = '轻钢龙骨石膏板'
        spec = self.CEILING_SPECS[ceiling_type]

        # 位置：吊顶中心
        position = {'x': length / 2, 'y': -width / 2, 'z': ceiling_height}

        # 受力点
        force_points = ceiling_force_points(ceiling_type, ceiling_height)

        # 接触面
        contact_faces = ceiling_contact_faces(ceiling_type, ceiling_height)

        # L2层
        l2 = {
            '类型': ceiling_type,
            '吊顶高度': f'{ceiling_height}mm',
            '长度': f'{length}mm',
            '宽度': f'{width}mm',
            '材质': material,
            '耐火等级': spec['fire_rating'],
            '单位重量': f'{spec["weight"]}kg/m²',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': width, 'z': spec['thickness']},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = ceiling_cbm(ceiling_type, ceiling_height)

        super().__init__(
            entity_type='吊顶',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.ceiling_type = ceiling_type
        self.ceiling_height = ceiling_height
        self.length = length
        self.width = width
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = ceiling_type

    def check_hidden_pipes(self, entities: List[Any]) -> Dict[str, Any]:
        """检查隐藏管线是否在吊顶上方"""
        hidden = []
        for e in entities:
            e_type = getattr(e, 'entity_type', '')
            if e_type in ('管道', '风管', '桥架'):
                pos = e.layer.get('l3_dynamic_state', {}).get('绝对坐标', {})
                if pos.get('z', 0) > self.ceiling_height:
                    hidden.append({
                        'id': getattr(e, 'id', None),
                        'type': e_type,
                        'z': pos.get('z'),
                    })
        return {
            'passed': len(hidden) > 0 or True,
            'hidden_count': len(hidden),
            'hidden_pipes': hidden,
        }

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
            'entity_type': '吊顶',
            'ceiling_type': self.ceiling_type,
            'ceiling_height': self.ceiling_height,
            'length': self.length,
            'width': self.width,
            'layer': self.layer,
        }