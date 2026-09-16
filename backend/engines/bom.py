# -*- coding: utf-8 -*-
"""
BOM引擎
受 GPL v3.0 保护

物料清单计算。
阀门主材+辅材；管道10米=6+4+卡箍。
"""

from typing import Dict, Any, List, Optional
from .event_bus import EventBus


class BOMEngine:
    """BOM引擎"""

    # 单位映射
    UNIT_MAP = {
        '管道': 'm', '支架': '个', '阀门': '个', '卡箍': '个',
        '法兰': '个', '螺栓': '套', '垫片': '个', '套管': '个',
        '弯头': '个', '三通': '个',
    }

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()

    # ==================== 主入口 ====================

    def generate_bom(self, entities: List) -> Dict[str, Any]:
        """生成BOM清单"""
        items: List[Dict[str, Any]] = []
        total_amount = 0.0

        # 按类别分组
        by_category = self.get_by_category(entities)
        for category, lst in by_category.items():
            quantity = self.calculate_quantity(lst, category)
            unit = self.UNIT_MAP.get(category, '个')
            items.append({
                'category': category,
                'quantity': quantity,
                'unit': unit,
                'count': len(lst),
            })

        return {
            'items': items,
            'total': len(items),
        }

    def get_by_category(self, entities: List) -> Dict[str, List]:
        """按类别分组"""
        groups: Dict[str, List] = {}
        for e in entities:
            etype = getattr(e, 'entity_type', '未知')
            groups.setdefault(etype, []).append(e)
        return groups

    def calculate_quantity(self, entities: List, category: str) -> float:
        """计算某类别工程量"""
        total = 0.0
        for e in entities:
            if category == '管道':
                if hasattr(e, 'layer'):
                    length_mm = e.layer.get('l3_dynamic_state', {}).get('长度', 10000)
                    total += float(length_mm) / 1000
                else:
                    total += 10.0
            else:
                total += 1.0
        return round(total, 2)

    # ==================== 阀门BOM ====================

    def get_valve_bom(self, valve_entity) -> Dict[str, Any]:
        """获取阀门BOM（主材+辅材）"""
        return {
            'main': [
                {'name': '阀体', 'spec': 'DN100', 'quantity': 1, 'unit': '个'},
                {'name': '手轮', 'spec': 'Φ200', 'quantity': 1, 'unit': '个'},
                {'name': '阀杆', 'spec': 'Φ20×130', 'quantity': 1, 'unit': '个'},
            ],
            'aux': [
                {'name': '法兰', 'spec': 'DN100 PN16', 'quantity': 2, 'unit': '个'},
                {'name': '垫片', 'spec': 'DN100 δ3', 'quantity': 2, 'unit': '个'},
                {'name': '螺栓', 'spec': 'M16×80', 'quantity': 16, 'unit': '套'},
                {'name': '螺母', 'spec': 'M16', 'quantity': 16, 'unit': '个'},
                {'name': '垫圈', 'spec': 'M16', 'quantity': 16, 'unit': '个'},
            ],
        }

    # ==================== 管道BOM ====================

    def get_pipe_bom(self, pipe_entity) -> Dict[str, Any]:
        """获取管道BOM（管道+卡箍+弯头）"""
        # 简化：假设10米管道
        length_mm = 10000
        if hasattr(pipe_entity, 'layer'):
            length_mm = pipe_entity.layer.get('l3_dynamic_state', {}).get('长度', 10000)

        # 分段计算
        segments = []
        remaining = length_mm
        while remaining > 6000:
            segments.append(6000)
            remaining -= 6000
        if remaining > 0:
            segments.append(remaining)

        clamps_count = len(segments) - 1

        return {
            'pipe': [
                {'name': '镀锌钢管', 'spec': 'DN100', 'quantity': round(length_mm / 1000, 2), 'unit': 'm'},
            ],
            'clamps': [
                {'name': '沟槽卡箍', 'spec': 'DN100', 'quantity': max(0, clamps_count), 'unit': '个'},
            ],
            'elbows': [
                {'name': '弯头', 'spec': 'DN100 90°', 'quantity': 0, 'unit': '个'},
            ],
        }

    # ==================== 支架BOM ====================

    def get_support_bom(self, support_entity) -> Dict[str, Any]:
        """获取支架BOM"""
        return {
            'main': [
                {'name': '横担', 'spec': 'L50×50×6', 'quantity': 1, 'unit': '个'},
                {'name': '立杆', 'spec': 'L50×50×6', 'quantity': 1, 'unit': '个'},
                {'name': '底板', 'spec': '100×100×8', 'quantity': 1, 'unit': '个'},
            ],
            'aux': [
                {'name': '膨胀螺栓', 'spec': 'M12×100', 'quantity': 2, 'unit': '套'},
                {'name': 'U型管卡', 'spec': 'DN100 M12', 'quantity': 1, 'unit': '个'},
                {'name': '橡胶垫', 'spec': 'δ3', 'quantity': 1, 'unit': '个'},
            ],
        }

    # ==================== 事件发布 ====================

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}