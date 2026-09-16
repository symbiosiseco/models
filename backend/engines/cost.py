# -*- coding: utf-8 -*-
"""
造价引擎
受 GPL v3.0 保护

清单量vs实际量对比，自动生成签证。
"""

from typing import Dict, Any, List
from datetime import datetime


class CostEngine:
    """造价引擎"""

    # 单价表（元/单位）
    UNIT_PRICES = {
        '管道': 850,
        '支架': 120,
        '综合支架': 200,
        '阀门': 680,
        '卡箍': 85,
        '套管': 200,
        '法兰': 120,
        '螺栓': 5,
        '垫片': 8,
        '风管': 180,
        '桥架': 150,
    }

    # 差异阈值
    DIFF_PERCENT_THRESHOLD = 5.0   # 5%
    DIFF_AMOUNT_THRESHOLD = 100.0  # 100元

    def __init__(self, event_bus=None, config_obj=None):
        self.event_bus = event_bus
        self.config = config_obj
        self.summary = {'total': 0, 'by_category': {}, 'visaCount': 0}
        self.visas: List[Dict[str, Any]] = []

    # ==================== 主入口 ====================

    def generate_from_entities(self, entities: List) -> Dict[str, Any]:
        """从实体列表生成造价"""
        by_category: Dict[str, Dict[str, Any]] = {}
        total = 0.0

        for e in entities:
            cost = self.calculate_entity_cost(e)
            category = cost['category']
            if category not in by_category:
                by_category[category] = {
                    'quantity': 0,
                    'unit_price': cost['unit_price'],
                    'amount': 0.0,
                }
            by_category[category]['quantity'] += cost['quantity']
            by_category[category]['amount'] += cost['amount']
            total += cost['amount']

        visas = self.check_differences(entities)

        self.summary = {
            'total': round(total, 2),
            'by_category': by_category,
            'visaCount': len(visas),
        }
        return self.summary

    def calculate_entity_cost(self, entity) -> Dict[str, Any]:
        """计算单个实体造价"""
        e_type = getattr(entity, 'entity_type', '')
        handler = {
            '管道': self.calc_pipe_cost,
            '支架': self.calc_support_cost,
            '阀门': self.calc_valve_cost,
            '卡箍': self.calc_clamp_cost,
            '套管': self.calc_sleeve_cost,
        }.get(e_type)

        if handler:
            return handler(entity)

        # 默认处理
        unit_price = self.UNIT_PRICES.get(e_type, 0)
        return {
            'entity_id': getattr(entity, 'id', ''),
            'category': e_type,
            'quantity': 1,
            'unit_price': unit_price,
            'amount': unit_price,
            'difference': 0,
        }

    # ==================== 分类计算 ====================

    def calc_pipe_cost(self, entity) -> Dict[str, Any]:
        """计算管道造价（按米）"""
        length_m = 10.0
        if hasattr(entity, 'layer'):
            length_mm = entity.layer.get('l3_dynamic_state', {}).get('长度', 10000)
            length_m = float(length_mm) / 1000
        unit_price = self.UNIT_PRICES['管道']
        return {
            'entity_id': getattr(entity, 'id', ''),
            'category': '管道',
            'quantity': round(length_m, 2),
            'unit_price': unit_price,
            'amount': round(length_m * unit_price, 2),
            'difference': 0,
        }

    def calc_support_cost(self, entity) -> Dict[str, Any]:
        """计算支架造价（按个）"""
        unit_price = self.UNIT_PRICES['支架']
        return {
            'entity_id': getattr(entity, 'id', ''),
            'category': '支架',
            'quantity': 1,
            'unit_price': unit_price,
            'amount': unit_price,
            'difference': 0,
        }

    def calc_valve_cost(self, entity) -> Dict[str, Any]:
        """计算阀门造价（按个）"""
        unit_price = self.UNIT_PRICES['阀门']
        return {
            'entity_id': getattr(entity, 'id', ''),
            'category': '阀门',
            'quantity': 1,
            'unit_price': unit_price,
            'amount': unit_price,
            'difference': 0,
        }

    def calc_clamp_cost(self, entity) -> Dict[str, Any]:
        """计算卡箍造价（按个）"""
        unit_price = self.UNIT_PRICES['卡箍']
        return {
            'entity_id': getattr(entity, 'id', ''),
            'category': '卡箍',
            'quantity': 1,
            'unit_price': unit_price,
            'amount': unit_price,
            'difference': 0,
        }

    def calc_sleeve_cost(self, entity) -> Dict[str, Any]:
        """计算套管造价（按个）"""
        unit_price = self.UNIT_PRICES['套管']
        return {
            'entity_id': getattr(entity, 'id', ''),
            'category': '套管',
            'quantity': 1,
            'unit_price': unit_price,
            'amount': unit_price,
            'difference': 0,
        }

    # ==================== 差异检查 ====================

    def check_differences(self, entities: List) -> List[Dict[str, Any]]:
        """检查差异，生成签证"""
        visas = []
        for e in entities:
            list_qty = self._get_list_quantity(e)
            actual_qty = self._get_actual_quantity(e)
            if list_qty == 0:
                continue

            diff = actual_qty - list_qty
            unit_price = self.UNIT_PRICES.get(getattr(e, 'entity_type', ''), 0)
            diff_amount = diff * unit_price

            # 判断是否超阈值
            percent = abs(diff) / list_qty * 100 if list_qty > 0 else 0
            exceeds = (
                percent > self.DIFF_PERCENT_THRESHOLD or
                abs(diff_amount) > self.DIFF_AMOUNT_THRESHOLD
            )

            if exceeds:
                visa = {
                    'entity_id': getattr(e, 'id', ''),
                    'category': getattr(e, 'entity_type', ''),
                    'list_quantity': list_qty,
                    'actual_quantity': actual_qty,
                    'difference': round(diff, 2),
                    'difference_amount': round(diff_amount, 2),
                    'reason': '实际量超清单量' if diff > 0 else '实际量少于清单量',
                    'status': '待确认',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                visas.append(visa)

                # 通过事件总线发布
                if self.event_bus:
                    self.event_bus.publish('签证生成', {
                        'visa_id': f'VISA-{len(visas):03d}',
                        'entity_id': visa['entity_id'],
                        'difference': visa['difference'],
                    })

        self.visas = visas
        return visas

    def _get_list_quantity(self, entity) -> float:
        """获取清单量"""
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            if '清单量' in l2:
                return float(l2['清单量'])
            if entity.entity_type == '管道':
                return 4.8  # 演示用
        return 1.0

    def _get_actual_quantity(self, entity) -> float:
        """获取实际量"""
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            if '实际量' in l2:
                return float(l2['实际量'])
            if entity.entity_type == '管道':
                return 5.0  # 演示用
        return 1.0

    # ==================== 查询/更新 ====================

    def get_summary(self) -> Dict[str, Any]:
        """获取造价汇总"""
        return self.summary

    def get_details(self) -> List[Dict[str, Any]]:
        """获取造价明细"""
        return [v for v in self.visas]

    def update_cost(self, entity_id: str, new_status: str) -> Dict[str, Any]:
        """更新造价状态"""
        for visa in self.visas:
            if visa['entity_id'] == entity_id:
                visa['status'] = new_status
                return {'success': True, 'entity_id': entity_id, 'status': new_status}
        return {'success': False, 'message': '未找到对应签证'}