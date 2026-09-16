# -*- coding: utf-8 -*-
"""
搜索接口
受 GPL v3.0 保护

含受力点/接触面搜索。
"""

from flask import Blueprint, request, jsonify

search_bp = Blueprint('search', __name__)

_search_engine = None
_event_bus = None


def set_deps(search_engine, event_bus):
    """注入依赖"""
    global _search_engine, _event_bus
    _search_engine = search_engine
    _event_bus = event_bus


@search_bp.route('/api/search/', methods=['GET'])
def search():
    """关键词搜索"""
    keyword = request.args.get('keyword', '')
    if not keyword or not _search_engine:
        return jsonify({'success': True, 'data': []})
    results = _search_engine.search(keyword)
    return jsonify({'success': True, 'data': [_to_dict(e) for e in results]})


@search_bp.route('/api/search/type/<entity_type>', methods=['GET'])
def search_by_type(entity_type):
    """按类型搜索"""
    if not _search_engine:
        return jsonify({'success': True, 'data': []})
    results = _search_engine.search_by_type(entity_type)
    return jsonify({'success': True, 'data': [_to_dict(e) for e in results]})


@search_bp.route('/api/search/position', methods=['GET'])
def search_by_position():
    """按位置搜索"""
    try:
        x = float(request.args.get('x', 0))
        y = float(request.args.get('y', 0))
        z = float(request.args.get('z', 0))
        radius = float(request.args.get('radius', 1000))
    except ValueError:
        return jsonify({'success': False, 'message': '坐标无效'}), 400

    if not _search_engine:
        return jsonify({'success': True, 'data': []})
    results = _search_engine.search_by_position(x, y, z, radius)
    return jsonify({'success': True, 'data': [_to_dict(e) for e in results]})


@search_bp.route('/api/search/force_point', methods=['GET'])
def search_by_force_point():
    """按受力点搜索"""
    try:
        cmin = float(request.args.get('min', 0))
        cmax = float(request.args.get('max', 99999))
    except ValueError:
        return jsonify({'success': False, 'message': '承重范围无效'}), 400

    if not _search_engine:
        return jsonify({'success': True, 'data': []})
    results = _search_engine.search_by_force_point(cmin, cmax)
    return jsonify({'success': True, 'data': [_to_dict(e) for e in results]})


@search_bp.route('/api/search/contact_face', methods=['GET'])
def search_by_contact_face():
    """按接触面搜索"""
    cf_type = request.args.get('cf_type', '')
    if not cf_type:
        return jsonify({'success': False, 'message': '缺少接触面类型'}), 400
    if not _search_engine:
        return jsonify({'success': True, 'data': []})
    results = _search_engine.search_by_contact_face(cf_type)
    return jsonify({'success': True, 'data': [_to_dict(e) for e in results]})


@search_bp.route('/api/search/status/<status>', methods=['GET'])
def search_by_status(status):
    """按状态搜索"""
    if not _search_engine:
        return jsonify({'success': True, 'data': []})
    results = _search_engine.search_by_status(status)
    return jsonify({'success': True, 'data': [_to_dict(e) for e in results]})


@search_bp.route('/api/search/system/<system>', methods=['GET'])
def search_by_system(system):
    """按系统搜索"""
    if not _search_engine:
        return jsonify({'success': True, 'data': []})
    results = _search_engine.search_by_system(system)
    return jsonify({'success': True, 'data': [_to_dict(e) for e in results]})


@search_bp.route('/api/search/stats', methods=['GET'])
def search_stats():
    """搜索索引统计"""
    if not _search_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _search_engine.get_index_stats()})


def _to_dict(entity):
    """实体转字典"""
    if hasattr(entity, 'to_dict'):
        return entity.to_dict()
    return {
        'id': getattr(entity, 'id', ''),
        'entity_type': getattr(entity, 'entity_type', ''),
    }