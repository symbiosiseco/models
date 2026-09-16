# -*- coding: utf-8 -*-
"""
分包场景
受 GPL v3.0 保护

专业作业。
调用WorkerCBM+TaskCBM。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class SubcontractorScene:
    """分包场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.materials: List[str] = []
        self.problems: List[Dict[str, Any]] = []
        self._subscribe_events()

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('任务派发', self._on_event, 'subcontractor')
        self.event_bus.subscribe('产物完成', self._on_event, 'subcontractor')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        pass

    # ==================== 接受任务 ====================

    def accept_task(self, task_id: str) -> Dict[str, Any]:
        """接受任务"""
        self.tasks[task_id] = {'task_id': task_id, 'status': '已接受'}
        if self.event_bus:
            self.event_bus.publish('任务接受', {'task_id': task_id})
        return {'success': True, 'task_id': task_id, 'status': '已接受'}

    # ==================== 派工 ====================

    def assign_worker(self, task_id: str, worker_id: str) -> Dict[str, Any]:
        """派工"""
        # 通过 WorkerCBM 检查
        worker_cbm = self.engines.get('worker_cbm')
        if worker_cbm:
            check = worker_cbm.check_capacity()
            if not check.get('passed', True):
                return {'success': False, 'message': '工人体力不足'}

        task = self.tasks.setdefault(task_id, {'task_id': task_id})
        task['actor'] = worker_id

        if self.event_bus:
            self.event_bus.publish('任务派发', {
                'task_id': task_id,
                'worker_id': worker_id,
            })
        return {'success': True, 'task_id': task_id, 'worker_id': worker_id}

    # ==================== 领料 ====================

    def request_material(self, material_ids: List[str]) -> Dict[str, Any]:
        """领料"""
        for mid in material_ids:
            self.materials.append(mid)
        if self.event_bus:
            self.event_bus.publish('L3变化', {'materials': material_ids})
        return {'success': True, 'materials': material_ids}

    # ==================== 报量 ====================

    def report_progress(self, task_id: str, progress: float) -> Dict[str, Any]:
        """报量"""
        task = self.tasks.setdefault(task_id, {'task_id': task_id})
        task['progress'] = progress
        if self.event_bus:
            self.event_bus.publish('进度更新', {
                'task_id': task_id,
                'progress': progress,
            })
        return {'success': True, 'task_id': task_id, 'progress': progress}

    # ==================== 处理问题 ====================

    def handle_problem(self, task_id: str, problem: str) -> Dict[str, Any]:
        """处理问题"""
        problem_id = f'SUBPROB-{len(self.problems) + 1:03d}'
        self.problems.append({
            'problem_id': problem_id,
            'task_id': task_id,
            'problem': problem,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        if self.event_bus:
            self.event_bus.publish('现场问题', {'problem_id': problem_id, 'task_id': task_id, 'problem': problem})
        return {'success': True, 'problem_id': problem_id}

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {'role': role, 'tasks': list(self.tasks.values()), 'materials': self.materials}