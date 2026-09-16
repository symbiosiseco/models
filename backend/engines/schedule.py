# -*- coding: utf-8 -*-
"""
进度引擎
受 GPL v3.0 保护

进度计算和横道图。
事件驱动，任务完成自动更新进度。
"""

from typing import Dict, Any, List
from datetime import datetime
from .event_bus import EventBus


class ScheduleEngine:
    """进度引擎"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()

    # ==================== 计算进度 ====================

    def calculate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算进度"""
        total = len(tasks)
        if total == 0:
            return {'total': 0, 'completed': 0, 'running': 0, 'pending': 0, 'percentage': 0}

        completed = len([t for t in tasks if t.get('status') == '已完成'])
        running = len([t for t in tasks if t.get('status') == '执行中'])
        pending = len([t for t in tasks if t.get('status') == '待执行'])
        percentage = round(completed / total * 100, 2)

        return {
            'total': total,
            'completed': completed,
            'running': running,
            'pending': pending,
            'percentage': percentage,
        }

    # ==================== 关键路径 ====================

    def get_critical_path(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """获取关键路径"""
        # 简化：按任务链追踪
        if not tasks:
            return []

        # 找第一个任务（无前置）
        first = None
        for t in tasks:
            if not t.get('predecessor'):
                first = t
                break

        if not first:
            return []

        path = [first['id']]
        current = first
        visited = {first['id']}

        while True:
            successors = current.get('successor', [])
            if isinstance(successors, str):
                successors = [successors]
            if not successors:
                break
            next_id = successors[0]
            if next_id in visited:
                break
            visited.add(next_id)
            path.append(next_id)
            next_task = next((t for t in tasks if t['id'] == next_id), None)
            if not next_task:
                break
            current = next_task

        return path

    # ==================== 甘特图数据 ====================

    def get_gantt_data(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取甘特图数据"""
        gantt = []
        for t in tasks:
            gantt.append({
                'task_id': t['id'],
                'name': t.get('name', ''),
                'start': t.get('start_time', ''),
                'end': t.get('end_time', ''),
                'duration': t.get('duration', 0),
                'progress': self._calc_task_progress(t),
                'predecessor': t.get('predecessor'),
                'successor': t.get('successor', []),
            })
        return gantt

    def _calc_task_progress(self, task: Dict[str, Any]) -> float:
        """计算单个任务进度"""
        status = task.get('status', '待执行')
        if status == '已完成':
            return 100.0
        if status == '执行中':
            return 50.0
        return 0.0

    # ==================== 进度百分比 ====================

    def get_progress_percentage(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取进度百分比"""
        overall = self.calculate(tasks)

        by_type: Dict[str, Dict[str, Any]] = {}
        for t in tasks:
            ttype = t.get('type', '未知')
            if ttype not in by_type:
                by_type[ttype] = {'total': 0, 'completed': 0}
            by_type[ttype]['total'] += 1
            if t.get('status') == '已完成':
                by_type[ttype]['completed'] += 1

        for ttype in by_type:
            tot = by_type[ttype]['total']
            by_type[ttype]['percentage'] = round(by_type[ttype]['completed'] / tot * 100, 2) if tot > 0 else 0

        return {
            'overall': overall['percentage'],
            'by_type': by_type,
        }

    # ==================== 逾期任务 ====================

    def get_overdue_tasks(self, tasks: List[Dict[str, Any]],
                           current_time: str = '') -> List[Dict[str, Any]]:
        """获取逾期任务"""
        current_time = current_time or datetime.now().strftime('%Y-%m-%d %H:%M')
        overdue = []
        for t in tasks:
            if t.get('status') == '已完成':
                continue
            end_time = t.get('end_time', '')
            if end_time and end_time < current_time:
                overdue.append(t)
        return overdue

    # ==================== 更新进度 ====================

    def update_progress(self, task_id: str, progress: float) -> Dict[str, Any]:
        """更新任务进度"""
        if self.event_bus:
            self.event_bus.publish('进度更新', {
                'task_id': task_id,
                'progress': progress,
            })
        return {'success': True, 'task_id': task_id, 'progress': progress}

    # ==================== 事件发布 ====================

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}