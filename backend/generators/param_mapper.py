# -*- coding: utf-8 -*-
"""
参数映射引擎
受 GPL v3.0 保护

把厂家参数映射到六层架构。
"""

from typing import Dict, Any, Optional
from datetime import datetime


class ParamMapper:
    """参数映射引擎"""

    def __init__(self):
        pass

    # ==================== R层映射 ====================

    def map_to_r_layer(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """厂家参数→R层（类别/厂家/模板）"""
        return {
            '类别': product.get('产品名称', ''),
            '规则组': product.get('category', '物品') + '管理规则组',
            '厂家': product.get('厂家', ''),
            '模板ID': product.get('template_id', ''),
            '模板名': product.get('产品名称', ''),
            '类型': product.get('产品型号', ''),
        }

    # ==================== L1层映射 ====================

    def map_to_l1_identity(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """厂家参数→L1层（唯一ID）"""
        return {
            '唯一ID': product.get('entity_id', ''),
            '存在锚点': '不可替换',
            '模板ID': product.get('template_id', ''),
        }

    # ==================== L2层映射 ====================

    def map_to_l2_static(self, product: Dict[str, Any],
                         params: Dict[str, Any],
                         anchors: Optional[list] = None,
                         force_points: Optional[list] = None,
                         contact_faces: Optional[list] = None) -> Dict[str, Any]:
        """厂家参数→L2层（外形/锚点/受力点/接触面）"""
        l2 = dict(params)
        l2['锚点'] = anchors or []
        l2['受力点'] = force_points or []
        l2['接触面'] = contact_faces or []
        l2['包围盒'] = self._calc_bbox(params)
        return l2

    # ==================== L3层映射 ====================

    def map_to_l3_dynamic(self, product: Dict[str, Any],
                          position: Optional[Dict] = None) -> Dict[str, Any]:
        """位置→L3层（绝对坐标/状态）"""
        position = position or {'x': 0, 'y': 0, 'z': 0}
        return {
            '绝对坐标': position,
            '状态': '待装配',
            '受力点实时坐标': [],
        }

    # ==================== L4层映射 ====================

    def map_to_l4_events(self, product: Dict[str, Any]) -> list:
        """时间→L4层（初始事件）"""
        return [
            {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'event': '实体创建',
                'detail': f'由 {product.get("厂家", "未知厂家")} 创建',
            }
        ]

    # ==================== CBM层映射 ====================

    def map_to_cbm(self, product: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """规则→CBM层"""
        return dict(rules) if rules else {}

    # ==================== 参数到字段映射 ====================

    def _map_params_to_fields(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """参数到字段映射（标准化）"""
        # 支持标准字段名 + 厂家自定义字段名
        field_mapping = {
            'outer_diameter': '外径',
            'outer': '外径',
            'diameter': '直径',
            'length': '长度',
            'weight': '重量',
            'material': '材质',
            'width': '宽度',
            'height': '高度',
            'thickness': '厚度',
            'pressure': '工作压力',
        }
        result = {}
        for k, v in params.items():
            standard_key = field_mapping.get(k, k)
            result[standard_key] = v
        return result

    # ==================== 包围盒计算 ====================

    def _calc_bbox(self, params: Dict[str, Any]) -> Dict[str, float]:
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
        return {'x': length, 'y': outer, 'z': thickness}