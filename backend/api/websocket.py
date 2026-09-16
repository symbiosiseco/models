# -*- coding: utf-8 -*-
"""
WebSocket接口
受 GPL v3.0 保护

实时同步。
含事件总线订阅 + CBM状态推送 + 受力点推送。
"""

from typing import Dict, Any, List
from engines.sync import SyncEngine
from flask import Blueprint

websocket_bp = Blueprint('websocket', __name__)


# 全局同步引擎
_sync_engine = None
_socketio = None


def set_deps(sync_engine: SyncEngine, socketio):
    """注入依赖"""
    global _sync_engine, _socketio
    _sync_engine = sync_engine
    _socketio = socketio


# ==================== SocketIO 事件处理器 ====================

def register_socketio_handlers(socketio):
    """注册SocketIO事件处理器"""
    global _socketio
    _socketio = socketio

    @socketio.on('connect')
    def handle_connect():
        """连接"""
        from flask import request
        client_id = request.sid
        if _sync_engine:
            _sync_engine.subscribe(client_id, [])
        socketio.emit('connected', {'client_id': client_id})

    @socketio.on('disconnect')
    def handle_disconnect():
        """断开"""
        from flask import request
        client_id = request.sid
        if _sync_engine:
            _sync_engine.unsubscribe(client_id)

    @socketio.on('subscribe')
    def handle_subscribe(data):
        """订阅实体"""
        from flask import request
        client_id = request.sid
        entity_ids = data.get('entity_ids', [])
        if _sync_engine:
            _sync_engine.subscribe(client_id, entity_ids)
        socketio.emit('subscribed', {'entity_ids': entity_ids}, room=client_id)

    @socketio.on('unsubscribe')
    def handle_unsubscribe():
        """取消订阅"""
        from flask import request
        client_id = request.sid
        if _sync_engine:
            _sync_engine.unsubscribe(client_id)

    @socketio.on('subscribe_events')
    def handle_subscribe_events(data):
        """订阅事件类型"""
        from flask import request
        client_id = request.sid
        event_types = data.get('event_types', [])
        if _sync_engine:
            _sync_engine.subscribe_events(client_id, event_types)
        socketio.emit('subscribed_events', {'event_types': event_types}, room=client_id)

    @socketio.on('subscribe_cbm')
    def handle_subscribe_cbm(data):
        """订阅CBM状态"""
        from flask import request
        client_id = request.sid
        entity_ids = data.get('entity_ids', [])
        if _sync_engine:
            _sync_engine.subscribe_cbm(client_id, entity_ids)
        socketio.emit('subscribed_cbm', {'entity_ids': entity_ids}, room=client_id)

    @socketio.on('subscribe_force_points')
    def handle_subscribe_force_points(data):
        """订阅受力点"""
        from flask import request
        client_id = request.sid
        entity_ids = data.get('entity_ids', [])
        if _sync_engine:
            _sync_engine.subscribe_force_points(client_id, entity_ids)
        socketio.emit('subscribed_force_points', {'entity_ids': entity_ids}, room=client_id)

    @socketio.on('ping')
    def handle_ping():
        """心跳"""
        from datetime import datetime
        socketio.emit('pong', {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})


# ==================== 推送函数 ====================

def push_event(client_id: str, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """推送事件给单个客户端"""
    if _socketio:
        _socketio.emit(event_type, data, room=client_id)
        return {'success': True}
    return {'success': False, 'message': 'SocketIO未初始化'}


def broadcast_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """广播事件"""
    if _sync_engine:
        return _sync_engine.broadcast(event_type, data)
    return {'success': False}