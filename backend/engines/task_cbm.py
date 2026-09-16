# -*- coding: utf-8 -*-
"""
任务CBM引擎
受 GPL v3.0 保护

任务完成后触发下游。
任务CBM是"流程驱动"——负责触发下游，是流程的核心。
"""

from typing import Dict, Any, List
from datetime import datetime
from .event_bus import EventBus


class TaskCBM:
    """任务CBM引擎"""

    def __init__(self, task, event_bus: EventBus, all_tasks: Dict[str, Any] = None):
        self.task = task
        self.event_bus = event_bus
        self.all_tasks = all_tasks or {}
        self.watching = False
        self.completed_products: List[str] = []

    # ==================== 监听 ====================

    def watch(self) -> Dict[str, Any]:
        """开始监听产物完成"""
        self.event_bus.subscribe(
            '产物完成',
            self._on_product_complete_event,
            f'task_cbm_{self._task_id()}'
        )
        self.watching = True
        return {'success': True, 'task_id': self._task_id()}

    def unwatch(self) -> Dict[str, Any]:
        """停止监听"""
        self.event_bus.unsubscribe('产物完成', f'task_cbm_{self._task_id()}')
        self.watching = False
        return {'success': True, 'task_id': self._task_id()}

    def _on_product_complete_event(self, event_type: str, data: Dict[str, Any]):
        """事件总线回调"""
        # 只处理本任务相关产物
        task_id = data.get('task_id')
        if task_id and task_id != self._task_id():
            return
        product_id = data.get('entity_id')
        if product_id:
            self.on_product_complete(product_id)

    # ==================== 产物完成 ====================

    def on_product_complete(self, product_id: str) -> Dict[str, Any]:
        """产物完成回调"""
        if product_id not in self.completed_products:
            self.completed_products.append(product_id)

        all_done = self.check_all_products_done()

        if all_done:
            self.mark_complete()

        return {
            'recorded': True,
            'all_done': all_done,
            'completed': len(self.completed_products),
        }

    def check_all_products_done(self) -> bool:
        """检查所有产物是否完成"""
        l2 = self.task.layer.get('l2_static_attributes', {})
        products = l2.get('输出产物', [])
        if not products:
            # 无产物定义时，视为完成
            return True
        # 所有产物都在已完成列表里
        product_ids = [
            p.get('id') if isinstance(p, dict) else p
            for p in products
        ]
        return all(pid in self.completed_products for pid in product_ids)

    # ==================== 任务完成 ====================

    def mark_complete(self) -> Dict[str, Any]:
        """
        标记任务完成。

        流程：
            1. 更新 task.L3.状态 = "已完成"
            2. 写L4
            3. 通过事件总线发布"任务完成"
            4. 调用 trigger_successor
        """
        self.task.layer['l3_dynamic_state']['状态'] = '已完成'
        self.write_l4('任务完成', f'完成产物{len(self.completed_products)}个')

        self.event_bus.publish('任务完成', {
            'task_id': self._task_id(),
            'triggered_tasks': self._get_successors(),
        })

        self.trigger_successor()
        return {'success': True, 'task_id': self._task_id()}

    # ==================== 触发下游 ====================

    def trigger_successor(self) -> Dict[str, Any]:
        """
        触发下游任务。

        流程：
            1. 检查 successor 的前置条件
            2. 满足 → 更新状态="待执行"
            3. 通知 successor 的 CBM
            4. 通过事件总线发布"任务派发"
        """
        successors = self._get_successors()
        triggered = []

        for successor_id in successors:
            successor = self.all_tasks.get(successor_id)
            if not successor:
                continue

            # 检查前置条件
            if not self._check_predecessor(successor_id):
                continue

            # 更新状态
            successor.layer['l3_dynamic_state']['状态'] = '待执行'

            # 通过事件总线发布任务派发
            self.event_bus.publish('任务派发', {
                'task_id': successor_id,
                'worker_id': successor.layer.get('l2_static_attributes', {}).get('执行人'),
            })

            triggered.append(successor_id)

        return {'success': True, 'triggered_tasks': triggered}

    def notify_worker(self, worker_id: str) -> Dict[str, Any]:
        """通知执行人"""
        self.event_bus.publish('任务派发', {
            'task_id': self._task_id(),
            'worker_id': worker_id,
        })
        return {'success': True, 'worker_id': worker_id}

    # ==================== 前置条件检查 ====================

    def check_predecessor(self) -> bool:
        """检查前置任务是否完成"""
        l2 = self.task.layer.get('l2_static_attributes', {})
        cbm = self.task.layer.get('cbm_abilities', {})
        predecessor_id = cbm.get('前置任务') or l2.get('前置任务')

        if not predecessor_id:
            return True

        predecessor = self.all_tasks.get(predecessor_id)
        if not predecessor:
            return True

        status = predecessor.layer.get('l3_dynamic_state', {}).get('状态')
        return status == '已完成'

    def _check_predecessor(self, successor_id: str) -> bool:
        """检查某个后继任务的前置条件是否满足"""
        successor = self.all_tasks.get(successor_id)
        if not successor:
            return False

        cbm = successor.layer.get('cbm_abilities', {})
        predecessor_id = cbm.get('前置任务')

        if not predecessor_id:
            return True

        # 前置任务必须完成
        predecessor = self.all_tasks.get(predecessor_id)
        if not predecessor:
            return True

        return predecessor.layer.get('l3_dynamic_state', {}).get('状态') == '已完成'

    # ==================== 写L4 ====================

    def write_l4(self, event: str, detail: str = '') -> Dict[str, Any]:
        """写L4"""
        self.task.add_event(event, detail)
        return {'success': True}

    # ==================== 工具 ====================

    def _task_id(self) -> str:
        return getattr(self.task, 'id', 'UNKNOWN')

    def _get_successors(self) -> List[str]:
        cbm = self.task.layer.get('cbm_abilities', {})
        successors = cbm.get('后继任务', [])
        if isinstance(successors, str):
            return [successors] if successors else []
        return list(successors or [])