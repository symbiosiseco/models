# -*- coding: utf-8 -*-
"""
墙体实体
受 GPL v3.0 保护

含受力点+接触面。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import wall_cbm, wall_force_points, wall_contact_faces
from config import config


class WallEntity(BaseEntity):
    """墙体实体"""

    # 墙体规格
    WALL_SPECS = {
        '砌体墙240': {'thickness': 240, 'density': 1800, 'capacity': '5kN/m²'},
        '砌体墙120': {'thickness': 120, 'density': 1800, 'capacity': '3kN/m²'},
        '混凝土墙200': {'thickness': 200, 'density': 2500, 'capacity': '10kN/m²'},
        '轻质隔墙100': {'thickness': 100, 'density': 800,  'capacity': '2kN/m²'},
    }

    def __init__(self, wall_type: str = '砌体墙240', length: float = 10000,
                 height: float = 3000, thickness: float = 240,
                 material: str = '烧结普通砖', mortar: str = 'M5水泥砂浆',
                 space: Optional[Dict] = None):
        if wall_type not in self.WALL_SPECS:
            wall_type = '砌体墙240'
        spec = self.WALL_SPECS[wall_type]

        # 位置：墙体中心
        position = {'x': length / 2, 'y': 0, 'z': height / 2}

        # 受力点
        force_points = wall_force_points(wall_type, thickness)

        # 接触面
        contact_faces = wall_contact_faces(wall_type, thickness)

        # L2层
        l2 = {
            '类型': wall_type,
            '长度': f'{length}mm',
            '高度': f'{height}mm',
            '厚度': f'{thickness}mm',
            '材质': material,
            '砂浆': mortar,
            '容重': f'{spec["density"]}kg/m³',
            '承重能力': spec['capacity'],
            '洞口': [],
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': thickness, 'z': height},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = wall_cbm(wall_type, thickness)

        super().__init__(
            entity_type='墙体',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.wall_type = wall_type
        self.length = length
        self.height = height
        self.thickness = thickness
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = wall_type

    def add_opening(self, x: float, z: float, diameter: float,
                    purpose: str = '') -> Dict[str, Any]:
        """向L2洞口数组追加洞口记录"""
        opening = {
            'id': f'opening_{len(self.layer["l2_static_attributes"]["洞口"]) + 1}',
            '位置': {'x': x, 'z': z},
            '直径': f'{diameter}mm',
            '用途': purpose,
        }
        self.layer['l2_static_attributes']['洞口'].append(opening)
        return {'success': True, 'opening': opening}

    def get_openings(self) -> List[Dict[str, Any]]:
        """获取洞口列表"""
        return self.layer['l2_static_attributes'].get('洞口', [])

    def check_opening_fit(self, sleeve_dn: str) -> Dict[str, Any]:
        """检查套管能否穿过洞口"""
        # 洞口直径 vs 套管外径
        openings = self.get_openings()
        if not openings:
            return {'passed': False, 'message': '无洞口'}

        sleeve_outer_map = {'DN100': 114.3, 'DN150': 168.3, 'DN200': 219.1}
        sleeve_outer = sleeve_outer_map.get(sleeve_dn, 168.3)

        for op in openings:
            try:
                op_d = float(str(op.get('直径', '0mm')).replace('mm', ''))
            except (ValueError, TypeError):
                continue
            if op_d >= sleeve_outer:
                return {'passed': True, 'opening': op, 'message': '套管可穿过'}
        return {'passed': False, 'message': '洞口太小'}

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
            'entity_type': '墙体',
            'wall_type': self.wall_type,
            'length': self.length,
            'height': self.height,
            'thickness': self.thickness,
            'openings': self.get_openings(),
            'layer': self.layer,
        }