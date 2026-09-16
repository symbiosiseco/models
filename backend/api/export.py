# -*- coding: utf-8 -*-
"""
导出接口
受 GPL v3.0 保护

含8种报表导出 + 受力点/接触面/L4导出。
"""

import os
from flask import Blueprint, request, jsonify, send_file

export_bp = Blueprint('export', __name__)

_export_engine = None
_report_engine = None
_event_bus = None
_all_entities = {}


def set_deps(export_engine, report_engine, event_bus, entities):
    """注入依赖"""
    global _export_engine, _report_engine, _event_bus, _all_entities
    _export_engine = export_engine
    _report_engine = report_engine
    _event_bus = event_bus
    _all_entities = entities


def _safe_send(file_path):
    """安全发送文件"""
    if not file_path or not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '文件不存在'}), 404
    return send_file(file_path, as_attachment=True)


@export_bp.route('/api/export/excel', methods=['POST'])
def export_excel():
    """导出Excel"""
    if not _export_engine:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    report_type = data.get('report_type', 'export')
    result = _export_engine.export_to_excel(data, f'{report_type}.xlsx')
    return _safe_send(result.get('file_path'))


@export_bp.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    """导出PDF"""
    if not _export_engine:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    report_type = data.get('report_type', 'export')
    result = _export_engine.export_to_pdf(data, f'{report_type}.pdf')
    return _safe_send(result.get('file_path'))


@export_bp.route('/api/export/json', methods=['POST'])
def export_json():
    """导出JSON"""
    if not _export_engine:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    report_type = data.get('report_type', 'export')
    result = _export_engine.export_to_json(data, f'{report_type}.json')
    return _safe_send(result.get('file_path'))


@export_bp.route('/api/export/entity_list', methods=['POST'])
def export_entity_list():
    """导出实体列表"""
    if not _export_engine:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    format = data.get('format', 'excel')
    result = _export_engine.export_entity_list(list(_all_entities.values()), format)
    return _safe_send(result.get('file_path'))


@export_bp.route('/api/export/report/<report_type>', methods=['POST'])
def export_report(report_type):
    """导出报表"""
    if not _export_engine or not _report_engine:
        return jsonify({'success': False}), 500

    data = request.get_json() or {}
    format = data.get('format', 'excel')

    entities = list(_all_entities.values())
    report_data = {}
    if report_type == 'quantity':
        report_data = _report_engine.generate_quantity_report(entities)
    elif report_type == 'payment':
        report_data = _report_engine.generate_payment_report(entities)
    elif report_type == 'acceptance':
        report_data = _report_engine.generate_acceptance_report(entities)
    elif report_type == 'change':
        report_data = _report_engine.generate_change_report(entities)
    elif report_type == 'material':
        report_data = _report_engine.generate_material_report(entities)
    elif report_type == 'quality':
        report_data = _report_engine.generate_quality_report(entities)
    elif report_type == 'asbuilt':
        report_data = _report_engine.generate_asbuilt_report(entities)
    elif report_type == 'visa':
        report_data = _report_engine.generate_visa_report(entities)
    else:
        return jsonify({'success': False, 'message': '未知报表类型'}), 400

    if format == 'excel':
        result = _export_engine.export_to_excel(report_data, f'{report_type}.xlsx')
    elif format == 'pdf':
        result = _export_engine.export_to_pdf(report_data, f'{report_type}.pdf')
    else:
        result = _export_engine.export_to_json(report_data, f'{report_type}.json')

    return _safe_send(result.get('file_path'))


@export_bp.route('/api/export/force_points', methods=['POST'])
def export_force_points():
    """导出受力点"""
    if not _export_engine:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    entity_id = data.get('entity_id', '')
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    fps = []
    if hasattr(entity, 'layer'):
        fps = entity.layer.get('l2_static_attributes', {}).get('受力点', [])

    result = _export_engine.export_to_json(
        {'entity_id': entity_id, 'force_points': fps},
        f'force_points_{entity_id}.json'
    )
    return _safe_send(result.get('file_path'))


@export_bp.route('/api/export/contact_faces', methods=['POST'])
def export_contact_faces():
    """导出接触面"""
    if not _export_engine:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    entity_id = data.get('entity_id', '')
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    cfs = []
    if hasattr(entity, 'layer'):
        cfs = entity.layer.get('l2_static_attributes', {}).get('接触面', [])

    result = _export_engine.export_to_json(
        {'entity_id': entity_id, 'contact_faces': cfs},
        f'contact_faces_{entity_id}.json'
    )
    return _safe_send(result.get('file_path'))


@export_bp.route('/api/export/l4', methods=['POST'])
def export_l4():
    """导出L4履历"""
    if not _export_engine:
        return jsonify({'success': False}), 500
    data = request.get_json() or {}
    entity_id = data.get('entity_id', '')
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    l4 = []
    if hasattr(entity, 'layer'):
        l4 = entity.layer.get('l4_event_chain', [])

    result = _export_engine.export_to_json(
        {'entity_id': entity_id, 'l4_events': l4},
        f'l4_{entity_id}.json'
    )
    return _safe_send(result.get('file_path'))