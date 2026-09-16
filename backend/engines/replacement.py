# -*- coding: utf-8 -*-
"""
替换引擎
受 GPL v3.0 保护

处理厂家参数替换和异常换货。
通过任务CBM触发换货。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class ReplacementEngine:
    """替换引擎"""

    def __init__(self, event_bus: Optional[EventBus] = None, template_store=None):
        self.event_bus = event_bus or EventBus()
        self.template_store = template_store
        self.collision_engine = None
        self.cost_engine = None
        self.history: List[Dict[str, Any]] = []
        self.replacement_orders: List[Dict[str, Any]] = []
        self.counter = 0

    # ==================== 替换实体 ====================

    def replace_entity(self, old_id: str, new_template_id: str,
                        position: Optional[Dict] = None) -> Dict[str, Any]:
        """
        替换实体。

        流程：
            1. 从模板存储器取新模板
            2. 生成新实体
            3. 替换旧实体
            4. 重算碰撞
            5. 重算造价
            6. 写L4
            7. 通过事件总线发布
        """
        if not self.template_store:
            return {'success': False, 'message': '模板存储器未初始化'}

        position = position or {'x': 0, 'y': 0, 'z': 0}

        # 从模板实例化新实体
        try:
            new_entity = self.template_store.instantiate(new_template_id, position)
        except ValueError as e:
            return {'success': False, 'message': str(e)}

        # 重算碰撞
        self._recalc_collision(new_entity)

        # 重算造价
        self._recalc_cost(new_entity)

        # 写L4
        self._update_l4(old_id, '替换', f'替换为 {new_template_id}')

        result = {
            'success': True,
            'old_id': old_id,
            'new_id': new_entity['id'],
            'new_template_id': new_template_id,
        }
        self.history.append({
            **result,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('实体替换', result)

        return result

    # ==================== 处理装配错误 ====================

    def handle_assembly_error(self, part_id: str, target_id: str,
                               error: str) -> Dict[str, Any]:
        """
        处理装配错误。

        流程：
            1. 记录装配失败
            2. 生成换货单
            3. 通过事件总线发布"换货触发"
            4. 通知配送员
        """
        order = self.generate_replacement_order(part_id)

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('换货触发', {
                'order_id': order['order_id'],
                'part_id': part_id,
                'target_id': target_id,
                'error': error,
            })

        return {
            'success': True,
            'order_id': order['order_id'],
            'message': f'装配失败：{error}，已生成换货单',
        }

    # ==================== 生成换货单 ====================

    def generate_replacement_order(self, part_id: str) -> Dict[str, Any]:
        """生成换货单"""
        self.counter += 1
        order_id = f'REPL-{self.counter:03d}'

        order = {
            'order_id': order_id,
            'part_id': part_id,
            'reason': '装配失败，孔径不匹配',
            'status': '待处理',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.replacement_orders.append(order)

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('换货单生成', order)

        return order

    # ==================== 查询 ====================

    def get_replacement_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """获取替换历史"""
        return [h for h in self.history if h.get('old_id') == entity_id or h.get('new_id') == entity_id]

    def get_replacement_orders(self) -> List[Dict[str, Any]]:
        """获取所有换货单"""
        return self.replacement_orders

    # ==================== 内部方法 ====================

    def _recalc_collision(self, entity) -> Dict[str, Any]:
        """重算碰撞"""
        if self.collision_engine:
            # 真实场景会重新检测
            pass
        return {'success': True}

    def _recalc_cost(self, entity) -> Dict[str, Any]:
        """重算造价"""
        if self.cost_engine:
            # 真实场景会重新计算
            pass
        return {'success': True}

    def _update_l4(self, entity_id: str, event: str, detail: str):
        """写L4（简化）"""
        pass

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}