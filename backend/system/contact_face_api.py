# -*- coding: utf-8 -*-
"""
接触面API
受 GPL v3.0 保护

接触面列表/检查/垫片检查/管道分段。
"""

from flask import Blueprint, request, jsonify

contact_face_bp = Blueprint('contact_face', __name__)

_contact_check = None
_all_entities = {}


def set_deps(contact_check, entities):
    """注入依赖"""
    global _contact_check, _all_entities
    _contact_check = contact_check
    _all_entities = entities


@contact_face_bp.route('/api/contact_faces/<entity_id>', methods=['GET'])
def list_contact_faces(entity_id):
    """接触面列表"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    cfs = []
    if hasattr(entity, 'layer'):
        cfs = entity.layer.get('l2_static_attributes', {}).get('接触面', [])

    return jsonify({'success': True, 'data': cfs})


@contact_face_bp.route('/api/contact_faces/<entity_id>/<cf_id>', methods=['GET'])
def get_contact_face(entity_id, cf_id):
    """单个接触面"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    cfs = []
    if hasattr(entity, 'layer'):
        cfs = entity.layer.get('l2_static_attributes', {}).get('接触面', [])

    cf = next((x for x in cfs if x.get('id') == cf_id), None)
    if not cf:
        return jsonify({'success': False, 'message': '接触面不存在'}), 404

    return jsonify({'success': True, 'data': cf})


@contact_face_bp.route('/api/contact_faces/check', methods=['POST'])
def check_contact_faces():
    """接触面检查"""
    data = request.get_json() or {}
    entity_id = data.get('entity_id', '')
    other_id = data.get('other_id', '')

    entity = _all_entities.get(entity_id)
    other = _all_entities.get(other_id)
    if not entity or not other:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    if _contact_check:
        result = _contact_check.check_contact_faces(entity, other)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': True, 'data': {'passed': True}})


@contact_face_bp.route('/api/contact_faces/check_gasket', methods=['POST'])
def check_gasket():
    """垫片检查（5个约束）"""
    data = request.get_json() or {}
    gasket_id = data.get('gasket_id', '')
    flange_left_id = data.get('flange_left_id', '')
    flange_right_id = data.get('flange_right_id', '')

    gasket = _all_entities.get(gasket_id)
    flange_left = _all_entities.get(flange_left_id)
    flange_right = _all_entities.get(flange_right_id)

    if not gasket or not flange_left or not flange_right:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    results = {}
    if _contact_check:
        results = {
            'position': _contact_check.check_gasket_position(gasket, flange_left, flange_right),
            'range': _contact_check.check_gasket_range(gasket, flange_left),
            'hole_clearance': _contact_check.check_gasket_hole_clearance(gasket, flange_left),
            'direction': _contact_check.check_gasket_direction(gasket, flange_left),
            'count': _contact_check.check_gasket_count([flange_left, flange_right], [gasket]),
        }

    return jsonify({'success': True, 'data': results})


@contact_face_bp.route('/api/contact_faces/check_pipe', methods=['POST'])
def check_pipe():
    """管道分段检查"""
    data = request.get_json() or {}
    pipe_id = data.get('pipe_id', '')

    pipe = _all_entities.get(pipe_id)
    if not pipe:
        return jsonify({'success': False, 'message': '管道不存在'}), 404

    if _contact_check:
        result = _contact_check.check_pipe_segments(pipe)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': True, 'data': {'passed': True}})


@contact_face_bp.route('/api/contact_faces/check_clamp', methods=['POST'])
def check_clamp():
    """卡箍检查"""
    data = request.get_json() or {}
    clamp_id = data.get('clamp_id', '')
    pipe_id = data.get('pipe_id', '')
    gasket_id = data.get('gasket_id', '')

    clamp = _all_entities.get(clamp_id)
    pipe = _all_entities.get(pipe_id)
    gasket = _all_entities.get(gasket_id)

    if not clamp or not pipe:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    results = {}
    if _contact_check:
        results = {
            'groove': _contact_check.check_clamp_groove(clamp, pipe),
            'rubber_ring': _contact_check.check_clamp_rubber_ring(clamp, gasket),
        }

    return jsonify({'success': True, 'data': results})