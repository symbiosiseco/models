# -*- coding: utf-8 -*-
"""
报表引擎
受 GPL v3.0 保护

从模型自动衍生8种报表。
从实体的L2/L3/L4自动汇总。
"""

from typing import Dict, Any, List
from datetime import datetime
from .event_bus import EventBus


class ReportEngine:
    """报表引擎"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()

    # ==================== 1. 工程量清单 ====================

    def generate_quantity_report(self, entities: List) -> Dict[str, Any]:
        """生成工程量清单"""
        groups: Dict[str, Dict[str, Any]] = {}
        unit_prices = {'管道': 850, '支架': 120, '阀门': 680, '卡箍': 85, '套管': 200}
        total = 0.0

        for e in entities:
            etype = getattr(e, 'entity_type', '')
            if etype not in unit_prices:
                continue
            if etype not in groups:
                groups[etype] = {
                    'category': etype,
                    'quantity': 0,
                    'unit': self._get_unit(etype),
                    'unit_price': unit_prices[etype],
                    'amount': 0.0,
                }
            qty = self._get_quantity(e)
            groups[etype]['quantity'] += qty
            amount = qty * unit_prices[etype]
            groups[etype]['amount'] += amount
            total += amount

        return {
            'report_type': '工程量清单',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': list(groups.values()),
            'total': round(total, 2),
        }

    # ==================== 2. 进度款申请 ====================

    def generate_payment_report(self, entities: List) -> Dict[str, Any]:
        """生成进度款申请"""
        completed_entities = [e for e in entities if self._is_completed(e)]
        total_amount = 0.0
        items = []

        unit_prices = {'管道': 850, '支架': 120, '阀门': 680, '卡箍': 85}
        for e in completed_entities:
            etype = getattr(e, 'entity_type', '')
            unit_price = unit_prices.get(etype, 0)
            if unit_price == 0:
                continue
            qty = self._get_quantity(e)
            amount = qty * unit_price
            total_amount += amount
            items.append({
                'entity_id': getattr(e, 'id', ''),
                'category': etype,
                'quantity': qty,
                'unit_price': unit_price,
                'amount': round(amount, 2),
            })

        return {
            'report_type': '进度款申请',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': items,
            'total': round(total_amount, 2),
        }

    # ==================== 3. 验收记录 ====================

    def generate_acceptance_report(self, entities: List) -> Dict[str, Any]:
        """生成验收记录"""
        records = []
        for e in entities:
            status = self._get_status(e)
            if status in ('已验收', '已安装'):
                records.append({
                    'entity_id': getattr(e, 'id', ''),
                    'entity_type': getattr(e, 'entity_type', ''),
                    'status': status,
                    'accepted_at': self._get_status(e, '验收时间'),
                })
        return {
            'report_type': '验收记录',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'records': records,
            'total': len(records),
        }

    # ==================== 4. 变更台账 ====================

    def generate_change_report(self, entities: List) -> Dict[str, Any]:
        """生成变更台账"""
        changes = []
        for e in entities:
            if getattr(e, 'entity_type', '') != '变更':
                continue
            l2 = self._get_l2(e)
            changes.append({
                'change_id': getattr(e, 'id', ''),
                'change_type': l2.get('变更类型'),
                'reason': l2.get('变更原因'),
                'before': l2.get('变更前状态'),
                'after': l2.get('变更后状态'),
                'added_cost': l2.get('增加造价'),
            })
        return {
            'report_type': '变更台账',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'records': changes,
            'total': len(changes),
        }

    # ==================== 5. 材料台账 ====================

    def generate_material_report(self, entities: List) -> Dict[str, Any]:
        """生成材料台账"""
        materials: Dict[str, Dict[str, Any]] = {}
        for e in entities:
            etype = getattr(e, 'entity_type', '')
            if etype in ('管道', '支架', '阀门', '卡箍', '套管', '法兰', '螺栓', '垫片'):
                if etype not in materials:
                    materials[etype] = {'category': etype, 'total': 0, 'used': 0, 'remaining': 0}
                qty = self._get_quantity(e)
                materials[etype]['total'] += qty
                if self._is_completed(e):
                    materials[etype]['used'] += qty
                else:
                    materials[etype]['remaining'] += qty

        return {
            'report_type': '材料台账',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': list(materials.values()),
        }

    # ==================== 6. 质量记录 ====================

    def generate_quality_report(self, entities: List) -> Dict[str, Any]:
        """生成质量记录"""
        records = []
        for e in entities:
            l4 = self._get_l4(e)
            for event in l4:
                if '质检' in event.get('event', '') or '质量' in event.get('event', ''):
                    records.append({
                        'entity_id': getattr(e, 'id', ''),
                        'time': event.get('time'),
                        'event': event.get('event'),
                        'detail': event.get('detail'),
                    })
        return {
            'report_type': '质量记录',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'records': records,
            'total': len(records),
        }

    # ==================== 7. 竣工图 ====================

    def generate_asbuilt_report(self, entities: List) -> Dict[str, Any]:
        """生成竣工图（最终状态的三维模型）"""
        items = []
        for e in entities:
            pos = self._get_position(e)
            bbox = self._get_bbox(e)
            items.append({
                'entity_id': getattr(e, 'id', ''),
                'entity_type': getattr(e, 'entity_type', ''),
                'final_position': pos,
                'bounding_box': bbox,
                'final_status': self._get_status(e),
            })
        return {
            'report_type': '竣工图',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': items,
            'total': len(items),
        }

    # ==================== 8. 签证单 ====================

    def generate_visa_report(self, entities: List) -> Dict[str, Any]:
        """生成签证单"""
        visas = []
        for e in entities:
            if getattr(e, 'entity_type', '') != '签证':
                continue
            l2 = self._get_l2(e)
            visas.append({
                'visa_id': getattr(e, 'id', ''),
                'visa_type': l2.get('签证类型'),
                'reason': l2.get('签证原因'),
                'amount': l2.get('金额'),
                'status': self._get_status(e),
            })
        return {
            'report_type': '签证单',
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'records': visas,
            'total': len(visas),
        }

    # ==================== 工具方法 ====================

    def _get_unit(self, etype: str) -> str:
        return {'管道': 'm', '支架': '个', '阀门': '个', '卡箍': '个', '套管': '个'}.get(etype, '个')

    def _get_quantity(self, entity) -> float:
        """获取实体工程量"""
        etype = getattr(entity, 'entity_type', '')
        if etype == '管道':
            if hasattr(entity, 'layer'):
                length_mm = entity.layer.get('l3_dynamic_state', {}).get('长度', 10000)
                return round(float(length_mm) / 1000, 2)
            return 10.0
        return 1.0

    def _get_status(self, entity, key: str = '状态') -> Any:
        if hasattr(entity, 'get_status'):
            return entity.get_status(key, '')
        if hasattr(entity, 'layer'):
            return entity.layer.get('l3_dynamic_state', {}).get(key, '')
        return ''

    def _get_l2(self, entity) -> Dict[str, Any]:
        if hasattr(entity, 'layer'):
            return entity.layer.get('l2_static_attributes', {})
        return {}

    def _get_l4(self, entity) -> List[Dict[str, Any]]:
        if hasattr(entity, 'layer'):
            return entity.layer.get('l4_event_chain', [])
        return []

    def _get_position(self, entity) -> Dict[str, float]:
        if hasattr(entity, 'get_position'):
            return entity.get_position()
        if hasattr(entity, 'layer'):
            return entity.layer.get('l3_dynamic_state', {}).get(
                '绝对坐标', {'x': 0, 'y': 0, 'z': 0}
            )
        return {'x': 0, 'y': 0, 'z': 0}

    def _get_bbox(self, entity) -> Dict[str, float]:
        if hasattr(entity, 'get_bounding_box'):
            return entity.get_bounding_box()
        return self._get_l2(entity).get('包围盒', {'x': 0, 'y': 0, 'z': 0})

    def _is_completed(self, entity) -> bool:
        return self._get_status(entity) in ('已完成', '已安装', '已验收')