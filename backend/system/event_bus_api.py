# -*- coding: utf-8 -*-
"""
事件总线API
受 GPL v3.0 保护

事件订阅/发布/历史。
"""

from flask import Blueprint, request, jsonify

event_bus_bp = Blueprint('event_bus', __name__)

_event_bus = None


def set_deps(event_bus):
    """注入依赖"""
    global _event_bus
    _event_bus = event_bus


# 25种事件类型
EVENT_TYPES = [
    'L3变化', '任务派发', '任务开始', '任务完成',
    '产物完成', '装配失败', '接触面错误', '换货触发',
    '验收通过', '验收不通过', '变更触发', '变更审批',
    '签证生成', '签证支付', '签字', '签字完成', '签字驳回',
    '流程启动', '流程完成', '流程审批', '流程驳回', '流程通知',
    '通知', '碰撞解决', '寿命到期', '导出完成',
    '监管警告', '现场反馈', '实测记录', '支架调节',
    '实体替换', '换货单生成', '进度更新', '项目更新',
]


@event_bus_bp.route('/api/events/', methods=['GET'])
def list_events():
    """事件列表"""
    if not _event_bus:
        return jsonify({'success': True, 'data': []})
    event_type = request.args.get('event_type')
    limit = int(request.args.get('limit', 100))
    events = _event_bus.get_events(event_type, limit)
    return jsonify({'success': True, 'data': events})


@event_bus_bp.route('/api/events/subscribe', methods=['POST'])
def subscribe_events():
    """订阅事件"""
    data = request.get_json() or {}
    event_type = data.get('event_type', '')
    subscriber_id = data.get('subscriber_id', '')

    if not event_type or not subscriber_id:
        return jsonify({'success': False, 'message': '缺少参数'}), 400

    if _event_bus:
        result = _event_bus.subscribe(event_type, None, subscriber_id)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': '事件总线未初始化'}), 500


@event_bus_bp.route('/api/events/unsubscribe', methods=['POST'])
def unsubscribe_events():
    """取消订阅"""
    data = request.get_json() or {}
    event_type = data.get('event_type', '')
    subscriber_id = data.get('subscriber_id', '')
    if _event_bus:
        result = _event_bus.unsubscribe(event_type, subscriber_id)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False}), 500


@event_bus_bp.route('/api/events/publish', methods=['POST'])
def publish_event():
    """发布事件"""
    data = request.get_json() or {}
    event_type = data.get('event_type', '')
    event_data = data.get('data', {})

    if not event_type:
        return jsonify({'success': False, 'message': '事件类型不能为空'}), 400

    if _event_bus:
        result = _event_bus.publish(event_type, event_data)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False}), 500


@event_bus_bp.route('/api/events/history', methods=['GET'])
def event_history():
    """事件历史"""
    if not _event_bus:
        return jsonify({'success': True, 'data': []})
    event_type = request.args.get('event_type')
    limit = int(request.args.get('limit', 100))
    events = _event_bus.get_events(event_type, limit)
    return jsonify({'success': True, 'data': events})


@event_bus_bp.route('/api/events/types', methods=['GET'])
def event_types():
    """事件类型列表"""
    return jsonify({'success': True, 'data': EVENT_TYPES})


@event_bus_bp.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    """事件详情"""
    if not _event_bus:
        return jsonify({'success': False}), 500
    events = _event_bus.get_events(None, 1000)
    for e in events:
        if e.get('id') == event_id:
            return jsonify({'success': True, 'data': e})
    return jsonify({'success': False, 'message': '事件不存在'}), 404