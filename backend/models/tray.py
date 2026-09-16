# -*- coding: utf-8 -*-
"""
桥架实体
受 GPL v3.0 保护

镀锌钢板桥架。含受力点+接触面。
桥架优先级3，与水管间距≥100mm。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import tray_cbm, tray_force_points, tray_contact_faces
from config import config


class TrayEntity(BaseEntity):
    """桥架实体"""

    # 桥架规格（宽×高）
    TRAY_SPECS = {
        '300×100': {'width': 300, 'height': 100, 'weight_per_m': 8},
        '400×100': {'width': 400, 'height': 100, 'weight_per_m': 10},
        '200×100': {'width': 200, 'height': 100, 'weight_per_m': 6},
    }

    # 最小间距
    MIN_CLEARANCE = 100

    def __init__(self, spec: str = '300×100', material: str = '镀锌钢板',
                 thickness: float = 1.0, start: Optional[Dict] = None,
                 end: Optional[Dict] = None, manufacturer: str = '桥架厂',
                 system: str = '电气系统', space: Optional[Dict] = None):
        if spec not in self.TRAY_SPECS:
            spec = '300×100'
        spec_data = self.TRAY_SPECS[spec]

        start = start or {'x': 0, 'y': -1000, 'z': 2700}
        end = end or {'x': 10000, 'y': -1000, 'z': 2700}

        # 长度计算
        length = abs(end['x'] - start['x']) or 10000
        center = {
            'x': (start['x'] + end['x']) / 2,
            'y': (start['y'] + end['y']) / 2,
            'z': (start['z'] + end['z']) / 2,
        }

        # 重量计算
        total_weight = round(spec_data['weight_per_m'] * length / 1000, 2)

        # 受力点/接触面
        force_points = tray_force_points(spec, thickness)
        contact_faces = tray_contact_faces(spec, thickness)

        # L2层
        l2 = {
            '规格': spec,
            '宽度': f'{spec_data["width"]}mm',
            '高度': f'{spec_data["height"]}mm',
            '材质': material,
            '壁厚': f'{thickness}mm',
            '连接方式': '螺栓连接',
            '单位重量': f'{spec_data["weight_per_m"]}kg/m',
            '总重量': f'{total_weight}kg',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': spec_data['width'], 'z': spec_data['height']},
        }

        # L3层
        l3 = {
            '起点坐标': start,
            '终点坐标': end,
            '中心坐标': center,
            '长度': length,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = tray_cbm(spec, thickness)

        super().__init__(
            entity_type='桥架',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=center,
        )

        self.spec = spec
        self.length = length
        self.start = start
        self.end = end
        self.system = system
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = spec
        self.layer['r_layer']['系统'] = system

    def calc_weight(self) -> float:
        """计算桥架总重量"""
        return float(str(self.layer['l2_static_attributes']['总重量']).replace('kg', ''))

    def check_clearance(self, entities: List[Any]) -> Dict[str, Any]:
        """检查与水管的间距"""
        violations = []
        my_pos = self.get_position()

        for e in entities:
            if e is self:
                continue
            e_type = getattr(e, 'entity_type', '')
            if e_type not in ('管道', '阀门', '卡箍', '风管'):
                continue

            e_pos = e.layer.get('l3_dynamic_state', {}).get('绝对坐标', {})
            dy = abs(my_pos['y'] - e_pos.get('y', 0))
            dz = abs(my_pos['z'] - e_pos.get('z', 0))

            min_dist = min(dy, dz)
            if min_dist < self.MIN_CLEARANCE:
                violations.append({
                    'entity_id': getattr(e, 'id', None),
                    'entity_type': e_type,
                    'distance': min_dist,
                    'required': self.MIN_CLEARANCE,
                })

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'message': f'间距检查完成，{"通过" if not violations else f"发现{len(violations)}个违规"}',
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
            'entity_type': '桥架',
            'spec': self.spec,
            'length': self.length,
            'start': self.start,
            'end': self.end,
            'layer': self.layer,
        }