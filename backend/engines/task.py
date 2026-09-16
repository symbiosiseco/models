# -*- coding: utf-8 -*-
"""
任务引擎
受 GPL v3.0 保护

管理任务的加载、启动、完成、触发链。
与 task_cbm.py 配合，由事件总线驱动。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class TaskEngine:
    """任务引擎"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.started = False

    # ==================== 加载/启动 ====================

    def load(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """加载任务清单"""
        self.tasks = {}
        for t in tasks:
            self.tasks[t['id']] = t
        return {'success': True, 'total_tasks': len(self.tasks)}

    def start(self) -> Dict[str, Any]:
        """启动任务引擎，订阅事件总线"""
        started_tasks = 0
        if self.event_bus:
            self.event_bus.subscribe('任务完成', self._on_task_complete, 'task_engine')
        for t in self.tasks.values():
            if t.get('status') == '待执行':
                started_tasks += 1
        self.started = True
        return {'success': True, 'started_tasks': started_tasks}

    # ==================== 完成任务 ====================

    def complete(self, task_id: str) -> Dict[str, Any]:
        """
        完成任务。

        流程：
            1. 更新 task.status = '已完成'
            2. 写 L4
            3. 通过 event_bus 发布 '任务完成' 事件
            4. 返回被触发的下游任务列表
        """
        task = self.tasks.get(task_id)
        if not task:
            return {'success': False, 'message': f'任务不存在：{task_id}'}

        if task.get('status') == '已完成':
            return {'success': False, 'message': f'任务已完成：{task_id}'}

        task['status'] = '已完成'
        task['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 通过事件总线发布
        triggered = self.get_triggered(task_id)
        if self.event_bus:
            self.event_bus.publish('任务完成', {
                'task_id': task_id,
                'triggered_tasks': triggered,
            })

        return {
            'success': True,
            'task_id': task_id,
            'triggered_tasks': triggered,
        }

    def get_triggered(self, task_id: str) -> List[str]:
        """获取被触发的下游任务"""
        task = self.tasks.get(task_id)
        if not task:
            return []
        successors = task.get('cbm', {}).get('后继任务', [])
        if isinstance(successors, str):
            successors = [successors] if successors else []
        # 更新下游任务状态
        for sid in successors:
            if sid in self.tasks:
                self.tasks[sid]['status'] = '待执行'
        return list(successors)

    # ==================== 事件回调 ====================

    def _on_task_complete(self, event_type: str, data: Dict[str, Any]):
        """事件回调"""
        task_id = data.get('task_id')
        if not task_id or task_id not in self.tasks:
            return
        # 更新状态
        self.tasks[task_id]['status'] = '已完成'

    # ==================== 状态查询 ====================

    def get_status(self) -> Dict[str, Any]:
        """获取任务引擎状态"""
        total = len(self.tasks)
        pending = len([t for t in self.tasks.values() if t.get('status') == '待执行'])
        running = len([t for t in self.tasks.values() if t.get('status') == '执行中'])
        done = len([t for t in self.tasks.values() if t.get('status') == '已完成'])
        return {
            'total': total,
            'pending': pending,
            'running': running,
            'done': done,
        }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取单个任务"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return list(self.tasks.values())

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待执行任务"""
        return [t for t in self.tasks.values() if t.get('status') == '待执行']

    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取执行中任务"""
        return [t for t in self.tasks.values() if t.get('status') == '执行中']

    def get_done_tasks(self) -> List[Dict[str, Any]]:
        """获取已完成任务"""
        return [t for t in self.tasks.values() if t.get('status') == '已完成']

    # ==================== 事件发布 ====================

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布事件"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False, 'message': '事件总线未初始化'}

    # ==================== 重置 ====================

    def reset(self) -> Dict[str, Any]:
        """重置"""
        for t in self.tasks.values():
            t['status'] = '待执行'
            t.pop('completed_at', None)
        self.started = False
        return {'success': True}