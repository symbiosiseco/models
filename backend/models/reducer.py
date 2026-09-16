# -*- coding: utf-8 -*-
"""
变径管实体
受 GPL v3.0 保护

连接两段不同管径的管道。含受力点+接触面。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from config import config


class ReducerEntity(BaseEntity):
    """变径管实体"""

    # 变径管规格
    REDUCER_SPECS = {
        'DN50':  {'outer': 60.3},
        'DN80':  {'outer': 88.9},
        'DN100': {'outer': 114.3},
        'DN150': {'outer': 168.3},
        'DN200': {'outer': 219.1},
    }

    def __init__(self, dn_in: str = 'DN100', dn_out: str = 'DN80',
                 material: str = '镀锌铸铁', position: Optional[Dict] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        # 校验：进出口管径必须不同
        if dn_in == dn_out:
            raise ValueError(f'变径管的进口和出口管径不能相同：{dn_in}')
        if dn_in not in self.REDUCER_SPECS:
            dn_in = 'DN100'
        if dn_out not in self.REDUCER_SPECS:
            dn_out = 'DN80'

        outer_in = self.REDUCER_SPECS[dn_in]['outer']
        outer_out = self.REDUCER_SPECS[dn_out]['outer']
        # 长度 = (外径_in + 外径_out) × 1.5
        length = round((outer_in + outer_out) * 1.5, 2)

        position = position or {'x': 7000, 'y': -150, 'z': 2500}

        # 受力点：变径管中心
        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '变径管中心',
                '方向': 'X+',
                '传力对象': '管道',
                '承重上限': '500kg',
            }
        ]

        # 接触面：两端沟槽
        contact_faces = [
            {
                'id': 'cf_groove_in',
                '类型': '沟槽',
                '位置': {'x': -length / 2, 'y': 0, 'z': 0},
                '法线方向': 'X-',
                '接触对象类型': ['卡箍'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
            {
                'id': 'cf_groove_out',
                '类型': '沟槽',
                '位置': {'x': length / 2, 'y': 0, 'z': 0},
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
            '进口规格': dn_in,
            '出口规格': dn_out,
            '材质': material,
            '进口外径': f'{outer_in}mm',
            '出口外径': f'{outer_out}mm',
            '长度': f'{length}mm',
            '变径方式': '同心变径',
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': max(outer_in, outer_out), 'z': max(outer_in, outer_out)},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '进口端坐标': {'x': position['x'] - length / 2, 'y': position['y'], 'z': position['z']},
            '出口端坐标': {'x': position['x'] + length / 2, 'y': position['y'], 'z': position['z']},
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = {
            '物理规则': {
                '包围盒': {'x': length, 'y': max(outer_in, outer_out), 'z': max(outer_in, outer_out)},
                '最小间距': 100,
                '允许接触': ['卡箍', '管道'],
                '禁止穿透': True,
                '接触方式': '沟槽卡接',
            },
            '受力规则': {
                '自重': '2kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['变径管自重 → 两端沟槽 → 卡箍 → 管道'],
                '承重上限': '500kg',
            },
            '装配规则': {
                '连接对象': ['卡箍', '管道'],
                '拧紧力矩': '2.5-3.5N·m',
                '装配顺序': ['橡胶圈放入', '两端对齐', '卡箍扣合', '螺栓拧紧'],
                '密封等级': 'PN16',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '维护空间': 100,
                '检查周期': '每年1次',
                '禁止场景': '重力排水管（坡度要求）',
            },
        }

        super().__init__(
            entity_type='变径管',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn_in = dn_in
        self.dn_out = dn_out
        self.length = length
        self.system = system
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = f'{dn_in}→{dn_out}'

    def get_end_positions(self) -> Dict[str, Any]:
        """获取两端坐标"""
        return {
            'in': self.layer['l3_dynamic_state']['进口端坐标'],
            'out': self.layer['l3_dynamic_state']['出口端坐标'],
        }

    def calc_length(self) -> float:
        """计算变径管长度"""
        return self.length

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
            'entity_type': '变径管',
            'dn_in': self.dn_in,
            'dn_out': self.dn_out,
            'length': self.length,
            'layer': self.layer,
        }