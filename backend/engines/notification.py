# -*- coding: utf-8 -*-
"""
通知引擎
受 GPL v3.0 保护

向对应角色派发通知。
通过事件总线通知。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class NotificationEngine:
    """通知引擎"""

    # 通知类型
    NOTIFY_TYPES = ['任务派发', '任务完成', '变更通知', '验收通知', '进度款通知', '装配失败', '换货触发']

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self.notifications: List[Dict[str, Any]] = []
        self.counter = 0

    # ==================== 订阅事件 ====================

    def subscribe_events(self) -> Dict[str, Any]:
        """订阅事件总线"""
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('任务派发', self._on_task_assigned, 'notification')
        self.event_bus.subscribe('任务完成', self._on_task_complete, 'notification')
        self.event_bus.subscribe('装配失败', self._on_assembly_failed, 'notification')
        self.event_bus.subscribe('验收通过', self._on_accepted, 'notification')
        self.event_bus.subscribe('验收不通过', self._on_rejected, 'notification')
        self.event_bus.subscribe('变更审批', self._on_change_approved, 'notification')
        self.event_bus.subscribe('进度款审批', self._on_payment_approved, 'notification')
        return {'success': True}

    # ==================== 事件回调 ====================

    def _on_task_assigned(self, event_type: str, data: Dict[str, Any]):
        worker_id = data.get('worker_id')
        task_id = data.get('task_id')
        if worker_id:
            self.notify(worker_id, '任务派发', f'你有新任务 {task_id}', source_event='任务派发')

    def _on_task_complete(self, event_type: str, data: Dict[str, Any]):
        self.notify_role('项目经理', '任务完成', f"任务 {data.get('task_id')} 已完成", source_event='任务完成')

    def _on_assembly_failed(self, event_type: str, data: Dict[str, Any]):
        worker_id = data.get('worker_id')
        error = data.get('error', '')
        if worker_id:
            self.notify(worker_id, '装配失败', f'装配失败：{error}', source_event='装配失败')

    def _on_accepted(self, event_type: str, data: Dict[str, Any]):
        self.notify_role('甲方', '验收通知', f"{data.get('entity_id')} 验收通过", source_event='验收通过')

    def _on_rejected(self, event_type: str, data: Dict[str, Any]):
        self.notify_role('施工员', '验收通知', f"{data.get('entity_id')} 验收不通过", source_event='验收不通过')

    def _on_change_approved(self, event_type: str, data: Dict[str, Any]):
        self.notify_role('施工员', '变更通知', f"变更 {data.get('change_id')} 已审批", source_event='变更审批')

    def _on_payment_approved(self, event_type: str, data: Dict[str, Any]):
        self.notify_role('财务', '进度款通知', f"进度款 {data.get('payment_id')} 已审批", source_event='进度款审批')

    # ==================== 通知方法 ====================

    def notify(self, recipient: str, notify_type: str, content: str,
                source_event: str = '') -> Dict[str, Any]:
        """通知具体人员"""
        if notify_type not in self.NOTIFY_TYPES:
            return {'success': False, 'message': f'未知通知类型：{notify_type}'}
        if not recipient:
            return {'success': False, 'message': '接收人不能为空'}

        self.counter += 1
        notify_id = f'NOTI-{self.counter:04d}'

        notification = {
            'notify_id': notify_id,
            'notify_type': notify_type,
            'recipient': recipient,
            'content': content,
            'source_event': source_event,
            'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'read': False,
        }
        self.notifications.append(notification)

        # 通过事件总线发布"通知"事件（给前端）
        if self.event_bus:
            self.event_bus.publish('通知', {
                'notify_id': notify_id,
                'notify_type': notify_type,
                'recipient': recipient,
                'content': content,
                'source_event': source_event,
            })

        return {'success': True, 'notify_id': notify_id, 'recipient': recipient}

    def notify_role(self, role: str, notify_type: str, content: str,
                     source_event: str = '') -> Dict[str, Any]:
        """通知某个角色（简化：直接以角色名作为接收人ID）"""
        return self.notify(role, notify_type, content, source_event)

    def notify_org(self, org_code: str, notify_type: str, content: str) -> Dict[str, Any]:
        """通知某个单位"""
        return self.notify(org_code, notify_type, content)

    def broadcast(self, notify_type: str, content: str) -> Dict[str, Any]:
        """广播给所有人"""
        return self.notify('ALL', notify_type, content)

    # ==================== 查询 ====================

    def get_notifications(self, recipient: str) -> List[Dict[str, Any]]:
        """获取某人的通知列表"""
        return [n for n in self.notifications if n['recipient'] == recipient]

    def get_unread(self, recipient: str) -> List[Dict[str, Any]]:
        """获取未读通知"""
        return [n for n in self.notifications if n['recipient'] == recipient and not n['read']]

    def mark_read(self, notify_id: str) -> Dict[str, Any]:
        """标记已读"""
        for n in self.notifications:
            if n['notify_id'] == notify_id:
                n['read'] = True
                return {'success': True, 'notify_id': notify_id}
        return {'success': False, 'message': f'通知不存在：{notify_id}'}

    def mark_all_read(self, recipient: str) -> Dict[str, Any]:
        """标记所有已读"""
        count = 0
        for n in self.notifications:
            if n['recipient'] == recipient and not n['read']:
                n['read'] = True
                count += 1
        return {'success': True, 'count': count}

    # ==================== 事件发布 ====================

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}

    # ==================== 创建通知记录 ====================

    def _create_notification(self, recipient: str, notify_type: str,
                              content: str) -> Dict[str, Any]:
        """创建通知记录（兼容层）"""
        return self.notify(recipient, notify_type, content)