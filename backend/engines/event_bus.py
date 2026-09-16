# -*- coding: utf-8 -*-
"""
事件总线
受 GPL v3.0 保护

负责所有CBM之间的事件发布、订阅、广播。
所有CBM通过事件总线通信，解耦。
"""

from typing import Dict, List, Callable, Any
from datetime import datetime


class EventBus:
    """事件总线"""

    # 事件历史上限
    HISTORY_LIMIT = 1000

    def __init__(self):
        # 订阅者：event_type -> List[{'subscriber_id': str, 'callback': callable}]
        self.subscribers: Dict[str, List[Dict[str, Any]]] = {}
        # 事件历史
        self.history: List[Dict[str, Any]] = []
        # 事件ID计数器
        self._event_counter = 0

    def publish(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发布事件。

        返回值：
            {success, event_id, subscribers_count}
        """
        if not event_type:
            return {'success': False, 'message': '事件类型不能为空'}

        self._event_counter += 1
        event_id = f"EVT-{self._event_counter:06d}"

        # 记录事件历史
        event_record = {
            'id': event_id,
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.history.append(event_record)
        if len(self.history) > self.HISTORY_LIMIT:
            self.history = self.history[-self.HISTORY_LIMIT:]

        # 通知订阅者
        subscribers_count = self._notify_subscribers(event_type, data)

        return {
            'success': True,
            'event_id': event_id,
            'subscribers_count': subscribers_count,
        }

    def subscribe(self, event_type: str, callback: Callable, subscriber_id: str) -> Dict[str, Any]:
        """
        订阅事件。

        返回值：
            {success, subscriber_id}
        """
        if not event_type:
            return {'success': False, 'message': '事件类型不能为空'}
        if not subscriber_id:
            return {'success': False, 'message': '订阅者ID不能为空'}

        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        # 去重：同一订阅者多次订阅同一事件时更新回调
        for sub in self.subscribers[event_type]:
            if sub['subscriber_id'] == subscriber_id:
                sub['callback'] = callback
                return {'success': True, 'subscriber_id': subscriber_id}

        self.subscribers[event_type].append({
            'subscriber_id': subscriber_id,
            'callback': callback,
        })
        return {'success': True, 'subscriber_id': subscriber_id}

    def unsubscribe(self, event_type: str, subscriber_id: str) -> Dict[str, Any]:
        """
        取消订阅。

        返回值：
            {success, subscriber_id}
        """
        if event_type not in self.subscribers:
            return {'success': False, 'message': '事件类型未订阅'}

        original_len = len(self.subscribers[event_type])
        self.subscribers[event_type] = [
            sub for sub in self.subscribers[event_type]
            if sub['subscriber_id'] != subscriber_id
        ]
        removed = original_len - len(self.subscribers[event_type])

        return {'success': removed > 0, 'subscriber_id': subscriber_id}

    def broadcast(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        广播给所有订阅者（等同于publish，语义化包装）。

        返回值：
            {success, event_id, subscribers_count}
        """
        return self.publish(event_type, data)

    def get_events(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取事件历史。

        参数：
            event_type: 事件类型（None表示所有类型）
            limit: 最多返回条数
        """
        if event_type:
            events = [e for e in self.history if e['event_type'] == event_type]
        else:
            events = self.history
        return events[-limit:]

    def get_subscribers(self, event_type: str) -> List[str]:
        """获取某事件类型的所有订阅者ID"""
        if event_type not in self.subscribers:
            return []
        return [sub['subscriber_id'] for sub in self.subscribers[event_type]]

    def get_all_event_types(self) -> List[str]:
        """获取所有已注册的事件类型"""
        return list(self.subscribers.keys())

    def clear(self) -> Dict[str, Any]:
        """清空事件总线和历史"""
        self.subscribers = {}
        self.history = []
        self._event_counter = 0
        return {'success': True}

    def _emit(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """内部发送事件（publish的别名）"""
        return self.publish(event_type, data)

    def _notify_subscribers(self, event_type: str, data: Dict[str, Any]) -> int:
        """通知订阅者，返回成功通知的数量"""
        if event_type not in self.subscribers:
            return 0

        count = 0
        for sub in self.subscribers[event_type]:
            try:
                if sub['callback']:
                    sub['callback'](event_type, data)
                count += 1
            except Exception as e:
                # callback异常不影响其他订阅者
                print(f"⚠️ 订阅者 {sub['subscriber_id']} 回调异常：{e}")
        return count

    def _record_history(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """记录事件历史（内部方法）"""
        return {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }