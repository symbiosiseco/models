# -*- coding: utf-8 -*-
"""
标准参数 API
受 GPL v3.0 保护

V2.0（阶段2-2）：
- POST /api/standards/reload  重载所有标准 JSON，触发传播
- GET  /api/standards/changes 查看变更历史
- GET  /api/standards/pending 查看待更新/待确认实体
- GET  /api/standards/relations 查看依赖关系表
"""

from flask import Blueprint, jsonify, request

standards_bp = Blueprint('standards', __name__, url_prefix='/api/standards')

_propagation_engine = None
_standard_reader = None


def set_deps(propagation_engine, standard_reader):
    """注入依赖"""
    global _propagation_engine, _standard_reader
    _propagation_engine = propagation_engine
    _standard_reader = standard_reader


@standards_bp.route('/reload', methods=['POST'])
def reload_standards():
    """
    重载所有标准文件，触发参数传播。

    用法：
        fetch('/api/standards/reload', {method: 'POST'})
    """
    if not _standard_reader or not _propagation_engine:
        return jsonify({'success': False, 'message': '未初始化'}), 500

    try:
        # 清缓存（强制下次读取最新文件）
        _standard_reader.clear_cache()

        # 遍历所有类别，逐个通知
        categories = _standard_reader.list_categories()
        all_changes = []

        for category in categories:
            result = _propagation_engine.on_param_change(category, '*')
            if result.get('affected_count', 0) > 0:
                all_changes.append(result)

        # 汇总
        total_affected = sum(c.get('affected_count', 0) for c in all_changes)

        return jsonify({
            'success': True,
            'categories_checked': len(categories),
            'categories_changed': len(all_changes),
            'total_affected': total_affected,
            'details': all_changes,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@standards_bp.route('/changes', methods=['GET'])
def get_changes():
    """查看变更历史"""
    if not _propagation_engine:
        return jsonify({'success': False, 'message': '未初始化'}), 500

    limit = int(request.args.get('limit', 100))
    history = _propagation_engine.get_change_history(limit)
    return jsonify({'success': True, 'data': history, 'count': len(history)})


@standards_bp.route('/pending', methods=['GET'])
def get_pending():
    """
    查看待更新/待确认实体。

    - pending_rebuild: 未安装，可直接自动更新
    - pending_confirmation: 已安装，需人工确认
    """
    if not _propagation_engine:
        return jsonify({'success': False, 'message': '未初始化'}), 500

    rebuilds = _propagation_engine.get_pending_rebuilds()
    confirmations = _propagation_engine.get_pending_confirmations()

    return jsonify({
        'success': True,
        'pending_rebuild': rebuilds,
        'pending_confirmation': confirmations,
        'rebuild_count': len(rebuilds),
        'confirmation_count': len(confirmations),
    })


@standards_bp.route('/relations', methods=['GET'])
def get_relations():
    """查看依赖关系表"""
    if not _propagation_engine:
        return jsonify({'success': False, 'message': '未初始化'}), 500

    return jsonify({'success': True, 'data': _propagation_engine.get_relations()})


# ★ V2.0 阶段2-3：新增重建 API

_rebuild_engine = None


def set_rebuild_engine(rebuild_engine):
    """注入重建引擎"""
    global _rebuild_engine
    _rebuild_engine = rebuild_engine


@standards_bp.route('/rebuild', methods=['POST'])
def rebuild_entity():
    """
    重建单个实体。

    请求体：
        {"entity_id": "FLANGE-001"}
    """
    if not _rebuild_engine:
        return jsonify({'success': False, 'message': '重建引擎未初始化'}), 500

    data = request.get_json() or {}
    entity_id = data.get('entity_id')
    if not entity_id:
        return jsonify({'success': False, 'message': '缺少 entity_id'}), 400

    result = _rebuild_engine.rebuild_entity(entity_id)
    return jsonify(result)


@standards_bp.route('/rebuild_all', methods=['POST'])
def rebuild_all():
    """重建所有待更新的实体"""
    if not _rebuild_engine:
        return jsonify({'success': False, 'message': '重建引擎未初始化'}), 500

    result = _rebuild_engine.rebuild_all_pending()
    return jsonify(result)


@standards_bp.route('/rebuild_history', methods=['GET'])
def get_rebuild_history():
    """查看重建历史"""
    if not _rebuild_engine:
        return jsonify({'success': False, 'message': '重建引擎未初始化'}), 500

    limit = int(request.args.get('limit', 100))
    history = _rebuild_engine.get_history(limit)
    return jsonify({'success': True, 'data': history, 'count': len(history)})