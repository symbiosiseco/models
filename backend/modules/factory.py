# -*- coding: utf-8 -*-
"""
工厂场景
受 GPL v3.0 保护

生产制造。
调用TaskCBM驱动生产任务。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class FactoryScene:
    """工厂场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.inventory: Dict[str, int] = {}
        self.counter = 0
        self._subscribe_events()

    # ==================== 事件订阅 ====================

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('订单生成', self._on_event, 'factory')
        self.event_bus.subscribe('换货触发', self._on_event, 'factory')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        pass

    # ==================== 接收订单 ====================

    def receive_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """接收订单"""
        self.counter += 1
        order_id = f'ORD-{self.counter:03d}'
        self.orders[order_id] = {
            'order_id': order_id,
            'data': order_data,
            'status': '已接收',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        if self.event_bus:
            self.event_bus.publish('订单接收', {'order_id': order_id})
        return {'success': True, 'order_id': order_id}

    # ==================== 排产 ====================

    def plan_production(self, order_id: str) -> Dict[str, Any]:
        """排产"""
        order = self.orders.get(order_id)
        if not order:
            return {'success': False, 'message': '订单不存在'}
        # 简化：生成任务清单
        tasks = [
            {'task_id': f'TASK-PROD-{order_id}', 'type': '生产', 'status': '待执行'}
        ]
        if self.event_bus:
            self.event_bus.publish('生产任务', {'order_id': order_id, 'tasks': tasks})
        return {'success': True, 'tasks': tasks}

    # ==================== 生产 ====================

    def produce(self, material_id: str) -> Dict[str, Any]:
        """生产"""
        self.counter += 1
        l1_id = f'PROD-{self.counter:04d}'
        # 库存+1
        self.inventory[material_id] = self.inventory.get(material_id, 0) + 1
        if self.event_bus:
            self.event_bus.publish('产品生成', {
                'material_id': material_id,
                'l1_id': l1_id,
            })
        return {'success': True, 'material_id': material_id, 'l1_id': l1_id}

    # ==================== 质检 ====================

    def quality_check(self, material_id: str) -> Dict[str, Any]:
        """质检"""
        # 简化：默认合格
        passed = True
        return {'success': True, 'material_id': material_id, 'passed': passed}

    # ==================== 发货 ====================

    def ship(self, material_id: str, logistics_id: str = '') -> Dict[str, Any]:
        """发货"""
        if material_id in self.inventory and self.inventory[material_id] > 0:
            self.inventory[material_id] -= 1
        if self.event_bus:
            self.event_bus.publish('发货', {
                'material_id': material_id,
                'logistics_id': logistics_id,
            })
        return {'success': True, 'material_id': material_id, 'shipped': True}

    # ==================== 库存查询 ====================

    def get_inventory(self) -> Dict[str, Any]:
        """库存查询"""
        total = sum(self.inventory.values())
        return {
            'total': total,
            'by_category': dict(self.inventory),
        }

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {'role': role, 'orders': list(self.orders.values()), 'inventory': self.inventory}