# -*- coding: utf-8 -*-
"""
边界计算引擎
受 GPL v3.0 保护

自动计算包围盒、锚点、受力点、接触面。
"""

import math
from typing import Dict, Any, List
from .ai_connector import AIConnector


class BoundaryCalculator:
    """边界计算引擎"""

    # 螺栓孔分布圆直径系数
    PCD_RATIO = 0.85

    # 规格→螺栓孔数
    BOLT_COUNT_MAP = {
        'DN50': 4, 'DN80': 4, 'DN100': 8, 'DN150': 8, 'DN200': 12,
    }

    # 规格→孔径
    HOLE_DIAMETER_MAP = {
        'DN50': 18, 'DN80': 18, 'DN100': 18, 'DN150': 22, 'DN200': 22,
    }

    def __init__(self):
        self.ai = AIConnector()

    # ==================== 主入口 ====================

    def calc_all(self, product: Dict[str, Any],
                 params: Dict[str, Any]) -> Dict[str, Any]:
        """计算所有边界"""
        return {
            '包围盒': self.calc_bounding_box(params),
            '锚点': self.calc_anchors(product, params),
            '受力点': self.calc_force_points(product, params),
            '接触面': self.calc_contact_faces(product, params),
        }

    # ==================== 包围盒 ====================

    def calc_bounding_box(self, params: Dict[str, Any]) -> Dict[str, float]:
        """计算包围盒"""
        def parse(val, default=100.0):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace('mm', '').strip())
                except ValueError:
                    return default
            return default

        length = parse(params.get('长度', params.get('外径', 100)), 100)
        outer = parse(params.get('外径', params.get('宽度', 100)), 100)
        thickness = parse(params.get('厚度', params.get('高度', outer)), outer)

        # 特殊处理：管道长度为标准长度
        if params.get('标准长度'):
            length = parse(params['标准长度'], 6000)

        return {'x': length, 'y': outer, 'z': thickness}

    # ==================== 锚点 ====================

    def calc_anchors(self, product: Dict[str, Any],
                     params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算锚点（螺栓孔位置、孔径）"""
        ptype = self.ai._guess_type(product.get('产品名称', ''))
        spec = product.get('规格', product.get('产品型号', ''))

        if ptype in ('阀门', '法兰'):
            return self._derive_anchor_positions(ptype, spec, params)
        return []

    def _derive_anchor_positions(self, product_type: str, spec: str,
                                  params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """推导锚点位置"""
        # 从规格提取DN
        dn = 'DN100'
        for key in ['DN50', 'DN80', 'DN100', 'DN150', 'DN200']:
            if key in str(spec):
                dn = key
                break

        count = self.BOLT_COUNT_MAP.get(dn, 8)
        hole_d = self.HOLE_DIAMETER_MAP.get(dn, 18)
        outer = float(params.get('外径', 220) or 220)
        pcd = outer * self.PCD_RATIO

        anchors = []
        for i in range(count):
            angle = 2 * math.pi * i / count
            anchors.append({
                'id': f'bolt_hole_{i + 1}',
                '类型': '螺栓孔',
                '孔径': hole_d,
                '位置': {
                    'x': 0,
                    'y': round(pcd / 2 * math.cos(angle), 2),
                    'z': round(pcd / 2 * math.sin(angle), 2),
                },
                '用途': f'穿M16螺栓',
            })
        return anchors

    # ==================== 受力点 ====================

    def calc_force_points(self, product: Dict[str, Any],
                          params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算受力点"""
        ptype = self.ai._guess_type(product.get('产品名称', ''))
        outer = float(params.get('外径', 220) or 220)
        length = float(params.get('长度', 280) or 280)

        if ptype == '阀门':
            return [{
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': -outer / 2},
                '类型': '法兰面承压',
                '方向': 'Z-',
                '传力对象': '管道',
                '承重上限': '500kg',
            }]
        elif ptype == '法兰':
            return [{
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '法兰面承压',
                '方向': 'X+',
                '传力对象': '螺栓',
                '承重上限': '500kg',
            }]
        elif ptype == '膨胀螺栓':
            return [{
                'id': 'fp_axis',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '螺杆中轴',
                '方向': 'Z-',
                '传力对象': '楼板',
                '承重上限': '400kg',
            }]
        elif ptype == '卡箍':
            return [{
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '卡箍中心',
                '方向': 'X+',
                '传力对象': '管道',
                '承重上限': '500kg',
            }]
        elif ptype == '承重支架':
            return [{
                'id': 'fp_beam_top',
                '位置': {'x': 0, 'y': 0, 'z': 150},
                '类型': '横梁顶面承压',
                '方向': 'Z-',
                '传力对象': '管道',
                '承重上限': '500kg',
            }]
        elif ptype == '镀锌钢管':
            return [{
                'id': 'fp_support_contact',
                '位置': {'x': 0, 'y': 0, 'z': -outer / 2},
                '类型': '支架接触点',
                '方向': 'Z-',
                '传力对象': '支架',
                '承重上限': '500kg',
            }]
        elif ptype == '橡胶圈':
            return [{
                'id': 'fp_center',
                '位置': {'x': 0, 'y': 0, 'z': 0},
                '类型': '垫片中心',
                '方向': 'X+',
                '传力对象': '法兰',
                '承重上限': '500kg',
            }]

        return []

    # ==================== 接触面 ====================

    def calc_contact_faces(self, product: Dict[str, Any],
                           params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算接触面"""
        ptype = self.ai._guess_type(product.get('产品名称', ''))
        outer = float(params.get('外径', 220) or 220)
        length = float(params.get('长度', 280) or 280)
        thickness = float(params.get('厚度', 24) or 24)

        if ptype == '阀门':
            return [
                {'id': 'cf_flange_left', '类型': '法兰面', '位置': {'x': -length / 2, 'y': 0, 'z': 0}, '法线方向': 'X-', '接触对象类型': ['垫片'], '允许偏差': '0mm', '必须包含': ['垫片'], '违反后果': '漏水', '装配顺序': 1},
                {'id': 'cf_flange_right', '类型': '法兰面', '位置': {'x': length / 2, 'y': 0, 'z': 0}, '法线方向': 'X+', '接触对象类型': ['垫片'], '允许偏差': '0mm', '必须包含': ['垫片'], '违反后果': '漏水', '装配顺序': 1},
            ]
        elif ptype == '法兰':
            return [
                {'id': 'cf_face_left', '类型': '法兰面', '位置': {'x': -thickness / 2, 'y': 0, 'z': 0}, '法线方向': 'X-', '接触对象类型': ['垫片'], '允许偏差': '0mm', '必须包含': ['垫片'], '违反后果': '漏水', '装配顺序': 1},
                {'id': 'cf_face_right', '类型': '法兰面', '位置': {'x': thickness / 2, 'y': 0, 'z': 0}, '法线方向': 'X+', '接触对象类型': ['垫片'], '允许偏差': '0mm', '必须包含': ['垫片'], '违反后果': '漏水', '装配顺序': 1},
            ]
        elif ptype == '膨胀螺栓':
            return [{'id': 'cf_shaft', '类型': '螺杆外表面', '位置': {'x': 0, 'y': 0, 'z': 0}, '法线方向': 'Z-', '接触对象类型': ['钻孔'], '允许偏差': '0mm', '必须包含': [], '违反后果': '固定不牢', '装配顺序': 1}]
        elif ptype == '卡箍':
            return [
                {'id': 'cf_inner_groove', '类型': '内壁沟槽', '位置': {'x': 0, 'y': 0, 'z': 0}, '法线方向': 'X+', '接触对象类型': ['管道'], '允许偏差': '0mm', '必须包含': ['橡胶圈'], '违反后果': '漏水', '装配顺序': 1},
                {'id': 'cf_inner_ring', '类型': '内壁', '位置': {'x': 0, 'y': 0, 'z': 0}, '法线方向': 'X+', '接触对象类型': ['橡胶圈'], '允许偏差': '0mm', '必须包含': [], '违反后果': '漏水', '装配顺序': 1},
            ]
        elif ptype == '承重支架':
            return [
                {'id': 'cf_beam_top', '类型': '横梁顶面', '位置': {'x': 0, 'y': 0, 'z': 150}, '法线方向': 'Z+', '接触对象类型': ['管道'], '允许偏差': '0mm', '必须包含': [], '违反后果': '掉落', '装配顺序': 2},
                {'id': 'cf_plate_bottom', '类型': '底板底面', '位置': {'x': 0, 'y': 0, 'z': -150}, '法线方向': 'Z-', '接触对象类型': ['楼板'], '允许偏差': '0mm', '必须包含': [], '违反后果': '固定不牢', '装配顺序': 1},
            ]
        elif ptype == '镀锌钢管':
            return [
                {'id': 'cf_groove_start', '类型': '沟槽', '位置': {'x': -length / 2, 'y': 0, 'z': 0}, '法线方向': 'X-', '接触对象类型': ['卡箍'], '允许偏差': '0mm', '必须包含': ['橡胶圈'], '违反后果': '漏水', '装配顺序': 1},
                {'id': 'cf_groove_end', '类型': '沟槽', '位置': {'x': length / 2, 'y': 0, 'z': 0}, '法线方向': 'X+', '接触对象类型': ['卡箍'], '允许偏差': '0mm', '必须包含': ['橡胶圈'], '违反后果': '漏水', '装配顺序': 1},
                {'id': 'cf_bottom', '类型': '管道底面', '位置': {'x': 0, 'y': 0, 'z': -outer / 2}, '法线方向': 'Z-', '接触对象类型': ['支架'], '允许偏差': '0mm', '必须包含': [], '违反后果': '掉落', '装配顺序': 2},
            ]
        elif ptype == '橡胶圈':
            return [
                {'id': 'cf_gasket_left', '类型': '垫片左面', '位置': {'x': -thickness / 2, 'y': 0, 'z': 0}, '法线方向': 'X-', '接触对象类型': ['法兰'], '允许偏差': '0mm', '必须包含': [], '违反后果': '漏水', '装配顺序': 1},
                {'id': 'cf_gasket_right', '类型': '垫片右面', '位置': {'x': thickness / 2, 'y': 0, 'z': 0}, '法线方向': 'X+', '接触对象类型': ['法兰'], '允许偏差': '0mm', '必须包含': [], '违反后果': '漏水', '装配顺序': 1},
            ]
        return []