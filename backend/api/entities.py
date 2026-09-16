# -*- coding: utf-8 -*-
"""
实体接口
受 GPL v3.0 保护

所有实体的CRUD。
含受力点/接触面/CBM/L4查询。
"""

from flask import Blueprint, request, jsonify

entities_bp = Blueprint('entities', __name__)

# 全局实体存储（由app.py注入）
_all_entities = {}


def set_entities(entities):
    """注入实体存储"""
    global _all_entities
    _all_entities = entities


@entities_bp.route('/api/entities/', methods=['GET'])
def list_entities():
    """实体列表"""
    result = []
    for e in _all_entities.values():
        if hasattr(e, 'to_dict'):
            result.append(e.to_dict())
        else:
            result.append({'id': getattr(e, 'id', ''), 'entity_type': getattr(e, 'entity_type', '')})
    return jsonify({'success': True, 'data': result})


@entities_bp.route('/api/entities/<entity_id>', methods=['GET'])
def get_entity(entity_id):
    """实体详情"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404
    if hasattr(entity, 'to_dict'):
        return jsonify({'success': True, 'data': entity.to_dict()})
    return jsonify({'success': True, 'data': entity})


@entities_bp.route('/api/entities/', methods=['POST'])
def create_entity():
    """创建实体"""
    data = request.get_json() or {}
    eid = data.get('id', '')
    if not eid:
        return jsonify({'success': False, 'message': '缺少 id'}), 400
    _all_entities[eid] = data
    return jsonify({'success': True, 'data': data})


@entities_bp.route('/api/entities/<entity_id>', methods=['PUT'])
def update_entity(entity_id):
    """更新实体"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404
    data = request.get_json() or {}
    if hasattr(entity, 'layer'):
        entity.layer.get('l2_static_attributes', {}).update(data.get('l2', {}))
        entity.layer.get('l3_dynamic_state', {}).update(data.get('l3', {}))
    return jsonify({'success': True, 'data': entity.to_dict() if hasattr(entity, 'to_dict') else entity})


@entities_bp.route('/api/entities/<entity_id>', methods=['DELETE'])
def delete_entity(entity_id):
    """删除实体"""
    if entity_id in _all_entities:
        del _all_entities[entity_id]
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '实体不存在'}), 404


@entities_bp.route('/api/scene/', methods=['GET'])
def get_scene():
    """场景信息"""
    return jsonify({
        'success': True,
        'data': {
            'total': len(_all_entities),
            'entities': [{'id': getattr(e, 'id', ''), 'entity_type': getattr(e, 'entity_type', '')} for e in _all_entities.values()],
        },
    })


@entities_bp.route('/api/entities/<entity_id>/force_points', methods=['GET'])
def get_force_points(entity_id):
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
            '受力状态': l3_data.get('受力状态'),
        })
    return jsonify({'success': True, 'data': result})


@entities_bp.route('/api/entities/<entity_id>/contact_faces', methods=['GET'])
def get_contact_faces(entity_id):
    """接触面列表"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404
    cfs = []
    if hasattr(entity, 'layer'):
        cfs = entity.layer.get('l2_static_attributes', {}).get('接触面', [])
    return jsonify({'success': True, 'data': cfs})


@entities_bp.route('/api/entities/<entity_id>/cbm', methods=['GET'])
def get_cbm_status(entity_id):
    """CBM状态"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404
    cbm = {}
    status = 'stable'
    if hasattr(entity, 'layer'):
        cbm = entity.layer.get('cbm_abilities', {})
        status = entity.layer.get('l3_dynamic_state', {}).get('cbm_status', 'stable')
    return jsonify({'success': True, 'data': {'rules': cbm, 'status': status}})


@entities_bp.route('/api/entities/<entity_id>/l4', methods=['GET'])
def get_l4(entity_id):
    """L4履历"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404
    l4 = []
    if hasattr(entity, 'layer'):
        l4 = entity.layer.get('l4_event_chain', [])
    return jsonify({'success': True, 'data': l4})