# -*- coding: utf-8 -*-
"""
L4 全生命周期 API
受 GPL v3.0 保护

提供 L4 套娃履历查询、到期提醒、品质追溯接口。

V2.0 新增（专报G）：
- GET /api/l4/<entity_id>           获取 L4 履历
- GET /api/l4/<entity_id>/lifecycle 获取生命周期
- GET /api/l4/alerts                获取到期提醒
- POST /api/l4/<entity_id>/inspect  记录检查
"""

from flask import Blueprint, request, jsonify
from datetime import datetime


l4_bp = Blueprint('l4', __name__, url_prefix='/api/l4')

_entity_map = {}
_maintenance_scene = None


def set_deps(entity_map, maintenance_scene=None):
    """注入依赖"""
    global _entity_map, _maintenance_scene
    _entity_map = entity_map
    _maintenance_scene = maintenance_scene


@l4_bp.route('/<entity_id>', methods=['GET'])
def get_l4(entity_id):
    """获取 L4 履历（含套娃式履历）"""
    entity = _entity_map.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': f'实体不存在：{entity_id}'}), 404

    l4 = entity.layer.get('l4_event_chain', []) if hasattr(entity, 'layer') else []

    return jsonify({
        'success': True,
        'entity_id': entity_id,
        'entity_type': getattr(entity, 'entity_type', ''),
        'events': l4,
        'count': len(l4),
    })


@l4_bp.route('/<entity_id>/lifecycle', methods=['GET'])
def get_lifecycle(entity_id):
    """获取生命周期"""
    if _maintenance_scene:
        result = _maintenance_scene.get_lifecycle(entity_id)
        return jsonify(result)
    return jsonify({'success': False, 'message': '运维场景未初始化'}), 500


@l4_bp.route('/<entity_id>/trace', methods=['GET'])
def trace_quality(entity_id):
    """★ V2.0 新增：品质追溯（L4套娃履历）"""
    if _maintenance_scene:
        result = _maintenance_scene.trace_quality(entity_id)
        return jsonify(result)
    return jsonify({'success': False, 'message': '运维场景未初始化'}), 500


@l4_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """★ V2.0 新增：获取到期提醒"""
    if _maintenance_scene:
        result = _maintenance_scene.check_lifecycle_alerts()
        return jsonify(result)
    return jsonify({'success': False, 'message': '运维场景未初始化'}), 500


@l4_bp.route('/<entity_id>/inspect', methods=['POST'])
def record_inspection(entity_id):
    """★ V2.0 新增：记录检查"""
    if _maintenance_scene:
        data = request.get_json() or {}
        result = _maintenance_scene.record_inspection(
            entity_id, data.get('result', '检查完成')
        )
        return jsonify(result)
    return jsonify({'success': False, 'message': '运维场景未初始化'}), 500