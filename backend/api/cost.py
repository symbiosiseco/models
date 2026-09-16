# -*- coding: utf-8 -*-
"""
造价接口
受 GPL v3.0 保护

含清单量vs实际量 + 签证自动生成。
"""

from flask import Blueprint, request, jsonify

cost_bp = Blueprint('cost', __name__)

_cost_engine = None
_event_bus = None
_all_entities = {}


def set_deps(cost_engine, event_bus, entities):
    """注入依赖"""
    global _cost_engine, _event_bus, _all_entities
    _cost_engine = cost_engine
    _event_bus = event_bus
    _all_entities = entities


@cost_bp.route('/api/cost/summary', methods=['GET'])
def cost_summary():
    """造价汇总"""
    if not _cost_engine:
        return jsonify({'success': True, 'data': {'total': 0, 'by_category': {}, 'visaCount': 0}})
    _cost_engine.generate_from_entities(list(_all_entities.values()))
    return jsonify({'success': True, 'data': _cost_engine.get_summary()})


@cost_bp.route('/api/cost/details', methods=['GET'])
def cost_details():
    """造价明细"""
    if not _cost_engine:
        return jsonify({'success': True, 'data': []})
    details = []
    for e in _all_entities.values():
        cost = _cost_engine.calculate_entity_cost(e)
        details.append(cost)
    return jsonify({'success': True, 'data': details})


@cost_bp.route('/api/cost/visa', methods=['GET'])
def cost_visa():
    """签证列表"""
    if not _cost_engine:
        return jsonify({'success': True, 'data': []})
    return jsonify({'success': True, 'data': _cost_engine.visas})


@cost_bp.route('/api/cost/update', methods=['POST'])
def cost_update():
    """更新造价状态"""
    data = request.get_json() or {}
    entity_id = data.get('entity_id', '')
    new_status = data.get('new_status', '')
    if _cost_engine:
        result = _cost_engine.update_cost(entity_id, new_status)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': '引擎未初始化'})


@cost_bp.route('/api/cost/differences', methods=['GET'])
def cost_differences():
    """差异列表"""
    if not _cost_engine:
        return jsonify({'success': True, 'data': []})
    visas = _cost_engine.check_differences(list(_all_entities.values()))
    return jsonify({'success': True, 'data': visas})


@cost_bp.route('/api/cost/check_differences', methods=['POST'])
def check_differences():
    """检查差异+生成签证"""
    if not _cost_engine:
        return jsonify({'success': True, 'data': {'differences': [], 'visas': []}})
    visas = _cost_engine.check_differences(list(_all_entities.values()))
    return jsonify({
        'success': True,
        'data': {
            'differences': visas,
            'visas': visas,
        },
    })


@cost_bp.route('/api/cost/entity/<entity_id>', methods=['GET'])
def entity_cost(entity_id):
    """单实体造价"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404
    if _cost_engine:
        return jsonify({'success': True, 'data': _cost_engine.calculate_entity_cost(entity)})
    return jsonify({'success': True, 'data': {}})