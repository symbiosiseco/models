# -*- coding: utf-8 -*-
"""
供应商场景
受 GPL v3.0 保护

材料供应。
通过事件总线接收订单。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class SupplierScene:
    """供应商场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.stock: Dict[str, int] = {'DN100管道': 100, 'DN100阀门': 10, 'DN100卡箍': 50}
        self.replacements: List[Dict[str, Any]] = []
        self._subscribe_events()

    # ==================== 事件订阅 ====================

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('换货触发', self._on_event, 'supplier')
        self.event_bus.subscribe('订单生成', self._on_event, 'supplier')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        if event_type == '换货触发':
            self.replacements.append({
                'order_id': data.get('order_id'),
                'part_id': data.get('part_id'),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })

    # ==================== 接单 ====================

    def receive_order(self, order_id: str) -> Dict[str, Any]:
        """接单"""
        self.orders[order_id] = {
            'order_id': order_id,
            'status': '已接单',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        if self.event_bus:
            self.event_bus.publish('订单接收', {'order_id': order_id})
        return {'success': True, 'order_id': order_id, 'status': '已接单'}

    # ==================== 查库存 ====================

    def check_stock(self, material_id: str) -> Dict[str, Any]:
        """查库存"""
        stock = self.stock.get(material_id, 0)
        return {
            'material_id': material_id,
            'stock': stock,
            'available': stock > 0,
        }

    # ==================== 发货 ====================

    def ship_order(self, order_id: str, logistics_id: str = '') -> Dict[str, Any]:
        """发货"""
        order = self.orders.get(order_id)
        if not order:
            return {'success': False, 'message': '订单不存在'}
        order['status'] = '已发货'
        order['logistics_id'] = logistics_id
        if self.event_bus:
            self.event_bus.publish('发货', {'order_id': order_id, 'logistics_id': logistics_id})
        return {'success': True, 'order_id': order_id, 'logistics_id': logistics_id, 'status': '已发货'}

    # ==================== 对账 ====================

    def track_payment(self, order_id: str) -> Dict[str, Any]:
        """对账"""
        return {
            'order_id': order_id,
            'amount': 0,
            'status': '待对账',
        }

    # ==================== 处理换货单 ====================

    def handle_replacement(self, order_id: str) -> Dict[str, Any]:
        """处理换货单"""
        replacement_id = f'REPL-{len(self.replacements) + 1:03d}'
        if self.event_bus:
            self.event_bus.publish('换货处理', {
                'order_id': order_id,
                'replacement_id': replacement_id,
            })
        return {
            'success': True,
            'order_id': order_id,
            'replacement_id': replacement_id,
        }

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {
            'role': role,
            'orders': list(self.orders.values()),
            'stock': self.stock,
        }