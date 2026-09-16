# -*- coding: utf-8 -*-
"""
楼板实体
受 GPL v3.0 保护

承载体上部。含受力点+接触面。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import slab_cbm, slab_force_points, slab_contact_faces
from config import config


class SlabEntity(BaseEntity):
    """楼板实体"""

    # 楼板规格
    SLAB_SPECS = {
        '楼板100': {'thickness': 100, 'density': 2500, 'capacity': '6000kg/m²'},
        '楼板120': {'thickness': 120, 'density': 2500, 'capacity': '8000kg/m²'},
        '楼板150': {'thickness': 150, 'density': 2500, 'capacity': '10000kg/m²'},
        '楼板200': {'thickness': 200, 'density': 2500, 'capacity': '12000kg/m²'},
    }

    def __init__(self, slab_type: str = '楼板120', length: float = 10000,
                 width: float = 3000, thickness: float = 120,
                 material: str = 'C30混凝土', flatness: float = 3.0,
                 space: Optional[Dict] = None):
        if slab_type not in self.SLAB_SPECS:
            slab_type = '楼板120'
        spec = self.SLAB_SPECS[slab_type]

        # 位置：楼板中心，底面z=3000
        position = {'x': length / 2, 'y': -width / 2, 'z': 3000 - thickness / 2}

        # 受力点
        force_points = slab_force_points(slab_type, thickness)

        # 接触面
        contact_faces = slab_contact_faces(slab_type, thickness)

        # L2层
        l2 = {
            '类型': slab_type,
            '长度': f'{length}mm',
            '宽度': f'{width}mm',
            '厚度': f'{thickness}mm',
            '材质': material,
            '板底平整度': f'±{flatness}mm',
            '实测记录': [],
            '承重能力': spec['capacity'],
            '容重': f'{spec["density"]}kg/m³',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': width, 'z': thickness},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '底面标高': 3000,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = slab_cbm(slab_type, thickness)

        super().__init__(
            entity_type='楼板',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.slab_type = slab_type
        self.length = length
        self.width = width
        self.thickness = thickness
        self.flatness = flatness
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = slab_type

    def add_measurement(self, x: float, y: float, actual_z: float,
                        measured_by: str = '') -> Dict[str, Any]:
        """添加实测记录"""
        record = {
            'x': x,
            'y': y,
            '实际标高': actual_z,
            '设计标高': 3000,
            '偏差': round(actual_z - 3000, 2),
            '测量人': measured_by,
        }
        self.layer['l2_static_attributes']['实测记录'].append(record)
        return {'success': True, 'record': record}

    def get_measurements(self) -> List[Dict[str, Any]]:
        """获取实测记录"""
        return self.layer['l2_static_attributes'].get('实测记录', [])

    def calc_flatness_deviation(self) -> Dict[str, Any]:
        """计算平整度偏差"""
        measurements = self.get_measurements()
        if not measurements:
            return {'passed': True, 'max_deviation': 0}

        max_dev = max(abs(m['偏差']) for m in measurements)
        passed = max_dev <= self.flatness
        return {
            'passed': passed,
            'max_deviation': max_dev,
            'threshold': self.flatness,
            'message': f'最大偏差{max_dev}mm，阈值±{self.flatness}mm',
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
            'entity_type': '楼板',
            'slab_type': self.slab_type,
            'length': self.length,
            'width': self.width,
            'thickness': self.thickness,
            'measurements': self.get_measurements(),
            'layer': self.layer,
        }