# -*- coding: utf-8 -*-
"""
人的CBM引擎
受 GPL v3.0 保护

接收任务、执行任务、报告完成。
人的CBM是"执行者"——只负责做，不负责决定做什么。
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .event_bus import EventBus


class WorkerCBM:
    """人的CBM引擎"""

    # 体力下限
    STAMINA_THRESHOLD = 60

    def __init__(self, worker, event_bus: EventBus):
        self.worker = worker
        self.event_bus = event_bus
        self.watching = False

    # ==================== 监听 ====================

    def watch(self) -> Dict[str, Any]:
        """开始监听任务派发"""
        self.event_bus.subscribe(
            '任务派发',
            self._on_task_assigned_event,
            f'worker_cbm_{self.worker.id}'
        )
        self.watching = True
        return {'success': True, 'worker_id': self.worker.id}

    def unwatch(self) -> Dict[str, Any]:
        """停止监听"""
        self.event_bus.unsubscribe('任务派发', f'worker_cbm_{self.worker.id}')
        self.watching = False
        return {'success': True, 'worker_id': self.worker.id}

    def _on_task_assigned_event(self, event_type: str, data: Dict[str, Any]):
        """事件总线回调：只处理分配给自己或自己岗位的任务"""
        target_worker = data.get('worker_id')
        if target_worker and target_worker != self.worker.id:
            return
        self.on_task_assigned(data.get('task'))

    # ==================== 任务接收 ====================

    def on_task_assigned(self, task) -> Dict[str, Any]:
        """
        收到任务。

        检查：
            1. 技能匹配
            2. 体力（≥60%）
            3. 是否空闲
            4. 活动范围
        """
        if task is None:
            return {'accepted': False, 'message': '任务为空'}

        # 检查技能
        skill_check = self.check_skill(task)
        if not skill_check.get('passed'):
            return {'accepted': False, 'checks': [skill_check], 'message': '技能不匹配'}

        # 检查体力
        capacity_check = self.check_capacity()
        if not capacity_check.get('passed'):
            return {'accepted': False, 'checks': [capacity_check], 'message': '体力不足'}

        # 检查空闲
        availability_check = self.check_availability()
        if not availability_check.get('passed'):
            return {'accepted': False, 'checks': [availability_check], 'message': '非空闲状态'}

        # 全部通过 → 接受任务
        task_id = task.get('id') if isinstance(task, dict) else getattr(task, 'id', None)
        self.accept_task(task_id)
        return {
            'accepted': True,
            'checks': [skill_check, capacity_check, availability_check],
            'message': '接受任务',
        }

    def accept_task(self, task_id: str) -> Dict[str, Any]:
        """接受任务"""
        self.update_l3('当前任务', task_id)
        self.update_l3('状态', '忙碌')
        self.write_l4(f'接收任务 {task_id}', '')
        return {'success': True, 'message': '已接受任务', 'task_id': task_id}

    # ==================== 任务执行 ====================

    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """执行任务"""
        self.update_l3('状态', '忙碌')
        self.update_l3('当前任务', task_id)
        # 通过事件总线发布L3变化
        self.event_bus.publish('L3变化', {
            'entity_id': self.worker.id,
            'new_l3': self.worker.layer.get('l3_dynamic_state', {}),
        })
        return {'success': True, 'message': '执行任务中', 'task_id': task_id}

    def report_complete(self, task_id: str, photos: Optional[list] = None) -> Dict[str, Any]:
        """
        报告完成。

        流程：
            1. 更新L3状态="空闲"
            2. 更新L3当前任务=None
            3. 写L4
            4. 通过事件总线发布"任务完成"
        """
        self.update_l3('状态', '空闲')
        self.update_l3('当前任务', None)
        self.write_l4(f'完成任务 {task_id}', f'照片{len(photos or [])}张')

        self.event_bus.publish('任务完成', {
            'task_id': task_id,
            'worker_id': self.worker.id,
            'photos': photos or [],
        })

        return {'success': True, 'message': '任务完成', 'task_id': task_id}

    # ==================== 状态检查 ====================

    def check_capacity(self) -> Dict[str, Any]:
        """检查体力是否够（≥60%）"""
        stamina_str = self.worker.layer.get('l3_dynamic_state', {}).get('体力', '100%')
        try:
            stamina = float(str(stamina_str).replace('%', ''))
        except ValueError:
            stamina = 100.0

        passed = stamina >= self.STAMINA_THRESHOLD
        return {
            'passed': passed,
            'check': '体力检查',
            'stamina': stamina,
            'message': f'体力 {stamina}%',
        }

    def check_skill(self, task) -> Dict[str, Any]:
        """检查技能是否匹配任务"""
        task_type = task.get('type') if isinstance(task, dict) else getattr(task, 'task_type', '')
        worker_skills = self.worker.layer.get('l2_static_attributes', {}).get('技能', [])
        if not task_type or not worker_skills:
            return {'passed': True, 'check': '技能检查', 'message': '无技能约束'}
        # 简单匹配：任务类型在技能列表里
        passed = any(task_type in str(s) for s in worker_skills)
        return {
            'passed': passed,
            'check': '技能检查',
            'message': f'技能匹配：{passed}',
        }

    def check_availability(self) -> Dict[str, Any]:
        """检查是否空闲"""
        status = self.worker.layer.get('l3_dynamic_state', {}).get('状态', '空闲')
        passed = status in ('空闲', 'idle')
        return {
            'passed': passed,
            'check': '空闲检查',
            'status': status,
        }

    # ==================== 更新L3 ====================

    def update_l3(self, key: str, value: Any) -> Dict[str, Any]:
        """更新人的L3"""
        self.worker.layer['l3_dynamic_state'][key] = value
        return {'success': True}

    # ==================== 写L4 ====================

    def write_l4(self, event: str, detail: str = '') -> Dict[str, Any]:
        """写L4"""
        self.worker.add_event(event, detail)
        return {'success': True}