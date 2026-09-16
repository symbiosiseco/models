# -*- coding: utf-8 -*-
"""
演示执行器
受 GPL v3.0 保护

管理任务播放的状态机。
事件驱动，订阅事件总线。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class DemoRunner:
    """演示执行器"""

    # 状态机
    STATUS_IDLE = 'idle'
    STATUS_RUNNING = 'running'
    STATUS_PAUSED = 'paused'
    STATUS_FINISHED = 'finished'

    # 录制上限
    MAX_RECORD_SECONDS = 300

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.tasks: List[Dict[str, Any]] = []
        self.current_index = -1
        self.status = self.STATUS_IDLE
        self.speed = 1.0
        self.records: List[Dict[str, Any]] = []
        self.current_record: Optional[Dict[str, Any]] = None
        self.recording = False
        self._subscribe_events()

    # ==================== 事件订阅 ====================

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        for et in ['任务完成', '任务派发', '装配失败', 'L3变化']:
            self.event_bus.subscribe(et, self._on_event, 'demo_runner')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        if event_type == '任务完成':
            triggered = data.get('triggered_tasks', [])
            if triggered:
                self.auto_play_next(triggered)

    def auto_play_next(self, triggered_tasks: List[str]):
        for tid in triggered_tasks:
            idx = next((i for i, t in enumerate(self.tasks) if t.get('id') == tid), None)
            if idx is not None:
                self.current_index = idx
                self.status = self.STATUS_RUNNING
                break

    # ==================== 加载/启动 ====================

    def load(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.tasks = list(tasks)
        self.current_index = -1
        self.status = self.STATUS_IDLE
        return {'success': True, 'total': len(self.tasks)}

    def start(self) -> Dict[str, Any]:
        if not self.tasks:
            return {'success': False, 'message': '无任务'}
        self.status = self.STATUS_RUNNING
        self.current_index = 0
        return {'success': True, 'status': self.status}

    def pause(self) -> Dict[str, Any]:
        if self.status == self.STATUS_RUNNING:
            self.status = self.STATUS_PAUSED
        return {'success': True, 'status': self.status}

    def next(self) -> Dict[str, Any]:
        if self.current_index < len(self.tasks) - 1:
            self.current_index += 1
        else:
            self.status = self.STATUS_FINISHED
        return self.get_current_frame()

    def prev(self) -> Dict[str, Any]:
        if self.current_index > 0:
            self.current_index -= 1
        return self.get_current_frame()

    def reset(self) -> Dict[str, Any]:
        self.current_index = -1
        self.status = self.STATUS_IDLE
        return {'success': True, 'status': self.status}

    def get_current_frame(self) -> Dict[str, Any]:
        if self.current_index < 0 or self.current_index >= len(self.tasks):
            return {'status': self.status, 'index': self.current_index, 'total': len(self.tasks)}
        task = self.tasks[self.current_index]
        return {
            'status': self.status,
            'index': self.current_index,
            'total': len(self.tasks),
            'task': task.get('id'),
            'actor': task.get('actor'),
            'action': task.get('name'),
        }

    def complete_current(self) -> Dict[str, Any]:
        if self.current_index < 0 or self.current_index >= len(self.tasks):
            return {'success': False}
        task = self.tasks[self.current_index]
        task['status'] = '已完成'
        triggered = task.get('cbm', {}).get('后继任务', [])
        if self.event_bus:
            self.event_bus.publish('任务完成', {
                'task_id': task.get('id'),
                'triggered_tasks': triggered,
            })
        return {'success': True, 'task_id': task.get('id'), 'triggered_tasks': triggered}

    def auto_play(self, speed: float = 1.0) -> Dict[str, Any]:
        self.speed = speed
        self.status = self.STATUS_RUNNING
        self.current_index = 0
        return {'success': True, 'speed': speed}

    # ==================== 操作录制 ====================

    def record_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        if not self.recording:
            self.recording = True
            self.current_record = {
                'id': f'REC-{len(self.records) + 1:03d}',
                'actions': [],
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        if self.current_record is not None:
            self.current_record['actions'].append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': action,
            })
        return {'success': True, 'record_id': self.current_record['id'] if self.current_record else None}

    def stop_record(self) -> Dict[str, Any]:
        self.recording = False
        if self.current_record:
            self.records.append(self.current_record)
            rid = self.current_record['id']
            self.current_record = None
            return {'success': True, 'record_id': rid}
        return {'success': False}

    def save_record(self, record_id: str) -> Dict[str, Any]:
        return {'success': True, 'record_id': record_id}

    def get_records(self) -> List[Dict[str, Any]]:
        return [{'id': r['id'], 'action_count': len(r['actions'])} for r in self.records]

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        return next((r for r in self.records if r['id'] == record_id), None)

    def replay(self, record_id: str, speed: float = 1.0) -> Dict[str, Any]:
        record = self.get_record(record_id)
        if not record:
            return {'success': False, 'message': '录制不存在'}
        return {'success': True, 'record_id': record_id, 'actions': len(record['actions']), 'speed': speed}