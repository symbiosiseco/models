# -*- coding: utf-8 -*-
"""
受力点API
受 GPL v3.0 保护

受力点列表/实时坐标/历史。
"""

from flask import Blueprint, request, jsonify

force_point_bp = Blueprint('force_point', __name__)

_entity_cbm = None
_all_entities = {}


def set_deps(entity_cbm, entities):
    """注入依赖"""
    global _entity_cbm, _all_entities
    _entity_cbm = entity_cbm
    _all_entities = entities


@force_point_bp.route('/api/force_points/<entity_id>', methods=['GET'])
def list_force_points(entity_id):
    """受力点列表"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    force_points = []
    l3_fp = []
    if hasattr(entity, 'layer'):
        force_points = entity.layer.get('l2_static_attributes', {}).get('受力点', [])
        l3_fp = entity.layer.get('l3_dynamic_state', {}).get('受力点实时坐标', [])

    result = []
    for fp in force_points:
        l3_data = next((x for x in l3_fp if x.get('id') == fp.get('id')), {})
        result.append({
            **fp,
            '实时坐标': l3_data.get('绝对坐标'),
            '当前受力': l3_data.get('当前受力'),
            '受力方向': l3_data.get('受力方向'),
            '受力状态': l3_data.get('受力状态'),
        })

    return jsonify({'success': True, 'data': result})


@force_point_bp.route('/api/force_points/<entity_id>/live', methods=['GET'])
def live_force_points(entity_id):
    """受力点实时坐标"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    l3_fp = []
    if hasattr(entity, 'layer'):
        l3_fp = entity.layer.get('l3_dynamic_state', {}).get('受力点实时坐标', [])

    return jsonify({'success': True, 'data': l3_fp})


@force_point_bp.route('/api/force_points/<entity_id>/<fp_id>', methods=['GET'])
def get_force_point(entity_id, fp_id):
    """单个受力点"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    force_points = []
    if hasattr(entity, 'layer'):
        force_points = entity.layer.get('l2_static_attributes', {}).get('受力点', [])

    fp = next((x for x in force_points if x.get('id') == fp_id), None)
    if not fp:
        return jsonify({'success': False, 'message': '受力点不存在'}), 404

    return jsonify({'success': True, 'data': fp})


@force_point_bp.route('/api/force_points/<entity_id>/<fp_id>/history', methods=['GET'])
def force_point_history(entity_id, fp_id):
    """受力历史"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    # 从L4中提取受力相关事件
    history = []
    if hasattr(entity, 'layer'):
        l4 = entity.layer.get('l4_event_chain', [])
        history = [e for e in l4 if '受力' in e.get('event', '') or 'fp_id' in str(e)]

    return jsonify({'success': True, 'data': history})


@force_point_bp.route('/api/force_points/check', methods=['POST'])
def check_force():
    """受力检查"""
    data = request.get_json() or {}
    entity_id = data.get('entity_id', '')
    fp_id = data.get('fp_id', '')
    force_value = data.get('force_value', 0)

    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    force_points = []
    if hasattr(entity, 'layer'):
        force_points = entity.layer.get('l2_static_attributes', {}).get('受力点', [])

    fp = next((x for x in force_points if x.get('id') == fp_id), None)
    if not fp:
        return jsonify({'success': False, 'message': '受力点不存在'}), 404

    capacity = _parse_capacity(fp.get('承重上限', '500kg'))
    passed = float(force_value) <= capacity

    return jsonify({
        'success': True,
        'data': {
            'passed': passed,
            'current_force': force_value,
            'capacity': capacity,
            'status': 'stable' if passed else 'overload',
        },
    })


@force_point_bp.route('/api/force_points/update', methods=['POST'])
def update_force():
    """更新受力"""
    data = request.get_json() or {}
    entity_id = data.get('entity_id', '')
    fp_id = data.get('fp_id', '')
    force_value = data.get('force_value', '0kg')

    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    if hasattr(entity, 'layer'):
        l3 = entity.layer['l3_dynamic_state']
        if '受力点实时坐标' not in l3:
            l3['受力点实时坐标'] = []
        for fp in l3['受力点实时坐标']:
            if fp.get('id') == fp_id:
                fp['当前受力'] = force_value
                break
        else:
            l3['受力点实时坐标'].append({'id': fp_id, '当前受力': force_value})

    return jsonify({'success': True})


def _parse_capacity(val):
    """解析承重上限"""
    try:
        return float(str(val).replace('kg', '').replace('N·m', '').strip())
    except (ValueError, TypeError):
        return 0.0