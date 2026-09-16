# -*- coding: utf-8 -*-
"""
项目CBM引擎
受 GPL v3.0 保护

资源调度、优先级、冲突处理。
项目CBM是"总协调"——负责跨任务的资源调度、优先级、冲突处理。
"""

from typing import Dict, Any, List
from .event_bus import EventBus


class ProjectCBM:
    """项目CBM引擎"""

    def __init__(self, project, event_bus: EventBus, all_tasks: Dict[str, Any] = None):
        self.project = project
        self.event_bus = event_bus
        self.all_tasks = all_tasks or {}
        self.watching = False
        self.conflicts: List[Dict[str, Any]] = []

    # ==================== 监听 ====================

    def watch(self) -> Dict[str, Any]:
        """开始监听任务完成"""
        self.event_bus.subscribe(
            '任务完成',
            self._on_task_complete_event,
            f'project_cbm_{self._project_id()}'
        )
        self.watching = True
        return {'success': True, 'project_id': self._project_id()}

    def unwatch(self) -> Dict[str, Any]:
        """停止监听"""
        self.event_bus.unsubscribe('任务完成', f'project_cbm_{self._project_id()}')
        self.watching = False
        return {'success': True, 'project_id': self._project_id()}

    def _on_task_complete_event(self, event_type: str, data: Dict[str, Any]):
        """事件总线回调"""
        task_id = data.get('task_id')
        task = self.all_tasks.get(task_id)
        if task:
            self.on_task_complete(task)

    # ==================== 任务完成回调 ====================

    def on_task_complete(self, task) -> Dict[str, Any]:
        """
        任务完成回调。

        流程：
            1. 更新项目进度
            2. 检查资源冲突
            3. 检查是否需要重排
        """
        progress = self.get_progress()
        conflicts = self._check_conflicts()

        self.notify_stakeholders({
            'event_type': '任务完成',
            'task_id': getattr(task, 'id', None),
            'progress': progress,
        })

        return {
            'progress_updated': True,
            'progress': progress,
            'conflicts': conflicts,
        }

    # ==================== 资源调度 ====================

    def schedule_resources(self) -> Dict[str, Any]:
        """
        资源调度。

        流程：
            1. 根据任务优先级分配资源
            2. 检查人员/材料可用性
        """
        scheduled = []
        for task_id, task in self.all_tasks.items():
            status = task.layer.get('l3_dynamic_state', {}).get('状态')
            if status != '待执行':
                continue

            # 检查前置
            cbm = task.layer.get('cbm_abilities', {})
            predecessor_id = cbm.get('前置任务')
            if predecessor_id:
                pred = self.all_tasks.get(predecessor_id)
                if pred and pred.layer.get('l3_dynamic_state', {}).get('状态') != '已完成':
                    continue

            # 通过事件总线派发
            self.event_bus.publish('任务派发', {
                'task_id': task_id,
                'worker_id': task.layer.get('l2_static_attributes', {}).get('执行人'),
            })
            scheduled.append(task_id)

        return {'success': True, 'scheduled_tasks': scheduled}

    def resolve_conflict(self, task_a, task_b) -> Dict[str, Any]:
        """
        冲突处理。

        流程：
            1. 检测多任务争抢同一资源
            2. 按优先级分配
        """
        priority_a = task_a.layer.get('cbm_abilities', {}).get('优先级', 5)
        priority_b = task_b.layer.get('cbm_abilities', {}).get('优先级', 5)

        # 数字小的胜出
        if priority_a <= priority_b:
            winner, loser = task_a, task_b
        else:
            winner, loser = task_b, task_a

        result = {
            'winner': getattr(winner, 'id', None),
            'loser': getattr(loser, 'id', None),
            'reason': f'优先级 {priority_a} vs {priority_b}',
        }
        self.event_bus.publish('冲突解决', result)
        self.conflicts.append(result)
        return {'success': True, 'resolved': result}

    def prioritize_tasks(self) -> List[Dict[str, Any]]:
        """优先级排序"""
        tasks = list(self.all_tasks.values())
        sorted_tasks = sorted(
            tasks,
            key=lambda t: t.layer.get('cbm_abilities', {}).get('优先级', 5)
        )
        return [
            {'task_id': getattr(t, 'id', None), 'priority': t.layer.get('cbm_abilities', {}).get('优先级', 5)}
            for t in sorted_tasks
        ]

    # ==================== 动态重排 ====================

    def replan(self) -> Dict[str, Any]:
        """
        动态重排。

        场景：现场变故（天气、材料延迟）
        流程：自动调整任务顺序
        """
        # 简单重排：按优先级
        prioritized = self.prioritize_tasks()
        return {'success': True, 'new_schedule': prioritized}

    # ==================== 通知相关方 ====================

    def notify_stakeholders(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """通知相关方"""
        self.event_bus.publish('项目更新', event)
        return {'success': True}

    # ==================== 进度 ====================

    def get_progress(self) -> Dict[str, Any]:
        """获取项目进度"""
        total = len(self.all_tasks)
        if total == 0:
            return {'total': 0, 'completed': 0, 'percentage': 0}

        completed = sum(
            1 for t in self.all_tasks.values()
            if t.layer.get('l3_dynamic_state', {}).get('状态') == '已完成'
        )
        return {
            'total': total,
            'completed': completed,
            'percentage': round(completed / total * 100, 2),
        }

    # ==================== 内部 ====================

    def _check_conflicts(self) -> List[Dict[str, Any]]:
        """检查资源冲突"""
        # 简化：检测同一执行人的多个待执行任务
        worker_tasks: Dict[str, List[str]] = {}
        for task_id, task in self.all_tasks.items():
            if task.layer.get('l3_dynamic_state', {}).get('状态') != '待执行':
                continue
            worker = task.layer.get('l2_static_attributes', {}).get('执行人')
            if worker:
                worker_tasks.setdefault(worker, []).append(task_id)

        conflicts = []
        for worker, task_ids in worker_tasks.items():
            if len(task_ids) > 1:
                conflicts.append({
                    'type': '资源冲突',
                    'worker': worker,
                    'tasks': task_ids,
                })
        return conflicts

    def _project_id(self) -> str:
        return getattr(self.project, 'id', 'UNKNOWN')