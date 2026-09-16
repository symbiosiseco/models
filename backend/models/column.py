# -*- coding: utf-8 -*-
"""
柱子实体
受 GPL v3.0 保护

中间垂直支撑。含受力点+接触面。
柱子y=200，避让管道y=-150。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import column_cbm, column_force_points, column_contact_faces
from config import config


class ColumnEntity(BaseEntity):
    """柱子实体"""

    # 柱子规格
    COLUMN_SPECS = {
        '400': {'width': 400, 'height': 3000, 'reinforcement': '4Φ20', 'capacity': '2000kN'},
        '500': {'width': 500, 'height': 3000, 'reinforcement': '4Φ22', 'capacity': '3000kN'},
        '600': {'width': 600, 'height': 3000, 'reinforcement': '4Φ25', 'capacity': '4000kN'},
    }

    def __init__(self, x_pos: float = 2500, width: float = 400,
                 height: float = 3000, material: str = 'C30混凝土',
                 reinforcement: str = '4Φ20', load_capacity: str = '2000kN',
                 space: Optional[Dict] = None):
        spec = self.COLUMN_SPECS.get(str(int(width)), self.COLUMN_SPECS['400'])

        # 位置：柱子中心（y=200避让管道）
        position = {'x': x_pos, 'y': 200, 'z': height / 2}

        # 受力点
        force_points = column_force_points(width, height)

        # 接触面
        contact_faces = column_contact_faces(width, height)

        # L2层
        l2 = {
            '类型': '混凝土柱',
            '截面尺寸': f'{width}×{width}mm',
            '高度': f'{height}mm',
            '材质': material,
            '配筋': reinforcement or spec['reinforcement'],
            '承重能力': load_capacity or spec['capacity'],
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': width, 'y': width, 'z': height},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = column_cbm(width, height)

        super().__init__(
            entity_type='柱子',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.x_pos = x_pos
        self.width = width
        self.height = height
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = f'{width}×{width}'

    def check_load(self, load: str) -> Dict[str, Any]:
        """检查载荷是否超过承重能力"""
        try:
            load_kn = float(str(load).replace('kN', '').strip())
            capacity_kn = float(str(self.layer['l2_static_attributes']['承重能力'])
                                .replace('kN', '').strip())
        except (ValueError, TypeError):
            return {'passed': True, 'message': '无法解析载荷'}

        passed = load_kn <= capacity_kn
        return {
            'passed': passed,
            'load': load_kn,
            'capacity': capacity_kn,
            'message': f'载荷{load_kn}kN，承重{capacity_kn}kN',
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
            'entity_type': '柱子',
            'x_pos': self.x_pos,
            'width': self.width,
            'height': self.height,
            'position': self.get_position(),
            'layer': self.layer,
        }