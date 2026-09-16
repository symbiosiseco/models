# -*- coding: utf-8 -*-
"""
报表接口
受 GPL v3.0 保护

8种报表 + 事件驱动自动更新。
"""

from flask import Blueprint, request, jsonify

reports_bp = Blueprint('reports', __name__)

_report_engine = None
_event_bus = None
_all_entities = {}


def set_deps(report_engine, event_bus, entities):
    """注入依赖"""
    global _report_engine, _event_bus, _all_entities
    _report_engine = report_engine
    _event_bus = event_bus
    _all_entities = entities


def _entities():
    return list(_all_entities.values())


@reports_bp.route('/api/report/quantity', methods=['GET'])
def quantity_report():
    """工程量清单"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_quantity_report(_entities())})


@reports_bp.route('/api/report/payment', methods=['GET'])
def payment_report():
    """进度款申请"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_payment_report(_entities())})


@reports_bp.route('/api/report/acceptance', methods=['GET'])
def acceptance_report():
    """验收记录"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_acceptance_report(_entities())})


@reports_bp.route('/api/report/change', methods=['GET'])
def change_report():
    """变更台账"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_change_report(_entities())})


@reports_bp.route('/api/report/material', methods=['GET'])
def material_report():
    """材料台账"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_material_report(_entities())})


@reports_bp.route('/api/report/quality', methods=['GET'])
def quality_report():
    """质量记录"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_quality_report(_entities())})


@reports_bp.route('/api/report/asbuilt', methods=['GET'])
def asbuilt_report():
    """竣工图"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_asbuilt_report(_entities())})


@reports_bp.route('/api/report/visa', methods=['GET'])
def visa_report():
    """签证单"""
    if not _report_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _report_engine.generate_visa_report(_entities())})


@reports_bp.route('/api/report/types', methods=['GET'])
def report_types():
    """报表类型列表"""
    types = [
        {'id': 'quantity', 'name': '工程量清单', 'format': 'excel'},
        {'id': 'payment', 'name': '进度款申请', 'format': 'excel+pdf'},
        {'id': 'acceptance', 'name': '验收记录', 'format': 'pdf'},
        {'id': 'change', 'name': '变更台账', 'format': 'excel'},
        {'id': 'material', 'name': '材料台账', 'format': 'excel'},
        {'id': 'quality', 'name': '质量记录', 'format': 'pdf'},
        {'id': 'asbuilt', 'name': '竣工图', 'format': 'json'},
        {'id': 'visa', 'name': '签证单', 'format': 'pdf'},
    ]
    return jsonify({'success': True, 'data': types})