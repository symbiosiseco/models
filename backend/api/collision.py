# -*- coding: utf-8 -*-
"""
碰撞检测接口
受 GPL v3.0 保护

含分级预警 + 碰撞摘要 + 解决。
"""

from flask import Blueprint, request, jsonify

collision_bp = Blueprint('collision', __name__)

# 全局引擎（由app.py注入）
_collision_engine = None
_event_bus = None
_all_entities = {}


def set_deps(collision_engine, event_bus, entities):
    """注入依赖"""
    global _collision_engine, _event_bus, _all_entities
    _collision_engine = collision_engine
    _event_bus = event_bus
    _all_entities = entities


@collision_bp.route('/api/collisions/', methods=['GET'])
def list_collisions():
    """碰撞列表"""
    entity_id = request.args.get('entity_id')
    if not _collision_engine:
        return jsonify({'success': True, 'data': []})
    collisions = _collision_engine.detect_all(list(_all_entities.values()))
    if entity_id:
        collisions = [c for c in collisions if c.get('entity1') == entity_id or c.get('entity2') == entity_id]
    return jsonify({'success': True, 'data': collisions})


@collision_bp.route('/api/collision/list', methods=['GET'])
def collision_list_compat():
    """兼容路径"""
    return list_collisions()


@collision_bp.route('/api/collision/check', methods=['POST'])
def check_collision():
    """检测两个实体"""
    data = request.get_json() or {}
    e1_id = data.get('entity1_id', '')
    e2_id = data.get('entity2_id', '')
    e1 = _all_entities.get(e1_id)
    e2 = _all_entities.get(e2_id)
    if not e1 or not e2:
        return jsonify({'success': False, 'message': '实体不存在'}), 404
    if _collision_engine:
        result = _collision_engine.detect_pair(e1, e2)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': True, 'data': {'collision': False}})


@collision_bp.route('/api/collision/check_all', methods=['POST'])
def check_all():
    """检测所有实体"""
    if not _collision_engine:
        return jsonify({'success': True, 'data': []})
    collisions = _collision_engine.detect_all(list(_all_entities.values()))
    return jsonify({'success': True, 'data': collisions})


@collision_bp.route('/api/collision/summary', methods=['GET'])
def collision_summary():
    """碰撞摘要（红/黄/绿）"""
    if not _collision_engine:
        return jsonify({'success': True, 'data': {'red': 0, 'yellow': 0, 'green': 0}})
    _collision_engine.detect_all(list(_all_entities.values()))
    summary = _collision_engine.get_summary()
    summary['green'] = max(0, len(_all_entities) - summary.get('red', 0) - summary.get('yellow', 0))
    return jsonify({'success': True, 'data': summary})


@collision_bp.route('/api/collision/<collision_id>/resolve', methods=['POST'])
def resolve_collision(collision_id):
    """解决碰撞"""
    data = request.get_json() or {}
    resolution = data.get('resolution', '')
    if _event_bus:
        _event_bus.publish('碰撞解决', {
            'collision_id': collision_id,
            'resolution': resolution,
        })
    return jsonify({'success': True, 'data': {'collision_id': collision_id, 'resolution': resolution}})