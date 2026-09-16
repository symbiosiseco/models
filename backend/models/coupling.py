# -*- coding: utf-8 -*-
"""
联轴器实体
受 GPL v3.0 保护

连接两段同管径的管道。含受力点+接触面。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from config import config


class CouplingEntity(BaseEntity):
    """联轴器实体"""

    # 联轴器规格
    COUPLING_SPECS = {
        'DN50':  {'outer': 88,  'length': 100},
        'DN80':  {'outer': 120, 'length': 120},
        'DN100': {'outer': 140, 'length': 140},
        'DN150': {'outer': 200, 'length': 180},
        'DN200': {'outer': 260, 'length': 220},
    }

    def __init__(self, dn: str = 'DN100', material: str = '镀锌铸铁',
                 position: Optional[Dict] = None, connect_pipes: Optional[List] = None,
                 system: str = '消防给水系统', space: Optional[Dict] = None):
        if dn not in self.COUPLING_SPECS:
            dn = 'DN100'
        spec = self.COUPLING_SPECS[dn]

        position = position or {'x': 3000, 'y': -150, 'z': 2500}
        connect_pipes = connect_pipes or []

        # 受力点：联轴器中心
        force_points = [
            {
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '联轴器中心',
                '方向': 'X+',
                '传力对象': '管道',
                '承重上限': '500kg',
            }
        ]

        # 接触面：两端沟槽
        contact_faces = [
            {
                'id': 'cf_groove_left',
                '类型': '沟槽',
                '位置': {'x': -spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X-',
                '接触对象类型': ['管道'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
            {
                'id': 'cf_groove_right',
                '类型': '沟槽',
                '位置': {'x': spec['length'] / 2, 'y': 0, 'z': 0},
                '法线方向': 'X+',
                '接触对象类型': ['管道'],
                '允许偏差': '0mm',
                '必须包含': ['橡胶圈'],
                '违反后果': '漏水',
                '装配顺序': 1,
            },
        ]

        # L2层
        l2 = {
            '规格': dn,
            '材质': material,
            '外径': f'{spec["outer"]}mm',
            '长度': f'{spec["length"]}mm',
            '连接管道': connect_pipes,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': spec['length'], 'y': spec['outer'], 'z': spec['outer']},
        }

        # L3层
        l3 = {
            '绝对坐标': position,
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = {
            '物理规则': {
                '包围盒': {'x': spec['length'], 'y': spec['outer'], 'z': spec['outer']},
                '最小间距': 50,
                '允许接触': ['管道'],
                '禁止穿透': True,
                '接触方式': '沟槽卡接',
            },
            '受力规则': {
                '自重': '1.5kg',
                '受力点': {'x': 0, 'y': 0, 'z': 0},
                '传力路径': ['管道轴向力 → 联轴器 → 两段管道连接'],
                '承重上限': '500kg',
            },
            '装配规则': {
                '连接对象': ['管道'],
                '拧紧力矩': '2.5-3.5N·m',
                '装配顺序': ['橡胶圈放入', '两段管道对齐', '联轴器扣合', '螺栓拧紧'],
                '密封等级': 'PN16',
            },
            '规范约束': {
                '安装规范': 'GB 50242',
                '维护空间': 100,
                '检查周期': '每年1次',
                '管径要求': '两端必须同管径',
            },
        }

        super().__init__(
            entity_type='联轴器',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=position,
        )

        self.dn = dn
        self.system = system
        self.connect_pipes = list(connect_pipes)
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = dn

    def check_dn_match(self, pipe1_dn: str, pipe2_dn: str) -> bool:
        """检查两段管道管径是否一致"""
        return pipe1_dn == pipe2_dn

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
            'entity_type': '联轴器',
            'dn': self.dn,
            'connect_pipes': self.connect_pipes,
            'layer': self.layer,
        }