# -*- coding: utf-8 -*-
"""
模板接口
受 GPL v3.0 保护

含受力点/接触面/硬性要求查询。
"""

from flask import Blueprint, request, jsonify

templates_bp = Blueprint('templates', __name__)

_template_store = None
_event_bus = None
_all_entities = {}


def set_deps(template_store, event_bus, entities):
    """注入依赖"""
    global _template_store, _event_bus, _all_entities
    _template_store = template_store
    _event_bus = event_bus
    _all_entities = entities


@templates_bp.route('/api/templates/', methods=['GET'])
def list_templates():
    """模板列表"""
    if not _template_store:
        return jsonify({'success': True, 'data': []})
    category = request.args.get('category')
    entity_type = request.args.get('entity_type')
    templates = _template_store.list_all(category, entity_type)
    return jsonify({'success': True, 'data': templates})


@templates_bp.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """模板详情"""
    if not _template_store:
        return jsonify({'success': False}), 500
    tpl = _template_store.get(template_id)
    if not tpl:
        return jsonify({'success': False, 'message': '模板不存在'}), 404
    return jsonify({'success': True, 'data': tpl})


@templates_bp.route('/api/templates/', methods=['POST'])
def create_template():
    """创建模板"""
    if not _template_store:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    try:
        result = _template_store.create(data)
        return jsonify({'success': True, 'data': result})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@templates_bp.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """删除模板"""
    if not _template_store:
        return jsonify({'success': False}), 500
    result = _template_store.delete(template_id)
    return jsonify({'success': result})


@templates_bp.route('/api/templates/<template_id>/instantiate', methods=['POST'])
def instantiate_template(template_id):
    """生成实例"""
    if not _template_store:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    position = data.get('position', {'x': 0, 'y': 0, 'z': 0})
    try:
        entity = _template_store.instantiate(template_id, position)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 404

    _all_entities[entity['id']] = entity

    if _event_bus:
        _event_bus.publish('L3变化', {
            'entity_id': entity['id'],
            'new_status': '待装配',
        })

    return jsonify({'success': True, 'data': entity})


@templates_bp.route('/api/templates/stats/', methods=['GET'])
def template_stats():
    """模板统计"""
    if not _template_store:
        return jsonify({'success': True, 'data': {}})
    groups = _template_store.get_by_category()
    return jsonify({
        'success': True,
        'data': {k: len(v) for k, v in groups.items()},
    })


@templates_bp.route('/api/templates/<template_id>/force_points', methods=['GET'])
def template_force_points(template_id):
    """受力点"""
    if not _template_store:
        return jsonify({'success': False}), 500
    tpl = _template_store.get(template_id)
    if not tpl:
        return jsonify({'success': False, 'message': '模板不存在'}), 404
    return jsonify({'success': True, 'data': tpl.get('force_points', [])})


@templates_bp.route('/api/templates/<template_id>/contact_faces', methods=['GET'])
def template_contact_faces(template_id):
    """接触面"""
    if not _template_store:
        return jsonify({'success': False}), 500
    tpl = _template_store.get(template_id)
    if not tpl:
        return jsonify({'success': False, 'message': '模板不存在'}), 404
    return jsonify({'success': True, 'data': tpl.get('contact_faces', [])})


@templates_bp.route('/api/templates/<template_id>/manual', methods=['GET'])
def template_manual(template_id):
    """硬性要求"""
    if not _template_store:
        return jsonify({'success': False}), 500
    tpl = _template_store.get(template_id)
    if not tpl:
        return jsonify({'success': False, 'message': '模板不存在'}), 404
    return jsonify({'success': True, 'data': tpl.get('硬性要求', {})})