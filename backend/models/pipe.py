# -*- coding: utf-8 -*-
"""
管道实体
受 GPL v3.0 保护

镀锌钢管。含受力点+接触面+分段规则。
10米管道 = 6米 + 4米 + 卡箍（真实产品，不是一整条10米）。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import pipe_cbm, pipe_force_points, pipe_contact_faces
from config import config


class PipeEntity(BaseEntity):
    """管道实体"""

    # 管道国标尺寸（GB/T 3091）
    PIPE_SPECS = {
        'DN50':  {'outer': 60.3,  'wall': 3.8, 'weight': 5.3},
        'DN80':  {'outer': 88.9,  'wall': 4.0, 'weight': 8.4},
        'DN100': {'outer': 114.3, 'wall': 4.0, 'weight': 10.9},
        'DN150': {'outer': 168.3, 'wall': 4.5, 'weight': 18.2},
        'DN200': {'outer': 219.1, 'wall': 6.0, 'weight': 31.5},
    }

    # 管道标准长度
    STANDARD_LENGTH = 6000

    def __init__(self, dn: str = 'DN100', material: str = '热浸镀锌钢管',
                 start: Optional[Dict] = None, end: Optional[Dict] = None,
                 manufacturer: str = '钢管厂', system: str = '消防给水系统',
                 space: Optional[Dict] = None):
        # 规格校验
        if dn not in self.PIPE_SPECS:
            dn = 'DN100'
        spec = self.PIPE_SPECS[dn]

        # 默认起终点
        start = start or {'x': 0, 'y': -150, 'z': 2500}
        end = end or {'x': 10000, 'y': -150, 'z': 2500}

        # 计算长度
        length = abs(end['x'] - start['x']) or 10000
        center = {
            'x': (start['x'] + end['x']) / 2,
            'y': (start['y'] + end['y']) / 2,
            'z': (start['z'] + end['z']) / 2,
        }

        # 计算总重量
        total_weight = round(spec['weight'] * length / 1000, 2)

        # 分段规则
        segments = self._calc_segments(length)

        # 受力点
        force_points = pipe_force_points(dn, spec['outer'], length)

        # 接触面
        contact_faces = pipe_contact_faces(dn, spec['outer'], length)

        # L2层
        l2 = {
            '管径': dn,
            '外径': f'{spec["outer"]}mm',
            '壁厚': f'{spec["wall"]}mm',
            '材质': material,
            '连接方式': '沟槽卡箍',
            '单位重量': f'{spec["weight"]}kg/m',
            '总重量': f'{total_weight}kg',
            '防腐': '热浸镀锌',
            '标准长度': f'{self.STANDARD_LENGTH}mm',
            '分段规则': segments,
            '受力点': force_points,
            '接触面': contact_faces,
            '包围盒': {'x': length, 'y': spec['outer'], 'z': spec['outer']},
        }

        # L3层
        l3 = {
            '起点坐标': start,
            '终点坐标': end,
            '中心坐标': center,
            '长度': length,
            '工作压力': '1.6MPa',
            '受力点实时坐标': [],
        }

        # CBM层
        cbm = pipe_cbm(dn, spec['outer'], length)

        super().__init__(
            entity_type='管道',
            manufacturer=manufacturer,
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=center,
        )

        # 附加字段
        self.dn = dn
        self.system = system
        self.length = length
        self.start = start
        self.end = end
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['规格'] = dn
        self.layer['r_layer']['系统'] = system

    def _calc_segments(self, length: float) -> Dict[str, Any]:
        """
        计算管道分段规则。

        规则：
            - 长度 ≤ 6000mm：不分段
            - 长度 > 6000mm：6米 + 余量 + 卡箍
            - 10米 = 6+4
        """
        if length <= self.STANDARD_LENGTH:
            return {
                '总长': f'{length}mm',
                '分段': [{'长度': f'{length}mm', '起点': 0, '终点': length}],
                '连接件': [],
            }

        segs = []
        remaining = length
        pos = 0
        while remaining > self.STANDARD_LENGTH:
            segs.append({'长度': f'{self.STANDARD_LENGTH}mm', '起点': pos, '终点': pos + self.STANDARD_LENGTH})
            pos += self.STANDARD_LENGTH
            remaining -= self.STANDARD_LENGTH
        if remaining > 0:
            segs.append({'长度': f'{remaining}mm', '起点': pos, '终点': pos + remaining})

        # 卡箍位于每段交界处
        clamps = []
        for i in range(len(segs) - 1):
            clamps.append({
                '类型': '卡箍',
                '位置': segs[i]['终点'],
                '含橡胶圈': True,
            })

        return {
            '总长': f'{length}mm',
            '分段': segs,
            '连接件': clamps,
        }

    def get_segments(self) -> List[Dict[str, Any]]:
        """获取管道分段"""
        return self.layer['l2_static_attributes'].get('分段规则', {}).get('分段', [])

    def get_clamps(self) -> List[Dict[str, Any]]:
        """获取卡箍位置"""
        return self.layer['l2_static_attributes'].get('分段规则', {}).get('连接件', [])

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '管道',
            'dn': self.dn,
            'length': self.length,
            'start': self.start,
            'end': self.end,
            'layer': self.layer,
        }