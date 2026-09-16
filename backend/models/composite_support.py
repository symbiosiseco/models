# -*- coding: utf-8 -*-
"""
综合支架实体
受 GPL v3.0 保护

承载多专业管道。含受力点+接触面。
注意：重力排水管不能放入综合支架（坡度要求）。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from config import config


class CompositeSupportEntity(BaseEntity):
    """综合支架实体"""

    # 规格
    COMPOSITE_SPECS = {
        '综合支架': {
            '规格': '槽钢10#',
            '材质': 'Q235B',
            '总承重': '1000kg',
            '总重量': '12kg',
        },
    }

    def __init__(self, index: int = 0, support_type: str = '综合支架',
                 x_pos: Optional[float] = None, pipes: Optional[List] = None,
                 space: Optional[Dict] = None):
        if x_pos is None:
            x_pos = 1000 + index * 2000

        spec = self.COMPOSITE_SPECS.get(support_type, self.COMPOSITE_SPECS['综合支架'])
        pipes = pipes or []

        # 受力点：槽钢顶面中心
        force_points = [
            {
                'id': 'fp_beam_top',
                '位置': {'x': 0, 'y': 0, 'z': 200},
                '类型': '槽钢顶面承压',
                '方向': 'Z-',
                '传力对象': '管道',
                '承重上限': spec['总承重'],
            }
        ]

        # 接触面：槽钢顶面（多专业管道）+ 底板底面（楼板）
        contact_faces = [
            {
                'id': 'cf_beam_top',
                '类型': '槽钢顶面',
                '位置': {'x': 0, 'y': 0, 'z': 200},
                '法线方向': 'Z+',
                '接触对象类型': ['管道'],
                '允许偏差': '0mm',
                '必须包含': [],
                '违反后果': '掉落',
                '装配顺序': 2,
            },
            {
                'id': 'cf_plate_bottom',
                '类型': '底板底面',
                '位置': {'x': 0, 'y': 0, 'z': -200},
                '法线方向': 'Z-',
                '接触对象类型': ['楼板'],
                '允许偏差': '0mm',
                '必须包含': [],
                '违反后果': '固定不牢',
                '装配顺序': 1,
            },
        ]

        # L2层
        l2 = {
            '类型': support_type,
            '规格': spec['规格'],
            '材质': spec['材质'],
            '承载管道': [],
            '总承重': spec['总承重'],
            '总重量': spec['总重量'],
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': 200, 'y': 600, 'z': 400},
        }

        # L3层
        l3 = {
            '绝对坐标': {'x': x_pos, 'y': -100, 'z': 2500},
            '承载管道列表': [],
            '受力点实时坐标': [],
        }

        # CBM层：多专业综合受力
        cbm = {
            '物理规则': {
                '包围盒': {'x': 200, 'y': 600, 'z': 400},
                '最小间距': 100,
                '允许接触': ['管道', '楼板'],
                '禁止穿透': True,
                '接触方式': '槽钢顶面承压',
            },
            '受力规则': {
                '自重': spec['总重量'],
                '传力路径': ['多专业管道载荷 → 槽钢 → 立杆 → 底板 → 膨胀螺栓 → 楼板'],
                '承重上限': spec['总承重'],
            },
            '装配规则': {
                '连接对象': ['管道', '楼板'],
                '拧紧力矩': '40N·m',
                '装配顺序': ['测楼板高度', '底板固定', '立杆焊接', '槽钢焊接'],
                '密封等级': '无',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '支架间距': 3000,
                '维护空间': 500,
                '检查周期': '每年1次',
                '禁止承载': ['重力排水管'],  # 坡度要求
            },
        }

        super().__init__(
            entity_type='综合支架',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position={'x': x_pos, 'y': -100, 'z': 2500},
        )

        self.index = index
        self.support_type = support_type
        self.x_pos = x_pos
        self.pipes = list(pipes)
        self.space = space or config.SPACE_UNITS

        # 添加初始管道
        for pipe in pipes:
            self.add_pipe(pipe)

    def add_pipe(self, pipe: Any) -> Dict[str, Any]:
        """
        添加承载管道。

        规则：重力排水管不能放入综合支架（坡度要求）。
        """
        pipe_id = pipe.id if hasattr(pipe, 'id') else str(pipe)
        pipe_type = getattr(pipe, 'entity_type', '')
        pipe_system = pipe.layer.get('r_layer', {}).get('系统', '') if hasattr(pipe, 'layer') else ''

        # 检查重力排水管
        if '重力排水' in pipe_system or '重力排水' in pipe_type:
            return {
                'success': False,
                'message': '重力排水管不能放入综合支架（坡度要求）',
            }

        self.layer['l2_static_attributes']['承载管道'].append(pipe_id)
        self.layer['l3_dynamic_state']['承载管道列表'].append(pipe_id)
        self.pipes.append(pipe)

        return {'success': True, 'pipe_id': pipe_id}

    def calc_total_load(self) -> Dict[str, Any]:
        """计算所有管道的总载荷"""
        total = 0.0
        for pipe in self.pipes:
            weight_str = pipe.layer.get('l2_static_attributes', {}).get('总重量', '0kg') if hasattr(pipe, 'layer') else '0kg'
            try:
                total += float(str(weight_str).replace('kg', ''))
            except (ValueError, TypeError):
                pass
        return {
            'total_load': round(total, 2),
            'pipe_count': len(self.pipes),
            'capacity': self.layer['l2_static_attributes']['总承重'],
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
            'entity_type': '综合支架',
            'index': self.index,
            'x_pos': self.x_pos,
            'pipes': [p.id if hasattr(p, 'id') else str(p) for p in self.pipes],
            'layer': self.layer,
        }