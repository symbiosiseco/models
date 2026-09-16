# -*- coding: utf-8 -*-
"""
弯头实体
受 GPL v3.0 保护

连接两段不同方向的管道。含受力点+接触面。
"""

import math
from typing import Dict, Any, Optional
from .entity import BaseEntity
from config import config


class ElbowEntity(BaseEntity):
    """弯头实体"""

    # 弯头规格
    ELBOW_SPECS = {
        'DN50':  {'outer': 60.3,  'length': 100},
        'DN80':  {'outer': 88.9,  'length': 140},
        'DN100': {'outer': 114.3, 'length': 180},
        'DN150': {'outer': 168.3, 'length': 260},
        'DN200': {'outer': 219.1, 'length': 340},
    }

    # 允许角度
    ALLOWED_ANGLES = [45, 90]

    def __init__(self, dn: str = 'DN100', angle: int = 90, radius: str = '1.5D',
                 material: str = '镀锌铸铁', position: Optional[Dict] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        # 参数校验
        if dn not in self.ELBOW_SPECS:
            dn = 'DN100'
        if angle not in self.ALLOWED_ANGLES:
            angle = 90
        spec = self.ELBOW_SPECS[dn]

        position = position or {'x': 8000, 'y': -150, 'z': 2500}

        # 受力点：弯头中心
        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '弯头中心',
                '方向': 'Z-',
                '传力对象': '管道',
                '承重上限': '500kg',
            }
        ]

        # 接触面：两端沟槽
        contact_faces = [
            {
                'id': 'cf_groove_start',
                '类型': '沟槽',
                '位置': {'x': -spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X-',
                '接触对象类型': ['卡箍'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
            {
                'id': 'cf_groove_end',
                '类型': '沟槽',
                '位置': {'x': spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X+',
                '接触对象类型': ['卡箍'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
        ]

        # L2层
        l2 = {
            '规格': dn,
            '角度': f'{angle}°',
            '弯曲半径': radius,
            '材质': material,
            '外径': f'{spec["outer"]}mm',
            '中心长度': f'{spec["length"]}mm',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['length'], 'y': spec['outer'], 'z': spec['outer']},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '旋转角度': 0,
            '起始端坐标': {'x': position['x'] - spec['length'] / 2, 'y': position['y'], 'z': position['z']},
            '终止端坐标': {'x': position['x'] + spec['length'] / 2, 'y': position['y'], 'z': position['z']},
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = {
            '物理规则': {
                '包围盒': {'x': spec['length'], 'y': spec['outer'], 'z': spec['outer']},
                '最小间距': 100,
                '允许接触': ['卡箍', '管道'],
                '禁止穿透': True,
                '接触方式': '沟槽卡接',
            },
            '受力规则': {
                '自重': '2kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['弯头自重 → 两端沟槽 → 卡箍 → 管道'],
                '承重上限': '500kg',
            },
            '装配规则': {
                '连接对象': ['卡箍', '管道'],
                '拧紧力矩': '2.5-3.5N·m',
                '装配顺序': ['橡胶圈放入', '两端管道对齐', '卡箍扣合', '螺栓拧紧'],
                '密封等级': 'PN16',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '弯曲半径要求': '≥1.0D',
                '维护空间': 100,
                '检查周期': '每年1次',
            },
        }

        super().__init__(
            entity_type='弯头',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.angle = angle
        self.radius = radius
        self.system = system
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = dn
        self.layer['r_layer']['角度'] = f'{angle}°'

    def calc_arc_length(self) -> float:
        """
        计算弯曲弧长 = π × R × angle / 180

        R = 1.5D 或 1.0D × 管径
        """
        spec = self.ELBOW_SPECS[self.dn]
        # 弯曲半径
        if self.radius == '1.0D':
            R = spec['outer']
        elif self.radius == '1.5D':
            R = spec['outer'] * 1.5
        else:
            R = spec['outer'] * 1.5
        # 弧长
        arc = math.pi * R * self.angle / 180
        return round(arc, 2)

    def get_end_positions(self) -> Dict[str, Any]:
        """获取两端坐标"""
        return {
            'start': self.layer['l3_dynamic_state']['起始端坐标'],
            'end': self.layer['l3_dynamic_state']['终止端坐标'],
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
            'entity_type': '弯头',
            'dn': self.dn,
            'angle': self.angle,
            'radius': self.radius,
            'arc_length': self.calc_arc_length(),
            'layer': self.layer,
        }