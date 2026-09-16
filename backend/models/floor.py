# -*- coding: utf-8 -*-
"""
地面实体
受 GPL v3.0 保护

承载体下部。含受力点+接触面。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import floor_cbm, floor_force_points, floor_contact_faces
from config import config


class FloorEntity(BaseEntity):
    """地面实体"""

    # 地面规格
    FLOOR_SPECS = {
        '混凝土地面': {'thickness': 200, 'density': 2500, 'capacity': '5000kg/m²'},
        '环氧地面':   {'thickness': 180, 'density': 2200, 'capacity': '4000kg/m²'},
        '防静电地面': {'thickness': 150, 'density': 2000, 'capacity': '3000kg/m²'},
    }

    def __init__(self, floor_type: str = '混凝土地面', length: float = 10000,
                 width: float = 3000, thickness: float = 200,
                 material: str = 'C25混凝土', load_capacity: str = '5000kg/m²',
                 space: Optional[Dict] = None):
        if floor_type not in self.FLOOR_SPECS:
            floor_type = '混凝土地面'
        spec = self.FLOOR_SPECS[floor_type]

        # 位置：地面中心，表面z=0
        position = {'x': length / 2, 'y': -width / 2, 'z': -thickness / 2}

        # 受力点
        force_points = floor_force_points(floor_type, thickness)

        # 接触面
        contact_faces = floor_contact_faces(floor_type, thickness)

        # L2层
        l2 = {
            '类型': floor_type,
            '长度': f'{length}mm',
            '宽度': f'{width}mm',
            '厚度': f'{thickness}mm',
            '材质': material,
            '承重能力': load_capacity or spec['capacity'],
            '容重': f'{spec["density"]}kg/m³',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': width, 'z': thickness},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '表面标高': 0,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = floor_cbm(floor_type, thickness)

        super().__init__(
            entity_type='地面',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.floor_type = floor_type
        self.length = length
        self.width = width
        self.thickness = thickness
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = floor_type

    def check_load(self, load: str) -> Dict[str, Any]:
        """检查载荷是否超过承重能力"""
        try:
            load_kg = float(str(load).replace('kg/m²', '').replace('kg', '').strip())
            capacity_kg = float(str(self.layer['l2_static_attributes']['承重能力'])
                                .replace('kg/m²', '').replace('kg', '').strip())
        except (ValueError, TypeError):
            return {'passed': True, 'message': '无法解析载荷'}

        passed = load_kg <= capacity_kg
        return {
            'passed': passed,
            'load': load_kg,
            'capacity': capacity_kg,
            'message': f'载荷{load_kg}kg/m²，承重{capacity_kg}kg/m²',
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
            'entity_type': '地面',
            'floor_type': self.floor_type,
            'length': self.length,
            'width': self.width,
            'thickness': self.thickness,
            'layer': self.layer,
        }