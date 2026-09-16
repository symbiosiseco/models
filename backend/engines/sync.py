# -*- coding: utf-8 -*-
"""
数据同步引擎
受 GPL v3.0 保护

前后端实时同步。
通过事件总线 + WebSocket。
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .event_bus import EventBus


class SyncEngine:
    """数据同步引擎"""

    # 缓存上限（每客户端）
    CACHE_LIMIT = 100

    def __init__(self, event_bus: Optional[EventBus] = None, socketio=None):
        self.event_bus = event_bus or EventBus()
        self.socketio = socketio
        # client_id → 订阅的实体ID列表
        self.subscriptions: Dict[str, List[str]] = {}
        # client_id → 订阅的事件类型列表
        self.event_subscriptions: Dict[str, List[str]] = {}
        # client_id → 待推送事件缓存
        self.pending_events: Dict[str, List[Dict[str, Any]]] = {}
        # 所有连接过的客户端
        self.clients: List[str] = []

    # ==================== 订阅事件总线 ====================

    def _subscribe_to_bus(self) -> Dict[str, Any]:
        """订阅事件总线的所有事件"""
        if not self.event_bus:
            return {'success': False}
        for event_type in [
            'L3变化', '任务派发', '任务完成', '任务开始',
            '产物完成', '装配失败', '接触面错误', '换货触发',
            '验收通过', '验收不通过', '变更触发', '变更审批',
            '签证生成', '签证支付', '签字', '签字完成', '签字驳回',
            '流程启动', '流程完成', '流程审批', '流程驳回', '流程通知',
            '通知', '碰撞解决', '寿命到期', '导出完成',
            '监管警告', '现场反馈', '实测记录', '支架调节',
            '实体替换', '换货单生成', '进度更新', '项目更新',
        ]:
            self.event_bus.subscribe(event_type, self.on_event, 'sync_engine')
        return {'success': True}

    # ==================== 事件回调 ====================

    def on_event(self, event_type: str, data: Dict[str, Any]):
        """事件总线回调：广播给所有客户端"""
        self.broadcast(event_type, data)

    # ==================== 广播 ====================

    def broadcast(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        广播事件给所有客户端。

        流程：
            1. 遍历所有已连接客户端
            2. 检查是否订阅该事件
            3. 推送事件
        """
        event = {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        clients_count = 0
        for client_id in self.clients:
            if self._is_subscribed(client_id, event_type, data):
                self._push_to_client(client_id, event)
                clients_count += 1

        return {'success': True, 'clients_count': clients_count}

    def _is_subscribed(self, client_id: str, event_type: str,
                        data: Dict[str, Any]) -> bool:
        """检查客户端是否订阅了该事件"""
        # 事件类型订阅
        event_subs = self.event_subscriptions.get(client_id, [])
        if event_subs and event_type not in event_subs and '*' not in event_subs:
            return False

        # 实体订阅
        entity_id = data.get('entity_id')
        entity_subs = self.subscriptions.get(client_id, [])
        if entity_subs and entity_id and entity_id not in entity_subs and '*' not in entity_subs:
            return False

        return True

    # ==================== 客户端订阅 ====================

    def subscribe(self, client_id: str, entity_ids: List[str]) -> Dict[str, Any]:
        """客户端订阅实体"""
        if client_id not in self.clients:
            self.clients.append(client_id)
        self.subscriptions[client_id] = list(entity_ids)
        return {'success': True, 'client_id': client_id, 'subscriptions': entity_ids}

    def subscribe_events(self, client_id: str, event_types: List[str]) -> Dict[str, Any]:
        """客户端订阅事件类型"""
        if client_id not in self.clients:
            self.clients.append(client_id)
        self.event_subscriptions[client_id] = list(event_types)
        return {'success': True, 'client_id': client_id, 'event_types': event_types}

    def subscribe_cbm(self, client_id: str, entity_ids: List[str]) -> Dict[str, Any]:
        """客户端订阅CBM状态"""
        if client_id not in self.clients:
            self.clients.append(client_id)
        self.event_subscriptions.setdefault(client_id, []).append('L3变化')
        self.subscriptions[client_id] = list(entity_ids)
        return {'success': True, 'client_id': client_id}

    def subscribe_force_points(self, client_id: str, entity_ids: List[str]) -> Dict[str, Any]:
        """客户端订阅受力点"""
        if client_id not in self.clients:
            self.clients.append(client_id)
        self.subscriptions[client_id] = list(entity_ids)
        return {'success': True, 'client_id': client_id}

    def unsubscribe(self, client_id: str) -> Dict[str, Any]:
        """取消订阅"""
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        if client_id in self.event_subscriptions:
            del self.event_subscriptions[client_id]
        if client_id in self.clients:
            self.clients.remove(client_id)
        return {'success': True, 'client_id': client_id}

    # ==================== 推送 ====================

    def _push_to_client(self, client_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """推送给单个客户端"""
        if self.socketio:
            try:
                self.socketio.emit(event['event_type'], event['data'], room=client_id)
            except Exception as e:
                self._cache_event(client_id, event)
        else:
            # SocketIO未初始化时缓存
            self._cache_event(client_id, event)
        return {'success': True, 'client_id': client_id}

    def _cache_event(self, client_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """缓存事件（客户端离线时）"""
        if client_id not in self.pending_events:
            self.pending_events[client_id] = []
        self.pending_events[client_id].append(event)
        # 限制缓存上限
        if len(self.pending_events[client_id]) > self.CACHE_LIMIT:
            self.pending_events[client_id] = self.pending_events[client_id][-self.CACHE_LIMIT:]
        return {'success': True}

    # ==================== 查询 ====================

    def get_pending_events(self, client_id: str) -> List[Dict[str, Any]]:
        """获取待推送事件"""
        events = self.pending_events.get(client_id, [])
        self.pending_events[client_id] = []
        return events

    def get_connected_clients(self) -> List[str]:
        """获取所有连接的客户端"""
        return list(self.clients)

    def get_client_subscriptions(self, client_id: str) -> List[str]:
        """获取客户端的订阅列表"""
        return self.subscriptions.get(client_id, [])

    def clear_cache(self) -> Dict[str, Any]:
        """清空缓存"""
        self.pending_events = {}
        return {'success': True}